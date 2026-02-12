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
import sys
from pathlib import Path

# Add backend and db directories to path to allow db imports
backend_dir = Path(__file__).resolve().parent.parent
db_dir = backend_dir / "db"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(db_dir))

from db.connectToAlarmSystem import connectUserToSystem, getCurrentAlarmSystemID
from db.connectMCtoAlarmSystem import connectMicroController
from db.insertIntoDB import insertUserInDB
from db.googleAuth import find_or_create_google_user, find_google_user_only

#########
#imports for Google OAuth
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import jwt
from pydantic import BaseModel


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


# Temporary storage
EVENTS: List[ValidateData] = []

connected_clients: List[asyncio.Queue] = []

# FCM tokens for push notifications (device tokens registered by the app)
fcm_tokens: List[str] = []
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


def _send_push_for_event(event: ValidateData):
    """Send FCM notification for door_open / door_closed to all registered tokens."""
    if event.event_type not in ("door_open", "door_closed"):
        return
    if not fcm_tokens:
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
            tokens=fcm_tokens,
        )
        messaging.send_each_for_multicast(message)
    except Exception as e:
        print(f"FCM send failed: {e}")


class RegisterTokenRequest(BaseModel):
    token: str


@app.post("/api/notifications/register")
def register_fcm_token(req: RegisterTokenRequest):
    if not req.token or not req.token.strip():
        raise HTTPException(status_code=400, detail="Missing token")
    t = req.token.strip()
    if t not in fcm_tokens:
        fcm_tokens.append(t)
    return {"status": "ok", "message": "Token registered"}


@app.post("/api/events")
def receive_event(event: ValidateData):
    EVENTS.append(event)

    # Push the new event into every connected client's queue
    for queue in connected_clients:
        queue.put_nowait(event.model_dump())

    # Push notification for door open/close
    _send_push_for_event(event)

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

<<<<<<< HEAD
=======
#########
# Google OAuth endpoints - use a router so /api/auth/* is guaranteed to work

from fastapi import APIRouter

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
>>>>>>> b17c1d96c94f42a75b5950b4d7ced8e0a8195c63
