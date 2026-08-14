import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Earthquake Data Analysis Dashboard",
    page_icon="Logo-PTS.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# THEME / CSS
# ============================================================================
st.markdown(
    """
    <style>
        .main { background-color: #f4f5f7; }
        .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }

        /* Header */
        .dashboard-header {
            background: linear-gradient(90deg, #1f2440 0%, #b5451b 100%);
            padding: 2rem 2.2rem;
            border-radius: 18px;
            margin-bottom: 1.5rem;
            box-shadow: 0 6px 20px rgba(31, 36, 64, 0.25);
        }
        .dashboard-header h1 {
            color: white; font-size: 2.1rem; font-weight: 800; margin: 0;
        }
        .dashboard-header p {
            color: rgba(255,255,255,0.85); font-size: 0.98rem; margin-top: 0.4rem;
        }

        /* KPI cards */
        .kpi-card {
            background: white;
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            border-left: 5px solid #b5451b;
            height: 100%;
        }
        .kpi-label {
            font-size: 0.78rem; font-weight: 700; color: #6b7280;
            text-transform: uppercase; letter-spacing: 0.04em;
        }
        .kpi-value {
            font-size: 1.55rem; font-weight: 800; color: #1f2937; margin-top: 2px;
        }
        .kpi-sub { font-size: 0.78rem; color: #9ca3af; margin-top: 2px; }

        /* Section titles */
        .section-title {
            font-size: 1.15rem; font-weight: 700; color: #1f2937;
            margin: 1.3rem 0 0.7rem 0; padding-bottom: 0.35rem;
            border-bottom: 2px solid #b5451b33;
        }

        /* Query card */
        .query-meta {
            background: white; border-radius: 12px; padding: 0.9rem 1.1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 0.8rem;
        }
        .badge {
            display:inline-block; background:#b5451b1a; color:#b5451b;
            font-size:0.72rem; font-weight:700; padding:2px 10px;
            border-radius:999px; margin-right:6px; text-transform:uppercase;
            letter-spacing:0.03em;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 12px; overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        }

        section[data-testid="stSidebar"] { background-color: #1c1e2b; }
        section[data-testid="stSidebar"] * { color: #f1f1f4 !important; }
        section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] textarea {
            color: #1f2937 !important;
        }

        footer {visibility: hidden;}
        .app-footer {
            text-align:center; color:#9ca3af; font-size:0.8rem;
            margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# DATABASE CONNECTION
# Credentials are read from st.secrets (.streamlit/secrets.toml) or
# environment variables — never hardcoded in source. Example secrets.toml:
#
# [postgres]
# username = "postgres"
# password = "your-password"
# host = "localhost"
# port = 5432
# database = "earthquake_db"
# ============================================================================
@st.cache_resource
def get_engine():
    pg = st.secrets.get("postgres", {}) if hasattr(st, "secrets") else {}
    username = pg.get("username", os.environ.get("PGUSER", "postgres"))
    password = pg.get("password", os.environ.get("PGPASSWORD"))
    host = pg.get("host", os.environ.get("PGHOST", "localhost"))
    port = pg.get("port", os.environ.get("PGPORT", 5432))
    database = pg.get("database", os.environ.get("PGDATABASE", "earthquake_db"))

    if not password:
        st.error(
            "⚠️ No database password found. Set it in `.streamlit/secrets.toml` "
            "under `[postgres]`, or via the `PGPASSWORD` environment variable."
        )
        st.stop()

    return create_engine(
        f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}",
        pool_pre_ping=True,
    )


engine = get_engine()


@st.cache_data(ttl=600)
def run_query(sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, engine)


@st.cache_data(ttl=600)
def get_overview_stats():
    """Best-effort summary stats for the top of the dashboard. Fails soft."""
    stats = {}
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT COUNT(*) FROM earthquakes")).fetchone()
            stats["total"] = row[0] if row else None
    except Exception:
        stats["total"] = None
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT ROUND(AVG(mag)::numeric, 2) FROM earthquakes")).fetchone()
            stats["avg_mag"] = row[0] if row else None
    except Exception:
        stats["avg_mag"] = None
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT MAX(mag) FROM earthquakes")).fetchone()
            stats["max_mag"] = row[0] if row else None
    except Exception:
        stats["max_mag"] = None
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT COUNT(*) FROM earthquakes WHERE tsunami = 1")
            ).fetchone()
            stats["tsunamis"] = row[0] if row else None
    except Exception:
        stats["tsunamis"] = None
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT COUNT(DISTINCT country) FROM earthquakes WHERE country IS NOT NULL")
            ).fetchone()
            stats["countries"] = row[0] if row else None
    except Exception:
        stats["countries"] = None
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT year FROM earthquakes GROUP BY year ORDER BY COUNT(*) DESC LIMIT 1")
            ).fetchone()
            stats["peak_year"] = row[0] if row else None
    except Exception:
        stats["peak_year"] = None
    return stats


# ============================================================================
# QUERY LIBRARY — grouped into categories, numbered for reference
# ============================================================================
QUERY_GROUPS = {
    "⚡ Rankings & Extremes": {
        "Top 10 Strongest Earthquakes": """
            SELECT id, time, place, country, mag, depth_km, strong_destructive_flag
            FROM earthquakes ORDER BY mag DESC LIMIT 10;
        """,
        "Top 10 Deepest Earthquakes": """
            SELECT id, time, place, country, depth_km, mag
            FROM earthquakes ORDER BY depth_km DESC LIMIT 10;
        """,
        "Shallow & Strong Earthquakes (depth < 50km, mag > 7.5)": """
            SELECT id, time, place, country, depth_km, mag
            FROM earthquakes WHERE depth_km < 50 AND mag > 7.5 ORDER BY mag DESC;
        """,
        "Top 5 Places by Earthquake Count": """
            SELECT place, COUNT(*) AS earthquake_count
            FROM earthquakes GROUP BY place ORDER BY earthquake_count DESC LIMIT 5;
        """,
        "High Station Coverage Events (nst > 100)": """
            SELECT id, time, place, mag, nst
            FROM earthquakes WHERE nst > 100 ORDER BY nst DESC;
        """,
    },
    "📊 Magnitude & Type Analysis": {
        "Average Magnitude per Magnitude Type": """
            SELECT "magType", ROUND(AVG(mag)::numeric, 2) AS avg_magnitude, COUNT(*) AS earthquake_count
            FROM earthquakes GROUP BY "magType" ORDER BY avg_magnitude DESC;
        """,
        "Average Magnitude by Alert Level": """
            SELECT alert, COUNT(*) AS earthquake_count, ROUND(AVG(mag)::numeric, 2) AS avg_magnitude
            FROM earthquakes GROUP BY alert ORDER BY avg_magnitude DESC;
        """,
        "Count by Alert Level": """
            SELECT alert, COUNT(*) AS earthquake_count
            FROM earthquakes GROUP BY alert ORDER BY earthquake_count DESC;
        """,
        "Top 5 Countries by Average Magnitude": """
            SELECT country, ROUND(AVG(mag)::numeric, 2) AS avg_magnitude, COUNT(*) AS earthquake_count
            FROM earthquakes GROUP BY country HAVING COUNT(*) > 0
            ORDER BY avg_magnitude DESC LIMIT 5;
        """,
        "Magnitude Difference: Tsunami vs Non-Tsunami": """
            SELECT tsunami, ROUND(AVG(mag)::numeric, 2) AS avg_magnitude, COUNT(*) AS earthquake_count
            FROM earthquakes GROUP BY tsunami ORDER BY tsunami DESC;
        """,
    },
    "🕒 Time-Based Trends": {
        "Year with Most Earthquakes": """
            SELECT year, COUNT(*) AS total_earthquakes
            FROM earthquakes GROUP BY year ORDER BY total_earthquakes DESC LIMIT 1;
        """,
        "Month with Highest Number of Earthquakes": """
            SELECT month, COUNT(*) AS total_earthquakes
            FROM earthquakes GROUP BY month ORDER BY total_earthquakes DESC LIMIT 1;
        """,
        "Day of Week with Most Earthquakes": """
            SELECT day_of_week, COUNT(*) AS total_earthquakes
            FROM earthquakes GROUP BY day_of_week ORDER BY total_earthquakes DESC LIMIT 1;
        """,
        "Earthquakes per Hour of Day": """
            SELECT DATE_PART('hour', CAST(time AS TIMESTAMP)) AS hour_of_day, COUNT(*) AS total_earthquakes
            FROM earthquakes GROUP BY hour_of_day ORDER BY hour_of_day;
        """,
        "Tsunamis Triggered per Year": """
            SELECT year, COUNT(*) AS tsunami_count
            FROM earthquakes WHERE tsunami = 1 GROUP BY year ORDER BY year;
        """,
        "Year-over-Year Growth Rate (Global)": """
            WITH yearly_counts AS (
                SELECT year, COUNT(*) AS total_earthquakes
                FROM earthquakes GROUP BY year
            )
            SELECT year, total_earthquakes,
                   LAG(total_earthquakes) OVER (ORDER BY year) AS previous_year_count,
                   ROUND((
                       (total_earthquakes - LAG(total_earthquakes) OVER (ORDER BY year)) * 100.0
                       / LAG(total_earthquakes) OVER (ORDER BY year)
                   )::numeric, 2) AS yoy_growth_rate
            FROM yearly_counts ORDER BY year;
        """,
    },
    "🛰️ Reporting & Data Quality": {
        "Most Active Reporting Network (net)": """
            SELECT net, COUNT(*) AS total_earthquakes
            FROM earthquakes GROUP BY net ORDER BY total_earthquakes DESC LIMIT 1;
        """,
        "Reviewed vs Automatic Earthquakes (status)": """
            SELECT status, COUNT(*) AS earthquake_count
            FROM earthquakes GROUP BY status ORDER BY earthquake_count DESC;
        """,
        "Count by Earthquake Type": """
            SELECT type, COUNT(*) AS earthquake_count
            FROM earthquakes GROUP BY type ORDER BY earthquake_count DESC;
        """,
        "Count by Data Type (types)": """
            SELECT types, COUNT(*) AS earthquake_count
            FROM earthquakes GROUP BY types ORDER BY earthquake_count DESC;
        """,
        "Lowest Data Reliability Events (gap + rms)": """
            SELECT id, time, place, mag, gap, rms,
                   ROUND(((gap + rms) / 2.0)::numeric, 2) AS reliability_error_score
            FROM earthquakes WHERE gap IS NOT NULL AND rms IS NOT NULL
            ORDER BY reliability_error_score DESC LIMIT 10;
        """,
    },
    "🌍 Geographic & Advanced Analytics": {
        "Countries with Both Shallow & Deep Earthquakes (Same Month)": """
            SELECT country, year, month
            FROM earthquakes
            GROUP BY country, year, month
            HAVING SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) > 0
               AND SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) > 0
            ORDER BY country, year, month;
        """,
        "Top 3 Most Seismically Active Regions (Frequency x Magnitude)": """
            SELECT country, COUNT(*) AS earthquake_count,
                   ROUND(AVG(mag)::numeric, 2) AS avg_magnitude,
                   ROUND((COUNT(*) * AVG(mag))::numeric, 2) AS activity_score
            FROM earthquakes WHERE country IS NOT NULL
            GROUP BY country ORDER BY activity_score DESC LIMIT 3;
        """,
        "Average Depth Near Equator (±5° latitude) by Country": """
            SELECT country, COUNT(*) AS earthquake_count,
                   ROUND(AVG(depth_km)::numeric, 2) AS avg_depth_km
            FROM earthquakes WHERE latitude BETWEEN -5 AND 5 AND country IS NOT NULL
            GROUP BY country ORDER BY avg_depth_km DESC;
        """,
        "Highest Shallow-to-Deep Earthquake Ratio by Country": """
            SELECT country,
                   SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) AS shallow_count,
                   SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) AS deep_count,
                   ROUND((SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END)::numeric
                       / NULLIF(SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END), 0)), 2) AS shallow_deep_ratio
            FROM earthquakes WHERE country IS NOT NULL
            GROUP BY country
            HAVING SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) > 0
            ORDER BY shallow_deep_ratio DESC LIMIT 10;
        """,
        "Regions with Most Deep-Focus Earthquakes (depth > 300km)": """
            SELECT country, COUNT(*) AS deep_earthquake_count,
                   ROUND(AVG(depth_km)::numeric, 2) AS avg_depth_km
            FROM earthquakes WHERE depth_km > 300 AND country IS NOT NULL
            GROUP BY country ORDER BY deep_earthquake_count DESC LIMIT 10;
        """,
    },
    "🗒️ Not Available in This Dataset": {
        "Most Active Reporting Network by Continent": "SELECT 'Continent column not available in earthquake dataset' AS note;",
        "Total Estimated Economic Loss per Continent": "SELECT 'Continent column not available in earthquake dataset' AS note;",
        "Average RMS and Gap per Continent": "SELECT 'Continent column not available in earthquake dataset' AS note;",
        "Consecutive Earthquakes Within 50km & 1 Hour": "SELECT 'Continent column not available in earthquake dataset' AS note;",
    },
}

TOTAL_QUERIES = sum(len(v) for v in QUERY_GROUPS.values())

# ============================================================================
# HEADER
# ============================================================================
st.markdown(
    f"""
    <div class="dashboard-header">
        <h1>🌋 Earthquake Data Analysis Dashboard</h1>
        <p>{TOTAL_QUERIES} pre-built analyses across rankings, time trends, geography, and data quality</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# OVERVIEW KPI STRIP (live from the database, fails gracefully)
