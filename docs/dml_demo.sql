-- DML demonstration. Everything runs inside one transaction that is rolled back, so the seeded data is untouched.
BEGIN;

-- INSERT: register a new vehicle
INSERT INTO vehicles (registration_number, vehicle_type_id, branch_id, chassis_number, purchase_date, current_odometer, status)
VALUES ('KA01ZZ9999', 1, 1, 'CHS99999999999999', DATE '2026-01-15', 1000, 'active') RETURNING vehicle_id, registration_number, status;

-- INSERT: policy for the new vehicle, then fuel purchase (total_cost is a generated column; trigger advances odometer)
INSERT INTO insurance (vehicle_id, provider, policy_number, start_date, expiry_date, premium, coverage_amount)
SELECT vehicle_id, 'New India Assurance', 'POL-DEMO-0001', CURRENT_DATE - 30, CURRENT_DATE + 335, 42000, 1500000 FROM vehicles WHERE registration_number = 'KA01ZZ9999' RETURNING policy_number, expiry_date;
INSERT INTO fuel_transactions (vehicle_id, driver_id, transaction_date, fuel_type, litres, price_per_litre, odometer, fuel_station)
SELECT vehicle_id, 1, CURRENT_DATE, 'Diesel', 40, 92.50, 1150, 'Indian Oil, Hosur Road' FROM vehicles WHERE registration_number = 'KA01ZZ9999' RETURNING litres, price_per_litre, total_cost, odometer;
SELECT registration_number, current_odometer FROM vehicles WHERE registration_number = 'KA01ZZ9999';

-- UPDATE: send the vehicle for maintenance
UPDATE vehicles SET status = 'maintenance' WHERE registration_number = 'KA01ZZ9999' RETURNING registration_number, status;
UPDATE vehicles SET status = 'active' WHERE registration_number = 'KA01ZZ9999';

-- INSERT trip, then stored procedure close_trip
INSERT INTO trips (vehicle_id, driver_id, route_id, start_time, start_odometer, status)
SELECT vehicle_id, 1, 1, now() - INTERVAL '3 hours', 1150, 'in_progress' FROM vehicles WHERE registration_number = 'KA01ZZ9999' RETURNING trip_id, status, start_odometer \gset new_
CALL close_trip(:new_trip_id, 1290);
SELECT trip_id, status, start_odometer, end_odometer, end_odometer - start_odometer AS distance_km FROM trips WHERE trip_id = :new_trip_id;
SELECT registration_number, current_odometer FROM vehicles WHERE registration_number = 'KA01ZZ9999';

-- Constraint / trigger rejections (each in a savepoint so the transaction continues)
SAVEPOINT s1;
INSERT INTO vehicles (registration_number, vehicle_type_id, branch_id, chassis_number, purchase_date) VALUES ('BAD-REG', 1, 1, 'CHS00000000000001', DATE '2026-01-01');
ROLLBACK TO s1;
SAVEPOINT s2;
INSERT INTO fuel_transactions (vehicle_id, transaction_date, fuel_type, litres, price_per_litre, odometer, fuel_station)
SELECT vehicle_id, CURRENT_DATE, 'Diesel', 10, 90, 500, 'Odometer regression' FROM vehicles WHERE registration_number = 'KA01ZZ9999';
ROLLBACK TO s2;
SAVEPOINT s3;
CALL close_trip(1, 99999);
ROLLBACK TO s3;
SAVEPOINT s4;
INSERT INTO trips (vehicle_id, driver_id, route_id, start_time, start_odometer, status)
SELECT vehicle_id, 1, 1, now() + INTERVAL '2 years', 1290, 'planned' FROM vehicles WHERE registration_number = 'KA01ZZ9999';
ROLLBACK TO s4;

-- DELETE: remove the demo records (children first)
DELETE FROM trips WHERE vehicle_id = (SELECT vehicle_id FROM vehicles WHERE registration_number = 'KA01ZZ9999');
DELETE FROM fuel_transactions WHERE vehicle_id = (SELECT vehicle_id FROM vehicles WHERE registration_number = 'KA01ZZ9999');
DELETE FROM vehicles WHERE registration_number = 'KA01ZZ9999' RETURNING registration_number;  -- insurance row is removed by ON DELETE CASCADE
SELECT count(*) AS remaining_demo_policies FROM insurance WHERE policy_number = 'POL-DEMO-0001';

ROLLBACK;
