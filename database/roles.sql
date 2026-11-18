-- Database-level role-based access control (complements the application's JWT roles).
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fleet_viewer_role') THEN CREATE ROLE fleet_viewer_role NOLOGIN; END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fleet_manager_role') THEN CREATE ROLE fleet_manager_role NOLOGIN; END IF;
END $$;

-- Viewer: read-only on operational data and analytical views; no access to credentials.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO fleet_viewer_role;
REVOKE SELECT ON users FROM fleet_viewer_role;

-- Manager: read plus insert/update on operational tables; deletes are reserved for the owner/admin.
GRANT fleet_viewer_role TO fleet_manager_role;
GRANT INSERT, UPDATE ON vehicles, drivers, routes, trips, fuel_transactions, maintenance, accidents, insurance, expenses, vehicle_assignments TO fleet_manager_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fleet_manager_role;
