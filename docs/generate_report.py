"""Builds docs/DBMS_Project_Report.docx from DBMS-Project-Template.docx, project SQL files and report_assets/."""
import copy
import os
import re
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
A = os.path.join(HERE, "report_assets")
TITLE = "Smart Vehicle Fleet Management & Analytics System"
d = Document(os.path.join(HERE, "DBMS-Project-Template.docx"))
body = d.element.body


def read(path):
    with open(path, encoding="utf8") as fh:
        return fh.read().rstrip("\n")


# ---------------------------------------------------------------- helpers
def set_font(run, size=12, bold=None, italic=None, name="Times New Roman", color=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), name)
    run.font.size = Pt(size)
    if bold is not None: run.bold = bold
    if italic is not None: run.italic = italic
    if color: run.font.color.rgb = RGBColor.from_string(color)


def shade(el_pr, fill):
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
    el_pr.append(shd)


def new_p(style=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=6, keep_next=False):
    p = d.add_paragraph(style=style)
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.keep_with_next = keep_next
    return p


def text(t, size=12, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6):
    p = new_p(align=align, after=after)
    # **bold** inline markup
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", t)):
        if part:
            set_font(p.add_run(part), size, bold=(bold or i % 2 == 1), italic=italic)
    return p


def bullet(t, size=12):
    p = new_p(after=3)
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.2)
    set_font(p.add_run("•  "), size)
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", t)):
        if part:
            set_font(p.add_run(part), size, bold=(i % 2 == 1))
    return p


_bm = [100]
HEADINGS = []


def heading2(num, title, new_page=True):
    p = d.add_paragraph(style="Heading 2")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.page_break_before = new_page
    r = p.add_run(f"{num}. {title}" if num else title)
    set_font(r, 18, bold=True)
    _bm[0] += 1
    name = f"_Toc{_bm[0]}"
    s = OxmlElement("w:bookmarkStart"); s.set(qn("w:id"), str(_bm[0])); s.set(qn("w:name"), name)
    e = OxmlElement("w:bookmarkEnd"); e.set(qn("w:id"), str(_bm[0]))
    p._p.insert(1 if p._p.pPr is not None else 0, s); p._p.append(e)
    HEADINGS.append((num, title, name))
    return p


def heading4(title):
    p = d.add_paragraph(style="Heading 4")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_font(p.add_run(title), 13, bold=True)
    return p


