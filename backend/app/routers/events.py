#
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import json
import time

from app.validate2 import ValidateData
from app.security import get_current_user, AuthenticatedUser
from app.services.event_service import (
    EVENTS,
    connected_clients,
    get_alarm_system_id_for_user,
    get_alarm_system_id_for_device,
    is_duplicate,
    is_sequence_valid,
)
from db.events import save_event, get_events_for_system
from db.device_last_seen import update_last_seen
from app.services.notification_service import send_push_for_event

router = APIRouter()


def is_microcontroller_registered_to_user(device_id: str, user_id: int) -> bool:
    user_system_id = get_alarm_system_id_for_user(user_id)
    device_system_id = get_alarm_system_id_for_device(device_id)
    return user_system_id is not None and user_system_id == device_system_id


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
def receive_event(
    event: ValidateData,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    if not is_microcontroller_registered_to_user(event.device_id, current_user.user_id):
        raise HTTPException(status_code=403, detail="Device not registered to this user")

    if is_duplicate(event.device_id, event.count):
        raise HTTPException(status_code=409, detail="Duplicate event")

    if not is_sequence_valid(event.device_id, event.count):
        raise HTTPException(status_code=400, detail="Invalid event sequence")

    alarm_system_id = get_alarm_system_id_for_device(event.device_id)

    event_dict = event.model_dump()
    event_dict["timestamp"] = time.time()
    was_armed = _is_system_armed(alarm_system_id)
    EVENTS.append((event_dict, alarm_system_id, was_armed))

    try:
        save_event(event_dict, alarm_system_id, was_armed)
    except Exception as e:
        print(f"Event persist error: {e}")

    if alarm_system_id is not None:
        try:
            update_last_seen(event.device_id, event_dict["timestamp"])
        except Exception:
            pass
    # Debug: print current_power_usage events being received
    if event.event_type == "current_power_usage":
        
        print(f"Power Event #{event.count} received. Usage: {event.value}mA")

    for queue, client_system_id in connected_clients:
        if client_system_id == alarm_system_id:
            queue.put_nowait(event_dict)

    if _is_system_armed(alarm_system_id):
        send_push_for_event(event_dict, alarm_system_id)

    return {"status": "ok", "message": "Event received"}


@router.get("/events")
def get_events(current_user: AuthenticatedUser = Depends(get_current_user)):
    alarm_system_id = get_alarm_system_id_for_user(current_user.user_id)

    if alarm_system_id is None:
        return []

    events = get_events_for_system(alarm_system_id, armed_only=True)
    return events


@router.get("/events/stream")
async def stream_events(current_user: AuthenticatedUser = Depends(get_current_user)):
    alarm_system_id = get_alarm_system_id_for_user(current_user.user_id)

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
