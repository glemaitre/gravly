import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import gpxpy
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models.base import Base
from .models.track import (
    SurfaceType,
    TireType,
    Track,
    TrackResponse,
    TrackType,
    TrackWithGPXDataResponse,
)
from .utils.config import load_environment_config
from .utils.gpx import GPXData, extract_from_gpx_file, generate_gpx_segment
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
    expose_headers=["*"],
)


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


@app.post("/api/segments", response_model=TrackResponse)
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
                    file_path=str(processed_file_path),
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
                return TrackResponse(
                    id=track.id,
                    file_path=str(processed_file_path),
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
    return TrackResponse(
        id=0,  # Placeholder ID when database is not available
        file_path=str(processed_file_path),
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


@app.options("/api/segments/search")
async def search_segments_options():
    """Handle preflight requests for the search endpoint."""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        },
    )


@app.get("/api/segments/search")
async def search_segments_in_bounds(
    north: float, south: float, east: float, west: float
):
    """Search for segments that intersect with the given map bounds using streaming.

    This uses simple bounding box intersection - a segment is included if its bounding
    rectangle overlaps with the search area rectangle. Streams segments as they are
    processed, allowing the frontend to start drawing immediately.

    Parameters
    ----------
    north : float
        Northern boundary of the search area
    south : float
        Southern boundary of the search area
    east : float
        Eastern boundary of the search area
    west : float
        Western boundary of the search area
    """
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")

    async def generate():
        try:
            async with SessionLocal() as session:
                stmt = (
                    select(Track)
                    .filter(
                        and_(
                            Track.bound_north >= south,
                            Track.bound_south <= north,
                            Track.bound_east >= west,
                            Track.bound_west <= east,
                        )
                    )
                    .order_by(Track.created_at.desc())
                )

                result = await session.execute(stmt)
                tracks = result.scalars().all()

                yield f"data: {len(tracks)}\n\n"

                for track in tracks:
                    if storage_manager:
                        try:
                            gpx_bytes = storage_manager.load_gpx_data(track.file_path)
                            gpx_xml_data = gpx_bytes.decode("utf-8")
                        except Exception as e:
                            logger.warning(
                                f"Failed to load GPX data for track {track.id}: "
                                f"{str(e)}"
                            )

                    track_response = TrackWithGPXDataResponse(
                        id=track.id,
                        file_path=track.file_path,
                        name=track.name,
                        bound_north=track.bound_north,
                        bound_south=track.bound_south,
                        bound_east=track.bound_east,
                        bound_west=track.bound_west,
                        surface_type=track.surface_type.value,
                        difficulty_level=track.difficulty_level,
                        track_type=track.track_type.value,
                        tire_dry=track.tire_dry.value,
                        tire_wet=track.tire_wet.value,
                        comments=track.comments or "",
                        gpx_xml_data=gpx_xml_data,
                    )

                    track_json = json.dumps(track_response.model_dump())
                    yield f"data: {track_json}\n\n"

                yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in streaming endpoint: {str(e)}")
            yield f"data: {{'error': '{str(e)}'}}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Expose-Headers": "*",
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
