import asyncio
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


class FakeIndices:
    def __init__(self):
        self._exists = True
        self.created_called_with: dict[str, Any] | None = None

    async def exists(self, index: str) -> bool:  # noqa: D401
        return self._exists

    async def create(self, index: str, body: dict[str, Any]):  # noqa: D401
        self._exists = True
        self.created_called_with = {"index": index, "body": body}
        return {"acknowledged": True}


class FakeElasticsearch:
    def __init__(self):
        self.indices = FakeIndices()
        self._docs: dict[str, dict[str, Any]] = {}
        self._available = True
        self.last_search_body: dict[str, Any] | None = None

    def set_available(self, available: bool) -> None:
        self._available = available

    async def ping(self) -> bool:
        if not self._available:
            raise RuntimeError("ES unavailable")
        return True

    async def index(self, index: str, id: str, body: dict[str, Any]):  # noqa: A003
        self._docs[id] = body
        return {"result": "created"}

    async def search(self, index: str, body: dict[str, Any]):
        self.last_search_body = body
        hits: list[dict[str, Any]] = []
        for doc_id, source in self._docs.items():
            hits.append({"_id": doc_id, "_source": source})
        return {"hits": {"hits": hits}}

    async def get(self, index: str, id: str):  # noqa: A003
        if id not in self._docs:
            raise KeyError("not found")
        return {"_source": self._docs[id]}


def get_app_and_es(monkeypatch):
    # Import the backend app
    from src import main as backend_main

    fake_es = FakeElasticsearch()

    # Replace Elasticsearch client
    monkeypatch.setattr(backend_main, "es", fake_es, raising=True)

    # Prevent loading mock GPX data during startup
    monkeypatch.setattr("src.main.Path.exists", lambda self: False)

    return backend_main.app, fake_es


def test_root(monkeypatch):
    app, _ = get_app_and_es(monkeypatch)
    with TestClient(app) as client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"message": "Cycling GPX API"}


def test_search_rides_no_filters(monkeypatch):
    app, fake_es = get_app_and_es(monkeypatch)

    # Seed some docs
    # Minimal document fields used by the API
    fake_doc = {
        "name": "City Ride",
        "distance": 12.3,
        "elevation_gain": 210.0,
        "elevation_loss": 200.0,
        "bounds": {"north": 1, "south": 0, "east": 1, "west": 0},
        "points": [{"lat": 0.0, "lon": 0.0, "elevation": 0.0}],
    }

    # Index is async; call via helper
    asyncio.run(fake_es.index(index="gpx_tracks", id="ride-1", body=fake_doc))

    with TestClient(app) as client:
        resp = client.get("/api/rides")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "ride-1"
        assert data[0]["name"] == "City Ride"


