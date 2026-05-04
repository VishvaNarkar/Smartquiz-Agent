import pytest
import json
from core.validator import validate_mcqs
from services.api import SmartQuizAPI
from services.scoring import evaluate
from services.user_manager import UserManager
from services.document_processor import build_document_topic, extract_document_text

def test_validate_mcqs():
    # Valid MCQs
    valid_mcqs = [
        {
            "question": "What is 2+2?",
            "options": ["3", "4", "5", "6"],
            "answer": "4"
        }
    ]
    assert len(validate_mcqs(valid_mcqs)) == 1

    # Invalid MCQs
    invalid_mcqs = [
        {
            "question": "What is 2+2?",
            "options": ["3", "4"],  # Only 2 options
            "answer": "4"
        },
        {
            "options": ["A", "B", "C", "D"],  # Missing question
            "answer": "A"
        }
    ]
    assert len(validate_mcqs(invalid_mcqs)) == 0

def test_validate_letter_answers():
    mcqs = [
        {
            "question": "What does VLAN stand for?",
            "options": [
                "Virtual Local Area Network",
                "Vital Link Automation Network",
                "Voice Local Access Network",
                "Video LAN"
            ],
            "answer": "A"
        }
    ]
    normalized = validate_mcqs(mcqs)
    assert normalized[0]["answer"] == "Virtual Local Area Network"

def test_evaluate():
    mcqs = [
        {
            "question": "What is 2+2?",
            "options": ["3", "4", "5", "6"],
            "answer": "4"
        },
        {
            "question": "What is 3+3?",
            "options": ["5", "6", "7", "8"],
            "answer": "6"
        }
    ]

    # Correct answers
    user_answers = ["4", "6"]
    score, results = evaluate(mcqs, user_answers)
    assert score == 2
    assert len(results) == 2
    assert results[0]["status"] == "✅"
    assert results[1]["status"] == "✅"

def test_user_registration_login_and_analytics(tmp_path):
    user_manager = UserManager(data_dir=str(tmp_path))

    assert user_manager.register_user("Alice", "Password123", "alice@example.com")
    assert user_manager.authenticate_user("Alice", "Password123")
    assert user_manager.authenticate_user(" Alice ", "Password123")
    assert not user_manager.authenticate_user("Alice", "WrongPassword")

    quiz_data = {
        "topic": "Math",
        "difficulty": "Easy",
        "questions": ["q1", "q2"],
    }
    user_manager.save_quiz_result("Alice", quiz_data, 2)

    analytics = user_manager.get_user_analytics("Alice")
    assert analytics["total_quizzes"] == 1
    assert analytics["average_score"] == 100.0
    assert analytics["recent_quizzes"]
    assert analytics["recent_quizzes"][0]["topic"] == "Math"
    assert analytics["weak_topics"] == []


