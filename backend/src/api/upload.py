"""Upload API endpoints for GPX files and images."""

import io
import logging
import uuid
from pathlib import Path

import gpxpy
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image
from werkzeug.utils import secure_filename

from ..utils.gpx import GPXData, extract_from_gpx_file
from ..utils.storage import StorageManager, cleanup_local_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])


def create_upload_router(temp_dir, storage_manager: StorageManager | None) -> APIRouter:
    """Create upload router with dependencies."""

    # Store references for testing purposes
    router.temp_dir = temp_dir
    router.storage_manager = storage_manager

    @router.post("/upload-gpx", response_model=GPXData)
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
        # Import globals from main
        from ..dependencies import temp_dir as global_temp_dir

        if not file.filename.endswith(".gpx"):
            raise HTTPException(status_code=400, detail="File must be a GPX file")

        if not global_temp_dir:
            raise HTTPException(
                status_code=500, detail="Temporary directory not initialized"
            )

        file_id = str(uuid.uuid4())
        file_path = Path(global_temp_dir.name) / f"{file_id}.gpx"
        logger.info(
            f"Uploading file {file.filename} to temporary directory: {file_path}"
        )

        try:
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            logger.info(f"Successfully saved file {file.filename} as {file_id}.gpx")
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to save file: {str(e)}"
            )

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
                f"Successfully parsed GPX file {file_id}.gpx with "
                f"{len(gpx_data.points)} points"
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

    @router.post("/upload-image")
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
        # Import globals from main
        from ..dependencies import storage_manager as global_storage_manager
        from ..dependencies import temp_dir as global_temp_dir

        # Basic content-type validation
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        if not global_temp_dir:
            raise HTTPException(
                status_code=500, detail="Temporary directory not initialized"
            )

        if not global_storage_manager:
            raise HTTPException(
                status_code=500, detail="Storage manager not initialized"
            )

        image_file_id = str(uuid.uuid4())

        # Secure filename sanitization
        sanitized_original_name = (
            secure_filename(file.filename or "") if file.filename else ""
        )
        file_extension = Path(sanitized_original_name).suffix.lower() or ".jpg"
        temp_image_path = (
            Path(global_temp_dir.name) / f"{image_file_id}{file_extension}"
        )

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
                raise HTTPException(
                    status_code=400, detail=f"Invalid image file: {str(e)}"
                )

            # Save file temporarily
            with open(temp_image_path, "wb") as temp_file:
                temp_file.write(content)

            # Upload to storage using the storage manager
            storage_key = global_storage_manager.upload_image(
                local_file_path=temp_image_path,
                file_id=image_file_id,
                prefix="images-segments",
            )

            # Generate URL for the image
            image_url = global_storage_manager.get_image_url(storage_key)

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
            raise HTTPException(
                status_code=500, detail=f"Failed to upload image: {str(e)}"
            )

    return router
