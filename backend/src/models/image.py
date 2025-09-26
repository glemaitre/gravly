from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TrackImage(Base):
    """Model for track images with one-to-many relationship to tracks."""

    __tablename__ = "track_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )
    image_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(UTC), nullable=False
    )

    # Relationship to Track
    track = relationship("Track", back_populates="images")


class TrackImageResponse(BaseModel):
    """Response model for track images."""

    id: int
    track_id: int
    image_id: str
    image_url: str
    storage_key: str
    filename: str | None = None
    original_filename: str | None = None
    created_at: datetime


class TrackImageCreateRequest(BaseModel):
    """Request model for creating track images."""

    track_id: int
    image_url: str
    storage_key: str
    filename: str | None = None
    original_filename: str | None = None
