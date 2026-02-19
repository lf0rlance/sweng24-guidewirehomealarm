from fastapi import APIRouter, HTTPException
from app.models.response_models import AuthResponse
from app.models.request_models import GoogleAuthRequest
from app.services.auth_service import signup_user, signin_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(request: GoogleAuthRequest):
    try:
        return signup_user(request.idToken)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/signin", response_model=AuthResponse)
def signin(request: GoogleAuthRequest):
    try:
        return signin_user(request.idToken)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
