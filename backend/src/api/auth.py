"""Authentication API endpoints."""

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models.auth_user import AuthUser, AuthUserResponse, AuthUserSummary

logger = logging.getLogger(__name__)


def create_auth_router(
    session_local: async_sessionmaker[AsyncSession] | None,
) -> APIRouter:
    """Create and configure the authentication router.

    Parameters
    ----------
    session_local : Optional[async_sessionmaker[AsyncSession]]
        Database session factory, can be None for testing

    Returns
    -------
    APIRouter
        Configured FastAPI router with auth endpoints
    """
    router = APIRouter(prefix="/api/auth", tags=["auth"])

    @router.get("/check-authorization")
    async def check_strava_authorization(strava_id: int):
        """Check if a Strava user is authorized to access editor feature."""
        # Import global SessionLocal from main
        from ..main import SessionLocal as global_session_local

        if global_session_local is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with global_session_local() as session:
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

    @router.get("/users", response_model=list[AuthUserResponse])
    async def list_authorized_users():
        """List all authorized users (admin function)."""
        # Import global SessionLocal from main
        from ..main import SessionLocal as global_session_local

        if global_session_local is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        try:
            async with global_session_local() as session:
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
            raise HTTPException(
                status_code=500, detail=f"Failed to list users: {str(e)}"
            )

    return router
