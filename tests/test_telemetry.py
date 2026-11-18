"""Redis telemetry tests (create/read/update/delete + RBAC). Requires a running Redis."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
VID = 987654


def headers(user, password):
    token = client.post("/api/auth/login", json={"username": user, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_telemetry_crud_and_roles():
    mgr, admin, viewer = headers("manager", "Manager@123"), headers("admin", "Fleet@123"), headers("viewer", "Viewer@123")
    body = {"latitude": 12.97, "longitude": 77.59, "speed_kmph": 50, "fuel_level_pct": 60}
    assert client.put(f"/api/telemetry/{VID}", json=body, headers=viewer).status_code == 403
    assert client.put(f"/api/telemetry/{VID}", json=body, headers=mgr).status_code == 200
    assert client.get(f"/api/telemetry/{VID}", headers=viewer).json()["speed_kmph"] == "50.0"
    assert client.patch(f"/api/telemetry/{VID}", json={"speed_kmph": 75}, headers=mgr).json()["speed_kmph"] == "75.0"
    near = client.get("/api/telemetry/nearby/search", params={"latitude": 12.9, "longitude": 77.6, "radius_km": 30}, headers=viewer).json()
    assert any(r["vehicle_id"] == VID for r in near)
    assert client.delete(f"/api/telemetry/{VID}", headers=mgr).status_code == 403
    assert client.delete(f"/api/telemetry/{VID}", headers=admin).status_code == 204
    assert client.get(f"/api/telemetry/{VID}", headers=admin).status_code == 404


def test_telemetry_validation():
    mgr = headers("manager", "Manager@123")
    bad = {"latitude": 120, "longitude": 77, "speed_kmph": 50, "fuel_level_pct": 60}
    assert client.put(f"/api/telemetry/{VID}", json=bad, headers=mgr).status_code == 422
