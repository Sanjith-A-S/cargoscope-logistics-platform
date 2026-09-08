from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from auth.auth import create_access_token, authenticate_operator, get_current_user

router = APIRouter(tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate the operator and return a JWT access token."""
    if not authenticate_operator(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": request.username})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return information about the currently authenticated operator."""
    return {"username": current_user["username"], "role": "operator"}
