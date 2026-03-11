from pydantic import BaseModel, EmailStr, Field


class GoogleAuthRequest(BaseModel):
    idToken: str


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

class SimpleStatusResponse(BaseModel):
    status: str
    message: str
