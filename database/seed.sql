INSERT INTO manufacturers (name,country) VALUES
('Tata Motors','India'),('Mahindra','India'),('Ashok Leyland','India'),('Eicher','India'),('Maruti Suzuki','India');
INSERT INTO vehicle_types (manufacturer_id,name,category,default_fuel_type,expected_kmpl) VALUES
(1,'Ace Gold','Light Commercial','Diesel',17),(1,'Prima 5530','Heavy Truck','Diesel',4.5),(2,'Bolero Pik-Up','Pickup','Diesel',14),(2,'Supro Cargo','Mini Truck','Diesel',17),(3,'Dost+','Light Commercial','Diesel',15),(3,'BOSS 1920','Heavy Truck','Diesel',4.8),(4,'Pro 2059','Medium Truck','Diesel',6),(4,'Pro 3015','Heavy Truck','Diesel',5),(5,'Super Carry','Mini Truck','Petrol',18),(5,'Eeco Cargo','Van','CNG',20);
INSERT INTO branches (name,city,state,phone) VALUES
('Bengaluru Central','Bengaluru','Karnataka','08040001001'),('Mysuru Depot','Mysuru','Karnataka','08214001002'),('Chennai Logistics','Chennai','Tamil Nadu','04440001003'),('Pune Operations','Pune','Maharashtra','02040001004'),('Hyderabad Hub','Hyderabad','Telangana','04040001005');
INSERT INTO maintenance_types (name,service_interval_km,service_interval_days) VALUES
('Routine Service',10000,180),('Oil Change',5000,120),('Brake Inspection',15000,365),('Tyre Rotation',8000,180),('Engine Repair',20000,365);
INSERT INTO service_centers (name,city,phone,is_authorized) VALUES
('Tata Motors Service Hub','Bengaluru','08050002001',true),('Mahindra Fleet Care','Mysuru','08215002002',true),('Chennai Truck Works','Chennai','04450002003',false),('Pune Auto Services','Pune','02050002004',false),('Hyderabad Commercial Garage','Hyderabad','04050002005',true);

INSERT INTO vehicles (registration_number,vehicle_type_id,branch_id,chassis_number,purchase_date,current_odometer,status)
SELECT CASE ((n-1)%5) WHEN 0 THEN 'KA01' WHEN 1 THEN 'KA05' WHEN 2 THEN 'TN09' WHEN 3 THEN 'MH12' ELSE 'TS08' END ||
       (ARRAY['AB','MN','XY','PQ','RT','KL','DV','GS','HN','JK'])[1+((n-1)%10)] || LPAD((1200+n)::text,4,'0'),
       1+((n-1)%10),1+((n-1)%5),'CHS' || LPAD(n::text,14,'0'),DATE '2022-01-01' + (n*13),0,
       CASE WHEN n IN (7,23) THEN 'maintenance'::vehicle_status ELSE 'active'::vehicle_status END
FROM generate_series(1,50) n;
INSERT INTO drivers (branch_id,full_name,license_number,license_expiry,joining_date,phone,status)
SELECT 1+((n-1)%5),
       (ARRAY['Aarav','Vivaan','Aditya','Arjun','Rohan','Karthik','Sanjay','Nikhil','Manish','Rahul','Kavya','Ananya','Meera','Priya','Divya'])[1+((n-1)%15)] || ' ' ||
       (ARRAY['Sharma','Reddy','Iyer','Patil','Nair','Kumar','Singh','Rao','Menon','Das'])[1+((n-1)%10)],
       'DL' || LPAD((201500000000+n)::text,12,'0'),DATE '2027-12-31' - (n*7),DATE '2020-01-01'+(n*23),'9' || LPAD((800000000+n)::text,9,'0'),
       CASE WHEN n=29 THEN 'on_leave'::driver_status ELSE 'active'::driver_status END
