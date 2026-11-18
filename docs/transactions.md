# Transaction handling

Trip creation in `backend/app/services.py` is one transaction. It verifies active vehicle and driver status, verifies policy coverage on the trip date, inserts the trip, flushes so PostgreSQL triggers run, then commits. Any SQL or validation failure rolls the session back, leaving no partial trip or odometer update.

The database independently repeats the insurance condition in a trigger. This means direct SQL cannot bypass the API’s business rule.
