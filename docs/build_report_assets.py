"""Generates the images used by the DBMS project report (schema diagram, table/query result snapshots)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import psycopg

OUT = os.path.join(os.path.dirname(__file__), "report_assets")
os.makedirs(OUT, exist_ok=True)
DSN = os.environ.get("REPORT_DSN", "postgresql://fleet_admin:change_me_locally@localhost:5432/smart_fleet")
conn = psycopg.connect(DSN)
cur = conn.cursor()
plt.rcParams["font.family"] = "DejaVu Sans"


def fmt(v, w=24):
    s = "—" if v is None else str(v)
    return s if len(s) <= w else s[: w - 1] + "…"


def render_table(headers, rows, title, path, footer=None):
    fig_w = min(max(6.5, 0.95 * len(headers)), 11)
    row_h = 0.26
    fig = plt.figure(figsize=(fig_w, 0.5 + row_h * (len(rows) + 1)), dpi=170)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1 - 0.4 / (0.5 + row_h * (len(rows) + 1))])
    ax.axis("off")
    fig.text(0.005, 0.97, title + (f"    -- {footer}" if footer else ""), fontsize=7.5, fontweight="bold", color="#152235", va="top")
    tbl = ax.table(cellText=[[fmt(c) for c in r] for r in rows], colLabels=[h.replace("_", " ") for h in headers], cellLoc="left", bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(6.8)
    tbl.auto_set_column_width(list(range(len(headers))))
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        cell.set_linewidth(0.5)
        if r == 0:
            cell.set_facecolor("#1a936f"); cell.get_text().set_color("white"); cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor("#f8fafc" if r % 2 else "white")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def run(sql):
    cur.execute(sql)
    return [d.name for d in cur.description], cur.fetchall()


TABLES = ["manufacturers", "vehicle_types", "branches", "vehicles", "drivers", "routes", "trips", "fuel_transactions",
          "maintenance_types", "service_centers", "maintenance", "accidents", "insurance", "expenses", "vehicle_assignments", "users"]
counts = {}
for t in TABLES:
    cur.execute(f"SELECT count(*) FROM {t}")
    counts[t] = cur.fetchone()[0]
    sel = "user_id, username, role, is_active, created_at, left(password_hash, 14) || '…' AS password_hash" if t == "users" else "*"
    cols, rows = run(f"SELECT {sel} FROM {t} ORDER BY 1 LIMIT 6")
    if not rows:
        rows = [["(no rows – populated through the API / vehicle assignment workflow)"] + [""] * (len(cols) - 1)]
    render_table(cols, rows, f"{t}  ({counts[t]} rows)", f"{OUT}/tbl_{t}.png", footer=f"SELECT {sel} FROM {t} ORDER BY 1 LIMIT 6;")

QUERIES = {
    "q_view_vehicle_performance": ("vehicle_performance_view (top 6 by distance)", "SELECT registration_number, vehicle_type, total_trips, total_distance, fuel_litres, fuel_cost, maintenance_cost, fuel_efficiency_kmpl FROM vehicle_performance_view ORDER BY total_distance DESC, registration_number LIMIT 6"),
    "q_view_maintenance_due": ("maintenance_due_view (service alerts)", "SELECT * FROM maintenance_due_view WHERE service_status <> 'scheduled' ORDER BY next_service_date LIMIT 6"),
    "q_func_operating_cost": ("SELECT * FROM vehicle_operating_cost(1, NULL, NULL);", "SELECT * FROM vehicle_operating_cost(1, NULL, NULL)"),
    "q_func_driver_perf": ("SELECT * FROM driver_performance(1, NULL, NULL);", "SELECT * FROM driver_performance(1, NULL, NULL)"),
    "q_recursive": ("Recursive CTE – continuous monthly fuel spend", "WITH RECURSIVE months(m) AS (SELECT date_trunc('month',MIN(transaction_date)) FROM fuel_transactions UNION ALL SELECT m + INTERVAL '1 month' FROM months WHERE m < (SELECT date_trunc('month',MAX(transaction_date)) FROM fuel_transactions)) SELECT to_char(m,'YYYY-MM') AS month, COALESCE(SUM(f.total_cost),0) AS fuel_cost FROM months LEFT JOIN fuel_transactions f ON date_trunc('month',f.transaction_date)=m GROUP BY m ORDER BY m"),
    "q_correlated": ("Correlated subquery – latest policy per vehicle (6 rows)", "SELECT i.vehicle_id, i.policy_number, i.provider, i.expiry_date FROM insurance i WHERE expiry_date=(SELECT MAX(i2.expiry_date) FROM insurance i2 WHERE i2.vehicle_id=i.vehicle_id) ORDER BY 1 LIMIT 6"),
    "q_join": ("Multi-table JOIN – trip manifest (6 rows)", "SELECT t.trip_id, v.registration_number, d.full_name, r.route_name, t.status FROM trips t JOIN vehicles v USING(vehicle_id) JOIN drivers d USING(driver_id) JOIN routes r USING(route_id) ORDER BY t.trip_id LIMIT 6"),
    "q_window": ("Window function – cost rank (top 6)", "SELECT registration_number, total_operating_cost, DENSE_RANK() OVER(ORDER BY total_operating_cost DESC) cost_rank FROM vehicle_cost_view ORDER BY cost_rank LIMIT 6"),
}
for key, (title, sql) in QUERIES.items():
    cols, rows = run(sql)
    render_table(cols, rows, title, f"{OUT}/{key}.png")

# ---------- Relational schema diagram ----------
cur.execute("""SELECT c.table_name, c.column_name, c.data_type, c.is_nullable FROM information_schema.columns c
               WHERE c.table_schema='public' AND c.table_name = ANY(%s) ORDER BY c.table_name, c.ordinal_position""", (TABLES,))
cols = {}
for t, c, dt, nl in cur.fetchall():
    cols.setdefault(t, []).append([c, dt, nl])
cur.execute("""SELECT tc.table_name, kcu.column_name FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu
               ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema WHERE tc.constraint_type='PRIMARY KEY' AND tc.table_schema='public'""")
pk = set(cur.fetchall())
cur.execute("""SELECT tc.table_name, kcu.column_name, ccu.table_name FROM information_schema.table_constraints tc
               JOIN information_schema.key_column_usage kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema
               JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name=tc.constraint_name AND ccu.table_schema=tc.table_schema
               WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public'""")
