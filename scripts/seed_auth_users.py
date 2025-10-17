#!/usr/bin/env python3
"""
Database Seeding Script for Authorized Strava Users

This script seeds the database with authorized Strava users who have access
to the editor feature. The authorized users are defined in a configuration file.

Usage:
    pixi run python scripts/seed_auth_users.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the backend src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "backend" / "src"))

from models.auth_user import AuthUser
from models.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from utils.config import load_environment_config
from utils.postgres import get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def seed_authorized_users():
    """Seed database with authorized Strava users."""
    logger.info("Starting authorized users seeding script")

    # Load configuration
    try:
        db_config, storage_config, strava_config, map_config, server_config = (
            load_environment_config()
        )
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    # Initialize database
    database_url = get_database_url(
        host=db_config.host,
        port=db_config.port,
        database=db_config.name,
        username=db_config.user,
        password=db_config.password,
    )

    engine = create_async_engine(database_url, echo=False, future=True)
    SessionLocal = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    try:
        # Ensure database tables exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured")

        # Load authorized users from environment variable
        auth_users_env_str = os.getenv("AUTHORIZED_STRAVA_USERS", "")
        if not auth_users_env_str.strip():
            logger.error(
                "No authorized users found in AUTHORIZED_STRAVA_USERS environment variable"
            )
            logger.error(
                "Please set AUTHORIZED_STRAVA_USERS in your .env/auth_users file"
            )
            return

        auth_users_to_add = []
        for user_str in auth_users_env_str.split(","):
            user_str = user_str.strip()
            if user_str:
                try:
                    strava_id = int(user_str)
                    auth_users_to_add.append(
                        {
                            "strava_id": strava_id,
                            "firstname": None,
                            "lastname": None,
                        }
                    )
                    logger.info(
                        f"Will seed authorized user with Strava ID: {strava_id}"
                    )
                except ValueError:
                    logger.warning(f"Invalid Strava ID format: {user_str}")
                    continue

        if not auth_users_to_add:
            logger.error("No valid Strava IDs found to seed")
            return

        async with SessionLocal() as session:
            for user_data in auth_users_to_add:
                try:
                    # Check if user already exists
                    from sqlalchemy import select

                    existing_user = await session.execute(
                        select(AuthUser).where(
                            AuthUser.strava_id == user_data["strava_id"]
                        )
                    )
                    existing = existing_user.scalar_one_or_none()

                    if existing:
                        logger.info(
                            f"Authorized user {user_data['strava_id']} already exists, skipping"
                        )
                        continue

                    # Create new authorized user
                    auth_user = AuthUser(**user_data)
                    session.add(auth_user)
                    logger.info(
                        f"Added authorized user with Strava ID: {user_data['strava_id']}"
                    )
                except Exception as e:
                    logger.error(f"Failed to add user {user_data}: {e}")
                    continue

            # Commit all changes
            await session.commit()
            logger.info(
                f"Successfully seeded {len(auth_users_to_add)} authorized users"
            )

    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise
    finally:
        await engine.dispose()


async def main():
    """Main function to run the authorized users seeding."""
    logger.info("Starting authorized Strava users database seeding script")

    try:
        await seed_authorized_users()
        logger.info("Authorized users database seeding completed successfully!")
    except Exception as e:
        logger.error(f"Authorized users database seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
