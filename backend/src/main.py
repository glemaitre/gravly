import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from tempfile import TemporaryDirectory

import gpxpy
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .gpx_editor import GPXProcessingError, process_gpx_for_segment_creation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global temporary directory for the session
temp_dir: TemporaryDirectory | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown."""
    global temp_dir

    # Create temporary directory for the session
    temp_dir = TemporaryDirectory(prefix="cycling_gpx_")
    logger.info(f"Created temporary directory: {temp_dir.name}")

    # Initialize database (create tables if not exist)
    # TODO: Uncomment when database is needed
    # try:
    #     async with engine.begin() as conn:
    #         await conn.run_sync(Base.metadata.create_all)
    #     print("Database tables ensured")
    # except Exception as db_e:
    #     print(f"Warning: Could not initialize database: {db_e}")

    # Yield control to the application
    yield

    # Clean up temporary directory on shutdown
    if temp_dir:
        logger.info(f"Cleaning up temporary directory: {temp_dir.name}")
        temp_dir.cleanup()


app = FastAPI(title="Cycling GPX API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup (PostgreSQL via SQLAlchemy async)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # Fallback to local development URL. Example: postgresql+asyncpg://user:pass@localhost/db
    "postgresql+asyncpg://postgres:postgres@localhost:5432/cycling",
)


class Base(DeclarativeBase):
    pass


class TireType(str):
    SLICK = "slick"
    SEMI_SLICK = "semi-slick"
    KNOBS = "knobs"


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tire_dry: Mapped[str] = mapped_column(
        SAEnum(TireType.SLICK, TireType.SEMI_SLICK, TireType.KNOBS, name="tire_type"),
        nullable=False,
    )
    tire_wet: Mapped[str] = mapped_column(
        SAEnum(TireType.SLICK, TireType.SEMI_SLICK, TireType.KNOBS, name="tire_type"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


engine = create_async_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Pydantic models
class GPXPoint(BaseModel):
    lat: float
    lon: float
    elevation: float
    time: str | None = None


class GPXUploadResponse(BaseModel):
    file_id: str
    track_name: str
    total_points: int
    bounds: dict
    elevation_stats: dict | None = None


class SegmentCreateResponse(BaseModel):
    id: int
    name: str
    tire_dry: str
    tire_wet: str
    file_path: str


@app.get("/")
async def root():
    return {"message": "Cycling GPX API"}


def parse_gpx_file(file_path: str) -> dict:
    """Parse a GPX file and extract track information"""
    with open(file_path) as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    if not gpx.tracks:
        raise ValueError("No tracks found in GPX file")

    track = gpx.tracks[0]
    points = []
    total_distance = 0
    total_elevation_gain = 0
    total_elevation_loss = 0
    prev_elevation = None

    lats = []
    lons = []
    elevations = []

    for segment in track.segments:
        for point in segment.points:
            if point.latitude and point.longitude:
                lats.append(point.latitude)
                lons.append(point.longitude)

                elevation = point.elevation or 0
                elevations.append(elevation)
                points.append(
                    GPXPoint(
                        lat=point.latitude,
                        lon=point.longitude,
                        elevation=elevation,
                        time=point.time.isoformat() if point.time else None,
                    )
                )

                if prev_elevation is not None:
                    elevation_diff = elevation - prev_elevation
                    if elevation_diff > 0:
                        total_elevation_gain += elevation_diff
                    else:
                        total_elevation_loss += abs(elevation_diff)

                prev_elevation = elevation

    # Calculate total distance
    for i in range(1, len(points)):
        p1 = points[i - 1]
        p2 = points[i]
        # Simple distance calculation (for more accuracy, use geopy)
        import math

        lat1, lon1 = math.radians(p1.lat), math.radians(p1.lon)
        lat2, lon2 = math.radians(p2.lat), math.radians(p2.lon)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        distance = 6371 * c  # Earth radius in km
        total_distance += distance

    bounds = {
        "north": max(lats),
        "south": min(lats),
        "east": max(lons),
        "west": min(lons),
    }

    elevation_stats = None
    if elevations:
        elevation_stats = {
            "min": min(elevations),
            "max": max(elevations),
            "total_points": len(elevations),
        }

    return {
        "name": track.name or "Unnamed Track",
        "points": points,
        "total_distance": total_distance,
        "total_elevation_gain": total_elevation_gain,
        "total_elevation_loss": total_elevation_loss,
        "bounds": bounds,
        "elevation_stats": elevation_stats,
    }


@app.post("/api/upload-gpx", response_model=GPXUploadResponse)
async def upload_gpx(file: UploadFile = File(...)):
    """Upload a GPX file temporarily and return track information"""
    global temp_dir

    if not file.filename.endswith(".gpx"):
        raise HTTPException(status_code=400, detail="File must be a GPX file")

    if not temp_dir:
        raise HTTPException(
            status_code=500, detail="Temporary directory not initialized"
        )

    # Generate unique file ID
    file_id = str(uuid.uuid4())

    # Save uploaded file in the session temporary directory
    file_path = os.path.join(temp_dir.name, f"{file_id}.gpx")
    logger.info(f"Uploading file {file.filename} to temporary directory: {file_path}")

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"Successfully saved file {file.filename} as {file_id}.gpx")
    except Exception as e:
        logger.error(f"Failed to save file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Parse GPX file
    try:
        gpx_data = parse_gpx_file(file_path)
        logger.info(
            f"Successfully parsed GPX file {file_id}.gpx with {len(gpx_data['points'])} points"
        )
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Failed to parse GPX file {file_id}.gpx: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid GPX file: {str(e)}")

    return GPXUploadResponse(
        file_id=file_id,
        track_name=gpx_data["name"],
        total_points=len(gpx_data["points"]),
        bounds=gpx_data["bounds"],
        elevation_stats=gpx_data["elevation_stats"],
    )


@app.get("/api/gpx-points/{file_id}")
async def get_gpx_points(file_id: str):
    """Get the actual track points from an uploaded GPX file"""
    global temp_dir

    if not temp_dir:
        raise HTTPException(
            status_code=500, detail="Temporary directory not initialized"
        )

    file_path = os.path.join(temp_dir.name, f"{file_id}.gpx")
    logger.info(f"Fetching points for file {file_id}.gpx from: {file_path}")

    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")

    try:
        gpx_data = parse_gpx_file(file_path)
        logger.info(
            f"Successfully retrieved {len(gpx_data['points'])} points for file {file_id}.gpx"
        )
        return {"points": gpx_data["points"]}
    except Exception as e:
        logger.error(f"Failed to parse GPX file {file_id}.gpx: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to parse GPX file: {str(e)}"
        )


@app.post("/api/segments", response_model=SegmentCreateResponse)
async def create_segment(
    name: str = Form(...),
    tire_dry: str = Form(...),
    tire_wet: str = Form(...),
    file_id: str = Form(...),
    start_index: int = Form(...),
    end_index: int = Form(...),
    surface_type: str = Form(None),
    difficulty_level: int = Form(None),
    commentary_text: str = Form(""),
    video_links: str = Form("[]"),
):
    """Create a new segment: process uploaded GPX file with indices, store locally and metadata in DB.

    Note: Files are saved under `mock_gpx/` for now; later this should target S3.
    """
    allowed = {"slick", "semi-slick", "knobs"}
    if tire_dry not in allowed or tire_wet not in allowed:
        raise HTTPException(status_code=422, detail="Invalid tire types")

    # Find the uploaded file
    global temp_dir

    if not temp_dir:
        raise HTTPException(
            status_code=500, detail="Temporary directory not initialized"
        )

    original_file_path = os.path.join(temp_dir.name, f"{file_id}.gpx")
    logger.info(f"Processing segment from file {file_id}.gpx at: {original_file_path}")

    if not os.path.exists(original_file_path):
        logger.warning(f"Uploaded file not found: {original_file_path}")
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    # Ensure destination directory exists
    dest_dir = "mock_gpx"
    os.makedirs(dest_dir, exist_ok=True)

    # Process the GPX file with the given indices
    try:
        logger.info(
            f"Processing segment '{name}' from indices {start_index} to {end_index}"
        )
        processing_result = process_gpx_for_segment_creation(
            input_file_path=original_file_path,
            start_index=start_index,
            end_index=end_index,
            segment_name=name,
            output_dir=dest_dir,
        )
        processed_file_path = processing_result["processed_file"]
        logger.info(f"Successfully created segment file: {processed_file_path}")

    except GPXProcessingError as gpx_e:
        logger.error(f"GPX processing failed for segment '{name}': {str(gpx_e)}")
        raise HTTPException(
            status_code=422, detail=f"GPX processing failed: {str(gpx_e)}"
        )
    except Exception as e:
        logger.error(f"Failed to process GPX file for segment '{name}': {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process GPX file: {str(e)}"
        )

    # Store metadata in DB (using the processed file path)
    # TODO: Uncomment when database is needed
    # async with SessionLocal() as session:
    #     seg = Segment(
    #         name=name, tire_dry=tire_dry, tire_wet=tire_wet, file_path=processed_file_path
    #     )
    #     session.add(seg)
    #     await session.commit()
    #     await session.refresh(seg)

    # Clean up temporary file
    try:
        os.remove(original_file_path)
    except Exception:
        pass  # Don't fail if cleanup fails

    # For now, return a mock response since we're not using the database
    return SegmentCreateResponse(
        id=1,  # Mock ID
        name=name,
        tire_dry=tire_dry,
        tire_wet=tire_wet,
        file_path=processed_file_path,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
