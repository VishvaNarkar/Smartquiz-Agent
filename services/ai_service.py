import logging
from urllib.parse import urlparse

import requests
import streamlit as st
from core.formatter import clean_json_output
from core.validator import validate_mcqs
from core.generator import generate_mcqs
from config import OLLAMA_URL

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def _clean_topic(topic: str) -> str:
        topic = topic.strip()
        if len(topic) > 100:
            raise ValueError("Topic too long")
        return topic.replace("{", "").replace("}", "").replace("\n", " ")

    @staticmethod
    def check_ollama_health() -> bool:
        parsed = urlparse(OLLAMA_URL)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        try:
            response = requests.get(base_url, timeout=5)
            return response.status_code < 500
        except requests.RequestException:
            logger.error("Ollama health check failed for %s", base_url)
            return False

    @st.cache_data(show_spinner=False)
    def cached_generate_quiz(_self, topic: str, difficulty: str, num_questions: int = 5):
        return _self._generate_quiz(topic, difficulty, num_questions)

    def _generate_quiz(self, topic: str, difficulty: str, num_questions: int = 5):
        if not self.check_ollama_health():
            raise RuntimeError("Ollama is unavailable. Please start the Ollama server.")

        topic = self._clean_topic(topic)
        mcqs = generate_mcqs(topic, difficulty, num_questions)
        mcqs = validate_mcqs(mcqs)

        unique_questions = {}
        for q in mcqs:
            if q["question"] not in unique_questions:
                unique_questions[q["question"]] = q

        return list(unique_questions.values())

    def generate_quiz(self, topic: str, difficulty: str, num_questions: int = 5):
        return self.cached_generate_quiz(topic, difficulty, num_questions)
