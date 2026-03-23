from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time

from app.config import settings
from app.services.event_service import get_alarm_system_id_for_user, EVENTS, connected_clients
from db.events import save_event

router = APIRouter(prefix="/api/alarm", tags=["alarm"])
security = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
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


@router.get("", response_model=dict)
def get_armed_status(user_id: int = Depends(get_current_user_id)):
    """Return current armed state for the logged-in user's alarm system."""
    alarm_system_id = get_alarm_system_id_for_user(user_id)
    if alarm_system_id is None:
        raise HTTPException(status_code=400, detail="No alarm system linked")
    try:
        from db.getModeOfSystem import getModeBySysId
        armed = getModeBySysId(alarm_system_id)
        return {"armed": bool(armed) if armed is not None else False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("", response_model=dict)
def set_armed_status(
    body: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Set armed state. Body: { \"armed\": true } or { \"armed\": false }."""
    alarm_system_id = get_alarm_system_id_for_user(user_id)
    if alarm_system_id is None:
        raise HTTPException(status_code=400, detail="No alarm system linked")
    armed = body.get("armed")
    if not isinstance(armed, bool):
        raise HTTPException(status_code=400, detail="Body must be { \"armed\": true } or { \"armed\": false }")
    try:
        from db.setModeAlarmSystem import setMode
        setMode(alarm_system_id, armed)

        # Record an alarm state change event so history can show arm/disarm actions.
        event_type = "alarm_enabled" if armed else "alarm_disabled"
        event_dict = {
            "device_id": f"system_{alarm_system_id}",
            "event_type": event_type,
            "count": 1,
            "timestamp": time.time(),
        }

        # Track in in-memory EVENTS and notify any connected event streams.
        EVENTS.append((event_dict, alarm_system_id, True))
        for queue, client_system_id in connected_clients:
            if client_system_id == alarm_system_id:
                queue.put_nowait(event_dict)

        # Persist in DB so it appears in history even after restart.
        try:
            save_event(event_dict, alarm_system_id, True)
        except Exception as persist_err:
            # Log but don't fail the API call – arming still succeeded.
            print(f"Alarm state event persist failed: {persist_err}")

        return {"armed": armed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
