import bcrypt
import json
import os
import re
from threading import Lock
from typing import Dict, List, Optional, Set
from datetime import datetime

lock = Lock()
USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_]{3,32}$")


def normalize_username(username: str) -> str:
    return (username or "").strip()


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_REGEX.fullmatch(normalize_username(username)))


def to_canonical_username(username: str) -> str:
    raw = normalize_username(username)
    if is_valid_username(raw):
        return raw

    canonical = re.sub(r"[^A-Za-z0-9_]", "_", raw)
    canonical = re.sub(r"_+", "_", canonical).strip("_")

    if not canonical:
        canonical = "user"

    canonical = canonical[:32]
    if len(canonical) < 3:
        canonical = (canonical + "_user")[:32]
    return canonical

class UserManager:
    """Local user repository with migration-aware username compatibility support."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.quiz_history_file = os.path.join(data_dir, "quiz_history.json")
        self.aliases_file = os.path.join(data_dir, "username_aliases.json")
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

        if os.path.exists(self.aliases_file):
            try:
                with open(self.aliases_file, 'r') as f:
                    self.username_aliases = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.username_aliases = {}
        else:
            self.username_aliases = {}

        migrated = self._migrate_legacy_usernames()
        stats_recomputed = self._recompute_user_stats()
        if migrated or stats_recomputed:
            # Persist startup migrations once so subsequent loads are clean.
            self._save_data()

    def _save_data(self):
        """Save users and quiz history to files."""
        with lock:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            with open(self.quiz_history_file, 'w') as f:
                json.dump(self.quiz_history, f, indent=2)
            with open(self.aliases_file, 'w') as f:
                json.dump(self.username_aliases, f, indent=2)

    def _migrate_legacy_usernames(self) -> bool:
        # Canonicalize old usernames (for example, names with spaces) and preserve aliases.
        changed = False
        updated_users = {}
        updated_history = {}

        existing_targets = set()

        for username in list(self.users.keys()):
            resolved = self._resolve_or_canonicalize(username, existing_targets)
            if resolved != username:
                changed = True
                self.username_aliases[normalize_username(username)] = resolved
                self._migrate_user_quiz_file(username, resolved)
            updated_users[resolved] = self.users[username]
            existing_targets.add(resolved)

        for username, history in self.quiz_history.items():
            resolved = self.username_aliases.get(normalize_username(username), self._resolve_or_canonicalize(username, existing_targets))
            updated_history[resolved] = history
            existing_targets.add(resolved)
            if resolved != username:
                changed = True
                self.username_aliases[normalize_username(username)] = resolved

        if changed:
            self.users = updated_users
            self.quiz_history = updated_history

        return changed

    def _resolve_or_canonicalize(self, username: str, reserved: Set[str]) -> str:
        raw = normalize_username(username)

        # Preserve existing valid usernames as-is.
        if is_valid_username(raw) and raw not in reserved:
            return raw

        canonical = to_canonical_username(raw)
        candidate = canonical
        counter = 1
        while candidate in reserved or (candidate in self.users and candidate != raw):
            suffix = f"_{counter}"
            candidate = f"{canonical[:32-len(suffix)]}{suffix}"
            counter += 1

        return candidate

    def _migrate_user_quiz_file(self, old_username: str, new_username: str) -> None:
        # Keep historical quiz files accessible after username migration.
        old_file = os.path.join(self.data_dir, f"user_{old_username}_quizzes.json")
        new_file = os.path.join(self.data_dir, f"user_{new_username}_quizzes.json")

        if old_file == new_file:
            return
        if not os.path.exists(old_file):
            return
        if os.path.exists(new_file):
            return

        try:
            os.rename(old_file, new_file)
        except OSError:
            # If rename fails, keep old file; alias resolution still allows access through canonical.
            pass

    def _score_percentage(self, score: float, num_questions: int) -> float:
        # Normalize score representation across analytics surfaces.
        if num_questions <= 0:
            return 0.0
        return (float(score) / float(num_questions)) * 100.0

    def _recompute_user_stats(self) -> bool:
        changed = False
        for username, user in self.users.items():
            history = self.quiz_history.get(username, [])
            total_quizzes = len(history)
            percentages = []
            for entry in history:
                num_questions = int(entry.get("num_questions", 0) or 0)
                score = float(entry.get("score", 0) or 0)
                percentages.append(self._score_percentage(score, num_questions))

            avg_percentage = (sum(percentages) / len(percentages)) if percentages else 0.0

            if user.get("total_quizzes") != total_quizzes or float(user.get("average_score", 0.0)) != float(avg_percentage):
                user["total_quizzes"] = total_quizzes
                user["average_score"] = avg_percentage
                changed = True

        return changed

    def resolve_username(self, username: str) -> str:
        normalized = normalize_username(username)
        if normalized in self.users:
            return normalized
        return self.username_aliases.get(normalized, normalized)

    def hash_password(self, password: str) -> str:
        """Hash password for storage using bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def register_user(self, username: str, password: str, email: str = "") -> bool:
        """Register a new user."""
        username = normalize_username(username)
        email = email.strip()
        if not is_valid_username(username):
            return False
        if not password or len(password) < 8:
            return False
        if username in self.users or username in self.username_aliases:
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
        username = self.resolve_username(username)
        if not is_valid_username(username):
            return False
        if username not in self.users:
            return False
        hashed = self.users[username]["password"]
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def get_user_profile(self, username: str) -> Optional[Dict]:
        """Get user profile."""
        username = self.resolve_username(username)
        if not is_valid_username(username):
            return None
        return self.users.get(username)

    def save_quiz_result(self, username: str, quiz_data: Dict, score: float):
        """Save quiz result and update user stats."""
        username = self.resolve_username(username)
        if username not in self.users:
            return

        # Older data files or partial migrations can leave the history bucket missing.
        self.quiz_history.setdefault(username, [])

        num_questions = len(quiz_data.get("questions", []))
        percentage = self._score_percentage(score, num_questions)

        # Save quiz history
        quiz_entry = {
            "timestamp": datetime.now().isoformat(),
            "topic": quiz_data.get("topic", ""),
            "difficulty": quiz_data.get("difficulty", ""),
            "num_questions": num_questions,
            "score": score,
            "score_percentage": percentage,
            "questions": quiz_data.get("questions", [])
        }
        self.quiz_history[username].append(quiz_entry)

        # Update user stats
        user = self.users[username]
        user["total_quizzes"] += 1
        user["average_score"] = ((user["average_score"] * (user["total_quizzes"] - 1)) + percentage) / user["total_quizzes"]

        # Update weak topics
        self._update_weak_topics(username, quiz_data, score)

        self._save_data()

    def _update_weak_topics(self, username: str, quiz_data: Dict, score: float):
        """Update weak topics based on quiz performance."""
        username = self.resolve_username(username)
        topic = quiz_data.get("topic", "General")
        num_questions = len(quiz_data.get("questions", []))
        percentage = self._score_percentage(score, num_questions)

        user = self.users[username]

        if topic not in user["weak_topics"]:
            user["weak_topics"][topic] = {"attempts": 0, "avg_score": 0.0}

        topic_stats = user["weak_topics"][topic]
        topic_stats["attempts"] += 1
        topic_stats["avg_score"] = ((topic_stats["avg_score"] * (topic_stats["attempts"] - 1)) + percentage) / topic_stats["attempts"]

    def get_weak_topics(self, username: str) -> List[str]:
        """Get list of weak topics for a user."""
        username = self.resolve_username(username)
        if username not in self.users:
            return []
        weak_topics = []
        for topic, stats in self.users[username]["weak_topics"].items():
            if stats["avg_score"] < 70.0:  # Consider below 70% as weak
                weak_topics.append(topic)
        return weak_topics

    def get_last_quiz_topic(self, username: str) -> str:
        """Get the topic from the most recent quiz attempt."""
        username = self.resolve_username(username)
        if username not in self.quiz_history or not self.quiz_history[username]:
            return ""
        last_entry = self.quiz_history[username][-1]
        return last_entry.get("topic", "")

    def get_user_analytics(self, username: str) -> Dict:
        """Get analytics for a user."""
        username = self.resolve_username(username)
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