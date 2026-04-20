import json
import logging
import time
from typing import Any, Dict, List

import requests
from config import OLLAMA_MODEL, OLLAMA_URL
from core.formatter import clean_json_output

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _is_chat_completions_url(url: str) -> bool:
    normalized = (url or "").lower()
    return "/chat/completions" in normalized

def generate_mcqs(
    topic: str,
    difficulty: str,
    num_questions: int = 5,
    model: str | None = None,
    api_url: str | None = None,
    api_key: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Generate multiple-choice questions using Ollama or OpenAI-compatible chat APIs.

    Args:
        topic (str): The topic for the questions.
        difficulty (str): Difficulty level (Easy, Medium, Hard).
        num_questions (int): Number of questions to generate.
        model (str, optional): Model name to use.
        api_url (str, optional): Custom API endpoint URL.
        api_key (str, optional): Authorization token for custom APIs.

    Returns:
        list: List of validated MCQ dictionaries.

    Raises:
        RuntimeError: When the AI API returns an error or output is invalid.
    """
    if not topic.strip():
        raise ValueError("Topic cannot be empty")

    topic = topic.strip()
    if len(topic) > 100:
        raise ValueError("Topic too long")
    topic = topic.replace("{", "").replace("}", "").replace("\n", " ")

    prompt = f"""
    You are an expert exam creator.

    Rules:
    - Strict JSON only
    - No explanation
    - No extra text
    - Each question must be unique
    - Answer MUST match one option

    Generate {num_questions} {difficulty} level multiple-choice questions on "{topic}".

    Strict JSON format:
    [
      {{
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "answer": "correct option text"
      }}
    ]

    Ensure the JSON is valid and each question has exactly 4 options.
    """

    model_name = model or OLLAMA_MODEL
    request_url = api_url or OLLAMA_URL

    # Support both local Ollama prompt API and OpenAI-compatible chat-completions APIs.
    if _is_chat_completions_url(request_url):
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.3,
            "stream": False,
        }
    else:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
        }

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                "Generating %s MCQs on '%s' with difficulty '%s' (attempt %s/%s)",
                num_questions,
                topic,
                difficulty,
                attempt,
                max_attempts,
            )
            response = requests.post(request_url, json=payload, headers=headers, timeout=600)

            if response.status_code != 200:
                error_text = response.text.strip()
                message = f"AI API Error: {response.status_code} - {error_text}"
                logger.error(message)
                if attempt < max_attempts and response.status_code >= 500:
                    time.sleep(2)
                    continue
                raise RuntimeError(message)

            try:
                data = response.json()
                if _is_chat_completions_url(request_url):
                    # Cloud providers typically return choices[].message.content.
                    choices = data.get("choices") or []
                    first_choice = choices[0] if choices else {}
                    message_obj = first_choice.get("message") or {}
                    output = message_obj.get("content") or data.get("output_text") or response.text
                else:
                    output = data.get("response") or data.get("output") or response.text
            except json.JSONDecodeError:
                output = response.text

            if not isinstance(output, str):
                output = str(output)

            output = output.strip()
            mcqs = clean_json_output(output)

            if not mcqs:
                logger.warning("No valid MCQs generated. Raw output: %s", output[:500])
                raise RuntimeError("AI provider returned invalid MCQ output")

            logger.info("Successfully generated %s MCQs", len(mcqs))
            return mcqs

        except requests.exceptions.RequestException as exc:
            message = f"Network error while calling AI provider: {exc}"
            logger.error(message)
            if attempt < max_attempts:
                time.sleep(2)
                continue
            raise RuntimeError(message)

    raise RuntimeError("Failed to generate MCQs from Ollama")