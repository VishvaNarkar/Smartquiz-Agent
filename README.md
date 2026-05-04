# 🧠 SmartQuiz Agent

An AI-powered adaptive quiz platform with a secure FastAPI backend and a modern Next.js frontend.
Build custom or adaptive quizzes, generate quizzes from uploaded documents, track progress, review detailed results, and export quizzes to Google Forms.

## ✨ Highlights

- 🤖 **AI Quiz Generation**: Generate MCQs with local Ollama, supported cloud endpoints, or uploaded documents.
- 👤 **Secure Auth Flow**: Login/registration with bcrypt hashing and bearer-token protected APIs.
- 🔄 **Session Safety**: Token refresh endpoint and friendly frontend auto-redirect on expiry.
- 🧭 **Adaptive Learning**: Target weak topics automatically based on previous performance.
- 📊 **Analytics Dashboard**: Track total quizzes, average score, weak topics, and recent performance.
- 📝 **Quiz Review Experience**: Detailed per-question breakdown with your answer vs correct answer.
- 📤 **Google Form Export**: Export quiz data to Google Forms with credentials upload.
- 🧱 **Clean Architecture**: Clear separation across API, services, core logic, and UI layers.

## 🏗️ Tech Stack

### Backend

- 🐍 Python + FastAPI
- ⚡ Uvicorn
- 🔐 bcrypt
- 📁 JSON persistence (local development friendly)

### Frontend

- ⚛️ Next.js (App Router)
- 🟦 TypeScript
- 🎨 Tailwind CSS
- 🗃️ Zustand
- 🌐 Axios + interceptor-based auth/session handling

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Optional for local model: Ollama

## 1️⃣ Clone and Enter Project

```bash
git clone https://github.com/VishvaNarkar/Smartquiz-Agent.git
cd smartquiz-agent
```

## 2️⃣ Install Dependencies

```bash
python -m pip install -r requirements.txt
cd frontend
npm install
```

## 3️⃣ Configure Environment

Create a root `.env` file for backend settings, and use the frontend example file if you want a starter for browser settings:

```bash
cp frontend/.env.example frontend/.env.local
```

Important variables:

- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `SMARTQUIZ_CLOUD_API_KEY`
- `SMARTQUIZ_AUTH_SECRET`
- Document uploads require the parser packages listed in `requirements.txt` (`pypdf`, `python-docx`, and `python-pptx`). Legacy `.doc` files may need to be converted to `.docx` or PDF if extraction fails.

Frontend optional config (`frontend/.env.local`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 4️⃣ Run App

```bash
python api_server.py
```

```bash
cd frontend
npm run dev
```

## 🌐 Default URLs

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## 🔌 API Overview

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`

### Quiz

- `POST /quiz/custom`
- `POST /quiz/document`
- `POST /quiz/adaptive`
- `POST /quiz/submit`
- `POST /quiz/export-google-form`

### User Data

- `GET /user/{username}/analytics`
- `GET /user/{username}/quizzes`
- `GET /user/{username}/quizzes/{quiz_id}`
- `DELETE /user/quiz`
- `POST /user/quiz/delete`

### Settings / Credentials

- `GET /settings/ai`
- `POST /settings/ai`
- `POST /credentials/upload`

The document quiz endpoint accepts multipart uploads with `username`, `difficulty`, `num_questions`, optional `topic`, and a file upload. Supported files are PDF, PPT/PPTX, DOC, and DOCX; the upload limit is 12 MB. For legacy `.doc` files, conversion to `.docx` or PDF is the safest path if text extraction is unavailable.

## 🔐 Security Model

- ✅ Bearer token required on protected endpoints.
- ✅ User ownership checks enforced on user-scoped APIs.
- ✅ Strict username rules + legacy alias migration support.
- ✅ Cloud API URL allowlist for supported providers.
- ✅ Credentials upload validation (type, size, JSON shape).
- ✅ Document quiz uploads with file type checks, size limits, and extracted-text parsing.
- ✅ Cloud API keys not persisted in plaintext settings files.

## 📁 Repository Structure

```text
smartquiz-agent/
├── api_server.py
├── config.py
├── requirements.txt
├── assets/
├── auth/
├── core/
├── data/
├── frontend/
├── services/
└── tests/
```

## 🧪 Testing

Run core + auth smoke tests:

```bash
python -m pytest -q tests/test_core.py tests/test_auth_smoke.py
```

Build frontend for production checks:

```bash
cd frontend
npm run build
```

## 🐳 Docker

Build and run backend container:

```bash
docker build -t smartquiz-agent .
docker run --rm -p 8000:8000 smartquiz-agent
```

Container health check uses `/health`.

## 🧰 Developer Notes

- 📚 Setup details: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- 🔐 Google credentials help: [CREDENTIALS_RECOVERY.md](CREDENTIALS_RECOVERY.md)
- 🤝 Contribution process: [CONTRIBUTING.md](CONTRIBUTING.md)
- 🛡️ Security reporting: [SECURITY.md](SECURITY.md)

## 🗺️ Roadmap Ideas

- 📈 Advanced progress visualizations
- 🧠 Better adaptive curriculum sequencing
- 🧪 Expanded test coverage (integration + e2e)

## 📜 License

MIT License
