"""
modules/auth/router.py — Auth endpoints (signup, login, me).

Registration line in main.py:
    app.include_router(auth_router, prefix="/api")
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.db import get_db
from core.auth import get_current_user
from core.models import User, Organization
from modules.auth.schemas import SignupRequest, LoginRequest, TokenResponse, MeResponse
from modules.auth import service

router = APIRouter(tags=["Auth"])


@router.post("/auth/signup", response_model=TokenResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Create a new organisation and its first user. Returns a JWT immediately."""
    user = service.create_org_and_user(
        email=request.email,
        password=request.password,
        org_name=request.org_name,
        db=db,
    )
    token = service.build_token(user)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email + password. Returns a JWT.

    Admin credentials are checked first:
      - If ADMIN_USERNAME / ADMIN_PASSWORD_HASH env vars are set and match,
        issues a JWT with role='admin' — frontend redirects to /admin.
      - Otherwise, proceeds with regular org-user authentication.
    """
    # 1. Try admin credentials (returns token str or None)
    admin_token = service.try_authenticate_admin(request.email, request.password)
    if admin_token:
        return {"access_token": admin_token, "token_type": "bearer"}

    # 2. Fall through to regular user auth
    user = service.authenticate_user(
        email=request.email,
        password=request.password,
        db=db,
    )
    token = service.build_token(user)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/me", response_model=MeResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's profile."""
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    org = db.query(Organization).filter(Organization.id == current_user["org_id"]).first()
    return {
        "email": user.email,
        "org_id": user.org_id,
        "org_name": org.name if org else "",
        "user_id": user.id,
    }
