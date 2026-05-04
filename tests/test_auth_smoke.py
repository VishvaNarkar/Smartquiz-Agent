from fastapi.testclient import TestClient
import api_server


def _reset_rate_limits():
    api_server._rate_limit_buckets["login"].clear()
    api_server._rate_limit_buckets["refresh"].clear()


def test_auth_login_refresh_and_ownership_flow(monkeypatch):
    _reset_rate_limits()

    monkeypatch.setattr(
        api_server.api,
        "authenticate_user",
        lambda username, password: username == "Alice_1" and password == "Password123",
    )
    monkeypatch.setattr(
        api_server.api,
        "resolve_username",
        lambda username: "Alice_1" if username.strip() in {"Alice_1", "Alice One"} else username,
    )
    monkeypatch.setattr(
        api_server.api,
        "get_user_analytics",
        lambda username: {
            "total_quizzes": 0,
            "average_score": 0.0,
            "weak_topics": [],
            "recent_quizzes": [],
            "topic_performance": {},
        },
    )

    client = TestClient(api_server.app)

    login_response = client.post(
        "/auth/login",
        json={"username": "Alice One", "password": "Password123"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["user"] == "Alice_1"
    assert login_body.get("access_token")

    headers = {"Authorization": f"Bearer {login_body['access_token']}"}

    refresh_response = client.post("/auth/refresh", headers=headers)
    assert refresh_response.status_code == 200
    assert refresh_response.json().get("access_token")

    own_response = client.get("/user/Alice_1/analytics", headers=headers)
    assert own_response.status_code == 200

    forbidden_response = client.get("/user/Bob/analytics", headers=headers)
    assert forbidden_response.status_code == 403


def test_login_rate_limit_smoke(monkeypatch):
    _reset_rate_limits()

    monkeypatch.setattr(api_server.api, "authenticate_user", lambda username, password: False)

    client = TestClient(api_server.app)

    for _ in range(api_server.LOGIN_RATE_LIMIT_MAX_REQUESTS):
        response = client.post(
            "/auth/login",
            json={"username": "RateUser", "password": "WrongPassword123"},
        )
        assert response.status_code == 401

    throttled = client.post(
        "/auth/login",
        json={"username": "RateUser", "password": "WrongPassword123"},
    )
    assert throttled.status_code == 429


def test_refresh_requires_token_and_credentials_upload_validation(monkeypatch):
    _reset_rate_limits()

    monkeypatch.setattr(api_server.api, "authenticate_user", lambda username, password: True)
    monkeypatch.setattr(api_server.api, "resolve_username", lambda username: username.strip())

    client = TestClient(api_server.app)

    no_auth_refresh = client.post("/auth/refresh")
    assert no_auth_refresh.status_code == 401

    login_response = client.post(
        "/auth/login",
        json={"username": "Uploader_1", "password": "Password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    bad_upload = client.post(
        "/credentials/upload",
        headers=headers,
        files={"file": ("credentials.json", b"not-json", "application/json")},
    )
    assert bad_upload.status_code == 400


def test_document_quiz_endpoint_validation(monkeypatch):
    _reset_rate_limits()

    monkeypatch.setattr(api_server.api, "authenticate_user", lambda username, password: True)
    monkeypatch.setattr(api_server.api, "resolve_username", lambda username: username.strip())

    client = TestClient(api_server.app)

    login_response = client.post(
        "/auth/login",
        json={"username": "DocUser", "password": "Password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    bad_extension = client.post(
        "/quiz/document",
        headers=headers,
        data={"username": "DocUser", "difficulty": "Medium", "num_questions": "5"},
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert bad_extension.status_code == 400
