import json
import os
import re
from datetime import datetime
from threading import Lock
from config import QUIZZES_DATA_PATH
from core.validator import validate_mcqs

lock = Lock()
USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_]{3,32}$")


def _sanitize_username_for_path(username):
    # File-path safety guard for per-user quiz files.
    clean_username = (username or "").strip()
    if not USERNAME_REGEX.fullmatch(clean_username):
        raise ValueError("Invalid username format")
    return clean_username


def _resolve_quiz_file(username=None):
    if username:
        safe_username = _sanitize_username_for_path(username)
        return QUIZZES_DATA_PATH.replace("quizzes.json", f"user_{safe_username}_quizzes.json")
    return QUIZZES_DATA_PATH

def load_quizzes(username=None):
    """Load quizzes from JSON file and normalize stored answers."""
    user_file = _resolve_quiz_file(username)

    if os.path.exists(user_file):
        try:
            with open(user_file, 'r') as f:
                quizzes = json.load(f)
        except (json.JSONDecodeError, IOError):
            quizzes = []
    else:
        quizzes = []

    for quiz in quizzes:
        if isinstance(quiz, dict) and isinstance(quiz.get("mcqs"), list):
            quiz["mcqs"] = validate_mcqs(quiz["mcqs"])

    return quizzes

def save_quiz(quiz_data, username=None):
    """Save a quiz to JSON file, normalizing answers first."""
    if isinstance(quiz_data, dict) and isinstance(quiz_data.get("mcqs"), list):
        quiz_data["mcqs"] = validate_mcqs(quiz_data["mcqs"])

    quizzes = load_quizzes(username)
    quizzes.append(quiz_data)

    user_file = _resolve_quiz_file(username)

    with lock:
        with open(user_file, 'w') as f:
            json.dump(quizzes, f, indent=4)


def delete_quiz(quiz_id, username=None):
    """Delete a quiz by ID and return True if deleted."""
    quizzes = load_quizzes(username)
    filtered_quizzes = [quiz for quiz in quizzes if quiz.get("id") != quiz_id]
    if len(filtered_quizzes) == len(quizzes):
        return False

    user_file = _resolve_quiz_file(username)
    with lock:
        with open(user_file, 'w') as f:
            json.dump(filtered_quizzes, f, indent=4)
    return True


def update_latest_quiz_score(
    topic,
    difficulty,
    num_questions,
    score,
    username=None,
    quiz_id=None,
    submitted_answers=None,
    results=None,
):
    """Attach submission details to the matching quiz entry."""
    # This keeps score/submission details colocated with generated quiz snapshots.
    quizzes = load_quizzes(username)

    target_quiz = None
    if quiz_id:
        for quiz in quizzes:
            if quiz.get("id") == quiz_id:
                target_quiz = quiz
                break

    if target_quiz is None:
        for quiz in reversed(quizzes):
            if (
                quiz.get("topic") == topic
                and quiz.get("difficulty") == difficulty
                and int(quiz.get("num_questions", 0)) == int(num_questions)
            ):
                target_quiz = quiz
                break

    if target_quiz is None:
        return False

    target_quiz["score"] = score
    if submitted_answers is not None:
        target_quiz["submitted_answers"] = submitted_answers
    if results is not None:
        target_quiz["results"] = results
    target_quiz["submitted_at"] = target_quiz.get("submitted_at") or datetime.now().isoformat()

    user_file = _resolve_quiz_file(username)
    with lock:
        with open(user_file, 'w') as f:
            json.dump(quizzes, f, indent=4)
    return True


def create_quiz_and_save(quiz_data, username=None):
    """Save quiz and return its ID."""
    save_quiz(quiz_data, username)
    return quiz_data.get("id")


def get_latest_quiz(username=None):
    """Get most recent saved quiz."""
    quizzes = load_quizzes(username)
    return quizzes[-1] if quizzes else None


def get_quiz_by_id(quiz_id, username=None):
    """Retrieve a quiz by ID."""
    quizzes = load_quizzes(username)
    for quiz in quizzes:
        if quiz.get("id") == quiz_id:
            return quiz
    return None


def update_quiz(quiz_id, username=None, **updates):
    """Update quiz fields by ID."""
    quizzes = load_quizzes(username)
    updated = False

    for quiz in quizzes:
        if quiz.get("id") == quiz_id:
            quiz.update(updates)
            updated = True
            break

    if not updated:
        return False

    user_file = _resolve_quiz_file(username)
    with lock:
        with open(user_file, 'w') as f:
            json.dump(quizzes, f, indent=4)
    return True