#
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import json

from app.validate2 import ValidateData
from app.services.event_service import EVENTS, connected_clients, is_duplicate
from app.security import AuthenticatedUser, get_current_user
from db.getMicrocontrollerBySystem import is_microcontroller_registered_to_user

router = APIRouter()


@router.post("/api/events")
def receive_event(event: ValidateData, current_user: AuthenticatedUser = Depends(get_current_user)):
    # Extract numeric ID from device_id (e.g. "esp32_123" → 123)
    microcontroller_id = int(event.device_id.split("_")[1])

    if not is_microcontroller_registered_to_user(microcontroller_id, current_user.user_id):
        raise HTTPException(status_code=403, detail="Device not registered to your alarm system")

    if is_duplicate(event.device_id, event.count):
        raise HTTPException(status_code=409, detail="Duplicate event rejected")

    EVENTS.append(event)

    for queue in connected_clients:
        queue.put_nowait(event.model_dump())

    return {"status": "ok"}


@router.get("/events")
def get_events(_user: AuthenticatedUser = Depends(get_current_user)):
    return EVENTS


@router.get("/events/stream")
async def stream_events(_user: AuthenticatedUser = Depends(get_current_user)):
    queue: asyncio.Queue = asyncio.Queue()
    connected_clients.append(queue)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            connected_clients.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
