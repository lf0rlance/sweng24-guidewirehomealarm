from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import json
import jwt

from app.validate2 import ValidateData
from app.config import settings
from app.services.event_service import (
    EVENTS,
    connected_clients,
    get_alarm_system_id_for_user,
    get_alarm_system_id_for_device,
)
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


@router.post("/api/events")
def receive_event(event: ValidateData):
    alarm_system_id = get_alarm_system_id_for_device(event.device_id)

    event_dict = event.model_dump()
    EVENTS.append((event_dict, alarm_system_id))

    # Push only to matching system streams
    for queue, client_system_id in connected_clients:
        if client_system_id == alarm_system_id:
            queue.put_nowait(event_dict)

    send_push_for_event(event, alarm_system_id)

    return {"status": "ok", "message": "Event received"}


@router.get("/events")
def get_events(user_id: int = Depends(get_current_user_id)):
    alarm_system_id = get_alarm_system_id_for_user(user_id)

    if alarm_system_id is None:
        return []

    return [
        event_dict
        for event_dict, sid in EVENTS
        if sid == alarm_system_id
    ]


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