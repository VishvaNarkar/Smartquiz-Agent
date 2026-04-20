import uuid
from datetime import datetime
from typing import Dict, List, Tuple

from core.validator import validate_mcqs
from data.data_manager import delete_quiz, get_quiz_by_id, load_quizzes, save_quiz, update_latest_quiz_score
from services.adaptive_engine import AdaptiveAIEngine
from services.ai_service import AIService
from services.form_creator import create_form
from services.user_manager import UserManager


class SmartQuizAPI:
    """Facade service that coordinates user, quiz, analytics, and export operations."""

    def __init__(self):
        self.user_manager = UserManager()
        self.ai_service = AIService()
        self.adaptive_engine = AdaptiveAIEngine(self.user_manager, self.ai_service)

    def authenticate_user(self, username: str, password: str) -> bool:
        return self.user_manager.authenticate_user(username, password)

    def register_user(self, username: str, password: str, email: str = "") -> bool:
        return self.user_manager.register_user(username, password, email)

    def resolve_username(self, username: str) -> str:
        return self.user_manager.resolve_username(username)

    def get_user_analytics(self, username: str) -> Dict:
        # Analytics are computed from persisted quizzes to keep UI and storage consistent.
        username = self.resolve_username(username)
        quizzes = load_quizzes(username)

        if not quizzes:
            return {
                "total_quizzes": 0,
                "average_score": 0.0,
                "weak_topics": [],
                "recent_quizzes": [],
                "topic_performance": {},
            }

        # Normalize ordering for recent views.
        quizzes_sorted = sorted(
            quizzes,
            key=lambda q: q.get("timestamp", ""),
            reverse=True,
        )

        scored_quizzes = [
            quiz for quiz in quizzes if isinstance(quiz.get("score"), (int, float)) and quiz.get("num_questions")
        ]

        percentages = []
        topic_rollups: Dict[str, Dict[str, float]] = {}
        for quiz in scored_quizzes:
            num_questions = max(int(quiz.get("num_questions", 0)), 1)
            percentage = (float(quiz.get("score", 0)) / num_questions) * 100.0
            percentages.append(percentage)

            topic = quiz.get("topic", "General")
            if topic not in topic_rollups:
                topic_rollups[topic] = {"attempts": 0.0, "total_percentage": 0.0}
            topic_rollups[topic]["attempts"] += 1.0
            topic_rollups[topic]["total_percentage"] += percentage

        topic_performance: Dict[str, Dict[str, float]] = {}
        weak_topics: List[str] = []
        for topic, rollup in topic_rollups.items():
            attempts = int(rollup["attempts"])
            avg_score = rollup["total_percentage"] / rollup["attempts"] if rollup["attempts"] else 0.0
            topic_performance[topic] = {
                "attempts": attempts,
                "avg_score": avg_score,
            }
            if avg_score < 70.0:
                weak_topics.append(topic)

        average_score = (sum(percentages) / len(percentages)) if percentages else 0.0

        return {
            "total_quizzes": len(quizzes),
            "average_score": average_score,
            "weak_topics": weak_topics,
            "recent_quizzes": quizzes_sorted[:5],
            "topic_performance": topic_performance,
        }

    def get_recent_quizzes(self, username: str) -> List[Dict]:
        username = self.resolve_username(username)
        quizzes = load_quizzes(username)
        history = self.user_manager.quiz_history.get(username, [])

        if not history:
            return quizzes

        used_history_indices = set()
        for quiz in quizzes:
            if isinstance(quiz.get("score"), (int, float)):
                continue

            for idx in range(len(history) - 1, -1, -1):
                if idx in used_history_indices:
                    continue
                entry = history[idx]

                if (
                    entry.get("topic") == quiz.get("topic")
                    and entry.get("difficulty") == quiz.get("difficulty")
                    and int(entry.get("num_questions", 0)) == int(quiz.get("num_questions", 0))
                ):
                    quiz["score"] = entry.get("score")
                    used_history_indices.add(idx)
                    break

        return quizzes

    def get_quiz(self, username: str, quiz_id: str) -> Dict | None:
        username = self.resolve_username(username)
        return get_quiz_by_id(quiz_id, username)

    def delete_quiz(self, username: str, quiz_id: str) -> bool:
        username = self.resolve_username(username)
        return delete_quiz(quiz_id, username)

    def sync_quiz_score(
        self,
        username: str,
        topic: str,
        difficulty: str,
        num_questions: int,
        score: float,
        quiz_id: str | None = None,
        submitted_answers: List[str] | None = None,
        results: List[Dict] | None = None,
    ) -> bool:
        username = self.resolve_username(username)
        return update_latest_quiz_score(
            topic,
            difficulty,
            num_questions,
            score,
            username,
            quiz_id=quiz_id,
            submitted_answers=submitted_answers,
            results=results,
        )

    def generate_custom_quiz_with_id(
        self,
        username: str,
        topic: str,
        difficulty: str,
        num_questions: int,
        model: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
    ) -> Tuple[List[Dict], str]:
        # Generate + validate MCQs before persisting to history.
        username = self.resolve_username(username)
        mcqs = self.ai_service.generate_quiz(topic, difficulty, num_questions, model=model, api_url=api_url, api_key=api_key)
        mcqs = validate_mcqs(mcqs)

        quiz_data = {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": len(mcqs),
            "mcqs": mcqs,
            "timestamp": datetime.now().isoformat(),
        }
        save_quiz(quiz_data, username)
        return mcqs, quiz_data["id"]

    def generate_custom_quiz(
        self,
        username: str,
        topic: str,
        difficulty: str,
        num_questions: int,
        model: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
    ):
        mcqs, _quiz_id = self.generate_custom_quiz_with_id(
            username,
            topic,
            difficulty,
            num_questions,
            model=model,
            api_url=api_url,
            api_key=api_key,
        )
        return mcqs

    def generate_adaptive_quiz_with_id(
        self,
        username: str,
        num_questions: int = 5,
        model: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
    ) -> Tuple[List[Dict], str, str]:
        # Adaptive engine selects topic based on user weakness profile.
        username = self.resolve_username(username)
        mcqs, topic = self.adaptive_engine.generate_adaptive_quiz(
            username,
            num_questions,
            model=model,
            api_url=api_url,
            api_key=api_key,
        )
        mcqs = validate_mcqs(mcqs)

        quiz_data = {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "difficulty": "Adaptive",
            "num_questions": len(mcqs),
            "mcqs": mcqs,
            "timestamp": datetime.now().isoformat(),
        }
        save_quiz(quiz_data, username)
        return mcqs, topic, quiz_data["id"]

    def generate_adaptive_quiz(
        self,
        username: str,
        num_questions: int = 5,
        model: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
    ) -> Tuple[List[Dict], str]:
        mcqs, topic, _quiz_id = self.generate_adaptive_quiz_with_id(
            username,
            num_questions,
            model=model,
            api_url=api_url,
            api_key=api_key,
        )
        return mcqs, topic

    def export_google_form(self, mcqs: List[Dict], title: str = None) -> str:
        return create_form(mcqs, title=title)

    def save_quiz_result(self, username: str, quiz_data: Dict, score: float):
        username = self.resolve_username(username)
        self.user_manager.save_quiz_result(username, quiz_data, score)

    def analyze_performance(self, username: str, performance_data: Dict) -> Dict:
        username = self.resolve_username(username)
        return self.adaptive_engine.analyze_performance(username, performance_data)
