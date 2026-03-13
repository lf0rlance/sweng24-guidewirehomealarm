from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config import settings
from app.services.event_service import get_alarm_system_id_for_user

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
        return {"armed": armed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