def image(path, width=6.2, caption=None):
    p = new_p(align=WD_ALIGN_PARAGRAPH.CENTER, after=2, keep_next=bool(caption))
    p.add_run().add_picture(path, width=Inches(width))
    if caption:
        c = new_p(align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
        set_font(c.add_run(caption), 10, italic=True)


def code(src, size=7.5):
    lines = src.split("\n")
    for i in range(0, len(lines), 45):
        p = new_p(align=WD_ALIGN_PARAGRAPH.LEFT, after=0)
        shade(p._p.get_or_add_pPr(), "F3F4F6")
        chunk = lines[i:i + 45]
        for j, ln in enumerate(chunk):
            r = p.add_run(ln.replace("\t", "    "))
            set_font(r, size, name="Courier New")
            if j < len(chunk) - 1:
                r.add_break()
    new_p(after=4)


def set_cell(cell, t, size=10, bold=False, fill=None, color=None, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_after = Pt(1)
    set_font(p.add_run(str(t)), size, bold=bold, color=color)
    if fill:
        tcpr = cell._tc.get_or_add_tcPr(); shade(tcpr, fill)


def table(headers, rows, widths, size=9.5, highlight=None):
    t = d.add_table(rows=1, cols=len(headers))
    tblpr = t._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{edge}"); b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "4"); b.set(qn("w:color"), "808080"); borders.append(b)
    tblpr.append(borders)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblpr.append(lay)
    for i, h in enumerate(headers):
        set_cell(t.rows[0].cells[i], h, size, bold=True, fill="D9EAD3")
    for row in rows:
        cells = t.add_row().cells
        hl = highlight(row) if highlight else None
        for i, v in enumerate(row):
            set_cell(cells[i], v, size, fill="FFF2CC" if hl else None, bold=bool(hl and i == 0))
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Inches(w)
    trpr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); trpr.append(th)
    new_p(after=6)
    return t


def landscape_section():
    s = d.add_section(WD_SECTION.NEW_PAGE)
    s.orientation = WD_ORIENT.LANDSCAPE
    s.page_width, s.page_height = Inches(11.69), Inches(8.27)
    s.left_margin = s.right_margin = Inches(0.8)
    s.top_margin, s.bottom_margin = Inches(1.15), Inches(1.15)
    sp = s._sectPr
    for tag in ("w:titlePg", "w:pgNumType"):
        el = sp.find(qn(tag))
        if el is not None: sp.remove(el)
    return s


def portrait_section():
    s = d.add_section(WD_SECTION.NEW_PAGE)
    s.orientation = WD_ORIENT.PORTRAIT
    s.page_width, s.page_height = Inches(8.27), Inches(11.69)
    s.left_margin = s.right_margin = Inches(0.79)
    s.top_margin, s.bottom_margin = Inches(1.17), Inches(1.37)
    sp = s._sectPr
    for tag in ("w:titlePg", "w:pgNumType"):
        el = sp.find(qn(tag))
        if el is not None: sp.remove(el)
    return s


# ---------------------------------------------------------------- template surgery
els = list(body)
paras = {i: e for i, e in enumerate(els)}
rubric_tbl = copy.deepcopy(els[84])
toc_tbl = els[29]
abstract_head = els[23]
from docx.text.paragraph import Paragraph  # noqa: E402


def replace_text(p_el, new):
    p = Paragraph(p_el, d)
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)
    p.runs[0].text = new


replace_text(els[13], TITLE)
replace_text(els[20], "Class of Prof.  [FACULTY NAME]")
# remove abstract instructions (24-28) and everything after the TOC table except sectPr
for i in range(24, 29):
    body.remove(els[i])
for i in range(30, len(els)):
    if els[i].tag != qn("w:sectPr"):
        body.remove(els[i])

# header project title
for sec in d.sections:
    for hdr in (sec.header, sec.first_page_header):
        for p in hdr.paragraphs:
            for r in p.runs:
                if "<Project Title>" in r.text:
                    r.text = r.text.replace("<Project Title>", TITLE)
        for t in hdr._element.iter(qn("w:t")):
            if t.text and "<Project Title>" in t.text:
                t.text = t.text.replace("<Project Title>", TITLE)

# abstract paragraphs, inserted right after the "Abstract" heading paragraph
ABSTRACT = [
    "Commercial fleets in India operate hundreds of vehicles across several branches, yet maintenance schedules, fuel purchases, insurance renewals, accidents and trips are frequently tracked in disconnected spreadsheets. This leads to missed services, unnoticed fuel leakage, uninsured trips and no reliable view of the real cost of running each vehicle.",
    "The Smart Vehicle Fleet Management & Analytics System is a full-stack database application that centralises these records in a normalised PostgreSQL 16 database of 16 relations, protected by primary, foreign and unique keys, CHECK constraints, range-exclusion constraints, four triggers, three analytical functions, one stored procedure and four reporting views. Live vehicle telemetry (position, speed, fuel level and engine temperature) is held in Redis as hashes with a time-to-live and a geospatial index, and the dashboard query is cached there as well.",
    "A FastAPI service exposes role-based, JWT-secured REST endpoints, and a Next.js (App Router) interface presents operational pages and an analytics dashboard for fuel, maintenance, utilisation and efficiency. Three roles (admin, fleet manager and viewer) are enforced both in the API and with PostgreSQL roles. The seeded data set contains 50 vehicles, 30 drivers, 250 trips, 500 fuel purchases and 100 maintenance records, and the integration tests exercise authentication, business-rule rejection and the Redis create/read/update/delete cycle.",
]
anchor = abstract_head
for t in ABSTRACT:
    np_ = OxmlElement("w:p"); anchor.addnext(np_); anchor = np_
    p = Paragraph(np_, d); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(8)
    set_font(p.add_run(t), 12)

