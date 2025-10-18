"""Wahoo Cloud API integration endpoints."""

import logging
import os
import secrets
import urllib.parse

import httpx
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..utils.config import load_environment_config

logger = logging.getLogger(__name__)

# Load Wahoo configuration
try:
    _, _, _, _, server_config = load_environment_config()
    WAHOO_CLIENT_ID = os.getenv("WAHOO_CLIENT_ID")
    WAHOO_CLIENT_SECRET = os.getenv("WAHOO_CLIENT_SECRET")
    WAHOO_REDIRECT_URI = os.getenv("WAHOO_REDIRECT_URI")
    WAHOO_API_BASE_URL = os.getenv("WAHOO_API_BASE_URL", "https://api.wahooligan.com")
    WAHOO_AUTH_URL = os.getenv(
        "WAHOO_AUTH_URL", "https://api.wahooligan.com/oauth/authorize"
    )
    WAHOO_TOKEN_URL = os.getenv(
        "WAHOO_TOKEN_URL", "https://api.wahooligan.com/oauth/token"
    )
    WAHOO_SCOPES = os.getenv("WAHOO_SCOPES", "read,read_workouts")

    if not all([WAHOO_CLIENT_ID, WAHOO_CLIENT_SECRET, WAHOO_REDIRECT_URI]):
        logger.warning(
            "Wahoo API configuration incomplete. Some features may not work."
        )
except Exception as e:
    logger.error(f"Failed to load Wahoo configuration: {e}")
    WAHOO_CLIENT_ID = None
    WAHOO_CLIENT_SECRET = None
    WAHOO_REDIRECT_URI = None
    WAHOO_API_BASE_URL = "https://api.wahooligan.com"
    WAHOO_AUTH_URL = "https://api.wahooligan.com/oauth/authorize"
    WAHOO_TOKEN_URL = "https://api.wahooligan.com/oauth/token"
    WAHOO_SCOPES = "read,read_workouts"


def create_wahoo_router(
    session_local: async_sessionmaker[AsyncSession] | None,
) -> APIRouter:
    """Create and configure the Wahoo API router.

    Parameters
    ----------
    session_local : Optional[async_sessionmaker[AsyncSession]]
        Database session factory, can be None for testing

    Returns
    -------
    APIRouter
        Configured FastAPI router with Wahoo API endpoints
    """
    router = APIRouter(prefix="/api/wahoo", tags=["wahoo"])

    @router.get("/status")
    async def get_wahoo_status():
        """Check Wahoo API connection status for the current user."""
        # Import global SessionLocal from main
        from ..dependencies import SessionLocal as global_session_local

        if global_session_local is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        # For now, we'll implement a simple status check
        # In a real implementation, you'd check if the user has valid Wahoo tokens
        return {
            "connected": False,
            "user": None,
            "message": "Wahoo integration not yet implemented",
        }

    @router.post("/authorize")
    async def initiate_wahoo_authorization():
        """Initiate Wahoo OAuth2 authorization flow."""
        if not WAHOO_CLIENT_ID or not WAHOO_CLIENT_SECRET or not WAHOO_REDIRECT_URI:
            raise HTTPException(
                status_code=503,
                detail="Wahoo API not configured. Please check environment variables.",
            )

        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        auth_params = {
            "client_id": WAHOO_CLIENT_ID,
            "redirect_uri": WAHOO_REDIRECT_URI,
            "scope": WAHOO_SCOPES,
            "response_type": "code",
            "state": state,
        }

        auth_url = f"{WAHOO_AUTH_URL}?{urllib.parse.urlencode(auth_params)}"

        return {"authorization_url": auth_url, "state": state}

    @router.get("/callback")
    async def wahoo_oauth_callback(
        code: str = Query(..., description="Authorization code from Wahoo"),
        state: str = Query(..., description="State parameter for CSRF protection"),
        error: str | None = Query(None, description="Error from Wahoo OAuth"),
    ):
        """Handle Wahoo OAuth2 callback."""
        if error:
            raise HTTPException(
                status_code=400, detail=f"OAuth authorization failed: {error}"
            )

        if not code:
            raise HTTPException(
                status_code=400, detail="Authorization code not provided"
            )

        try:
            # Exchange authorization code for access token
            token_data = {
                "client_id": WAHOO_CLIENT_ID,
                "client_secret": WAHOO_CLIENT_SECRET,
                "code": code,
                "redirect_uri": WAHOO_REDIRECT_URI,
                "grant_type": "authorization_code",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    WAHOO_TOKEN_URL,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    logger.error(
                        f"Token exchange failed: {response.status_code} - "
                        f"{response.text}"
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to exchange authorization code for access token",
                    )

                token_response = response.json()
                access_token = token_response.get("access_token")

                if not access_token:
                    raise HTTPException(
                        status_code=400, detail="No access token received from Wahoo"
                    )

                # Get user information from Wahoo API
                user_response = await client.get(
                    f"{WAHOO_API_BASE_URL}/users/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                if user_response.status_code != 200:
                    logger.error(
                        f"Failed to get user info: {user_response.status_code} - "
                        f"{user_response.text}"
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to get user information from Wahoo",
                    )

                user_data = user_response.json()

                # Store tokens and user data (in a real implementation,
                # you'd store these in the database)
                # For now, we'll just return success
                return {
                    "success": True,
                    "user": {
                        "id": user_data.get("id"),
                        "firstname": user_data.get("firstname"),
                        "lastname": user_data.get("lastname"),
                        "email": user_data.get("email"),
                    },
                    "message": "Successfully connected to Wahoo Cloud API",
                }

        except httpx.RequestError as e:
            logger.error(f"HTTP request error during Wahoo OAuth: {e}")
            raise HTTPException(
                status_code=500, detail="Network error during Wahoo authentication"
            )
        except Exception as e:
            logger.error(f"Unexpected error during Wahoo OAuth: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error during Wahoo authentication",
            )

    @router.post("/disconnect")
    async def disconnect_wahoo():
        """Disconnect from Wahoo API (revoke tokens)."""
        # In a real implementation, you'd revoke the stored tokens
        return {"success": True, "message": "Disconnected from Wahoo Cloud API"}

    @router.get("/test")
    async def test_wahoo_api():
        """Test Wahoo API connection."""
        # In a real implementation, you'd use stored tokens to make a test API call
        return {
            "status": "not_implemented",
            "message": "Wahoo API test not yet implemented",
            "endpoints_available": [
                "GET /users/me",
                "GET /workouts",
                "GET /workout_summaries",
                "GET /plans",
                "GET /routes",
            ],
        }

    return router
