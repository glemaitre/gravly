#!/usr/bin/env python3
"""
Setup script for Elasticsearch index and mock data
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from main import es, index_gpx_file


async def setup_elasticsearch():
    """Setup Elasticsearch index and load mock data"""
    print("Setting up Elasticsearch...")

    try:
        # Create index if it doesn't exist
        if not await es.indices.exists(index="gpx_tracks"):
            print("Creating gpx_tracks index...")
            await es.indices.create(
                index="gpx_tracks",
                body={
                    "mappings": {
                        "properties": {
                            "name": {"type": "text"},
                            "distance": {"type": "float"},
                            "elevation_gain": {"type": "float"},
                            "elevation_loss": {"type": "float"},
                            "bounds": {"type": "object"},
                            "points": {"type": "nested"},
                            "created_at": {"type": "date"},
                        }
                    }
                },
            )
            print("Index created successfully!")
        else:
            print("Index already exists!")

        # Load mock GPX files
        mock_dir = Path(__file__).parent.parent / "mock_gpx"
        if mock_dir.exists():
            print(f"Loading mock GPX files from {mock_dir}...")
            for gpx_file in mock_dir.glob("*.gpx"):
                print(f"Processing {gpx_file.name}...")
                file_id = gpx_file.stem
                result = await index_gpx_file(str(gpx_file), file_id)
                if result:
                    print(f"✓ Successfully indexed {gpx_file.name}")
                else:
                    print(f"✗ Failed to index {gpx_file.name}")
        else:
            print("No mock_gpx directory found!")

        print("Setup complete!")
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(setup_elasticsearch())