def test_legacy_username_migration_and_alias_lookup(tmp_path):
    users_file = tmp_path / "users.json"
    history_file = tmp_path / "quiz_history.json"
    legacy_quiz_file = tmp_path / "user_Alice Smith_quizzes.json"

    users_file.write_text(
        json.dumps(
            {
                "Alice Smith": {
                    "password": "$2b$12$N2OnXQDzM3aMZxxg4B3T5eq7Q.JkSQ0E2fM2xR9gXR1W1sm.fY5m6",
                    "email": "",
                    "created_at": "2026-04-01T00:00:00",
                    "weak_topics": {},
                    "total_quizzes": 1,
                    "average_score": 2.0,
                }
            }
        ),
        encoding="utf-8",
    )
    history_file.write_text(
        json.dumps(
            {
                "Alice Smith": [
                    {
                        "timestamp": "2026-04-01T00:00:00",
                        "topic": "Math",
                        "difficulty": "Easy",
                        "num_questions": 2,
                        "score": 2,
                        "questions": ["q1", "q2"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    legacy_quiz_file.write_text("[]", encoding="utf-8")

    user_manager = UserManager(data_dir=str(tmp_path))

    assert "Alice_Smith" in user_manager.users
    assert user_manager.resolve_username("Alice Smith") == "Alice_Smith"
    assert user_manager.users["Alice_Smith"]["average_score"] == 100.0
    assert (tmp_path / "user_Alice_Smith_quizzes.json").exists()


def test_api_custom_and_adaptive_quiz_generation(monkeypatch, tmp_path):
    api = SmartQuizAPI()
    api.user_manager = UserManager(data_dir=str(tmp_path))

    assert api.register_user("Bob", "SecurePass123", "bob@example.com")
    assert api.authenticate_user("Bob", "SecurePass123")

    fake_mcqs = [
        {
            "question": "What color is the sky?",
            "options": ["Blue", "Green", "Red", "Yellow"],
            "answer": "Blue"
        }
    ]

    saved_quizzes = []
    monkeypatch.setattr(api.ai_service, "generate_quiz", lambda topic, difficulty, num, **kwargs: fake_mcqs)
    monkeypatch.setattr("services.api.save_quiz", lambda quiz_data, username: saved_quizzes.append((quiz_data, username)))

    generated = api.generate_custom_quiz("Bob", "Science", "Easy", 1)
    assert generated == validate_mcqs(fake_mcqs)
    assert saved_quizzes and saved_quizzes[-1][1] == "Bob"

    monkeypatch.setattr(api.adaptive_engine, "generate_adaptive_quiz", lambda username, num, **kwargs: (fake_mcqs, "Science"))
    adaptive_mcqs, topic = api.generate_adaptive_quiz("Bob", 1)
    assert adaptive_mcqs == validate_mcqs(fake_mcqs)
    assert topic == "Science"
    assert saved_quizzes[-1][1] == "Bob"


def test_document_quiz_generation_uses_uploaded_text(monkeypatch, tmp_path):
    api = SmartQuizAPI()
    api.user_manager = UserManager(data_dir=str(tmp_path))

    assert api.register_user("Dana", "SecurePass123", "dana@example.com")

    fake_mcqs = [
        {
            "question": "What is the main idea?",
            "options": ["A", "B", "C", "D"],
            "answer": "A"
        }
    ]

    captured = {}

    def fake_generate_quiz(topic, difficulty, num, **kwargs):
        captured["topic"] = topic
        captured["difficulty"] = difficulty
        captured["num"] = num
        captured["source_text"] = kwargs.get("source_text")
        captured["source_label"] = kwargs.get("source_label")
        return fake_mcqs

    monkeypatch.setattr(api.ai_service, "generate_quiz", fake_generate_quiz)
    monkeypatch.setattr("services.api.save_quiz", lambda quiz_data, username: None)

    mcqs, topic, quiz_id = api.generate_document_quiz_with_id(
        "Dana",
        "lesson-notes.pdf",
        "This is the extracted document text.",
        "Medium",
        3,
    )

    assert mcqs == validate_mcqs(fake_mcqs)
    assert topic == "lesson notes"
    assert quiz_id
    assert captured["source_text"] == "This is the extracted document text."
    assert captured["source_label"] == "lesson-notes.pdf"


def test_document_topic_and_extraction_helpers():
    assert build_document_topic("chapter-one.docx") == "chapter one"

    with pytest.raises(ValueError):
        extract_document_text("notes.txt", b"plain text")


def test_save_quiz_result_initializes_missing_history_bucket(tmp_path):
    user_manager = UserManager(data_dir=str(tmp_path))
    assert user_manager.register_user("Eve", "Password123", "eve@example.com")

    # Simulate a partially migrated data file where the user exists but history was not created.
    user_manager.quiz_history.pop("Eve", None)

    quiz_data = {
        "topic": "Math",
        "difficulty": "Easy",
        "questions": [{"question": "Q1", "options": ["A", "B", "C", "D"], "answer": "A"}],
    }

    user_manager.save_quiz_result("Eve", quiz_data, 1)

    assert user_manager.quiz_history["Eve"]
    assert user_manager.quiz_history["Eve"][0]["topic"] == "Math"


def test_adaptive_review_fallback_uses_last_topic(monkeypatch, tmp_path):
    api = SmartQuizAPI()
    api.user_manager = UserManager(data_dir=str(tmp_path))
    api.adaptive_engine = api.adaptive_engine.__class__(api.user_manager, api.ai_service)

    assert api.register_user("Carol", "ReviewPass123", "carol@example.com")
    assert api.authenticate_user("Carol", "ReviewPass123")

    quiz_data = {
        "topic": "Firewall",
        "difficulty": "Medium",
        "questions": [
            {"question": "Q1", "options": ["A", "B", "C", "D"], "answer": "A"}
        ]
    }
    api.user_manager.save_quiz_result("Carol", quiz_data, 1)

    fake_mcqs = [
        {"question": "Firewall review", "options": ["A", "B", "C", "D"], "answer": "A"}
    ]
    monkeypatch.setattr(api.ai_service, "generate_quiz", lambda topic, difficulty, num, **kwargs: fake_mcqs)

    adaptive_mcqs, topic = api.generate_adaptive_quiz("Carol", 1)
    assert adaptive_mcqs == validate_mcqs(fake_mcqs)
    assert topic == "Firewall"
