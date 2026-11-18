CREATE OR REPLACE FUNCTION validate_insurance_for_trip() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status IN ('planned', 'in_progress', 'completed') AND NOT EXISTS (
    SELECT 1 FROM insurance i
    WHERE i.vehicle_id = NEW.vehicle_id
      AND i.start_date <= NEW.start_time::date AND i.expiry_date >= NEW.start_time::date
  ) THEN
    RAISE EXCEPTION 'Vehicle % has no valid insurance for trip date %', NEW.vehicle_id, NEW.start_time::date;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trip_insurance_guard BEFORE INSERT OR UPDATE OF vehicle_id, start_time, status ON trips
FOR EACH ROW EXECUTE FUNCTION validate_insurance_for_trip();

CREATE OR REPLACE FUNCTION validate_and_update_odometer() RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE latest NUMERIC;
BEGIN
  SELECT GREATEST(v.current_odometer, COALESCE(MAX(x.odo), 0)) INTO latest
  FROM vehicles v
  LEFT JOIN (
    SELECT vehicle_id, odometer AS odo FROM fuel_transactions
    UNION ALL SELECT vehicle_id, odometer FROM maintenance
    UNION ALL SELECT vehicle_id, COALESCE(end_odometer, start_odometer) FROM trips
  ) x ON x.vehicle_id = v.vehicle_id
  WHERE v.vehicle_id = NEW.vehicle_id GROUP BY v.current_odometer;
  IF NEW.odometer < latest THEN
    RAISE EXCEPTION 'Odometer % cannot be lower than latest recorded reading % for vehicle %', NEW.odometer, latest, NEW.vehicle_id;
  END IF;
  UPDATE vehicles SET current_odometer = GREATEST(current_odometer, NEW.odometer) WHERE vehicle_id = NEW.vehicle_id;
  RETURN NEW;
END $$;
CREATE TRIGGER fuel_odometer_guard BEFORE INSERT OR UPDATE OF odometer ON fuel_transactions
FOR EACH ROW EXECUTE FUNCTION validate_and_update_odometer();
CREATE TRIGGER maintenance_odometer_guard BEFORE INSERT OR UPDATE OF odometer ON maintenance
FOR EACH ROW EXECUTE FUNCTION validate_and_update_odometer();

CREATE OR REPLACE FUNCTION update_vehicle_after_maintenance() RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE type_row maintenance_types%ROWTYPE;
BEGIN
  SELECT * INTO type_row FROM maintenance_types WHERE maintenance_type_id = NEW.maintenance_type_id;
  UPDATE vehicles SET
    status = 'active',
    next_service_date = COALESCE(NEW.next_service_date, NEW.service_date + type_row.service_interval_days),
    next_service_odometer = COALESCE(NEW.next_service_odometer, NEW.odometer + type_row.service_interval_km),
    current_odometer = GREATEST(current_odometer, NEW.odometer)
  WHERE vehicle_id = NEW.vehicle_id;
  RETURN NEW;
END $$;
CREATE TRIGGER maintenance_completion_update AFTER INSERT OR UPDATE ON maintenance
FOR EACH ROW EXECUTE FUNCTION update_vehicle_after_maintenance();

CREATE OR REPLACE FUNCTION update_vehicle_after_completed_trip() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status = 'completed' THEN
    UPDATE vehicles SET current_odometer = GREATEST(current_odometer, NEW.end_odometer) WHERE vehicle_id = NEW.vehicle_id;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER completed_trip_odometer AFTER INSERT OR UPDATE ON trips
FOR EACH ROW EXECUTE FUNCTION update_vehicle_after_completed_trip();
