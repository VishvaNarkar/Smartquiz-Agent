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

def generate_mcqs(topic: str, difficulty: str, num_questions: int = 5) -> List[Dict[str, Any]]:
    """
    Generate multiple-choice questions using Ollama API.

    Args:
        topic (str): The topic for the questions.
        difficulty (str): Difficulty level (Easy, Medium, Hard).
        num_questions (int): Number of questions to generate.

    Returns:
        list: List of validated MCQ dictionaries.

    Raises:
        RuntimeError: When Ollama returns an error or output is invalid.
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

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

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
            response = requests.post(OLLAMA_URL, json=payload, timeout=600)

            if response.status_code != 200:
                error_text = response.text.strip()
                message = f"Ollama API Error: {response.status_code} - {error_text}"
                logger.error(message)
                if attempt < max_attempts and response.status_code >= 500:
                    time.sleep(2)
                    continue
                raise RuntimeError(message)

            try:
                data = response.json()
                output = data.get("response") or data.get("output") or response.text
            except json.JSONDecodeError:
                output = response.text

            if not isinstance(output, str):
                output = str(output)

            output = output.strip()
            mcqs = clean_json_output(output)

            if not mcqs:
                logger.warning("No valid MCQs generated. Raw output: %s", output[:500])
                raise RuntimeError("Ollama returned invalid MCQ output")

            logger.info("Successfully generated %s MCQs", len(mcqs))
            return mcqs

        except requests.exceptions.RequestException as exc:
            message = f"Network error while calling Ollama: {exc}"
            logger.error(message)
            if attempt < max_attempts:
                time.sleep(2)
                continue
            raise RuntimeError(message)

    raise RuntimeError("Failed to generate MCQs from Ollama")