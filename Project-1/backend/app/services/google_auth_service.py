"""Google OAuth 2.0 authentication service."""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

import requests
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.models import User
from app.services.auth_service import normalize_email, validate_amzur_email

_GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

AUTH_URL = "https://accounts.google.com/o/oauth2/auth"

TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

_STATE_TTL_SECONDS = 600
_state_store: dict[str, tuple[str, float]] = {}


def _cleanup_state_store(now: float) -> None:
    expired = [k for k, (_, expires_at) in _state_store.items() if expires_at <= now]
    for key in expired:
        _state_store.pop(key, None)


def _generate_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return verifier, challenge


def _require_oauth_settings() -> None:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "oauth_not_configured",
                "message": "Google OAuth credentials are not configured.",
            },
        )


def build_authorization_url() -> str:
    """Return the Google OAuth consent-screen URL."""
    _require_oauth_settings()
    now = time.time()
    _cleanup_state_store(now)

    state = secrets.token_urlsafe(32)
    code_verifier, code_challenge = _generate_pkce_pair()
    _state_store[state] = (code_verifier, now + _STATE_TTL_SECONDS)

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(_GOOGLE_SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "select_account",
        # Domain hint keeps the user on company accounts.
        "hd": "amzur.com",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


async def handle_oauth_callback(
    code: str,
    state: str | None,
    db: AsyncSession,
) -> User:
    """Exchange the authorization code for a profile, then upsert the user."""
    _require_oauth_settings()
    now = time.time()
    _cleanup_state_store(now)

    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "oauth_state_missing",
                "message": "OAuth state missing from callback.",
            },
        )

    state_entry = _state_store.pop(state, None)
    if state_entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "oauth_state_invalid",
                "message": "OAuth state is invalid or expired. Retry sign-in.",
            },
        )

    code_verifier, _expires_at = state_entry

    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)

    if response.status_code != 200:
        print("Google OAuth Error:", response.text)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "oauth_code_exchange_failed",
                "message": response.text,
            },
        )

    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "oauth_code_exchange_failed",
                "message": "Token response did not include access_token.",
            },
        )

    profile_response = requests.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if profile_response.status_code != 200:
        print("Google UserInfo Error:", profile_response.text)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "oauth_profile_fetch_failed",
                "message": profile_response.text,
            },
        )

    profile = profile_response.json()
    email = normalize_email(profile.get("email", ""))

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "oauth_no_email",
                "message": "Google account did not provide an email address.",
            },
        )

    # Domain restriction — same policy as password auth
    validate_amzur_email(email)

    # Upsert: link existing account OR create Google-only account
    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, hashed_password=None)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user
