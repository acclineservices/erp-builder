"""Request and response contracts for authentication endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EmailLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    remember_me: bool = False


class EmailRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class MobileRequest(BaseModel):
    mobile_number: str = Field(min_length=6, max_length=20)


class MobileOtpLoginRequest(MobileRequest):
    code: str = Field(min_length=6, max_length=6)
    remember_me: bool = False


class TokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=512)


class ActivationRequest(TokenRequest):
    password: str = Field(min_length=8, max_length=256)


class MobilePasswordResetRequest(MobileOtpLoginRequest):
    new_password: str = Field(min_length=8, max_length=256)


class PasswordResetRequest(TokenRequest):
    new_password: str = Field(min_length=8, max_length=256)


class MessageResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str | None
    mobile_number: str | None
    account_state: str
    is_platform_admin: bool


class SessionResponse(BaseModel):
    user: UserResponse
    expires_at: datetime


class CompanyResponse(BaseModel):
    id: UUID
    business_name: str

