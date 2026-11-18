from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, Computed
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Manufacturer(Base):
    __tablename__ = "manufacturers"
    manufacturer_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    country: Mapped[str] = mapped_column(String(60))


class VehicleType(Base):
    __tablename__ = "vehicle_types"
    vehicle_type_id: Mapped[int] = mapped_column(primary_key=True)
    manufacturer_id: Mapped[int] = mapped_column(ForeignKey("manufacturers.manufacturer_id"))
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(40))
    default_fuel_type: Mapped[str] = mapped_column(String(30))
    expected_kmpl: Mapped[Decimal] = mapped_column(Numeric(5, 2))


class Branch(Base):
    __tablename__ = "branches"
    branch_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(20))


class Vehicle(Base):
    __tablename__ = "vehicles"
    vehicle_id: Mapped[int] = mapped_column(primary_key=True)
    registration_number: Mapped[str] = mapped_column(String(15), unique=True)
    vehicle_type_id: Mapped[int] = mapped_column(ForeignKey("vehicle_types.vehicle_type_id"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.branch_id"))
    chassis_number: Mapped[str] = mapped_column(String(30), unique=True)
    purchase_date: Mapped[date] = mapped_column(Date)
    current_odometer: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    next_service_date: Mapped[date | None] = mapped_column(Date)
    next_service_odometer: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(Enum("active", "maintenance", "inactive", "retired", name="vehicle_status", create_type=False))


class Driver(Base):
    __tablename__ = "drivers"
    driver_id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.branch_id"))
    full_name: Mapped[str] = mapped_column(String(120))
    license_number: Mapped[str] = mapped_column(String(30), unique=True)
    license_expiry: Mapped[date] = mapped_column(Date)
    joining_date: Mapped[date] = mapped_column(Date)
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    status: Mapped[str] = mapped_column(Enum("active", "on_leave", "inactive", name="driver_status", create_type=False))


class Route(Base):
    __tablename__ = "routes"
    route_id: Mapped[int] = mapped_column(primary_key=True)
    route_name: Mapped[str] = mapped_column(String(120), unique=True)
    origin: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(100))
    planned_distance_km: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estimated_duration_minutes: Mapped[int]


class Trip(Base):
    __tablename__ = "trips"
    trip_id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.driver_id"))
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.route_id"))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    start_odometer: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    end_odometer: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(Enum("planned", "in_progress", "completed", "cancelled", name="trip_status", create_type=False))
    notes: Mapped[str | None] = mapped_column(Text)


class FuelTransaction(Base):
    __tablename__ = "fuel_transactions"
    fuel_transaction_id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"))
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.driver_id"))
    transaction_date: Mapped[date] = mapped_column(Date)
    fuel_type: Mapped[str] = mapped_column(String(30))
    litres: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    price_per_litre: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), Computed("ROUND(litres * price_per_litre, 2)"))
    odometer: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fuel_station: Mapped[str] = mapped_column(String(140))


class Maintenance(Base):
    __tablename__ = "maintenance"
    maintenance_id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"))
    maintenance_type_id: Mapped[int] = mapped_column(ForeignKey("maintenance_types.maintenance_type_id"))
    service_center_id: Mapped[int] = mapped_column(ForeignKey("service_centers.service_center_id"))
    service_date: Mapped[date] = mapped_column(Date)
    odometer: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str | None] = mapped_column(Text)
    next_service_date: Mapped[date | None] = mapped_column(Date)
    next_service_odometer: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))


class Accident(Base):
    __tablename__ = "accidents"
    accident_id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"))
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.driver_id"))
    accident_date: Mapped[date] = mapped_column(Date)
    location: Mapped[str] = mapped_column(String(180))
    severity: Mapped[str] = mapped_column(Enum("minor", "moderate", "major", "critical", name="accident_severity", create_type=False))
    estimated_damage: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str] = mapped_column(Text)


class Insurance(Base):
    __tablename__ = "insurance"
    insurance_id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"))
    provider: Mapped[str] = mapped_column(String(100))
    policy_number: Mapped[str] = mapped_column(String(60), unique=True)
    start_date: Mapped[date] = mapped_column(Date)
    expiry_date: Mapped[date] = mapped_column(Date)
    premium: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    coverage_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))


class Expense(Base):
    __tablename__ = "expenses"
    expense_id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.vehicle_id"))
    expense_date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str | None] = mapped_column(Text)


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean)
