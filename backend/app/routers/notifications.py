from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config import settings
from app.models.request_models import RegisterTokenRequest
from app.models.response_models import SimpleStatusResponse
from app.services.notification_service import register_fcm_token
from db.connectToAlarmSystem import ensure_user_has_alarm_system

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

security = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> int:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        return int(payload["userId"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/register", response_model=SimpleStatusResponse)
def register_token(
    request: RegisterTokenRequest,
    user_id: int = Depends(get_current_user_id)
):
    # Ensure user has an alarm system (create one if needed) so we can store their FCM token
    alarm_system_id = ensure_user_has_alarm_system(user_id)
    if alarm_system_id is None:
        raise HTTPException(status_code=400, detail="Could not create alarm system")

    register_fcm_token(alarm_system_id, request.token, user_id)
    return {"status": "ok", "message": "Token registered"}