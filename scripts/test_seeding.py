#!/usr/bin/env python3
"""
Test script for the database seeding functionality.

This script tests the GPX generation and database seeding with a small number of segments.
"""

import asyncio
import logging

# Add the backend src directory to the Python path
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "backend" / "src"))

from database_seeding import seed_database

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_seeding():
    """Test the database seeding with a small number of segments."""
    logger.info("Starting test seeding with 5 segments")

    try:
        await seed_database(num_segments=5, target_distance_km=5.0, batch_size=2)
        logger.info("Test seeding completed successfully!")
    except Exception as e:
        logger.error(f"Test seeding failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_seeding())