# ============================================================================
stats = get_overview_stats()


def fmt(val, decimals=None):
    if val is None:
        return "—"
    if decimals is not None:
        try:
            return f"{float(val):.{decimals}f}"
        except (TypeError, ValueError):
            return str(val)
    try:
        return f"{int(val):,}"
    except (TypeError, ValueError):
        return str(val)


k1, k2, k3, k4, k5 = st.columns(5)
kpi_data = [
    (k1, "Total Earthquakes", fmt(stats.get("total")), "records in dataset"),
    (k2, "Average Magnitude", fmt(stats.get("avg_mag"), 2), "across all events"),
    (k3, "Strongest Recorded", fmt(stats.get("max_mag"), 1), "peak magnitude"),
    (k4, "Tsunamis Triggered", fmt(stats.get("tsunamis")), "tsunami-flagged events"),
    (k5, "Countries Affected", fmt(stats.get("countries")), f"peak year: {fmt(stats.get('peak_year'))}"),
]
for col, label, value, sub in kpi_data:
    with col:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )

# ============================================================================
# SIDEBAR — SEARCH + CATEGORY + QUERY SELECTION
# ============================================================================
st.sidebar.markdown("## 🔎 Choose an Analysis")

search_term = st.sidebar.text_input("Search all queries", placeholder="e.g. tsunami, depth, alert…")

