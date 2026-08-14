import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# ============================================================
# RENDER POSTGRESQL DATABASE CONNECTION
# ============================================================

DATABASE_URL = (
    "postgresql://earthquake_user:"
    "LV3TUg8gpIuzQaMIjkfIqQqJ80PGePMp"
    "@dpg-d9vmeoe417fc73e90tj0-a.oregon-postgres.render.com/"
    "earthquake_db_cdfc"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# ============================================================
# STREAMLIT PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Earthquake Dashboard",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Earthquake Data Analysis Dashboard")
st.markdown(
    "Explore earthquake data stored in PostgreSQL using SQL analysis."
)

# ============================================================
# SQL QUERIES
# ============================================================

queries = {

    "1. Top 10 Strongest Earthquakes":
            """
        SELECT
            id,
            time,
            place,
            country,
            mag,
            depth_km,
            strong_destructive_flag
        FROM earthquakes
        ORDER BY mag DESC
        LIMIT 10;
        """,

    "2. Top 10 Deepest Earthquakes":
            """
        SELECT
            id,
            time,
            place,
            country,
            depth_km,
            mag
        FROM earthquakes
        ORDER BY depth_km DESC
        LIMIT 10;
        """,

    "3. Year with Most Earthquakes":
            """
        SELECT
            id,
            time,
            place,
            country,
            depth_km,
            mag
        FROM earthquakes
        WHERE depth_km < 50
        AND mag > 7.5
        ORDER BY mag DESC;
        """,

    "4. Most Active Reporting Network":
            """
        SELECT 'Continent column not available in earthquake dataset' AS note;
        """,
    "5. Average magnitude per magnitude type (magType)":
            """
        SELECT
            "magType",
            ROUND(AVG(mag)::numeric, 2) AS avg_magnitude,
            COUNT(*) AS earthquake_count
        FROM earthquakes
        GROUP BY "magType"
        ORDER BY avg_magnitude DESC;
        """,
    "6. Year with most earthquakes":
            """
        SELECT
            year,
            COUNT(*) AS total_earthquakes
        FROM earthquakes
        GROUP BY year
        ORDER BY total_earthquakes DESC
        LIMIT 1;
        """,
    "7. Month with highest number of earthquakes":
            """
        SELECT
            month,
            COUNT(*) AS total_earthquakes
        FROM earthquakes
        GROUP BY month
        ORDER BY total_earthquakes DESC
        LIMIT 1;
        """,
    "8. Day of week with most earthquakes":
            """
        SELECT
            day_of_week,
            COUNT(*) AS total_earthquakes
        FROM earthquakes
        GROUP BY day_of_week
        ORDER BY total_earthquakes DESC
        LIMIT 1;
        """,
    "9. Count of earthquakes per hour of day":
            """
        SELECT
            DATE_PART('hour', CAST(time AS TIMESTAMP)) AS hour_of_day,
            COUNT(*) AS total_earthquakes
        FROM earthquakes
        GROUP BY hour_of_day
        ORDER BY hour_of_day;
        """,
    "10.   Most active reporting network (net)":
            """
        SELECT
            net,
            COUNT(*) AS total_earthquakes
        FROM earthquakes
        GROUP BY net
        ORDER BY total_earthquakes DESC
        LIMIT 1;
        """,
    "11.  Top 5 places with highest casualties":
            """
        SELECT
            place,
            COUNT(*) AS earthquake_count
        FROM earthquakes
        GROUP BY place
        ORDER BY earthquake_count DESC
        LIMIT 5;
        """,
    "12.  Total estimated economic loss per continent":
            """
        SELECT 'Continent column not available in earthquake dataset' AS note;
        """,
    "13.  Average economic loss by alert level":
            """
        SELECT
            alert,
            COUNT(*) AS earthquake_count,
            ROUND(AVG(mag)::numeric, 2) AS avg_magnitude
        FROM earthquakes
        GROUP BY alert
        ORDER BY avg_magnitude DESC;
        """,
    "14.  Count of reviewed vs automatic earthquakes (status)":
            """
        SELECT
            status,
            COUNT(*) AS earthquake_count
        FROM earthquakes
        GROUP BY status
        ORDER BY earthquake_count DESC;
        """,
    "15.  Count by earthquake type (type)":
            """
        SELECT
            type,
            COUNT(*) AS earthquake_count
        FROM earthquakes
        GROUP BY type
        ORDER BY earthquake_count DESC;
        """,
    "16.  Number of earthquakes by data type (types)":
            """
        SELECT
            types,
            COUNT(*) AS earthquake_count
        FROM earthquakes
        GROUP BY types
        ORDER BY earthquake_count DESC;
        """,
    "17.  Average RMS and gap per continent":
            """
        SELECT 'Continent column not available in earthquake dataset' AS note;
        """,
    "18.  Events with high station coverage (nst > threshold)":
            """
        SELECT
            id,
            time,
            place,
            mag,
            nst
        FROM earthquakes
        WHERE nst > 100
        ORDER BY nst DESC;
        """,
    "19.  Number of tsunamis triggered per year":
            """
        SELECT
            year,
            COUNT(*) AS tsunami_count
        FROM earthquakes
        WHERE tsunami = 1
        GROUP BY year
        ORDER BY year;
        """,
    "20.  Count earthquakes by alert levels (red, orange, etc.)":
            """
        SELECT
            alert,
            COUNT(*) AS earthquake_count
        FROM earthquakes
        GROUP BY alert
        ORDER BY earthquake_count DESC;
        """,
    "21.Find the top 5 countries with the highest average magnitude of earthquakes in the past 5 years":
            """
        SELECT
            country,
            ROUND(AVG(mag)::numeric, 2) AS avg_magnitude,
            COUNT(*) AS earthquake_count
        FROM earthquakes
        GROUP BY country
        HAVING COUNT(*) > 0
        ORDER BY avg_magnitude DESC
        LIMIT 5;
        """,
    "22.Find countries that have experienced both shallow and deep earthquakes within the same month":
            """
        SELECT
            country,
            year,
            month
        FROM earthquakes
        GROUP BY country, year, month
        HAVING
            SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) > 0
            AND
            SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) > 0
        ORDER BY country, year, month;
        """,
    "23.Compute the year-over-year growth rate in the total number of earthquakes globally":
            """
        WITH yearly_counts AS (
            SELECT
                year,
                COUNT(*) AS total_earthquakes
            FROM earthquakes
            GROUP BY year
        )
        SELECT
            year,
            total_earthquakes,
            LAG(total_earthquakes) OVER (ORDER BY year) AS previous_year_count,
            ROUND(
                (
                    (total_earthquakes - LAG(total_earthquakes) OVER (ORDER BY year))
                    * 100.0
                    / LAG(total_earthquakes) OVER (ORDER BY year)
                )::numeric,
                2
            ) AS yoy_growth_rate
        FROM yearly_counts
        ORDER BY year;
        """,
    "24. List the 3 most seismically active regions by combining both frequency and average magnitude":
            """
        SELECT
            country,
            COUNT(*) AS earthquake_count,
            ROUND(AVG(mag)::numeric, 2) AS avg_magnitude,
            ROUND((COUNT(*) * AVG(mag))::numeric, 2) AS activity_score
        FROM earthquakes
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY activity_score DESC
        LIMIT 3;
        """,
    "25. For each country, calculate the average depth of earthquakes within ±5° latitude range of the equator":
            """
        SELECT
            country,
            COUNT(*) AS earthquake_count,
            ROUND(AVG(depth_km)::numeric, 2) AS avg_depth_km
        FROM earthquakes
        WHERE latitude BETWEEN -5 AND 5
        AND country IS NOT NULL
        GROUP BY country
        ORDER BY avg_depth_km DESC;
        """,
    "26. Identify countries having the highest ratio of shallow to deep earthquakes":
            """
        SELECT
            country,
            SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END) AS shallow_count,
            SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) AS deep_count,
            ROUND(
                (
                    SUM(CASE WHEN depth_km < 70 THEN 1 ELSE 0 END)::numeric
                    / NULLIF(SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END), 0)
                ),
                2
            ) AS shallow_deep_ratio
        FROM earthquakes
        WHERE country IS NOT NULL
        GROUP BY country
        HAVING SUM(CASE WHEN depth_km > 300 THEN 1 ELSE 0 END) > 0
        ORDER BY shallow_deep_ratio DESC
        LIMIT 10;
        """,
    "27. Find the average magnitude difference between earthquakes with tsunami alerts and those without":
            """
        SELECT
            tsunami,
            ROUND(AVG(mag)::numeric, 2) AS avg_magnitude,
            COUNT(*) AS earthquake_count
        FROM earthquakes
        GROUP BY tsunami
        ORDER BY tsunami DESC;
        """,
    "28. Using the gap and rms columns, identify events with the lowest data reliability (highest average error margins)":
            """
        SELECT
            id,
            time,
            place,
            mag,
            gap,
            rms,
            ROUND(((gap + rms) / 2.0)::numeric, 2) AS reliability_error_score
        FROM earthquakes
        WHERE gap IS NOT NULL
        AND rms IS NOT NULL
        ORDER BY reliability_error_score DESC
        LIMIT 10;
        """,
    "29. Find pairs of consecutive earthquakes (by time) that occurred within 50 km of each other and within 1 hour":
            """
        SELECT 'Continent column not available in earthquake dataset' AS note;
        """,
    "30. Determine the regions with the highest frequency of deep-focus earthquakes (depth > 300 km)":
            """ 
        SELECT
            country,
            COUNT(*) AS deep_earthquake_count,
            ROUND(AVG(depth_km)::numeric, 2) AS avg_depth_km
        FROM earthquakes
        WHERE depth_km > 300
        AND country IS NOT NULL
        GROUP BY country
        ORDER BY deep_earthquake_count DESC
        LIMIT 10;
        """
}

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Analysis Options")

selected_query = st.sidebar.selectbox(
    "Choose Analysis",
    list(queries.keys())
)

# ============================================================
# DATABASE CONNECTION TEST
# ============================================================

if st.sidebar.button("Test Database Connection"):

    try:
        with engine.connect() as connection:
            st.sidebar.success("✅ Database connected successfully!")

    except Exception as e:
        st.sidebar.error("❌ Database connection failed")
        st.sidebar.code(str(e))

# ============================================================
# RUN QUERY
# ============================================================

if st.button("▶ Run Query", use_container_width=True):

    try:

        with st.spinner("Running SQL query..."):

            df = pd.read_sql(
                queries[selected_query],
                engine
            )

        st.subheader(selected_query)

        if df.empty:

            st.warning("No records found.")

        else:

            st.success(
                f"Query executed successfully — {len(df):,} rows returned."
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            # ------------------------------------------------
            # DOWNLOAD CSV
            # ------------------------------------------------

            csv = df.to_csv(index=False)

            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name="earthquake_analysis_result.csv",
                mime="text/csv"
            )

    except Exception as e:

        st.error("❌ Error while executing query")

        st.code(
            str(e),
            language="text"
        )

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Earthquake Data Analysis Dashboard | PostgreSQL + Streamlit"
)