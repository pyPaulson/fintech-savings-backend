from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date
from typing import Optional
from uuid import UUID
from app.models.user import GenderEnum


def _normalize_email_str(v: object) -> object:
    if isinstance(v, str):
        return v.strip().lower()
    return v


def _normalize_otp_str(v: object) -> object:
    if isinstance(v, str):
        return v.strip()
    return v


# Request schema
class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, description="User's first name")
    last_name: str = Field(..., min_length=1, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    gender: Optional[GenderEnum] = Field(None, description="User's gender")
    date_of_birth: Optional[date] = Field(None, description="User's date of birth")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        return _normalize_email_str(v)


# Response schema
class UserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}


class AuthSessionResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleTokenLoginRequest(BaseModel):
    id_token: str = Field(..., min_length=10)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        return _normalize_email_str(v)


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1)
    last_name: Optional[str] = Field(None, min_length=1)
    phone_number: Optional[str] = Field(None)
    gender: Optional[GenderEnum] = Field(None)
    date_of_birth: Optional[date] = Field(None)


class PasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        return _normalize_email_str(v)


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=8)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        return _normalize_email_str(v)

    @field_validator("otp", mode="before")
    @classmethod
    def normalize_otp(cls, v: object) -> object:
        return _normalize_otp_str(v)


class PasswordResetOtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        return _normalize_email_str(v)

    @field_validator("otp", mode="before")
    @classmethod
    def normalize_otp(cls, v: object) -> object:
        return _normalize_otp_str(v)


class EmailVerificationRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        return _normalize_email_str(v)


class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        return _normalize_email_str(v)

    @field_validator("otp", mode="before")
    @classmethod
    def normalize_otp(cls, v: object) -> object:
        return _normalize_otp_str(v)
