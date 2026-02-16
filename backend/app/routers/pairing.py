from fastapi import APIRouter, HTTPException
from app.models.request_models import PairUserRequest, ConnectMicrocontrollerRequest
from app.models.response_models import SimpleStatusResponse, MicrocontrollerConnectResponse
from db.connectToAlarmSystem import connectUserToSystem, getCurrentAlarmSystemID
from db.connectMCtoAlarmSystem import connectMicroController

router = APIRouter()


@router.post("/api/pair", response_model=SimpleStatusResponse)
def pair_user(request: PairUserRequest):
    if not connectUserToSystem(request.username, request.system_password):
        raise HTTPException(status_code=400, detail="Pairing failed")

    return {"status": "ok"}


@router.post("/api/microcontroller/connect", response_model=MicrocontrollerConnectResponse)
def connect_microcontroller(request: ConnectMicrocontrollerRequest):
    system_id = getCurrentAlarmSystemID(request.username)

    if system_id is None:
        raise HTTPException(status_code=400, detail="User not paired")

    if not connectMicroController(
        microControllerId=request.microcontroller_id,
        username=request.username
    ):
        raise HTTPException(status_code=400, detail="Connection failed")

    return {
        "status": "ok",
        "alarm_system_id": system_id
    }
