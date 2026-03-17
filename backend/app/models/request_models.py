from pydantic import BaseModel


class GoogleAuthRequest(BaseModel):
    idToken: str


class EmailPasswordLoginRequest(BaseModel):
    email: str
    password: str


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


# Admin-only request bodies
class SetSensorLabelsRequest(BaseModel):
    labels: list[str]  # e.g. ["Front door", "Back door", "Living room window"]


class AddUserToHomeRequest(BaseModel):
    username: str
    email: str
    password: str
    phone: str | None = None
    access_level: str = "owner"  # owner, trusted_full, child, arm_only, viewer, etc.


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
    access_level: str | None = None


class LinkExistingUserToHomeRequest(BaseModel):
    """Admin: link an existing account to a home (no new account created)."""
    email: str | None = None
    user_id: int | None = None
    access_level: str = "owner"