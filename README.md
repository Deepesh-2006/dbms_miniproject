# Smart Vehicle Fleet Management & Analytics System

A full-stack DBMS project for managing an Indian commercial fleet. It combines a Next.js analytics dashboard with a FastAPI REST API, a PostgreSQL database that enforces business rules itself, and Redis for live vehicle telemetry and dashboard caching.

## Highlights

- 16 normalized PostgreSQL tables and realistic seed data: 50 vehicles, 30 drivers, 15 routes, 250 trips, 500 fuel purchases, 100 maintenance records, 32 accidents, and 240 expenses.
- Role-based JWT authentication: **admin**, **fleet manager**, and **viewer**.
- CRUD APIs for operational entities; trip creation is an atomic transaction.
- Four analytical views, three SQL functions, four triggers, targeted indexes, and 25 documented non-trivial SQL queries.
- Responsive SaaS-style dashboard powered by actual database views and aggregates, with charts for fuel, maintenance, utilization, and efficiency.

## Architecture

```text
React + Tailwind + Recharts  →  FastAPI + SQLAlchemy  →  PostgreSQL 16
        port 5173                    port 8000              port 5432
```

The backend is modular: routers expose the API, Pydantic validates requests, `services.py` owns transactional trip creation, and PostgreSQL owns durable constraints and triggers. Docker seeds the database only on its first initialisation.

## Quick start

1. Install Docker Desktop and copy the environment template:

   ```bash
   cp .env.example .env
   docker compose up --build
   ```

2. Open [http://localhost:3000](http://localhost:3000). API Swagger documentation is at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

3. Sign in using one of these seeded accounts:

   | Role | Username | Password |
   |---|---|---|
   | Admin | `admin` | `Fleet@123` |
   | Fleet Manager | `manager` | `Manager@123` |
   | Viewer | `viewer` | `Viewer@123` |

The database has a persistent Docker volume. To seed afresh for a demonstration, run `docker compose down -v` and then start it again. This deletes only this project’s Docker database volume.

## Local development

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev   # Next.js on http://localhost:3000
```

Set `DATABASE_URL=postgresql+psycopg://fleet_admin:change_me_locally@localhost:5432/smart_fleet` locally; the compose network uses `db` as its host. The database SQL scripts run in this order: schema, indexes, triggers, functions, views, seed.

## API overview

| Endpoint group | Operations |
|---|---|
| `/api/auth/login` | JWT login |
| `/api/vehicles`, `/drivers`, `/routes` | List, get, create, update, delete |
| `/api/fuel`, `/maintenance`, `/accidents`, `/insurance`, `/expenses` | List, get, create, update, delete |
| `/api/trips` | List and transaction-safe create |
| `/api/telemetry/{vehicle_id}` | Redis: PUT (create/upsert), GET, PATCH (update), DELETE; `/api/telemetry/nearby/search` geo query |
| `/api/analytics/dashboard`, `/api/analytics/insights` | Dashboard charts and intelligence |
| `/api/vehicles/{id}/details` | Vehicle history and operating cost |

All list endpoints offer pagination; the vehicle and driver endpoints also support search. Mutating endpoints are restricted to administrators and fleet managers, and deletion is administrator-only.

## DBMS concepts demonstrated

- **Keys and integrity:** primary/foreign/unique keys, check constraints, enums, a generated total-cost field, plus PostgreSQL range-exclusion constraints preventing overlapping vehicle or driver assignments.
- **Views:** `vehicle_performance_view`, `driver_performance_view`, `vehicle_cost_view`, and `maintenance_due_view`.
- **Functions:** `vehicle_fuel_efficiency`, `vehicle_operating_cost`, and `driver_performance` accept IDs and optional date ranges.
- **Triggers:** insurance is required on a trip; fuel and maintenance cannot regress odometers; a completed service refreshes vehicle service schedule; a completed trip updates the vehicle odometer.
- **Indexes:** see [database/indexes.sql](database/indexes.sql). Composite indexes match history-by-vehicle/date access patterns; `EXPLAIN (ANALYZE, BUFFERS)` on `trips WHERE vehicle_id = ? ORDER BY start_time DESC` and `fuel_transactions WHERE vehicle_id = ? AND transaction_date >= ?` demonstrates their use once data volume grows.
- **Queries:** [docs/sql_queries.sql](docs/sql_queries.sql) has 25 meaningful joins, aggregates, CTEs, subqueries, date queries, filters, functions, and window queries.

## Redis (NoSQL) component

Latest vehicle telemetry lives in Redis hashes (`telemetry:vehicle:{id}`, 15-minute TTL) with a geospatial index (`fleet:positions`); the dashboard response is cached for 60 seconds (`cache:dashboard`). Set `REDIS_URL` (default `redis://localhost:6379/0`). If Redis is down the dashboard still works (cache is skipped) and telemetry endpoints return 503.

## Project report

`docs/DBMS_Project_Report.docx` follows the course template. Regenerate it with `python docs/build_report_assets.py && python docs/generate_report.py` (needs `python-docx`, `matplotlib`, `psycopg`, a seeded database). Fill in the SRN/name/faculty placeholders on the title page and the footer; Word refreshes the table-of-contents page numbers on open.

## Documentation

- [Schema and ER diagram](docs/database_schema.md)
- [Normalization rationale](docs/normalization.md)
- [Transaction handling](docs/transactions.md)
- SQL implementation: [schema](database/schema.sql), [views](database/views.sql), [functions](database/procedures.sql), [triggers](database/triggers.sql), [indexes](database/indexes.sql), [seed data](database/seed.sql)

## Testing

With the compose database running:

```bash
pip install -r backend/requirements.txt
pytest tests -q
```

The integration tests exercise login, live dashboard analytics, vehicle uniqueness, trip odometer validation, expired-insurance rejection, fuel validation, and maintenance date validation.
