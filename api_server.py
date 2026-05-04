"""
FastAPI server for SmartQuiz Agent
Wraps existing Python services and exposes them as REST API
"""

import os
import sys
import re
import time
import json
import base64
import hmac
import hashlib
import secrets
from threading import Lock
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from services.api import SmartQuizAPI
from services.document_processor import (
    MAX_DOCUMENT_BYTES,
    build_document_topic,
    extract_document_text,
    is_supported_document,
)
from services.settings_manager import SettingsManager
from config import OLLAMA_MODEL, OLLAMA_URL

ALLOWED_CLOUD_CHAT_COMPLETIONS_URLS = {
    "https://api.groq.com/openai/v1/chat/completions",
    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
}
USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_]{3,32}$")
AUTH_SECRET_FILE = "data/.auth_secret"
TOKEN_EXPIRY_SECONDS = 60 * 60 * 24
MAX_CREDENTIALS_FILE_BYTES = 1 * 1024 * 1024
ALLOWED_CREDENTIALS_CONTENT_TYPES = {
    "application/json",
    "text/json",
    "application/octet-stream",
}

LOGIN_RATE_LIMIT_MAX_REQUESTS = 10
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 60
REFRESH_RATE_LIMIT_MAX_REQUESTS = 30
REFRESH_RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_lock = Lock()
_rate_limit_buckets: Dict[str, Dict[str, List[float]]] = {
    "login": {},
    "refresh": {},
}

app = FastAPI(title="SmartQuiz Agent API", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize API
api = SmartQuizAPI()


# ============================================================================
# Request/Response Models
# ============================================================================


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = ""


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[str] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None


class QuizGenerationRequest(BaseModel):
    username: str
    topic: str
    difficulty: str
    num_questions: int = 5


class AdaptiveQuizRequest(BaseModel):
    username: str
    num_questions: int = 5


class DeleteQuizRequest(BaseModel):
    username: str
    quiz_id: str


class QuizSubmissionRequest(BaseModel):
    username: str
    topic: str
    difficulty: str
    questions: List[Dict[str, Any]]
    answers: List[str]
    quiz_id: Optional[str] = None


class AISettingsRequest(BaseModel):
    ai_source: str
    ai_model: str
    ai_api_url: str
    ai_api_key: str


class ExportGoogleFormRequest(BaseModel):
    username: str
    mcqs: List[Dict[str, Any]]
    topic: Optional[str] = None


# ============================================================================
# Auth & Validation Helpers
# ============================================================================


def _normalize_and_validate_username(username: str) -> str:
    normalized = (username or "").strip()
    if not USERNAME_REGEX.fullmatch(normalized):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-32 chars and contain only letters, numbers, or underscore",
        )
    return normalized


def _resolve_username_with_compat(username: str) -> str:
    normalized = (username or "").strip()
    if USERNAME_REGEX.fullmatch(normalized):
        return normalized

    resolved = api.resolve_username(normalized)
    if resolved and USERNAME_REGEX.fullmatch(resolved):
        return resolved

    raise HTTPException(
        status_code=400,
        detail="Username must be 3-32 chars and contain only letters, numbers, or underscore",
    )


def _ensure_ownership(request_username: str, current_username: str) -> None:
    if request_username != current_username:
        raise HTTPException(status_code=403, detail="You can only access your own resources")


def _enforce_rate_limit(bucket: str, key: str, max_requests: int, window_seconds: int) -> None:
    now = time.time()
    with _rate_limit_lock:
        bucket_entries = _rate_limit_buckets.setdefault(bucket, {})
        timestamps = bucket_entries.get(key, [])
        timestamps = [ts for ts in timestamps if now - ts < window_seconds]
        if len(timestamps) >= max_requests:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again shortly.")
        timestamps.append(now)
        bucket_entries[key] = timestamps