pb = OxmlElement("w:p"); toc_tbl.addprevious(pb)
Paragraph(pb, d).add_run().add_break(WD_BREAK.PAGE)

# ---------------------------------------------------------------- 1. Introduction
heading2(1, "Introduction")
heading4("Problem Statement")
text("Fleet operators need one trustworthy place that answers questions such as: which vehicles are due for service, which have uninsured or expiring policies, what does each vehicle really cost per kilometre, which drivers and routes perform best, and where is every vehicle right now. Today these answers are scattered across paper logs and spreadsheets, so decisions are late and errors (an odometer reading that goes backwards, a trip on a lapsed policy, a vehicle double-booked to two drivers) go unnoticed.")
text("This project builds a **Smart Vehicle Fleet Management & Analytics System** that stores the fleet’s operational history in a relational database which enforces the business rules itself, adds a NoSQL store for fast-changing live telemetry and cached analytics, and offers a secure web application with role-based access for administrators, fleet managers and read-only viewers.")

# ---------------------------------------------------------------- 2. URS
heading2(2, "User Requirements Specification")
heading4("Functional requirements")
for t in [
    "**Master data:** maintain manufacturers, vehicle types, branches, vehicles, drivers, routes, maintenance types and service centres.",
    "**Operations:** record trips (atomically, with validation), fuel purchases, maintenance, accidents, insurance policies and other expenses; assign drivers to vehicles without time overlap.",
    "**Business rules in the database:** valid registration format, non-decreasing odometers, a trip needs valid insurance on its date, a completed service refreshes the next-service schedule, and trip closing is handled by a stored procedure.",
    "**Analytics:** dashboard KPIs, monthly fuel and maintenance spend, utilisation, fuel efficiency, service alerts, insurance expiry alerts, and cost/efficiency insights built from views and functions.",
    "**Live telemetry (NoSQL):** store the latest position, speed, fuel level and engine temperature per vehicle with an expiry; update individual readings; delete; and find vehicles near a point.",
    "**Security:** username/password login issuing JWTs; three roles with different privileges; database-level roles for read-only and manager access.",
]:
    bullet(t)
heading4("Non-functional requirements")
for t in [
    "Data integrity first: constraints and triggers guarantee correctness even for direct SQL access.",
    "Responsiveness: indexes on history access paths and a 60-second Redis cache for the dashboard (about 43 ms uncached versus 3 ms cached in local testing).",
    "Reproducibility: one `docker compose up` starts PostgreSQL, Redis, the API and the Next.js application with seeded data.",
]:
    bullet(t)
heading4("User roles")
table(["Role", "Privileges"], [
    ["admin", "Full access to every page and API endpoint, including deletes and removal of telemetry."],
    ["fleet_manager", "Read everything; create and update operational records, trips and telemetry; cannot delete."],
    ["viewer", "Read-only access to dashboards, lists and telemetry."],
], [1.5, 5.2])
heading4("Technology stack and justification")
table(["Layer", "Technology", "Why it fits this problem"], [
    ["Relational database", "PostgreSQL 16", "Fleet data is highly relational with strict rules. PostgreSQL offers CHECK and generated columns, range-exclusion constraints (btree_gist) to stop overlapping assignments, PL/pgSQL triggers, procedures, views and window/recursive SQL."],
    ["NoSQL database", "Redis 7", "Telemetry is write-heavy, tiny, schema-light and only the latest value matters. Redis hashes, per-key TTL and GEOSEARCH give sub-millisecond reads and automatic expiry of stale vehicles."],
    ["Backend API", "FastAPI + SQLAlchemy + Pydantic", "Typed request validation, automatic OpenAPI documentation, dependency-injected JWT and role checks, and clean transaction control for trip creation."],
    ["Frontend", "Next.js 15 (App Router), React 19, Tailwind CSS, Recharts", "File-system routing for each page, a shared authenticated shell, static generation of list routes and rich charts for analytics."],
    ["Authentication", "JWT (HS256) + bcrypt, PostgreSQL roles", "Stateless API authentication with salted password hashes; database roles add defence in depth."],
    ["Deployment", "Docker Compose", "Identical environment for every evaluator; the database seeds itself on first start."],
], [1.3, 1.8, 3.6], size=9)
heading4("Justification for the NoSQL choice (Redis)")
text("Storing a reading every few seconds per vehicle in PostgreSQL would flood the transactional tables with rows nobody queries after a few minutes. Redis keeps only the latest reading, expires it automatically after 15 minutes if a vehicle stops reporting, and its geospatial index answers “which vehicles are within 50 km of this depot?” directly. The same server doubles as a cache for the dashboard aggregate. Durable history, money and compliance data stay in PostgreSQL, where ACID guarantees matter.")

