import streamlit as st
from ui.components import render_header, render_agent_activity_box, get_priority_badge
from services.inventory_service import InventoryService
from services.restock_service import RestockService
from agents.orchestrator import orchestrator


def render_agent_activity_view():
    render_header(
        "Agentic AI Orchestration Console",
        "Autonomous Multi-Agent Collaboration Pipeline for Pharmaceutical Supply Intelligence"
    )

    # Agent Architecture Diagram Callout
    st.markdown("""
    <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:14px 18px; margin-bottom:20px;">
        <h4 style="margin:0 0 8px 0; color:#0f172a;">🤖 Multi-Agent Pipeline Architecture</h4>
        <div style="display:flex; flex-wrap:wrap; align-items:center; gap:8px; font-size:0.88rem; font-weight:600;">
            <span style="background:#e0f2fe; color:#0369a1; padding:6px 12px; border-radius:6px;">1. Inventory Analyst</span>
            <span style="color:#94a3b8;">➔</span>
            <span style="background:#ede9fe; color:#6d28d9; padding:6px 12px; border-radius:6px;">2. Demand Forecaster</span>
            <span style="color:#94a3b8;">➔</span>
            <span style="background:#fef3c7; color:#b45309; padding:6px 12px; border-radius:6px;">3. Restock Optimizer</span>
            <span style="color:#94a3b8;">➔</span>
            <span style="background:#dcfce7; color:#15803d; padding:6px 12px; border-radius:6px;">4. Procurement Agent</span>
            <span style="color:#94a3b8;">➔</span>
            <span style="background:#fee2e2; color:#b91c1c; padding:6px 12px; border-radius:6px;">5. Human Approval</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    meds = InventoryService.get_all_medicines()
    if not meds:
        st.warning("Please seed the inventory first.")
        return

    med_map = {f"{m['medicine_name']} (Stock: {m['current_stock']} | ROP: {m['reorder_level']})": m["medicine_id"] for m in meds}

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
    with col_ctrl1:
        sel_label = st.selectbox("Select Medicine for Agentic Analysis", list(med_map.keys()))
        selected_med_id = med_map[sel_label]
    with col_ctrl2:
        forecast_days = st.selectbox("Forecast Horizon", [7, 14, 30], index=0, format_func=lambda x: f"{x} Days")
    with col_ctrl3:
        st.write("")
        st.write("")
        run_btn = st.button("🚀 Trigger Agent Workflow", type="primary", use_container_width=True)

    # Session state for latest execution result
    if "agent_workflow_state" not in st.session_state:
        st.session_state.agent_workflow_state = None

    if run_btn:
        with st.spinner("Multi-Agent team is analyzing inventory, running ML forecast, and generating proposals..."):
            state = orchestrator.run_workflow_for_medicine(selected_med_id, forecast_period=forecast_days)
            st.session_state.agent_workflow_state = state
            st.success("✓ Multi-Agent workflow completed successfully!")

    st.markdown("---")

    # Render Activity Logs & Proposal Result
    state = st.session_state.agent_workflow_state

    if state:
        st.subheader("📋 Live Agent Activity Log")
        for log_entry in state.activity_logs:
            render_agent_activity_box(log_entry.to_dict())

        st.markdown("<br>", unsafe_allow_html=True)

        # Show Output Synthesis
        st.subheader("📦 Generated Decision & Proposal")
        c_p1, c_p2 = st.columns([3, 2])

        with c_p1:
            inv = state.inventory_data
            fc = state.forecast_data
            rs = state.restock_data

            st.markdown(f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:16px;">
                <h4 style="margin:0 0 10px 0;">{inv.get('medicine_name')}</h4>
                <p style="margin:0 0 6px 0;"><strong>Stock Status:</strong> {inv.get('stock_status')} ({inv.get('current_stock')} units on hand)</p>
                <p style="margin:0 0 6px 0;"><strong>Demand Trend:</strong> {inv.get('trend')}</p>
                <p style="margin:0 0 6px 0;"><strong>ML Predicted Demand ({fc.get('forecast_period')}d):</strong> {fc.get('total_predicted_demand')} units ({fc.get('model_used')})</p>
                <p style="margin:0 0 6px 0;"><strong>Model Accuracy:</strong> MAE: {fc.get('mae')} | RMSE: {fc.get('rmse')}</p>
                <p style="margin:0 0 6px 0;"><strong>Safety Stock Buffer:</strong> {rs.get('safety_stock')} units</p>
                <p style="margin:0; font-weight:600; color:#0f172a;"><strong>Recommended Restock:</strong> {rs.get('recommended_quantity')} units (Priority: {rs.get('priority')})</p>
            </div>
            """, unsafe_allow_html=True)

        with c_p2:
            prop = state.proposal_data
            if prop.get("requires_approval"):
                st.markdown(f"""
                <div style="background:#fffbeb; border:1px solid #fef3c7; border-left:4px solid #f59e0b; border-radius:8px; padding:14px;">
                    <h5 style="margin:0 0 6px 0; color:#b45309;">⚠️ Awaiting Pharmacist Decision</h5>
                    <p style="margin:0 0 6px 0; font-size:0.88rem;"><strong>Proposed Order:</strong> {prop.get('proposed_units')} units</p>
                    <p style="margin:0 0 6px 0; font-size:0.88rem;"><strong>Estimated Value:</strong> INR {prop.get('estimated_cost', 0):,.2f}</p>
                    <p style="margin:0 0 10px 0; font-size:0.88rem;"><strong>Supplier:</strong> {prop.get('supplier')}</p>
                </div>
                """, unsafe_allow_html=True)

                rec_id = prop.get("recommendation_id")
                if rec_id:
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("✅ Approve Proposal", key="live_app_btn", type="primary", use_container_width=True):
                            RestockService.approve_recommendation(rec_id)
                            st.success("✓ Proposal Approved! Database updated.")
                            st.session_state.agent_workflow_state = None
                            st.rerun()
                    with col_b2:
                        if st.button("❌ Reject Proposal", key="live_rej_btn", use_container_width=True):
                            RestockService.reject_recommendation(rec_id, "Rejected in Agent Console")
                            st.warning("Proposal Rejected.")
                            st.session_state.agent_workflow_state = None
                            st.rerun()
            else:
                st.success("✓ Sufficient inventory. No purchase order required.")
    else:
        st.info("Select a medicine above and click **'Trigger Agent Workflow'** to execute the multi-agent pipeline.")
