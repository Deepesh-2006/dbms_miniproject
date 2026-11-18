"""Integration tests. Start the compose database before running: pytest tests -q."""
from datetime import date, datetime, timezone
from decimal import Decimal
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def auth_headers():
    response = client.post("/api/auth/login", json={"username": "admin", "password": "Fleet@123"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_authentication_and_dashboard():
    headers = auth_headers()
    response = client.get("/api/analytics/dashboard", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["total_vehicles"] >= 50
    assert len(body["monthly_fuel"]) > 0


def test_vehicle_creation_and_unique_registration():
    headers = auth_headers()
    registration = "KA99ZZ9999"
    payload = {"registration_number": registration, "vehicle_type_id": 1, "branch_id": 1,
               "chassis_number": "TESTCHASSIS9999", "purchase_date": "2026-08-01", "current_odometer": 100}
    created = client.post("/api/vehicles", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    duplicate = client.post("/api/vehicles", json=payload, headers=headers)
    assert duplicate.status_code == 409
    assert client.delete(f"/api/vehicles/{created.json()['vehicle_id']}", headers=headers).status_code == 204


def test_trip_rejects_bad_odometer_and_expired_insurance():
    headers = auth_headers()
    bad_odo = {"vehicle_id": 1, "driver_id": 1, "route_id": 1, "start_time": "2026-08-20T06:00:00+05:30",
               "end_time": "2026-08-20T10:00:00+05:30", "start_odometer": 500, "end_odometer": 499, "status": "completed"}
    assert client.post("/api/trips", json=bad_odo, headers=headers).status_code == 422
    expired = {"vehicle_id": 5, "driver_id": 5, "route_id": 1, "start_time": "2026-10-20T06:00:00+05:30",
               "end_time": "2026-10-20T10:00:00+05:30", "start_odometer": 30000, "end_odometer": 30100, "status": "completed"}
    response = client.post("/api/trips", json=expired, headers=headers)
    assert response.status_code == 422
    assert "insurance" in response.json()["detail"].lower()


def test_fuel_and_maintenance_constraints():
    headers = auth_headers()
    fuel = {"vehicle_id": 1, "driver_id": 1, "transaction_date": "2026-12-01", "fuel_type": "Diesel",
            "litres": 0, "price_per_litre": 92, "odometer": 99999, "fuel_station": "Test Station"}
    assert client.post("/api/fuel", json=fuel, headers=headers).status_code == 422
    maintenance = {"vehicle_id": 1, "maintenance_type_id": 1, "service_center_id": 1, "service_date": "2026-12-01",
                   "odometer": 99999, "cost": 5000, "next_service_date": "2026-11-01"}
    assert client.post("/api/maintenance", json=maintenance, headers=headers).status_code == 422
