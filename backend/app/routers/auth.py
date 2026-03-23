from fastapi import APIRouter, HTTPException
from app.models.response_models import AuthResponse, MfaRequiredResponse
from app.models.request_models import GoogleAuthRequest, OtpVerifyRequest
from app.services.auth_service import signup_user, signin_user_mfa, verify_otp_and_signin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(request: GoogleAuthRequest):
    try:
        return signup_user(request.idToken)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/signin", response_model=MfaRequiredResponse)
def signin(request: GoogleAuthRequest):
    try:
        return signin_user_mfa(request.idToken)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(request: OtpVerifyRequest):
    try:
        return verify_otp_and_signin(request.email, request.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
