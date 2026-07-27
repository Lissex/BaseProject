from uuid import UUID

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str
    email: str
    phone: str
    password: str = Field(min_length=1)


class RegisterResponse(BaseModel):
    id: UUID
    username: str
    email: str
    phone: str


class LoginRequest(BaseModel):
    identifier: str  # username или email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
    all_devices: bool = False