# ---------------------------------------------------------------- 3. ER model
heading2(3, "E-R Model")
heading4("List of Entities (weak entities highlighted)")
ENT = [
    ["manufacturers", "manufacturer_id", "name, country", "Strong"],
    ["vehicle_types", "vehicle_type_id", "name, category, default_fuel_type, expected_kmpl", "Strong"],
    ["branches", "branch_id", "name, city, state, phone", "Strong"],
    ["vehicles", "vehicle_id", "registration_number, chassis_number, purchase_date, current_odometer, next_service_*, status", "Strong"],
    ["drivers", "driver_id", "full_name, license_number, license_expiry, joining_date, phone, status", "Strong"],
    ["routes", "route_id", "route_name, origin, destination, planned_distance_km, estimated_duration_minutes", "Strong"],
    ["trips", "trip_id", "start/end time, start/end odometer, status, notes", "Strong"],
    ["fuel_transactions", "fuel_transaction_id", "transaction_date, fuel_type, litres, price_per_litre, total_cost, odometer, fuel_station", "Strong"],
    ["maintenance_types", "maintenance_type_id", "name, service_interval_km, service_interval_days", "Strong"],
    ["service_centers", "service_center_id", "name, city, phone, is_authorized", "Strong"],
    ["maintenance", "maintenance_id", "service_date, odometer, cost, description, next_service_date/odometer", "Strong"],
    ["accidents", "accident_id", "accident_date, location, severity, estimated_damage, description", "Strong"],
    ["insurance", "insurance_id", "provider, policy_number, start_date, expiry_date, premium, coverage_amount", "WEAK (existence-dependent on vehicles; ON DELETE CASCADE)"],
    ["expenses", "expense_id", "expense_date, category, amount, description", "Strong"],
    ["vehicle_assignments", "assignment_id", "assigned_from, assigned_to, notes", "Strong (relationship entity, see §4)"],
    ["users", "user_id", "username, password_hash, role, is_active, created_at", "Strong"],
    ["Telemetry (Redis hash)", "telemetry:vehicle:{id}", "latitude, longitude, speed_kmph, fuel_level_pct, engine_temp_c, updated_at", "NoSQL document – not in the ER diagram"],
]
table(["Entity", "Primary key", "Attributes", "Type"], ENT, [1.35, 1.35, 2.6, 1.4], size=8.5, highlight=lambda r: r[3].startswith("WEAK"))
text("Note: every table has a surrogate primary key, so no table is *identifier-dependent* in the strict textbook sense. **insurance** is the one entity that cannot exist without its vehicle (a policy covers exactly one vehicle and is deleted with it), so it is treated as the weak entity and highlighted above.", size=11)
heading4("Non-simple attributes")
table(["Kind", "Entity.Attribute", "How it is modelled"], [
    ["Composite", "vehicles.registration_number", "State code + RTO code + series + 4-digit number (e.g. KA01AB1201). Stored as one column; a regular-expression CHECK validates every component."],
    ["Composite", "Telemetry position", "latitude + longitude stored as hash fields and also indexed as one geospatial member in Redis."],
    ["Derived", "fuel_transactions.total_cost", "GENERATED ALWAYS AS (ROUND(litres × price_per_litre, 2)) STORED."],
    ["Derived", "trips distance (end_odometer − start_odometer)", "Computed in queries and the trips API; never stored twice."],
    ["Derived", "vehicle_performance_view.fuel_efficiency_kmpl", "Total completed-trip distance ÷ litres purchased, computed in the view."],
    ["Derived", "vehicle_cost_view.total_operating_cost", "Sum of fuel, maintenance, insurance and other expenses."],
    ["Derived", "maintenance_due_view.service_status", "Overdue / due soon / scheduled, calculated from next service date and odometer."],
    ["Derived (trigger-maintained)", "vehicles.current_odometer, next_service_date, next_service_odometer", "Updated by triggers after fuel, maintenance and completed-trip inserts."],
    ["Enumerated", "vehicles.status, drivers.status, trips.status, accidents.severity", "PostgreSQL ENUM types."],
    ["Multivalued", "none stored in a single column", "Repeating groups (policies, fuel purchases, services, accidents, assignments) are separate relations in first normal form."],
], [1.25, 2.1, 3.35], size=9)
heading4("Relationships and cardinalities")
table(["Relationship", "Entities", "Cardinality / participation"], [
    ["manufactures", "manufacturers – vehicle_types", "1 : N (total on vehicle_types)"],
    ["is of type", "vehicle_types – vehicles", "1 : N (total on vehicles)"],
    ["based at", "branches – vehicles", "1 : N (total on vehicles)"],
    ["employs", "branches – drivers", "1 : N (total on drivers)"],
    ["is insured by", "vehicles – insurance", "1 : N (total on insurance)"],
    ["is assigned to", "vehicles – drivers (via vehicle_assignments)", "M : N, time-bounded, no overlap per vehicle or per driver"],
    ["performs (ternary)", "vehicles – drivers – routes (trips)", "Each trip links exactly one vehicle, one driver and one route"],
    ["refuels", "vehicles – fuel_transactions; drivers – fuel_transactions", "1 : N each (driver optional)"],
    ["serviced by (ternary)", "vehicles – maintenance_types – service_centers (maintenance)", "Each service record links one vehicle, one type and one centre"],
    ["involved in", "vehicles – accidents; drivers – accidents", "1 : N each (driver optional)"],
    ["incurs", "vehicles – expenses", "1 : N (total on expenses)"],
], [1.4, 2.9, 2.4], size=9)

