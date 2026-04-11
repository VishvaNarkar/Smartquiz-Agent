# 🔐 Credentials Recovery Guide

Unfortunately, the `credentials.json` and `token.json` files were permanently deleted during the GitHub cleanup process. These files cannot be recovered from disk, but you can regenerate them easily.

## 📋 Recovering credentials.json

### Step 1: Go to Google Cloud Console
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one if needed)

### Step 2: Create OAuth 2.0 Credentials
1. Navigate to **Credentials** (left sidebar)
2. Click **+ Create Credentials** → **OAuth client ID**
3. Application type: **Desktop application**
4. Click **Create**
5. Download the JSON file

### Step 3: Place the File
1. Rename the downloaded file to `credentials.json`
2. Move it to `auth/credentials.json` in your project directory

```bash
# Example on Windows:
Move-Item "Downloads\client_secrets_*.json" "auth\credentials.json"

# On macOS/Linux:
mv ~/Downloads/client_secrets_*.json auth/credentials.json
```

## 🔄 Recovering token.json

The `token.json` file is **automatically generated** on first use. You don't need to create it manually.

### How to Generate It:
1. Run the SmartQuiz application:
   ```bash
   streamlit run ui/streamlit_app.py
   ```
2. Try to create and export a Google Form
3. A browser window will open asking for Google authentication
4. Authorize the app
5. The `token.json` file will be automatically created in `auth/`

The file structure should look like:
```
auth/
├── auth.py
├── __init__.py
├── credentials.json    ← Downloaded from Google Cloud Console
└── token.json          ← Auto-generated after first OAuth flow
```

## ⚠️ Important Security Notes

- **Never commit these files to GitHub** (they're protected by `.gitignore`)
- Keep `credentials.json` and `token.json` private and secure
- If credentials are compromised, regenerate them in Google Cloud Console
- Use environment variables in production instead of local files

## ✅ Verification

After recovering both files, verify the setup:

```bash
# Check files exist
ls -la auth/
# Should show:
# total XX
# -rw-r--r--  1 user  group  XXX Nov XX XX:XX auth.py
# -rw-r--r--  1 user  group  XXX Nov XX XX:XX __init__.py
# -rw-r--r--  1 user  group  XXX Nov XX XX:XX credentials.json
# -rw-r--r--  1 user  group  XXX Nov XX XX:XX token.json
```

## 🚀 Next Steps

Once files are recovered, you can:
1. Test the application locally
2. Deploy to Docker/cloud
3. Use the adaptive quiz and Google Forms export features

For more help, check the [README.md](../README.md) troubleshooting section.
