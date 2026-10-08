from datetime import date, timedelta
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ui.components import render_header, render_kpi
from services.inventory_service import InventoryService
from services.sales_service import SalesService
from ml.predictor import predictor


def render_forecast_view():
    render_header(
        "Machine Learning Demand Forecasting",
        "Predictive Demand Horizon Using Trained Random Forest Regressor"
    )

    meds = InventoryService.get_all_medicines()
    if not meds:
        st.warning("Please seed the medicine catalog first.")
        return

    med_map = {f"{m['medicine_name']} ({m['category']})": m["medicine_id"] for m in meds}

    # Controls row
    fc1, fc2, fc3 = st.columns([2, 1, 1])
    with fc1:
        sel_label = st.selectbox("Select Target Medicine", list(med_map.keys()))
        target_med_id = med_map[sel_label]
    with fc2:
        forecast_horizon = st.selectbox("Forecast Horizon", [7, 14, 30], index=0, format_func=lambda x: f"{x} Days")
    with fc3:
        st.write("")
        st.write("")
        run_forecast_btn = st.button("🔮 Generate Prediction", use_container_width=True, type="primary")

    # Generate Forecast
    with st.spinner("Generating time-series forecast using Random Forest..."):
        try:
            pred_data = predictor.predict_demand(medicine_id=target_med_id, forecast_days=forecast_horizon)
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            return

    # Metrics Row
    tot_pred = pred_data["total_predicted_demand"]
    cur_stock = pred_data["current_stock"]
    lead_t = pred_data["lead_time"]
    avg_d = pred_data["average_daily_demand"]
    net_diff = cur_stock - tot_pred

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi(f"{forecast_horizon}-Day Predicted Demand", f"{tot_pred} units", f"Avg {avg_d}/day", "#3b82f6")
    with c2:
        render_kpi("Current Stock", f"{cur_stock} units", f"Reorder point: {pred_data['reorder_level']}", "#10b981" if cur_stock > pred_data["reorder_level"] else "#ef4444")
    with c3:
        status_color = "#10b981" if net_diff >= 0 else "#ef4444"
        render_kpi("Net Horizon Balance", f"{net_diff:+d} units", "Surplus" if net_diff >= 0 else "DEFICIT / SHORTAGE", status_color)
    with c4:
        render_kpi("Supplier Lead Time", f"{lead_t} days", f"Model: {pred_data['model_used'][:13]}...", "#6366f1")

    st.markdown("<br>", unsafe_allow_html=True)

    # Historical Sales vs Predicted Demand Chart
    st.subheader(f"📈 30-Day Historical Sales + {forecast_horizon}-Day ML Forecast")

    # Fetch last 30 days of actual sales
    history_records = SalesService.get_sales_history(medicine_id=target_med_id, limit=30)
    hist_df = pd.DataFrame(history_records).sort_values("sale_date") if history_records else pd.DataFrame()

    fig = go.Figure()

    if not hist_df.empty:
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(hist_df["sale_date"]),
            y=hist_df["quantity_sold"],
            mode="lines+markers",
            name="Actual Historical Sales",
            line=dict(color="#0284c7", width=2.5),
            marker=dict(size=5)
        ))

    # Add predicted trace
    pred_df = pd.DataFrame(pred_data["daily_forecasts"])
    pred_df["date"] = pd.to_datetime(pred_df["date"])

    fig.add_trace(go.Scatter(
        x=pred_df["date"],
        y=pred_df["predicted_demand"],
        mode="lines+markers",
        name=f"Predicted Demand ({pred_data['model_used']})",
        line=dict(color="#f59e0b", width=3, dash="dash"),
        marker=dict(size=6, symbol="star")
    ))

    # Reference line for current stock
    fig.add_hline(
        y=cur_stock,
        line_dash="dot",
        line_color="#ef4444" if cur_stock <= pred_data["reorder_level"] else "#10b981",
        annotation_text=f"Current Stock ({cur_stock} units)",
        annotation_position="bottom right"
    )

    fig.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Date",
        yaxis_title="Daily Units",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Detailed Daily Breakdown Table
    with st.expander("📅 View Detailed Daily Forecast Schedule"):
        df_daily = pd.DataFrame(pred_data["daily_forecasts"])
        df_daily.columns = ["Date", "Predicted Units"]
        st.dataframe(df_daily, use_container_width=True, hide_index=True)
