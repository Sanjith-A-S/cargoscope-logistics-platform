"""
auth/auth.py — backward-compatibility shim.
The canonical implementation is now in core/auth.py.
"""
from core.auth import (  # noqa: F401
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_HOURS,
    pwd_context,
    oauth2_scheme,
    create_access_token,
    verify_token,
    get_current_user,
)
