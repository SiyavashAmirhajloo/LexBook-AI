"""Auth models (V9).

User accounts + per-device refresh-token sessions. Backwards compatible
with the guest mode: every anonymous session is still addressable as
`user_id` in the future, but in V9 we only persist users for
email/password and Google login. Guest sessions are JWT-only.
"""
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.documents import Base


class User(Base):
    """A registered user (email/password or Google OAuth)."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    # Nullable: Google sign-in users have no local password.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Display name from Google, or first part of email.
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    # 'email' | 'google' | 'guest' — useful for analytics + future migrations.
    provider: Mapped[str] = mapped_column(String(16), nullable=False, default="email")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(Base):
    """A refresh-token session. Revocable."""

    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Opaque token; not the JWT itself (server-side store lets us revoke).
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_agent: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    ip: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="sessions")
