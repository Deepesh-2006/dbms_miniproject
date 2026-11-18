CREATE OR REPLACE FUNCTION vehicle_fuel_efficiency(p_vehicle_id BIGINT, p_from DATE DEFAULT NULL, p_to DATE DEFAULT NULL)
RETURNS TABLE(total_distance NUMERIC, total_litres NUMERIC, km_per_litre NUMERIC) LANGUAGE sql STABLE AS $$
  WITH t AS (SELECT COALESCE(SUM(end_odometer-start_odometer),0) distance FROM trips WHERE vehicle_id=p_vehicle_id AND status='completed' AND start_time::date BETWEEN COALESCE(p_from, DATE '1900-01-01') AND COALESCE(p_to, DATE '9999-12-31')),
  f AS (SELECT COALESCE(SUM(litres),0) litres FROM fuel_transactions WHERE vehicle_id=p_vehicle_id AND transaction_date BETWEEN COALESCE(p_from, DATE '1900-01-01') AND COALESCE(p_to, DATE '9999-12-31'))
  SELECT t.distance, f.litres, CASE WHEN f.litres=0 THEN NULL ELSE ROUND(t.distance/f.litres,2) END FROM t CROSS JOIN f;
$$;
CREATE OR REPLACE FUNCTION vehicle_operating_cost(p_vehicle_id BIGINT, p_from DATE DEFAULT NULL, p_to DATE DEFAULT NULL)
RETURNS TABLE(fuel_cost NUMERIC, maintenance_cost NUMERIC, insurance_cost NUMERIC, other_expenses NUMERIC, total_cost NUMERIC) LANGUAGE sql STABLE AS $$
  WITH limits AS (SELECT COALESCE(p_from,DATE '1900-01-01') d1, COALESCE(p_to,DATE '9999-12-31') d2), c AS (
    SELECT (SELECT COALESCE(SUM(total_cost),0) FROM fuel_transactions, limits WHERE vehicle_id=p_vehicle_id AND transaction_date BETWEEN d1 AND d2) fuel,
      (SELECT COALESCE(SUM(cost),0) FROM maintenance, limits WHERE vehicle_id=p_vehicle_id AND service_date BETWEEN d1 AND d2) maint,
      (SELECT COALESCE(SUM(premium),0) FROM insurance, limits WHERE vehicle_id=p_vehicle_id AND start_date BETWEEN d1 AND d2) ins,
      (SELECT COALESCE(SUM(amount),0) FROM expenses, limits WHERE vehicle_id=p_vehicle_id AND expense_date BETWEEN d1 AND d2) other)
  SELECT fuel,maint,ins,other, fuel+maint+ins+other FROM c;
$$;
CREATE OR REPLACE FUNCTION driver_performance(p_driver_id BIGINT, p_from DATE DEFAULT NULL, p_to DATE DEFAULT NULL)
RETURNS TABLE(completed_trips BIGINT, distance_km NUMERIC, avg_duration_minutes NUMERIC, accident_count BIGINT) LANGUAGE sql STABLE AS $$
  WITH d AS (SELECT COALESCE(p_from, DATE '1900-01-01') d1, COALESCE(p_to, DATE '9999-12-31') d2)
  SELECT COUNT(t.trip_id), COALESCE(SUM(t.end_odometer-t.start_odometer),0), ROUND(COALESCE(AVG(EXTRACT(EPOCH FROM (t.end_time-t.start_time))/60),0)::numeric,2),
    (SELECT COUNT(*) FROM accidents a,d WHERE a.driver_id=p_driver_id AND a.accident_date BETWEEN d.d1 AND d.d2)
  FROM trips t,d WHERE t.driver_id=p_driver_id AND t.status='completed' AND t.start_time::date BETWEEN d.d1 AND d.d2;
$$;

CREATE OR REPLACE PROCEDURE close_trip(p_trip_id BIGINT, p_end_odometer NUMERIC, p_end_time TIMESTAMPTZ DEFAULT now())
LANGUAGE plpgsql AS $$
DECLARE trip_row trips%ROWTYPE;
BEGIN
  SELECT * INTO trip_row FROM trips WHERE trip_id = p_trip_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Trip % does not exist', p_trip_id; END IF;
  IF trip_row.status IN ('completed', 'cancelled') THEN RAISE EXCEPTION 'Trip % is already %', p_trip_id, trip_row.status; END IF;
  IF p_end_odometer < trip_row.start_odometer THEN RAISE EXCEPTION 'End odometer % is below start odometer %', p_end_odometer, trip_row.start_odometer; END IF;
  UPDATE trips SET status = 'completed', end_odometer = p_end_odometer, end_time = GREATEST(p_end_time, trip_row.start_time) WHERE trip_id = p_trip_id;
END $$;
