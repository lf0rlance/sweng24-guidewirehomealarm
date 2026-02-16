from fastapi import APIRouter, HTTPException
from app.models.request_models import CreateUserRequest
from app.models.response_models import SimpleStatusResponse
from db.insertIntoDB import insertUserInDB

router = APIRouter()


@router.post("/api/createUser", response_model=SimpleStatusResponse)
def create_user(request: CreateUserRequest):
    if not insertUserInDB(
        request.username,
        request.email,
        request.alarm_system_id,
        request.password
    ):
        raise HTTPException(status_code=400, detail="User already exists")

    return {"status": "ok"}
