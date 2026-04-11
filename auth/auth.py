import os
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from config import GOOGLE_SCOPES, TOKEN_PATH, CREDENTIALS_PATH

logger = logging.getLogger(__name__)

def get_credentials():
    """
    Get Google API credentials, refreshing if necessary.

    Returns:
        Credentials: Valid Google OAuth credentials.
    """
    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, GOOGLE_SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load token: {e}")

    # Refresh or re-authenticate if invalid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Credentials refreshed")
            except Exception as e:
                logger.warning(f"Failed to refresh credentials: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"Credentials file not found: {CREDENTIALS_PATH}. Please set up Google OAuth.")

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
            logger.info("New credentials obtained")

            # Save token securely
            with open(TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())

    return creds