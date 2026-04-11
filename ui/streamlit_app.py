import logging
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from config import APP_TITLE, DEFAULT_NUM_QUESTIONS, MAX_NUM_QUESTIONS
from core.validator import validate_mcqs
from services.api import SmartQuizAPI
from services.scoring import evaluate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize service API
api = SmartQuizAPI()

# Session state initialization
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "mcqs" not in st.session_state:
    st.session_state.mcqs = None
if "results" not in st.session_state:
    st.session_state.results = None
if "login_username" not in st.session_state:
    st.session_state.login_username = ""
if "login_password" not in st.session_state:
    st.session_state.login_password = ""
if "reg_username" not in st.session_state:
    st.session_state.reg_username = ""
if "reg_password" not in st.session_state:
    st.session_state.reg_password = ""
if "reg_email" not in st.session_state:
    st.session_state.reg_email = ""
if "clear_login_fields" not in st.session_state:
    st.session_state.clear_login_fields = False
if "clear_register_fields" not in st.session_state:
    st.session_state.clear_register_fields = False

def login_page():
    if st.session_state.clear_login_fields:
        st.session_state.login_username = ""
        st.session_state.login_password = ""
        st.session_state.clear_login_fields = False
    if st.session_state.clear_register_fields:
        st.session_state.reg_username = ""
        st.session_state.reg_password = ""
        st.session_state.reg_email = ""
        st.session_state.clear_register_fields = False

    st.title("🔐 Login to SmartQuiz")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            normalized_username = username.strip()
            if api.authenticate_user(normalized_username, password):
                st.session_state.user = normalized_username
                st.session_state.page = "dashboard"
                st.session_state.clear_login_fields = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        st.subheader("Register")
        new_username = st.text_input("Username", key="reg_username")
        new_password = st.text_input("Password", type="password", key="reg_password")
        email = st.text_input("Email (optional)", key="reg_email")

        if st.button("Register"):
            normalized_username = new_username.strip()
            if api.register_user(normalized_username, new_password, email):
                st.session_state.clear_register_fields = True
                st.success("Registration successful! Please login.")
            else:
                st.error("Username already exists or invalid input")

def dashboard_page():
    st.title(f"📊 Welcome back, {st.session_state.user}!")

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "login"
        st.session_state.clear_login_fields = True
        st.rerun()

    # Analytics
    analytics = api.get_user_analytics(st.session_state.user)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Quizzes", analytics.get("total_quizzes", 0))
    with col2:
        st.metric("Average Score", f"{analytics.get('average_score', 0):.1f}%")
    with col3:
        st.metric("Weak Topics", len(analytics.get("weak_topics", [])))

    # Quick actions
    st.header("Quick Actions")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎯 Generate Adaptive Quiz", use_container_width=True):
            st.session_state.page = "adaptive_quiz"
            st.rerun()

    with col2:
        if st.button("📝 Create Custom Quiz", use_container_width=True):
            st.session_state.page = "custom_quiz"
            st.rerun()

    # Recent quizzes
    user_quizzes = api.get_recent_quizzes(st.session_state.user)
    if user_quizzes:
        st.header("Recent Quizzes")
        for quiz in reversed(user_quizzes[-3:]):
            with st.expander(f"{quiz['topic']} ({quiz['difficulty']})"):
                st.write(f"**Questions:** {quiz.get('num_questions', 0)}")
                st.write(f"**Date:** {quiz.get('timestamp', 'N/A')[:10] if 'timestamp' in quiz else 'N/A'}")

    # Weak topics
    weak_topics = analytics.get("weak_topics", [])
    if weak_topics:
        st.header("📉 Areas to Focus On")
        for topic in weak_topics[:5]:
            st.write(f"• {topic}")

def adaptive_quiz_page():
    st.title("🎯 Adaptive Quiz")

    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.write("This quiz is tailored to your weak areas based on your performance.")
    st.info(
        "If you have identified weak topic areas, adaptive mode will generate a quiz on one of those topics. "
        "If no weak topics are found, it will review your most recent quiz topic; only when no history exists will it use a general Mixed Subjects quiz."
    )

    if st.button("Generate Adaptive Quiz"):
        progress = st.progress(0)
        with st.spinner("Generating personalized quiz..."):
            try:
                progress.progress(25)
                mcqs, topic = api.generate_adaptive_quiz(st.session_state.user)
                progress.progress(75)
                mcqs = validate_mcqs(mcqs)
                progress.progress(100)
                st.session_state.mcqs = mcqs
                st.session_state.current_topic = topic
                st.session_state.current_difficulty = "Adaptive"
                st.success(f"Generated {len(mcqs)} personalized questions on {topic}!")
            except Exception as e:
                st.error(f"Failed to generate quiz: {e}")
            finally:
                progress.empty()

    # Display quiz
    display_quiz()

