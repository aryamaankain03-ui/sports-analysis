import os
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Tennis Intelligence Studio",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "tennis_db")

# NAVIGATION CONSTANTS (Ensures exact string matching across radio & logic)
NAV_OVERVIEW = "🏠 Executive Overview"
NAV_COMPETITIONS = "🏆 Competition Analytics"
NAV_VENUES = "🏟️ Venues & Logistics"
NAV_RANKINGS = "🎾 Player Rankings"

# Color Palette Definitions (Professional Theme)
PRIMARY_COLOR = "#0F172A"
ACCENT_COLOR = "#2563EB"
BG_COLOR = "#F8FAFC"
CARD_BG = "#FFFFFF"
TEXT_COLOR = "#1E293B"
MUTED_TEXT = "#64748B"
BORDER_COLOR = "#E2E8F0"

# ============================================================
# ADVANCED CUSTOM CSS
# ============================================================
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* Global Background */
    .stApp {{
        background-color: {BG_COLOR};
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {PRIMARY_COLOR};
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}

    section[data-testid="stSidebar"] * {{
        color: #F1F5F9 !important;
    }}

    /* Title Styling */
    .main-header {{
        padding: 10px 0px 25px 0px;
    }}
    .main-title {{
        font-size: 32px;
        font-weight: 800;
        color: {TEXT_COLOR};
        letter-spacing: -0.5px;
    }}
    .main-subtitle {{
        font-size: 15px;
        color: {MUTED_TEXT};
        margin-top: 4px;
    }}

    /* Custom Metric / KPI Cards */
    .kpi-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER_COLOR};
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.08);
    }}
    .kpi-title {{
        font-size: 13px;
        font-weight: 600;
        color: {MUTED_TEXT};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 28px;
        font-weight: 700;
        color: {TEXT_COLOR};
    }}

    /* Tab Customization */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 1px solid {BORDER_COLOR};
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 45px;
        white-space: pre-wrap;
        border-radius: 8px 8px 0px 0px;
        font-weight: 600;
        font-size: 14px;
        color: {MUTED_TEXT};
    }}
    .stTabs [aria-selected="true"] {{
        color: {ACCENT_COLOR} !important;
        border-bottom: 2px solid {ACCENT_COLOR} !important;
    }}

    /* Section Headers */
    .section-header {{
        font-size: 18px;
        font-weight: 700;
        color: {TEXT_COLOR};
        margin: 20px 0 12px 0;
    }}

    /* Status Pill */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 600;
    }}
    .status-success {{
        background-color: #DCFCE7;
        color: #166534;
    }}
    .status-error {{
        background-color: #FEE2E2;
        color: #991B1B;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# DATABASE CONNECTION & CACHING
# ============================================================
@st.cache_resource
def get_db_connection():
    """Create persistent MySQL database connection pool."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except mysql.connector.Error:
        return None

@st.cache_data(ttl=300)
def run_query(query: str) -> pd.DataFrame:
    """Execute SQL query with automatic 5-minute caching for performance optimization."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = connection.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        df = pd.DataFrame(data, columns=columns)
        cursor.close()
        connection.close()
        return df
    except mysql.connector.Error:
        return pd.DataFrame()

# Helper for standard Plotly charts layout styling
def apply_chart_theme(fig, height=400):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="Inter, sans-serif", color="#334155", size=12),
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title_font=dict(size=12, color="#64748B")),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title_font=dict(size=12, color="#64748B")),
        hoverlabel=dict(bgcolor="#0F172A", font_size=13, font_family="Inter, sans-serif")
    )
    return fig

