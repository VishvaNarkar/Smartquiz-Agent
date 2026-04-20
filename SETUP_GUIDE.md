# 🛠️ SmartQuiz Agent Setup Guide

This guide walks you through local setup, secure configuration, and verification for both backend and frontend.

## ✅ Prerequisites

- 🐍 Python 3.10+
- 🟢 Node.js 18+
- 📦 pip + npm
- 🤖 Optional: Ollama (for local model inference)

## 1️⃣ Clone and Enter Project

```bash
git clone <your-repo-url>
cd smartquiz-agent
```

## 2️⃣ Backend Setup

### Create and activate virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install backend dependencies

```bash
python -m pip install -r requirements.txt
```

## 3️⃣ Frontend Setup

```bash
cd frontend
npm install
cd ..
```

## 4️⃣ Environment Configuration

Copy and edit env file:

```bash
cp .env.example .env
```

Recommended values:

- `SMARTQUIZ_AUTH_SECRET` for token signing
- `SMARTQUIZ_CLOUD_API_KEY` for cloud model usage
- `OLLAMA_URL` and `OLLAMA_MODEL` for local inference

Frontend optional file (`frontend/.env.local`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 5️⃣ Start Application

### Fast path

Windows:

```bash
start-dev.bat
```

macOS/Linux:

```bash
chmod +x start-dev.sh
./start-dev.sh
```

### Manual path

Terminal A:

```bash
python api_server.py
```

Terminal B:

```bash
cd frontend
npm run dev
```

## 6️⃣ Verify Installation

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

## 7️⃣ Run Smoke Tests

```bash
python -m pytest -q tests/test_core.py tests/test_auth_smoke.py
```

## 🔐 Security Tips for Local Setup

- Never commit `.env`, credentials files, or data snapshots.
- Prefer environment variables for cloud API keys.
- Revoke and rotate provider keys if exposed.

## 🐳 Docker Quick Check

```bash
docker build -t smartquiz-agent .
docker run --rm -p 8000:8000 smartquiz-agent
```

## 🧯 Troubleshooting

| Problem | Fix |
|---|---|
| `401 Missing bearer token` | Login again and ensure frontend uses updated token flow |
| `429 Too many requests` | Wait for rate-limit window to reset |
| Cloud model not generating | Set `SMARTQUIZ_CLOUD_API_KEY` and verify provider URL in settings |
| Credentials upload rejected | Ensure JSON file includes Google OAuth required fields |
| Frontend cannot reach backend | Check `NEXT_PUBLIC_API_URL` and backend port |

## 📌 Related Docs

- Project overview: [README.md](README.md)
- Credentials recovery: [CREDENTIALS_RECOVERY.md](CREDENTIALS_RECOVERY.md)
- Security policy: [SECURITY.md](SECURITY.md)
