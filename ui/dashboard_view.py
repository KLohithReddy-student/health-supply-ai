import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ui.components import render_header, render_kpi, get_priority_badge
from services.inventory_service import InventoryService
from services.sales_service import SalesService
from services.alert_service import AlertService
from services.restock_service import RestockService


def render_dashboard_view():
    render_header(
        "Health Supply AI: Decision Support Dashboard",
        "Predictive Pharmacy Inventory Management & Multi-Agent Restocking Intelligence"
    )

    # 1. Fetch KPI metrics
    kpis = InventoryService.get_inventory_kpis()
    alerts = AlertService.get_all_alerts(status_filter="Active")
    recommendations = RestockService.get_all_recommendations(status_filter="Pending")

    # 2. Render KPI Cards Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        render_kpi("Total SKUs", str(kpis["total_skus"]), "Registered medicines", "#3b82f6")
    with c2:
        render_kpi("Total Stock", f"{kpis['total_units']:,}", "Units on hand", "#10b981")
    with c3:
        render_kpi("Inventory Value", f"INR {kpis['total_valuation']:,.0f}", "At cost valuation", "#6366f1")
    with c4:
        render_kpi("Low-Stock Alerts", str(kpis["low_stock_count"]), "Requires reordering", "#ef4444")
    with c5:
        render_kpi("Expiring <90d", str(kpis["expiring_soon_count"]), "Batch expiry risks", "#f59e0b")
    with c6:
        render_kpi("Pending Orders", str(len(recommendations)), "Awaiting approval", "#8b5cf6")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Interactive Visualizations
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("📊 Current Stock vs Reorder Level")
        medicines = InventoryService.get_all_medicines()
        if medicines:
            m_df = pd.DataFrame(medicines)
            # Create grouped or comparative bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=m_df["medicine_name"],
                y=m_df["current_stock"],
                name="Current Stock",
                marker_color=m_df["current_stock"].apply(
                    lambda x: "#ef4444" if x <= 20 else ("#f59e0b" if x <= 50 else "#10b981")
                ),
                text=m_df["current_stock"],
                textposition="auto"
            ))
            fig.add_trace(go.Scatter(
                x=m_df["medicine_name"],
                y=m_df["reorder_level"],
                name="Reorder Level Threshold",
                mode="lines+markers",
                line=dict(color="#ef4444", width=2, dash="dash"),
                marker=dict(symbol="diamond", size=7)
            ))
            fig.update_layout(
                margin=dict(l=20, r=20, t=30, b=100),
                height=380,
                xaxis_tickangle=-45,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No medicine inventory found. Please seed the database.")

    with col_right:
        st.subheader("🔥 Top 6 Fast-Moving Medicines (30d)")
        top_meds = SalesService.get_top_selling_medicines(days=30, limit=6)
        if top_meds:
            t_df = pd.DataFrame(top_meds)
            fig_top = px.bar(
                t_df,
                x="total_sold",
                y="medicine_name",
                orientation="h",
                text="total_sold",
                labels={"total_sold": "Units Sold", "medicine_name": "Medicine"},
                color="total_sold",
                color_continuous_scale="Teal"
            )
            fig_top.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=380,
                showlegend=False,
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
                template="plotly_white"
            )
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("No historical sales records to display.")

    st.markdown("---")

    # 4. Critical Action Center
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🚨 Priority Active Alerts")
        if alerts:
            for alt in alerts[:4]:
                badge = get_priority_badge(alt["priority"])
                st.markdown(f"""
                <div style="padding:10px 14px; background:#f8fafc; border-left:4px solid {'#ef4444' if alt['priority']=='Critical' else '#f59e0b'}; border-radius:6px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>{alt['alert_type']} — {alt['medicine_name']}</strong>
                        {badge}
                    </div>
                    <div style="font-size:0.85rem; color:#475569; margin-top:4px;">{alt['message']}</div>
                </div>
                """, unsafe_allow_html=True)
            if len(alerts) > 4:
                st.caption(f"+ {len(alerts) - 4} more active alerts. Visit the 'Alerts' tab to view all.")
        else:
            st.success("✓ No active inventory alerts! All medicines within healthy levels.")

    with col_b:
        st.subheader("📋 Pending Restock Proposals")
        if recommendations:
            for rec in recommendations[:3]:
                badge = get_priority_badge(rec["priority"])
                st.markdown(f"""
                <div style="padding:10px 14px; background:#f8fafc; border-left:4px solid #8b5cf6; border-radius:6px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>{rec['medicine_name']}</strong>
                        {badge}
                    </div>
                    <div style="font-size:0.85rem; color:#475569; margin-top:4px;">
                        Proposed Restock: <strong>{rec['recommended_quantity']} units</strong> (Est. Cost: INR {rec['estimated_cost']:,.2f})
                        <br><em>Supplier: {rec['supplier']} | Lead Time: {rec['lead_time']} days</em>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.info("👉 Go to **'Procurement Approvals'** or **'Agent Activity'** to Approve, Edit, or Reject these proposals.")
        else:
            st.success("✓ No pending purchase orders. All restocking recommendations processed.")