def custom_quiz_page():
    st.title("📝 Custom Quiz")

    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

    # Main form
    with st.form("quiz_form"):
        topic = st.text_input("Enter Topic", max_chars=100)
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        num = st.slider("Number of Questions", 1, MAX_NUM_QUESTIONS, DEFAULT_NUM_QUESTIONS)

        submitted = st.form_submit_button("Generate Quiz")

    if submitted:
        if not topic.strip():
            st.error("Please enter a valid topic.")
        else:
            progress = st.progress(0)
            with st.spinner("⏳ Generating quiz... (This may take a moment while Ollama responds)"):
                try:
                    progress.progress(25)
                    mcqs = api.generate_custom_quiz(st.session_state.user, topic, difficulty, num)
                    progress.progress(75)
                    mcqs = validate_mcqs(mcqs)
                    progress.progress(100)
                except Exception as error:
                    st.error(f"Failed to generate quiz: {error}")
                    mcqs = []
            progress.empty()

            if not mcqs:
                if topic.strip():
                    st.error("Failed to generate quiz. Ensure Ollama is running: `ollama serve`")
            else:
                st.session_state.current_topic = topic
                st.session_state.current_difficulty = difficulty
                st.session_state["mcqs"] = mcqs
                st.success(f"Generated {len(mcqs)} questions!")

    # Display quiz
    display_quiz()

def display_quiz():
    if "mcqs" in st.session_state and st.session_state.mcqs:
        mcqs = st.session_state["mcqs"]
        st.header("Quiz Questions")
        st.divider()

        # Collect answers
        answers = []
        for i, q in enumerate(mcqs):
            st.write(f"**Q{i+1}:** {q['question']}")
            options = ["-- Select Answer --"] + q["options"]
            selected = st.radio("", options, key=f"q_{i}")
            st.divider()
            if selected is None or selected.startswith("--"):
                answers.append("")
            else:
                answers.append(selected)
            st.write("")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit Answers"):
                if any(answer == "" for answer in answers):
                    st.error("Please answer every question before submitting the quiz.")
                else:
                    score, results = evaluate(mcqs, answers)
                    st.session_state["results"] = results
                    st.session_state["score"] = score

                    # Save results to user profile
                    quiz_data = {
                        "topic": getattr(st.session_state, 'current_topic', 'Adaptive'),
                        "difficulty": getattr(st.session_state, 'current_difficulty', 'Medium'),
                        "questions": mcqs
                    }
                    api.save_quiz_result(st.session_state.user, quiz_data, score)

                    st.success(f"Score: {score}/{len(results)}")

                    # Show analysis
                    analysis = api.analyze_performance(st.session_state.user, {"score": score, "questions": mcqs})
                    st.info("💡 " + " | ".join(analysis.get("recommendations", [])))

        with col2:
            if st.button("Export to Google Form"):
                with st.spinner("Creating Google Form..."):
                    try:
                        title = f"{st.session_state.user}'s Quiz"
                        link = api.export_google_form(mcqs, title=title)
                        st.success(f"Form Created: {link}")
                    except Exception as e:
                        st.error(f"Failed to create form: {str(e)}")

    # Display results
    if "results" in st.session_state and st.session_state.results:
        st.header("Results")
        score = st.session_state["score"]
        results = st.session_state["results"]
        st.write(f"**Final Score: {score}/{len(results)}**")

        for r in results:
            status = "✅ Correct" if r["status"] == "✅" else "❌ Incorrect"
            st.write(f"- {r['question']}: {status} (Correct: {r['correct']}, Your: {r['your_answer']})")

# Main app logic
if st.session_state.user is None:
    login_page()
else:
    if st.session_state.page == "dashboard":
        dashboard_page()
    elif st.session_state.page == "adaptive_quiz":
        adaptive_quiz_page()
    elif st.session_state.page == "custom_quiz":
        custom_quiz_page()