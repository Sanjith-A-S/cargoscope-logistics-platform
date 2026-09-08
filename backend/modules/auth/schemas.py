"""
modules/auth/schemas.py — Pydantic request/response models for Auth module.
"""
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: str
    password: str
    org_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    email: str
    org_id: int
    org_name: str
    user_id: int
