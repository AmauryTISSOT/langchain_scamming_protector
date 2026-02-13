import json
import os
import tempfile
from dotenv import load_dotenv


def load_config():
    """Load environment variables and setup Google TTS credentials.
    Returns the GROQ_API_KEY."""
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY manquante dans le fichier .env")

    google_credentials = os.getenv("GOOGLE_CREDENTIALS")
    if google_credentials and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            creds_dict = json.loads(google_credentials)
            creds_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            )
            json.dump(creds_dict, creds_file)
            creds_file.close()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_file.name
        except Exception:
            pass

    return api_key