# Custom Metric Component Helper
def display_kpi(label: str, value: str):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 10px 0;">
            <div style="font-size: 22px; font-weight: 800; letter-spacing: -0.5px;">🎾 Tennis Studio</div>
            <div style="font-size: 12px; opacity: 0.7; margin-top: 2px;">Sportradar Data Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")

    page = st.radio(
        "NAVIGATION",
        [
            NAV_OVERVIEW,
            NAV_COMPETITIONS,
            NAV_VENUES,
            NAV_RANKINGS
        ],
        index=0
    )

    st.markdown("---")
    
    # Connection Check Badge
    conn_check = get_db_connection()
    if conn_check and conn_check.is_connected():
        st.markdown('<span class="status-badge status-success">● DB Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-error">● DB Disconnected</span>', unsafe_allow_html=True)

    st.markdown(
        """
        <div style="font-size:12px; color:#94A3B8; margin-top: 30px;">
        <b>Engine:</b> MySQL + Streamlit<br>
        <b>Provider:</b> Sportradar Tennis API
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# PAGE 1: EXECUTIVE OVERVIEW
# ============================================================
if page == NAV_OVERVIEW:
    st.markdown(
        """
        <div class="main-header">
            <div class="main-title">Executive Game Analytics Overview</div>
            <div class="main-subtitle">Comprehensive data overview across global tennis competitions, venues, and players.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch Top Metrics
    category_df = run_query("SELECT COUNT(*) AS total_categories FROM categories")
    competition_df = run_query("SELECT COUNT(*) AS total_competitions FROM competitions")
    venue_df = run_query("SELECT COUNT(*) AS total_venues FROM venues")
    competitor_df = run_query("SELECT COUNT(*) AS total_competitors FROM competitors")
    country_df = run_query("SELECT COUNT(DISTINCT country) AS total_countries FROM competitors")
    points_df = run_query("SELECT MAX(points) AS highest_points FROM competitor_rankings")

    total_categories = int(category_df.iloc[0]["total_categories"]) if not category_df.empty else 0
    total_competitions = int(competition_df.iloc[0]["total_competitions"]) if not competition_df.empty else 0
    total_venues = int(venue_df.iloc[0]["total_venues"]) if not venue_df.empty else 0
    total_competitors = int(competitor_df.iloc[0]["total_competitors"]) if not competitor_df.empty else 0
    total_countries = int(country_df.iloc[0]["total_countries"]) if not country_df.empty else 0
    highest_points = int(points_df.iloc[0]["highest_points"]) if not points_df.empty else 0

    st.markdown('<div class="section-header">📊 Executive Overview Metrics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1: display_kpi("Competitions", f"{total_competitions:,}")
    with col2: display_kpi("Categories", f"{total_categories:,}")
    with col3: display_kpi("Competitors", f"{total_competitors:,}")
    with col4: display_kpi("Venues", f"{total_venues:,}")
    with col5: display_kpi("Countries", f"{total_countries:,}")
    with col6: display_kpi("Top Score", f"{highest_points:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 1. Competitions by Category Chart
    st.markdown('<div class="section-header">🏆 Top Categories by Number of Competitions</div>', unsafe_allow_html=True)
    competition_category_df = run_query(
        """
        SELECT c.category_name, COUNT(co.competition_id) AS total_competitions
        FROM categories c
        LEFT JOIN competitions co ON c.category_id = co.category_id
        GROUP BY c.category_id, c.category_name
        ORDER BY total_competitions DESC LIMIT 10
        """
    )
    if not competition_category_df.empty:
        fig_category = px.bar(
            competition_category_df,
            x="category_name",
            y="total_competitions",
            text_auto=True,
            color="total_competitions",
            color_continuous_scale="Blues",
            labels={"category_name": "Category", "total_competitions": "Competitions"}
        )
        fig_category.update_coloraxes(showscale=False)
        apply_chart_theme(fig_category, height=380)
        st.plotly_chart(fig_category, use_container_width=True)

    # 2. Two Column Geographical Layout
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown('<div class="section-header">🌍 Top 10 Countries by Venue Count</div>', unsafe_allow_html=True)
        venue_country_df = run_query(
            """
            SELECT country_name, COUNT(*) AS total_venues
            FROM venues
            GROUP BY country_name
            ORDER BY total_venues DESC LIMIT 10
            """
        )
        if not venue_country_df.empty:
            fig_venues = px.bar(
                venue_country_df,
                x="total_venues",
                y="country_name",
                orientation="h",
                text_auto=True,
                color="total_venues",
                color_continuous_scale="Teal",
                labels={"country_name": "Country", "total_venues": "Venues"}
            )
            fig_venues.update_coloraxes(showscale=False)
            fig_venues.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig_venues, height=380)
            st.plotly_chart(fig_venues, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-header">🎾 Top 10 Countries by Competitor Count</div>', unsafe_allow_html=True)
        competitor_country_df = run_query(
            """
            SELECT country, COUNT(*) AS total_competitors
            FROM competitors
            GROUP BY country
            ORDER BY total_competitors DESC LIMIT 10
            """
        )
        if not competitor_country_df.empty:
            fig_competitors = px.bar(
                competitor_country_df,
                x="total_competitors",
                y="country",
                orientation="h",
                text_auto=True,
                color="total_competitors",
                color_continuous_scale="Viridis",
                labels={"country": "Country", "total_competitors": "Competitors"}
            )
            fig_competitors.update_coloraxes(showscale=False)
            fig_competitors.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig_competitors, height=380)
            st.plotly_chart(fig_competitors, use_container_width=True)

    # 3. Top Ranked Competitors
    st.markdown('<div class="section-header">⭐ Top 10 Competitors by Ranking Points</div>', unsafe_allow_html=True)
    top_competitors_df = run_query(
        """
        SELECT c.name, c.country, cr.`rank`, cr.points
        FROM competitors c
        JOIN competitor_rankings cr ON c.competitor_id = cr.competitor_id
        ORDER BY cr.points DESC LIMIT 10
        """
    )
    if not top_competitors_df.empty:
        st.dataframe(
            top_competitors_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "points": st.column_config.ProgressColumn(
                    "Points",
                    format="%d",
                    min_value=0,
                    max_value=int(top_competitors_df["points"].max())
                )
            }
        )

# ============================================================
# PAGE 2: COMPETITIONS
# ============================================================
elif page == NAV_COMPETITIONS:
    st.markdown(
        """
        <div class="main-header">
            <div class="main-title">Competition Analytics</div>
            <div class="main-subtitle">Explore tennis competitions, categories, formats, and hierarchy.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    comp_tot = run_query("SELECT COUNT(*) AS total FROM competitions")
    cat_tot = run_query("SELECT COUNT(*) AS total FROM categories")
    dbl_tot = run_query("SELECT COUNT(*) AS total FROM competitions WHERE LOWER(competition_name) LIKE '%doubles%'")
    par_tot = run_query("SELECT COUNT(*) AS total FROM competitions WHERE parent_id IS NULL")

    t_comp = int(comp_tot.iloc[0]["total"]) if not comp_tot.empty else 0
    t_cat = int(cat_tot.iloc[0]["total"]) if not cat_tot.empty else 0
    t_dbl = int(dbl_tot.iloc[0]["total"]) if not dbl_tot.empty else 0
    t_par = int(par_tot.iloc[0]["total"]) if not par_tot.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1: display_kpi("Total Competitions", f"{t_comp:,}")
    with col2: display_kpi("Categories", f"{t_cat:,}")
    with col3: display_kpi("Doubles Events", f"{t_dbl:,}")
    with col4: display_kpi("Top-Level Events", f"{t_par:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "📋 All Competitions",
            "📊 By Category",
            "🎾 Doubles",
            "🔎 Category Search",
            "🔗 Parent / Sub",
            "📈 Type Distribution",
            "🏆 Top-Level"
        ]
    )

    with tab1:
        st.markdown('<div class="section-header">📋 All Competitions with Category</div>', unsafe_allow_html=True)
        all_comp_df = run_query(
            """
            SELECT co.competition_id, co.competition_name, co.type, co.gender, c.category_name
            FROM competitions co
            LEFT JOIN categories c ON co.category_id = c.category_id
            ORDER BY co.competition_name
            """
        )
        if not all_comp_df.empty:
            search = st.text_input("🔍 Search competition", placeholder="Enter competition name...", key="tab1_search")
            filtered_df = all_comp_df[all_comp_df["competition_name"].str.contains(search, case=False, na=False)] if search else all_comp_df
            st.caption(f"Showing {len(filtered_df):,} of {len(all_comp_df):,} competitions")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown('<div class="section-header">📊 Competitions per Category</div>', unsafe_allow_html=True)
        cat_comp_df = run_query(
            """
            SELECT c.category_name, COUNT(co.competition_id) AS total_competitions
            FROM categories c
            LEFT JOIN competitions co ON c.category_id = co.category_id
            GROUP BY c.category_id, c.category_name
            ORDER BY total_competitions DESC
            """
        )
        if not cat_comp_df.empty:
            fig = px.bar(
                cat_comp_df.head(15),
                x="total_competitions",
                y="category_name",
                orientation="h",
                text_auto=True,
                color="total_competitions",
                color_continuous_scale="Blues",
                labels={"total_competitions": "Competitions", "category_name": "Category"}
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=500)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header">🎾 Doubles Competitions</div>', unsafe_allow_html=True)
        doubles_df = run_query(
            """
            SELECT co.competition_id, co.competition_name, co.type, co.gender, c.category_name
            FROM competitions co
            LEFT JOIN categories c ON co.category_id = c.category_id
            WHERE LOWER(co.competition_name) LIKE '%doubles%'
            ORDER BY co.competition_name
            """
        )
        if not doubles_df.empty:
            st.metric("Doubles Competitions Found", f"{len(doubles_df):,}")
            st.dataframe(doubles_df, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown('<div class="section-header">🔎 Competitions by Selected Category</div>', unsafe_allow_html=True)
        cats_df = run_query("SELECT category_id, category_name FROM categories ORDER BY category_name")
        if not cats_df.empty:
            category_names = cats_df["category_name"].dropna().tolist()
            default_idx = category_names.index("ITF Men") if "ITF Men" in category_names else 0
            selected_category = st.selectbox("Select a category", category_names, index=default_idx)
            
            safe_cat = selected_category.replace("'", "''")
            sel_cat_df = run_query(
                f"""
                SELECT co.competition_id, co.competition_name, co.type, co.gender, c.category_name
                FROM competitions co
                JOIN categories c ON co.category_id = c.category_id
                WHERE c.category_name = '{safe_cat}'
                ORDER BY co.competition_name
                """
            )
            st.dataframe(sel_cat_df, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown('<div class="section-header">🔗 Parent and Sub-Competitions</div>', unsafe_allow_html=True)
        hierarchy_df = run_query(
            """
            SELECT child.competition_id, child.competition_name AS sub_competition,
                   parent.competition_name AS parent_competition, child.type, child.gender
            FROM competitions child
            LEFT JOIN competitions parent ON child.parent_id = parent.competition_id
            WHERE child.parent_id IS NOT NULL
            ORDER BY parent.competition_name, child.competition_name
            """
        )
        if not hierarchy_df.empty:
            st.dataframe(hierarchy_df, use_container_width=True, hide_index=True)

    with tab6:
        st.markdown('<div class="section-header">📈 Competition Type Distribution by Category</div>', unsafe_allow_html=True)
        type_dist_df = run_query(
            """
            SELECT c.category_name, co.type, COUNT(*) AS total_competitions
            FROM competitions co
            JOIN categories c ON co.category_id = c.category_id
            GROUP BY c.category_id, c.category_name, co.type
            ORDER BY c.category_name, total_competitions DESC
            """
        )
        if not type_dist_df.empty:
            category_filter = st.multiselect("Filter categories", sorted(type_dist_df["category_name"].dropna().unique()), default=[])
            if category_filter:
                chart_df = type_dist_df[type_dist_df["category_name"].isin(category_filter)]
            else:
                top_cats = type_dist_df.groupby("category_name")["total_competitions"].sum().nlargest(10).index
                chart_df = type_dist_df[type_dist_df["category_name"].isin(top_cats)]

            fig = px.bar(
                chart_df,
                x="category_name",
                y="total_competitions",
                color="type",
                barmode="stack",
                labels={"category_name": "Category", "total_competitions": "Competitions", "type": "Type"}
            )
            apply_chart_theme(fig, height=480)
            st.plotly_chart(fig, use_container_width=True)

    with tab7:
        st.markdown('<div class="section-header">🏆 Top-Level Competitions</div>', unsafe_allow_html=True)
        top_level_df = run_query(
            """
            SELECT co.competition_id, co.competition_name, co.type, co.gender, c.category_name
            FROM competitions co
            LEFT JOIN categories c ON co.category_id = c.category_id
            WHERE co.parent_id IS NULL
            ORDER BY co.competition_name
            """
        )
        if not top_level_df.empty:
            st.dataframe(top_level_df, use_container_width=True, hide_index=True)

# ============================================================
# PAGE 3: VENUES & LOGISTICS (FIXED NAV MATCH)
# ============================================================
elif page == NAV_VENUES:
    st.markdown(
        """
        <div class="main-header">
            <div class="main-title">Venues & Geographical Logistics</div>
            <div class="main-subtitle">Explore tennis venues, sports complexes, geographical distribution and timezones.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    c_tot = run_query("SELECT COUNT(*) AS total FROM complexes")
    v_tot = run_query("SELECT COUNT(*) AS total FROM venues")
    cntry_tot = run_query("SELECT COUNT(DISTINCT country_name) AS total FROM venues")
    tz_tot = run_query("SELECT COUNT(DISTINCT timezone) AS total FROM venues")

    t_c = int(c_tot.iloc[0]["total"]) if not c_tot.empty else 0
    t_v = int(v_tot.iloc[0]["total"]) if not v_tot.empty else 0
    t_cntry = int(cntry_tot.iloc[0]["total"]) if not cntry_tot.empty else 0
    t_tz = int(tz_tot.iloc[0]["total"]) if not tz_tot.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1: display_kpi("Complexes", f"{t_c:,}")
    with col2: display_kpi("Venues", f"{t_v:,}")
    with col3: display_kpi("Countries", f"{t_cntry:,}")
    with col4: display_kpi("Timezones", f"{t_tz:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "📋 All Venues",
            "📊 Venues per Complex",
            "🌎 Country Search",
            "🕐 Timezones",
            "🏟️ Multi-Venue Complexes",
            "🌍 By Country",
            "🔎 Complex Search"
        ]
    )

    with tab1:
        st.markdown('<div class="section-header">📋 All Venues with Associated Complex</div>', unsafe_allow_html=True)
        venues_df = run_query(
            """
            SELECT v.venue_id, v.venue_name, v.city_name, v.country_name, v.country_code, v.timezone, c.complex_name
            FROM venues v
            LEFT JOIN complexes c ON v.complex_id = c.complex_id
            ORDER BY v.venue_name
            """
        )
        if not venues_df.empty:
            search_v = st.text_input("🔍 Search venue", placeholder="Enter venue name...", key="v_search")
            filtered_v = venues_df[venues_df["venue_name"].str.contains(search_v, case=False, na=False)] if search_v else venues_df
            st.dataframe(filtered_v, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown('<div class="section-header">📊 Number of Venues in Each Complex</div>', unsafe_allow_html=True)
        v_per_c_df = run_query(
            """
            SELECT c.complex_name, COUNT(v.venue_id) AS total_venues
            FROM complexes c
            LEFT JOIN venues v ON c.complex_id = v.complex_id
            GROUP BY c.complex_id, c.complex_name
            ORDER BY total_venues DESC
            """
        )
        if not v_per_c_df.empty:
            fig = px.bar(
                v_per_c_df.head(15),
                x="total_venues",
                y="complex_name",
                orientation="h",
                text_auto=True,
                color="total_venues",
                color_continuous_scale="Tealgrn"
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=480)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header">🌎 Venues in a Specific Country</div>', unsafe_allow_html=True)
        countries_df = run_query("SELECT DISTINCT country_name FROM venues WHERE country_name IS NOT NULL ORDER BY country_name")
        if not countries_df.empty:
            countries = countries_df["country_name"].dropna().tolist()
            default_c = countries.index("Chile") if "Chile" in countries else 0
            selected_country = st.selectbox("Select country", countries, index=default_c)
            safe_c = selected_country.replace("'", "''")
            c_venues_df = run_query(
                f"""
                SELECT v.venue_id, v.venue_name, v.city_name, v.country_name, v.country_code, v.timezone, c.complex_name
                FROM venues v
                LEFT JOIN complexes c ON v.complex_id = c.complex_id
                WHERE v.country_name = '{safe_c}'
                ORDER BY v.venue_name
                """
            )
            st.dataframe(c_venues_df, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown('<div class="section-header">🕐 Venues and Their Timezones</div>', unsafe_allow_html=True)
        timezone_df = run_query("SELECT venue_name, city_name, country_name, timezone FROM venues ORDER BY timezone, venue_name")
        if not timezone_df.empty:
            tz_filter = st.multiselect("Filter by timezone", sorted(timezone_df["timezone"].dropna().unique()))
            filtered_tz = timezone_df[timezone_df["timezone"].isin(tz_filter)] if tz_filter else timezone_df
            st.dataframe(filtered_tz, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown('<div class="section-header">🏟️ Complexes with More Than One Venue</div>', unsafe_allow_html=True)
        multi_venue_df = run_query(
            """
            SELECT c.complex_id, c.complex_name, COUNT(v.venue_id) AS total_venues
            FROM complexes c
            JOIN venues v ON c.complex_id = v.complex_id
            GROUP BY c.complex_id, c.complex_name
            HAVING COUNT(v.venue_id) > 1
            ORDER BY total_venues DESC
            """
        )
        if not multi_venue_df.empty:
            fig = px.bar(
                multi_venue_df.head(15),
                x="total_venues",
                y="complex_name",
                orientation="h",
                text_auto=True,
                color="total_venues",
                color_continuous_scale="Blues"
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=450)
            st.plotly_chart(fig, use_container_width=True)

    with tab6:
        st.markdown('<div class="section-header">🌍 Venues Grouped by Country</div>', unsafe_allow_html=True)
        c_group_df = run_query(
            """
            SELECT country_name, country_code, COUNT(*) AS total_venues
            FROM venues
            GROUP BY country_name, country_code
            ORDER BY total_venues DESC
            """
        )
        if not c_group_df.empty:
            fig = px.bar(
                c_group_df.head(20),
                x="total_venues",
                y="country_name",
                orientation="h",
                text_auto=True,
                color="total_venues",
                color_continuous_scale="Viridis"
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=500)
            st.plotly_chart(fig, use_container_width=True)

    with tab7:
        st.markdown('<div class="section-header">🔎 Venues for a Specific Complex</div>', unsafe_allow_html=True)
        complexes_df = run_query("SELECT complex_id, complex_name FROM complexes ORDER BY complex_name")
        if not complexes_df.empty:
            complex_names = complexes_df["complex_name"].dropna().tolist()
            default_cmplx = complex_names.index("Nacional") if "Nacional" in complex_names else 0
            selected_complex = st.selectbox("Select complex", complex_names, index=default_cmplx)
            safe_cmplx = selected_complex.replace("'", "''")
            sel_cmplx_df = run_query(
                f"""
                SELECT v.venue_id, v.venue_name, v.city_name, v.country_name, v.country_code, v.timezone, c.complex_name
                FROM venues v
                JOIN complexes c ON v.complex_id = c.complex_id
                WHERE c.complex_name = '{safe_cmplx}'
                ORDER BY v.venue_name
                """
            )
            st.dataframe(sel_cmplx_df, use_container_width=True, hide_index=True)

# ============================================================
# PAGE 4: COMPETITOR RANKINGS
# ============================================================
elif page == NAV_RANKINGS:
    st.markdown(
        """
        <div class="main-header">
            <div class="main-title">Player Rankings & Performance</div>
            <div class="main-subtitle">Explore doubles rankings, competitor performance, point distribution, and country insights.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    comp_tot = run_query("SELECT COUNT(*) AS total FROM competitors")
    cntry_tot = run_query("SELECT COUNT(DISTINCT country) AS total FROM competitors")
    pts_tot = run_query("SELECT MAX(points) AS highest_points FROM competitor_rankings")
    stbl_tot = run_query("SELECT COUNT(*) AS total FROM competitor_rankings WHERE movement = 0")
    top5_tot = run_query("SELECT COUNT(*) AS total FROM competitor_rankings WHERE `rank` <= 5")

    t_comp = int(comp_tot.iloc[0]["total"]) if not comp_tot.empty else 0
    t_cntry = int(cntry_tot.iloc[0]["total"]) if not cntry_tot.empty else 0
    t_pts = int(pts_tot.iloc[0]["highest_points"]) if not pts_tot.empty else 0
    t_stbl = int(stbl_tot.iloc[0]["total"]) if not stbl_tot.empty else 0
    t_top5 = int(top5_tot.iloc[0]["total"]) if not top5_tot.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: display_kpi("Competitors", f"{t_comp:,}")
    with col2: display_kpi("Countries", f"{t_cntry:,}")
    with col3: display_kpi("Highest Points", f"{t_pts:,}")
    with col4: display_kpi("Stable Ranks", f"{t_stbl:,}")
    with col5: display_kpi("Top 5 Players", f"{t_top5:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📋 All Rankings",
            "🏆 Top 5",
            "↔️ Stable Rank",
            "🌍 Country Analysis",
            "📊 Competitors by Country",
            "⭐ Highest Points"
        ]
    )

    with tab1:
        st.markdown('<div class="section-header">📋 Competitor Rankings Explorer</div>', unsafe_allow_html=True)
        rankings_df = run_query(
            """
            SELECT c.competitor_id, c.name, c.country, c.country_code, cr.`rank`, cr.movement, cr.points, cr.competitions_played
            FROM competitors c
            JOIN competitor_rankings cr ON c.competitor_id = cr.competitor_id
            ORDER BY cr.`rank`
            """
        )
        if not rankings_df.empty:
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1: search_name = st.text_input("🔍 Search competitor", placeholder="Enter competitor name...", key="rank_s")
            with c_f2:
                countries = sorted(rankings_df["country"].dropna().unique().tolist())
                selected_countries = st.multiselect("🌍 Filter by country", countries)
            with c_f3:
                max_rank = int(rankings_df["rank"].max())
                rank_range = st.slider("🏆 Rank range", min_value=1, max_value=max_rank, value=(1, min(50, max_rank)))

            min_points = st.number_input("⭐ Minimum ranking points", min_value=0, max_value=int(rankings_df["points"].max()), value=0, step=100)

            filtered_df = rankings_df.copy()
            if search_name: filtered_df = filtered_df[filtered_df["name"].str.contains(search_name, case=False, na=False)]
            if selected_countries: filtered_df = filtered_df[filtered_df["country"].isin(selected_countries)]
            filtered_df = filtered_df[(filtered_df["rank"] >= rank_range[0]) & (filtered_df["rank"] <= rank_range[1]) & (filtered_df["points"] >= min_points)]

            st.caption(f"Showing {len(filtered_df):,} of {len(rankings_df):,} competitors")
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "points": st.column_config.ProgressColumn("points", format="%d", min_value=0, max_value=int(rankings_df["points"].max())),
                    "movement": st.column_config.NumberColumn("movement", format="%+d")
                }
            )

    with tab2:
        st.markdown('<div class="section-header">🏆 Top 5 Competitors</div>', unsafe_allow_html=True)
        top_five_df = run_query(
            """
            SELECT c.competitor_id, c.name, c.country, cr.`rank`, cr.movement, cr.points, cr.competitions_played
            FROM competitors c
            JOIN competitor_rankings cr ON c.competitor_id = cr.competitor_id
            WHERE cr.`rank` <= 5
            ORDER BY cr.`rank`
            """
        )
        if not top_five_df.empty:
            st.dataframe(top_five_df, use_container_width=True, hide_index=True)
            fig = px.bar(
                top_five_df,
                x="name",
                y="points",
                text_auto=True,
                color="points",
                color_continuous_scale="Blues",
                labels={"name": "Competitor", "points": "Ranking Points"},
                hover_data=["country", "rank", "movement"]
            )
            fig.update_coloraxes(showscale=False)
            apply_chart_theme(fig, height=400)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header">↔️ Competitors with No Rank Movement</div>', unsafe_allow_html=True)
        stable_df = run_query(
            """
            SELECT c.competitor_id, c.name, c.country, cr.`rank`, cr.movement, cr.points, cr.competitions_played
            FROM competitors c
            JOIN competitor_rankings cr ON c.competitor_id = cr.competitor_id
            WHERE cr.movement = 0
            ORDER BY cr.`rank`
            """
        )
        if not stable_df.empty:
            search_stable = st.text_input("🔍 Search stable competitor", placeholder="Enter competitor name...", key="stable_search")
            display_stable_df = stable_df[stable_df["name"].str.contains(search_stable, case=False, na=False)] if search_stable else stable_df
            st.dataframe(display_stable_df, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown('<div class="section-header">🌍 Country-Wise Ranking Points</div>', unsafe_allow_html=True)
        country_df = run_query("SELECT DISTINCT country FROM competitors WHERE country IS NOT NULL ORDER BY country")
        if not country_df.empty:
            countries = country_df["country"].dropna().tolist()
            default_cntry = countries.index("Croatia") if "Croatia" in countries else 0
            selected_country = st.selectbox("Select country", countries, index=default_cntry, key="c_pts_select")
            safe_country = selected_country.replace("'", "''")
            
            country_pts_df = run_query(
                f"""
                SELECT c.country, COUNT(*) AS total_competitors, SUM(cr.points) AS total_points, AVG(cr.points) AS average_points
                FROM competitors c
                JOIN competitor_rankings cr ON c.competitor_id = cr.competitor_id
                WHERE c.country = '{safe_country}'
                GROUP BY c.country
                """
            )
            if not country_pts_df.empty:
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1: display_kpi("Competitors", f"{int(country_pts_df.iloc[0]['total_competitors']):,}")
                with col_c2: display_kpi("Total Points", f"{int(country_pts_df.iloc[0]['total_points']):,}")
                with col_c3: display_kpi("Average Points", f"{country_pts_df.iloc[0]['average_points']:,.0f}")
                st.markdown("<br>", unsafe_allow_html=True)
                country_competitors_df = run_query(
                    f"""
                    SELECT c.name, c.country, cr.`rank`, cr.movement, cr.points, cr.competitions_played
                    FROM competitors c
                    JOIN competitor_rankings cr ON c.competitor_id = cr.competitor_id
                    WHERE c.country = '{safe_country}'
                    ORDER BY cr.`rank`
                    """
                )
                st.dataframe(country_competitors_df, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown('<div class="section-header">📊 Competitors by Country</div>', unsafe_allow_html=True)
        competitors_country_df = run_query(
            """
            SELECT country, COUNT(*) AS total_competitors
            FROM competitors
            GROUP BY country
            ORDER BY total_competitors DESC
            """
        )
        if not competitors_country_df.empty:
            fig = px.bar(
                competitors_country_df.head(20),
                x="total_competitors",
                y="country",
                orientation="h",
                text_auto=True,
                color="total_competitors",
                color_continuous_scale="Viridis"
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=500)
            st.plotly_chart(fig, use_container_width=True)

    with tab6:
        st.markdown('<div class="section-header">⭐ Highest Ranking Points</div>', unsafe_allow_html=True)
        highest_pts_v_df = run_query("SELECT MAX(points) AS max_points FROM competitor_rankings")
        if not highest_pts_v_df.empty:
            max_points = int(highest_pts_v_df.iloc[0]["max_points"])
            highest_competitors_df = run_query(
                f"""
                SELECT c.competitor_id, c.name, c.country, cr.`rank`, cr.movement, cr.points, cr.competitions_played
                FROM competitors c
                JOIN competitor_rankings cr ON c.competitor_id = cr.competitor_id
                WHERE cr.points = {max_points}
                ORDER BY cr.`rank`
                """
            )
            st.metric("Highest Ranking Points Standard", f"{max_points:,}")
            st.dataframe(highest_competitors_df, use_container_width=True, hide_index=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #94A3B8; font-size: 13px; padding-bottom: 20px;">
        Tennis Game Analytics Studio • Powered by Streamlit & Plotly
    </div>
    """,
    unsafe_allow_html=True
)