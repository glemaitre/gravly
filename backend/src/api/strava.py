"""Strava API endpoints."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import gpxpy
from fastapi import APIRouter, Form, HTTPException, Query
from sqlalchemy import select
from stravalib import Client

from ..models.strava_token import StravaToken
from ..services.strava import StravaService
from ..utils.gpx import extract_from_gpx_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strava", tags=["strava"])


def create_strava_router(temp_dir) -> APIRouter:
    """Create Strava router with dependencies."""

    # Store references for testing purposes
    router.temp_dir = temp_dir

    @router.get("/auth-url")
    async def get_strava_auth_url(state: str = "strava_auth"):
        """Get Strava OAuth authorization URL"""
        from ..dependencies import server_config, strava_config

        try:
            # Create a client just for getting the auth URL
            client = Client()

            # Use centralized server configuration for OAuth redirect
            redirect_uri = f"{server_config.frontend_url}/strava-callback"

            auth_url = client.authorization_url(
                client_id=int(strava_config.client_id),
                redirect_uri=redirect_uri,
                scope=["activity:read_all"],
                state=state,
            )

            return {"auth_url": auth_url}
        except Exception as e:
            logger.error(f"Error generating Strava auth URL: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate auth URL: {str(e)}"
            )

    @router.post("/exchange-code")
    async def exchange_strava_code(code: str = Form(...)):
        """Exchange Strava authorization code for access token"""
        from ..dependencies import SessionLocal, strava_config

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with SessionLocal() as db_session:
                # Manually exchange the code using the client directly
                client = Client()
                token_response = client.exchange_code_for_token(
                    client_id=strava_config.client_id,
                    client_secret=strava_config.client_secret,
                    code=code,
                    return_athlete=True,
                )

                # Extract AccessInfo and athlete from response
                # We always pass return_athlete=True, so we should always get a tuple
                if not isinstance(token_response, tuple):
                    raise HTTPException(
                        status_code=400, detail="Unexpected response from Strava API"
                    )

                access_info, athlete = token_response

                if not athlete:
                    raise HTTPException(
                        status_code=400, detail="No athlete information in response"
                    )

                # Build token response
                token_dict = {
                    "access_token": access_info["access_token"],
                    "refresh_token": access_info["refresh_token"],
                    "expires_at": access_info["expires_at"],
                    "athlete": athlete.model_dump(),
                }

                # Extract athlete info and strava_id
                strava_id = athlete.id

                # Prepare athlete data for storage (convert datetime objects to
                # ISO strings)
                def convert_datetime(obj):
                    if hasattr(obj, "isoformat"):
                        return obj.isoformat()
                    elif isinstance(obj, dict):
                        return {k: convert_datetime(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_datetime(item) for item in obj]
                    return obj

                athlete_dict = athlete.model_dump()
                athlete_serializable = convert_datetime(athlete_dict)
                athlete_data_for_storage = json.dumps(athlete_serializable)

                # Convert integer timestamp to datetime
                token_response_obj = token_dict
                expires_at_dt = datetime.fromtimestamp(token_response_obj["expires_at"])

                # Check if token already exists - use correct column name
                strava_id_col = StravaToken.__table__.c.user_id
                result = await db_session.execute(
                    select(StravaToken).where(strava_id_col == strava_id)
                )
                token_record = result.scalar_one_or_none()

                if token_record:
                    # Update existing
                    token_record.access_token = token_response_obj["access_token"]
                    token_record.refresh_token = token_response_obj["refresh_token"]
                    token_record.expires_at = expires_at_dt
                    token_record.athlete_data = athlete_data_for_storage
                else:
                    # Create new
                    token_record = StravaToken(
                        strava_id=strava_id,
                        access_token=token_response_obj["access_token"],
                        refresh_token=token_response_obj["refresh_token"],
                        expires_at=expires_at_dt,
                        athlete_data=athlete_data_for_storage,
                    )
                    db_session.add(token_record)

                await db_session.commit()

                return {
                    "access_token": token_response_obj["access_token"],
                    "expires_at": token_response_obj["expires_at"],
                    "athlete": athlete_serializable,
                }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error exchanging Strava code: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Failed to exchange code: {str(e)}"
            )

    @router.post("/refresh-token")
    async def refresh_strava_token(strava_id: int = Form(...)):
        """Refresh Strava access token using refresh token"""
        from ..dependencies import SessionLocal, strava_config

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with SessionLocal() as db_session:
                strava_service = StravaService(
                    strava_config, db_session=db_session, strava_id=strava_id
                )
                success = await strava_service.refresh_access_token()
                if success:
                    return {"success": True, "message": "Token refreshed successfully"}
                else:
                    raise HTTPException(
                        status_code=401, detail="Failed to refresh token"
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing Strava token: {str(e)}")
            raise HTTPException(status_code=401, detail="Failed to refresh token")

    @router.get("/activities")
    async def get_strava_activities(
        strava_id: int = Query(..., description="Strava user ID"),
        page: int = Query(1, ge=1),
        per_page: int = Query(30, ge=1, le=200),
    ):
        """Get list of Strava activities"""
        from ..dependencies import SessionLocal, strava_config

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with SessionLocal() as db_session:
                strava_service = StravaService(
                    strava_config, db_session=db_session, strava_id=strava_id
                )
                # Check authentication by trying to get activities
                # (will raise if not authenticated)
                activities = await strava_service.get_activities(page, per_page)

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
    async def get_strava_activity_gpx(
        activity_id: str, strava_id: int = Query(..., description="Strava user ID")
    ):
        """Get GPX data for a Strava activity"""
        from ..dependencies import SessionLocal, strava_config, temp_dir

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        if temp_dir is None:
            raise HTTPException(
                status_code=500, detail="Temporary directory not initialized"
            )

        try:
            async with SessionLocal() as db_session:
                strava_service = StravaService(
                    strava_config, db_session=db_session, strava_id=strava_id
                )
                # Check authentication by trying to get GPX
                # (will raise if not authenticated)
                gpx_string = await strava_service.get_activity_gpx(activity_id)

                if not gpx_string:
                    raise HTTPException(
                        status_code=404,
                        detail="No GPX data available for this activity",
                    )

                gpx_bytes = gpx_string.encode("utf-8")

                # Save the GPX data to temporary file and process it
                file_id = str(uuid.uuid4())

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
                    logger.error(
                        f"Failed to parse Strava GPX file {file_id}.gpx: {str(e)}"
                    )
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