if search_term:
    matches = {
        group: {name: sql for name, sql in q.items() if search_term.lower() in name.lower()}
        for group, q in QUERY_GROUPS.items()
    }
    matches = {g: q for g, q in matches.items() if q}
    if not matches:
        st.sidebar.warning("No queries match your search.")
        matches = QUERY_GROUPS
else:
    matches = QUERY_GROUPS

selected_group = st.sidebar.radio("Category", list(matches.keys()))
selected_query_name = st.sidebar.selectbox("Query", list(matches[selected_group].keys()))
run = st.sidebar.button("▶️ Run Query", use_container_width=True, type="primary")

st.sidebar.markdown("---")
st.sidebar.caption(f"**{TOTAL_QUERIES}** total analyses across **{len(QUERY_GROUPS)}** categories")
st.sidebar.caption("Data source: local PostgreSQL `earthquakes` table")
st.markdown(
    "<div style='text-align:center; color:gray;'>Created by <b>Pearlraj</b></div>",
    unsafe_allow_html=True
)
# ============================================================================
# MAIN PANEL
# ============================================================================
st.markdown('<div class="section-title">📌 Selected Analysis</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="query-meta"><span class="badge">{selected_group.strip()}</span>'
    f'<b>{selected_query_name}</b></div>',
    unsafe_allow_html=True,
)

