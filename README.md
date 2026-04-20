# 🧠 SmartQuiz Agent

An AI-powered adaptive quiz platform with a secure FastAPI backend and a modern Next.js frontend.
Build custom or adaptive quizzes, track progress, review detailed results, and export quizzes to Google Forms.

## ✨ Highlights

- 🤖 **AI Quiz Generation**: Generate MCQs with local Ollama or supported cloud endpoints.
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

### 1) Install dependencies

```bash
python -m pip install -r requirements.txt
cd frontend
npm install
```

### 2) Configure environment

Copy env example and set values as needed:

```bash
cp .env.example .env
```

Important variables:

- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `SMARTQUIZ_CLOUD_API_KEY`
- `SMARTQUIZ_AUTH_SECRET`

Frontend optional config (`frontend/.env.local`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3) Run app

#### Windows

```bash
start-dev.bat
```

#### macOS/Linux

```bash
chmod +x start-dev.sh
./start-dev.sh
```

Or run manually:

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

## 🔐 Security Model

- ✅ Bearer token required on protected endpoints.
- ✅ User ownership checks enforced on user-scoped APIs.
- ✅ Strict username rules + legacy alias migration support.
- ✅ Cloud API URL allowlist for supported providers.
- ✅ Credentials upload validation (type, size, JSON shape).
- ✅ Cloud API keys not persisted in plaintext settings files.

## 📁 Repository Structure

```text
smartquiz-agent/
├── api_server.py
├── config.py
├── requirements.txt
├── start-dev.bat
├── start-dev.sh
├── core/
├── services/
├── data/
├── tests/
├── frontend/
├── auth/
└── ui/                # Legacy Streamlit interface (optional)
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
