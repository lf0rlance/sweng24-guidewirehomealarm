from typing import Dict, Set, Optional, List, Any
from pathlib import Path
from datetime import datetime

from app.config import settings

# In-memory cache; also persisted in DB (see db.fcm_tokens) so tokens survive restart
fcm_tokens_by_system: Dict[int, Set[str]] = {}
_firebase_initialized = False


def register_fcm_token(alarm_system_id: int, token: str, user_id: Optional[int] = None):
    # Remove token from any other system (one device = one system)
    for sid, tokens in list(fcm_tokens_by_system.items()):
        tokens.discard(token)
    fcm_tokens_by_system.setdefault(alarm_system_id, set()).add(token)
    # Persist so tokens survive backend restart
    try:
        from db.fcm_tokens import save_fcm_token

        if save_fcm_token(alarm_system_id, token, user_id):
            print(
                f"FCM token saved for alarm_system_id={alarm_system_id} user_id={user_id} (preview ...{token[-8:]})"
            )
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
_PUSH_EVENT_TYPES = ("door_open", "door_closed", "door_open_2", "door_closed_2", "led_toggle")


def _format_event_time(timestamp: float) -> str:
    """Format Unix timestamp as e.g. 'Feb 18, 14:32'."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%b %d, %H:%M")
    except Exception:
        return ""


def _title_for_sensor_event(event_type: str, alarm_system_id: int) -> str:
    """Notification title aligned with admin-configured names (see db.sensor_labels)."""
    try:
        from db.sensor_labels import get_sensor_labels

        labels = get_sensor_labels(alarm_system_id)
    except Exception:
        labels = []
    n1 = (labels[0] if len(labels) > 0 else "").strip() or None
    n2 = (labels[1] if len(labels) > 1 else "").strip() or None

    if event_type == "door_open":
        return f"{n1} opened" if n1 else "Door opened"
    if event_type == "door_closed":
        return f"{n1} closed" if n1 else "Door closed"
    if event_type == "door_open_2":
        return f"{n2} opened" if n2 else "Sensor 2 opened"
    if event_type == "door_closed_2":
        return f"{n2} closed" if n2 else "Sensor 2 closed"
    return "Sensor event"


def send_push_for_event(event_dict: Dict[str, Any], alarm_system_id: Optional[int]):
    """event_dict must have event_type, device_id, timestamp (Unix float)."""
    event_type = event_dict.get("event_type")
    if event_type not in _PUSH_EVENT_TYPES:
        return

    if alarm_system_id is None:
        print(f"Push skipped: event {event_type} from {event_dict.get('device_id')} has no alarm_system_id (link ESP32 in app Settings)")
        return

    try:
        from db.fcm_tokens import get_fcm_tokens_excluding_trusted

        tokens = get_fcm_tokens_excluding_trusted(alarm_system_id)
    except Exception:
        tokens = _get_tokens_for_system(alarm_system_id)
    if not tokens:
        print(f"Push skipped: no FCM tokens for alarm_system_id={alarm_system_id} (open app while logged in to register)")
        return

    if not init_firebase_if_needed():
        print("Push skipped: Firebase not initialized (set FIREBASE_CREDENTIALS_PATH in backend .env)")
        return

    try:
        from firebase_admin import messaging

        if event_type in ("door_open", "door_closed", "door_open_2", "door_closed_2"):
            title = _title_for_sensor_event(event_type, alarm_system_id)
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
        print(f"Push sent: {event_type} to {batch.success_count}/{len(tokens)} devices (excludes trusted; failures: {batch.failure_count})")
        if batch.failure_count > 0:
            for i, err in enumerate(batch.responses):
                if not err.success:
                    print(f"  FCM failure[{i}]: {err.exception}")
    except Exception as e:
        print(f"FCM send failed: {e}")


def send_push_to_tokens(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
) -> int:
    """Send FCM to an explicit token list. Returns success count."""
    if not tokens:
        return 0
    if not init_firebase_if_needed():
        return 0
    try:
        from firebase_admin import messaging

        android_config = messaging.AndroidConfig(
            notification=messaging.AndroidNotification(channel_id="sensor_events"),
            priority="high",
        )
        payload_data = {k: str(v) for k, v in (data or {}).items()}
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=payload_data,
            tokens=tokens,
            android=android_config,
        )
        batch = messaging.send_each_for_multicast(message)
        return batch.success_count
    except Exception as e:
        print(f"send_push_to_tokens failed: {e}")
        return 0


def notify_guardians_child_or_trusted_arm_action(
    alarm_system_id: int,
    actor_user_id: int,
    armed: bool,
) -> None:
    """Notify owner + spouse when child/trusted arms or disarms (immediate disarm path for child only)."""
    try:
        from db.fcm_tokens import get_fcm_tokens_for_users
        from db.home_roles import get_username, user_ids_guardians

        guardians = [u for u in user_ids_guardians(alarm_system_id) if u != actor_user_id]
        if not guardians:
            return
        name = get_username(actor_user_id)
        action = "armed" if armed else "disarmed"
        title = f"Alarm {action}"
        body = f"{name} {action} the alarm"
        tokens = get_fcm_tokens_for_users(alarm_system_id, guardians)
        if not tokens:
            return
        send_push_to_tokens(tokens, title, body)
    except Exception as e:
        print(f"notify_guardians_arm_action failed: {e}")


def notify_owners_disarm_approval_needed(
    alarm_system_id: int,
    request_id: str,
    actor_user_id: int,
) -> None:
    """Trusted disarm: only owner(s) get a request to approve."""
    try:
        from db.fcm_tokens import get_fcm_tokens_for_users
        from db.home_roles import get_username, user_ids_owners_only

        owners = user_ids_owners_only(alarm_system_id)
        if not owners:
            return
        name = get_username(actor_user_id)
        title = "Approve disarm?"
        body = f"{name} asked to disarm the alarm. Open the app to approve or deny."
        tokens = get_fcm_tokens_for_users(alarm_system_id, owners)
        if not tokens:
            return
        send_push_to_tokens(
            tokens,
            title,
            body,
            data={"type": "disarm_request", "request_id": request_id},
        )
    except Exception as e:
        print(f"notify_owners_disarm_approval failed: {e}")


def send_notification_to_system(alarm_system_id: int, title: str, body: str) -> int:
    """
    Send a one-off notification to all devices registered for this home (e.g. admin notifying homeowner).
    Returns number of devices successfully sent to.
    """
    tokens = _get_tokens_for_system(alarm_system_id)
    if not tokens:
        return 0
    if not init_firebase_if_needed():
        return 0
    try:
        from firebase_admin import messaging
        android_config = messaging.AndroidConfig(
            notification=messaging.AndroidNotification(channel_id="sensor_events"),
            priority="high",
        )
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=tokens,
            android=android_config,
        )
        batch = messaging.send_each_for_multicast(message)
        return batch.success_count
    except Exception as e:
        print(f"send_notification_to_system failed: {e}")
        return 0