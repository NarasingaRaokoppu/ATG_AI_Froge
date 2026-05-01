"""Auth routes — register, login, logout, me."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.core.security import ACCESS_COOKIE_NAME, get_current_user
from app.db import get_db
from app.models import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Create a new account without starting an authenticated session."""
    return await auth_service.register_user(db, payload.email, payload.password)


@router.post("/login", response_model=UserResponse)
async def login(
    payload: UserLogin,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Verify credentials and issue an httpOnly auth cookie."""
    user, token = await auth_service.login_user(db, payload.email, payload.password)
    _set_cookie(response, token)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Clear the auth cookie."""
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Return the currently authenticated user."""
    return current_user
