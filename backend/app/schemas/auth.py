"""Pydantic schemas for V9 auth endpoints."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    # bcrypt's effective limit is 72 bytes; enforce 72 chars in the schema
    # so the user gets a clean 422 instead of a 500.
    password: str = Field(..., min_length=8, max_length=72)
    name: str = Field(default="", max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds, for the access token


class UserResponse(BaseModel):
    # Use plain str for email because guest addresses live at the
    # special-use `.local` TLD which EmailStr rejects by spec.
    id: UUID
    email: str
    name: str
    provider: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenPair


class RefreshRequest(BaseModel):
    refresh_token: str


class GuestResponse(BaseModel):
    user: UserResponse
    tokens: TokenPair
    note: str = "Guest sessions are anonymous. Register to keep your data."
