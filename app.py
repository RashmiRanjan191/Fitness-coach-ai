import os
import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st
from openai import OpenAI

from avatar import render_avatar

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "kinetic_coach.db"

st.set_page_config(
    page_title="Kinetic Coach | AI Fitness Companion",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #f7fbff 0%, #ffffff 50%, #f7fbff 100%);
    }
    .hero {
        padding: 2rem 2.2rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #102a43 0%, #1f5f8b 100%);
        color: white;
        margin-bottom: 1rem;
    }
    .hero h1 { margin-bottom: .35rem; font-size: 2.5rem; }
    .hero p { font-size: 1.08rem; opacity: .92; }
    .pill {
        display:inline-block;
        padding:.35rem .7rem;
        border-radius:999px;
        background:#e7f5ff;
        color:#145374;
        font-size:.82rem;
        font-weight:700;
        margin-right:.35rem;
    }
    .card {
        background:white;
        border:1px solid #e7eef5;
        border-radius:18px;
        padding:1.1rem;
        box-shadow:0 5px 18px rgba(16,42,67,.06);
        margin-bottom:.8rem;
    }
    .score {
        font-size:3.1rem;
        font-weight:800;
        color:#145374;
        line-height:1;
    }
    .muted { color:#66788a; font-size:.92rem; }
    .small-note {
        font-size:.8rem;
        color:#718096;
        margin-top:.5rem;
    }
    [data-testid="stMetricValue"] { font-size: 1.65rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Database / analytics
# -----------------------------
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            event TEXT NOT NULL,
            session_id TEXT,
            metadata TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            session_id TEXT,
            rating INTEGER,
            would_return TEXT,
            useful_part TEXT,
            improvement TEXT,
            avatar_helped TEXT
        )
    """)
    conn.commit()
    return conn

CONN = db()

def log_event(event, metadata=None):
    try:
        CONN.execute(
            "INSERT INTO events(ts,event,session_id,metadata) VALUES(?,?,?,?)",
            (
                datetime.utcnow().isoformat(),
                event,
                st.session_state.get("session_id", ""),
                json.dumps(metadata or {}),
            ),
        )
        CONN.commit()
    except Exception:
        pass

def save_feedback(rating, would_return, useful_part, improvement, avatar_helped):
    CONN.execute(
        """INSERT INTO feedback
        (ts,session_id,rating,would_return,useful_part,improvement,avatar_helped)
        VALUES(?,?,?,?,?,?,?)""",
        (
            datetime.utcnow().isoformat(),
            st.session_state.get("session_id", ""),
            rating,
            would_return,
            useful_part,
            improvement,
            avatar_helped,
        ),
    )
    CONN.commit()
    log_event("feedback_submitted", {"rating": rating, "would_return": would_return})

# -----------------------------
# AI
# -----------------------------
def get_secret(name, default=""):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
MODEL = get_secret("OPENAI_MODEL", "gpt-5.6-luna")

SYSTEM_PROMPT = """
You are Kinetic Coach, a friendly AI fitness companion.

Your job is to help users build small, realistic movement habits.
You are NOT a doctor and must not diagnose disease, estimate medical conditions,
or make claims about biological age or medical fitness.

Rules:
- Be concise, warm, practical and motivating.
- Personalize advice using the user's stated goal, activity level and constraints.
- Prefer small actions that can be completed today.
- Never shame the user.
- Do not recommend dangerous exercise, extreme dieting, supplements, or medication.
- If the user mentions chest pain, fainting, severe shortness of breath, serious injury,
  or another urgent symptom, tell them to stop exercising and seek appropriate medical care.
- Make clear that you are AI when relevant.
- Avoid collecting sensitive personal information.
"""

def ai_response(user_text, context="", history=None):
    if not OPENAI_API_KEY:
        return (
            "I’m currently in demo mode because no OpenAI API key is configured. "
            "You can still explore the product, and the app will use the built-in "
            "demo coach for the assessment."
        )

    client = OpenAI(api_key=OPENAI_API_KEY)
    history = history or []
    recent = history[-8:]
    conversation = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in recent
    )

    prompt = f"""
USER PROFILE:
{context}

RECENT CONVERSATION:
{conversation}

CURRENT USER MESSAGE:
{user_text}

Respond as Kinetic Coach. Give a direct, useful answer in 2-5 short paragraphs
or bullets. Do not over-explain.
"""

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=prompt,
        )
        return response.output_text.strip()
    except Exception as exc:
        return (
            "I couldn't reach the AI service right now. "
            "Please check the API key/model configuration. "
            f"Technical detail: {type(exc).__name__}"
        )

def calculate_score(activity, sleep, energy, sitting, consistency):
    activity_points = {
        "Rarely / almost never": 10,
        "1–2 days/week": 25,
        "3–4 days/week": 40,
        "5+ days/week": 50,
    }
    sleep_points = {
        "Less than 5 hours": 5,
        "5–6 hours": 10,
        "6–7 hours": 15,
        "7–9 hours": 20,
        "More than 9 hours": 17,
    }
    energy_points = {"Low": 4, "Okay": 8, "Good": 13, "Excellent": 15}
    sitting_points = {
        "Less than 3 hours": 10,
        "3–5 hours": 8,
        "5–8 hours": 5,
        "More than 8 hours": 2,
    }
    consistency_points = {
        "Not at all": 1,
        "Sometimes": 3,
        "Most weeks": 5,
        "Almost every week": 5,
    }
    score = (
        activity_points[activity]
        + sleep_points[sleep]
        + energy_points[energy]
        + sitting_points[sitting]
        + consistency_points[consistency]
    )
    return max(0, min(100, score))

def score_label(score):
    if score >= 80:
        return "Strong foundation"
    if score >= 60:
        return "Good starting point"
    if score >= 40:
        return "Room to improve"
    return "Let's build the basics"

def build_plan(profile, score):
    goal = profile["goal"]
    activity = profile["activity"]
    sitting = profile["sitting"]

    if goal == "Build a consistent exercise habit":
        focus = "consistency"
    elif goal == "Improve energy and daily movement":
        focus = "daily movement"
    elif goal == "Improve strength":
        focus = "strength"
    elif goal == "Improve flexibility / mobility":
        focus = "mobility"
    else:
        focus = "overall movement"

    plan = [
        "2 min — easy warm-up: shoulder rolls, marching and gentle mobility",
        "3 min — movement block: bodyweight squats + wall push-ups",
        "2 min — brisk walk or marching in place",
        "2 min — mobility: hips, upper back and ankles",
        "1 min — slow breathing and cooldown",
    ]

    if sitting == "More than 8 hours":
        micro = "Every 60–90 minutes, take a 2-minute movement break."
    elif sitting == "5–8 hours":
        micro = "Add 2–3 short movement breaks during your work/study day."
    else:
        micro = "Keep one short movement break between long study/work blocks."

    return {
        "focus": focus,
        "plan": plan,
        "micro": micro,
        "score": score,
        "label": score_label(score),
        "goal": goal,
        "activity": activity,
    }

# -----------------------------
# Session state
# -----------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    log_event("session_started")

if "profile" not in st.session_state:
    st.session_state.profile = None
if "plan" not in st.session_state:
    st.session_state.plan = None
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I’m Kinetic Coach 👋 I’m an AI fitness companion. "
                "Start with the quick check-in and I’ll turn your answers into "
                "a simple plan you can actually use today."
            ),
        }
    ]

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## 🏃 Kinetic Coach")
    st.caption("AI-powered movement companion")
    st.divider()
    st.markdown("### MVP flow")
    st.markdown(
        "1. Quick check-in\n"
        "2. Get a readiness snapshot\n"
        "3. Receive a 10-minute plan\n"
        "4. Chat with the AI avatar\n"
        "5. Give feedback"
    )
    st.divider()
    st.caption("AI transparency")
    st.caption(
        "You are interacting with AI. This product is for general wellness "
        "and habit support, not medical diagnosis or treatment."
    )

# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div class="hero">
  <span class="pill">AI AVATAR MVP</span>
  <span class="pill">PERSONALIZED COACHING</span>
  <h1>Kinetic Coach</h1>
  <p>A conversational AI fitness companion that turns a few simple answers into a realistic movement plan.</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(
    ["🏠 Check-in", "🤖 AI Coach", "📈 Progress", "💬 Feedback"]
)

# -----------------------------
# Check-in
# -----------------------------
with tab1:
    col1, col2 = st.columns([1.05, 1.6])

    with col1:
        st.markdown("### Meet your coach")
        render_avatar(
            "Hi! I’m Kinetic Coach. Complete the quick check-in and I’ll build a small plan for you.",
            height=370,
        )

    with col2:
        st.markdown("### 60-second movement check-in")
        st.caption("No sensitive health information is required.")

        with st.form("assessment_form"):
            age_range = st.selectbox(
                "Age range",
                ["18–24", "25–34", "35–44", "45+"],
            )
            goal = st.selectbox(
                "What is your main goal?",
                [
                    "Build a consistent exercise habit",
                    "Improve energy and daily movement",
                    "Improve strength",
                    "Improve flexibility / mobility",
                    "General fitness",
                ],
            )
            activity = st.selectbox(
                "How often do you currently exercise?",
                [
                    "Rarely / almost never",
                    "1–2 days/week",
                    "3–4 days/week",
                    "5+ days/week",
                ],
            )
            sleep = st.selectbox(
                "Typical sleep duration",
                [
                    "Less than 5 hours",
                    "5–6 hours",
                    "6–7 hours",
                    "7–9 hours",
                    "More than 9 hours",
                ],
            )
            energy = st.select_slider(
                "How is your usual energy?",
                options=["Low", "Okay", "Good", "Excellent"],
                value="Okay",
            )
            sitting = st.selectbox(
                "Approximate daily sitting time",
                [
                    "Less than 3 hours",
                    "3–5 hours",
                    "5–8 hours",
                    "More than 8 hours",
                ],
            )
            consistency = st.selectbox(
                "How consistent are you with your movement goal?",
                ["Not at all", "Sometimes", "Most weeks", "Almost every week"],
            )

            submitted = st.form_submit_button(
                "✨ Create my Kinetic Plan",
                use_container_width=True,
            )

        if submitted:
            profile = {
                "age_range": age_range,
                "goal": goal,
                "activity": activity,
                "sleep": sleep,
                "energy": energy,
                "sitting": sitting,
                "consistency": consistency,
            }
            score = calculate_score(activity, sleep, energy, sitting, consistency)
            plan = build_plan(profile, score)
            st.session_state.profile = profile
            st.session_state.plan = plan
            log_event("assessment_completed", {"score": score, "goal": goal})
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        f"Your Kinetic readiness snapshot is **{score}/100 — {score_label(score)}**. "
                        f"Your main focus is **{plan['focus']}**. I’ve created a 10-minute starter plan "
                        "below. Ask me anything about adapting it."
                    ),
                }
            )
            st.success("Your personalized plan is ready.")

    if st.session_state.plan:
        plan = st.session_state.plan
        st.divider()
        st.markdown("## Your Kinetic snapshot")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="card"><div class="muted">Readiness snapshot</div><div class="score">{plan["score"]}</div><div>{plan["label"]}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card"><div class="muted">Primary focus</div><h3>{plan["focus"].title()}</h3><div>{plan["goal"]}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card"><div class="muted">Daily movement cue</div><h3>Small & consistent</h3><div>{plan["micro"]}</div></div>', unsafe_allow_html=True)

        st.markdown("### Today's 10-minute starter plan")
        for i, item in enumerate(plan["plan"], 1):
            st.markdown(f"**{i}. {item}**")

        st.info(
            "Wellness note: this is a general AI-generated habit plan, not medical advice. "
            "Stop if an activity causes pain or concerning symptoms."
        )

# -----------------------------
# Coach
# -----------------------------
with tab2:
    left, right = st.columns([1, 1.65])

    with left:
        st.markdown("### 🤖 Your AI avatar")
        last_text = st.session_state.messages[-1]["content"]
        render_avatar(last_text, height=430)

    with right:
        st.markdown("### Talk to Kinetic Coach")
        st.caption("Ask about your plan, motivation, time constraints, or how to adapt a session.")

        for msg in st.session_state.messages:
            with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
                st.markdown(msg["content"])

        prompt = st.chat_input("e.g. I only have 5 minutes today...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            profile_text = json.dumps(st.session_state.profile or {}, indent=2)
            answer = ai_response(
                prompt,
                context=profile_text,
                history=st.session_state.messages,
            )
            st.session_state.messages.append({"role": "assistant", "content": answer})
            log_event("avatar_chat", {"message_length": len(prompt)})
            st.rerun()

# -----------------------------
# Progress / evidence
# -----------------------------
with tab3:
    st.markdown("### 📈 Product usage signals")
    st.caption(
        "These are MVP analytics for validation. Do not present numbers as traction "
        "until you have real users interacting with the deployed product."
    )

    events = CONN.execute(
        "SELECT event, COUNT(*) FROM events GROUP BY event ORDER BY COUNT(*) DESC"
    ).fetchall()
    feedback_count = CONN.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]

    total_sessions = CONN.execute(
        "SELECT COUNT(*) FROM events WHERE event='session_started'"
    ).fetchone()[0]
    assessments = CONN.execute(
        "SELECT COUNT(*) FROM events WHERE event='assessment_completed'"
    ).fetchone()[0]
    chats = CONN.execute(
        "SELECT COUNT(*) FROM events WHERE event='avatar_chat'"
    ).fetchone()[0]

    a, b, c, d = st.columns(4)
    a.metric("Sessions", total_sessions)
    b.metric("Assessments", assessments)
    c.metric("Avatar chats", chats)
    d.metric("Feedback", feedback_count)

    st.markdown("### Event breakdown")
    if events:
        st.dataframe(
            [{"Event": e, "Count": n} for e, n in events],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No usage events yet. Share the app with your first testers.")

    st.markdown("### Validation plan")
    st.markdown("""
    **Suggested first target:** 20 real testers.

    Track:
    - assessment start rate
    - assessment completion rate
    - avatar interaction rate
    - plan completion / intended action
    - willingness to return
    - qualitative feedback

    **Important:** replace all demo/target numbers in your final deck with actual observed data.
    """)

# -----------------------------
# Feedback
# -----------------------------
with tab4:
    st.markdown("### 💬 30-second feedback")
    st.caption("This feedback helps validate whether the product is useful and whether the avatar adds value.")

    with st.form("feedback_form"):
        rating = st.slider("How useful was the experience?", 1, 5, 4)
        would_return = st.radio(
            "Would you use Kinetic Coach again?",
            ["Yes", "Maybe", "No"],
            horizontal=True,
        )
        avatar_helped = st.radio(
            "Did the AI avatar make the experience better?",
            ["Yes", "A little", "No"],
            horizontal=True,
        )
        useful_part = st.text_area(
            "What was the most useful part?",
            placeholder="Example: The plan was simple and realistic...",
        )
        improvement = st.text_area(
            "What should we improve?",
            placeholder="Example: I want voice interaction...",
        )
        feedback_submit = st.form_submit_button(
            "Send feedback",
            use_container_width=True,
        )

    if feedback_submit:
        save_feedback(
            rating,
            would_return,
            useful_part,
            improvement,
            avatar_helped,
        )
        st.success("Thanks — your feedback was recorded.")

st.divider()
st.caption(
    "Kinetic Coach is an internship MVP. AI-generated wellness guidance is informational "
    "and not a substitute for professional medical advice."
)
