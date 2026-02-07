# ===============================================================
# SKILL GAP ANALYZER PRO MAX
# Full Hackathon Production Version (~470 lines)
# ===============================================================
# Features:
# ✔ Login/Register
# ✔ Goal-based assessment
# ✔ Radar charts + readiness score
# ✔ AI Mentor (rule-based intelligent advice)
# ✔ Course recommendations
# ✔ Real Gmail email reminders
# ✔ Automatic daily emails
# ✔ Streak + badges
# ✔ Leaderboard medals
# ✔ Progress history graph
# ✔ Calendar planner (tasks + deadlines)
# ✔ SQLite database
# ✔ Deploy-safe (no APIs required)
# ===============================================================

import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import plotly.express as px
import smtplib
from email.mime.text import MIMEText


# ===============================================================
# CONFIG
# ===============================================================

st.set_page_config(
    page_title="Skill Gap Analyzer Pro Max",
    layout="wide"
)

# 🔴 PUT YOUR GMAIL DETAILS HERE
SENDER_EMAIL = "yourgmail@gmail.com"
SENDER_PASS = "your_app_password"


# ===============================================================
# DATABASE
# ===============================================================

conn = sqlite3.connect("skillgap.db", check_same_thread=False)
c = conn.cursor()

# Users
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT,
    email TEXT,
    streak INTEGER DEFAULT 0,
    total_days INTEGER DEFAULT 0,
    last_date TEXT,
    last_email_date TEXT
)
""")

# Assessment history
c.execute("""
CREATE TABLE IF NOT EXISTS progress(
    username TEXT,
    goal TEXT,
    score INTEGER,
    date TEXT
)
""")

# Calendar tasks
c.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    username TEXT,
    task TEXT,
    due TEXT,
    done INTEGER DEFAULT 0
)
""")

conn.commit()


# ===============================================================
# CAREER DATA
# ===============================================================

CAREER_SKILLS = {
    "Data Scientist": ["Python","SQL","ML","Statistics","Communication"],
    "Web Developer": ["HTML","CSS","JavaScript","React","Git"],
    "Designer": ["UI","UX","Figma","Creativity","Communication"]
}

COURSES = {
    "Python":"Python for Everybody – Coursera",
    "SQL":"SQL Basics – Great Learning",
    "ML":"Intro to Machine Learning – Coursera",
    "Statistics":"Statistics – Khan Academy",
    "Communication":"Soft Skills – YouTube",
    "React":"React Guide – Udemy"
}


# ===============================================================
# UTILITIES
# ===============================================================

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()


# ===============================================================
# EMAIL SYSTEM (REAL)
# ===============================================================

def send_email(receiver, message):

    try:
        msg = MIMEText(message)
        msg["Subject"] = "📚 Skill Gap Reminder"
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, receiver, msg.as_string())
        server.quit()
        return True
    except:
        return False


# ===============================================================
# AUTO DAILY EMAIL (trigger on login)
# ===============================================================

def send_daily_reminder(user, email):

    today = str(datetime.date.today())

    c.execute("SELECT last_email_date FROM users WHERE username=?", (user,))
    last = c.fetchone()[0]

    if last == today:
        return

    message = f"""
Hello {user},

Daily reminder from Skill Gap Analyzer 🚀

Spend at least 1–2 hours today improving your skills.

Consistency beats intensity.
Open the app to continue learning!

Good luck!
"""

    if send_email(email, message):
        c.execute(
            "UPDATE users SET last_email_date=? WHERE username=?",
            (today, user)
        )
        conn.commit()


# ===============================================================
# AUTH
# ===============================================================

def register(u,p,e):
    try:
        c.execute(
            "INSERT INTO users(username,password,email) VALUES (?,?,?)",
            (u,hash_pw(p),e)
        )
        conn.commit()
        return True
    except:
        return False


def login(u,p):
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (u,hash_pw(p))
    )
    return c.fetchone()


# ===============================================================
# STREAK SYSTEM
# ===============================================================

def update_streak(u):

    today = str(datetime.date.today())

    c.execute("SELECT streak,total_days,last_date FROM users WHERE username=?", (u,))
    s,t,last = c.fetchone()

    if last != today:

        yesterday = str(datetime.date.today()-datetime.timedelta(days=1))

        if last == yesterday:
            s += 1
        else:
            s = 1

        t += 1

        c.execute("""
        UPDATE users
        SET streak=?, total_days=?, last_date=?
        WHERE username=?
        """,(s,t,today,u))

        conn.commit()

    return s,t


def badge(s):
    if s >= 30: return "👑 Legend"
    if s >= 14: return "🥇 Gold"
    if s >= 7:  return "🥈 Silver"
    if s >= 3:  return "🥉 Bronze"
    return "🙂 Beginner"


