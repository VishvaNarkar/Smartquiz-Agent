# 🤝 Contributing to SmartQuiz Agent

Thanks for contributing.
This guide keeps changes consistent, secure, and easy to review.

## 🚀 Quick Contribution Flow

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/short-description
```

3. Implement your change with tests/docs updates.
4. Run checks locally.
5. Open a pull request with clear scope and rationale.

## ✅ Local Checks Before PR

Backend tests:

```bash
python -m pytest -q tests/test_core.py tests/test_auth_smoke.py
```

Frontend build:

```bash
cd frontend
npm run build
```

## 🧭 Coding Guidelines

- Keep changes focused and minimal.
- Preserve existing architecture boundaries (`core`, `services`, API, frontend state).
- Add concise comments only where flow is non-obvious.
- Avoid introducing plaintext secret handling.
- Ensure new endpoints enforce auth/ownership if user-scoped.

## 📚 Documentation Expectations

If behavior changes, update relevant docs:

- `README.md`
- `SETUP_GUIDE.md`
- `frontend/README.md`
- `SECURITY.md` (if security posture changes)
- `CREDENTIALS_RECOVERY.md` when Google Forms credentials behavior changes
- Keep `README.md`, `SETUP_GUIDE.md`, and `frontend/README.md` aligned when the document-upload flow or supported file types change

## 🐛 Reporting Bugs

Please include:

- Reproduction steps
- Expected vs actual behavior
- Logs/errors
- Environment details (OS, Python/Node versions)

## 🔐 Security-sensitive Contributions

For auth, tokens, credentials, rate limits, or data ownership changes:

- Add/adjust smoke tests
- Explain threat model assumptions in PR description
- Prefer deny-by-default behavior

## 📝 Pull Request Checklist

- [ ] Code builds and tests pass
- [ ] Docs updated if needed
- [ ] No secrets or generated runtime files committed
- [ ] Scope is clear and reviewable