landscape_section()
heading4("ER Diagram")
image(os.path.join(HERE, "ER_Diagram.png"), width=8.4, caption="Figure 1 – E-R diagram of the Smart Fleet database (docs/ER_Diagram.png / .svg)")
portrait_section()

# ---------------------------------------------------------------- 4. Relational model
heading2(4, "Relational Model", new_page=False)
heading4("List of Relations (those that are not entities in the ER model are labelled)")
REL = [
    ["manufacturers", "Entity relation", "manufacturer_id", "—"],
    ["vehicle_types", "Entity relation", "vehicle_type_id", "manufacturer_id → manufacturers"],
    ["branches", "Entity relation", "branch_id", "—"],
    ["vehicles", "Entity relation", "vehicle_id", "vehicle_type_id → vehicle_types; branch_id → branches"],
    ["drivers", "Entity relation", "driver_id", "branch_id → branches"],
    ["routes", "Entity relation", "route_id", "—"],
    ["insurance", "Entity relation (weak)", "insurance_id", "vehicle_id → vehicles (CASCADE)"],
    ["vehicle_assignments", "RELATIONSHIP relation – not an entity (M:N vehicles–drivers)", "assignment_id", "vehicle_id → vehicles; driver_id → drivers"],
    ["trips", "RELATIONSHIP relation – ternary vehicles–drivers–routes (carries own attributes)", "trip_id", "vehicle_id, driver_id, route_id"],
    ["fuel_transactions", "Entity relation", "fuel_transaction_id", "vehicle_id → vehicles; driver_id → drivers (nullable)"],
    ["maintenance_types", "Entity relation", "maintenance_type_id", "—"],
    ["service_centers", "Entity relation", "service_center_id", "—"],
    ["maintenance", "RELATIONSHIP relation – ternary vehicles–maintenance_types–service_centers", "maintenance_id", "vehicle_id, maintenance_type_id, service_center_id"],
    ["accidents", "Entity relation", "accident_id", "vehicle_id → vehicles; driver_id → drivers (nullable)"],
    ["expenses", "Entity relation", "expense_id", "vehicle_id → vehicles"],
    ["users", "Entity relation (security)", "user_id", "—"],
]
table(["Relation", "Origin in the ER model", "Primary key", "Foreign keys"], REL, [1.35, 2.2, 1.3, 1.85], size=8.5, highlight=lambda r: r[1].startswith("RELATIONSHIP"))
heading4("Keys and constraints")
for t in [
    "**Unique keys:** manufacturers.name, branches.name, vehicles.registration_number and chassis_number, drivers.license_number and phone, insurance.policy_number, routes.route_name, users.username, (manufacturer_id, name) on vehicle_types.",
    "**CHECK constraints:** registration format, odometer ≥ 0, litres/price > 0, expiry_date > start_date, end_time ≥ start_time, end_odometer ≥ start_odometer, completed trips must have end time and odometer, maintenance next dates not before the service, expense category list, user role list.",
    "**Exclusion constraints:** a vehicle and a driver can each hold only one assignment at any instant (GiST over tstzrange).",
    "**Normalization:** the schema is in third normal form: manufacturer is separated from vehicle type, type from vehicle, maintenance type and service centre from maintenance, and branch from drivers and vehicles, so no update anomalies arise (see docs/normalization.md).",
]:
    bullet(t, 11.5)

