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
    username: str | None = None
    system_password: str


class ConnectMicrocontrollerRequest(BaseModel):
    username: str | None = None
    microcontroller_id: int

class SimpleStatusResponse(BaseModel):
    status: str
    message: str
