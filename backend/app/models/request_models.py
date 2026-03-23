from pydantic import BaseModel


class GoogleAuthRequest(BaseModel):
    idToken: str


class RegisterTokenRequest(BaseModel):
    token: str


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    alarm_system_id: int | None = None


class PairUserRequest(BaseModel):
    username: str
    system_password: str


class ConnectMicrocontrollerRequest(BaseModel):
    username: str
    microcontroller_id: int


class ConnectDeviceRequest(BaseModel):
    """Link ESP32 to current user's alarm system (JWT). Default device_id esp32_001 -> microcontroller_id 1."""
    microcontroller_id: int = 1

class SimpleStatusResponse(BaseModel):
    status: str
    message: str

class OtpVerifyRequest(BaseModel):
    email: str
    code: str

class MfaRequiredResponse(BaseModel):
    mfa_required: bool
    email: str