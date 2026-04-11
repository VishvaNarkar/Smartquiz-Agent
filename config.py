import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ollama Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Google API Scopes
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive"
]

# App Configuration
APP_TITLE = "SmartQuiz Agent"
DEFAULT_NUM_QUESTIONS = 5
MAX_NUM_QUESTIONS = 20

# Data Paths
QUIZZES_DATA_PATH = "data/quizzes.json"
TOKEN_PATH = "auth/token.json"
CREDENTIALS_PATH = "auth/credentials.json"