# ==========================================================
# SKILL GAP ANALYZER – CLOUD SAFE VERSION
# No dotenv • Only st.secrets • Streamlit Cloud ready
# ==========================================================

import streamlit as st
import sqlite3
import hashlib
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime
import pandas as pd
import plotly.express as px

# ==========================================================
# PAGE
# ==========================================================
st.set_page_config(page_title="Skill Gap Analyzer", layout="wide")

# ==========================================================
# EMAIL (Cloud safe)
# ==========================================================
EMAIL_USER = st.secrets.get("EMAIL_USER")
EMAIL_PASS = st.secrets.get("EMAIL_PASS")

# ==========================================================
# DATABASE
# ==========================================================
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

# ==========================================================
# DATA
# ==========================================================
CAREER_SKILLS = {
"Data Scientist": ["Python","SQL","ML","Statistics","Visualization"],
"Web Developer": ["HTML","CSS","JavaScript","React","Backend"],
"AI Engineer": ["Python","ML","DL","Math"]
}

QUIZ = {
"Python":[
("len([1,2,3]) ?",["2","3","4","5"],"3"),
("Keyword to define function?",["fun","define","def","func"],"def"),
("List symbol?",["()","{}","[]","<>"],"[]")
],
"SQL":[
("SELECT returns?",["rows","tables","files","columns"],"rows"),
("Filter keyword?",["WHERE","WHEN","FILTER","IF"],"WHERE")
]
}

# ==========================================================
# HELPERS
# ==========================================================

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def send_email(to_email, subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        st.error("Email secrets missing in Streamlit settings")
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

def ai_recommend(goal,gaps):

    text = f"""
🚀 Personalized Skill Plan for {goal}

You are currently weak in:
{", ".join(gaps)}

Recommended steps:

1️⃣ Learn fundamentals  
2️⃣ Watch tutorials  
3️⃣ Practice daily coding  
4️⃣ Build mini projects  
5️⃣ Track progress  

Daily time: 1–2 hours  
Expected improvement: 30 days
"""

    return text

# ==========================================================
# AUTH
# ==========================================================

def auth():

    tab1,tab2 = st.tabs(["Login","Register"])

    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")

        if st.button("Login"):
            row = c.execute("SELECT password FROM users WHERE username=?",(u,)).fetchone()

            if row and row[0]==hash_pw(p):
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        u = st.text_input("Username", key="reg_u")
        e = st.text_input("Email", key="reg_e")
        p = st.text_input("Password", type="password", key="reg_p")

        if st.button("Register"):
            c.execute("INSERT OR REPLACE INTO users VALUES(?,?,?,?,?,?)",
                      (u,e,hash_pw(p),0,0,""))
            conn.commit()
            st.success("Registered successfully")

# ==========================================================
# NOT LOGGED
# ==========================================================
if "user" not in st.session_state:
    auth()
    st.stop()

user = st.session_state.user

# ==========================================================
# SIDEBAR
# ==========================================================
page = st.sidebar.radio(
"Navigation",
["Home","Assessment","Dashboard","Leaderboard","Email Reminder"]
)

# ==========================================================
# HOME
# ==========================================================
if page=="Home":

    st.title("🚀 Skill Gap Analyzer")

    goals = ["Select your career goal..."] + list(CAREER_SKILLS.keys())

    goal = st.selectbox("Choose Career Goal", goals, index=0)

    if goal=="Select your career goal...":
        st.stop()

    st.session_state.goal = goal
    st.success("Goal selected")

# ==========================================================
# ASSESSMENT
# ==========================================================
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
        if percent<70:
            gaps = CAREER_SKILLS[goal]

        plan = ai_recommend(goal,gaps)

        st.success(f"Score: {percent}%")
        st.info(plan)

        today = datetime.now().strftime("%Y-%m-%d")

        c.execute("INSERT INTO progress VALUES(?,?,?,?)",
                  (user,goal,percent,today))
        conn.commit()

        update_streak(user)

# ==========================================================
# DASHBOARD
# ==========================================================
if page=="Dashboard":

    df = pd.read_sql_query(
        "SELECT * FROM progress WHERE username=?",
        conn,
        params=(user,)
    )

    if len(df)>0:
        fig = px.line(df,x="date",y="score",title="Progress Over Time")
        st.plotly_chart(fig,use_container_width=True)

    row = c.execute(
        "SELECT streak,total_days FROM users WHERE username=?",
        (user,)
    ).fetchone()

    st.metric("🔥 Streak",row[0])
    st.metric("📅 Total Days",row[1])

# ==========================================================
# LEADERBOARD
# ==========================================================
if page=="Leaderboard":

    df = pd.read_sql_query(
        "SELECT username,streak,total_days FROM users ORDER BY streak DESC",
        conn
    )

    st.dataframe(df)

# ==========================================================
# EMAIL REMINDER
# ==========================================================
if page=="Email Reminder":

    email = c.execute(
        "SELECT email FROM users WHERE username=?",
        (user,)
    ).fetchone()[0]

    st.write("Your email:",email)

    if st.button("Send Reminder Now"):
        send_email(
            email,
            "Daily Skill Reminder",
            "Practice today and maintain your streak!"
        )
        st.success("Reminder sent")
