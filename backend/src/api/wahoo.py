"""Wahoo API endpoints."""

import logging

from fastapi import APIRouter, Form, HTTPException, Query

from src.dependencies import get_wahoo_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wahoo", tags=["wahoo"])


def create_wahoo_router() -> APIRouter:
    """Create Wahoo router with dependencies."""

    @router.get("/auth-url")
    async def get_wahoo_auth_url(state: str = "wahoo_auth"):
        """Get Wahoo OAuth authorization URL"""
        try:
            wahoo_service = get_wahoo_service()

            # Use centralized server configuration for OAuth redirect

            auth_url = wahoo_service.get_authorization_url(state)

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
        try:
            wahoo_service = get_wahoo_service()
            token_response = wahoo_service.exchange_code_for_token(code)
            return {
                "access_token": token_response["access_token"],
                "expires_at": token_response["expires_at"],
            }
        except Exception as e:
            logger.error(f"Error exchanging Wahoo code: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Failed to exchange code: {str(e)}"
            )

    @router.post("/refresh-token")
    async def refresh_wahoo_token():
        """Refresh Wahoo access token using refresh token"""
        try:
            wahoo_service = get_wahoo_service()
            success = wahoo_service.refresh_access_token()
            if success:
                return {"success": True, "message": "Token refreshed successfully"}
            else:
                raise HTTPException(status_code=401, detail="Failed to refresh token")
        except Exception as e:
            logger.error(f"Error refreshing Wahoo token: {str(e)}")
            raise HTTPException(status_code=401, detail="Failed to refresh token")

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

            logger.info(f"Received Wahoo authorization code: {code}")

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

    return router
