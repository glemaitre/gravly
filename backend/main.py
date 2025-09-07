import json
import os
from contextlib import asynccontextmanager
from datetime import datetime

import gpxpy
import uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown."""
    try:
        # Test connection first
        await es.ping()
        print("Connected to Elasticsearch successfully")

        # Create index if it doesn't exist
        if not await es.indices.exists(index="gpx_tracks"):
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
            print("Created gpx_tracks index")

        # Load mock GPX files
        mock_dir = "mock_gpx"
        if os.path.exists(mock_dir):
            for filename in os.listdir(mock_dir):
                if filename.endswith(".gpx"):
                    file_path = os.path.join(mock_dir, filename)
                    file_id = filename.replace(".gpx", "")
                    await index_gpx_file(file_path, file_id)
            print("Loaded mock GPX files")
    except Exception as e:
        print(f"Warning: Could not connect to Elasticsearch: {e}")
        print("Backend will start but search functionality will be limited")

    # Yield control to the application
    yield

    # Shutdown: close Elasticsearch
    try:
        await es.close()
    except Exception:
        pass


app = FastAPI(title="Cycling GPX API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Elasticsearch client
es = AsyncElasticsearch(
    "http://localhost:9200",
    headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"},
)


# Pydantic models
class GPXPoint(BaseModel):
    lat: float
    lon: float
    elevation: float
    time: str | None = None


class GPXTrack(BaseModel):
    name: str
    points: list[GPXPoint]
    total_distance: float
    total_elevation_gain: float
    total_elevation_loss: float
    duration: float | None = None
    bounds: dict


class RideCard(BaseModel):
    id: str
    name: str
    distance: float
    elevation_gain: float
    duration: float | None = None
    bounds: dict
    points: list[dict] | None = []
    thumbnail_url: str | None = None


class RideSearchRequest(BaseModel):
    bounds: dict | None = None
    min_distance: float | None = None
    max_distance: float | None = None
    min_elevation: float | None = None
    max_elevation: float | None = None


def parse_gpx_file(file_path: str) -> GPXTrack:
    """Parse a GPX file and extract track information"""
    with open(file_path) as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    if not gpx.tracks:
        raise ValueError("No tracks found in GPX file")

    track = gpx.tracks[0]
    points = []
    total_distance = 0
    total_elevation_gain = 0
    total_elevation_loss = 0
    prev_elevation = None

    lats = []
    lons = []

    for segment in track.segments:
        for point in segment.points:
            if point.latitude and point.longitude:
                lats.append(point.latitude)
                lons.append(point.longitude)

                elevation = point.elevation or 0
                points.append(
                    GPXPoint(
                        lat=point.latitude,
                        lon=point.longitude,
                        elevation=elevation,
                        time=point.time.isoformat() if point.time else None,
                    )
                )

                if prev_elevation is not None:
                    elevation_diff = elevation - prev_elevation
                    if elevation_diff > 0:
                        total_elevation_gain += elevation_diff
                    else:
                        total_elevation_loss += abs(elevation_diff)

                prev_elevation = elevation

    # Calculate total distance
    for i in range(1, len(points)):
        p1 = points[i - 1]
        p2 = points[i]
        # Simple distance calculation (for more accuracy, use geopy)
        import math

        lat1, lon1 = math.radians(p1.lat), math.radians(p1.lon)
        lat2, lon2 = math.radians(p2.lat), math.radians(p2.lon)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        distance = 6371 * c  # Earth radius in km
        total_distance += distance

    bounds = {"north": max(lats), "south": min(lats), "east": max(lons), "west": min(lons)}

    return GPXTrack(
        name=track.name or "Unnamed Track",
        points=points,
        total_distance=total_distance,
        total_elevation_gain=total_elevation_gain,
        total_elevation_loss=total_elevation_loss,
        bounds=bounds,
    )


async def index_gpx_file(file_path: str, file_id: str):
    """Index a GPX file in Elasticsearch"""
    try:
        track = parse_gpx_file(file_path)

        # Create document for Elasticsearch
        doc = {
            "id": file_id,
            "name": track.name,
            "distance": track.total_distance,
            "elevation_gain": track.total_elevation_gain,
            "elevation_loss": track.total_elevation_loss,
            "bounds": track.bounds,
            "points": [
                {"lat": p.lat, "lon": p.lon, "elevation": p.elevation} for p in track.points
            ],
            "created_at": datetime.now().isoformat(),
        }

        await es.index(index="gpx_tracks", id=file_id, body=doc)
        return track
    except Exception as e:
        print(f"Error indexing {file_path}: {e}")
        return None


@app.get("/")
async def root():
    return {"message": "Cycling GPX API"}


@app.get("/api/rides", response_model=list[RideCard])
async def search_rides(
    bounds: str | None = Query(
        None, description="JSON string with north, south, east, west bounds"
    ),
    min_distance: float | None = None,
    max_distance: float | None = None,
    min_elevation: float | None = None,
    max_elevation: float | None = None,
):
    """Search for rides with optional filters"""
    try:
        # Test Elasticsearch connection
        await es.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="Elasticsearch is not available")

    query = {"match_all": {}}

    filters = []

    if bounds:
        try:
            bounds_data = json.loads(bounds)
            # For now, we'll use a simple bounding box filter on the bounds field
            # In a real implementation, you'd want to index the track points for geo queries
            filters.append(
                {
                    "bool": {
                        "must": [
                            {"range": {"bounds.north": {"lte": bounds_data["north"]}}},
                            {"range": {"bounds.south": {"gte": bounds_data["south"]}}},
                            {"range": {"bounds.east": {"lte": bounds_data["east"]}}},
                            {"range": {"bounds.west": {"gte": bounds_data["west"]}}},
                        ]
                    }
                }
            )
        except:
            pass

    if min_distance is not None or max_distance is not None:
        distance_range = {}
        if min_distance is not None:
            distance_range["gte"] = min_distance
        if max_distance is not None:
            distance_range["lte"] = max_distance
        filters.append({"range": {"distance": distance_range}})

    if min_elevation is not None or max_elevation is not None:
        elevation_range = {}
        if min_elevation is not None:
            elevation_range["gte"] = min_elevation
        if max_elevation is not None:
            elevation_range["lte"] = max_elevation
        filters.append({"range": {"elevation_gain": elevation_range}})

    if filters:
        query = {"bool": {"must": filters}}

    try:
        response = await es.search(index="gpx_tracks", body={"query": query, "size": 100})

        rides = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            rides.append(
                RideCard(
                    id=hit["_id"],
                    name=source["name"],
                    distance=source["distance"],
                    elevation_gain=source["elevation_gain"],
                    bounds=source["bounds"],
                    points=source.get("points", []),
                )
            )

        return rides
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rides/{ride_id}", response_model=GPXTrack)
async def get_ride(ride_id: str):
    """Get detailed information about a specific ride"""
    try:
        # Test Elasticsearch connection
        await es.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="Elasticsearch is not available")

    try:
        response = await es.get(index="gpx_tracks", id=ride_id)
        source = response["_source"]

        points = [GPXPoint(**p) for p in source["points"]]

        return GPXTrack(
            name=source["name"],
            points=points,
            total_distance=source["distance"],
            total_elevation_gain=source["elevation_gain"],
            total_elevation_loss=source["elevation_loss"],
            bounds=source["bounds"],
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Ride not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
