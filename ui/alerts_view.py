import streamlit as st
import pandas as pd
from ui.components import render_header, render_kpi, get_priority_badge
from services.alert_service import AlertService


def render_alerts_view():
    render_header(
        "Real-Time Alerts & Early Warnings",
        "Automated Surveillance for Stockouts, Near-Expiry Batches & Demand Surges"
    )

    # Top Toolbar
    t1, t2, t3, t4 = st.columns([1.5, 1.5, 1.5, 2])
    with t1:
        status_sel = st.selectbox("Status", ["Active", "Resolved", "Dismissed", "All"])
    with t2:
        prio_sel = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"])
    with t3:
        type_sel = st.selectbox("Alert Type", ["All", "Low Stock", "Expiry Risk", "Demand Surge"])
    with t4:
        st.write("")
        st.write("")
        if st.button("🔄 Scan & Refresh Alerts Now", use_container_width=True, type="primary"):
            new_alts = AlertService.scan_and_generate_alerts()
            st.success(f"✓ Scan completed! {new_alts} new alert(s) identified.")
            st.rerun()

    # Fetch alerts
    alerts = AlertService.get_all_alerts(status_filter=status_sel, priority_filter=prio_sel)
    if type_sel != "All":
        alerts = [a for a in alerts if a["alert_type"] == type_sel]

    # Metrics Summary
    crit_count = sum(1 for a in alerts if a["priority"] == "Critical")
    high_count = sum(1 for a in alerts if a["priority"] == "High")
    low_stock_count = sum(1 for a in alerts if a["alert_type"] == "Low Stock")
    expiry_count = sum(1 for a in alerts if a["alert_type"] == "Expiry Risk")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi("Critical Warnings", str(crit_count), "Immediate action needed", "#ef4444")
    with c2:
        render_kpi("High Priority", str(high_count), "Action required soon", "#f59e0b")
    with c3:
        render_kpi("Low Stock Items", str(low_stock_count), "Under reorder threshold", "#3b82f6")
    with c4:
        render_kpi("Expiry Hazards", str(expiry_count), "Batches <90 days", "#8b5cf6")

    st.markdown("---")

    # Render Alerts List
    st.subheader(f"🚨 Alerts ({len(alerts)} items)")

    if not alerts:
        st.success(f"✓ No alerts found matching criteria ({status_sel} / {prio_sel} / {type_sel}).")
        return

    for alt in alerts:
        prio = alt["priority"]
        border_col = "#ef4444" if prio == "Critical" else ("#ea580c" if prio == "High" else "#ca8a04")
        badge = get_priority_badge(prio)

        with st.container():
            st.markdown(f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:6px solid {border_col}; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="font-size:1.05rem; color:#0f172a;">{alt['medicine_name']}</strong>
                        <span style="color:#64748b; font-size:0.85rem; margin-left:8px;">({alt['category']})</span>
                    </div>
                    <div>
                        {badge}
                        <span style="font-size:0.8rem; color:#94a3b8; margin-left:8px;">{alt['alert_date']}</span>
                    </div>
                </div>
                <div style="margin:8px 0 6px 0; color:#334155; font-size:0.95rem;">
                    <strong>{alt['alert_type']}:</strong> {alt['message']}
                </div>
                <div style="font-size:0.8rem; color:#64748b;">
                    Current Stock: <strong>{alt['current_stock']} units</strong> | Status: <strong>{alt['alert_status']}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons for active alerts
            if alt["alert_status"] == "Active":
                b1, b2, _ = st.columns([1, 1, 4])
                with b1:
                    if st.button("Resolve", key=f"res_{alt['alert_id']}"):
                        AlertService.update_alert_status(alt["alert_id"], "Resolved")
                        st.rerun()
                with b2:
                    if st.button("Dismiss", key=f"dis_{alt['alert_id']}"):
                        AlertService.update_alert_status(alt["alert_id"], "Dismissed")
                        st.rerun()
