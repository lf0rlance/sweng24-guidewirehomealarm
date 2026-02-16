import asyncio
import json
import socket
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Set, Tuple

from fastapi import APIRouter, FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import jwt
from pydantic import BaseModel

from app.config import settings
from app.validate2 import ValidateData

# Add backend and db to path for db imports
backend_dir = Path(__file__).resolve().parent.parent
db_dir = backend_dir / "db"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(db_dir))

from db.connectToAlarmSystem import (
    connectUserToSystem,
    getCurrentAlarmSystemID,
    get_alarm_system_id_by_user_id,
    get_alarm_system_id_by_device_id,
)
from db.connectMCtoAlarmSystem import connectMicroController
from db.insertIntoDB import insertUserInDB
from db.googleAuth import find_or_create_google_user, find_google_user_only


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
    print("Home Alarm Backend started")
    print(f"Network URL: {effective_url}")
    print(f"Loopback:    http://127.0.0.1:{port}")
    for route in app.routes:
        if hasattr(route, "path") and "/api/auth" in getattr(route, "path", ""):
            methods = getattr(route, "methods", set()) or set()
            print(f"  Auth: {', '.join(sorted(methods))} {route.path}")
    print("================================================")

    yield

    # ---- shutdown ----
    print("Home Alarm Backend shutting down")


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

# --- Auth and ping first so they are always registered ---
@app.get("/ping")
def ping():
    return {"pong": True}


@app.get("/api/auth/health")
def api_auth_health():
    return {"status": "ok", "auth": "signup,signin,google"}


# Events stored as (event_dict, alarm_system_id). alarm_system_id is None if device not registered.
EVENTS: List[Tuple[dict, int | None]] = []

# Each stream client: (queue, alarm_system_id). Events are only pushed to queues with matching alarm_system_id.
connected_clients: List[Tuple[asyncio.Queue, int | None]] = []

security = HTTPBearer(auto_error=False)


def get_current_user_id(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> int:
    """Decode JWT from Authorization header and return user id. Raises 401 if missing or invalid."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
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

# FCM tokens per alarm_system_id so push is only sent to devices for that system
fcm_tokens_by_system: Dict[int, Set[str]] = {}
_firebase_initialized = False


def _init_firebase_if_needed():
    global _firebase_initialized
    if _firebase_initialized:
        return True
    if not getattr(settings, "firebase_credentials_path", None) or not settings.firebase_credentials_path:
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
        print(f"Firebase init failed (push disabled): {e}")
    return False


def _send_push_for_event(event: ValidateData, alarm_system_id: int | None):
    """Send FCM notification for door_open / door_closed only to tokens registered for this alarm system."""
    if event.event_type not in ("door_open", "door_closed"):
        return
    if alarm_system_id is None:
        print(f"[FCM] skip push for {event.device_id}: device not linked to any alarm system")
        return
    tokens = list(fcm_tokens_by_system.get(alarm_system_id) or [])
    if not tokens:
        print(f"[FCM] skip push for alarm_system_id={alarm_system_id} ({event.device_id}): no tokens registered")
        return
    if not _init_firebase_if_needed():
        return
    try:
        from firebase_admin import messaging
        title = "Door opened" if event.event_type == "door_open" else "Door closed"
        body = f"{event.device_id}"
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={"event_type": event.event_type, "device_id": event.device_id},
            tokens=tokens,
        )
        messaging.send_each_for_multicast(message)
        print(f"[FCM] push sent: alarm_system_id={alarm_system_id} {event.event_type} -> {len(tokens)} device(s)")
    except Exception as e:
        print(f"FCM send failed: {e}")


class RegisterTokenRequest(BaseModel):
    token: str


@app.post("/api/notifications/register")
def register_fcm_token(req: RegisterTokenRequest, user_id: int = Depends(get_current_user_id)):
    """Register FCM token for the authenticated user's alarm system. Requires Authorization Bearer."""
    if not req.token or not req.token.strip():
        raise HTTPException(status_code=400, detail="Missing token")
    t = req.token.strip()
    alarm_system_id = get_alarm_system_id_by_user_id(user_id)
    if alarm_system_id is None:
        print(f"[FCM] user_id={user_id} has no alarm_system_id; token not stored")
        return {"status": "ok", "message": "Token not associated (user not paired with a system)"}
    # Remove token from any other system (e.g. re-register after login on same device)
    for sid, tokens in list(fcm_tokens_by_system.items()):
        tokens.discard(t)
    for sid in list(fcm_tokens_by_system.keys()):
        if not fcm_tokens_by_system[sid]:
            del fcm_tokens_by_system[sid]
    fcm_tokens_by_system.setdefault(alarm_system_id, set()).add(t)
    print(f"[FCM] token registered: user_id={user_id} -> alarm_system_id={alarm_system_id} (tokens for this system: {len(fcm_tokens_by_system[alarm_system_id])})")
    return {"status": "ok", "message": "Token registered for your alarm system"}


@app.get("/api/notifications/debug")
def debug_fcm_tokens():
    """Debug: list FCM tokens and device->system mapping so you can see why esp32_222 might go to wrong user."""
    # Which alarm_system_id does each test device map to?
    device_to_system = {
        "esp32_111": get_alarm_system_id_by_device_id("esp32_111"),
        "esp32_222": get_alarm_system_id_by_device_id("esp32_222"),
    }
    out = {}
    for sid, tokens in fcm_tokens_by_system.items():
        out[int(sid)] = {
            "count": len(tokens),
            "token_previews": [t[-8:] if len(t) >= 8 else "..." for t in sorted(tokens)],
        }
    return {
        "device_to_alarm_system": device_to_system,
        "fcm_tokens_by_system": out,
    }


@app.post("/api/events")
def receive_event(event: ValidateData):
    # Associate event with alarm system by device_id (esp32_xxxxx -> microcontroller lookup)
    alarm_system_id = get_alarm_system_id_by_device_id(event.device_id)
    event_dict = event.model_dump()
    EVENTS.append((event_dict, alarm_system_id))

    # Push only to stream clients that belong to this alarm system
    for queue, client_system_id in connected_clients:
        if client_system_id is not None and client_system_id == alarm_system_id:
            queue.put_nowait(event_dict)

    # Push notification only to tokens registered for this event's alarm system
    _send_push_for_event(event, alarm_system_id)

    return {
        "status": "ok",
        "message": "Event received"
    }


@app.get("/events")
def get_events(user_id: int = Depends(get_current_user_id)):
    """Return events for the authenticated user's alarm system only."""
    alarm_system_id = get_alarm_system_id_by_user_id(user_id)
    if alarm_system_id is None:
        return []  # User not paired with a system; show no events
    return [
        event_dict
        for event_dict, sid in EVENTS
        if sid == alarm_system_id
    ]


@app.get("/events/stream")
async def stream_events(user_id: int = Depends(get_current_user_id)):
    """SSE stream of events for the authenticated user's alarm system only."""
    alarm_system_id = get_alarm_system_id_by_user_id(user_id)
    queue: asyncio.Queue = asyncio.Queue()
    entry = (queue, alarm_system_id)
    connected_clients.append(entry)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if entry in connected_clients:
                connected_clients.remove(entry)

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
        username=username
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

# Google OAuth endpoints (router so /api/auth/* is registered)
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


class GoogleAuthRequest(BaseModel):
    idToken: str


def _verify_google_token(id_token_str: str):
    """Verify Google ID token and return idinfo dict. Raises on failure."""
    idinfo = id_token.verify_oauth2_token(
        id_token_str,
        google_requests.Request(),
        settings.google_client_id
    )
    if idinfo['aud'] != settings.google_client_id:
        raise ValueError('Could not verify audience.')
    return idinfo


def _user_response(user: dict):
    """Build JWT and user response for a given user dict."""
    token = jwt.encode(
        {"userId": user["id"], "email": user["email"]},
        settings.jwt_secret,
        algorithm="HS256"
    )
    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]}
    }


