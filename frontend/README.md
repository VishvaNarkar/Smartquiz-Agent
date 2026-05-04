# ⚛️ SmartQuiz Frontend

Modern Next.js frontend for SmartQuiz Agent.

## ✨ Frontend Capabilities

- 🔐 Login/register UI connected to backend auth
- 🧭 Dashboard and sidebar navigation
- 🧠 Custom and adaptive quiz flows, including quizzes generated from uploaded documents
- ✅ Results and detailed review screens
- 📦 Settings page for AI provider selection and credentials upload
- 🔄 Session expiry handling with auto-redirect and friendly toast
- 📄 Document uploads through the custom quiz page using the backend `/quiz/document` endpoint

## 🚀 Run Locally

```bash
npm install
npm run dev
```

App URL: http://localhost:3000

## 🏗️ Build for Production

```bash
npm run build
npm start
```

## ⚙️ Frontend Environment

Create `frontend/.env.local` if needed:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If you want a starter file, copy [frontend/.env.example](frontend/.env.example) to `frontend/.env.local`.

## 🧱 Architecture Overview

- `src/app` → App Router pages/layouts
- `src/lib/api.ts` → Axios client + auth interceptors + token refresh flow
- `src/store/store.ts` → Zustand state (auth/session + quiz state)
- `src/app/globals.css` → shared design tokens/utilities

## 🔐 Session/Auth Behavior

- Login receives bearer token from backend.
- Token is persisted in auth store.
- API requests attach token automatically.
- Near expiry, token refresh is attempted.
- On expired session/401, frontend logs out, toasts, and redirects to `/`.

## 📄 Main Routes

- `/` login/register
- `/dashboard`
- `/dashboard/quiz-custom`
- `/dashboard/quiz-adaptive`
- `/dashboard/quiz`
- `/dashboard/results`
- `/dashboard/history`
- `/dashboard/settings`

## 🧪 Dev Checks

```bash
npm run build
```

If build passes, TypeScript and route-level bundling are healthy.

## 🛠️ Troubleshooting

| Issue | Quick Fix |
|---|---|
| API 401 on dashboard | Log in again to refresh session/token |
| API base URL wrong | Check `NEXT_PUBLIC_API_URL` |
| Styling looks broken | Restart dev server and verify Tailwind setup |
| Page stuck after auth | Clear local storage and re-login |
