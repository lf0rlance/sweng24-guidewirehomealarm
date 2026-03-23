from pydantic import BaseModel
from typing import Optional


class SimpleStatusResponse(BaseModel):
    status: str
    message: str  # Added this field


class UserResponse(BaseModel):
    id: int
    email: str
    name: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class MicrocontrollerConnectResponse(BaseModel):
    status: str
    alarm_system_id: int


class HealthResponse(BaseModel):
    status: str
    service: str
    backend_url: Optional[str]

class MfaRequiredResponse(BaseModel):
    mfa_required: bool
    email: str