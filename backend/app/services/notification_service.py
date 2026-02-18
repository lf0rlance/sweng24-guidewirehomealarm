from typing import Dict, Set, Optional
from pathlib import Path

from app.config import settings

fcm_tokens_by_system: Dict[int, Set[str]] = {}
_firebase_initialized = False


def register_fcm_token(alarm_system_id: int, token: str):
    for sid, tokens in list(fcm_tokens_by_system.items()):
        tokens.discard(token)

    fcm_tokens_by_system.setdefault(alarm_system_id, set()).add(token)


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


def send_push_for_event(event, alarm_system_id: Optional[int]):
    if event.event_type not in ("door_open", "door_closed"):
        return

    if alarm_system_id is None:
        return

    tokens = list(fcm_tokens_by_system.get(alarm_system_id) or [])
    if not tokens:
        return

    if not init_firebase_if_needed():
        return

    try:
        from firebase_admin import messaging

        title = "Door opened" if event.event_type == "door_open" else "Door closed"

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=event.device_id
            ),
            data={
                "event_type": event.event_type,
                "device_id": event.device_id,
            },
            tokens=tokens,
        )

        messaging.send_each_for_multicast(message)

    except Exception as e:
        print(f"FCM send failed: {e}")