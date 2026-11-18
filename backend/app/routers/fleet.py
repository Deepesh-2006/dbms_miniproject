from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Accident, Branch, Driver, Expense, FuelTransaction, Insurance, Maintenance, Manufacturer, Route, Trip, Vehicle, VehicleType
from app.routers.crud import create_crud_router, serialize
from app.schemas import AccidentIn, DriverIn, ExpenseIn, FuelIn, InsuranceIn, MaintenanceIn, RouteIn, TripIn, VehicleIn
from app.security import allow_roles, current_user
from app.services import create_trip

router = APIRouter()
router.include_router(create_crud_router(Vehicle, VehicleIn, "vehicle_id", "/vehicles", "registration_number"))
router.include_router(create_crud_router(Driver, DriverIn, "driver_id", "/drivers", "full_name"))
router.include_router(create_crud_router(Route, RouteIn, "route_id", "/routes", "route_name"))
router.include_router(create_crud_router(FuelTransaction, FuelIn, "fuel_transaction_id", "/fuel", "fuel_station"))
router.include_router(create_crud_router(Maintenance, MaintenanceIn, "maintenance_id", "/maintenance"))
router.include_router(create_crud_router(Accident, AccidentIn, "accident_id", "/accidents", "location"))
router.include_router(create_crud_router(Insurance, InsuranceIn, "insurance_id", "/insurance", "policy_number"))
router.include_router(create_crud_router(Expense, ExpenseIn, "expense_id", "/expenses"))


@router.post("/trips", status_code=201, tags=["trips"])
def add_trip(payload: TripIn, db: Session = Depends(get_db), _=Depends(allow_roles("admin", "fleet_manager"))):
    try:
        return serialize(create_trip(db, payload))
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(422, "Trip violates a database validation rule") from exc


@router.get("/trips", tags=["trips"])
def list_trips(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), _=Depends(current_user)):
    rows = db.execute(text("""SELECT t.*,v.registration_number,d.full_name,r.route_name,
       CASE WHEN t.end_odometer IS NULL THEN NULL ELSE t.end_odometer-t.start_odometer END distance_km
       FROM trips t JOIN vehicles v ON v.vehicle_id=t.vehicle_id JOIN drivers d ON d.driver_id=t.driver_id JOIN routes r ON r.route_id=t.route_id
       ORDER BY t.start_time DESC OFFSET :offset LIMIT :limit"""), {"offset": (page-1)*page_size, "limit": page_size}).mappings().all()
    total = db.execute(text("SELECT count(*) FROM trips")).scalar_one()
    return {"items": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/trips/{trip_id}", tags=["trips"])
def get_trip(trip_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    trip = db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(404, "Trip not found")
    return serialize(trip)


@router.put("/trips/{trip_id}", tags=["trips"])
def update_trip(trip_id: int, payload: TripIn, db: Session = Depends(get_db), _=Depends(allow_roles("admin", "fleet_manager"))):
    trip = db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(404, "Trip not found")
    # Reuse atomic validation for status changes by updating and flushing in one session.
    for key, value in payload.model_dump().items():
        setattr(trip, key, value)
    try:
        db.flush()
        db.commit()
        db.refresh(trip)
        return serialize(trip)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(422, "Trip violates a database validation rule") from exc


@router.delete("/trips/{trip_id}", status_code=204, tags=["trips"])
def delete_trip(trip_id: int, db: Session = Depends(get_db), _=Depends(allow_roles("admin"))):
    trip = db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(404, "Trip not found")
    db.delete(trip)
    db.commit()


@router.get("/catalog", tags=["catalog"])
def catalog(db: Session = Depends(get_db), _=Depends(current_user)):
    """Lookup data for frontend forms without hard-coded identifiers."""
    return {"manufacturers": [serialize(x) for x in db.query(Manufacturer).all()],
            "vehicle_types": [serialize(x) for x in db.query(VehicleType).all()],
            "branches": [serialize(x) for x in db.query(Branch).all()],
            "drivers": [serialize(x) for x in db.query(Driver).filter(Driver.status == "active").all()],
            "vehicles": [serialize(x) for x in db.query(Vehicle).filter(Vehicle.status == "active").all()],
            "routes": [serialize(x) for x in db.query(Route).all()]}


@router.get("/vehicles/{vehicle_id}/details", tags=["vehicles"])
def vehicle_details(vehicle_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")
    cost = db.execute(text("SELECT * FROM vehicle_operating_cost(:id)"), {"id": vehicle_id}).mappings().one()
    return {"vehicle": serialize(vehicle), "cost": dict(cost),
            "trips": [dict(r) for r in db.execute(text("SELECT * FROM trips WHERE vehicle_id=:id ORDER BY start_time DESC LIMIT 10"), {"id": vehicle_id}).mappings()],
            "fuel": [dict(r) for r in db.execute(text("SELECT * FROM fuel_transactions WHERE vehicle_id=:id ORDER BY transaction_date DESC LIMIT 10"), {"id": vehicle_id}).mappings()],
            "maintenance": [dict(r) for r in db.execute(text("SELECT * FROM maintenance WHERE vehicle_id=:id ORDER BY service_date DESC LIMIT 10"), {"id": vehicle_id}).mappings()]}
