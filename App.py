import streamlit as st
import sqlite3
import hashlib
import smtplib
from email.mime.text import MIMEText
import pandas as pd
import plotly.express as px
from datetime import date

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="Skill Gap Pro Max", page_icon="🚀", layout="wide")

# =====================================================
# 🎨 MODERN UI
# =====================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color:white;
}
div[data-testid="metric-container"]{
    background:rgba(255,255,255,0.08);
    border-radius:12px;
    padding:12px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE + SAFE MIGRATION
# =====================================================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

# create base tables
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT,
    email TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS progress(
    username TEXT,
    goal TEXT,
    score INTEGER
)
""")

# ---- AUTO ADD MISSING COLUMNS (future proof) ----
def add_col(table, col, definition):
    c.execute(f"PRAGMA table_info({table})")
    cols = [x[1] for x in c.fetchall()]
    if col not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")

add_col("users","streak","INTEGER DEFAULT 0")
add_col("users","last_date","TEXT")
add_col("users","total_days","INTEGER DEFAULT 0")

conn.commit()

# =====================================================
# EMAIL CONFIG (PUT YOURS)
# =====================================================
SENDER_EMAIL = "yourgmail@gmail.com"
SENDER_PASS = "yourapppassword"

def send_email(receiver, msg):
    try:
        m = MIMEText(msg)
        m["Subject"] = "📚 Study Reminder"
        m["From"] = SENDER_EMAIL
        m["To"] = receiver

        s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        s.login(SENDER_EMAIL, SENDER_PASS)
        s.sendmail(SENDER_EMAIL, receiver, m.as_string())
        s.quit()
        return True
    except:
        return False

# =====================================================
# HELPERS
# =====================================================
def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def register(u,p,e):
    try:
        c.execute("INSERT INTO users(username,password,email) VALUES (?,?,?)",
                  (u,hash_pw(p),e))
        conn.commit()
        return True
    except:
        return False

def login(u,p):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (u,hash_pw(p)))
    return c.fetchone()

# SAFE INSERT (never column mismatch)
def save_progress(u,g,s):
    c.execute(
        "INSERT INTO progress(username, goal, score) VALUES (?,?,?)",
        (u,g,s)
    )
    conn.commit()

def get_history(u):
    return pd.read_sql_query(
        "SELECT goal, score FROM progress WHERE username=?",
        conn, params=(u,)
    )

# =====================================================
# STREAK SYSTEM
# =====================================================
def update_streak(user):
    today = date.today().isoformat()

    c.execute("SELECT streak,last_date,total_days FROM users WHERE username=?",(user,))
    streak,last,total = c.fetchone()

    if last != today:
        if last:
            diff = (date.fromisoformat(today)-date.fromisoformat(last)).days
            streak = streak+1 if diff==1 else 1
        else:
            streak = 1

        total += 1
        c.execute(
            "UPDATE users SET streak=?, last_date=?, total_days=? WHERE username=?",
            (streak,today,total,user)
        )
        conn.commit()

    return streak,total

def badge(streak):
    if streak>=30: return "👑 Legend"
    if streak>=15: return "💎 Pro"
    if streak>=7: return "⚡ Consistent"
    if streak>=3: return "🔥 Starter"
    return "🙂 Beginner"

# =====================================================
# DETAILED AI PLAN
# =====================================================
def generate_ai_plan(goal,gaps):
    text=f"## 🤖 Personalized Study Plan for {goal}\n\n"
    for i,g in enumerate(gaps,1):
        text+=f"""
### Week {i}: {g}
• Day 1 – Learn theory  
• Day 2 – Watch tutorials  
• Day 3 – Practice exercises  
• Day 4 – Mini project  
• Day 5 – Solve problems  
• Day 6 – Revise  
• Day 7 – Publish project  
"""
    text+="\n### Final Week: Portfolio + Resume + Apply"
    return text

# =====================================================
# AUTH (unique keys)
# =====================================================
if "user" not in st.session_state:
    st.session_state.user=None
    st.session_state.email=None

def auth():
    t1,t2=st.tabs(["Login","Register"])

    with t1:
        u=st.text_input("Username",key="lu")
        p=st.text_input("Password",type="password",key="lp")
        if st.button("Login"):
            d=login(u,p)
            if d:
                st.session_state.user=d[0]
                st.session_state.email=d[2]
                st.rerun()

    with t2:
        u=st.text_input("Username",key="ru")
        p=st.text_input("Password",type="password",key="rp")
        e=st.text_input("Email",key="re")
        if st.button("Register"):
            register(u,p,e)
            st.success("Registered!")

if not st.session_state.user:
    auth()
    st.stop()

# =====================================================
# NAVIGATION
# =====================================================
page = st.sidebar.radio("Navigation",["🏠 Home","🔥 Streak","🏆 Leaderboard"])
st.sidebar.success(f"Logged in: {st.session_state.user}")

# =====================================================
# LEADERBOARD
# =====================================================
if page=="🏆 Leaderboard":
    st.title("🏆 Leaderboard")

    df=pd.read_sql_query(
        "SELECT username, streak, total_days FROM users ORDER BY streak DESC",
        conn
    )

    medals=["🥇","🥈","🥉"]
    df.insert(0,"Medal",[medals[i] if i<3 else "" for i in range(len(df))])

    st.dataframe(df,use_container_width=True)
    st.stop()

# =====================================================
# STREAK PAGE
# =====================================================
if page=="🔥 Streak":
    st.title("🔥 Streak Dashboard")

    c.execute("SELECT streak,total_days FROM users WHERE username=?",(st.session_state.user,))
    s,t=c.fetchone()

    col1,col2,col3=st.columns(3)
    col1.metric("Current Streak",s)
    col2.metric("Total Days",t)
    col3.metric("Badge",badge(s))

    if st.button("Mark Today Completed"):
        update_streak(st.session_state.user)
        st.success("Great job!")

    st.stop()

# =====================================================
# HOME PAGE
# =====================================================
CAREER_SKILLS={
"Data Scientist":["Python","SQL","ML","Stats","Viz"],
"Web Developer":["HTML","CSS","JS","React","Backend"],
"AI Engineer":["Python","DL","ML","Math","APIs"]
}

st.title("🚀 Skill Gap Analyzer")

goal=st.selectbox("Career Goal",list(CAREER_SKILLS.keys()))
skills={s:st.slider(s,0,5,2) for s in CAREER_SKILLS[goal]}

if st.button("Analyze"):

    strengths=[s for s in CAREER_SKILLS[goal] if skills[s]>=3]
    gaps=[s for s in CAREER_SKILLS[goal] if skills[s]<3]
    score=int(len(strengths)/len(CAREER_SKILLS[goal])*100)

    col1,col2,col3=st.columns(3)
    col1.metric("Readiness",f"{score}%")
    col2.metric("Strengths",len(strengths))
    col3.metric("Gaps",len(gaps))

    st.progress(score)

    df=pd.DataFrame({"Skill":skills.keys(),"Level":skills.values()})
    st.plotly_chart(px.line_polar(df,r="Level",theta="Skill",line_close=True))

    save_progress(st.session_state.user,goal,score)

    st.markdown("---")
    st.markdown(generate_ai_plan(goal,gaps))

    if st.button("Send Reminder Email"):
        send_email(st.session_state.email,f"Today's focus: {', '.join(gaps)}")
        st.success("Reminder sent!")
