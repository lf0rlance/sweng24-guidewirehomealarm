from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from validate2 import ValidateData
from typing import List
import asyncio
import json

app = FastAPI(title="Home Alarm Backend")

# Add CORS to connect to frontend on diff port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary storage
EVENTS: List[ValidateData] = []

connected_clients: List[asyncio.Queue] = []


@app.post("/events")
def receive_event(event: ValidateData):
    EVENTS.append(event)

    # Push the new event into every connected client's queue
    for queue in connected_clients:
        queue.put_nowait(event.model_dump())

    return {
        "status": "ok",
        "message": "Event received"
    }


@app.get("/events")
def get_events():
    return EVENTS


@app.get("/events/stream")
async def stream_events():
    # Each client that connects gets its own queue
    queue: asyncio.Queue = asyncio.Queue()
    connected_clients.append(queue)

    async def event_generator():
        try:
            while True:
                # Wait for the next event to appear in this client's queue
                event = await queue.get()
                # SSE format: "data: <json>\n\n"
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            # Client disconnected — clean up their queue
            connected_clients.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")