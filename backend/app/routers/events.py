from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import json
import jwt
import time

from app.validate2 import ValidateData
from app.config import settings
from app.services.event_service import (
    EVENTS,
    connected_clients,
    get_alarm_system_id_for_user,
    get_alarm_system_id_for_device,
)
from db.events import save_event, get_events_for_system
from app.services.notification_service import send_push_for_event

router = APIRouter()
security = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> int:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authorization")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        user_id = payload.get("userId")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _is_system_armed(alarm_system_id) -> bool:
    """True if this alarm system is armed (push/alert only when armed)."""
    if alarm_system_id is None:
        return False
    try:
        from db.getModeOfSystem import getModeBySysId
        return bool(getModeBySysId(alarm_system_id))
    except Exception:
        return False


@router.post("/api/events")
def receive_event(event: ValidateData):
    alarm_system_id = get_alarm_system_id_for_device(event.device_id)

    event_dict = event.model_dump()
    # Use server time so list and notifications show correct date/time (ESP32 may not have NTP)
    event_dict["timestamp"] = time.time()
    was_armed = _is_system_armed(alarm_system_id)
    EVENTS.append((event_dict, alarm_system_id, was_armed))

    # Persist to DB so history survives backend restarts
    try:
        save_event(event_dict, alarm_system_id, was_armed)
    except Exception as e:
        print(f"Event persist error: {e}")

    # Push only to matching system streams (app can show history either way)
    for queue, client_system_id in connected_clients:
        if client_system_id == alarm_system_id:
            queue.put_nowait(event_dict)

    # Only send push notifications when the system is armed
    if _is_system_armed(alarm_system_id):
        send_push_for_event(event_dict, alarm_system_id)

    return {"status": "ok", "message": "Event received"}


@router.get("/events")
def get_events(user_id: int = Depends(get_current_user_id)):
    alarm_system_id = get_alarm_system_id_for_user(user_id)

    if alarm_system_id is None:
        return []

    # Load from DB so history includes past events, not just this-process memory.
    events = get_events_for_system(alarm_system_id, armed_only=True)
    # Keep newest-first ordering for the client; it may reverse again in UI if desired.
    return events


@router.get("/events/stream")
async def stream_events(user_id: int = Depends(get_current_user_id)):
    alarm_system_id = get_alarm_system_id_for_user(user_id)

    queue: asyncio.Queue = asyncio.Queue()
    entry = (queue, alarm_system_id)
    connected_clients.append(entry)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            if entry in connected_clients:
                connected_clients.remove(entry)

    return StreamingResponse(event_generator(), media_type="text/event-stream")