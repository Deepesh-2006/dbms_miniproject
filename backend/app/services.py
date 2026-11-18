from datetime import date
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Driver, Insurance, Trip, Vehicle
from app.schemas import TripIn


def create_trip(db: Session, payload: TripIn) -> Trip:
    """A single transaction: all checks pass or no trip is persisted."""
    vehicle = db.get(Vehicle, payload.vehicle_id)
    driver = db.get(Driver, payload.driver_id)
    if not vehicle or vehicle.status != "active":
        raise HTTPException(422, "Vehicle does not exist or is not active")
    if not driver or driver.status != "active":
        raise HTTPException(422, "Driver does not exist or is not active")
    valid_policy = db.scalar(select(Insurance.insurance_id).where(
        Insurance.vehicle_id == payload.vehicle_id,
        Insurance.start_date <= payload.start_time.date(),
        Insurance.expiry_date >= payload.start_time.date(),
    ))
    if not valid_policy:
        raise HTTPException(422, "Vehicle insurance is invalid for the trip date")
    trip = Trip(**payload.model_dump())
    try:
        db.add(trip)
        db.flush()  # executes database insurance / odometer triggers before commit
        db.commit()
        db.refresh(trip)
        return trip
    except Exception:
        db.rollback()
        raise