landscape_section()
heading4("Schema Diagram")
image(os.path.join(A, "schema_diagram.png"), width=9.6, caption="Figure 2 – Relational schema (PK = primary key, FK = foreign key; arrows point to the referenced table)")
portrait_section()

# ---------------------------------------------------------------- 5. DDL
heading2(5, "SQL DDL Statements")
text("The DDL below is the content of the SQL scripts executed (in this order) when the PostgreSQL container initialises: schema, indexes, triggers, functions/procedures, views and roles.", size=11)
for title, f in [("5.1 Tables, types and constraints – database/schema.sql", "database/schema.sql"), ("5.2 Indexes – database/indexes.sql", "database/indexes.sql"),
                 ("5.3 Triggers – database/triggers.sql", "database/triggers.sql"), ("5.4 Functions and stored procedure – database/procedures.sql", "database/procedures.sql"),
                 ("5.5 Views – database/views.sql", "database/views.sql"), ("5.6 Database roles (RBAC) – database/roles.sql", "database/roles.sql")]:
    heading4(title)
    code(read(os.path.join(ROOT, f)), 7)

# ---------------------------------------------------------------- 6. DML
heading2(6, "SQL DML Statements")
heading4("6.1 INSERT / UPDATE / DELETE, stored procedure and rule violations (execution log)")
text("The script docs/dml_demo.sql runs inside one transaction that is rolled back, so the seeded data is not altered. Lines beginning with ERROR show the database rejecting invalid data.", size=11)
log = read(os.path.join(A, "dml_log.txt"))
log = "\n".join(l for l in log.split("\n") if not l.startswith("psql:docs/dml_demo.sql") or "ERROR" in l)
code(log.replace("psql:docs/dml_demo.sql:", "line "), 7)
heading4("6.2 Analytical queries (joins, nested, correlated, recursive, window functions) – docs/sql_queries.sql")
code(read(os.path.join(HERE, "sql_queries.sql")), 7)

