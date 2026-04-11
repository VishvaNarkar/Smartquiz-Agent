import uuid
from datetime import datetime
from typing import Dict, List, Tuple

from core.validator import validate_mcqs
from data.data_manager import load_quizzes, save_quiz
from services.adaptive_engine import AdaptiveAIEngine
from services.ai_service import AIService
from services.form_creator import create_form
from services.user_manager import UserManager


class SmartQuizAPI:
    def __init__(self):
        self.user_manager = UserManager()
        self.ai_service = AIService()
        self.adaptive_engine = AdaptiveAIEngine(self.user_manager, self.ai_service)

    def authenticate_user(self, username: str, password: str) -> bool:
        return self.user_manager.authenticate_user(username, password)

    def register_user(self, username: str, password: str, email: str = "") -> bool:
        return self.user_manager.register_user(username, password, email)

    def get_user_analytics(self, username: str) -> Dict:
        return self.user_manager.get_user_analytics(username)

    def get_recent_quizzes(self, username: str) -> List[Dict]:
        return load_quizzes(username)

    def generate_custom_quiz(self, username: str, topic: str, difficulty: str, num_questions: int):
        mcqs = self.ai_service.generate_quiz(topic, difficulty, num_questions)
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
        return mcqs

    def generate_adaptive_quiz(self, username: str, num_questions: int = 5) -> Tuple[List[Dict], str]:
        mcqs, topic = self.adaptive_engine.generate_adaptive_quiz(username, num_questions)
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
        return mcqs, topic

    def export_google_form(self, mcqs: List[Dict], title: str = None) -> str:
        return create_form(mcqs, title=title)

    def save_quiz_result(self, username: str, quiz_data: Dict, score: float):
        self.user_manager.save_quiz_result(username, quiz_data, score)

    def analyze_performance(self, username: str, performance_data: Dict) -> Dict:
        return self.adaptive_engine.analyze_performance(username, performance_data)
