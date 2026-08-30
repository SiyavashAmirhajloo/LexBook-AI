"""Auth service (V9).

JWT issuance/verification, Google OAuth code exchange, password hashing,
and the user/store primitives. Public surface used by api/auth.py and
middleware/auth.py.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AuthError, BadRequestError
from app.models import User, UserSession

# We use `bcrypt` directly instead of passlib. passlib 1.7.4 has a known
# incompatibility with bcrypt>=4 (it tries to hash a 50+ byte "wrap bug
# detection" string, which bcrypt 4.x rejects outright). Direct bcrypt
# is two lines of code and avoids that whole mess.
_BCRYPT_ROUNDS = 12


def hash_password(plain: str) -> str:
    pw = plain.encode("utf-8")[:72]  # bcrypt hard limit
    return bcrypt.hashpw(pw, bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pw = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pw, hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT ────────────────────────────────────────────────────────────

class TokenKind:
    ACCESS = "access"
    REFRESH = "refresh"
    GUEST = "guest"


def _now() -> datetime:
    return datetime.now(UTC)


def _encode(
    settings: Settings, sub: str, kind: str, ttl: timedelta, extra: dict[str, Any] | None = None
) -> str:
    payload: dict[str, Any] = {
        "sub": sub,
        "kind": kind,
        "iat": int(_now().timestamp()),
        "exp": int((_now() + ttl).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode(settings: Settings, token: str, expected_kind: str | None = None) -> dict:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as e:
        raise AuthError("Token expired", code="token_expired") from e
    except jwt.InvalidTokenError as e:
        raise AuthError("Invalid token", code="invalid_token") from e
    if expected_kind and data.get("kind") != expected_kind:
        raise AuthError(f"Wrong token type (got {data.get('kind')})", code="wrong_token_type")
    return data


def issue_access_token(settings: Settings, user_id: str) -> str:
    return _encode(
        settings, user_id, TokenKind.ACCESS, timedelta(minutes=settings.jwt_access_expire_minutes)
    )


def issue_refresh_token(
    settings: Settings, user_id: str, session_id: str
) -> tuple[str, str]:
    """Returns (signed_jwt_refresh, sha256_hex). The raw JWT is sent to the
    client; the hash is what we store, so we can revoke by hash without
    needing the original token."""
    raw = encode_refresh_token(settings, user_id, session_id)
    return raw, hashlib.sha256(raw.encode()).hexdigest()


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def encode_refresh_token(settings: Settings, user_id: str, session_id: str) -> str:
    return _encode(
        settings,
        user_id,
        TokenKind.REFRESH,
        timedelta(days=settings.jwt_refresh_expire_days),
        # jti guarantees uniqueness even if two refresh tokens for the
        # same user are issued in the same second (rotation path).
        extra={"sid": session_id, "jti": secrets.token_urlsafe(8)},
    )


def issue_guest_token(settings: Settings) -> str:
    return _encode(
        settings, "guest", TokenKind.GUEST, timedelta(minutes=settings.jwt_guest_expire_minutes)
    )


def decode_access(settings: Settings, token: str) -> dict:
    return _decode(settings, token, expected_kind=TokenKind.ACCESS)


def decode_refresh(settings: Settings, token: str) -> dict:
    return _decode(settings, token, expected_kind=TokenKind.REFRESH)


# ── User store ────────────────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    return await db.get(User, user_id)


async def create_user(
    db: AsyncSession, *, email: str, password: str, name: str = ""
) -> User:
    existing = await get_user_by_email(db, email)
    if existing:
        raise BadRequestError("Email already registered")
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        name=name or email.split("@")[0],
        provider="email",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(
    db: AsyncSession, *, email: str, password: str
) -> User:
    user = await get_user_by_email(db, email)
    if not user or not user.password_hash or not user.is_active:
        raise AuthError("Invalid email or password")
    if not verify_password(password, user.password_hash):
        raise AuthError("Invalid email or password")
    user.last_login_at = _now()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def upsert_google_user(
    db: AsyncSession, *, email: str, name: str = "", verified: bool = True
) -> User:
    user = await get_user_by_email(db, email)
    if user is None:
        user = User(
            email=email.lower(),
            password_hash=None,
            name=name or email.split("@")[0],
            provider="google",
        )
        db.add(user)
    elif user.provider == "email" and user.password_hash is None:
        # Promote empty local account to Google-linked (password remains unset).
        user.provider = "google"
    if name and not user.name:
        user.name = name
    user.last_login_at = _now()
    await db.commit()
    await db.refresh(user)
    return user


# ── Refresh-token sessions ────────────────────────────────────────

async def create_user_session(
    db: AsyncSession,
    user: User,
    *,
    refresh_hash: str,
    user_agent: str = "",
    ip: str = "",
    settings: Settings,
) -> UserSession:
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=refresh_hash,
        user_agent=user_agent[:256],
        ip=ip[:64],
        expires_at=_now() + timedelta(days=settings.jwt_refresh_expire_days),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def find_session_by_refresh_hash(
    db: AsyncSession, refresh_hash: str
) -> UserSession | None:
    result = await db.execute(
        select(UserSession).where(
            UserSession.refresh_token_hash == refresh_hash,
            UserSession.revoked_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_user_for_session(db: AsyncSession, session: UserSession) -> User:
    """Load the user attached to a session (avoid lazy-load surprises)."""
    user = await db.get(User, session.user_id)
    if not user:
        raise AuthError("Session points to a missing user", code="user_missing")
    return user


async def revoke_session(db: AsyncSession, session: UserSession) -> None:
    session.revoked_at = _now()
    await db.commit()


# ── Google OAuth (code → tokens → id_token) ──────────────────────

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_OPENID_CFG = "https://accounts.google.com/.well-known/openid-configuration"
_JWKS_CACHE: dict[str, Any] = {}


async def exchange_google_code(
    settings: Settings, code: str
) -> dict[str, Any]:
    """Trade a one-time authorization code for tokens."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise AuthError(
            "Google OAuth is not configured (set GOOGLE_CLIENT_ID/SECRET)",
            code="google_not_configured",
        )
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def verify_google_id_token(
    settings: Settings, id_token: str
) -> dict[str, Any]:
    """Verify Google id_token signature and return its claims.

    ponytail: Fetches Google's JWKS once per process. Refresh on key
    rotation error belongs in V9 production hardening.
    """
    if not _JWKS_CACHE:
        async with httpx.AsyncClient(timeout=30.0) as client:
            cfg = (await client.get(GOOGLE_OPENID_CFG)).json()
            jwks = (await client.get(cfg["jwks_uri"])).json()
            _JWKS_CACHE["jwks"] = jwks

    unverified_header = jwt.get_unverified_header(id_token)
    kid = unverified_header.get("kid")
    keys = _JWKS_CACHE["jwks"].get("keys", [])
    key = next((k for k in keys if k.get("kid") == kid), None)
    if not key:
        raise AuthError("Google signing key not found", code="google_key_not_found")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
    try:
        claims = jwt.decode(
            id_token,
            public_key,
            algorithms=[key.get("alg", "RS256")],
            audience=settings.google_client_id,
        )
    except jwt.ExpiredSignatureError as e:
        raise AuthError("Google id_token expired", code="google_token_expired") from e
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Invalid Google id_token: {e}", code="google_invalid_token") from e

    if settings.google_require_verified_email and not claims.get("email_verified"):
        raise AuthError("Google email not verified", code="google_email_unverified")
    return claims
