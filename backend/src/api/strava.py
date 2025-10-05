"""Strava API endpoints."""

import logging
import uuid
from pathlib import Path

import gpxpy
from fastapi import APIRouter, Form, HTTPException, Query

from ..services.strava import StravaService
from ..utils.gpx import extract_from_gpx_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strava", tags=["strava"])


def create_strava_router(strava_service: StravaService, temp_dir) -> APIRouter:
    """Create Strava router with dependencies."""

    # Store references for testing purposes
    router.strava_service = strava_service
    router.temp_dir = temp_dir

    @router.get("/auth-url")
    async def get_strava_auth_url(state: str = "strava_auth"):
        """Get Strava OAuth authorization URL"""
        try:
            redirect_uri = "http://localhost:3000/strava-callback"
            auth_url = strava_service.get_authorization_url(redirect_uri, state)
            return {"auth_url": auth_url}
        except Exception as e:
            logger.error(f"Error generating Strava auth URL: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate auth URL: {str(e)}"
            )

    @router.post("/exchange-code")
    async def exchange_strava_code(code: str = Form(...)):
        """Exchange Strava authorization code for access token"""
        try:
            token_response = strava_service.exchange_code_for_token(code)
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

    @router.post("/refresh-token")
    async def refresh_strava_token():
        """Refresh Strava access token using refresh token"""
        try:
            success = strava_service.refresh_access_token()
            if success:
                return {"success": True, "message": "Token refreshed successfully"}
            else:
                raise HTTPException(status_code=401, detail="Failed to refresh token")
        except Exception as e:
            logger.error(f"Error refreshing Strava token: {str(e)}")
            raise HTTPException(status_code=401, detail="Failed to refresh token")

    @router.get("/activities")
    async def get_strava_activities(
        page: int = Query(1, ge=1), per_page: int = Query(30, ge=1, le=200)
    ):
        """Get list of Strava activities"""
        try:
            # Check authentication by trying to get activities
            # (will raise if not authenticated)
            activities = strava_service.get_activities(page, per_page)

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

    @router.get("/activities/{activity_id}/gpx")
    async def get_strava_activity_gpx(activity_id: str):
        """Get GPX data for a Strava activity"""
        try:
            # Import temp_dir from main module to access the global variable
            from ..main import temp_dir

            # Check authentication by trying to get GPX (will raise if not authenticated)
            gpx_string = strava_service.get_activity_gpx(activity_id)

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
                raise HTTPException(
                    status_code=500, detail=f"Failed to save GPX: {str(e)}"
                )

            try:
                with open(file_path) as gpx_file:
                    gpx = gpxpy.parse(gpx_file)
            except Exception as e:
                if file_path.exists():
                    file_path.unlink()
                logger.error(f"Failed to parse Strava GPX file {file_id}.gpx: {str(e)}")
                raise HTTPException(
                    status_code=400, detail=f"Invalid GPX file: {str(e)}"
                )

            try:
                gpx_data = extract_from_gpx_file(gpx, file_id)
                logger.info(f"Parsed GPX file with {len(gpx_data.points)} points")
            except Exception as e:
                if file_path.exists():
                    file_path.unlink()
                logger.error(
                    f"Failed to process Strava GPX file {file_id}.gpx: {str(e)}"
                )
                raise HTTPException(
                    status_code=400, detail=f"Invalid GPX file: {str(e)}"
                )

            # Add the file ID to the response
            gpx_data_dict = gpx_data.model_dump()
            gpx_data_dict["file_id"] = file_id

            return gpx_data_dict

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error fetching Strava GPX for activity {activity_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch GPX: {str(e)}"
            )

    return router
