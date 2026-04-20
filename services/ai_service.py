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
    def _get_base_url(api_url: str | None = None) -> str:
        service_url = api_url or OLLAMA_URL
        parsed = urlparse(service_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    @staticmethod
    def check_service_health(api_url: str | None = None) -> bool:
        base_url = AIService._get_base_url(api_url)
        # If using OpenAI, skip strict health check (OpenAI root returns 404/405)
        if "openai.com" in base_url:
            return True
        try:
            response = requests.get(base_url, timeout=5)
            # Accept 2xx, 3xx, 404, 405 as healthy for local endpoints
            return response.status_code < 500 or response.status_code in (404, 405)
        except requests.RequestException:
            logger.error("AI service health check failed for %s", base_url)
            return False

    @st.cache_data(show_spinner=False)
    def cached_generate_quiz(
        _self,
        topic: str,
        difficulty: str,
        num_questions: int = 5,
        model: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
    ):
        return _self._generate_quiz(topic, difficulty, num_questions, model=model, api_url=api_url, api_key=api_key)

    def _generate_quiz(
        self,
        topic: str,
        difficulty: str,
        num_questions: int = 5,
        model: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
    ):
        if not self.check_service_health(api_url):
            raise RuntimeError("The selected AI service is unavailable. Please check the endpoint and try again.")

        topic = self._clean_topic(topic)
        mcqs = generate_mcqs(topic, difficulty, num_questions, model=model, api_url=api_url, api_key=api_key)
        mcqs = validate_mcqs(mcqs)

        unique_questions = {}
        for q in mcqs:
            if q["question"] not in unique_questions:
                unique_questions[q["question"]] = q

        return list(unique_questions.values())

    def generate_quiz(
        self,
        topic: str,
        difficulty: str,
        num_questions: int = 5,
        model: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
    ):
        return self.cached_generate_quiz(
            topic,
            difficulty,
            num_questions,
            model=model,
            api_url=api_url,
            api_key=api_key,
        )
