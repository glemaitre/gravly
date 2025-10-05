"""Segments API endpoints."""

import json
import logging
import uuid
from pathlib import Path

import gpxpy
from fastapi import APIRouter, Form, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from ..models.image import TrackImage, TrackImageResponse
from ..models.track import (
    GPXDataResponse,
    SurfaceType,
    TireType,
    Track,
    TrackResponse,
    TrackType,
)
from ..models.video import TrackVideo, TrackVideoResponse
from ..utils.gpx import GPXData

logger = logging.getLogger(__name__)


def create_segments_router(
    session_local: async_sessionmaker[AsyncSession] | None,
) -> APIRouter:
    """Create and configure the segments router.

    Parameters
    ----------
    session_local : Optional[async_sessionmaker[AsyncSession]]
        Database session factory, can be None for testing

    Returns
    -------
    APIRouter
        Configured FastAPI router with segment endpoints
    """
    router = APIRouter(prefix="/api/segments", tags=["segments"])

    @router.post("/", response_model=TrackResponse)
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
        """Create a new segment: process uploaded GPX file with indices, upload to
        storage, and store metadata in DB.
        """
        allowed_tire_types = {"slick", "semi-slick", "knobs"}
        if tire_dry not in allowed_tire_types or tire_wet not in allowed_tire_types:
            raise HTTPException(status_code=422, detail="Invalid tire types")

        allowed_track_types = {"segment", "route"}
        if track_type not in allowed_track_types:
            raise HTTPException(status_code=422, detail="Invalid track type")

        # Import globals from main
        from ..dependencies import SessionLocal as global_session_local
        from ..dependencies import storage_manager as global_storage_manager
        from ..dependencies import temp_dir as global_temp_dir
        from ..utils.gpx import generate_gpx_segment

        # Import utility functions from their correct modules
        from ..utils.storage import cleanup_local_file

        if not global_temp_dir:
            raise HTTPException(
                status_code=500, detail="Temporary directory not initialized"
            )

        if not global_storage_manager:
            raise HTTPException(
                status_code=500, detail="Storage manager not initialized"
            )

        original_file_path = Path(global_temp_dir.name) / f"{file_id}.gpx"
        logger.info(
            f"Processing segment from file {file_id}.gpx at: {original_file_path}"
        )

        if not original_file_path.exists():
            logger.warning(f"Uploaded file not found: {original_file_path}")
            raise HTTPException(status_code=404, detail="Uploaded file not found")

        frontend_temp_dir = Path(global_temp_dir.name) / "gpx_segments"
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
                storage_key = global_storage_manager.upload_gpx_segment(
                    local_file_path=segment_file_path,
                    file_id=segment_file_id,
                    prefix="gpx-segments",
                )
                logger.info(f"Successfully uploaded segment to storage: {storage_key}")

                cleanup_success = cleanup_local_file(segment_file_path)
                if cleanup_success:
                    logger.info(
                        f"Successfully cleaned up local file: {segment_file_path}"
                    )
                else:
                    logger.warning(
                        f"Failed to clean up local file: {segment_file_path}"
                    )

                processed_file_path = (
                    f"{global_storage_manager.get_storage_root_prefix()}/{storage_key}"
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
        if global_session_local is not None:
            try:
                async with global_session_local() as session:
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

                    # Process video data and create TrackVideo records
                    if video_links and video_links != "[]":
                        try:
                            video_info_list = json.loads(video_links)

                            for video_info in video_info_list:
                                if isinstance(video_info, dict) and all(
                                    key in video_info for key in ["url", "platform"]
                                ):
                                    # Generate unique video_id
                                    video_id = str(uuid.uuid4())

                                    track_video = TrackVideo(
                                        track_id=track.id,
                                        video_id=video_id,
                                        video_url=video_info["url"],
                                        video_title=video_info.get("title", ""),
                                        platform=video_info["platform"],
                                    )
                                    session.add(track_video)

                            await session.commit()
                            logger.info(
                                f"Successfully linked {len(video_info_list)} "
                                f"videos to track {track.id}"
                            )

                        except (json.JSONDecodeError, Exception) as e:
                            logger.warning(f"Failed to process video data: {str(e)}")
                            # Continue without videos

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

    @router.options("/search")
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

    @router.get("/search")
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

        This uses simple bounding box intersection - a segment is included if its
        bounding rectangle intersects with the search area rectangle (at least
        partially visible). The results are limited to the specified number of
        segments, selecting those closest to the center of the search bounds.
        Streams segments as they are processed, allowing the frontend to start
        drawing immediately.

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
        # Import global SessionLocal from main
        from ..dependencies import SessionLocal as global_session_local

        if not global_session_local:
            raise HTTPException(status_code=500, detail="Database not available")

        # Convert string track_type to enum
        try:
            track_type_enum = TrackType(track_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid track_type: {track_type}. Must be 'segment' or 'route'"
                ),
            )

        async def generate():
            try:
                async with global_session_local() as session:
                    search_center_latitude = (north + south) / 2
                    search_center_longitude = (east + west) / 2

                    # Calculate squared Euclidean distance for better performance on
                    # local areas. For small distances, this is a good approximation
                    # and much
                    # faster than Haversine Using squared distance to avoid sqrt()
                    # calculation
                    distance_expr = (
                        func.pow(Track.barycenter_latitude - search_center_latitude, 2)
                        + func.pow(
                            Track.barycenter_longitude - search_center_longitude, 2
                        )
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

    @router.get("/{track_id}/gpx", response_model=GPXDataResponse)
    async def get_track_gpx_data(track_id: int):
        """Get GPX data for a specific track by ID.

        This endpoint fetches the GPX XML data from storage for the given track ID.
        This is called by the frontend only when it needs to render the track on the
        map.

        Parameters
        ----------
        track_id : int
            The ID of the track to fetch GPX data for

        Returns
        -------
        GPXDataResponse
            The GPX XML content only
        """
        # Import globals from main
        from ..dependencies import SessionLocal as global_session_local
        from ..dependencies import storage_manager as global_storage_manager

        if not global_session_local:
            raise HTTPException(status_code=500, detail="Database not available")

        if not global_storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not available")

        try:
            async with global_session_local() as session:
                stmt = select(Track).filter(Track.id == track_id)
                result = await session.execute(stmt)
                track = result.scalar_one_or_none()

                if not track:
                    raise HTTPException(status_code=404, detail="Track not found")

                try:
                    gpx_bytes = global_storage_manager.load_gpx_data(track.file_path)
                    if gpx_bytes is None:
                        logger.warning(
                            f"No GPX data found for track {track_id} at path: "
                            f"{track.file_path}"
                        )
                        raise HTTPException(
                            status_code=404, detail="GPX data not found"
                        )
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
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )

    @router.get("/{track_id}", response_model=TrackResponse)
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
        # Import global SessionLocal from main
        from ..dependencies import SessionLocal as global_session_local

        if not global_session_local:
            raise HTTPException(status_code=500, detail="Database not available")

        try:
            async with global_session_local() as session:
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
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )

    @router.get("/{track_id}/data", response_model=GPXData)
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
        # Import globals from main
        from ..dependencies import SessionLocal as global_session_local
        from ..dependencies import storage_manager as global_storage_manager
        from ..utils.gpx import extract_from_gpx_file

        if not global_session_local:
            raise HTTPException(status_code=500, detail="Database not available")

        if not global_storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not available")

        try:
            async with global_session_local() as session:
                stmt = select(Track).filter(Track.id == track_id)
                result = await session.execute(stmt)
                track = result.scalar_one_or_none()

                if not track:
                    raise HTTPException(status_code=404, detail="Track not found")

                try:
                    # Load GPX data from storage
                    gpx_bytes = global_storage_manager.load_gpx_data(track.file_path)
                    if gpx_bytes is None:
                        logger.warning(
                            f"No GPX data found for track {track_id} at path: "
                            f"{track.file_path}"
                        )
                        raise HTTPException(
                            status_code=404, detail="GPX data not found"
                        )

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
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )

    @router.get("/{track_id}/images", response_model=list[TrackImageResponse])
    async def get_track_images(track_id: int):
        """Get all images associated with a specific track by ID.

        Parameters
        ----------
        track_id : int
            The ID of the track to fetch images for

        Returns
        -------
        list[TrackImageResponse]
            List of track images with their metadata
        """
        # Import global SessionLocal from main
        from ..dependencies import SessionLocal as global_session_local

        if not global_session_local:
            raise HTTPException(status_code=500, detail="Database not available")

        try:
            async with global_session_local() as session:
                # First verify the track exists
                track_stmt = select(Track).filter(Track.id == track_id)
                track_result = await session.execute(track_stmt)
                track = track_result.scalar_one_or_none()

                if not track:
                    raise HTTPException(status_code=404, detail="Track not found")

                # Get all images for this track
                images_stmt = select(TrackImage).filter(TrackImage.track_id == track_id)
                images_result = await session.execute(images_stmt)
                images = images_result.scalars().all()

                # Convert to response models
                image_responses = []
                for image in images:
                    image_response = TrackImageResponse(
                        id=image.id,
                        track_id=image.track_id,
                        image_id=image.image_id,
                        image_url=image.image_url,
                        storage_key=image.storage_key,
                        filename=image.filename,
                        original_filename=image.original_filename,
                        created_at=image.created_at,
                    )
                    image_responses.append(image_response)

                logger.info(
                    f"Retrieved {len(image_responses)} images for track {track_id}"
                )
                return image_responses

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching images for track {track_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )

    @router.get("/{track_id}/videos", response_model=list[TrackVideoResponse])
    async def get_track_videos(track_id: int):
        """Get all videos associated with a specific track by ID.

        Parameters
        ----------
        track_id : int
            The ID of the track to fetch videos for

        Returns
        -------
        list[TrackVideoResponse]
            List of track videos with their metadata
        """
        # Import global SessionLocal from main
        from ..dependencies import SessionLocal as global_session_local

        if not global_session_local:
            raise HTTPException(status_code=500, detail="Database not available")

        try:
            async with global_session_local() as session:
                # First verify the track exists
                track_stmt = select(Track).filter(Track.id == track_id)
                track_result = await session.execute(track_stmt)
                track = track_result.scalar_one_or_none()

                if not track:
                    raise HTTPException(status_code=404, detail="Track not found")

                # Get all videos for this track
                videos_stmt = select(TrackVideo).filter(TrackVideo.track_id == track_id)
                videos_result = await session.execute(videos_stmt)
                videos = videos_result.scalars().all()

                # Convert to response models
                video_responses = []
                for video in videos:
                    video_response = TrackVideoResponse(
                        id=video.id,
                        track_id=video.track_id,
                        video_id=video.video_id,
                        video_url=video.video_url,
                        video_title=video.video_title,
                        platform=video.platform,
                        created_at=video.created_at,
                    )
                    video_responses.append(video_response)

                logger.info(
                    f"Retrieved {len(video_responses)} videos for track {track_id}"
                )
                return video_responses

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching videos for track {track_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )

    @router.put("/{track_id}", response_model=TrackResponse)
    async def update_segment(
        track_id: int,
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
        """Update an existing segment: process uploaded GPX file with indices,
        upload to storage, update metadata in DB, and remove the previous file.

        Parameters
        ----------
        track_id : int
            The ID of the track to update
        name : str
            Name of the segment
        track_type : str
            Type of track ('segment' or 'route')
        tire_dry : str
            Tire type for dry conditions
        tire_wet : str
            Tire type for wet conditions
        file_id : str
            File ID for the GPX data
        start_index : int
            Start index for GPX segment extraction
        end_index : int
            End index for GPX segment extraction
        surface_type : str
            Type of surface
        difficulty_level : int
            Difficulty level (1-5)
        commentary_text : str
            Commentary text
        video_links : str
            JSON string of video links
        image_data : str
            JSON string of image data

        Returns
        -------
        TrackResponse
            Updated track information
        """
        allowed_tire_types = {"slick", "semi-slick", "knobs"}
        if tire_dry not in allowed_tire_types or tire_wet not in allowed_tire_types:
            raise HTTPException(status_code=422, detail="Invalid tire types")

        allowed_track_types = {"segment", "route"}
        if track_type not in allowed_track_types:
            raise HTTPException(status_code=422, detail="Invalid track type")

        # Import globals from main
        from ..dependencies import SessionLocal as global_session_local
        from ..dependencies import storage_manager as global_storage_manager
        from ..dependencies import temp_dir as global_temp_dir
        from ..utils.gpx import generate_gpx_segment

        # Import utility functions from their correct modules
        from ..utils.storage import cleanup_local_file

        if not global_temp_dir:
            raise HTTPException(
                status_code=500, detail="Temporary directory not initialized"
            )

        if not global_storage_manager:
            raise HTTPException(
                status_code=500, detail="Storage manager not initialized"
            )

        if not global_session_local:
            raise HTTPException(status_code=500, detail="Database not available")

        # Check if track exists and get current file path for cleanup
        async with global_session_local() as session:
            track_stmt = select(Track).filter(Track.id == track_id)
            track_result = await session.execute(track_stmt)
            existing_track = track_result.scalar_one_or_none()

            if not existing_track:
                raise HTTPException(status_code=404, detail="Track not found")

            old_file_path = existing_track.file_path
            logger.info(f"Updating track {track_id}, old file: {old_file_path}")

        # Handle GPX file processing
        original_file_path = Path(global_temp_dir.name) / f"{file_id}.gpx"
        logger.info(
            f"Processing segment from file {file_id}.gpx at: {original_file_path}"
        )

        if not original_file_path.exists():
            logger.warning(f"Uploaded file not found: {original_file_path}")
            raise HTTPException(status_code=404, detail="Uploaded file not found")

        frontend_temp_dir = Path(global_temp_dir.name) / "gpx_segments"
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
                # Upload new GPX file to storage
                storage_key = global_storage_manager.upload_gpx_segment(
                    local_file_path=segment_file_path,
                    file_id=segment_file_id,
                    prefix="gpx-segments",
                )
                logger.info(f"Successfully uploaded segment to storage: {storage_key}")

                cleanup_success = cleanup_local_file(segment_file_path)
                if cleanup_success:
                    logger.info(
                        f"Successfully cleaned up local file: {segment_file_path}"
                    )
                else:
                    logger.warning(
                        f"Failed to clean up local file: {segment_file_path}"
                    )

                processed_file_path = (
                    f"{global_storage_manager.get_storage_root_prefix()}/{storage_key}"
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

        # Update metadata in DB and handle file cleanup
        try:
            async with global_session_local() as session:
                # Get the track again within this session
                track_stmt = select(Track).filter(Track.id == track_id)
                track_result = await session.execute(track_stmt)
                track = track_result.scalar_one_or_none()

                if not track:
                    raise HTTPException(status_code=404, detail="Track not found")

                # Calculate new bounds and barycenter
                barycenter_latitude = (bounds.north + bounds.south) / 2
                barycenter_longitude = (bounds.east + bounds.west) / 2

                # Update track fields
                track.file_path = str(processed_file_path)
                track.bound_north = bounds.north
                track.bound_south = bounds.south
                track.bound_east = bounds.east
                track.bound_west = bounds.west
                track.barycenter_latitude = barycenter_latitude
                track.barycenter_longitude = barycenter_longitude
                track.name = name
                track.track_type = TrackType(track_type)
                track.difficulty_level = difficulty_level
                track.surface_type = SurfaceType(surface_type)
                track.tire_dry = TireType(tire_dry)
                track.tire_wet = TireType(tire_wet)
                track.comments = commentary_text

                await session.commit()
                await session.refresh(track)

                # Process image data and add new TrackImage records (preserve existing)
                try:
                    image_data_list = json.loads(image_data) if image_data else []
                    video_links_list = json.loads(video_links) if video_links else []

                    # Add new images (preserve existing ones)
                    for img_data in image_data_list:
                        track_image = TrackImage(
                            track_id=track.id,
                            image_id=img_data["image_id"],
                            image_url=img_data["image_url"],
                            storage_key=img_data.get("storage_key", ""),
                            filename=img_data.get("filename", ""),
                            original_filename=img_data.get("original_filename", ""),
                        )
                        session.add(track_image)

                    # Add new videos (preserve existing ones)
                    for video_data in video_links_list:
                        track_video = TrackVideo(
                            track_id=track.id,
                            video_id=video_data["id"],
                            video_url=video_data["url"],
                            video_title=None,  # Could be extracted from URL if needed
                            platform=video_data.get("platform", "other"),
                        )
                        session.add(track_video)

                    await session.commit()

                except Exception as media_e:
                    logger.warning(f"Failed to update media for segment: {media_e}")
                    # Continue without media updates

                # Now that DB is updated, clean up the old file
                try:
                    # Extract storage key from old file path
                    if old_file_path.startswith(
                        global_storage_manager.get_storage_root_prefix()
                    ):
                        # Remove the storage root prefix to get the storage key
                        prefix_len = len(
                            global_storage_manager.get_storage_root_prefix()
                        )
                        old_storage_key = old_file_path[prefix_len + 1 :]
                        delete_success = (
                            global_storage_manager.delete_gpx_segment_by_url(
                                old_file_path
                            )
                        )
                        if delete_success:
                            logger.info(
                                f"Successfully deleted old file: {old_storage_key}"
                            )
                        else:
                            logger.warning(
                                f"Failed to delete old file: {old_storage_key}"
                            )
                    else:
                        logger.warning(
                            f"Old file path doesn't match storage format:"
                            f" {old_file_path}"
                        )
                except Exception as cleanup_e:
                    logger.warning(f"Failed to cleanup old file: {cleanup_e}")
                    # Continue even if cleanup fails

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
            logger.error(f"Failed to update segment in database: {db_e}")
            # Try to clean up the newly uploaded file since DB update failed
            try:
                if "storage_key" in locals():
                    global_storage_manager.delete_gpx_segment_by_url(storage_key)
            except Exception as cleanup_e:
                logger.error(f"Failed to cleanup new file after DB error: {cleanup_e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to update segment: {str(db_e)}"
            )

    @router.delete("/{track_id}")
    async def delete_segment(track_id: int):
        """Delete a track and all associated files from storage and database.

        Parameters
        ----------
        track_id : int
            The ID of the track to delete

        Returns
        -------
        dict
            Success message with deleted track information
        """
        # Import globals from main
        from ..dependencies import SessionLocal as global_session_local
        from ..dependencies import storage_manager as global_storage_manager

        if not global_session_local:
            raise HTTPException(status_code=500, detail="Database not available")

        if not global_storage_manager:
            raise HTTPException(
                status_code=500, detail="Storage manager not initialized"
            )

        try:
            async with global_session_local() as session:
                # First, get the track and its associated files with eager loading
                stmt = (
                    select(Track)
                    .options(selectinload(Track.images), selectinload(Track.videos))
                    .filter(Track.id == track_id)
                )
                result = await session.execute(stmt)
                track = result.scalar_one_or_none()

                if not track:
                    raise HTTPException(status_code=404, detail="Track not found")

                # Get associated images and videos for storage cleanup
                images = track.images
                videos = track.videos

                # Delete files from storage before database deletion
                # Delete GPX file
                try:
                    if track.file_path:
                        logger.info(
                            f"Deleting GPX file from storage: {track.file_path}"
                        )
                        global_storage_manager.delete_gpx_segment_by_url(
                            track.file_path
                        )
                except Exception as e:
                    logger.warning(f"Failed to delete GPX file from storage: {str(e)}")

                # Delete associated images from storage
                for image in images:
                    try:
                        # Construct the proper storage URL from storage_key
                        storage_url = (
                            f"{global_storage_manager.get_storage_root_prefix()}/"
                            f"{image.storage_key}"
                        )
                        logger.info(f"Deleting image from storage: {storage_url}")
                        global_storage_manager.delete_image_by_url(storage_url)
                    except Exception as e:
                        logger.warning(f"Failed to delete image from storage: {str(e)}")

                # Note: Videos are just URLs, no files to delete from storage

                # Store track info for response before deletion
                track_info = {
                    "id": track.id,
                    "name": track.name,
                    "file_path": track.file_path,
                    "images_count": len(images),
                    "videos_count": len(videos),
                }

                # Delete the track (cascade will handle images and videos in DB)
                stmt = delete(Track).where(Track.id == track_id)
                await session.execute(stmt)
                await session.commit()

                logger.info(
                    f"Successfully deleted track {track_id} and all associated files"
                )
                return {
                    "message": "Track deleted successfully",
                    "deleted_track": track_info,
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting track {track_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to delete track: {str(e)}"
            )

    return router
