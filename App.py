# =========================================================
# SKILL GAP ANALYZER PRO MAX – FINAL STABLE ALL-IN-ONE
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
# EMAIL SECRETS (Streamlit Cloud)
# =========================================================
EMAIL_USER = st.secrets.get("EMAIL_USER", "")
EMAIL_PASS = st.secrets.get("EMAIL_PASS", "")

# =========================================================
# DATABASE (AUTO SAFE MIGRATION – NEVER BREAKS)
# =========================================================

conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

# minimal base
c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
email TEXT,
password TEXT
)
""")

def add(col, typ):
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
    except:
        pass

add("streak","INTEGER DEFAULT 0")
add("total_days","INTEGER DEFAULT 0")
add("last_active","TEXT")

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

# ---------------- EMAIL ----------------
def send_email(email):

    if not EMAIL_USER or not EMAIL_PASS:
        st.error("Email not configured in secrets")
        return

    if not email or "@" not in email:
        st.error("Invalid email")
        return

    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = email
    msg["Subject"] = "Daily Study Reminder"
    msg.set_content("Practice today to maintain your streak!")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# ---------------- STREAK ----------------
def update_streak(user):

    row = c.execute(
        "SELECT streak,total_days,last_active FROM users WHERE username=?",
        (user,)
    ).fetchone()

    if row is None:
        return

    s = row[0] or 0
    t = row[1] or 0
    last = row[2]

    if last != today():
        s += 1
        t += 1

    c.execute(
        "UPDATE users SET streak=?,total_days=?,last_active=? WHERE username=?",
        (s,t,today(),user)
    )
    conn.commit()

# =========================================================
# QUIZ DATA (10 EACH)
# =========================================================

CAREERS = {
"Data Scientist":[
("Library for arrays?",["NumPy","HTML","CSS","Excel"],"NumPy"),
("SQL filter keyword?",["WHERE","JOIN","GROUP","SORT"],"WHERE"),
("Regression predicts?",["numbers","labels","text","audio"],"numbers"),
("Mean equals?",["average","mode","sum","range"],"average"),
("Visualization tool?",["Plotly","Docker","Linux","Git"],"Plotly"),
("Overfitting means?",["memorizing","generalizing","testing","none"],"memorizing"),
("Pandas handles?",["dataframes","images","servers","none"],"dataframes"),
("Probability range?",["0-1","1-100","10-20","none"],"0-1"),
("Classification predicts?",["labels","numbers","none","text"],"labels"),
("Feature means?",["input variable","output","model","loss"],"input variable")
],

"Web Developer":[
("HTML stands for?",["Hyper Text Markup Language","Home Tool","None","Markup Tool"],"Hyper Text Markup Language"),
("CSS used for?",["styling","database","backend","math"],"styling"),
("JS used for?",["interactivity","design","storage","none"],"interactivity"),
("Tag for link?",["<a>","<p>","<div>","<h1>"],"<a>"),
("React is?",["framework","db","os","browser"],"framework"),
("NodeJS runs on?",["server","design","css","none"],"server"),
("Git is for?",["version control","hosting","design","none"],"version control"),
("HTTP GET does?",["fetch data","delete","update","none"],"fetch data"),
("Database example?",["MongoDB","HTML","CSS","Figma"],"MongoDB"),
("Flexbox is?",["layout system","python lib","ai model","none"],"layout system")
],

"AI Engineer":[
("Deep learning uses?",["neural networks","css","html","excel"],"neural networks"),
("GPU helps in?",["training faster","styling","hosting","none"],"training faster"),
("NLP means?",["Natural Language Processing","None","Link","Logic"],"Natural Language Processing"),
("TensorFlow is?",["framework","db","os","browser"],"framework"),
("CNN best for?",["images","text","audio","none"],"images"),
("Loss measures?",["error","speed","size","none"],"error"),
("Gradient descent is?",["optimization","storage","design","none"],"optimization"),
("Dataset split?",["train/test","cpu/gpu","css/html","none"],"train/test"),
("Activation adds?",["non-linearity","speed","color","none"],"non-linearity"),
("Overfitting equals?",["memorizing","learning","generalizing","none"],"memorizing")
]
}

COURSES = {
"Data Scientist":["Coursera ML","Kaggle Practice","Statistics Khan Academy"],
"Web Developer":["FreeCodeCamp","React Docs","NodeJS Guide"],
"AI Engineer":["Deep Learning Course","TensorFlow Docs","HuggingFace NLP"]
}

# =========================================================
# AUTH
# =========================================================

def auth():

    tab1,tab2 = st.tabs(["Login","Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            row = c.execute("SELECT password FROM users WHERE username=?", (u,)).fetchone()
            if row and row[0] == hash_pw(p):
                st.session_state.user = u
                st.session_state.page = "Home"
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        u = st.text_input("Username", key="r1")
        e = st.text_input("Email", key="r2")
        p = st.text_input("Password", type="password", key="r3")

        if st.button("Register"):
            c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)",
                      (u,e,hash_pw(p),0,0,""))
            conn.commit()

            st.session_state.user = u
            st.session_state.page = "Home"
            st.rerun()

if "user" not in st.session_state:
    auth()
    st.stop()

user = st.session_state.user

# =========================================================
# STABLE NAVIGATION
# =========================================================

PAGES = ["Home","Assessment","Dashboard","Leaderboard","Email Reminder"]

if "page" not in st.session_state:
    st.session_state.page = "Home"

page = st.sidebar.radio("Navigation", PAGES, index=PAGES.index(st.session_state.page))
st.session_state.page = page

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

# =========================================================
# HOME
# =========================================================

if page == "Home":
    st.title("🚀 Skill Gap Analyzer")

    goal = st.selectbox("Choose Career Goal", ["Select..."]+list(CAREERS.keys()))

    if goal != "Select...":
        st.session_state.goal = goal
        st.session_state.page = "Assessment"
        st.rerun()

# =========================================================
# ASSESSMENT
# =========================================================

if page == "Assessment":

    goal = st.session_state.get("goal")
    if not goal:
        st.warning("Select goal first")
        st.stop()

    questions = CAREERS[goal]
    score = 0

    for i,(q,opts,ans) in enumerate(questions):
        choice = st.radio(f"Q{i+1}. {q}", opts, key=f"{goal}_{i}")
        if choice == ans:
            score += 1

    if st.button("Submit Assessment"):
        percent = int(score/len(questions)*100)

        c.execute("INSERT INTO progress VALUES (?,?,?,?)",
                  (user,goal,percent,today()))
        conn.commit()

        update_streak(user)

        st.success(f"Score: {percent}%")

        st.subheader("📚 Courses")
        for course in COURSES[goal]:
            st.write("•", course)

# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    df = pd.read_sql_query("SELECT * FROM progress WHERE username=?", conn, params=(user,))

    row = c.execute(
        "SELECT streak,total_days FROM users WHERE username=?",
        (user,)
    ).fetchone()

    s,t = (row if row else (0,0))

    st.metric("🔥 Streak", s)
    st.metric("📅 Active Days", t)

    if len(df) > 0:
        fig = px.line(df, x="date", y="score", markers=True)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# LEADERBOARD
# =========================================================

if page == "Leaderboard":

    df = pd.read_sql_query(
        "SELECT username,streak,total_days FROM users ORDER BY streak DESC",
        conn
    )

    medals = ["🥇","🥈","🥉"]
    rows=[]

    for i,row in df.iterrows():
        rows.append([i+1, medals[i] if i<3 else "", row.username, row.streak, row.total_days])

    display = pd.DataFrame(rows, columns=["Rank","Medal","User","Streak","Days"])
    st.dataframe(display, use_container_width=True)

# =========================================================
# EMAIL
# =========================================================

if page == "Email Reminder":

    row = c.execute(
        "SELECT email FROM users WHERE username=?",
        (user,)
    ).fetchone()

    if row is None:
        st.error("No email found")
    else:
        email = row[0]

        if st.button("Send Reminder"):
            send_email(email)
            st.success("Reminder sent!")
