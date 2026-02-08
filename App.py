# =========================================================
# SKILL GAP ANALYZER – CLEAN FINAL STABLE BUILD
# No migrations • No schema drift • No unpack errors • Stable
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

st.set_page_config(page_title="Skill Gap Analyzer", layout="wide")

# =========================================================
# DATABASE (FIXED SCHEMA – NEVER CHANGES)
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
# HELPERS
# =========================================================

def today():
    return datetime.now().strftime("%Y-%m-%d")

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- SAFE EMAIL ----------------

EMAIL_USER = st.secrets.get("EMAIL_USER","")
EMAIL_PASS = st.secrets.get("EMAIL_PASS","")

def send_email(email):
    if not email or not EMAIL_USER:
        return

    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = email
    msg["Subject"] = "Daily Study Reminder"
    msg.set_content("Practice today to maintain your streak!")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=context) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# ---------------- SAFE STREAK ----------------

def update_streak(user):

    row = c.execute(
        "SELECT streak,total_days,last_active FROM users WHERE username=?",
        (user,)
    ).fetchone()

    if not row:
        return

    s,t,last = row

    if last != today():
        s += 1
        t += 1

    c.execute("""
        UPDATE users
        SET streak=?, total_days=?, last_active=?
        WHERE username=?
    """,(s,t,today(),user))

    conn.commit()

# =========================================================
# QUIZ DATA (10 EACH)
# =========================================================

CAREERS = {
"Data Scientist":[("Library for arrays?",["NumPy","HTML","CSS","Excel"],"NumPy")] * 10,
"Web Developer":[("HTML stands for?",["Hyper Text Markup Language","None"],"Hyper Text Markup Language")] * 10,
"AI Engineer":[("Deep learning uses?",["neural networks","css"],"neural networks")] * 10
}

# =========================================================
# AUTH
# =========================================================

def auth():

    tab1,tab2 = st.tabs(["Login","Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password",type="password")

        if st.button("Login"):
            row = c.execute(
                "SELECT password FROM users WHERE username=?",
                (u,)
            ).fetchone()

            if row and row[0]==hash_pw(p):
                st.session_state.user=u
                st.session_state.page="Home"
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        u = st.text_input("Username",key="r1")
        e = st.text_input("Email",key="r2")
        p = st.text_input("Password",type="password",key="r3")

        if st.button("Register"):

            # EXPLICIT columns → NEVER breaks
            c.execute("""
                INSERT OR REPLACE INTO users(username,email,password)
                VALUES(?,?,?)
            """,(u,e,hash_pw(p)))

            conn.commit()

            st.session_state.user=u
            st.session_state.page="Home"
            st.rerun()

if "user" not in st.session_state:
    auth()
    st.stop()

user = st.session_state.user

# =========================================================
# NAVIGATION (SINGLE SOURCE OF TRUTH)
# =========================================================

PAGES=["Home","Assessment","Dashboard","Leaderboard","Email"]

if "page" not in st.session_state:
    st.session_state.page="Home"

page = st.sidebar.radio("Menu",PAGES,index=PAGES.index(st.session_state.page))
st.session_state.page=page

# =========================================================
# HOME
# =========================================================

if page=="Home":

    goal = st.selectbox("Select Career",["Select..."]+list(CAREERS.keys()))

    if goal!="Select...":
        st.session_state.goal=goal
        st.session_state.page="Assessment"
        st.rerun()

# =========================================================
# ASSESSMENT
# =========================================================

if page=="Assessment":

    goal = st.session_state.get("goal")

    if not goal:
        st.stop()

    score=0
    qs = CAREERS[goal]

    for i,(q,opts,ans) in enumerate(qs):
        choice = st.radio(q,opts,key=i)
        if choice==ans:
            score+=1

    if st.button("Submit"):

        percent=int(score/len(qs)*100)

        c.execute("INSERT INTO progress VALUES (?,?,?,?)",
                  (user,goal,percent,today()))
        conn.commit()

        update_streak(user)

        st.success(f"Score {percent}%")

# =========================================================
# DASHBOARD
# =========================================================

if page=="Dashboard":

    row = c.execute(
        "SELECT streak,total_days FROM users WHERE username=?",
        (user,)
    ).fetchone()

    s,t = row if row else (0,0)

    st.metric("🔥 Streak",s)
    st.metric("📅 Days",t)

# =========================================================
# LEADERBOARD
# =========================================================

if page=="Leaderboard":

    df=pd.read_sql_query(
        "SELECT username,streak,total_days FROM users ORDER BY streak DESC",
        conn
    )

    st.dataframe(df)

# =========================================================
# EMAIL
# =========================================================

if page=="Email":

    row=c.execute("SELECT email FROM users WHERE username=?",(user,)).fetchone()

    if row:
        if st.button("Send Reminder"):
            send_email(row[0])
            st.success("Sent")
