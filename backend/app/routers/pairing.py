from fastapi import APIRouter, Depends, HTTPException
from app.models.request_models import PairUserRequest, ConnectMicrocontrollerRequest
from app.models.response_models import SimpleStatusResponse, MicrocontrollerConnectResponse
from db.connectToAlarmSystem import connectUserToSystem, getCurrentAlarmSystemID
from db.connectMCtoAlarmSystem import connectMicroController
from app.security import AuthenticatedUser, get_current_user

router = APIRouter()


@router.post("/api/pair", response_model=SimpleStatusResponse)
def pair_user(
    request: PairUserRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    if not connectUserToSystem(current_user.user_id, request.system_password):
        raise HTTPException(status_code=400, detail="Pairing failed")

    return {"status": "ok", "message": "Paired successfully"}


@router.post("/api/microcontroller/connect", response_model=MicrocontrollerConnectResponse)
def connect_microcontroller(
    request: ConnectMicrocontrollerRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    system_id = getCurrentAlarmSystemID(current_user.user_id)

    if system_id is None:
        raise HTTPException(status_code=400, detail="User not paired")

    if not connectMicroController(
        microControllerId=request.microcontroller_id,
        user_id=current_user.user_id,
    ):
        raise HTTPException(status_code=400, detail="Connection failed")

    return {
        "status": "ok",
        "alarm_system_id": system_id
    }
