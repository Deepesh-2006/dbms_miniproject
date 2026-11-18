-- 01 INNER JOIN: trip manifest
SELECT t.trip_id,v.registration_number,d.full_name,r.route_name,t.status FROM trips t JOIN vehicles v USING(vehicle_id) JOIN drivers d USING(driver_id) JOIN routes r USING(route_id);
-- 02 LEFT JOIN: vehicles with their most recent fuel use
SELECT v.registration_number,MAX(f.transaction_date) last_fuel_date FROM vehicles v LEFT JOIN fuel_transactions f USING(vehicle_id) GROUP BY v.vehicle_id;
-- 03 GROUP BY: fuel spend by vehicle
SELECT vehicle_id,SUM(total_cost) fuel_cost FROM fuel_transactions GROUP BY vehicle_id;
-- 04 HAVING: unusually fuel-heavy vehicles
SELECT vehicle_id,SUM(total_cost) total FROM fuel_transactions GROUP BY vehicle_id HAVING SUM(total_cost)>50000;
-- 05 subquery: vehicles above fleet average cost
SELECT * FROM vehicle_cost_view WHERE total_operating_cost>(SELECT AVG(total_operating_cost) FROM vehicle_cost_view);
-- 06 correlated subquery: latest policy per vehicle
SELECT i.* FROM insurance i WHERE expiry_date=(SELECT MAX(i2.expiry_date) FROM insurance i2 WHERE i2.vehicle_id=i.vehicle_id);
-- 07 CTE: monthly cost rollup
WITH m AS (SELECT date_trunc('month',transaction_date) month,SUM(total_cost) fuel FROM fuel_transactions GROUP BY 1) SELECT * FROM m ORDER BY month;
-- 08 CASE: insurance alert bands
SELECT policy_number,CASE WHEN expiry_date<CURRENT_DATE THEN 'expired' WHEN expiry_date<=CURRENT_DATE+30 THEN 'expiring' ELSE 'valid' END alert FROM insurance;
-- 09 aggregate: fleet average efficiency
SELECT AVG(fuel_efficiency_kmpl) FROM vehicle_performance_view WHERE fuel_efficiency_kmpl IS NOT NULL;
-- 10 window rank: most expensive vehicles
SELECT registration_number,total_operating_cost,DENSE_RANK() OVER(ORDER BY total_operating_cost DESC) cost_rank FROM vehicle_cost_view;
-- 11 window running total: cumulative fuel cost
SELECT transaction_date,total_cost,SUM(total_cost) OVER(ORDER BY transaction_date,fuel_transaction_id) running_cost FROM fuel_transactions;
-- 12 date query: trips this month
SELECT * FROM trips WHERE date_trunc('month',start_time)=date_trunc('month',CURRENT_DATE);
-- 13 route utilization
SELECT r.route_name,COUNT(t.trip_id) completed FROM routes r LEFT JOIN trips t ON t.route_id=r.route_id AND t.status='completed' GROUP BY r.route_id ORDER BY completed DESC;
-- 14 vehicles without a completed trip
SELECT v.registration_number FROM vehicles v WHERE NOT EXISTS (SELECT 1 FROM trips t WHERE t.vehicle_id=v.vehicle_id AND t.status='completed');
-- 15 maintenance cost by type
SELECT mt.name,SUM(m.cost) cost FROM maintenance m JOIN maintenance_types mt USING(maintenance_type_id) GROUP BY mt.name;
-- 16 accident severity distribution
SELECT severity,COUNT(*),SUM(estimated_damage) FROM accidents GROUP BY severity;
-- 17 driver performance view
SELECT * FROM driver_performance_view ORDER BY total_distance DESC;
-- 18 service-alert view
SELECT * FROM maintenance_due_view WHERE service_status<>'scheduled';
-- 19 function: selected vehicle efficiency
SELECT * FROM vehicle_fuel_efficiency(1,DATE '2026-01-01',DATE '2026-12-31');
-- 20 function: selected vehicle operating cost
SELECT * FROM vehicle_operating_cost(1,NULL,NULL);
-- 21 function: selected driver performance
SELECT * FROM driver_performance(1,NULL,NULL);
-- 22 percentile: top 10% cost vehicles
SELECT * FROM vehicle_cost_view WHERE total_operating_cost>=PERCENTILE_CONT(.9) WITHIN GROUP(ORDER BY total_operating_cost);
-- 23 LAG: days between refuels
SELECT vehicle_id,transaction_date,transaction_date-LAG(transaction_date) OVER(PARTITION BY vehicle_id ORDER BY transaction_date) days_since_last FROM fuel_transactions;
-- 24 FILTER aggregates: cost sources by branch
SELECT b.name,SUM(f.total_cost) FILTER(WHERE f.fuel_type='Diesel') diesel_cost,SUM(f.total_cost) FILTER(WHERE f.fuel_type='CNG') cng_cost FROM branches b JOIN vehicles v USING(branch_id) LEFT JOIN fuel_transactions f USING(vehicle_id) GROUP BY b.name;
-- 25 CTE plus rank: top driver in each branch
WITH p AS (SELECT d.branch_id,d.full_name,dp.total_distance,RANK() OVER(PARTITION BY d.branch_id ORDER BY dp.total_distance DESC) r FROM drivers d JOIN driver_performance_view dp USING(driver_id)) SELECT * FROM p WHERE r=1;

-- 26 recursive CTE: continuous month calendar joined to monthly fuel spend (fills months with no purchases)
WITH RECURSIVE months(m) AS (SELECT date_trunc('month',MIN(transaction_date)) FROM fuel_transactions UNION ALL SELECT m + INTERVAL '1 month' FROM months WHERE m < (SELECT date_trunc('month',MAX(transaction_date)) FROM fuel_transactions)) SELECT to_char(m,'YYYY-MM') AS month, COALESCE(SUM(f.total_cost),0) AS fuel_cost FROM months LEFT JOIN fuel_transactions f ON date_trunc('month',f.transaction_date)=m GROUP BY m ORDER BY m;
