import streamlit as st
from config import APP_TITLE, APP_SUBTITLE, ACADEMIC_BATCH, DB_TYPE, SQLITE_PATH
from database.connection import init_db
from database.models import Medicine
from database.connection import get_db
from data.seed_data import seed_database
from services.alert_service import AlertService
from ui.components import apply_custom_styles
from ui.dashboard_view import render_dashboard_view
from ui.inventory_view import render_inventory_view
from ui.sales_view import render_sales_view
from ui.forecast_view import render_forecast_view
from ui.restock_view import render_restock_view
from ui.alerts_view import render_alerts_view
from ui.procurement_view import render_procurement_view
from ui.agent_activity_view import render_agent_activity_view
from ui.model_eval_view import render_model_eval_view

# Page Configuration
st.set_page_config(
    page_title="Health Supply AI - Medicine Demand & Restocking",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Clean Custom CSS
apply_custom_styles()


def ensure_database_ready():
    """Initializes schema and auto-seeds on initial launch if empty."""
    init_db()
    with get_db() as session:
        count = session.query(Medicine).count()
        if count == 0:
            seed_database(force_reset=False)


# Auto initialize
ensure_database_ready()

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0 16px 0;">
        <h2 style="color: #38bdf8; margin: 0; font-weight: 800; font-size: 1.45rem;">💊 Health Supply AI</h2>
        <p style="color: #94a3b8; font-size: 0.8rem; margin: 4px 0 0 0;">Pharmacy Inventory & Demand Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    nav_selection = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "💊 Inventory",
            "📈 Sales History",
            "🔮 Demand Forecast",
            "📦 Smart Restocking",
            "🚨 Alerts",
            "🤖 Agent Activity",
            "🛡️ Procurement Approvals",
            "🌲 Model Performance"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("<p style='font-size:0.75rem; color:#94a3b8; font-weight:600;'>SYSTEM & DATABASE</p>", unsafe_allow_html=True)
    db_badge = "MySQL Connected" if DB_TYPE == "mysql" else "SQLite (Local Auto-Fallback)"
    st.markdown(f"<span style='font-size:0.8rem; color:#38bdf8;'>● {db_badge}</span>", unsafe_allow_html=True)

    with st.expander("⚙️ System Tools"):
        if st.button("🔄 Rescan All Alerts", use_container_width=True):
            n = AlertService.scan_and_generate_alerts()
            st.success(f"Scanned: {n} new alerts.")
            st.rerun()

        if st.button("🌱 Reset & Re-Seed Demo Data", use_container_width=True):
            with st.spinner("Re-seeding 1-year synthetic data and alerts..."):
                seed_database(force_reset=True)
                st.success("Database re-seeded successfully!")
                st.rerun()

    st.markdown("""
    <div style="font-size: 0.72rem; color: #64748b; margin-top: 25px; line-height: 1.4;">
        <strong>Department of CSE (Data Science)</strong><br>
        Vardhaman College of Engineering<br>
        Batch: <code>24MPCSD-B07</code>
    </div>
    """, unsafe_allow_html=True)


# Route to selected page view
if nav_selection == "📊 Dashboard":
    render_dashboard_view()
elif nav_selection == "💊 Inventory":
    render_inventory_view()
elif nav_selection == "📈 Sales History":
    render_sales_view()
elif nav_selection == "🔮 Demand Forecast":
    render_forecast_view()
elif nav_selection == "📦 Smart Restocking":
    render_restock_view()
elif nav_selection == "🚨 Alerts":
    render_alerts_view()
elif nav_selection == "🤖 Agent Activity":
    render_agent_activity_view()
elif nav_selection == "🛡️ Procurement Approvals":
    render_procurement_view()
elif nav_selection == "🌲 Model Performance":
    render_model_eval_view()
