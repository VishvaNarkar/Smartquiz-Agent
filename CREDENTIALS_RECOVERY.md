# 🔐 Google Credentials Recovery Guide

Use this guide if `auth/credentials.json` is missing or invalid.

## 🎯 What this file is for

`credentials.json` contains Google OAuth client configuration used for Google Forms export.

## 1️⃣ Regenerate in Google Cloud Console

1. Open Google Cloud Console.
2. Select your project.
3. Enable APIs:
   - Google Forms API
   - Google Drive API
4. Go to **Credentials**.
5. Create OAuth Client ID.
6. Choose **Desktop app**.
7. Download JSON file.

## 2️⃣ Upload in SmartQuiz

1. Login to SmartQuiz.
2. Open **Settings**.
3. Use **Google Forms Credentials** upload on the dashboard settings page.
4. Select the downloaded `.json` file.

The authenticated upload endpoint is `POST /credentials/upload`, and it writes the validated file to `auth/credentials.json`.

## ✅ Server-side validation checks

Upload endpoint validates:

- File extension is `.json`
- MIME/content type is JSON compatible when provided
- File size <= 1MB
- JSON includes `installed` or `web`
- Required fields exist:
  - `client_id`
  - `client_secret`
  - `auth_uri`
  - `token_uri`

## 3️⃣ token.json behavior

`auth/token.json` is generated automatically after successful OAuth flow during first Google export action.

## 🛡️ Security reminders

- Never commit credentials files to Git.
- Rotate credentials immediately if exposed.
- Keep OAuth client restricted to expected usage.

## 🧪 Quick verification

After upload, try exporting a quiz to Google Forms.
If export succeeds, credentials are valid.