fks = cur.fetchall()
fkcols = {(a, b) for a, b, _ in fks}

# grid layout: (column, row)
POS = {"manufacturers": (0, 0), "vehicle_types": (1, 0), "branches": (2, 0), "routes": (3, 0), "users": (4, 0),
       "insurance": (0, 1), "vehicles": (1, 1), "drivers": (2, 1), "vehicle_assignments": (3, 1), "service_centers": (4, 1),
       "fuel_transactions": (0, 2), "trips": (1, 2), "accidents": (2, 2), "maintenance": (3, 2), "maintenance_types": (4, 2),
       "expenses": (1, 3)}
W, GAP_X, GAP_Y, LH = 3.1, 0.55, 0.7, 0.26
fig, ax = plt.subplots(figsize=(18.5, 12.2), dpi=150)
fig.patch.set_facecolor("#f8fafc"); ax.set_facecolor("#f8fafc")
rowh = {}
for t, (cx, cy) in POS.items():
    rowh[cy] = max(rowh.get(cy, 0), (len(cols[t]) + 1) * LH + 0.15)
ytop = {0: 0}
for r in range(1, 4):
    ytop[r] = ytop[r - 1] - rowh[r - 1] - GAP_Y
box = {}
for t, (cx, cy) in POS.items():
    x, y = cx * (W + GAP_X), ytop[cy]
    h = (len(cols[t]) + 1) * LH + 0.15
    box[t] = (x, y, W, h)
    ax.add_patch(FancyBboxPatch((x, y - h), W, h, boxstyle="round,pad=0,rounding_size=0.08", fc="white", ec="#94a3b8", lw=1.1, zorder=2))
    ax.add_patch(FancyBboxPatch((x, y - LH - 0.05), W, LH + 0.05, boxstyle="round,pad=0,rounding_size=0.08", fc="#1a936f", ec="#1a936f", zorder=3))
    ax.text(x + 0.12, y - LH / 2 - 0.03, t, color="white", fontsize=9.5, fontweight="bold", va="center", zorder=4)
    for i, (c, dt, nl) in enumerate(cols[t]):
        yy = y - (i + 1) * LH - LH / 2 - 0.12
        tag = "PK" if (t, c) in pk else ("FK" if (t, c) in fkcols else "")
        if tag:
            ax.text(x + 0.1, yy, tag, fontsize=6.5, color="#b45309" if tag == "PK" else "#1d4ed8", fontweight="bold", va="center", zorder=4)
        ax.text(x + 0.45, yy, c, fontsize=7.6, va="center", color="#152235", fontweight="bold" if tag == "PK" else "normal", zorder=4)
        ax.text(x + W - 0.1, yy, {"character varying": "varchar", "timestamp with time zone": "timestamptz", "USER-DEFINED": "enum", "numeric": "numeric", "bigint": "bigint"}.get(dt, dt), fontsize=6.3, ha="right", va="center", color="#64748b", zorder=4)

def anchor(a, b):
    xa, ya, wa, ha = box[a]; xb, yb, wb, hb = box[b]
    ca = (xa + wa / 2, ya - ha / 2); cb = (xb + wb / 2, yb - hb / 2)
    if abs(ca[0] - cb[0]) > abs(ca[1] - cb[1]) * 0.7 and abs(ca[0] - cb[0]) > 1:
        sa = (xa + wa if cb[0] > ca[0] else xa, ca[1]); sb = (xb if cb[0] > ca[0] else xb + wb, cb[1])
    else:
        sa = (ca[0], ya - ha if cb[1] < ca[1] else ya); sb = (cb[0], yb if cb[1] < ca[1] else yb - hb)
    return sa, sb
palette = ["#0ea5e9", "#8b5cf6", "#f59e0b", "#ef4444", "#14b8a6", "#64748b", "#ec4899", "#16a34a"]
for n, (child, col, parent) in enumerate(fks):
    sa, sb = anchor(child, parent)
    ax.annotate("", xy=sb, xytext=sa, arrowprops=dict(arrowstyle="-|>", color=palette[n % len(palette)], lw=1.1, shrinkA=0, shrinkB=0, connectionstyle="arc3,rad=0.06", alpha=0.85), zorder=1)
ax.set_xlim(-0.3, 5 * (W + GAP_X)); ax.set_ylim(ytop[3] - rowh[3] - 0.5, 0.7)
ax.set_title("Smart Fleet – Relational Schema (arrows: foreign key  →  referenced primary key)", loc="left", fontsize=13, fontweight="bold", color="#152235")
ax.axis("off")
fig.savefig(f"{OUT}/schema_diagram.png", bbox_inches="tight", facecolor="#f8fafc")
print("assets done; rows:", counts)
