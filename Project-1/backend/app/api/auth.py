"""Auth routes — register, login, logout, me, Google OAuth."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.core.security import ACCESS_COOKIE_NAME, create_access_token, get_current_user
from app.db import get_db
from app.models import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse
from app.services import auth_service
from app.services import google_auth_service

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


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

@router.get("/google/login")
async def google_login() -> RedirectResponse:
    """Redirect the browser to Google's OAuth consent screen."""
    authorization_url = google_auth_service.build_authorization_url()
    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedirectResponse:
    """Exchange the Google authorization code for a user and issue a JWT cookie."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "missing_code",
                "message": "Authorization code not found in callback",
            },
        )

    # Kept for future CSRF protection enhancements.
    _ = state

    try:
        user = await google_auth_service.handle_oauth_callback(
            code=code,
            state=state,
            db=db,
        )
        token = create_access_token(user_id=user.id, email=user.email)

        # Build a redirect to the frontend chat page and attach the cookie to it
        frontend_url = "http://localhost:5173/chat"
        redirect = RedirectResponse(url=frontend_url, status_code=status.HTTP_302_FOUND)
        redirect.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=token,
            httponly=True,
            secure=settings.ENVIRONMENT != "development",
            samesite="lax",
            max_age=settings.JWT_EXPIRE_MINUTES * 60,
            path="/",
        )
        return redirect
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "oauth_failed", "message": str(exc)},
        ) from exc
