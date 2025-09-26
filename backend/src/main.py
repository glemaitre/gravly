import io
import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import gpxpy
import httpx
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from PIL import Image
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from werkzeug.utils import secure_filename

from .models.auth_user import AuthUser, AuthUserResponse, AuthUserSummary
from .models.base import Base
from .models.image import TrackImage
from .models.track import (
    GPXDataResponse,
    SurfaceType,
    TireType,
    Track,
    TrackResponse,
    TrackType,
)
from .services.strava import StravaService
from .utils.config import load_environment_config
from .utils.gpx import GPXData, extract_from_gpx_file, generate_gpx_segment
from .utils.postgres import get_database_url
from .utils.storage import (
    LocalStorageManager,
    StorageManager,
    cleanup_local_file,
    get_storage_manager,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logger.info("Backend logging configured")

db_config, storage_config, strava_config, map_config = load_environment_config()

temp_dir: TemporaryDirectory | None = None
storage_manager: StorageManager | None = None
strava = StravaService(strava_config)
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
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Cycling GPX API"}


@app.get("/api/map-tiles/{z}/{x}/{y}.png")
async def get_map_tiles(z: int, x: int, y: int):
    """Proxy endpoint for Thunderforest map tiles to hide API key from frontend.

    This endpoint fetches map tiles from Thunderforest API using the server-side
    API key and returns them to the frontend, keeping the API key secure.

    Parameters
    ----------
    z : int
        Zoom level
    x : int
        Tile X coordinate
    y : int
        Tile Y coordinate

    Returns
    -------
    Response
        PNG image data of the map tile
    """
    try:
        # Construct the Thunderforest API URL with our server-side API key
        tile_url = f"https://{{s}}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey={map_config.thunderforest_api_key}"

        # Use a random subdomain (s) for load balancing
        import random

        subdomain = random.choice(["a", "b", "c"])
        tile_url = tile_url.replace("{s}", subdomain)

        # Fetch the tile from Thunderforest
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(tile_url)
            response.raise_for_status()

            # Return the tile image with appropriate headers
            return Response(
                content=response.content,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                    "Access-Control-Allow-Origin": "*",
                },
            )

    except httpx.HTTPStatusError as e:
        logger.warning(
            f"HTTP error fetching tile {z}/{x}/{y}: {e.response.status_code}"
        )
        raise HTTPException(
            status_code=e.response.status_code, detail="Failed to fetch map tile"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error fetching tile {z}/{x}/{y}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch map tile")
    except Exception as e:
        logger.error(f"Unexpected error fetching tile {z}/{x}/{y}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


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

    # Add the file ID to the GPX data so frontend can use it for segment creation
    gpx_data_dict = gpx_data.model_dump()
    gpx_data_dict["file_id"] = file_id

    return gpx_data_dict


@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file to storage manager and return the URL.

    Enhanced Security Features:
    - PIL-based image validation to verify real image format
    - Secure filename sanitization using werkzeug
    - Content-type and file format verification
    - Support for common image formats: JPEG, PNG, GIF, WebP

    Parameters
    ----------
    file: UploadFile
        The image file to upload.

    Returns
    -------
    dict
        Dictionary containing image_id and image_url.
    """
    global temp_dir, storage_manager

    # Basic content-type validation
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    if not temp_dir:
        raise HTTPException(
            status_code=500, detail="Temporary directory not initialized"
        )

    if not storage_manager:
        raise HTTPException(status_code=500, detail="Storage manager not initialized")

    image_file_id = str(uuid.uuid4())

    # Secure filename sanitization
    sanitized_original_name = (
        secure_filename(file.filename or "") if file.filename else ""
    )
    file_extension = Path(sanitized_original_name).suffix.lower() or ".jpg"
    temp_image_path = Path(temp_dir.name) / f"{image_file_id}{file_extension}"

    try:
        # Read file content for validation
        content = await file.read()

        # PIL-based image validation
        try:
            # Verify the image using PIL
            image_stream = io.BytesIO(content)
            with Image.open(image_stream) as img:
                # Verify it's a real image format
                if img.format not in ["JPEG", "PNG", "GIF", "WEBP"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported image format: {img.format}. "
                        f"Supported: JPEG, PNG, GIF, WebP",
                    )

                # Verify image is not corrupted
                img.verify()

            # Reset the stream for further processing
            image_stream.seek(0)

        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

        # Save file temporarily
        with open(temp_image_path, "wb") as temp_file:
            temp_file.write(content)

        # Upload to storage using the storage manager
        storage_key = storage_manager.upload_image(
            local_file_path=temp_image_path,
            file_id=image_file_id,
            prefix="images-segments",
        )

        # Generate URL for the image
        image_url = storage_manager.get_image_url(storage_key)

        # Clean up temp file
        cleanup_local_file(temp_image_path)

        logger.info(
            f"Successfully uploaded and validated image to storage: {storage_key}"
        )

        return {
            "image_id": image_file_id,
            "image_url": image_url,
            "storage_key": storage_key,
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        cleanup_local_file(temp_image_path)
        raise
    except Exception as e:
        cleanup_local_file(temp_image_path)
        logger.error(f"Failed to upload image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


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
    image_data: str = Form("[]"),
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
                barycenter_latitude = (bounds.north + bounds.south) / 2
                barycenter_longitude = (bounds.east + bounds.west) / 2

                track = Track(
                    file_path=str(processed_file_path),
                    bound_north=bounds.north,
                    bound_south=bounds.south,
                    bound_east=bounds.east,
                    bound_west=bounds.west,
                    barycenter_latitude=barycenter_latitude,
                    barycenter_longitude=barycenter_longitude,
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

                # Process image data and create TrackImage records
                if image_data and image_data != "[]":
                    try:
                        image_info_list = json.loads(image_data)

                        for image_info in image_info_list:
                            if isinstance(image_info, dict) and all(
                                key in image_info
                                for key in ["image_id", "image_url", "storage_key"]
                            ):
                                track_image = TrackImage(
                                    track_id=track.id,
                                    image_id=image_info["image_id"],
                                    image_url=image_info["image_url"],
                                    storage_key=image_info["storage_key"],
                                    filename=image_info.get("filename"),
                                    original_filename=image_info.get(
                                        "original_filename"
                                    ),
                                )
                                session.add(track_image)

                        await session.commit()
                        logger.info(
                            f"Successfully linked {len(image_info_list)} "
                            f"images to track {track.id}"
                        )

                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning(f"Failed to process image data: {str(e)}")
                        # Continue without images

                return TrackResponse(
                    id=track.id,
                    file_path=str(processed_file_path),
                    bound_north=track.bound_north,
                    bound_south=track.bound_south,
                    bound_east=track.bound_east,
                    bound_west=track.bound_west,
                    barycenter_latitude=track.barycenter_latitude,
                    barycenter_longitude=track.barycenter_longitude,
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
    barycenter_latitude = (bounds.north + bounds.south) / 2
    barycenter_longitude = (bounds.east + bounds.west) / 2

    return TrackResponse(
        id=0,  # Placeholder ID when database is not available
        file_path=str(processed_file_path),
        bound_north=bounds.north,
        bound_south=bounds.south,
        bound_east=bounds.east,
        bound_west=bounds.west,
        barycenter_latitude=barycenter_latitude,
        barycenter_longitude=barycenter_longitude,
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
    north: float,
    south: float,
    east: float,
    west: float,
    track_type: str = "segment",
    limit: int = Query(
        50,
        ge=1,
        le=1000,
        description="Maximum number of segments to return (default: 50)",
    ),
):
    """Search for segments that are at least partially visible within the given map
    bounds using streaming.

    This uses simple bounding box intersection - a segment is included if its bounding
    rectangle intersects with the search area rectangle (at least partially visible).
    The results are limited to the specified number of segments, selecting those closest
    to the center of the search bounds. Streams segments as they are processed, allowing
    the frontend to start drawing immediately.

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
    track_type : str
        Type of track to search for ('segment' or 'route')
    limit : int
        Maximum number of segments to return (default: 50, max: 1000)
    """
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")

    # Convert string track_type to enum
    try:
        track_type_enum = TrackType(track_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid track_type: {track_type}. Must be 'segment' or 'route'",
        )

    async def generate():
        try:
            async with SessionLocal() as session:
                search_center_latitude = (north + south) / 2
                search_center_longitude = (east + west) / 2

                # Calculate squared Euclidean distance for better performance on local
                # areas For small distances, this is a good approximation and much
                # faster than Haversine Using squared distance to avoid sqrt()
                # calculation
                distance_expr = (
                    func.pow(Track.barycenter_latitude - search_center_latitude, 2)
                    + func.pow(Track.barycenter_longitude - search_center_longitude, 2)
                ).label("distance")

                stmt = (
                    select(Track, distance_expr)
                    .filter(
                        and_(
                            Track.bound_north > south,
                            Track.bound_south < north,
                            Track.bound_east > west,
                            Track.bound_west < east,
                            Track.track_type == track_type_enum,
                        )
                    )
                    .order_by(distance_expr)
                    .limit(limit)
                )

                result = await session.execute(stmt)
                tracks_with_distance = result.all()
                tracks = [track for track, _ in tracks_with_distance]

                yield f"data: {len(tracks)}\n\n"

                for track in tracks:
                    # Return only overview data without GPX content
                    track_response = TrackResponse(
                        id=track.id,
                        file_path=track.file_path,
                        bound_north=track.bound_north,
                        bound_south=track.bound_south,
                        bound_east=track.bound_east,
                        bound_west=track.bound_west,
                        barycenter_latitude=track.barycenter_latitude,
                        barycenter_longitude=track.barycenter_longitude,
                        name=track.name,
                        track_type=track.track_type.value,
                        difficulty_level=track.difficulty_level,
                        surface_type=track.surface_type.value,
                        tire_dry=track.tire_dry.value,
                        tire_wet=track.tire_wet.value,
                        comments=track.comments or "",
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


@app.get("/api/segments/{track_id}/gpx", response_model=GPXDataResponse)
async def get_track_gpx_data(track_id: int):
    """Get GPX data for a specific track by ID.

    This endpoint fetches the GPX XML data from storage for the given track ID.
    This is called by the frontend only when it needs to render the track on the map.

    Parameters
    ----------
    track_id : int
        The ID of the track to fetch GPX data for

    Returns
    -------
    GPXDataResponse
        The GPX XML content only
    """
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")

    if not storage_manager:
        raise HTTPException(status_code=500, detail="Storage manager not available")

    try:
        async with SessionLocal() as session:
            stmt = select(Track).filter(Track.id == track_id)
            result = await session.execute(stmt)
            track = result.scalar_one_or_none()

            if not track:
                raise HTTPException(status_code=404, detail="Track not found")

            try:
                gpx_bytes = storage_manager.load_gpx_data(track.file_path)
                if gpx_bytes is None:
                    logger.warning(
                        f"No GPX data found for track {track_id} at path: "
                        f"{track.file_path}"
                    )
                    raise HTTPException(status_code=404, detail="GPX data not found")
                gpx_xml_data = gpx_bytes.decode("utf-8")
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(
                    f"Failed to load GPX data for track {track_id}: {str(e)}"
                )
                raise HTTPException(
                    status_code=500, detail=f"Failed to load GPX data: {str(e)}"
                )

            return GPXDataResponse(gpx_xml_data=gpx_xml_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching GPX data for track {track_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/segments/{track_id}", response_model=TrackResponse)
async def get_track_info(track_id: int):
    """Get basic track information by ID.

    Parameters
    ----------
    track_id : int
        The ID of the track to fetch info for

    Returns
    -------
    TrackResponse
        Basic track information
    """
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        async with SessionLocal() as session:
            stmt = select(Track).filter(Track.id == track_id)
            result = await session.execute(stmt)
            track = result.scalar_one_or_none()

            if not track:
                raise HTTPException(status_code=404, detail="Track not found")

            return TrackResponse(
                id=track.id,
                file_path=track.file_path,
                bound_north=track.bound_north,
                bound_south=track.bound_south,
                bound_east=track.bound_east,
                bound_west=track.bound_west,
                barycenter_latitude=track.barycenter_latitude,
                barycenter_longitude=track.barycenter_longitude,
                name=track.name,
                track_type=track.track_type,
                difficulty_level=track.difficulty_level,
                surface_type=track.surface_type,
                tire_dry=track.tire_dry,
                tire_wet=track.tire_wet,
                comments=track.comments,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching track info for track {track_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/segments/{track_id}/data", response_model=GPXData)
async def get_track_parsed_data(track_id: int):
    """Get parsed GPX data for a specific track by ID.

    This endpoint fetches the GPX file from storage, parses it, and returns
    the structured data directly to the frontend.

    Parameters
    ----------
    track_id : int
        The ID of the track to fetch parsed data for

    Returns
    -------
    GPXData
        The parsed GPX data with points, stats, and bounds
    """
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not available")

    if not storage_manager:
        raise HTTPException(status_code=500, detail="Storage manager not available")

    try:
        async with SessionLocal() as session:
            stmt = select(Track).filter(Track.id == track_id)
            result = await session.execute(stmt)
            track = result.scalar_one_or_none()

            if not track:
                raise HTTPException(status_code=404, detail="Track not found")

            try:
                # Load GPX data from storage
                gpx_bytes = storage_manager.load_gpx_data(track.file_path)
                if gpx_bytes is None:
                    logger.warning(
                        f"No GPX data found for track {track_id} at path: "
                        f"{track.file_path}"
                    )
                    raise HTTPException(status_code=404, detail="GPX data not found")

                # Parse GPX data
                gpx_xml_data = gpx_bytes.decode("utf-8")
                gpx = gpxpy.parse(gpx_xml_data)

                # Extract structured data using the utility function
                file_id = (
                    track.file_path.split("/")[-1].replace(".gpx", "")
                    if track.file_path
                    else str(track_id)
                )
                parsed_data = extract_from_gpx_file(gpx, file_id)

                return parsed_data

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(
                    f"Failed to parse GPX data for track {track_id}: {str(e)}"
                )
                raise HTTPException(
                    status_code=500, detail=f"Failed to parse GPX data: {str(e)}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching parsed data for track {track_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Strava API endpoints
@app.get("/api/strava/auth-url")
async def get_strava_auth_url(state: str = "strava_auth"):
    """Get Strava OAuth authorization URL"""
    try:
        redirect_uri = "http://localhost:3000/strava-callback"
        auth_url = strava.get_authorization_url(redirect_uri, state)
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error generating Strava auth URL: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate auth URL: {str(e)}"
        )


@app.post("/api/strava/exchange-code")
async def exchange_strava_code(code: str = Form(...)):
    """Exchange Strava authorization code for access token"""
    try:
        token_response = strava.exchange_code_for_token(code)
        return {
            "access_token": token_response["access_token"],
            "expires_at": token_response["expires_at"],
            "athlete": token_response["athlete"],
        }
    except Exception as e:
        logger.error(f"Error exchanging Strava code: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Failed to exchange code: {str(e)}"
        )


@app.post("/api/strava/refresh-token")
async def refresh_strava_token():
    """Refresh Strava access token using refresh token"""
    try:
        success = strava.refresh_access_token()
        if success:
            return {"success": True, "message": "Token refreshed successfully"}
        else:
            raise HTTPException(status_code=401, detail="Failed to refresh token")
    except Exception as e:
        logger.error(f"Error refreshing Strava token: {str(e)}")
        raise HTTPException(status_code=401, detail="Failed to refresh token")


@app.get("/api/strava/activities")
async def get_strava_activities(
    page: int = Query(1, ge=1), per_page: int = Query(30, ge=1, le=200)
):
    """Get list of Strava activities"""
    try:
        # Check authentication by trying to get activities
        # (will raise if not authenticated)
        activities = strava.get_activities(page, per_page)

        # Activities are already in dict format
        activities_data = activities

        return {
            "activities": activities_data,
            "page": page,
            "per_page": per_page,
            "total": len(activities_data),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Strava activities: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch activities: {str(e)}"
        )


@app.get("/api/strava/activities/{activity_id}/gpx")
async def get_strava_activity_gpx(activity_id: str):
    """Get GPX data for a Strava activity"""
    try:
        # Check authentication by trying to get GPX (will raise if not authenticated)
        gpx_string = strava.get_activity_gpx(activity_id)

        if not gpx_string:
            raise HTTPException(
                status_code=404, detail="No GPX data available for this activity"
            )

        gpx_bytes = gpx_string.encode("utf-8")

        # Save the GPX data to temporary file and process it
        file_id = str(uuid.uuid4())
        if not temp_dir:
            raise HTTPException(
                status_code=500, detail="Temporary directory not initialized"
            )

        file_path = Path(temp_dir.name) / f"{file_id}.gpx"
        logger.info(f"Processing Strava activity {activity_id}")

        try:
            with open(file_path, "wb") as f:
                f.write(gpx_bytes)
            logger.info(f"GPX file saved: {file_id}.gpx")
        except Exception as e:
            logger.error(f"Failed to save Strava GPX: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save GPX: {str(e)}")

        try:
            with open(file_path) as gpx_file:
                gpx = gpxpy.parse(gpx_file)
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Failed to parse Strava GPX file {file_id}.gpx: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid GPX file: {str(e)}")

        try:
            gpx_data = extract_from_gpx_file(gpx, file_id)
            logger.info(f"Parsed GPX file with {len(gpx_data.points)} points")
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Failed to process Strava GPX file {file_id}.gpx: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid GPX file: {str(e)}")

        # Add the file ID to the response
        gpx_data_dict = gpx_data.model_dump()
        gpx_data_dict["file_id"] = file_id

        return gpx_data_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Strava GPX for activity {activity_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch GPX: {str(e)}")


# Authorization endpoints
@app.get("/api/auth/check-authorization")
async def check_strava_authorization(strava_id: int):
    """Check if a Strava user is authorized to access editor feature."""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        async with SessionLocal() as session:
            result = await session.execute(
                select(AuthUser).where(AuthUser.strava_id == strava_id)
            )
            auth_user = result.scalar_one_or_none()

            if auth_user:
                return {
                    "authorized": True,
                    "user": AuthUserSummary(
                        strava_id=auth_user.strava_id,
                        firstname=auth_user.firstname,
                        lastname=auth_user.lastname,
                    ),
                }
            else:
                return {"authorized": False, "user": None}
    except Exception as e:
        logger.error(
            f"Error checking authorization for Strava ID {strava_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to check authorization: {str(e)}"
        )


@app.get("/api/auth/users", response_model=list[AuthUserResponse])
async def list_authorized_users():
    """List all authorized users (admin function)."""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        async with SessionLocal() as session:
            result = await session.execute(
                select(AuthUser).order_by(AuthUser.created_at)
            )
            auth_users = result.scalars().all()

            return [
                AuthUserResponse(
                    id=auth_user.id,
                    strava_id=auth_user.strava_id,
                    firstname=auth_user.firstname,
                    lastname=auth_user.lastname,
                    created_at=auth_user.created_at,
                    updated_at=auth_user.updated_at,
                )
                for auth_user in auth_users
            ]
    except Exception as e:
        logger.error(f"Error listing authorized users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
