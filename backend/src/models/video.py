from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TrackVideo(Base):
    """Model for track videos with one-to-many relationship to tracks."""

    __tablename__ = "track_videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False
    )
    video_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    video_url: Mapped[str] = mapped_column(Text, nullable=False)
    video_title: Mapped[str] = mapped_column(String(500), nullable=True)
    # Platform: youtube, vimeo, other
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(UTC), nullable=False
    )

    # Relationship to Track
    track = relationship("Track", back_populates="videos")


class TrackVideoResponse(BaseModel):
    """Response model for track videos."""

    id: int
    track_id: int
    video_id: str
    video_url: str
    video_title: str | None = None
    platform: str
    created_at: datetime


class TrackVideoCreateRequest(BaseModel):
    """Request model for creating track videos."""

    track_id: int
    video_url: str
    video_title: str | None = None
    platform: str
