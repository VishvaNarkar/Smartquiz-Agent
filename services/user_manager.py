import bcrypt
import json
import os
from threading import Lock
from typing import Dict, List, Optional
from datetime import datetime

lock = Lock()

class UserManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.quiz_history_file = os.path.join(data_dir, "quiz_history.json")
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()

    def _load_data(self):
        """Load users and quiz history from files."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.users = {}
        else:
            self.users = {}

        if os.path.exists(self.quiz_history_file):
            try:
                with open(self.quiz_history_file, 'r') as f:
                    self.quiz_history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.quiz_history = {}
        else:
            self.quiz_history = {}

    def _save_data(self):
        """Save users and quiz history to files."""
        with lock:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            with open(self.quiz_history_file, 'w') as f:
                json.dump(self.quiz_history, f, indent=2)

    def hash_password(self, password: str) -> str:
        """Hash password for storage using bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def register_user(self, username: str, password: str, email: str = "") -> bool:
        """Register a new user."""
        username = username.strip()
        email = email.strip()
        if not username or len(username) > 64:
            return False
        if not password or len(password) < 8:
            return False
        if username in self.users:
            return False
        self.users[username] = {
            "password": self.hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
            "weak_topics": {},
            "total_quizzes": 0,
            "average_score": 0.0
        }
        self.quiz_history[username] = []
        self._save_data()
        return True

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        username = username.strip()
        if username not in self.users:
            return False
        hashed = self.users[username]["password"]
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def get_user_profile(self, username: str) -> Optional[Dict]:
        """Get user profile."""
        return self.users.get(username)

    def save_quiz_result(self, username: str, quiz_data: Dict, score: float):
        """Save quiz result and update user stats."""
        if username not in self.users:
            return

        # Save quiz history
        quiz_entry = {
            "timestamp": datetime.now().isoformat(),
            "topic": quiz_data.get("topic", ""),
            "difficulty": quiz_data.get("difficulty", ""),
            "num_questions": len(quiz_data.get("questions", [])),
            "score": score,
            "questions": quiz_data.get("questions", [])
        }
        self.quiz_history[username].append(quiz_entry)

        # Update user stats
        user = self.users[username]
        user["total_quizzes"] += 1
        user["average_score"] = ((user["average_score"] * (user["total_quizzes"] - 1)) + score) / user["total_quizzes"]

        # Update weak topics
        self._update_weak_topics(username, quiz_data, score)

        self._save_data()

    def _update_weak_topics(self, username: str, quiz_data: Dict, score: float):
        """Update weak topics based on quiz performance."""
        topic = quiz_data.get("topic", "General")
        num_questions = len(quiz_data.get("questions", []))
        percentage = (score / num_questions) * 100 if num_questions > 0 else 0

        user = self.users[username]

        if topic not in user["weak_topics"]:
            user["weak_topics"][topic] = {"attempts": 0, "avg_score": 0.0}

        topic_stats = user["weak_topics"][topic]
        topic_stats["attempts"] += 1
        topic_stats["avg_score"] = ((topic_stats["avg_score"] * (topic_stats["attempts"] - 1)) + percentage) / topic_stats["attempts"]

    def get_weak_topics(self, username: str) -> List[str]:
        """Get list of weak topics for a user."""
        if username not in self.users:
            return []
        weak_topics = []
        for topic, stats in self.users[username]["weak_topics"].items():
            if stats["avg_score"] < 70.0:  # Consider below 70% as weak
                weak_topics.append(topic)
        return weak_topics

    def get_last_quiz_topic(self, username: str) -> str:
        """Get the topic from the most recent quiz attempt."""
        if username not in self.quiz_history or not self.quiz_history[username]:
            return ""
        last_entry = self.quiz_history[username][-1]
        return last_entry.get("topic", "")

    def get_user_analytics(self, username: str) -> Dict:
        """Get analytics for a user."""
        if username not in self.users:
            return {}

        user = self.users[username]
        history = self.quiz_history.get(username, [])

        return {
            "total_quizzes": user["total_quizzes"],
            "average_score": user["average_score"],
            "weak_topics": self.get_weak_topics(username),
            "recent_quizzes": history[-5:] if history else [],
            "topic_performance": user["weak_topics"]
        }