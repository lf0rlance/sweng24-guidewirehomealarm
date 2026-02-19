from typing import Dict, Set, Optional, List, Any
from pathlib import Path
from datetime import datetime

from app.config import settings

# In-memory cache; also persisted in DB (see db.fcm_tokens) so tokens survive restart
fcm_tokens_by_system: Dict[int, Set[str]] = {}
_firebase_initialized = False


def register_fcm_token(alarm_system_id: int, token: str):
    # Remove token from any other system (one device = one system)
    for sid, tokens in list(fcm_tokens_by_system.items()):
        tokens.discard(token)
    fcm_tokens_by_system.setdefault(alarm_system_id, set()).add(token)
    # Persist so tokens survive backend restart
    try:
        from db.fcm_tokens import save_fcm_token
        if save_fcm_token(alarm_system_id, token):
            print(f"FCM token saved for alarm_system_id={alarm_system_id} (preview ...{token[-8:]})")
    except Exception as e:
        print(f"FCM token persist failed: {e}")


def _get_tokens_for_system(alarm_system_id: int) -> List[str]:
    """Get tokens from memory, or load from DB if empty (e.g. after restart)."""
    in_mem = list(fcm_tokens_by_system.get(alarm_system_id) or [])
    if in_mem:
        return in_mem
    try:
        from db.fcm_tokens import get_fcm_tokens
        tokens = get_fcm_tokens(alarm_system_id)
        if tokens:
            fcm_tokens_by_system.setdefault(alarm_system_id, set()).update(tokens)
            print(f"FCM loaded {len(tokens)} token(s) from DB for alarm_system_id={alarm_system_id}")
        return tokens
    except Exception:
        return []


def init_firebase_if_needed() -> bool:
    global _firebase_initialized

    if _firebase_initialized:
        return True

    if not settings.firebase_credentials_path or not str(settings.firebase_credentials_path).strip():
        print("Push notifications disabled: FIREBASE_CREDENTIALS_PATH not set in .env")
        return False

    path = Path(settings.firebase_credentials_path)
    if not path.exists():
        print(f"Push notifications disabled: FIREBASE_CREDENTIALS_PATH file not found: {path}")
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials
        cred = credentials.Certificate(str(path))
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        print("Firebase Admin initialized for FCM push")
        return True
    except Exception as e:
        print(f"Firebase init failed: {e}")
    return False


# Event types we send push for (ESP32 may send "led_toggle" for reed; backend also supports door_open/door_closed)
_PUSH_EVENT_TYPES = ("door_open", "door_closed", "led_toggle")


def _format_event_time(timestamp: float) -> str:
    """Format Unix timestamp as e.g. 'Feb 18, 14:32'."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%b %d, %H:%M")
    except Exception:
        return ""


def send_push_for_event(event_dict: Dict[str, Any], alarm_system_id: Optional[int]):
    """event_dict must have event_type, device_id, timestamp (Unix float)."""
    event_type = event_dict.get("event_type")
    if event_type not in _PUSH_EVENT_TYPES:
        return

    if alarm_system_id is None:
        print(f"Push skipped: event {event_type} from {event_dict.get('device_id')} has no alarm_system_id (link ESP32 in app Settings)")
        return

    tokens = _get_tokens_for_system(alarm_system_id)
    if not tokens:
        print(f"Push skipped: no FCM tokens for alarm_system_id={alarm_system_id} (open app while logged in to register)")
        return

    if not init_firebase_if_needed():
        print("Push skipped: Firebase not initialized (set FIREBASE_CREDENTIALS_PATH in backend .env)")
        return

    try:
        from firebase_admin import messaging

        if event_type == "door_open":
            title = "Door opened"
        elif event_type == "door_closed":
            title = "Door closed"
        else:
            title = "Sensor event"  # led_toggle or other
        ts = event_dict.get("timestamp")
        time_str = _format_event_time(ts) if isinstance(ts, (int, float)) else ""
        body = time_str or event_dict.get("device_id", "")
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={"event_type": str(event_type), "device_id": event_dict.get("device_id", "")},
            tokens=tokens,
        )
        batch = messaging.send_each_for_multicast(message)
        print(f"Push sent: {event_type} to {batch.success_count}/{len(tokens)} devices (failures: {batch.failure_count})")
        if batch.failure_count > 0:
            for i, err in enumerate(batch.responses):
                if not err.success:
                    print(f"  FCM failure[{i}]: {err.exception}")
    except Exception as e:
        print(f"FCM send failed: {e}")