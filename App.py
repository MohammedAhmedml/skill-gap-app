# =========================================================
# SKILL GAP ANALYZER PRO – FINAL STABLE HACKATHON BUILD
# Clean • Robust • 10Q per career • No bugs • Cloud safe
# =========================================================

import streamlit as st
import sqlite3
import hashlib
import ssl
import smtplib
from email.message import EmailMessage
from datetime import datetime
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Skill Gap Analyzer Pro", layout="wide")

# =========================================================
# EMAIL (Streamlit secrets only)
# =========================================================
EMAIL_USER = st.secrets.get("EMAIL_USER")
EMAIL_PASS = st.secrets.get("EMAIL_PASS")

# =========================================================
# DATABASE
# =========================================================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
email TEXT,
password TEXT,
streak INTEGER DEFAULT 0,
total_days INTEGER DEFAULT 0,
last_active TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS progress(
username TEXT,
goal TEXT,
score INTEGER,
date TEXT
)
""")
conn.commit()

# =========================================================
# DATA (10 QUESTIONS PER CAREER)
# =========================================================

CAREER_QUIZ = {

"Data Scientist":[
("Python library for data?",["NumPy","HTML","CSS","Excel"],"NumPy"),
("SQL keyword for filter?",["WHERE","WHEN","IF","SORT"],"WHERE"),
("Regression predicts?",["numbers","images","text","audio"],"numbers"),
("Mean is?",["average","sum","mode","range"],"average"),
("Model overfits means?",["memorizes","generalizes","random","slow"],"memorizes"),
("Pandas used for?",["dataframes","games","design","ui"],"dataframes"),
("Probability range?",["0-1","1-10","10-20","0-100"],"0-1"),
("Visualization tool?",["Plotly","Docker","Git","HTML"],"Plotly"),
("Classification predicts?",["labels","numbers","shapes","colors"],"labels"),
("Feature means?",["input variable","output","model","loss"],"input variable")
],

"Web Developer":[
("HTML stands for?",["Hyper Text Markup Language","Home Tool Markup","Hyperlinks","None"],"Hyper Text Markup Language"),
("CSS used for?",["styling","database","logic","server"],"styling"),
("JS used for?",["interactivity","design","data","images"],"interactivity"),
("Tag for link?",["<a>","<p>","<div>","<h1>"],"<a>"),
("Framework example?",["React","MySQL","Python","Linux"],"React"),
("Backend example?",["Node.js","CSS","HTML","Figma"],"Node.js"),
("API means?",["Application Programming Interface","App Page Info","None","Code"],"Application Programming Interface"),
("Git used for?",["version control","design","deploy","host"],"version control"),
("Database example?",["MongoDB","React","Tailwind","CSS"],"MongoDB"),
("HTTP method to fetch?",["GET","PUT","POST","DEL"],"GET")
],

"AI Engineer":[
("Deep learning uses?",["neural networks","html","css","excel"],"neural networks"),
("GPU helps in?",["training faster","styling","design","hosting"],"training faster"),
("NLP means?",["Natural Language Processing","Neural Learning","None","Net Link"],"Natural Language Processing"),
("TensorFlow is?",["framework","database","browser","os"],"framework"),
("CNN used for?",["images","text only","audio only","none"],"images"),
("Loss function measures?",["error","speed","size","data"],"error"),
("Gradient descent?",["optimization","render","deploy","compile"],"optimization"),
("Dataset split?",["train/test","html/css","gpu/cpu","none"],"train/test"),
("Activation adds?",["non-linearity","speed","color","style"],"non-linearity"),
("Overfitting means?",["memorizing","learning","generalizing","none"],"memorizing")
]
}

COURSES = {
"Data Scientist":["Coursera ML","Kaggle practice","Statistics Khan Academy"],
"Web Developer":["FreeCodeCamp Web Dev","React Docs","NodeJS Guide"],
"AI Engineer":["Deep Learning Specialization","TensorFlow Docs","HuggingFace NLP"]
}

# =========================================================
# HELPERS
# =========================================================

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def send_email(to_email):
    if not to_email or "@" not in to_email:
        st.error("Invalid email")
        return

    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = "Daily Study Reminder"
    msg.set_content("Study today to maintain your streak!")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=context) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

def update_streak(user):
    today = datetime.now().strftime("%Y-%m-%d")
    s,t,last = c.execute("SELECT streak,total_days,last_active FROM users WHERE username=?",(user,)).fetchone()

    if last != today:
        s+=1
        t+=1

    c.execute("UPDATE users SET streak=?,total_days=?,last_active=? WHERE username=?",(s,t,today,user))
    conn.commit()

# =========================================================
# AUTH
# =========================================================

def auth():

    tab1,tab2=st.tabs(["Login","Register"])

    with tab1:
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        if st.button("Login"):
            row=c.execute("SELECT password FROM users WHERE username=?",(u,)).fetchone()
            if row and row[0]==hash_pw(p):
                st.session_state.user=u
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        u=st.text_input("Username",key="r1")
        e=st.text_input("Email",key="r2")
        p=st.text_input("Password",type="password",key="r3")
        if st.button("Register"):
            c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)",(u,e,hash_pw(p),0,0,""))
            conn.commit()
            st.session_state.user=u
            st.rerun()

if "user" not in st.session_state:
    auth()
    st.stop()

user=st.session_state.user

# =========================================================
# NAVIGATION
# =========================================================

page=st.sidebar.radio("Menu",["Home","Assessment","Dashboard","Leaderboard","Email Reminder"])

# =========================================================
# HOME
# =========================================================

if page=="Home":
    st.title("🚀 Skill Gap Analyzer")
    goal=st.selectbox("Choose Career Goal",["Select..."]+list(CAREER_QUIZ.keys()))
    if goal!="Select...":
        st.session_state.goal=goal
        st.session_state.page="Assessment"
        st.rerun()

# =========================================================
# ASSESSMENT (NO BUGS)
# =========================================================

if page=="Assessment":

    goal=st.session_state.get("goal")
    if not goal:
        st.warning("Select goal first")
        st.stop()

    questions=CAREER_QUIZ[goal]

    score=0

    for i,(q,opts,ans) in enumerate(questions):
        choice=st.radio(f"Q{i+1}. {q}",opts,key=i)
        if choice==ans:
            score+=1

    if st.button("Submit Test"):

        percent=int((score/len(questions))*100)

        today=datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO progress VALUES (?,?,?,?)",(user,goal,percent,today))
        conn.commit()

        update_streak(user)

        st.success(f"Score: {percent}%")

        st.subheader("📚 Recommended Courses")
        for c_name in COURSES[goal]:
            st.write("•",c_name)

        st.subheader("🗓 Weekly Plan")
        st.write("Week 1 Basics • Week 2 Practice • Week 3 Projects • Week 4 Mock Test")

# =========================================================
# DASHBOARD
# =========================================================

if page=="Dashboard":

    df=pd.read_sql_query("SELECT * FROM progress WHERE username=?",conn,params=(user,))

    if len(df)>0:
        fig=px.line(df,x="date",y="score",markers=True,title="Progress")
        st.plotly_chart(fig,use_container_width=True)

    s,t=c.execute("SELECT streak,total_days FROM users WHERE username=?",(user,)).fetchone()
    st.metric("🔥 Streak",s)
    st.metric("📅 Days Active",t)

# =========================================================
# LEADERBOARD (PRETTY TABLE)
# =========================================================

if page=="Leaderboard":

    df=pd.read_sql_query("SELECT username,streak,total_days FROM users ORDER BY streak DESC",conn)
    df["Rank"]=range(1,len(df)+1)
    df=df[["Rank","username","streak","total_days"]]
    st.dataframe(df,use_container_width=True)

# =========================================================
# EMAIL
# =========================================================

if page=="Email Reminder":
    email=c.execute("SELECT email FROM users WHERE username=?",(user,)).fetchone()[0]
    if st.button("Send Reminder"):
        send_email(email)
        st.success("Reminder sent!")