def _validate_google_credentials_json(contents: bytes) -> Dict[str, Any]:
    if len(contents) > MAX_CREDENTIALS_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Credentials file exceeds max size of 1MB")

    try:
        parsed = json.loads(contents.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON credentials file") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="Invalid credentials format")

    root_key = "installed" if isinstance(parsed.get("installed"), dict) else "web" if isinstance(parsed.get("web"), dict) else None
    if not root_key:
        raise HTTPException(status_code=400, detail="Credentials must contain 'installed' or 'web' configuration")

    config = parsed[root_key]
    required_fields = ["client_id", "client_secret", "auth_uri", "token_uri"]
    missing = [field for field in required_fields if not config.get(field)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Credentials missing required fields: {', '.join(missing)}")

    return parsed


def _get_auth_secret() -> bytes:
    env_secret = os.getenv("SMARTQUIZ_AUTH_SECRET", "").strip()
    if env_secret:
        return env_secret.encode("utf-8")

    os.makedirs(os.path.dirname(AUTH_SECRET_FILE), exist_ok=True)
    if os.path.exists(AUTH_SECRET_FILE):
        with open(AUTH_SECRET_FILE, "rb") as f:
            existing = f.read().strip()
            if existing:
                return existing

    generated = secrets.token_urlsafe(48).encode("utf-8")
    with open(AUTH_SECRET_FILE, "wb") as f:
        f.write(generated)
    return generated


def _b64url_encode(raw_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def _create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
    }
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(_get_auth_secret(), payload_part.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload_part}.{_b64url_encode(signature)}"


def _verify_access_token(token: str) -> str:
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

    expected_signature = hmac.new(_get_auth_secret(), payload_part.encode("utf-8"), hashlib.sha256).digest()
    provided_signature = _b64url_decode(signature_part)
    if not hmac.compare_digest(expected_signature, provided_signature):
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token payload") from exc

    username = _normalize_and_validate_username(payload.get("sub", ""))
    exp = int(payload.get("exp", 0))
    if exp <= int(time.time()):
        raise HTTPException(status_code=401, detail="Authentication token expired")

    return username


def get_current_user(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    return _verify_access_token(token)


def _normalize_ai_source(ai_source: str | None) -> str:
    source = (ai_source or "ollama").strip().lower().replace(" ", "")
    if source in ("ollama", "localollama"):
        return "ollama"
    return "openai"


def _default_api_url(ai_source: str) -> str:
    if ai_source == "ollama":
        return OLLAMA_URL
    return "https://api.groq.com/openai/v1/chat/completions"


def _normalize_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _is_allowed_cloud_api_url(url: str) -> bool:
    return _normalize_url(url) in ALLOWED_CLOUD_CHAT_COMPLETIONS_URLS


def _get_runtime_ai_config() -> Dict[str, str]:
    saved = SettingsManager.load_ai_settings() or {}
    ai_source = _normalize_ai_source(saved.get("ai_source"))

    if ai_source == "ollama":
        fallback_model = OLLAMA_MODEL
        fallback_key = ""
    else:
        fallback_model = "llama-3.1-8b-instant"
        fallback_key = ""

    ai_model = (saved.get("ai_model") or fallback_model).strip()
    ai_api_url = _normalize_url((saved.get("ai_api_url") or "").strip() or _default_api_url(ai_source))
    ai_api_key = (saved.get("ai_api_key") or fallback_key).strip()

    return {
        "ai_source": ai_source,
        "ai_model": ai_model,
        "ai_api_url": ai_api_url,
        "ai_api_key": ai_api_key,
    }


# ============================================================================
# Health Check
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# Authentication Endpoints
# ============================================================================


@app.post("/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user."""
    try:
        username = _normalize_and_validate_username(request.username)
        success = api.register_user(username, request.password, request.email or "")
        if success:
            return AuthResponse(
                success=True,
                message="Registration successful. Please login.",
            )

        raise HTTPException(
            status_code=400,
            detail="Username already exists or invalid input",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest, raw_request: Request):
    """Authenticate a user."""
    try:
        client_ip = raw_request.client.host if raw_request.client else "unknown"
        attempted_username = (request.username or "").strip()
        _enforce_rate_limit(
            "login",
            f"{client_ip}:{attempted_username.lower()}",
            LOGIN_RATE_LIMIT_MAX_REQUESTS,
            LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        )

        username = _resolve_username_with_compat(request.username)
        success = api.authenticate_user(username, request.password)
        if success:
            access_token = _create_access_token(username)
            return AuthResponse(
                success=True,
                message="Login successful",
                user=username,
                access_token=access_token,
                token_type="bearer",
            )

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/refresh", response_model=AuthResponse)
async def refresh_token(raw_request: Request, current_user: str = Depends(get_current_user)):
    """Refresh access token for authenticated user."""
    try:
        client_ip = raw_request.client.host if raw_request.client else "unknown"
        _enforce_rate_limit(
            "refresh",
            f"{client_ip}:{current_user}",
            REFRESH_RATE_LIMIT_MAX_REQUESTS,
            REFRESH_RATE_LIMIT_WINDOW_SECONDS,
        )

        access_token = _create_access_token(current_user)
        return AuthResponse(
            success=True,
            message="Token refreshed",
            user=current_user,
            access_token=access_token,
            token_type="bearer",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Quiz Endpoints
# ============================================================================


@app.post("/quiz/custom")
async def generate_custom_quiz(request: QuizGenerationRequest, current_user: str = Depends(get_current_user)):
    """Generate a custom quiz."""
    try:
        request_username = _resolve_username_with_compat(request.username)
        _ensure_ownership(request_username, current_user)

        runtime_config = _get_runtime_ai_config()
        if runtime_config["ai_source"] != "ollama" and not _is_allowed_cloud_api_url(runtime_config["ai_api_url"]):
            raise HTTPException(
                status_code=400,
                detail="Only Groq and Gemini API URLs are allowed for cloud providers",
            )
        if runtime_config["ai_source"] != "ollama" and not runtime_config["ai_api_key"]:
            raise HTTPException(status_code=400, detail="API key is required for cloud AI providers")

        mcqs, quiz_id = api.generate_custom_quiz_with_id(
            request_username,
            request.topic,
            request.difficulty,
            request.num_questions,
            model=runtime_config["ai_model"],
            api_url=runtime_config["ai_api_url"],
            api_key=runtime_config["ai_api_key"] or None,
        )
        return {
            "success": True,
            "quiz_id": quiz_id,
            "quiz": mcqs,
            "topic": request.topic,
            "difficulty": request.difficulty,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quiz/document")
async def generate_document_quiz(
    username: str = Form(...),
    difficulty: str = Form(...),
    num_questions: int = Form(5),
    topic: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    """Generate a quiz from an uploaded document."""
    try:
        request_username = _resolve_username_with_compat(username)
        _ensure_ownership(request_username, current_user)

        filename = (file.filename or "").strip()
        if not filename:
            raise HTTPException(status_code=400, detail="A valid file name is required")

        if not is_supported_document(filename):
            raise HTTPException(status_code=400, detail="Please upload a PDF, PPT/PPTX, DOC, or DOCX file")

        contents = await file.read(MAX_DOCUMENT_BYTES + 1)
        if len(contents) > MAX_DOCUMENT_BYTES:
            raise HTTPException(status_code=413, detail="Document exceeds the 12MB upload limit")

        document_text = extract_document_text(filename, contents)
        topic_name = (topic or "").strip() or build_document_topic(filename)

        config = _get_runtime_ai_config()
        mcqs, topic_name, quiz_id = api.generate_document_quiz_with_id(
            request_username,
            filename,
            document_text,
            difficulty,
            num_questions,
            topic=topic_name,
            model=config["ai_model"],
            api_url=config["ai_api_url"],
            api_key=config["ai_api_key"],
        )

        return {
            "success": True,
            "quiz_id": quiz_id,
            "quiz": mcqs,
            "topic": topic_name,
            "difficulty": difficulty,
            "source_type": "document",
            "source_name": filename,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quiz/adaptive")
async def generate_adaptive_quiz(request: AdaptiveQuizRequest, current_user: str = Depends(get_current_user)):
    """Generate an adaptive quiz based on weak topics."""
    try:
        request_username = _resolve_username_with_compat(request.username)
        _ensure_ownership(request_username, current_user)

        runtime_config = _get_runtime_ai_config()
        if runtime_config["ai_source"] != "ollama" and not _is_allowed_cloud_api_url(runtime_config["ai_api_url"]):
            raise HTTPException(
                status_code=400,
                detail="Only Groq and Gemini API URLs are allowed for cloud providers",
            )
        if runtime_config["ai_source"] != "ollama" and not runtime_config["ai_api_key"]:
            raise HTTPException(status_code=400, detail="API key is required for cloud AI providers")

        mcqs, topic, quiz_id = api.generate_adaptive_quiz_with_id(
            request_username,
            request.num_questions,
            model=runtime_config["ai_model"],
            api_url=runtime_config["ai_api_url"],
            api_key=runtime_config["ai_api_key"] or None,
        )
        return {
            "success": True,
            "quiz_id": quiz_id,
            "quiz": mcqs,
            "topic": topic,
            "difficulty": "Adaptive",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quiz/submit")
async def submit_quiz(request: QuizSubmissionRequest, current_user: str = Depends(get_current_user)):
    """Submit quiz answers and get results."""
    try:
        request_username = _resolve_username_with_compat(request.username)
        _ensure_ownership(request_username, current_user)

        # Evaluate answers
        from services.scoring import evaluate

        score, results = evaluate(request.questions, request.answers)

        # Save results
        quiz_data = {
            "topic": request.topic,
            "difficulty": request.difficulty,
            "questions": request.questions,
        }
        api.save_quiz_result(request_username, quiz_data, score)
        api.sync_quiz_score(
            request_username,
            request.topic,
            request.difficulty,
            len(request.questions),
            score,
            quiz_id=request.quiz_id,
            submitted_answers=request.answers,
            results=results,
        )

        # Get analysis
        analysis = api.analyze_performance(
            request_username,
            {"score": score, "questions": request.questions},
        )

        return {
            "success": True,
            "score": score,
            "total": len(results),
            "results": [
                {
                    "question": r["question"],
                    "correct": r["correct"],
                    "your_answer": r["your_answer"],
                    "status": r["status"],
                }
                for r in results
            ],
            "analysis": analysis,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# User Analytics Endpoints
# ============================================================================


@app.get("/user/{username}/analytics")
async def get_user_analytics(username: str, current_user: str = Depends(get_current_user)):
    """Get user analytics and profile data."""
    try:
        request_username = _resolve_username_with_compat(username)
        _ensure_ownership(request_username, current_user)

        analytics = api.get_user_analytics(request_username)
        return {
            "success": True,
            "analytics": analytics,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{username}/quizzes")
async def get_recent_quizzes(username: str, current_user: str = Depends(get_current_user)):
    """Get recent quizzes for a user."""
    try:
        request_username = _resolve_username_with_compat(username)
        _ensure_ownership(request_username, current_user)

        quizzes = api.get_recent_quizzes(request_username)
        return {
            "success": True,
            "quizzes": quizzes,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{username}/quizzes/{quiz_id}")
async def get_user_quiz(username: str, quiz_id: str, current_user: str = Depends(get_current_user)):
    """Get a specific quiz for a user."""
    try:
        request_username = _resolve_username_with_compat(username)
        _ensure_ownership(request_username, current_user)

        quiz = api.get_quiz(request_username, quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        return {
            "success": True,
            "quiz": quiz,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/user/quiz")
async def delete_user_quiz(request: DeleteQuizRequest, current_user: str = Depends(get_current_user)):
    """Delete a quiz for a user by quiz ID."""
    try:
        request_username = _resolve_username_with_compat(request.username)
        _ensure_ownership(request_username, current_user)

        deleted = api.delete_quiz(request_username, request.quiz_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Quiz not found")

        return {
            "success": True,
            "message": "Quiz deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/user/quiz/delete")
async def delete_user_quiz_fallback(request: DeleteQuizRequest, current_user: str = Depends(get_current_user)):
    """Fallback delete endpoint for clients/environments that block DELETE with JSON body."""
    return await delete_user_quiz(request, current_user)


# ============================================================================
# AI Settings Endpoints
# ============================================================================


@app.get("/settings/ai")
async def get_ai_settings(current_user: str = Depends(get_current_user)):
    """Get current AI settings."""
    try:
        settings = _get_runtime_ai_config()
        # Never return API key material in settings response.
        settings["ai_api_key"] = ""
        return {
            "success": True,
            "settings": settings,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/settings/ai")
async def save_ai_settings(request: AISettingsRequest, current_user: str = Depends(get_current_user)):
    """Save AI settings."""
    try:
        normalized_source = _normalize_ai_source(request.ai_source)
        normalized_model = request.ai_model.strip() or (OLLAMA_MODEL if normalized_source == "ollama" else "llama-3.1-8b-instant")
        normalized_url = _normalize_url(request.ai_api_url.strip() or _default_api_url(normalized_source))
        normalized_key = request.ai_api_key.strip() if normalized_source != "ollama" else ""

        if normalized_source == "ollama":
            normalized_url = OLLAMA_URL
            normalized_key = ""
        elif not _is_allowed_cloud_api_url(normalized_url):
            raise HTTPException(
                status_code=400,
                detail="Only Groq and Gemini API URLs are allowed for cloud providers",
            )
        elif not normalized_key:
            existing_settings = SettingsManager.load_ai_settings() or {}
            normalized_key = (existing_settings.get("ai_api_key") or "").strip()
            if not normalized_key:
                raise HTTPException(status_code=400, detail="API key is required for cloud AI providers")

        success = SettingsManager.save_ai_settings(
            normalized_source,
            normalized_model,
            normalized_url,
            normalized_key,
        )
        if success:
            return {
                "success": True,
                "message": "AI settings saved successfully",
            }

        raise HTTPException(status_code=500, detail="Failed to save settings")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Google Forms Export (Placeholder)
# ============================================================================


@app.post("/quiz/export-google-form")
async def export_to_google_form(request: ExportGoogleFormRequest, current_user: str = Depends(get_current_user)):
    """Export quiz to Google Forms."""
    try:
        request_username = _resolve_username_with_compat(request.username)
        _ensure_ownership(request_username, current_user)

        topic = (request.topic or "").strip()
        title = f"{topic} Quiz" if topic else f"{request_username}'s Quiz"
        link = api.export_google_form(request.mcqs, title=title)
        return {
            "success": True,
            "link": link,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Credentials Upload (Placeholder)
# ============================================================================


@app.post("/credentials/upload")
async def upload_credentials(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    """Upload Google API credentials."""
    try:
        filename = (file.filename or "").lower()
        content_type = (file.content_type or "").lower()

        if not filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="Only .json credentials files are allowed")
        if content_type and content_type not in ALLOWED_CREDENTIALS_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported file content type")

        credentials_path = os.path.join("auth", "credentials.json")
        os.makedirs(os.path.dirname(credentials_path), exist_ok=True)

        contents = await file.read()
        validated = _validate_google_credentials_json(contents)

        with open(credentials_path, "wb") as f:
            f.write(json.dumps(validated, indent=2).encode("utf-8"))

        return {
            "success": True,
            "message": "Credentials uploaded successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