# ---------------------------------------------------------------- 7. NoSQL
heading2(7, "NoSQL / Vector Database Commands")
text("Redis 7 stores one hash per vehicle (`telemetry:vehicle:{id}`) with a 900-second TTL, a sorted-set geospatial index (`fleet:positions`) and a JSON string cache (`cache:dashboard`, 60 s). The commands below were executed against the live server (docs/report_assets/redis_log.txt).", size=11)
table(["Key", "Type", "Content", "Expiry"], [
    ["telemetry:vehicle:{vehicle_id}", "Hash", "latitude, longitude, speed_kmph, fuel_level_pct, engine_temp_c, updated_at", "900 s"],
    ["fleet:positions", "Geo (sorted set)", "member = vehicle_id at (longitude, latitude)", "none (member removed on delete)"],
    ["cache:dashboard", "String (JSON)", "Result of /api/analytics/dashboard", "60 s"],
], [2.0, 1.1, 2.6, 1.0], size=9)
heading4("Create / Read / Update / Delete – redis-cli session")
code(read(os.path.join(A, "redis_log.txt")), 8)
heading4("REST endpoints backed by Redis (backend/app/routers/telemetry.py)")
table(["Operation", "Endpoint", "Redis commands", "Roles"], [
    ["Create / upsert", "PUT /api/telemetry/{vehicle_id}", "HSET + EXPIRE + GEOADD (pipeline)", "admin, fleet_manager"],
    ["Read one", "GET /api/telemetry/{vehicle_id}", "HGETALL, TTL", "all authenticated"],
    ["Read all", "GET /api/telemetry", "SCAN + HGETALL", "all authenticated"],
    ["Read nearby", "GET /api/telemetry/nearby/search", "GEOSEARCH … BYRADIUS … WITHDIST", "all authenticated"],
    ["Update", "PATCH /api/telemetry/{vehicle_id}", "EXISTS + HSET (changed fields only)", "admin, fleet_manager"],
    ["Delete", "DELETE /api/telemetry/{vehicle_id}", "DEL + ZREM (pipeline)", "admin"],
    ["Cache", "GET /api/analytics/dashboard", "GET / SET … EX 60", "all authenticated"],
], [1.1, 2.3, 2.1, 1.2], size=9)
text("No vector database is used: the system has no embedding or similarity-search requirement, so Redis (key-value / geospatial) is the NoSQL component.", size=11)

# ---------------------------------------------------------------- 8. Results
heading2(8, "Results")
heading4("Resulting tables’ screenshots (first rows of each table)")
for n, t in enumerate(["manufacturers", "vehicle_types", "branches", "vehicles", "drivers", "routes", "trips", "fuel_transactions",
          "maintenance_types", "service_centers", "maintenance", "accidents", "insurance", "expenses", "vehicle_assignments", "users"], 1):
    image(os.path.join(A, f"tbl_{t}.png"), width=6.6, caption=f"Figure {2+n}")
heading4("Views, functions and query results")
for k, cap in [("q_view_vehicle_performance", "View"), ("q_view_maintenance_due", "View"), ("q_func_operating_cost", "Function"), ("q_func_driver_perf", "Function"),
               ("q_join", "Join query"), ("q_correlated", "Correlated subquery"), ("q_recursive", "Recursive CTE"), ("q_window", "Window function")]:
    image(os.path.join(A, f"{k}.png"), width=6.3, caption=cap)

# ---------------------------------------------------------------- 9. Tree
heading2(9, "Next.js Project Tree Structure")
text("The frontend uses the Next.js App Router. Each folder under app/ is a route; the shared sidebar shell checks the JWT and redirects to /login when it is missing.", size=11)
code(read(os.path.join(A, "frontend_tree.txt")), 9)
table(["Route", "File", "Purpose"], [
    ["/login", "app/login/page.tsx", "Sign-in form calling POST /api/auth/login"],
    ["/dashboard", "app/dashboard/page.tsx", "KPI cards, charts and service alerts"],
    ["/vehicles, /drivers, /trips, /fuel, /maintenance, /accidents, /insurance, /expenses", "app/[section]/page.tsx", "Searchable list pages, pre-rendered for each known section"],
    ["/insights", "app/insights/page.tsx", "High cost, high maintenance and poor efficiency vehicles"],
], [2.4, 1.9, 2.4], size=9)

