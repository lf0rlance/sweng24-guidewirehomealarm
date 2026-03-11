#
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json

from app.validate2 import ValidateData
from app.services.event_service import EVENTS, connected_clients
from app.security import AuthenticatedUser, get_current_user

router = APIRouter()


@router.post("/api/events")
def receive_event(event: ValidateData, _user: AuthenticatedUser = Depends(get_current_user)):
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
