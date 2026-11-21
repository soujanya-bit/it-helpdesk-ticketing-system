
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Common fields shared by user schemas."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)


class UserCreate(UserBase):
    """Fields required when registering a new user."""

    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Credentials required for user login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(UserBase):
    """User information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT access token returned after successful login."""

    access_token: str
    token_type: str = "bearer"
