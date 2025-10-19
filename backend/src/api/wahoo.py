"""Wahoo API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Query

from src.dependencies import get_wahoo_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wahoo", tags=["wahoo"])


def create_wahoo_router() -> APIRouter:
    """Create Wahoo router with dependencies."""

    @router.get("/authorization-url")
    async def get_authorization_url():
        """Get Wahoo OAuth authorization URL."""
        try:
            wahoo_service = get_wahoo_service()
            auth_url = wahoo_service.get_authorization_url()

            logger.info("Generated Wahoo authorization URL")

            return {
                "authorization_url": auth_url,
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Error generating Wahoo authorization URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate authorization URL: {str(e)}",
            )

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
            print(f"Wahoo authorization code: {code}")

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