FROM generate_series(1,30) n;
INSERT INTO routes (route_name,origin,destination,planned_distance_km,estimated_duration_minutes) VALUES
('Bengaluru–Mysuru Express','Bengaluru','Mysuru',145,210),('Bengaluru–Chennai Freight','Bengaluru','Chennai',347,480),('Chennai–Puducherry Run','Chennai','Puducherry',152,220),('Pune–Mumbai Corridor','Pune','Mumbai',148,210),('Hyderabad–Vijayawada Route','Hyderabad','Vijayawada',275,390),('Bengaluru City Distribution','Bengaluru','Bengaluru',62,180),('Mysuru–Mangaluru Highway','Mysuru','Mangaluru',255,420),('Chennai–Coimbatore Express','Chennai','Coimbatore',505,690),('Pune–Nashik Supply','Pune','Nashik',210,300),('Hyderabad–Warangal Link','Hyderabad','Warangal',148,230),('Bengaluru–Hubballi Route','Bengaluru','Hubballi',410,600),('Chennai–Madurai Freight','Chennai','Madurai',462,630),('Pune–Kolhapur Delivery','Pune','Kolhapur',235,350),('Hyderabad–Nagpur Line','Hyderabad','Nagpur',500,720),('Mysuru Local Distribution','Mysuru','Mysuru',48,150);
INSERT INTO insurance (vehicle_id,provider,policy_number,start_date,expiry_date,premium,coverage_amount)
SELECT n,(ARRAY['ICICI Lombard','HDFC ERGO','Bajaj Allianz','Tata AIG','New India Assurance'])[1+((n-1)%5)],'POL-FLT-'||LPAD(n::text,5,'0'),DATE '2026-01-01',CASE WHEN n IN (5,10) THEN DATE '2026-09-15' ELSE DATE '2027-12-31' END,18000+(n%7)*2200,750000+(n%5)*100000 FROM generate_series(1,50) n;
INSERT INTO vehicle_assignments (vehicle_id,driver_id,assigned_from,notes)
SELECT n,n,TIMESTAMPTZ '2026-01-01 08:00:00+05:30','Primary fleet assignment' FROM generate_series(1,30) n;

INSERT INTO fuel_transactions (vehicle_id,driver_id,transaction_date,fuel_type,litres,price_per_litre,odometer,fuel_station)
SELECT v,1+((v-1)%30),DATE '2026-01-01'+(s*18)+(v%6),CASE WHEN v%10 IN (9,10) THEN 'CNG' ELSE 'Diesel' END,35+(v%11)+(s%4),90+(v%5),10000+(v*20)+(s*550),'IndianOil Fleet Station '||((v%5)+1)
FROM generate_series(1,50) v CROSS JOIN generate_series(1,10) s ORDER BY v,s;
INSERT INTO maintenance (vehicle_id,maintenance_type_id,service_center_id,service_date,odometer,cost,description,next_service_date,next_service_odometer)
SELECT v,1+((v-1)%5),1+((v-1)%5),DATE '2026-06-01'+(v%25),16500+(v*20),4500+(v%8)*850,'Scheduled fleet service',DATE '2026-12-01'+(v%20),24500+(v*20) FROM generate_series(1,50) v
UNION ALL
SELECT v,2,1+((v-1)%5),DATE '2026-09-01'+(v%20),18000+(v*20),2800+(v%6)*450,'Oil and filter replacement',DATE '2027-02-01'+(v%20),23000+(v*20) FROM generate_series(1,50) v ORDER BY 1,4;
INSERT INTO trips (vehicle_id,driver_id,route_id,start_time,end_time,start_odometer,end_odometer,status,notes)
SELECT v,1+((v-1)%30),1+((s+v-2)%15),TIMESTAMPTZ '2026-02-01 07:00:00+05:30'+((s*17+v)%180)*INTERVAL '1 day',TIMESTAMPTZ '2026-02-01 07:00:00+05:30'+((s*17+v)%180)*INTERVAL '1 day'+(3+(s%8))*INTERVAL '1 hour',20000+(v*20)+(s*700),20120+(v*20)+(s*700)+(s%4)*35,'completed','Completed scheduled delivery'
FROM generate_series(1,50) v CROSS JOIN generate_series(1,5) s ORDER BY v,s;
INSERT INTO accidents (vehicle_id,driver_id,accident_date,location,severity,estimated_damage,description)
SELECT 1+((n-1)%50),1+((n-1)%30),DATE '2026-03-01'+(n*4),(ARRAY['Bengaluru Outer Ring Road','NH 44 Hyderabad','Pune–Mumbai Expressway','Chennai Bypass','Mysuru Road'])[1+((n-1)%5)],(ARRAY['minor','moderate','major','minor','minor']) [1+((n-1)%5)]::accident_severity,3500+(n%7)*12000,'Reported fleet incident; inspection completed' FROM generate_series(1,32) n;
INSERT INTO expenses (vehicle_id,expense_date,category,amount,description)
SELECT 1+((n-1)%50),DATE '2026-01-01'+(n%240),(ARRAY['toll','repairs','other','insurance'])[1+((n-1)%4)],700+(n%13)*410,'Operational fleet expense' FROM generate_series(1,240) n;
INSERT INTO users (username,password_hash,role) VALUES
('admin',crypt('Fleet@123',gen_salt('bf')),'admin'),('manager',crypt('Manager@123',gen_salt('bf')),'fleet_manager'),('viewer',crypt('Viewer@123',gen_salt('bf')),'viewer');
UPDATE vehicles SET status='maintenance',next_service_date=DATE '2026-08-25' WHERE vehicle_id=7;
