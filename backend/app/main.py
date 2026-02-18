from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import socket

from app.config import settings
from app.routers import auth, events, users, pairing, notifications
from app.models.response_models import HealthResponse


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

    print("============================================")
    print("Home Alarm Backend started")
    print(f"Network URL: {effective_url}")
    print(f"Loopback:    http://127.0.0.1:{port}")
    print("============================================")

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

# Include routers
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(users.router)
app.include_router(pairing.router)
app.include_router(notifications.router)


@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "service": "backend",
        "backend_url": settings.backend_url
    }
