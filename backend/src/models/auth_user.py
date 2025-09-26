"""Database model for authorized Strava users."""

from datetime import UTC, datetime

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AuthUser(Base):
    """Database model for users authorized to access editor feature."""

    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strava_id: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False, index=True
    )
    firstname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lastname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class AuthUserResponse(PydanticBaseModel):
    """Response model for authorized user data."""

    id: int
    strava_id: int
    firstname: str | None = None
    lastname: str | None = None
    created_at: datetime
    updated_at: datetime


class AuthUserSummary(PydanticBaseModel):
    """Summary of authorized user (without IDs)."""

    strava_id: int
    firstname: str | None = None
    lastname: str | None = None
