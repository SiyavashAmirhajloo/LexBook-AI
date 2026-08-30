"""Auth API (V9): email/password, Google OAuth, guest."""
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.errors import AuthError, BadRequestError
from app.middleware.auth import current_user
from app.models import User
from app.schemas.auth import (
    AuthResponse,
    GuestResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
)
from app.services.auth import (
    authenticate,
    create_user,
    create_user_session,
    decode_refresh,
    exchange_google_code,
    find_session_by_refresh_hash,
    get_user_for_session,
    hash_refresh_token,
    issue_access_token,
    issue_refresh_token,
    revoke_session,
    upsert_google_user,
    verify_google_id_token,
)

router = APIRouter()


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        provider=user.provider,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def _token_pair(settings: Settings, user: User, refresh_raw: str, kind: str = "user") -> TokenPair:
    access = issue_access_token(settings, str(user.id))
    return TokenPair(
        access_token=access,
        refresh_token=refresh_raw,
        expires_in=settings.jwt_access_expire_minutes * 60,
    )


# ── Register + Login (email/password) ───────────────────────────

@router.post("/auth/register", response_model=AuthResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await create_user(db, email=payload.email, password=payload.password, name=payload.name)
    db.flush()
    raw, hashed = issue_refresh_token(settings, str(user.id), str(user.id))
    await create_user_session(
        db, user, refresh_hash=hashed,
        user_agent=request.headers.get("user-agent", ""),
        ip=request.client.host if request.client else "",
        settings=settings,
    )
    return AuthResponse(user=_user_response(user), tokens=_token_pair(settings, user, raw))


@router.post("/auth/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await authenticate(db, email=payload.email, password=payload.password)
    raw, hashed = issue_refresh_token(settings, str(user.id), str(user.id))
    await create_user_session(
        db, user, refresh_hash=hashed,
        user_agent=request.headers.get("user-agent", ""),
        ip=request.client.host if request.client else "",
        settings=settings,
    )
    return AuthResponse(user=_user_response(user), tokens=_token_pair(settings, user, raw))


# ── Refresh ──────────────────────────────────────────────────────

@router.post("/auth/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    decode_refresh(settings, payload.refresh_token)  # validates token shape/exp
    session = await find_session_by_refresh_hash(db, hash_refresh_token(payload.refresh_token))
    if not session:
        raise AuthError("Refresh token revoked or unknown", code="refresh_invalid")
    if session.expires_at < datetime.now(UTC):
        await revoke_session(db, session)
        raise AuthError("Refresh token expired", code="refresh_expired")
    user = await get_user_for_session(db, session)
    # Rotate: revoke old, mint new
    await revoke_session(db, session)
    raw, hashed = issue_refresh_token(settings, str(user.id), str(user.id))
    await create_user_session(
        db, user, refresh_hash=hashed,
        user_agent=request.headers.get("user-agent", ""),
        ip=request.client.host if request.client else "",
        settings=settings,
    )
    return _token_pair(settings, user, raw)


# ── Logout ────────────────────────────────────────────────────────

@router.post("/auth/logout", status_code=204)
async def logout(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await find_session_by_refresh_hash(db, hash_refresh_token(payload.refresh_token))
    if session:
        await revoke_session(db, session)


# ── Guest ────────────────────────────────────────────────────────

@router.post("/auth/guest", response_model=GuestResponse)
async def guest(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not settings.allow_guest:
        raise HTTPException(status_code=404, detail="Guest mode disabled")
    user = User(
        email=f"guest+{secrets.token_hex(6)}@lexbook.local",
        name="Guest",
        provider="guest",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    raw, hashed = issue_refresh_token(settings, str(user.id), str(user.id))
    await create_user_session(
        db, user, refresh_hash=hashed, settings=settings
    )
    return GuestResponse(user=_user_response(user), tokens=_token_pair(settings, user, raw))


# ── Google OAuth ─────────────────────────────────────────────────

@router.get("/auth/google/url")
async def google_url(settings: Settings = Depends(get_settings)):
    """Return the Google consent URL for the client to redirect to."""
    if not settings.google_client_id:
        raise BadRequestError("Google OAuth not configured on this server")
    params = (
        f"client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&access_type=offline"
    )
    return {
        "url": f"https://accounts.google.com/o/oauth2/v2/auth?{params}",
    }


@router.post("/auth/google/callback")
async def google_callback(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    tokens = await exchange_google_code(settings, code)
    id_token = tokens.get("id_token")
    if not id_token:
        raise AuthError("Google did not return id_token", code="google_no_id_token")
    claims = await verify_google_id_token(settings, id_token)
    email = claims.get("email")
    if not email:
        raise AuthError("Google account has no email", code="google_no_email")
    user = await upsert_google_user(
        db, email=email, name=claims.get("name", ""), verified=claims.get("email_verified", False)
    )
    raw, hashed = issue_refresh_token(settings, str(user.id), str(user.id))
    await create_user_session(
        db, user, refresh_hash=hashed,
        user_agent=request.headers.get("user-agent", ""),
        ip=request.client.host if request.client else "",
        settings=settings,
    )
    return AuthResponse(user=_user_response(user), tokens=_token_pair(settings, user, raw))


# ── Me ───────────────────────────────────────────────────────────

@router.get("/auth/me", response_model=UserResponse)
async def me(user: User = Depends(current_user)):
    return _user_response(user)
