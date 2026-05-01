"""Authentication business logic."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_amzur_email(email: str) -> None:
    domain = email.split("@")[-1].lower()
    if domain != "amzur.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden_domain",
                "message": "Only Amzur company emails are allowed.",
            },
        )


async def register_user(db: AsyncSession, email: str, password: str) -> User:
    """Create a new user with a hashed password."""
    normalized_email = normalize_email(email)
    validate_amzur_email(normalized_email)
    existing = await db.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "email_taken",
                "message": "An account with that email already exists",
            },
        )

    user = User(email=normalized_email, hashed_password=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, email: str, password: str) -> tuple[User, str]:
    """Verify credentials and return (user, access_token)."""
    normalized_email = normalize_email(email)
    validate_amzur_email(normalized_email)
    user = await db.scalar(select(User).where(User.email == normalized_email))
    if user is None or user.hashed_password is None:
        raise _user_not_registered()
    if not verify_password(password, user.hashed_password):
        raise _invalid_credentials()

    token = create_access_token(user_id=user.id, email=user.email)
    return user, token


def _user_not_registered() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "user_not_registered", "message": "User not registered"},
    )


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "invalid_credentials", "message": "Incorrect email or password"},
    )
