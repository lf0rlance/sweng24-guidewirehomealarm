from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time

from app.config import settings
from app.services.event_service import get_alarm_system_id_for_user, EVENTS, connected_clients
from db.events import save_event
from db import access_control
from db import disarm_codes

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
    membership = access_control.get_membership(user_id, alarm_system_id)
    if membership is None:
        raise HTTPException(status_code=403, detail="No access to this home")
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
    """
    Set armed state.

    Body:
      - { "armed": true } or { "armed": false }
      - optional for disarm: { "armed": false, "disarm_code": "ABC12345" }
    """
    alarm_system_id = get_alarm_system_id_for_user(user_id)
    if alarm_system_id is None:
        raise HTTPException(status_code=400, detail="No alarm system linked")
    armed = body.get("armed")
    if not isinstance(armed, bool):
        raise HTTPException(status_code=400, detail="Body must be { \"armed\": true } or { \"armed\": false }")
    membership = access_control.get_membership(user_id, alarm_system_id)
    if membership is None:
        raise HTTPException(status_code=403, detail="No access to this home")
    if armed and not membership.can_arm:
        raise HTTPException(status_code=403, detail="Not allowed to arm")
    if (not armed) and (not membership.can_disarm):
        # Allow one-time disarm codes for users without disarm permission.
        code = (body.get("disarm_code") or "").strip()
        ok, err = disarm_codes.consume_one_time_disarm_code(alarm_system_id, code, used_by_user_id=user_id)
        if not ok:
            raise HTTPException(status_code=403, detail=err or "Not allowed to disarm")
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


@router.post("/disarm-code", response_model=dict)
def create_disarm_code(
    body: dict,
    user_id: int = Depends(get_current_user_id),
):
    """
    Create a one-time disarm code for this home. Only users who can manage users can create codes.
    Body: { "ttl_seconds": 600 }
    """
    alarm_system_id = get_alarm_system_id_for_user(user_id)
    if alarm_system_id is None:
        raise HTTPException(status_code=400, detail="No alarm system linked")
    membership = access_control.get_membership(user_id, alarm_system_id)
    if membership is None or not membership.can_manage_users:
        raise HTTPException(status_code=403, detail="Not allowed to create disarm codes")
    ttl_seconds = body.get("ttl_seconds")
    if ttl_seconds is None:
        ttl_seconds = 600
    try:
        ttl_seconds = int(ttl_seconds)
    except Exception:
        raise HTTPException(status_code=400, detail="ttl_seconds must be an integer")
    code = disarm_codes.create_one_time_disarm_code(
        alarm_system_id=alarm_system_id,
        created_by_user_id=user_id,
        ttl_seconds=ttl_seconds,
    )
    if not code:
        raise HTTPException(status_code=500, detail="Could not create code")
    return {"code": code, "ttl_seconds": ttl_seconds}
