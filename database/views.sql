CREATE OR REPLACE VIEW vehicle_performance_view AS
WITH trips_agg AS (SELECT vehicle_id, COUNT(*) FILTER (WHERE status='completed') total_trips, COALESCE(SUM(end_odometer-start_odometer) FILTER (WHERE status='completed'),0) total_distance FROM trips GROUP BY vehicle_id),
fuel_agg AS (SELECT vehicle_id, SUM(litres) fuel_litres, SUM(total_cost) fuel_cost FROM fuel_transactions GROUP BY vehicle_id),
maintenance_agg AS (SELECT vehicle_id,SUM(cost) maintenance_cost FROM maintenance GROUP BY vehicle_id)
SELECT v.vehicle_id,v.registration_number,vt.name vehicle_type,COALESCE(t.total_trips,0) total_trips,COALESCE(t.total_distance,0) total_distance,COALESCE(f.fuel_litres,0) fuel_litres,COALESCE(f.fuel_cost,0) fuel_cost,COALESCE(m.maintenance_cost,0) maintenance_cost,
CASE WHEN COALESCE(f.fuel_litres,0)=0 THEN NULL ELSE ROUND(t.total_distance/f.fuel_litres,2) END fuel_efficiency_kmpl
FROM vehicles v JOIN vehicle_types vt ON vt.vehicle_type_id=v.vehicle_type_id LEFT JOIN trips_agg t ON t.vehicle_id=v.vehicle_id LEFT JOIN fuel_agg f ON f.vehicle_id=v.vehicle_id LEFT JOIN maintenance_agg m ON m.vehicle_id=v.vehicle_id;
CREATE OR REPLACE VIEW driver_performance_view AS
WITH trip_stats AS (SELECT driver_id,COUNT(*) FILTER (WHERE status='completed') trips_completed,COALESCE(SUM(end_odometer-start_odometer) FILTER (WHERE status='completed'),0) total_distance,ROUND(COALESCE(AVG(EXTRACT(EPOCH FROM(end_time-start_time))/60) FILTER (WHERE status='completed'),0)::numeric,2) avg_trip_duration_minutes FROM trips GROUP BY driver_id),
accident_stats AS (SELECT driver_id,COUNT(*) accident_count FROM accidents WHERE driver_id IS NOT NULL GROUP BY driver_id)
SELECT d.driver_id,d.full_name,d.license_number,COALESCE(t.trips_completed,0) trips_completed,COALESCE(t.total_distance,0) total_distance,COALESCE(a.accident_count,0) accident_count,COALESCE(t.avg_trip_duration_minutes,0) avg_trip_duration_minutes
FROM drivers d LEFT JOIN trip_stats t ON t.driver_id=d.driver_id LEFT JOIN accident_stats a ON a.driver_id=d.driver_id;
CREATE OR REPLACE VIEW vehicle_cost_view AS
WITH f AS (SELECT vehicle_id,SUM(total_cost) val FROM fuel_transactions GROUP BY vehicle_id),m AS (SELECT vehicle_id,SUM(cost) val FROM maintenance GROUP BY vehicle_id),i AS (SELECT vehicle_id,SUM(premium) val FROM insurance GROUP BY vehicle_id),e AS (SELECT vehicle_id,SUM(amount) val FROM expenses GROUP BY vehicle_id)
SELECT v.vehicle_id,v.registration_number,COALESCE(f.val,0) fuel_cost,COALESCE(m.val,0) maintenance_cost,COALESCE(i.val,0) insurance_cost,COALESCE(e.val,0) other_expenses,COALESCE(f.val,0)+COALESCE(m.val,0)+COALESCE(i.val,0)+COALESCE(e.val,0) total_operating_cost
FROM vehicles v LEFT JOIN f ON f.vehicle_id=v.vehicle_id LEFT JOIN m ON m.vehicle_id=v.vehicle_id LEFT JOIN i ON i.vehicle_id=v.vehicle_id LEFT JOIN e ON e.vehicle_id=v.vehicle_id;
CREATE OR REPLACE VIEW maintenance_due_view AS
SELECT v.vehicle_id,v.registration_number,v.current_odometer,v.next_service_date,v.next_service_odometer,
CASE WHEN v.next_service_date < CURRENT_DATE OR v.next_service_odometer <= v.current_odometer THEN 'overdue' WHEN v.next_service_date <= CURRENT_DATE+30 OR v.next_service_odometer <= v.current_odometer+1000 THEN 'due_soon' ELSE 'scheduled' END service_status
FROM vehicles v WHERE v.status <> 'retired' AND (v.next_service_date IS NOT NULL OR v.next_service_odometer IS NOT NULL);
