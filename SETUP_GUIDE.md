# 🛠️ SmartQuiz Agent Setup Guide

This guide walks you through local setup, secure configuration, and verification for both backend and frontend.

It also covers the document-upload quiz flow, which accepts PDF, PPT/PPTX, DOC, and DOCX files and generates questions from extracted text.

## ✅ Prerequisites

- 🐍 Python 3.10+
- 🟢 Node.js 18+
- 📦 pip + npm
- 🤖 Optional: Ollama (for local model inference)
- 📄 Document parsing libraries are installed through `requirements.txt` (`pypdf`, `python-docx`, and `python-pptx`)

## 1️⃣ Clone and Enter Project

```bash
git clone https://github.com/VishvaNarkar/Smartquiz-Agent.git
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

This installs the document-upload parsers used by the `/quiz/document` endpoint. Legacy `.doc` files may still need conversion to `.docx` or PDF if extraction support is unavailable in your environment.

## 3️⃣ Frontend Setup

```bash
cd frontend
npm install
cd ..
```

## 4️⃣ Environment Configuration

Create a backend `.env` file in the project root for server settings. If you want a frontend starter file, copy the example into `frontend/.env.local`:

```bash
cp frontend/.env.example frontend/.env.local
```

Recommended values:

- `SMARTQUIZ_AUTH_SECRET` for token signing
- `SMARTQUIZ_CLOUD_API_KEY` for cloud model usage
- `OLLAMA_URL` and `OLLAMA_MODEL` for local inference
- For document quizzes, keep the upload under 12 MB and use a supported file type.

Frontend optional file (`frontend/.env.local`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 5️⃣ Start Application

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
- Document quiz test: open the custom quiz page, switch to Document Upload, and verify a small PDF, DOCX, or PPTX can be uploaded successfully.
- Google credentials test: upload a valid `credentials.json` and confirm the form export path works from the dashboard settings page.

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
| Credentials upload rejected | Ensure the file is `.json`, under 1MB, and includes either `installed` or `web` with `client_id`, `client_secret`, `auth_uri`, and `token_uri` |
| Document upload rejected | Check file type, confirm the file is under 12 MB, and convert legacy `.doc` files to `.docx` or PDF if text extraction fails |
| Frontend cannot reach backend | Check `NEXT_PUBLIC_API_URL` and backend port |

## 📌 Related Docs

- Project overview: [README.md](README.md)
- Credentials recovery: [CREDENTIALS_RECOVERY.md](CREDENTIALS_RECOVERY.md)
- Security policy: [SECURITY.md](SECURITY.md)
