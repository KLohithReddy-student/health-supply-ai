import streamlit as st
import pandas as pd
from ui.components import render_header, get_priority_badge
from services.inventory_service import InventoryService
from services.restock_service import RestockService
from agents.orchestrator import orchestrator


def render_restock_view():
    render_header(
        "Smart Restocking Intelligence",
        "Data-Driven Inventory Replenishment & Explainable Safety Stock Optimization"
    )

    # Formula Callout
    st.markdown("""
    <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-left:6px solid #10b981; border-radius:8px; padding:12px 18px; margin-bottom:20px;">
        <h4 style="margin:0 0 6px 0; color:#166534;">📐 Explainable Replenishment Logic</h4>
        <code style="font-size:1.05rem; color:#14532d; font-weight:700;">Recommended Restock = max(0, Predicted Demand + Safety Stock - Current Stock)</code>
        <p style="margin:6px 0 0 0; font-size:0.85rem; color:#15803d;">
            Where <strong>Safety Stock</strong> is dynamically weighted by supplier lead time and historical demand volatility (<em>SS = Z × σ × √LeadTime</em>).
        </p>
    </div>
    """, unsafe_allow_html=True)

    meds = InventoryService.get_all_medicines()
    if not meds:
        st.warning("Please seed the inventory catalog first.")
        return

    # Trigger Batch Restock Calculations
    calc_rows = []
    with st.spinner("Computing replenishment metrics across catalog..."):
        for m in meds:
            calc = RestockService.calculate_restock_requirements(m["medicine_id"], forecast_days=7)
            calc_rows.append(calc)

    df_calc = pd.DataFrame(calc_rows)

    # Summary Metrics
    tot_rec_units = df_calc["recommended_quantity"].sum()
    tot_est_spend = df_calc["estimated_cost"].sum()
    crit_count = len(df_calc[df_calc["priority"] == "Critical"])
    high_count = len(df_calc[df_calc["priority"] == "High"])

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Restock Units Needed", f"{tot_rec_units:,} units")
    with m2:
        st.metric("Estimated Procurement Cost", f"INR {tot_est_spend:,.2f}")
    with m3:
        st.metric("Critical Stockout Risks", f"{crit_count} SKUs")
    with m4:
        st.metric("High Priority Reorders", f"{high_count} SKUs")

    st.markdown("---")

    # Interactive Restock Table
    st.subheader("📋 Replenishment Decision Matrix")

    # Priority filter
    sel_prio = st.selectbox("Filter Priority", ["All Priorities", "Critical Only", "High & Critical", "Actionable Only (>0 units)"])
    filtered_df = df_calc.copy()
    if sel_prio == "Critical Only":
        filtered_df = filtered_df[filtered_df["priority"] == "Critical"]
    elif sel_prio == "High & Critical":
        filtered_df = filtered_df[filtered_df["priority"].isin(["Critical", "High"])]
    elif sel_prio == "Actionable Only (>0 units)":
        filtered_df = filtered_df[filtered_df["recommended_quantity"] > 0]

    # Render nice table
    display_rows = []
    for _, r in filtered_df.iterrows():
        display_rows.append({
            "Medicine": r["medicine_name"],
            "Current Stock": r["current_stock"],
            "Reorder Point": r["reorder_level"],
            "7d Forecast": r["predicted_demand"],
            "Safety Buffer": r["safety_stock"],
            "Recommended Restock": f"⚡ {r['recommended_quantity']} units" if r["recommended_quantity"] > 0 else "0 (Adequate)",
            "Est. Cost (INR)": f"{r['estimated_cost']:,.2f}",
            "Priority": r["priority"],
            "Formula / Reason": r["reason"]
        })

    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

    # Quick One-Click Action
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🚀 Automated Procurement Pipeline")
    st.write("Forward actionable restocking recommendations to the Procurement & Compliance Agent for PO generation.")

    if st.button("Trigger Procurement Agent for All Actionable Items", type="primary"):
        with st.spinner("Executing Multi-Agent Procurement pipeline..."):
            count = 0
            for r in calc_rows:
                if r["recommended_quantity"] > 0:
                    orchestrator.run_workflow_for_medicine(r["medicine_id"], forecast_period=7)
                    count += 1
            st.success(f"✓ Successfully generated purchase-order proposals for {count} medicines! Awaiting human approval in Procurement tab.")
            st.rerun()
