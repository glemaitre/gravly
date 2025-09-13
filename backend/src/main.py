import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
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

from .utils.gpx import (
    GPXData,
    GPXProcessingError,
    extract_from_gpx_file,
    process_gpx_for_segment_creation,
)

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


# Pydantic models - using GPXData directly from gpx.py


class SegmentCreateResponse(BaseModel):
    id: int
    name: str
    tire_dry: str
    tire_wet: str
    file_path: str


@app.get("/")
async def root():
    return {"message": "Cycling GPX API"}


@app.post("/api/upload-gpx", response_model=GPXData)
async def upload_gpx(file: UploadFile = File(...)):
    """Upload a GPX file temporarily and return track information"""
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

    with open(file_path) as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    try:
        gpx_data = extract_from_gpx_file(gpx, file_id)
        logger.info(
            f"Successfully parsed GPX file {file_id}.gpx with {len(gpx_data.points)}"
            " points"
        )
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Failed to parse GPX file {file_id}.gpx: {str(e)}")
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
    """Create a new segment: process uploaded GPX file with indices, store
    locally and metadata in DB.

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

    original_file_path = Path(temp_dir.name) / f"{file_id}.gpx"
    logger.info(f"Processing segment from file {file_id}.gpx at: {original_file_path}")

    if not original_file_path.exists():
        logger.warning(f"Uploaded file not found: {original_file_path}")
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    # Ensure destination directory exists
    dest_dir = Path("mock_gpx")
    dest_dir.mkdir(exist_ok=True)

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
        original_file_path.unlink()
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
