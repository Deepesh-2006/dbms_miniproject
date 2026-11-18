from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app import nosql
from app.security import current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


def rows(db: Session, sql: str):
    return [dict(r) for r in db.execute(text(sql)).mappings().all()]


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(current_user)):
    cached = nosql.cache_get("cache:dashboard")
    if cached:
        return cached
    result = _dashboard(db)
    nosql.cache_set("cache:dashboard", result, ttl=60)
    return result


def _dashboard(db: Session):
    metrics = db.execute(text("""SELECT (SELECT count(*) FROM vehicles) total_vehicles,
      (SELECT count(*) FROM vehicles WHERE status='active') active_vehicles,
      (SELECT count(*) FROM vehicles WHERE status='maintenance') vehicles_under_maintenance,
      (SELECT count(*) FROM drivers WHERE status='active') active_drivers,
      (SELECT count(*) FROM trips WHERE status='completed') completed_trips,
      (SELECT COALESCE(sum(total_cost),0) FROM fuel_transactions) total_fuel_cost,
      (SELECT COALESCE(sum(cost),0) FROM maintenance) total_maintenance_cost,
      (SELECT COALESCE(sum(total_operating_cost),0) FROM vehicle_cost_view) total_operating_cost""")).mappings().one()
    return {"metrics": dict(metrics),
      "monthly_fuel": rows(db, "SELECT to_char(transaction_date,'Mon') AS month, date_trunc('month',transaction_date) sort, sum(total_cost) value FROM fuel_transactions GROUP BY 1,2 ORDER BY 2"),
      "monthly_maintenance": rows(db, "SELECT to_char(service_date,'Mon') AS month, date_trunc('month',service_date) sort, sum(cost) value FROM maintenance GROUP BY 1,2 ORDER BY 2"),
      "utilization": rows(db, "SELECT registration_number name,total_distance value FROM vehicle_performance_view ORDER BY value DESC LIMIT 8"),
      "fuel_efficiency": rows(db, "SELECT registration_number name,fuel_efficiency_kmpl value FROM vehicle_performance_view WHERE fuel_efficiency_kmpl IS NOT NULL ORDER BY value LIMIT 10"),
      "route_trips": rows(db, "SELECT r.route_name name,count(t.trip_id) value FROM routes r LEFT JOIN trips t ON t.route_id=r.route_id GROUP BY r.route_name ORDER BY value DESC LIMIT 8"),
      "alerts": rows(db, "SELECT registration_number,service_status,next_service_date,next_service_odometer FROM maintenance_due_view WHERE service_status <> 'scheduled' ORDER BY next_service_date NULLS LAST LIMIT 10"),
      "insurance_alerts": rows(db, "SELECT v.registration_number,i.expiry_date FROM insurance i JOIN vehicles v ON v.vehicle_id=i.vehicle_id WHERE i.expiry_date <= current_date+30 ORDER BY i.expiry_date")}


@router.get("/insights")
def insights(db: Session = Depends(get_db), _=Depends(current_user)):
    return {"high_cost": rows(db, "SELECT registration_number,total_operating_cost FROM vehicle_cost_view ORDER BY total_operating_cost DESC LIMIT 10"),
            "high_maintenance": rows(db, "SELECT v.registration_number,p.maintenance_cost FROM vehicle_performance_view p JOIN vehicles v ON v.vehicle_id=p.vehicle_id WHERE p.maintenance_cost > (SELECT avg(maintenance_cost) FROM vehicle_performance_view) ORDER BY p.maintenance_cost DESC"),
            "poor_efficiency": rows(db, "SELECT registration_number,vehicle_type,fuel_efficiency_kmpl FROM vehicle_performance_view WHERE fuel_efficiency_kmpl < (SELECT avg(fuel_efficiency_kmpl) FROM vehicle_performance_view) ORDER BY fuel_efficiency_kmpl")}
