"""
core/auth.py — JWT-based authentication utilities (multi-tenant version).

Replaces the old single-operator auth/auth.py. Key changes:
  - No OPERATOR_USERNAME / OPERATOR_PASSWORD env vars.
  - JWT payload now carries user_id and org_id alongside sub (email).
  - get_current_user() returns {"user_id": int, "org_id": int, "email": str}.
  - Every protected route uses this dependency to enforce the org boundary.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# ─── Config ───────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "dev-insecure-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

# ─── Password hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── OAuth2 scheme ────────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ─── Token helpers ────────────────────────────────────────────────────────────

def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException(401) on any failure."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role: str = payload.get("role")

        # Admin JWT: sub + role only, no user_id / org_id
        if role == "admin":
            sub: str = payload.get("sub")
            if sub is None:
                raise credentials_exception
            return {"sub": sub, "role": "admin", "user_id": None, "org_id": None}

        # Regular user JWT: must have sub, user_id, org_id
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        org_id: int = payload.get("org_id")
        if email is None or user_id is None or org_id is None:
            raise credentials_exception
        return {"email": email, "user_id": user_id, "org_id": org_id, "role": "user"}
    except JWTError:
        raise credentials_exception


# ─── FastAPI dependency ─────────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Returns {"email": str, "user_id": int, "org_id": int, "role": str}.
    org_id is the hard multi-tenancy boundary — every query must filter by it.
    Rejects admin tokens (role==admin lacks org_id, cannot act as a regular user).
    """
    claims = verify_token(token)
    if claims.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin tokens cannot be used for user-facing endpoints.",
        )
    return claims


def get_admin_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    FastAPI dependency for admin-only endpoints.
    Returns the JWT payload only if role == 'admin'; raises 403 otherwise.
    """
    claims = verify_token(token)
    if claims.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return claims
