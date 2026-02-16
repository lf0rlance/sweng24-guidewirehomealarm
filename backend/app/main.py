from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List
from pathlib import Path
import asyncio
import json
import socket
import sys
import jwt

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.validate2 import ValidateData
from app.config import settings

# -----------------------------
# DB IMPORT SETUP
# -----------------------------

backend_dir = Path(__file__).resolve().parent.parent
db_dir = backend_dir / "db"

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(db_dir))

from db.connectToAlarmSystem import connectUserToSystem, getCurrentAlarmSystemID
from db.connectMCtoAlarmSystem import connectMicroController
from db.insertIntoDB import insertUserInDB
from db.googleAuth import find_or_create_google_user, find_google_user_only


# -----------------------------
# Utility
# -----------------------------

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# -----------------------------
# Lifespan
# -----------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    local_ip = get_local_ip()
    port = settings.port
    effective_url = settings.backend_url or f"http://{local_ip}:{port}"

    print("================================================")
    print("Home Alarm Backend started")
    print(f"Network URL: {effective_url}")
    print(f"Loopback:    http://127.0.0.1:{port}")
    print("================================================")

    yield

    print("Home Alarm Backend shutting down")


app = FastAPI(
    title="Home Alarm Backend",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Basic Endpoints
# -----------------------------

@app.get("/ping")
def ping():
    return {"pong": True}


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


# -----------------------------
# Event Streaming + Notifications
# -----------------------------

EVENTS: List[ValidateData] = []
connected_clients: List[asyncio.Queue] = []
fcm_tokens: List[str] = []
_firebase_initialized = False


def _init_firebase_if_needed():
    global _firebase_initialized

    if _firebase_initialized:
        return True

    if not settings.firebase_credentials_path:
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials

        path = Path(settings.firebase_credentials_path)
        if not path.is_absolute():
            path = backend_dir / path

        if path.exists():
            cred = credentials.Certificate(str(path))
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)

            _firebase_initialized = True
            return True

    except Exception as e:
        print(f"Firebase init failed: {e}")

    return False


def _send_push_for_event(event: ValidateData):
    if event.event_type not in ("door_open", "door_closed"):
        return

    if not fcm_tokens:
        return

    if not _init_firebase_if_needed():
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
                "device_id": event.device_id
            },
            tokens=fcm_tokens,
        )

        messaging.send_each_for_multicast(message)

    except Exception as e:
        print(f"FCM send failed: {e}")


class RegisterTokenRequest(BaseModel):
    token: str


@app.post("/api/notifications/register")
def register_fcm_token(req: RegisterTokenRequest):
    if not req.token:
        raise HTTPException(status_code=400, detail="Missing token")

    token = req.token.strip()

    if token not in fcm_tokens:
        fcm_tokens.append(token)

    return {"status": "ok"}


@app.post("/api/events")
def receive_event(event: ValidateData):
    EVENTS.append(event)

    for queue in connected_clients:
        queue.put_nowait(event.model_dump())

    _send_push_for_event(event)

    return {"status": "ok"}


@app.get("/events")
def get_events():
    return EVENTS


@app.get("/events/stream")
async def stream_events():
    queue: asyncio.Queue = asyncio.Queue()
    connected_clients.append(queue)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            connected_clients.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# -----------------------------
# Database Integration
# -----------------------------

@app.post("/api/pair")
def pair_user(username: str, system_password: str):
    if not connectUserToSystem(username=username, system_password=system_password):
        raise HTTPException(status_code=400, detail="Pairing failed")

    return {"status": "ok"}


@app.post("/api/microcontroller/connect")
def connect_microcontroller(username: str, microcontroller_id: int):
    system_id = getCurrentAlarmSystemID(username)

    if system_id is None:
        raise HTTPException(status_code=400, detail="User not paired")

    if not connectMicroController(
        microControllerId=microcontroller_id,
        username=username
    ):
        raise HTTPException(status_code=400, detail="Connection failed")

    return {
        "status": "ok",
        "alarm_system_id": system_id
    }


@app.post("/api/createUser")
def create_user(username: str, email: str, password: str, alarm_system_id: int | None = None):
    if not insertUserInDB(username, email, alarm_system_id, password):
        raise HTTPException(status_code=400, detail="User already exists")

    return {"status": "ok"}


# -----------------------------
# Google OAuth
# -----------------------------

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


class GoogleAuthRequest(BaseModel):
    idToken: str


def _verify_google_token(id_token_str: str):
    idinfo = id_token.verify_oauth2_token(
        id_token_str,
        google_requests.Request(),
        settings.google_client_id
    )

    if idinfo["aud"] != settings.google_client_id:
        raise ValueError("Invalid audience")

    return idinfo


def _user_response(user: dict):
    token = jwt.encode(
        {"userId": user["id"], "email": user["email"]},
        settings.jwt_secret,
        algorithm="HS256"
    )

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    }


@auth_router.post("/signup")
def signup(request: GoogleAuthRequest):
    idinfo = _verify_google_token(request.idToken)

    google_id = idinfo.get("sub")
    email = idinfo.get("email")
    name = idinfo.get("name", email.split("@")[0])

    if find_google_user_only(google_id, email, name):
        raise HTTPException(status_code=409, detail="Account already exists")

    user = find_or_create_google_user(google_id, email, name)

    if not user:
        raise HTTPException(status_code=500, detail="User creation failed")

    return _user_response(user)


@auth_router.post("/signin")
def signin(request: GoogleAuthRequest):
    idinfo = _verify_google_token(request.idToken)

    google_id = idinfo.get("sub")
    email = idinfo.get("email")
    name = idinfo.get("name", email.split("@")[0])

    user = find_google_user_only(google_id, email, name)

    if not user:
        raise HTTPException(status_code=401, detail="Account does not exist")

    return _user_response(user)


@auth_router.post("/google")
def google_auth(request: GoogleAuthRequest):
    return signup(request)


app.include_router(auth_router)
