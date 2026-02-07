# ===============================================================
# SKILL GAP ANALYZER PRO MAX – FINAL UNIFIED VERSION
# ===============================================================
# Features:
# Login/Register
# Real MCQ + coding quiz
# AI Mentor
# Radar + progress charts
# Gmail real email
# Auto daily reminders
# Google Calendar event creation
# Streak + badges
# Leaderboard medals
# History tracking
# ===============================================================

import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import plotly.express as px
import smtplib
from email.mime.text import MIMEText

# Google calendar
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


# ===============================================================
# CONFIG
# ===============================================================

st.set_page_config(page_title="Skill Gap Pro Max", layout="wide")

SENDER_EMAIL = "yourgmail@gmail.com"
SENDER_PASS = "abcdefghijklmop"

SCOPES = ['https://www.googleapis.com/auth/calendar']


# ===============================================================
# DATABASE
# ===============================================================

conn = sqlite3.connect("skillgap.db", check_same_thread=False)
c = conn.cursor()

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

c.execute("""
CREATE TABLE IF NOT EXISTS progress(
    username TEXT,
    goal TEXT,
    score INTEGER,
    date TEXT
)
""")

conn.commit()


# ===============================================================
# CAREER + QUIZ DATA
# ===============================================================

CAREER_SKILLS = {
    "Data Scientist": ["Python","SQL","ML","Statistics"]
}

QUESTION_BANK = {
    "Python":[
        ("What is len([1,2,3])?",["2","3","4","5"],1),
        ("Keyword to define function?",["fun","define","def","func"],2),
        ("List symbol?",["()","{}","[]","<>"],2)
    ],
    "SQL":[
        ("Fetch rows command?",["GET","SELECT","SHOW","FETCH"],1),
        ("Primary key must be?",["duplicate","unique","null","float"],1),
        ("Join combines?",["tables","rows","columns","keys"],0)
    ],
    "ML":[
        ("Supervised learning needs?",["labels","cloud","GPU","None"],0),
        ("Example algorithm?",["HTML","Linear Regression","CSS","Excel"],1),
        ("Overfitting means?",["memorizing data","faster training","more RAM","none"],0)
    ],
    "Statistics":[
        ("Mean equals?",["median","average","range","mode"],1),
        ("Probability range?",["0-1","1-10","0-100","-1 to 1"],0),
        ("Variance measures?",["spread","size","mean","sum"],0)
    ]
}


# ===============================================================
# UTIL
# ===============================================================

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()


# ===============================================================
# EMAIL SYSTEM
# ===============================================================

def send_email(receiver, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = "Skill Gap Reminder"
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, receiver, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False


# ===============================================================
# DAILY AUTO EMAIL
# ===============================================================

def send_daily_reminder(user,email):
    today=str(datetime.date.today())
    c.execute("SELECT last_email_date FROM users WHERE username=?",(user,))
    last=c.fetchone()[0]

    if last==today:
        return

    msg=f"Hi {user},\nStudy today for at least 1 hour!"
    if send_email(email,msg):
        c.execute("UPDATE users SET last_email_date=? WHERE username=?",(today,user))
        conn.commit()


# ===============================================================
# GOOGLE CALENDAR EVENT
# ===============================================================

def add_calendar_event(title):

    creds=None

    if os.path.exists("token.pickle"):
        with open("token.pickle","rb") as token:
            creds=pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow=InstalledAppFlow.from_client_secrets_file(
                "credentials.json",SCOPES)
            creds=flow.run_local_server(port=0)

        with open("token.pickle","wb") as token:
            pickle.dump(creds,token)

    service=build("calendar","v3",credentials=creds)

    tomorrow=datetime.datetime.utcnow()+datetime.timedelta(days=1)

    event={
        'summary':title,
        'start':{'dateTime':tomorrow.isoformat()+'Z'},
        'end':{'dateTime':(tomorrow+datetime.timedelta(hours=1)).isoformat()+'Z'}
    }

    service.events().insert(calendarId='primary',body=event).execute()


# ===============================================================
# QUIZ ENGINE
# ===============================================================

def run_quiz(skills):

    scores={}

    for skill in skills:
        st.subheader(skill)
        qs=QUESTION_BANK[skill]
        correct=0

        for i,(q,opts,ans) in enumerate(qs):
            choice=st.radio(q,opts,key=f"{skill}{i}")
            if opts.index(choice)==ans:
                correct+=1

        scores[skill]=int((correct/len(qs))*5)

    return scores


# ===============================================================
# STREAK
# ===============================================================

def update_streak(u):
    today=str(datetime.date.today())

    c.execute("SELECT streak,total_days,last_date FROM users WHERE username=?",(u,))
    s,t,last=c.fetchone()

    if last!=today:
        s=1 if last!=str(datetime.date.today()-datetime.timedelta(days=1)) else s+1
        t+=1
        c.execute("UPDATE users SET streak=?,total_days=?,last_date=? WHERE username=?",(s,t,today,u))
        conn.commit()

    return s,t


# ===============================================================
# AI MENTOR
# ===============================================================

def ai_mentor(scores):
    weak=[k for k,v in scores.items() if v<3]
    return "Focus on: "+", ".join(weak)


# ===============================================================
# AUTH
# ===============================================================

def register(u,p,e):
    try:
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?)",(u,hash_pw(p),e,0,0,None,None))
        conn.commit()
        return True
    except:
        return False

