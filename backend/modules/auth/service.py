"""
modules/auth/service.py — Business logic for signup and login.

Multi-tenancy design:
  - Each signup creates a new Organization + the first User in that org.
  - Passwords are bcrypt-hashed via passlib.
  - login() validates against the users table — no hardcoded credentials.
  - Admin login: checked via ADMIN_USERNAME + ADMIN_PASSWORD_HASH env vars.
    Issues a JWT with role: 'admin' (no org_id).
"""
import os
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from core.models import Organization, User
from core.auth import pwd_context, create_access_token


def create_org_and_user(email: str, password: str, org_name: str, db: Session) -> User:
    """
    Create a new organization and its first user.
    Raises 409 if email is already registered.
    """
    # Check for duplicate email
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create org
    org = Organization(name=org_name.strip())
    db.add(org)
    db.flush()  # get org.id

    # Create user
    user = User(
        email=email.lower().strip(),
        password_hash=pwd_context.hash(password),
        org_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(email: str, password: str, db: Session) -> User:
    """
    Validate credentials against the users table.
    Raises 401 on any failure (intentionally vague for security).
    """
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def build_token(user: User) -> str:
    """Build a JWT for an authenticated user, embedding org_id as the tenancy claim."""
    return create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "org_id": user.org_id,
        }
    )


import logging
logger = logging.getLogger(__name__)


def try_authenticate_admin(username: str, password: str) -> str | None:
    """
    Check whether the credentials match the admin account configured via env vars.

    Returns a signed JWT with role='admin' if they match, or None if they don't
    (caller then falls through to regular user auth).

    Admin credentials are stored as:
      ADMIN_USERNAME  — the username string (not an email)
      ADMIN_PASSWORD_HASH — bcrypt hash of the password (same scheme as users)
    """
    admin_username = os.getenv("ADMIN_USERNAME", "")
    admin_pw_hash  = os.getenv("ADMIN_PASSWORD_HASH", "")

    if not admin_username or not admin_pw_hash:
        logger.debug("Admin auth skipped: ADMIN_USERNAME or ADMIN_PASSWORD_HASH not configured.")
        return None  # Admin account not configured — skip

    if username.strip() != admin_username:
        logger.debug("Admin auth skipped: username '%s' != admin_username", username)
        return None  # Not the admin username — fall through

    if not pwd_context.verify(password, admin_pw_hash):
        logger.warning("Admin auth failed: invalid password for admin user '%s'", admin_username)
        return None  # Wrong password — fall through (don't expose which part failed)

    logger.info("Admin user '%s' authenticated successfully.", admin_username)
    return create_access_token(data={"sub": admin_username, "role": "admin"})