# ---------------------------------------------------------------- 10. Screens
heading2(10, "Sample Screenshots of Application Code and Demo")
for f, cap in [("app_login.png", "Login page (Next.js /login)"), ("app_dashboard.png", "Dashboard – KPIs and charts backed by views and the Redis cache"),
               ("app_vehicles.png", "Vehicles list page"), ("app_trips.png", "Trips list page (JOIN across vehicles, drivers and routes)"),
               ("app_insights.png", "Insights page"), ("api_docs.png", "FastAPI OpenAPI (Swagger) documentation at /api/docs")]:
    image(os.path.join(A, f), width=6.2 if f != "app_dashboard.png" else 4.6, caption=cap)
heading4("Application code")
for f, cap in [("code_telemetry.png", "Redis telemetry router"), ("code_services.png", "Transactional trip creation (services.py)"), ("code_shell.png", "Authenticated Next.js shell")]:
    image(os.path.join(A, f), width=6.3, caption=cap)
heading4("Automated test run")
code(read(os.path.join(A, "pytest_log.txt")), 9)

# ---------------------------------------------------------------- 11. Rubrics
heading2(11, "Evaluation Rubrics – Completion Status")
rt = copy.deepcopy(rubric_tbl)
body.insert(list(body).index(body.findall(qn("w:sectPr"))[-1]), rt)
from docx.table import Table  # noqa: E402
tbl = Table(rt, d)
STATUS = [
    "Completed – ER diagram, relational schema, keys, relationships, CHECK / UNIQUE / exclusion constraints.",
    "Completed – PostgreSQL DDL with constraints (16 tables) and Redis NoSQL store with justification.",
    "Completed – INSERT / UPDATE / DELETE log; join, nested, correlated and recursive queries (26 documented).",
    "Completed – 4 triggers, 3 functions, 1 stored procedure, 4 views, CTEs; Redis create/read/update/delete.",
    "Completed – Next.js App Router interface, FastAPI backend, PostgreSQL + Redis integration.",
    "Completed – JWT login (frontend and backend), three roles enforced in API and as PostgreSQL roles.",
    "Partially complete – documentation, tests and demo done; the Git repository has no commits yet, so the GitHub push, commit history and individual-contribution notes are pending.",
]
for i, s in enumerate(STATUS, start=1):
    set_cell(tbl.rows[i].cells[3], s, 9.5)

# ---------------------------------------------------------------- TOC table fill
page_est = {1: 4, 2: 5, 3: 7, 4: 12, 5: 15, 6: 22, 7: 25, 8: 27, 9: 36, 10: 37, 11: 44}  # estimates; Word refreshes the PAGEREF fields on open
toc = __import__("docx").table.Table(toc_tbl, d)
bm = {n: name for n, _, name in HEADINGS}
for i in range(1, 12):
    row = toc.rows[i + 1]
    set_cell(row.cells[0], f"{i}.", 12, align=WD_ALIGN_PARAGRAPH.CENTER)
    c = row.cells[2]; c.text = ""
    p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    def fld(kind, instr=None, cached=None):
        r = p.add_run(); set_font(r, 12)
        if kind == "begin":
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), "begin"); r._r.append(fc)
        elif kind == "instr":
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instr; r._r.append(it)
        elif kind == "sep":
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), "separate"); r._r.append(fc)
        elif kind == "text":
            r.text = cached
        else:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), "end"); r._r.append(fc)
    fld("begin"); fld("instr", f" PAGEREF {bm[i]} \\h "); fld("sep"); fld("text", cached=str(page_est[i])); fld("end")

# make Word refresh the page-number fields when the file is opened
settings = d.settings.element
uf = OxmlElement("w:updateFields"); uf.set(qn("w:val"), "true"); settings.append(uf)

out = os.path.join(HERE, "DBMS_Project_Report.docx")
d.save(out)
print("saved", out)
