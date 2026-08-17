"""
schemas/auth.py — Pydantic schemas for JWT authentication.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: Optional[str]
    kabupaten: Optional[str]


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str
    full_name: Optional[str] = None
    kabupaten: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str]
    kabupaten: Optional[str]
    is_active: bool
    farmer_id: Optional[int] = None
    hub_id: Optional[int] = None

    model_config = {"from_attributes": True}
