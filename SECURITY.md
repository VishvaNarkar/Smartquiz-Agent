# 🛡️ Security Policy

## 📌 Supported Security Posture

SmartQuiz Agent is an actively evolving project.
Security fixes are prioritized for the latest main branch state.

## 🚨 Reporting a Vulnerability

Please do **not** open a public issue for sensitive vulnerabilities.

Use one of these disclosure channels:

1. Preferred: GitHub private vulnerability reporting (Security Advisory).
2. If private advisories are unavailable, open an issue with minimal details and request a private contact path.

## 🧭 What to include in a report

- Affected component/file
- Impact and attack scenario
- Reproduction steps or proof of concept
- Suggested mitigation (if available)

## ⏱️ Disclosure Process

- We acknowledge receipt as soon as possible.
- We investigate and validate impact.
- We patch and document mitigation.
- We coordinate disclosure timing with reporter when feasible.

## 🔐 Sensitive Data Handling Expectations

- Do not commit credentials (`auth/credentials.json`, tokens, env secrets).
- Use environment variables for cloud API keys and auth secrets.
- Keep local runtime data (`data/*.json`) outside public commits.

## ✅ Security Controls in Project

- Bearer-token protected endpoints
- Ownership checks on user-scoped resources
- Strict username validation + compatibility migration
- Auth endpoint rate limiting
- Credentials upload validation (type/size/schema)
- Cloud API URL allowlist

## 📣 Scope Notes

Out-of-scope examples (unless chained to real impact):

- Purely local-only dev misconfiguration without exploit path
- Non-sensitive console warnings
- Missing headers in local non-production setups
