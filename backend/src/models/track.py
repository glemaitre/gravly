import enum
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, Enum, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TrackType(enum.Enum):
    SEGMENT = "segment"
    ROUTE = "route"


class SurfaceType(enum.Enum):
    BIG_STONE_ROAD = "big-stone-road"
    BROKEN_PAVED_ROAD = "broken-paved-road"
    DIRTY_ROAD = "dirty-road"
    FIELD_TRAIL = "field-trail"
    FOREST_TRAIL = "forest-trail"
    SMALL_STONE_ROAD = "small-stone-road"


class TireType(enum.Enum):
    SLICK = "slick"
    SEMI_SLICK = "semi-slick"
    KNOBS = "knobs"


class Track(Base):
    __tablename__ = "tracks"
    __table_args__ = (
        Index(
            "idx_track_bounds_intersection",
            "bound_north",
            "bound_south",
            "bound_east",
            "bound_west",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    bound_north: Mapped[float] = mapped_column(Float)
    bound_south: Mapped[float] = mapped_column(Float)
    bound_east: Mapped[float] = mapped_column(Float)
    bound_west: Mapped[float] = mapped_column(Float)
    barycenter_latitude: Mapped[float] = mapped_column(Float)
    barycenter_longitude: Mapped[float] = mapped_column(Float)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    track_type: Mapped[TrackType] = mapped_column(Enum(TrackType))
    difficulty_level: Mapped[int] = mapped_column(Integer)
    surface_type: Mapped[SurfaceType] = mapped_column(Enum(SurfaceType))
    tire_dry: Mapped[TireType] = mapped_column(Enum(TireType))
    tire_wet: Mapped[TireType] = mapped_column(Enum(TireType))
    comments: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(UTC), nullable=False
    )

    # Relationship to images
    images = relationship(
        "TrackImage", back_populates="track", cascade="all, delete-orphan"
    )


class TrackResponse(BaseModel):
    id: int
    file_path: str
    bound_north: float
    bound_south: float
    bound_east: float
    bound_west: float
    barycenter_latitude: float
    barycenter_longitude: float
    name: str
    track_type: str
    difficulty_level: int
    surface_type: str
    tire_dry: str
    tire_wet: str
    comments: str


class TrackWithGPXDataResponse(TrackResponse):
    gpx_xml_data: str | None = None


class GPXDataResponse(BaseModel):
    gpx_xml_data: str