@auth_router.get("/health")
def auth_health():
    """Verify auth routes are loaded."""
    return {"status": "ok", "auth": "signup,signin,google"}


@auth_router.post("/signup")
def signup(request: GoogleAuthRequest):
    """
    Sign up: verify Google token, create user in DB only if new. If account exists, return error.
    """
    if not request.idToken:
        raise HTTPException(status_code=400, detail="Missing idToken")
    if not settings.google_client_id or not settings.jwt_secret:
        raise HTTPException(status_code=500, detail="Auth not configured")
    try:
        idinfo = _verify_google_token(request.idToken)
        google_id = idinfo.get('sub')
        email = idinfo.get('email')
        name = idinfo.get('name', (email or '').split('@')[0])
        if not google_id or not email:
            raise HTTPException(status_code=401, detail="Invalid Google token: missing user info")
        # Reject signup if account already exists
        existing = find_google_user_only(google_id, email, name)
        if existing:
            raise HTTPException(status_code=409, detail="Account already exists. Please sign in instead.")
        try:
            user = find_or_create_google_user(google_id, email, name)
        except Exception as db_error:
            print(f"Database error during signup: {db_error}")
            raise HTTPException(status_code=503, detail=f"Database error: {str(db_error)}")
        if not user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        return _user_response(user)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@auth_router.post("/signin")
def signin(request: GoogleAuthRequest):
    """
    Sign in: verify Google token, return JWT only if user already exists in DB.
    """
    if not request.idToken:
        raise HTTPException(status_code=400, detail="Missing idToken")
    if not settings.google_client_id or not settings.jwt_secret:
        raise HTTPException(status_code=500, detail="Auth not configured")
    try:
        idinfo = _verify_google_token(request.idToken)
        google_id = idinfo.get('sub')
        email = idinfo.get('email')
        name = idinfo.get('name', (email or '').split('@')[0])
        if not google_id or not email:
            raise HTTPException(status_code=401, detail="Invalid Google token: missing user info")
        user = find_google_user_only(google_id, email, name)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Account does not exist. Please sign up."
            )
        return _user_response(user)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signin error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# Legacy: same behavior as signup
@auth_router.post("/google")
def google_auth(request: GoogleAuthRequest):
    """Verify Google ID token and create/return user with JWT (same as signup)."""
    return signup(request)


# Mount auth router on the main app
app.include_router(auth_router)
