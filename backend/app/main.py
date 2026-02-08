from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from app.validate2 import ValidateData
from app.config import settings
from typing import List
import asyncio
import json
import socket


#########
#imports for db connection
from fastapi import HTTPException
from app.db.connectToAlarmSystem import connectUserToSystem
from app.db.connectMCtoAlarmSystem import connectMicroController
from app.db.connectToAlarmSystem import getCurrentAlarmSystemID
from app.db.insertIntoDB import insertUserInDB


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    local_ip = get_local_ip()
    port = settings.port

    effective_url = settings.backend_url or f"http://{local_ip}:{port}"

    print("================================================")
    print("🚀 Home Alarm Backend started")
    print(f"🌐 Network URL: {effective_url}")
    print(f"🔁 Loopback:    http://127.0.0.1:{port}")
    print("================================================")

    yield

    # ---- shutdown ----
    print("🛑 Home Alarm Backend shutting down")


app = FastAPI(
    title="Home Alarm Backend",
    lifespan=lifespan
)


# Use config for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Temporary storage
EVENTS: List[ValidateData] = []

connected_clients: List[asyncio.Queue] = []


@app.post("/api/events")
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

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "backend",
        "backend_url": settings.backend_url
    }

@app.get("/config")
def get_config():
    return {
        "backend_url": settings.backend_url,
        "stream_endpoint": f"{settings.backend_url}/events/stream"
    }

############################################################################
#Integrating db methods

@app.post("/api/pair")
def pair_user(username: str, system_password: str):
    success = connectUserToSystem(
        username=username,
        system_password=system_password
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Pairing failed (invalid password or already paired)"
        )

    return {
        "status": "ok",
        "message": "User paired with alarm system"
    }

@app.post("/api/microcontroller/connect")
def connect_microcontroller(username: str, microcontroller_id: int):
    system_id = getCurrentAlarmSystemID(username)

    if system_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not paired with an alarm system"
        )

    success = connectMicroController(
        microControllerId=microcontroller_id,
        alarmSystemId=system_id
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Microcontroller connection failed"
        )

    return {
        "status": "ok",
        "message": "Microcontroller connected",
        "alarm_system_id": system_id
    }

@app.post("/api/createUser")
def create_user(username: str, email: str, password: str, alarm_system_id: int | None = None):
    insertion = insertUserInDB(username, email, alarm_system_id ,password)

    if not insertion:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    return {
        "status": "ok",
        "message": "User created"
    }