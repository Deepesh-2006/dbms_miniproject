from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class VehicleIn(BaseModel):
    registration_number: str = Field(pattern=r"^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$")
    vehicle_type_id: int
    branch_id: int
    chassis_number: str = Field(min_length=5, max_length=30)
    purchase_date: date
    current_odometer: Decimal = Field(ge=0)
    status: str = "active"


class VehicleOut(VehicleIn, ORMModel):
    vehicle_id: int
    next_service_date: date | None = None
    next_service_odometer: Decimal | None = None


class DriverIn(BaseModel):
    branch_id: int
    full_name: str = Field(min_length=3, max_length=120)
    license_number: str = Field(min_length=5, max_length=30)
    license_expiry: date
    joining_date: date
    phone: str = Field(min_length=10, max_length=20)
    status: str = "active"

    @model_validator(mode="after")
    def dates_are_valid(self):
        if self.license_expiry <= self.joining_date:
            raise ValueError("license expiry must be after joining date")
        return self


class DriverOut(DriverIn, ORMModel):
    driver_id: int


class RouteIn(BaseModel):
    route_name: str
    origin: str
    destination: str
    planned_distance_km: Decimal = Field(gt=0)
    estimated_duration_minutes: int = Field(gt=0)


class RouteOut(RouteIn, ORMModel):
    route_id: int


class TripIn(BaseModel):
    vehicle_id: int
    driver_id: int
    route_id: int
    start_time: datetime
    end_time: datetime | None = None
    start_odometer: Decimal = Field(ge=0)
    end_odometer: Decimal | None = Field(default=None, ge=0)
    status: str = "planned"
    notes: str | None = None

    @model_validator(mode="after")
    def validate_completion(self):
        if self.end_time and self.end_time < self.start_time:
            raise ValueError("end time cannot precede start time")
        if self.end_odometer is not None and self.end_odometer < self.start_odometer:
            raise ValueError("end odometer cannot be lower than start odometer")
        if self.status == "completed" and (self.end_time is None or self.end_odometer is None):
            raise ValueError("completed trips require end time and end odometer")
        return self


class TripOut(TripIn, ORMModel):
    trip_id: int


class FuelIn(BaseModel):
    vehicle_id: int
    driver_id: int | None = None
    transaction_date: date
    fuel_type: str
    litres: Decimal = Field(gt=0)
    price_per_litre: Decimal = Field(gt=0)
    odometer: Decimal = Field(ge=0)
    fuel_station: str


class FuelOut(FuelIn, ORMModel):
    fuel_transaction_id: int
    total_cost: Decimal


class MaintenanceIn(BaseModel):
    vehicle_id: int
    maintenance_type_id: int
    service_center_id: int
    service_date: date
    odometer: Decimal = Field(ge=0)
    cost: Decimal = Field(ge=0)
    description: str | None = None
    next_service_date: date | None = None
    next_service_odometer: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def next_service_is_valid(self):
        if self.next_service_date and self.next_service_date < self.service_date:
            raise ValueError("next service date cannot precede service date")
        if self.next_service_odometer and self.next_service_odometer < self.odometer:
            raise ValueError("next service odometer cannot be lower than current")
        return self


class MaintenanceOut(MaintenanceIn, ORMModel):
    maintenance_id: int


class AccidentIn(BaseModel):
    vehicle_id: int
    driver_id: int | None = None
    accident_date: date
    location: str
    severity: str
    estimated_damage: Decimal = Field(ge=0)
    description: str


class AccidentOut(AccidentIn, ORMModel):
    accident_id: int


class InsuranceIn(BaseModel):
    vehicle_id: int
    provider: str
    policy_number: str
    start_date: date
    expiry_date: date
    premium: Decimal = Field(ge=0)
    coverage_amount: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def policy_dates_are_valid(self):
        if self.expiry_date <= self.start_date:
            raise ValueError("insurance expiry must be after start date")
        return self


class InsuranceOut(InsuranceIn, ORMModel):
    insurance_id: int


class ExpenseIn(BaseModel):
    vehicle_id: int
    expense_date: date
    category: str
    amount: Decimal = Field(ge=0)
    description: str | None = None


class ExpenseOut(ExpenseIn, ORMModel):
    expense_id: int


class Paginated(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int
