"""Wahoo API endpoints."""

import base64
import json
import logging
from datetime import datetime

import gpxpy
from fastapi import APIRouter, Form, HTTPException, Query
from sqlalchemy import select

from src.dependencies import get_wahoo_config
from src.models.track import Track, TrackType
from src.models.wahoo_token import WahooToken
from src.services.wahoo.client import Client
from src.services.wahoo.service import WahooService
from src.utils.gpx import convert_gpx_to_fit, extract_from_gpx_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wahoo", tags=["wahoo"])


def create_wahoo_router() -> APIRouter:
    """Create Wahoo router with dependencies."""

    @router.get("/auth-url")
    async def get_wahoo_auth_url(state: str = "wahoo_auth"):
        """Get Wahoo OAuth authorization URL"""
        from ..dependencies import wahoo_config

        try:
            client = Client()

            auth_url = client.authorization_url(
                client_id=wahoo_config.client_id,
                redirect_uri=wahoo_config.callback_url,
                scope=wahoo_config.scopes,
                state=state,
            )

            logger.info("Generated Wahoo authorization URL")

            return {"auth_url": auth_url}
        except Exception as e:
            logger.error(f"Error generating Wahoo authorization URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate authorization URL: {str(e)}",
            )

    @router.post("/exchange-code")
    async def exchange_wahoo_code(code: str = Form(...)):
        """Exchange Wahoo authorization code for access token"""
        from ..dependencies import SessionLocal, get_wahoo_config

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with SessionLocal() as db_session:
                # Exchange the code using the client directly
                client = Client()
                token_response = client.exchange_code_for_token(
                    client_id=get_wahoo_config().client_id,
                    client_secret=get_wahoo_config().client_secret,
                    code=code,
                    redirect_uri=get_wahoo_config().callback_url,
                )

                # Set the access token on the client to fetch user info
                client.access_token = token_response["access_token"]

                # Get user information to get the wahoo_id
                user_info = client.get_user()
                wahoo_id = user_info.get("id")

                if not wahoo_id:
                    raise HTTPException(
                        status_code=400, detail="No user ID in Wahoo response"
                    )

                # Convert integer timestamp to datetime
                expires_at_dt = datetime.fromtimestamp(token_response["expires_at"])

                # Check if token already exists
                wahoo_id_col = WahooToken.__table__.c.user_id
                result = await db_session.execute(
                    select(WahooToken).where(wahoo_id_col == wahoo_id)
                )
                token_record = result.scalar_one_or_none()

                # Serialize user_info for storage
                user_data_json = json.dumps(user_info)

                if token_record:
                    # Update existing
                    token_record.access_token = token_response["access_token"]
                    token_record.refresh_token = token_response["refresh_token"]
                    token_record.expires_at = expires_at_dt
                    token_record.user_data = user_data_json
                else:
                    # Create new
                    token_record = WahooToken(
                        wahoo_id=wahoo_id,
                        access_token=token_response["access_token"],
                        refresh_token=token_response["refresh_token"],
                        expires_at=expires_at_dt,
                        user_data=user_data_json,
                    )
                    db_session.add(token_record)

                await db_session.commit()

                return {
                    "access_token": token_response["access_token"],
                    "expires_at": token_response["expires_at"],
                    "user": user_info,
                }
        except Exception as e:
            logger.error(f"Error exchanging Wahoo code: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Failed to exchange code: {str(e)}"
            )

    @router.post("/refresh-token")
    async def refresh_wahoo_token(wahoo_id: int = Form(...)):
        """Refresh Wahoo access token using refresh token"""
        from ..dependencies import SessionLocal

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with SessionLocal() as db_session:
                wahoo_config = get_wahoo_config()
                wahoo_service = WahooService(
                    wahoo_config, db_session=db_session, wahoo_id=wahoo_id
                )
                success = await wahoo_service.refresh_access_token()
                if success:
                    return {"success": True, "message": "Token refreshed successfully"}
                else:
                    raise HTTPException(
                        status_code=401, detail="Failed to refresh token"
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing Wahoo token: {str(e)}")
            raise HTTPException(status_code=401, detail="Failed to refresh token")

    @router.post("/deauthorize")
    async def deauthorize_wahoo(wahoo_id: int = Form(...)):
        """Deauthorize the application and delete all tokens"""
        from ..dependencies import SessionLocal

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with SessionLocal() as db_session:
                wahoo_config = get_wahoo_config()
                wahoo_service = WahooService(
                    wahoo_config, db_session=db_session, wahoo_id=wahoo_id
                )

                # Deauthorize with Wahoo API
                await wahoo_service.deauthorize()
                logger.info(
                    f"Successfully deauthorized with Wahoo API for user {wahoo_id}"
                )

                # Delete tokens from our database
                wahoo_id_col = WahooToken.__table__.c.user_id
                result = await db_session.execute(
                    select(WahooToken).where(wahoo_id_col == wahoo_id)
                )
                token_record = result.scalar_one_or_none()

                if token_record:
                    await db_session.delete(token_record)
                    await db_session.commit()
                    logger.info(f"Deleted tokens from database for user {wahoo_id}")

                return {"success": True, "message": "Deauthorized successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deauthorizing: {str(e)}")
            raise HTTPException(
                status_code=401, detail=f"Failed to deauthorize: {str(e)}"
            )

    @router.get("/user")
    async def get_wahoo_user(wahoo_id: int = Query(..., description="Wahoo user ID")):
        """Get authenticated user information"""
        from ..dependencies import SessionLocal

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with SessionLocal() as db_session:
                wahoo_config = get_wahoo_config()
                wahoo_service = WahooService(
                    wahoo_config, db_session=db_session, wahoo_id=wahoo_id
                )
                user = await wahoo_service.get_user()
                return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Failed to get user: {str(e)}")

    @router.get("/callback")
    async def wahoo_callback(
        code: str = Query(None, description="Authorization code from Wahoo"),
    ):
        """Handle Wahoo OAuth callback and print the authorization code."""
        try:
            if not code:
                logger.warning("Wahoo callback received without authorization code")
                raise HTTPException(
                    status_code=400, detail="Authorization code is required"
                )

            return {
                "message": "Wahoo authorization code received successfully",
                "code": code,
                "status": "success",
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling Wahoo callback: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to handle callback: {str(e)}"
            )

    @router.post("/routes/{route_id}/upload")
    async def upload_route(
        route_id: int, wahoo_id: int = Query(..., description="Wahoo user ID")
    ):
        """Upload a route from the database to Wahoo"""
        from src.dependencies import SessionLocal as global_session_local

        if global_session_local is None:
            logger.error("Database not initialized")
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with global_session_local() as session:
                # Get the route from database
                stmt = select(Track).where(
                    Track.id == route_id, Track.track_type == TrackType.ROUTE
                )
                result = await session.execute(stmt)
                track = result.scalar_one_or_none()

                if not track:
                    logger.error(f"Route {route_id} not found in database")
                    raise HTTPException(status_code=404, detail="Route not found")

                # Load GPX file using storage manager
                from src.dependencies import storage_manager as global_storage_manager

                if not global_storage_manager:
                    raise HTTPException(
                        status_code=500, detail="Storage manager not available"
                    )

                gpx_bytes = global_storage_manager.load_gpx_data(track.file_path)

                if gpx_bytes is None:
                    logger.error(f"Failed to load GPX data from {track.file_path}")
                    raise HTTPException(status_code=404, detail="GPX file not found")

                gpx_content = gpx_bytes.decode("utf-8")

                wahoo_config = get_wahoo_config()
                wahoo_service = WahooService(
                    wahoo_config, db_session=session, wahoo_id=wahoo_id
                )

                # Parse GPX and extract metadata
                gpx = gpxpy.parse(gpx_content)
                gpx_data = extract_from_gpx_file(gpx, str(route_id))

                # Get start point
                start_point = gpx_data.points[0] if gpx_data.points else None

                # Convert GPX to FIT format
                fit_bytes = convert_gpx_to_fit(gpx, track.name)

                # Encode FIT content as base64 data URI for Wahoo API
                fit_base64 = base64.b64encode(fit_bytes).decode("utf-8")
                route_file_data_uri = f"data:application/vnd.fit;base64,{fit_base64}"

                # Call Wahoo service to upload route
                external_id = f"gravly_route_{route_id}"

                # Prepare common route parameters (for both create and update)
                common_params = {
                    "route_file": route_file_data_uri,
                    "filename": f"{track.name}.fit",
                    "route_name": track.name,
                    "description": track.comments or "",
                    "provider_updated_at": (
                        gpx.time.isoformat() if gpx.time else datetime.now().isoformat()
                    ),
                    "start_lat": start_point.latitude if start_point else 0.0,
                    "start_lng": start_point.longitude if start_point else 0.0,
                    "distance": gpx_data.total_stats.total_distance
                    * 1000,  # Convert km to meters
                    "ascent": max(0.0, gpx_data.total_stats.total_elevation_gain),
                    "descent": max(0.0, gpx_data.total_stats.total_elevation_loss),
                }

                # Get all routes from Wahoo to check if route exists
                all_routes = await wahoo_service.get_routes()

                # Look for existing route with matching external_id
                wahoo_route_id = None
                for route in all_routes:
                    if route.get("external_id") == external_id:
                        wahoo_route_id = route["id"]
                        break

                # Upload or update the route
                if wahoo_route_id:
                    # Update existing route (external_id is not passed for updates)
                    result = await wahoo_service.update_route(
                        route_id=wahoo_route_id, **common_params
                    )
                else:
                    # Create new route (include external_id for new routes)
                    create_params = {**common_params, "external_id": external_id}
                    result = await wahoo_service.create_route(**create_params)

                result_message = "updated" if wahoo_route_id else "uploaded"
                return {
                    "success": True,
                    "message": (
                        f"Route '{track.name}' {result_message} to Wahoo successfully"
                    ),
                }
        except HTTPException as he:
            logger.error(f"HTTPException raised: {he.status_code} - {he.detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to upload route: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to upload route: {str(e)}"
            )

    @router.delete("/routes/{route_id}")
    async def delete_route(
        route_id: int, wahoo_id: int = Query(..., description="Wahoo user ID")
    ):
        """Delete a route from Wahoo Cloud"""
        from src.dependencies import SessionLocal as global_session_local

        if global_session_local is None:
            logger.error("Database not initialized")
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with global_session_local() as session:
                # Get the route from database
                stmt = select(Track).where(
                    Track.id == route_id, Track.track_type == TrackType.ROUTE
                )
                result = await session.execute(stmt)
                track = result.scalar_one_or_none()

                if not track:
                    logger.error(f"Route {route_id} not found in database")
                    raise HTTPException(status_code=404, detail="Route not found")

                # Get Wahoo service
                wahoo_config = get_wahoo_config()
                wahoo_service = WahooService(
                    wahoo_config, db_session=session, wahoo_id=wahoo_id
                )

                # Get all routes from Wahoo to check if route exists
                all_routes = await wahoo_service.get_routes()

                # Look for existing route with matching external_id
                external_id = f"gravly_route_{route_id}"
                wahoo_route_id = None
                for route in all_routes:
                    if route.get("external_id") == external_id:
                        wahoo_route_id = route["id"]
                        break

                # Delete the route if it exists
                if wahoo_route_id:
                    await wahoo_service.delete_route(wahoo_route_id)
                    return {
                        "success": True,
                        "message": (
                            f"Route '{track.name}' deleted from Wahoo successfully"
                        ),
                    }
                else:
                    logger.warning(
                        f"Route with external_id '{external_id}' not found in Wahoo"
                    )
                    raise HTTPException(
                        status_code=404, detail="Route not found in Wahoo Cloud"
                    )

        except HTTPException as he:
            logger.error(f"HTTPException raised: {he.status_code} - {he.detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to delete route: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to delete route: {str(e)}"
            )

    return router
