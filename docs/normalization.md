# Normalization

The schema is in 3NF for practical fleet management.

1. **1NF:** scalar values only; a fuel purchase, accident, and service each have their own rows rather than repeated columns.
2. **2NF:** attributes describe the table’s key. For example, a trip stores route/driver/vehicle references, not their names or registration numbers.
3. **3NF:** manufacturer data is separated from vehicle type; type is separated from vehicle; maintenance type and service centre are separated from maintenance; branch is separated from drivers and vehicles. This prevents update anomalies.

`total_cost` on fuel is a PostgreSQL generated column rather than independently maintained duplicated data. The analytical views deliberately denormalize only at read time.
