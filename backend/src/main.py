import enum
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import gpxpy
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .utils.config import (
    load_environment_config,
)
from .utils.gpx import (
    GPXData,
    extract_from_gpx_file,
    generate_gpx_segment,
)
from .utils.postgres import get_database_url
from .utils.storage import (
    LocalStorageManager,
    StorageManager,
    cleanup_local_file,
    get_storage_manager,
)

db_config, storage_config = load_environment_config()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

temp_dir: TemporaryDirectory | None = None
storage_manager: StorageManager | None = None
DATABASE_URL = get_database_url(
    host=db_config.host,
    port=db_config.port,
    database=db_config.name,
    username=db_config.user,
    password=db_config.password,
)
engine = None
SessionLocal = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown."""
    global temp_dir, storage_manager, engine, SessionLocal

    temp_dir = TemporaryDirectory(prefix="cycling_gpx_")
    logger.info(f"Created temporary directory: {temp_dir.name}")

    try:
        engine = create_async_engine(DATABASE_URL, echo=False, future=True)
        SessionLocal = async_sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        logger.info("Database engine and session initialized")
    except Exception as db_init_e:
        logger.warning(f"Failed to initialize database engine: {db_init_e}")
        engine = None
        SessionLocal = None

    try:
        storage_manager = get_storage_manager(storage_config)
        logger.info(
            f"Storage manager initialized successfully "
            f"(type: {storage_config.storage_type})"
        )
    except Exception as e:
        logger.warning(f"Failed to initialize storage manager: {str(e)}")
        storage_manager = None

    if engine is not None:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables ensured")
        except Exception as db_e:
            logger.warning(f"Could not initialize database: {db_e}")
    else:
        logger.warning("Skipping database initialization - engine not available")

    yield

    if temp_dir:
        logger.info(f"Cleaning up temporary directory: {temp_dir.name}")
        temp_dir.cleanup()

    if engine:
        logger.info("Closing database engine")
        await engine.dispose()


app = FastAPI(title="Cycling GPX API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Base(DeclarativeBase):
    pass


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    bound_north: Mapped[float] = mapped_column(Float)
    bound_south: Mapped[float] = mapped_column(Float)
    bound_east: Mapped[float] = mapped_column(Float)
    bound_west: Mapped[float] = mapped_column(Float)
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


class TrackCreateResponse(BaseModel):
    id: int
    file_path: Path
    bound_north: float
    bound_south: float
    bound_east: float
    bound_west: float
    name: str
    track_type: str
    difficulty_level: int
    surface_type: str
    tire_dry: str
    tire_wet: str
    comments: str


@app.get("/")
async def root():
    return {"message": "Cycling GPX API"}


@app.get("/storage/{file_path:path}")
async def serve_storage_file(file_path: str):
    """Serve files from local storage for development."""
    global storage_manager

    if not storage_manager:
        raise HTTPException(status_code=500, detail="Storage manager not initialized")

    if not isinstance(storage_manager, LocalStorageManager):
        raise HTTPException(
            status_code=404, detail="File serving only available in local mode"
        )

    if hasattr(storage_manager, "get_file_path"):
        local_file_path = storage_manager.get_file_path(file_path)
    else:
        raise HTTPException(status_code=500, detail="Local storage not available")

    if not local_file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        local_file_path, media_type="application/gpx+xml", filename=local_file_path.name
    )


@app.post("/api/upload-gpx", response_model=GPXData)
async def upload_gpx(file: UploadFile = File(...)):
    """Upload a GPX file from the client to the server in a temporary directory.

    We return a `GPXData` object which contains the GPS points
    (latitude, longitude, elevation, time), the aggregated statistics and the bounds
    of the track.

    Parameters
    ----------
    file: UploadFile
        The GPX file to upload.

    Returns
    -------
    GPXData
        The track information of the uploaded GPX file.
    """
    global temp_dir

    if not file.filename.endswith(".gpx"):
        raise HTTPException(status_code=400, detail="File must be a GPX file")

    if not temp_dir:
        raise HTTPException(
            status_code=500, detail="Temporary directory not initialized"
        )

    file_id = str(uuid.uuid4())
    file_path = Path(temp_dir.name) / f"{file_id}.gpx"
    logger.info(f"Uploading file {file.filename} to temporary directory: {file_path}")

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"Successfully saved file {file.filename} as {file_id}.gpx")
    except Exception as e:
        logger.error(f"Failed to save file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    try:
        with open(file_path) as gpx_file:
            gpx = gpxpy.parse(gpx_file)
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Failed to parse GPX file {file_id}.gpx: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid GPX file: {str(e)}")

    try:
        gpx_data = extract_from_gpx_file(gpx, file_id)
        logger.info(
            f"Successfully parsed GPX file {file_id}.gpx with {len(gpx_data.points)}"
            " points"
        )
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Failed to process GPX file {file_id}.gpx: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid GPX file: {str(e)}")

    return gpx_data


@app.post("/api/segments", response_model=TrackCreateResponse)
async def create_segment(
    name: str = Form(...),
    track_type: str = Form("segment"),
    tire_dry: str = Form(...),
    tire_wet: str = Form(...),
    file_id: str = Form(...),
    start_index: int = Form(...),
    end_index: int = Form(...),
    surface_type: str = Form(...),
    difficulty_level: int = Form(...),
    commentary_text: str = Form(""),
    video_links: str = Form("[]"),
):
    """Create a new segment: process uploaded GPX file with indices, upload to storage,
    and store metadata in DB.
    """
    allowed_tire_types = {"slick", "semi-slick", "knobs"}
    if tire_dry not in allowed_tire_types or tire_wet not in allowed_tire_types:
        raise HTTPException(status_code=422, detail="Invalid tire types")

    allowed_track_types = {"segment", "route"}
    if track_type not in allowed_track_types:
        raise HTTPException(status_code=422, detail="Invalid track type")

    global temp_dir, storage_manager

    if not temp_dir:
        raise HTTPException(
            status_code=500, detail="Temporary directory not initialized"
        )

    if not storage_manager:
        raise HTTPException(status_code=500, detail="Storage manager not initialized")

    original_file_path = Path(temp_dir.name) / f"{file_id}.gpx"
    logger.info(f"Processing segment from file {file_id}.gpx at: {original_file_path}")

    if not original_file_path.exists():
        logger.warning(f"Uploaded file not found: {original_file_path}")
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    frontend_temp_dir = Path(temp_dir.name) / "gpx_segments"
    frontend_temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(
            f"Processing segment '{name}' from indices {start_index} to {end_index}"
        )
        segment_file_id, segment_file_path, bounds = generate_gpx_segment(
            input_file_path=original_file_path,
            start_index=start_index,
            end_index=end_index,
            segment_name=name,
            output_dir=frontend_temp_dir,
        )
        logger.info(f"Successfully created segment file: {segment_file_path}")

        try:
            storage_key = storage_manager.upload_gpx_segment(
                local_file_path=segment_file_path,
                file_id=segment_file_id,
                prefix="gpx-segments",
            )
            logger.info(f"Successfully uploaded segment to storage: {storage_key}")

            cleanup_success = cleanup_local_file(segment_file_path)
            if cleanup_success:
                logger.info(f"Successfully cleaned up local file: {segment_file_path}")
            else:
                logger.warning(f"Failed to clean up local file: {segment_file_path}")

            processed_file_path = (
                f"{storage_manager.get_storage_root_prefix()}/{storage_key}"
            )

        except Exception as storage_error:
            logger.error(f"Failed to upload to storage: {str(storage_error)}")
            cleanup_local_file(segment_file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload to storage: {str(storage_error)}",
            )

    except Exception as e:
        logger.error(f"Failed to process GPX file for segment '{name}': {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process GPX file: {str(e)}"
        )

    # Store metadata in DB (using the processed file path)
    if SessionLocal is not None:
        try:
            async with SessionLocal() as session:
                track = Track(
                    file_path=processed_file_path,
                    bound_north=bounds.north,
                    bound_south=bounds.south,
                    bound_east=bounds.east,
                    bound_west=bounds.west,
                    name=name,
                    track_type=TrackType(track_type),
                    difficulty_level=difficulty_level,
                    surface_type=SurfaceType(surface_type),
                    tire_dry=TireType(tire_dry),
                    tire_wet=TireType(tire_wet),
                    comments=commentary_text,
                )
                session.add(track)
                await session.commit()
                await session.refresh(track)
                return TrackCreateResponse(
                    id=track.id,
                    file_path=processed_file_path,
                    bound_north=track.bound_north,
                    bound_south=track.bound_south,
                    bound_east=track.bound_east,
                    bound_west=track.bound_west,
                    name=track.name,
                    track_type=track.track_type,
                    difficulty_level=int(track.difficulty_level),
                    surface_type=track.surface_type,
                    tire_dry=track.tire_dry,
                    tire_wet=track.tire_wet,
                    comments=track.comments,
                )
        except Exception as db_e:
            logger.warning(f"Failed to store segment in database: {db_e}")
            # Continue without database storage

        # Return response without database ID if database is not available
        return TrackCreateResponse(
            id=0,  # Placeholder ID when database is not available
            file_path=processed_file_path,
            bound_north=bounds.north,
            bound_south=bounds.south,
            bound_east=bounds.east,
            bound_west=bounds.west,
            name=name,
            track_type=track_type,
            difficulty_level=difficulty_level,
            surface_type=surface_type,
            tire_dry=tire_dry,
            tire_wet=tire_wet,
            comments=commentary_text,
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
