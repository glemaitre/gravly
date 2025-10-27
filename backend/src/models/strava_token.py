"""Database model for Strava OAuth tokens."""

from datetime import UTC, datetime

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StravaToken(Base):
    """Database model for Strava OAuth tokens per user."""

    __tablename__ = "strava_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strava_id: Mapped[int] = mapped_column(
        Integer, name="user_id", unique=True, nullable=False, index=True
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    athlete_data: Mapped[str | None] = mapped_column(
        Text, name="athlete_info", nullable=True
    )  # JSON string of athlete data
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class StravaTokenResponse(PydanticBaseModel):
    """Response model for Strava token data."""

    id: int
    strava_id: int
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class StravaTokenCreate(PydanticBaseModel):
    """Request model for creating Strava tokens."""

    strava_id: int
    access_token: str
    refresh_token: str
    expires_at: datetime
    athlete_data: str | None = None


class StravaTokenUpdate(PydanticBaseModel):
    """Request model for updating Strava tokens."""

    access_token: str
    refresh_token: str
    expires_at: datetime
    athlete_data: str | None = None