with st.expander("View SQL"):
    st.code(matches[selected_group][selected_query_name].strip(), language="sql")

if run:
    with st.spinner("Running query..."):
        try:
            df = run_query(matches[selected_group][selected_query_name])
        except Exception as e:
            st.error(f"Query failed: {e}")
            st.stop()

    st.markdown('<div class="section-title">📄 Results</div>', unsafe_allow_html=True)

    r1, r2 = st.columns(2)
    with r1:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-label">Rows Returned</div>'
            f'<div class="kpi-value">{len(df):,}</div></div>',
            unsafe_allow_html=True,
        )
    with r2:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-label">Columns</div>'
            f'<div class="kpi-value">{len(df.columns)}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.dataframe(df, use_container_width=True)

    # Auto-chart: one categorical + one numeric column → quick bar chart
    numeric_cols = df.select_dtypes("number").columns.tolist()
    non_numeric_cols = [c for c in df.columns if c not in numeric_cols]
    if len(df) > 1 and len(numeric_cols) >= 1 and len(non_numeric_cols) == 1:
        try:
            import plotly.express as px

            fig = px.bar(
                df,
                x=non_numeric_cols[0],
                y=numeric_cols[0],
                title=f"{numeric_cols[0]} by {non_numeric_cols[0]}",
                color=numeric_cols[0],
                color_continuous_scale="OrRd",
            )
            fig.update_layout(coloraxis_showscale=False, height=380)
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.caption("Install `plotly` to see auto-generated charts here.")

    csv = df.to_csv(index=False)
    st.download_button("⬇️ Download CSV", csv, "result.csv", "text/csv")
else:
    st.info("Select a category and query in the sidebar, then click **Run Query**.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown(
    '<div class="app-footer">Earthquake Data Analysis Dashboard · Created by <b>Pearlraj</b></div>',
    unsafe_allow_html=True,
)
