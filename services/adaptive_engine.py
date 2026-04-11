import logging
from typing import List, Dict, Any
from services.user_manager import UserManager

logger = logging.getLogger(__name__)

class AdaptiveAIEngine:
    def __init__(self, user_manager: UserManager, ai_service: Any):
        self.user_manager = user_manager
        self.ai_service = ai_service

    def generate_adaptive_quiz(self, username: str, num_questions: int = 5) -> tuple:
        """
        Generate an adaptive quiz based on user's weak topics.

        Args:
            username (str): The username.
            num_questions (int): Number of questions to generate.

        Returns:
            tuple: (list of MCQ dictionaries, topic used)
        """
        weak_topics = self.user_manager.get_weak_topics(username)

        if not weak_topics:
            last_topic = self.user_manager.get_last_quiz_topic(username)
            if last_topic:
                logger.info(
                    "No weak topics found for %s, generating a review quiz on last topic: %s",
                    username,
                    last_topic,
                )
                mcqs = self.ai_service.generate_quiz(last_topic, "Medium", num_questions)
                return mcqs, last_topic

            # If no weak topics and no quiz history, generate a general quiz
            logger.info("No weak topics found for %s, generating general quiz", username)
            mcqs = self.ai_service.generate_quiz("Mixed Subjects", "Medium", num_questions)
            return mcqs, "Mixed Subjects"

        # Prioritize the weakest topic (lowest average score)
        def topic_score(topic_name: str) -> float:
            profile = self.user_manager.get_user_profile(username) or {}
            weak_entry = profile.get("weak_topics", {}).get(topic_name)
            return weak_entry.get("avg_score", 100.0) if weak_entry else 100.0

        weak_topics_sorted = sorted(weak_topics, key=topic_score)
        target_topic = weak_topics_sorted[0]
        logger.info("Generating adaptive quiz for %s on weak topic: %s", username, target_topic)

        # Generate quiz on the weak topic with appropriate difficulty
        user_profile = self.user_manager.get_user_profile(username) or {}
        avg_score = user_profile.get("average_score", 50.0)

        # Adjust difficulty based on performance
        if avg_score < 50:
            difficulty = "Easy"
        elif avg_score < 75:
            difficulty = "Medium"
        else:
            difficulty = "Hard"

        mcqs = self.ai_service.generate_quiz(target_topic, difficulty, num_questions)
        return mcqs, target_topic

    def analyze_performance(self, username: str, quiz_results: Dict) -> Dict[str, Any]:
        """
        Analyze quiz performance and provide insights.

        Args:
            username (str): The username.
            quiz_results (dict): Quiz results data.

        Returns:
            dict: Analysis results.
        """
        score = quiz_results.get("score", 0)
        total_questions = len(quiz_results.get("questions", []))

        analysis = {
            "score": score,
            "total_questions": total_questions,
            "percentage": (score / total_questions) * 100 if total_questions > 0 else 0,
            "recommendations": []
        }

        if analysis["percentage"] < 70:
            analysis["recommendations"].append("Consider reviewing the topic material.")
            analysis["recommendations"].append("Try easier difficulty level.")

        weak_topics = self.user_manager.get_weak_topics(username)
        if weak_topics:
            analysis["recommendations"].append(f"Focus on these weak topics: {', '.join(weak_topics[:3])}")

        return analysis