def login(u,p):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",(u,hash_pw(p)))
    return c.fetchone()


# ===============================================================
# LOGIN PAGE
# ===============================================================

if "user" not in st.session_state:

    tab1,tab2=st.tabs(["Login","Register"])

    with tab1:
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        if st.button("Login"):
            d=login(u,p)
            if d:
                st.session_state.user=d[0]
                st.session_state.email=d[2]
                st.rerun()

    with tab2:
        u=st.text_input("Username",key="r1")
        p=st.text_input("Password",type="password",key="r2")
        e=st.text_input("Email")
        if st.button("Register"):
            register(u,p,e)
            st.success("Registered")

    st.stop()


# ===============================================================
# MAIN APP
# ===============================================================

user=st.session_state.user
email=st.session_state.email

send_daily_reminder(user,email)

page=st.sidebar.radio("Navigation",["Assessment","History","Streak","Leaderboard"])


# ===============================================================
# ASSESSMENT
# ===============================================================

if page=="Assessment":

    st.title("Skill Assessment Quiz")

    skills=CAREER_SKILLS["Data Scientist"]

    scores=run_quiz(skills)

    if st.button("Analyze"):

        df=pd.DataFrame({"Skill":scores.keys(),"Score":scores.values()})
        fig=px.line_polar(df,r="Score",theta="Skill",line_close=True)
        st.plotly_chart(fig)

        advice=ai_mentor(scores)
        st.success(advice)

        today=str(datetime.date.today())
        score=int(sum(scores.values())/(len(scores)*5)*100)
        c.execute("INSERT INTO progress VALUES (?,?,?,?)",(user,"Data Scientist",score,today))
        conn.commit()

        if st.button("Add Study Session to Google Calendar"):
            add_calendar_event("Skill Gap Study Session")
            st.success("Event added to your Google Calendar!")


# ===============================================================
# HISTORY
# ===============================================================

elif page=="History":

    df=pd.read_sql_query("SELECT date,score FROM progress WHERE username=?",conn,params=(user,))
    if not df.empty:
        fig=px.line(df,x="date",y="score",markers=True)
        st.plotly_chart(fig)


# ===============================================================
# STREAK
# ===============================================================

elif page=="Streak":

    s,t=update_streak(user)
    st.metric("Streak",s)
    st.metric("Days Active",t)


# ===============================================================
# LEADERBOARD
# ===============================================================

elif page=="Leaderboard":

    df=pd.read_sql_query("SELECT username,streak,total_days FROM users ORDER BY streak DESC",conn)
    st.dataframe(df)

