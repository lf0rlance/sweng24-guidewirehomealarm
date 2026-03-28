from pydantic import BaseModel, EmailStr, Field


class GoogleAuthRequest(BaseModel):
    idToken: str


class EmailPasswordLoginRequest(BaseModel):
    email: str
    password: str


class RegisterTokenRequest(BaseModel):
    token: str


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class PairUserRequest(BaseModel):
    username: str | None = None
    system_password: str = Field(min_length=8)


class ConnectMicrocontrollerRequest(BaseModel):
    username: str | None = None
    microcontroller_id: int = Field(gt=0)


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

# Admin-only request bodies
class SetSensorLabelsRequest(BaseModel):
    labels: list[str]  # e.g. ["Front door", "Back door", "Living room window"]


class AddUserToHomeRequest(BaseModel):
    username: str
    email: str
    password: str
    phone: str | None = None


class NotifyHomeownerRequest(BaseModel):
    title: str
    body: str


class UpdateAlarmSystemRequest(BaseModel):
    name: str


class UpdateUserRequest(BaseModel):
    username: str | None = None
    email: str | None = None
    phone: str | None = None
    password: str | None = None
