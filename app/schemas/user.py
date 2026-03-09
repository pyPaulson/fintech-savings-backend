from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional
from app.models.user import GenderEnum


# Request schema
class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, description="User's first name")
    last_name: str = Field(..., min_length=1, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    gender: Optional[GenderEnum] = Field(None, description="User's gender")
    date_of_birth: Optional[date] = Field(None, description="User's date of birth")


# Response schema
class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None

    model_config = {"from_attributes": True}  