def test_get_ride_success(monkeypatch):
    app, fake_es = get_app_and_es(monkeypatch)

    fake_doc = {
        "name": "Alps Tour",
        "distance": 101.5,
        "elevation_gain": 2500.0,
        "elevation_loss": 2500.0,
        "bounds": {"north": 46.0, "south": 45.0, "east": 7.5, "west": 6.0},
        "points": [
            {"lat": 45.1, "lon": 6.1, "elevation": 1000.0},
            {"lat": 45.2, "lon": 6.2, "elevation": 1100.0},
        ],
    }

    asyncio.run(fake_es.index(index="gpx_tracks", id="alps", body=fake_doc))

    with TestClient(app) as client:
        resp = client.get("/api/rides/alps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Alps Tour"
        assert data["total_distance"] == 101.5
        assert len(data["points"]) == 2


def test_get_ride_not_found(monkeypatch):
    app, _ = get_app_and_es(monkeypatch)
    with TestClient(app) as client:
        resp = client.get("/api/rides/missing")
        assert resp.status_code == 404


def test_elasticsearch_unavailable(monkeypatch):
    app, fake_es = get_app_and_es(monkeypatch)
    fake_es.set_available(False)

    with TestClient(app) as client:
        resp = client.get("/api/rides")
        assert resp.status_code == 503


def test_search_rides_builds_filters(monkeypatch):
    app, fake_es = get_app_and_es(monkeypatch)
    with TestClient(app) as client:
        resp = client.get(
            "/api/rides",
            params={
                "bounds": '{"north":2,"south":1,"east":2,"west":1}',
                "min_distance": 10,
                "max_distance": 100,
                "min_elevation": 200,
                "max_elevation": 1000,
            },
        )
        assert resp.status_code == 200
        assert fake_es.last_search_body is not None
        query = fake_es.last_search_body.get("query", {})
        assert "bool" in query and "must" in query["bool"]
        # Ensure both range filters are present
        must = query["bool"]["must"]
        assert any("range" in f and "distance" in f["range"] for f in must)
        assert any("range" in f and "elevation_gain" in f["range"] for f in must)


def test_parse_gpx_file_success(tmp_path, monkeypatch):
    from src.main import parse_gpx_file

    # Minimal GPX content with a track and two points
    gpx_content = """
    <gpx version="1.1" creator="test">
      <trk><name>Test Track</name><trkseg>
        <trkpt lat="45.0" lon="6.0"><ele>1000</ele></trkpt>
        <trkpt lat="45.001" lon="6.001"><ele>1010</ele></trkpt>
      </trkseg></trk>
    </gpx>
    """.strip()

    gpx_file = tmp_path / "test.gpx"
    gpx_file.write_text(gpx_content)

    track = parse_gpx_file(str(gpx_file))
    assert track.name == "Test Track"
    assert len(track.points) == 2
    assert track.total_elevation_gain >= 10
    assert track.total_elevation_loss == 0
    assert track.bounds["north"] >= track.bounds["south"]
    assert track.bounds["east"] >= track.bounds["west"]


def test_parse_gpx_file_no_tracks(tmp_path):
    from src.main import parse_gpx_file

    gpx_content = """
    <gpx version="1.1" creator="test">
    </gpx>
    """.strip()
    gpx_file = tmp_path / "empty.gpx"
    gpx_file.write_text(gpx_content)

    try:
        parse_gpx_file(str(gpx_file))
        raise AssertionError("Expected ValueError for no tracks")
    except ValueError as e:
        assert "No tracks found" in str(e)


def test_index_gpx_file_success(monkeypatch, tmp_path):
    from src import main as backend_main

    fake_es = FakeElasticsearch()
    monkeypatch.setattr(backend_main, "es", fake_es, raising=True)

    # Create a GPX file and index it
    gpx_content = """
    <gpx version="1.1" creator="test">
      <trk><name>Seed</name><trkseg>
        <trkpt lat="45.0" lon="6.0"><ele>1000</ele></trkpt>
        <trkpt lat="45.001" lon="6.001"><ele>1010</ele></trkpt>
      </trkseg></trk>
    </gpx>
    """.strip()
    p = tmp_path / "seed.gpx"
    p.write_text(gpx_content)

    track = asyncio.run(backend_main.index_gpx_file(str(p), "seed"))
    assert track is not None
    assert "seed" in fake_es._docs


def test_index_gpx_file_failure(monkeypatch):
    from src import main as backend_main

    fake_es = FakeElasticsearch()
    monkeypatch.setattr(backend_main, "es", fake_es, raising=True)

    # Non-existing file should lead to graceful None
    track = asyncio.run(backend_main.index_gpx_file("/no/such/file.gpx", "bad"))
    assert track is None


def test_lifespan_creates_index_and_loads_mock(monkeypatch):
    # Prepare app import with mocked conditions before TestClient creation
    from src import main as backend_main

    fake_es = FakeElasticsearch()
    fake_es.indices._exists = False

    # Capture calls to index_gpx_file
    async def fake_index_gpx_file(file_path: str, file_id: str):
        fake_es._docs[file_id] = {"name": "from-mock", "points": []}
        return None

    monkeypatch.setattr(backend_main, "es", fake_es, raising=True)
    monkeypatch.setattr(
        backend_main, "index_gpx_file", fake_index_gpx_file, raising=True
    )
    monkeypatch.setattr("src.main.Path.exists", lambda self: True)
    monkeypatch.setattr("src.main.Path.iterdir", lambda self: [Path("mock1.gpx")])

    with TestClient(backend_main.app):
        pass

    # Assert index creation happened
    assert fake_es.indices.created_called_with is not None
    # Assert mock loader attempted indexing
    assert "mock1" in fake_es._docs


def test_parse_gpx_file_elevation_loss(tmp_path):
    from src.main import parse_gpx_file

    gpx_content = """
    <gpx version=\"1.1\" creator=\"test\">
      <trk><name>Desc Test</name><trkseg>
        <trkpt lat=\"45.0\" lon=\"6.0\"><ele>1010</ele></trkpt>
        <trkpt lat=\"45.001\" lon=\"6.001\"><ele>1000</ele></trkpt>
      </trkseg></trk>
    </gpx>
    """.strip()
    p = tmp_path / "desc.gpx"
    p.write_text(gpx_content)

    track = parse_gpx_file(str(p))
    assert track.total_elevation_loss > 0


def test_search_rides_invalid_bounds_json(monkeypatch):
    app, fake_es = get_app_and_es(monkeypatch)
    with TestClient(app) as client:
        resp = client.get("/api/rides", params={"bounds": "not a json"})
        assert resp.status_code == 200
        # Should still perform a search
        assert fake_es.last_search_body is not None


def test_search_rides_es_error_returns_500(monkeypatch):
    app, fake_es = get_app_and_es(monkeypatch)

    async def raise_on_search(index: str, body: dict[str, Any]):
        raise RuntimeError("boom")

    # Monkeypatch the method on the instance
    fake_es.search = raise_on_search  # type: ignore[assignment]

    with TestClient(app) as client:
        resp = client.get("/api/rides")
        assert resp.status_code == 500


def test_get_ride_ping_unavailable(monkeypatch):
    app, fake_es = get_app_and_es(monkeypatch)
    fake_es.set_available(False)

    with TestClient(app) as client:
        resp = client.get("/api/rides/any")
        assert resp.status_code == 503


def test_main_guard_invokes_uvicorn(monkeypatch):
    # Ensure running module as __main__ calls uvicorn.run without warnings
    called = {"value": False}

    def fake_run(app, host: str, port: int):  # noqa: D401
        called["value"] = True

    import runpy
    import sys
    import types

    # Remove cached module to avoid RuntimeWarning from runpy
    sys.modules.pop("src.main", None)

    # Provide a fake uvicorn before executing module
    fake_uvicorn = types.SimpleNamespace(run=fake_run)
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    # Execute module as if run directly
    runpy.run_module("src.main", run_name="__main__")
    assert called["value"] is True
