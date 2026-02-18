from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config import settings
from app.models.request_models import RegisterTokenRequest
from app.models.response_models import SimpleStatusResponse
from app.services.notification_service import register_fcm_token
from app.services.event_service import get_alarm_system_id_for_user

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
    alarm_system_id = get_alarm_system_id_for_user(user_id)

    if alarm_system_id is None:
        raise HTTPException(status_code=400, detail="User not paired")

    register_fcm_token(alarm_system_id, request.token)

    return {
        "status": "ok",
        "message": "Token registered"
    }