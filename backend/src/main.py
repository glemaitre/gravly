import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import gpxpy
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .utils.gpx import (
    GPXData,
    extract_from_gpx_file,
    generate_gpx_segment,
)
from .utils.storage import (
    LocalStorageManager,
    StorageManager,
    cleanup_local_file,
    get_storage_manager,
)

env_file = (
    Path(__file__).parent.parent.parent
    / ".env"
    / f"{os.getenv('ENVIRONMENT', 'local')}"
)
if env_file.exists():
    load_dotenv(env_file)
    logging.info(f"Loaded environment variables from {env_file}")
else:  # fallback to .env file in root
    fallback_env = Path(__file__).parent.parent.parent / ".env"
    if fallback_env.exists():
        load_dotenv(fallback_env)
        logging.info(f"Loaded environment variables from {fallback_env}")
    else:
        logging.info("No .env file found, using system environment variables")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

temp_dir: TemporaryDirectory | None = None
storage_manager: StorageManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown."""
    global temp_dir, storage_manager

    temp_dir = TemporaryDirectory(prefix="cycling_gpx_")
    logger.info(f"Created temporary directory: {temp_dir.name}")

    try:
        storage_type = os.getenv("STORAGE_TYPE", "local").lower()

        if storage_type == "s3":
            config = {
                "bucket_name": os.getenv("AWS_S3_BUCKET"),
                "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            }
            # Filter out None values for S3
            config = {k: v for k, v in config.items() if v is not None}
        else:
            config = {
                "storage_root": os.getenv("LOCAL_STORAGE_ROOT"),
                "base_url": os.getenv("LOCAL_STORAGE_BASE_URL"),
            }
            # Filter out None values for local storage
            config = {k: v for k, v in config.items() if v is not None}

        storage_manager = get_storage_manager(storage_type, config)
        logger.info(f"Storage manager initialized successfully (type: {storage_type})")
    except Exception as e:
        logger.warning(f"Failed to initialize storage manager: {str(e)}")
        storage_manager = None

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


class SegmentCreateResponse(BaseModel):
    id: int
    name: str
    tire_dry: str
    tire_wet: str
    file_path: Path


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
    """Create a new segment: process uploaded GPX file with indices, upload to storage,
    and store metadata in DB.
    """
    allowed = {"slick", "semi-slick", "knobs"}
    if tire_dry not in allowed or tire_wet not in allowed:
        raise HTTPException(status_code=422, detail="Invalid tire types")

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
        segment_file_id, segment_file_path = generate_gpx_segment(
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

    # Store metadata in DB (using the S3 path)
    # TODO: Uncomment when database is needed
    # async with SessionLocal() as session:
    #     seg = Segment(
    #         name=name, tire_dry=tire_dry, tire_wet=tire_wet, file_path=processed_file_path
    #     )
    #     session.add(seg)
    #     await session.commit()
    #     await session.refresh(seg)
    #     return SegmentCreateResponse(
    #         id=seg.id,
    #         name=seg.name,
    #         tire_dry=seg.tire_dry,
    #         tire_wet=seg.tire_wet,
    #         file_path=seg.file_path,
    #     )

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
