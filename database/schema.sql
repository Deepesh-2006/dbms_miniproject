CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE vehicle_status AS ENUM ('active', 'maintenance', 'inactive', 'retired');
CREATE TYPE driver_status AS ENUM ('active', 'on_leave', 'inactive');
CREATE TYPE trip_status AS ENUM ('planned', 'in_progress', 'completed', 'cancelled');
CREATE TYPE accident_severity AS ENUM ('minor', 'moderate', 'major', 'critical');

CREATE TABLE manufacturers (
  manufacturer_id BIGSERIAL PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE,
  country VARCHAR(60) NOT NULL
);
CREATE TABLE vehicle_types (
  vehicle_type_id BIGSERIAL PRIMARY KEY,
  manufacturer_id BIGINT NOT NULL REFERENCES manufacturers(manufacturer_id),
  name VARCHAR(100) NOT NULL,
  category VARCHAR(40) NOT NULL,
  default_fuel_type VARCHAR(30) NOT NULL,
  expected_kmpl NUMERIC(5,2) NOT NULL CHECK (expected_kmpl > 0),
  UNIQUE (manufacturer_id, name)
);
CREATE TABLE branches (
  branch_id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  city VARCHAR(80) NOT NULL,
  state VARCHAR(80) NOT NULL,
  phone VARCHAR(20)
);
CREATE TABLE vehicles (
  vehicle_id BIGSERIAL PRIMARY KEY,
  registration_number VARCHAR(15) NOT NULL UNIQUE CHECK (registration_number ~ '^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$'),
  vehicle_type_id BIGINT NOT NULL REFERENCES vehicle_types(vehicle_type_id),
  branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
  chassis_number VARCHAR(30) NOT NULL UNIQUE,
  purchase_date DATE NOT NULL,
  current_odometer NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (current_odometer >= 0),
  next_service_date DATE,
  next_service_odometer NUMERIC(12,2) CHECK (next_service_odometer IS NULL OR next_service_odometer >= 0),
  status vehicle_status NOT NULL DEFAULT 'active'
);
CREATE TABLE drivers (
  driver_id BIGSERIAL PRIMARY KEY,
  branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
  full_name VARCHAR(120) NOT NULL,
  license_number VARCHAR(30) NOT NULL UNIQUE,
  license_expiry DATE NOT NULL,
  joining_date DATE NOT NULL,
  phone VARCHAR(20) NOT NULL UNIQUE,
  status driver_status NOT NULL DEFAULT 'active'
);
CREATE TABLE routes (
  route_id BIGSERIAL PRIMARY KEY,
  route_name VARCHAR(120) NOT NULL UNIQUE,
  origin VARCHAR(100) NOT NULL,
  destination VARCHAR(100) NOT NULL,
  planned_distance_km NUMERIC(10,2) NOT NULL CHECK (planned_distance_km > 0),
  estimated_duration_minutes INTEGER NOT NULL CHECK (estimated_duration_minutes > 0)
);
CREATE TABLE insurance (
  insurance_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
  provider VARCHAR(100) NOT NULL,
  policy_number VARCHAR(60) NOT NULL UNIQUE,
  start_date DATE NOT NULL,
  expiry_date DATE NOT NULL,
  premium NUMERIC(12,2) NOT NULL CHECK (premium >= 0),
  coverage_amount NUMERIC(14,2) NOT NULL CHECK (coverage_amount > 0),
  CHECK (expiry_date > start_date),
  UNIQUE (vehicle_id, policy_number)
);
CREATE TABLE vehicle_assignments (
  assignment_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicles(vehicle_id),
  driver_id BIGINT NOT NULL REFERENCES drivers(driver_id),
  assigned_from TIMESTAMPTZ NOT NULL,
  assigned_to TIMESTAMPTZ,
  notes TEXT,
  CHECK (assigned_to IS NULL OR assigned_to > assigned_from),
  EXCLUDE USING gist (vehicle_id WITH =, tstzrange(assigned_from, COALESCE(assigned_to, 'infinity')) WITH &&),
  EXCLUDE USING gist (driver_id WITH =, tstzrange(assigned_from, COALESCE(assigned_to, 'infinity')) WITH &&)
);
CREATE TABLE trips (
  trip_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicles(vehicle_id),
  driver_id BIGINT NOT NULL REFERENCES drivers(driver_id),
  route_id BIGINT NOT NULL REFERENCES routes(route_id),
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  start_odometer NUMERIC(12,2) NOT NULL CHECK (start_odometer >= 0),
  end_odometer NUMERIC(12,2),
  status trip_status NOT NULL DEFAULT 'planned',
  notes TEXT,
  CHECK (end_time IS NULL OR end_time >= start_time),
  CHECK (end_odometer IS NULL OR end_odometer >= start_odometer),
  CHECK ((status = 'completed') = (end_time IS NOT NULL AND end_odometer IS NOT NULL))
);
CREATE TABLE fuel_transactions (
  fuel_transaction_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicles(vehicle_id),
  driver_id BIGINT REFERENCES drivers(driver_id),
  transaction_date DATE NOT NULL,
  fuel_type VARCHAR(30) NOT NULL,
  litres NUMERIC(10,2) NOT NULL CHECK (litres > 0),
  price_per_litre NUMERIC(10,2) NOT NULL CHECK (price_per_litre > 0),
  total_cost NUMERIC(12,2) GENERATED ALWAYS AS (ROUND(litres * price_per_litre, 2)) STORED,
  odometer NUMERIC(12,2) NOT NULL CHECK (odometer >= 0),
  fuel_station VARCHAR(140) NOT NULL
);
CREATE TABLE maintenance_types (
  maintenance_type_id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  service_interval_km INTEGER NOT NULL CHECK (service_interval_km > 0),
  service_interval_days INTEGER NOT NULL CHECK (service_interval_days > 0)
);
CREATE TABLE service_centers (
  service_center_id BIGSERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  city VARCHAR(80) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  is_authorized BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE maintenance (
  maintenance_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicles(vehicle_id),
  maintenance_type_id BIGINT NOT NULL REFERENCES maintenance_types(maintenance_type_id),
  service_center_id BIGINT NOT NULL REFERENCES service_centers(service_center_id),
  service_date DATE NOT NULL,
  odometer NUMERIC(12,2) NOT NULL CHECK (odometer >= 0),
  cost NUMERIC(12,2) NOT NULL CHECK (cost >= 0),
  description TEXT,
  next_service_date DATE,
  next_service_odometer NUMERIC(12,2),
  CHECK (next_service_date IS NULL OR next_service_date >= service_date),
  CHECK (next_service_odometer IS NULL OR next_service_odometer >= odometer)
);
CREATE TABLE accidents (
  accident_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicles(vehicle_id),
  driver_id BIGINT REFERENCES drivers(driver_id),
  accident_date DATE NOT NULL,
  location VARCHAR(180) NOT NULL,
  severity accident_severity NOT NULL,
  estimated_damage NUMERIC(12,2) NOT NULL CHECK (estimated_damage >= 0),
  description TEXT NOT NULL
);
CREATE TABLE expenses (
  expense_id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES vehicles(vehicle_id),
  expense_date DATE NOT NULL,
  category VARCHAR(30) NOT NULL CHECK (category IN ('fuel', 'maintenance', 'insurance', 'toll', 'repairs', 'other')),
  amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
  description TEXT
);
CREATE TABLE users (
  user_id BIGSERIAL PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'fleet_manager', 'viewer')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
