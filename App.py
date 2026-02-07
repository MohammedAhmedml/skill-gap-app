# =========================================================
# SKILL GAP ANALYZER PRO MAX
# Full Hackathon Version (All features included)
# =========================================================

import streamlit as st
import sqlite3
import hashlib
import smtplib
import ssl
import os
from email.message import EmailMessage
from datetime import datetime
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# ========================
# LOAD ENV
# ========================
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# ========================
# PAGE CONFIG
# ========================
st.set_page_config(page_title="Skill Gap Analyzer", layout="wide")

# ========================
# DATABASE
# ========================
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

# ========================
# CAREER SKILLS
# ========================
CAREER_SKILLS = {
"Data Scientist": ["Python","SQL","ML","Statistics","Visualization"],
"Web Developer": ["HTML","CSS","JavaScript","React","Backend"],
"AI Engineer": ["Python","ML","DL","NLP","Math"]
}

# ========================
# QUIZ QUESTIONS
# ========================
QUIZ = {
"Python":[
("len([1,2,3]) ?", ["2","3","4","5"], "3"),
("Keyword for function?", ["fun","define","def","func"], "def"),
("List symbol?", ["()","{}","[]","<>"], "[]")
],
"SQL":[
("SELECT returns?", ["rows","tables","columns","files"], "rows"),
("Filter keyword?", ["WHERE","WHEN","IF","FILTER"], "WHERE")
]
}

# ========================
# HELPERS
# ========================

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def send_email(to_email, subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        st.error("Add EMAIL_USER and EMAIL_PASS in .env or secrets")
        return

    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=context) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

def update_streak(u):
    today = datetime.now().strftime("%Y-%m-%d")

    row = c.execute("SELECT streak,total_days,last_active FROM users WHERE username=?",(u,)).fetchone()

    if not row: return

    streak,total,last = row

    if last != today:
        streak += 1
        total += 1
        c.execute("""
        UPDATE users SET streak=?, total_days=?, last_active=? WHERE username=?
        """,(streak,total,today,u))
        conn.commit()

def ai_recommend(goal, gaps):
    plan = f"""
🚀 Personalized Plan for {goal}

You need improvement in:
{", ".join(gaps)}

Step-by-step:
1. Study basics
2. Practice daily
3. Build mini projects
4. Take free courses
5. Track progress

Spend 1–2 hours daily.
Within 30 days you can close these gaps.
"""
    return plan

# ========================
# AUTH
# ========================
def auth():

    tab1, tab2 = st.tabs(["Login","Register"])

    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")

        if st.button("Login"):
            row = c.execute("SELECT password FROM users WHERE username=?",(u,)).fetchone()
            if row and row[0]==hash_pw(p):
                st.session_state.user = u
                st.success("Logged in")
                st.rerun()

    with tab2:
        u = st.text_input("Username", key="reg_u")
        e = st.text_input("Email", key="reg_e")
        p = st.text_input("Password", type="password", key="reg_p")

        if st.button("Register"):
            c.execute("INSERT OR REPLACE INTO users VALUES(?,?,?,?,?,?)",
                      (u,e,hash_pw(p),0,0,""))
            conn.commit()
            st.success("Registered")

# ========================
# IF NOT LOGGED
# ========================
if "user" not in st.session_state:
    auth()
    st.stop()

user = st.session_state.user

# ========================
# SIDEBAR
# ========================
page = st.sidebar.radio("Navigation",
["Home","Assessment","Dashboard","Leaderboard","Email Reminder"])

# ========================
# HOME
# ========================
if page=="Home":

    st.title("🚀 Skill Gap Analyzer")

    goals = ["Select your career goal..."] + list(CAREER_SKILLS.keys())

    goal = st.selectbox("Career Goal", goals, index=0)

    if goal=="Select your career goal...":
        st.stop()

    st.session_state.goal = goal
    st.success("Goal selected!")

# ========================
# ASSESSMENT
# ========================
if page=="Assessment":

    goal = st.session_state.get("goal")

    if not goal:
        st.warning("Select goal first")
        st.stop()

    st.header("Skill Assessment Quiz")

    score = 0
    total = 0

    for skill in CAREER_SKILLS[goal]:
        if skill in QUIZ:

            st.subheader(skill)

            for q,opts,ans in QUIZ[skill]:
                choice = st.radio(q,opts,key=q)

                total+=1
                if choice==ans:
                    score+=1

    if st.button("Submit Test"):

        percent = int((score/total)*100)

        gaps = []
        if percent < 70:
            gaps = CAREER_SKILLS[goal]

        plan = ai_recommend(goal,gaps)

        st.write("Score:",percent,"%")
        st.write(plan)

        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO progress VALUES(?,?,?,?)",
                  (user,goal,percent,today))
        conn.commit()

        update_streak(user)

# ========================
# DASHBOARD
# ========================
if page=="Dashboard":

    df = pd.read_sql_query("SELECT * FROM progress WHERE username=?",conn,params=(user,))

    if len(df)==0:
        st.info("No attempts yet")
    else:
        fig = px.line(df,x="date",y="score",title="Progress")
        st.plotly_chart(fig,use_container_width=True)

    row = c.execute("SELECT streak,total_days FROM users WHERE username=?",(user,)).fetchone()

    st.metric("🔥 Streak",row[0])
    st.metric("📅 Total Days",row[1])

# ========================
# LEADERBOARD
# ========================
if page=="Leaderboard":

    df = pd.read_sql_query("SELECT username,streak,total_days FROM users ORDER BY streak DESC",conn)
    st.dataframe(df)

# ========================
# EMAIL REMINDER
# ========================
if page=="Email Reminder":

    row = c.execute("SELECT email FROM users WHERE username=?",(user,)).fetchone()
    email = row[0]

    st.write("Your email:",email)

    if st.button("Send Reminder Now"):
        send_email(email,"Daily Skill Reminder","Practice today and keep your streak!")
        st.success("Email sent!")
