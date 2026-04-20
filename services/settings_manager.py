import json
import os
from typing import Dict, Optional

SETTINGS_FILE = "data/ai_settings.json"
API_KEY_ENV_VAR = "SMARTQUIZ_CLOUD_API_KEY"


class SettingsManager:
    """Manage persistent AI settings storage.

    Security design:
    - Non-secret settings are persisted in JSON.
    - Cloud API keys are never written to disk; they are sourced from env/runtime memory.
    """

    _runtime_api_key: str = ""

    @staticmethod
    def _ensure_settings_dir():
        """Ensure the data directory exists."""
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

    @staticmethod
    def save_ai_settings(ai_source: str, ai_model: str, ai_api_url: str, ai_api_key: str) -> bool:
        """Save AI settings to persistent storage."""
        try:
            SettingsManager._ensure_settings_dir()
            # Security: never persist cloud API keys to disk.
            SettingsManager._runtime_api_key = (ai_api_key or "").strip()
            settings = {
                "ai_source": ai_source,
                "ai_model": ai_model,
                "ai_api_url": ai_api_url,
                "ai_api_key": "",
            }
            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save AI settings: {e}")
            return False

    @staticmethod
    def load_ai_settings() -> Optional[Dict]:
        """Load AI settings from persistent storage."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r") as f:
                    settings = json.load(f)

                # Migrate away from any legacy plaintext key on disk.
                migrated = False
                if settings.get("ai_api_key"):
                    settings["ai_api_key"] = ""
                    migrated = True

                env_key = os.getenv(API_KEY_ENV_VAR, "").strip()
                effective_key = env_key or SettingsManager._runtime_api_key
                settings["ai_api_key"] = effective_key

                if migrated:
                    with open(SETTINGS_FILE, "w") as f:
                        json.dump({**settings, "ai_api_key": ""}, f, indent=2)

                return settings
        except Exception as e:
            print(f"Failed to load AI settings: {e}")
        return None

    @staticmethod
    def get_ai_settings_with_defaults(defaults: Dict) -> Dict:
        """Get AI settings, falling back to defaults if not found."""
        saved = SettingsManager.load_ai_settings()
        if saved:
            return saved
        return defaults
