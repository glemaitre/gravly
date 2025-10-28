"""Database model for Wahoo OAuth tokens."""

from datetime import UTC, datetime

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WahooToken(Base):
    """Database model for Wahoo OAuth tokens per user."""

    __tablename__ = "wahoo_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wahoo_id: Mapped[int] = mapped_column(
        Integer, name="user_id", unique=True, nullable=False, index=True
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    user_data: Mapped[str | None] = mapped_column(
        Text, name="user_info", nullable=True
    )  # JSON string of user data
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class WahooTokenResponse(PydanticBaseModel):
    """Response model for Wahoo token data."""

    id: int
    wahoo_id: int
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class WahooTokenCreate(PydanticBaseModel):
    """Request model for creating Wahoo tokens."""

    wahoo_id: int
    access_token: str
    refresh_token: str
    expires_at: datetime
    user_data: str | None = None


class WahooTokenUpdate(PydanticBaseModel):
    """Request model for updating Wahoo tokens."""

    access_token: str
    refresh_token: str
    expires_at: datetime
    user_data: str | None = None
