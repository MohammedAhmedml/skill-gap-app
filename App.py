# =========================================================
# SKILL GAP ANALYZER – FINAL MASTER BUILD
# Cloud-safe • Auto login • Quiz • AI • Email • Leaderboard
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
# CONFIG
# =========================================================

st.set_page_config(page_title="Skill Gap Analyzer", layout="wide")

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

QUIZ = {
"Python":[
("len([1,2,3]) ?",["2","3","4","5"],"3"),
("Keyword for function?",["fun","define","def","func"],"def")
],
"SQL":[
("SELECT returns?",["rows","files","tables","none"],"rows")
]
}

# =========================================================
# HELPERS
# =========================================================

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- EMAIL ----------------
def send_email(to_email, subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        st.error("Email secrets missing")
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

# ---------------- STREAK ----------------
def update_streak(user):
    today = datetime.now().strftime("%Y-%m-%d")

    row = c.execute(
        "SELECT streak,total_days,last_active FROM users WHERE username=?",
        (user,)
    ).fetchone()

    streak,total,last = row

    if last != today:
        streak += 1
        total += 1

    c.execute("""
    UPDATE users SET streak=?, total_days=?, last_active=? WHERE username=?
    """,(streak,total,today,user))

    conn.commit()

# ---------------- AI PLAN ----------------
def ai_plan(goal, percent):
    if percent >= 80:
        return "Excellent! Start building real projects."

    return f"""
🚀 Personalized Plan for {goal}

• Practice weak skills daily
• Complete 2 courses
• Build 3 mini projects
• Study 1–2 hrs daily
• Retake test in 2 weeks
"""

# =========================================================
# AUTH (AUTO LOGIN INCLUDED)
# =========================================================

def auth():

    tab1, tab2 = st.tabs(["Login", "Register"])

    # -------- LOGIN --------
    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")

        if st.button("Login"):

            row = c.execute(
                "SELECT password FROM users WHERE username=?",
                (u.strip(),)
            ).fetchone()

            if row and row[0] == hash_pw(p.strip()):
                st.session_state.user = u.strip()
                st.rerun()
            else:
                st.error("Invalid login")

    # -------- REGISTER + AUTO LOGIN --------
    with tab2:
        u = st.text_input("Username", key="reg_u")
        e = st.text_input("Email", key="reg_e")
        p = st.text_input("Password", type="password", key="reg_p")

        if st.button("Register"):

            c.execute("""
            INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)
            """,(u.strip(), e.strip(), hash_pw(p.strip()), 0, 0, ""))

            conn.commit()

            # 🔥 auto login
            st.session_state.user = u.strip()
            st.success("Registered & logged in!")
            st.rerun()

# =========================================================
# IF NOT LOGGED
# =========================================================

if "user" not in st.session_state:
    auth()
    st.stop()

user = st.session_state.user

# =========================================================
# SIDEBAR
# =========================================================

if st.sidebar.button("Logout"):
    del st.session_state["user"]
    st.rerun()

page = st.sidebar.radio(
"Navigation",
["Home","Assessment","Dashboard","Leaderboard","Email Reminder"]
)

# =========================================================
# HOME
# =========================================================

if page == "Home":

    st.title("🚀 Skill Gap Analyzer")

    goals = ["Select your career goal..."] + list(CAREER_SKILLS.keys())

    goal = st.selectbox("Choose Career Goal", goals, index=0)

    if goal != "Select your career goal...":
        st.session_state.goal = goal
        st.success("Goal selected!")

# =========================================================
# ASSESSMENT QUIZ
# =========================================================

if page == "Assessment":

    goal = st.session_state.get("goal")

    if not goal:
        st.warning("Select goal first")
        st.stop()

    score = 0
    total = 0

    for skill in CAREER_SKILLS[goal]:
        if skill in QUIZ:
            st.subheader(skill)
            for q,opts,ans in QUIZ[skill]:
                choice = st.radio(q,opts,key=q)
                total += 1
                if choice == ans:
                    score += 1

    if st.button("Submit Test"):

        percent = int((score/total)*100)

        today = datetime.now().strftime("%Y-%m-%d")

        c.execute("INSERT INTO progress VALUES (?,?,?,?)",
                  (user,goal,percent,today))
        conn.commit()

        update_streak(user)

        st.success(f"Score: {percent}%")
        st.info(ai_plan(goal, percent))

# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    df = pd.read_sql_query(
        "SELECT * FROM progress WHERE username=?",
        conn, params=(user,)
    )

    if len(df)>0:
        fig = px.line(df, x="date", y="score", title="Progress")
        st.plotly_chart(fig, use_container_width=True)

    row = c.execute(
        "SELECT streak,total_days FROM users WHERE username=?",
        (user,)
    ).fetchone()

    st.metric("🔥 Streak", row[0])
    st.metric("📅 Days Active", row[1])

# =========================================================
# LEADERBOARD
# =========================================================

if page == "Leaderboard":

    df = pd.read_sql_query(
        "SELECT username,streak,total_days FROM users ORDER BY streak DESC",
        conn
    )

    st.dataframe(df)

# =========================================================
# EMAIL REMINDER
# =========================================================

if page == "Email Reminder":

    email = c.execute(
        "SELECT email FROM users WHERE username=?",
        (user,)
    ).fetchone()[0]

    if st.button("Send Reminder"):
        send_email(email,
                   "Daily Study Reminder",
                   "Practice today and maintain your streak!")
        st.success("Email sent!")
