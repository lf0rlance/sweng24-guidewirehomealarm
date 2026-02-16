from pathlib import Path
from typing import List
from app.config import settings

fcm_tokens: List[str] = []
_firebase_initialized = False


def init_firebase_if_needed():
    global _firebase_initialized

    if _firebase_initialized:
        return True

    if not settings.firebase_credentials_path:
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials

        path = Path(settings.firebase_credentials_path)

        if path.exists():
            cred = credentials.Certificate(str(path))
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)

            _firebase_initialized = True
            return True

    except Exception as e:
        print(f"Firebase init failed: {e}")

    return False
