from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    email: EmailStr
    role: str
    exp: datetime
    type: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class OTPChallenge(BaseModel):
    message: str
    otp_token: str


class OTPResend(BaseModel):
    otp_token: str


class OTPVerify(BaseModel):
    otp_token: str
    code: str = Field(..., pattern=r"^\d{6}$")


class MessageResponse(BaseModel):
    message: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
