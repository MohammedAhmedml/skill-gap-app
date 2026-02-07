# =========================================================
# SKILL GAP ANALYZER – FINAL HACKATHON PRO BUILD
# Clean • Polished • Auto flow • Courses • Weekly plan
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

# =========================================================
# PAGE
# =========================================================
st.set_page_config(page_title="Skill Gap Analyzer Pro", layout="wide")

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
# DATA
# =========================================================
CAREER_SKILLS = {
"Data Scientist": ["Python","SQL","ML","Statistics"],
"Web Developer": ["HTML","CSS","JavaScript"],
"AI Engineer": ["Python","ML","DL","Math"]
}

COURSES = {
"Python":"Python for Everybody – Coursera",
"SQL":"SQL Basics – W3Schools",
"ML":"Machine Learning – Coursera",
"Statistics":"Statistics Fundamentals – Khan Academy",
"HTML":"HTML & CSS – FreeCodeCamp",
"JavaScript":"JavaScript Essentials – Great Learning"
}

QUIZ = {
"Python":[("len([1,2,3])?",["2","3","4"],"3")],
"SQL":[("SELECT returns?",["rows","files"],"rows")],
"HTML":[("Tag for link?",["<a>","<p>"],"<a>")]
}

# =========================================================
# HELPERS
# =========================================================

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- EMAIL ----------------
def send_email(to_email):

    if not to_email or "@" not in to_email:
        st.error("Invalid email")
        return

    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = "Daily Skill Reminder"
    msg.set_content("Practice today and maintain your streak!")

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=context) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# ---------------- STREAK ----------------
def update_streak(user):
    today = datetime.now().strftime("%Y-%m-%d")

    s,t,last = c.execute(
        "SELECT streak,total_days,last_active FROM users WHERE username=?",
        (user,)
    ).fetchone()

    if last != today:
        s+=1
        t+=1

    c.execute(
        "UPDATE users SET streak=?,total_days=?,last_active=? WHERE username=?",
        (s,t,today,user)
    )
    conn.commit()

# ---------------- AI PLAN ----------------
def ai_plan(goal,percent):

    skills = CAREER_SKILLS[goal]

    courses = [COURSES.get(s,"Practice online") for s in skills]

    weekly = """
WEEK 1 → Fundamentals  
WEEK 2 → Practice problems  
WEEK 3 → Build project  
WEEK 4 → Mock interview  
"""

    return courses, weekly

# =========================================================
# AUTH (AUTO LOGIN)
# =========================================================
def auth():

    tab1,tab2 = st.tabs(["Login","Register"])

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
            if "@" not in e:
                st.error("Enter valid email")
                return

            c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)",
                      (u,e,hash_pw(p),0,0,""))
            conn.commit()

            st.session_state.user=u
            st.rerun()

# =========================================================
# NOT LOGGED
# =========================================================
if "user" not in st.session_state:
    auth()
    st.stop()

user=st.session_state.user

# =========================================================
# SIDEBAR
# =========================================================
if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

page=st.sidebar.radio("Menu",
["Home","Assessment","Dashboard","Leaderboard","Email Reminder"])

# =========================================================
# HOME → auto switch to assessment
# =========================================================
if page=="Home":

    goals=["Select..."]+list(CAREER_SKILLS.keys())
    g=st.selectbox("Choose Career Goal",goals,index=0)

    if g!="Select...":
        st.session_state.goal=g
        st.session_state.auto_page="Assessment"
        st.rerun()

# =========================================================
# AUTO PAGE SWITCH
# =========================================================
if "auto_page" in st.session_state:
    page=st.session_state.auto_page
    del st.session_state.auto_page

# =========================================================
# ASSESSMENT
# =========================================================
if page=="Assessment":

    goal=st.session_state.get("goal")

    if not goal:
        st.warning("Select goal first")
        st.stop()

    score=0
    total=0

    for skill in CAREER_SKILLS[goal]:
        if skill in QUIZ:
            st.subheader(skill)
            for q,opts,ans in QUIZ[skill]:
                choice=st.radio(q,opts,key=q)
                total+=1
                if choice==ans:
                    score+=1

    if st.button("Submit"):

        percent=int((score/total)*100)
        today=datetime.now().strftime("%Y-%m-%d")

        c.execute("INSERT INTO progress VALUES (?,?,?,?)",(user,goal,percent,today))
        conn.commit()

        update_streak(user)

        courses,weekly=ai_plan(goal,percent)

        st.success(f"Score: {percent}%")

        st.subheader("📚 Recommended Courses")
        for c_name in courses:
            st.write("•",c_name)

        st.subheader("🗓 Weekly Plan")
        st.code(weekly)

# =========================================================
# DASHBOARD
# =========================================================
if page=="Dashboard":

    df=pd.read_sql_query("SELECT * FROM progress WHERE username=?",conn,params=(user,))

    col1,col2,col3=st.columns(3)

    if len(df)>0:
        last=df.iloc[-1]["score"]
    else:
        last=0

    streak,total=c.execute("SELECT streak,total_days FROM users WHERE username=?",(user,)).fetchone()

    col1.metric("🔥 Streak",streak)
    col2.metric("📅 Days Active",total)
    col3.metric("📈 Last Score",f"{last}%")

    if len(df)>0:
        fig=px.line(df,x="date",y="score",markers=True,title="Progress Over Time")
        st.plotly_chart(fig,use_container_width=True)

# =========================================================
# LEADERBOARD
# =========================================================
if page=="Leaderboard":

    df=pd.read_sql_query(
        "SELECT username,streak,total_days FROM users ORDER BY streak DESC",
        conn
    )

    st.subheader("🏆 Leaderboard")

    medals=["🥇","🥈","🥉"]

    for i,row in df.iterrows():
        medal=medals[i] if i<3 else ""
        st.write(f"{medal} {row.username} — Streak {row.streak}")

# =========================================================
# EMAIL REMINDER
# =========================================================
if page=="Email Reminder":

    email=c.execute("SELECT email FROM users WHERE username=?",(user,)).fetchone()[0]

    if st.button("Send Reminder"):
        send_email(email)
        st.success("Email sent!")