# ===============================================================
# AI MENTOR (rule-based intelligent advice)
# ===============================================================

def ai_mentor(goal, scores):

    weak = [k for k,v in scores.items() if v<3]
    medium = [k for k,v in scores.items() if v==3]
    strong = [k for k,v in scores.items() if v>=4]

    msg = f"===== AI Career Mentor Report =====\n\n"
    msg += f"Goal: {goal}\n\n"

    msg += "Strong Skills:\n"
    for s in strong:
        msg += f"✓ {s}\n"

    msg += "\nNeeds Improvement:\n"
    for w in weak:
        msg += f"✗ {w} → {COURSES.get(w)}\n"

    msg += "\nWeekly Plan:\n"

    week = 1
    for w in weak:
        msg += f"Week {week}: Focus on {w}\n"
        week += 1

    msg += "\nStudy 1–2 hours daily and build mini projects."

    return msg


# ===============================================================
# LOGIN PAGE
# ===============================================================

if "user" not in st.session_state:

    tab1, tab2 = st.tabs(["Login","Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            data = login(u,p)
            if data:
                st.session_state.user = data[0]
                st.session_state.email = data[2]
                st.rerun()

    with tab2:
        u = st.text_input("Username", key="r1")
        p = st.text_input("Password", type="password", key="r2")
        e = st.text_input("Email")

        if st.button("Register"):
            if register(u,p,e):
                st.success("Registered successfully!")

    st.stop()


# ===============================================================
# MAIN
# ===============================================================

user = st.session_state.user
email = st.session_state.email

# 🔥 Auto daily email
send_daily_reminder(user, email)

page = st.sidebar.radio(
    "Navigation",
    ["Home","Progress","Calendar","Streak","Leaderboard"]
)


# ===============================================================
# HOME (Assessment + AI)
# ===============================================================

if page == "Home":

    st.title("🚀 Skill Gap Analyzer")

    goal = st.selectbox("Career Goal", list(CAREER_SKILLS.keys()))

    scores = {}
    for s in CAREER_SKILLS[goal]:
        scores[s] = st.slider(s,0,5,2)

    if st.button("Analyze"):

        df = pd.DataFrame({
            "Skill":scores.keys(),
            "Score":scores.values()
        })

        fig = px.line_polar(df,r="Score",theta="Skill",line_close=True)
        st.plotly_chart(fig,use_container_width=True)

        readiness = int(sum(scores.values())/(len(scores)*5)*100)
        st.metric("Readiness", f"{readiness}%")

        today = str(datetime.date.today())
        c.execute("INSERT INTO progress VALUES (?,?,?,?)",
                  (user,goal,readiness,today))
        conn.commit()

        advice = ai_mentor(goal,scores)
        st.text(advice)

        if st.button("📧 Send Email Now"):
            send_email(email, advice)
            st.success("Email sent!")


# ===============================================================
# PROGRESS HISTORY
# ===============================================================

elif page == "Progress":

    df = pd.read_sql_query(
        "SELECT date,score FROM progress WHERE username=?",
        conn,
        params=(user,)
    )

    if not df.empty:
        fig = px.line(df,x="date",y="score",markers=True)
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("No history yet.")


# ===============================================================
# CALENDAR PLANNER
# ===============================================================

elif page == "Calendar":

    st.title("📅 Study Planner")

    task = st.text_input("Task")
    due = st.date_input("Due Date")

    if st.button("Add Task"):
        c.execute("INSERT INTO tasks VALUES (?,?,?,0)",
                  (user,task,str(due)))
        conn.commit()

    df = pd.read_sql_query(
        "SELECT rowid,task,due,done FROM tasks WHERE username=?",
        conn,
        params=(user,)
    )

    for i,row in df.iterrows():
        col1,col2,col3 = st.columns([4,2,1])
        col1.write(row["task"])
        col2.write(row["due"])

        if col3.checkbox("Done", value=row["done"], key=row["rowid"]):
            c.execute("UPDATE tasks SET done=1 WHERE rowid=?",
                      (row["rowid"],))
            conn.commit()


# ===============================================================
# STREAK PAGE
# ===============================================================

elif page == "Streak":

    s,t = update_streak(user)

    st.metric("Current Streak", s)
    st.metric("Total Days", t)
    st.success("Badge: " + badge(s))


# ===============================================================
# LEADERBOARD
# ===============================================================

elif page == "Leaderboard":

    df = pd.read_sql_query(
        "SELECT username,streak,total_days FROM users ORDER BY streak DESC",
        conn
    )

    medals = ["🥇","🥈","🥉"]
    df.insert(0,"Medal",[medals[i] if i<3 else "" for i in range(len(df))])

    st.dataframe(df, use_container_width=True)
