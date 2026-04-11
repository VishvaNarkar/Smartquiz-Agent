import json
import os
from threading import Lock
from config import QUIZZES_DATA_PATH
from core.validator import validate_mcqs

lock = Lock()

def load_quizzes(username=None):
    """Load quizzes from JSON file and normalize stored answers."""
    if username:
        user_file = QUIZZES_DATA_PATH.replace("quizzes.json", f"user_{username}_quizzes.json")
    else:
        user_file = QUIZZES_DATA_PATH

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

    if username:
        user_file = QUIZZES_DATA_PATH.replace("quizzes.json", f"user_{username}_quizzes.json")
    else:
        user_file = QUIZZES_DATA_PATH

    with lock:
        with open(user_file, 'w') as f:
            json.dump(quizzes, f, indent=4)

def get_quiz_by_id(quiz_id, username=None):
    """Retrieve a quiz by ID."""
    quizzes = load_quizzes(username)
    for quiz in quizzes:
        if quiz.get("id") == quiz_id:
            return quiz
    return None