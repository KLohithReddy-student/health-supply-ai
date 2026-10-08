import streamlit as st
import pandas as pd
from ui.components import render_header, render_kpi, get_priority_badge
from services.restock_service import RestockService


def render_procurement_view():
    render_header(
        "Procurement & Human Approval Interface",
        "Compliance Verification, Order Adjustment & Human-in-the-Loop Decision Authorisation"
    )

    st.markdown("""
    <div style="background:#eff6ff; border:1px solid #bfdbfe; border-left:6px solid #3b82f6; border-radius:8px; padding:12px 18px; margin-bottom:20px;">
        <h4 style="margin:0 0 6px 0; color:#1e40af;">🛡️ Human-in-the-Loop Compliance Safeguard</h4>
        <p style="margin:0; font-size:0.85rem; color:#1d4ed8;">
            AI Agents propose restocking orders based on predictive demand, but <strong>no real orders are executed without explicit human verification</strong>.
            As the pharmacist, you have full authority to <strong>Approve</strong>, <strong>Adjust Quantity</strong>, or <strong>Reject</strong> every proposal.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_pending, tab_history = st.tabs(["⏳ Pending Approvals", "📜 Order History & Audit Trail"])

    with tab_pending:
        pending_recs = RestockService.get_all_recommendations(status_filter="Pending")

        if not pending_recs:
            st.success("✓ No pending purchase orders awaiting review. All restock proposals have been processed.")
        else:
            st.subheader(f"📋 Proposals Awaiting Your Decision ({len(pending_recs)})")

            for rec in pending_recs:
                rid = rec["recommendation_id"]
                med_name = rec["medicine_name"]
                prop_qty = rec["recommended_quantity"]
                prio = rec["priority"]
                badge = get_priority_badge(prio)
                unit_price = rec["unit_price"]
                est_cost = prop_qty * unit_price
                supplier = rec["supplier"]
                lead_time = rec["lead_time"]

                with st.expander(f"📦 {med_name} — Proposed Order: {prop_qty} units (INR {est_cost:,.2f})", expanded=True):
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.markdown(f"""
                        - **Medicine:** {med_name} ({rec['category']})
                        - **Current Stock:** `{rec['current_stock']} units`
                        - **Reorder Level:** `{rec['reorder_level']} units`
                        - **Supplier:** `{supplier}`
                        """)
                    with col_info2:
                        st.markdown(f"""
                        - **Supplier Lead Time:** `{lead_time} days`
                        - **Unit Price:** `INR {unit_price:.2f}`
                        - **Estimated Order Cost:** `INR {est_cost:,.2f}`
                        - **Priority:** {badge}
                        """, unsafe_allow_html=True)

                    st.markdown(f"**Rationale:** *{rec['reason']}*")
                    st.markdown("---")

                    # Human Decision Form
                    st.markdown("##### ✍️ Pharmacist Decision")
                    c_act1, c_act2, c_act3 = st.columns([1.5, 1.5, 2])

                    with c_act1:
                        fulfill_now = st.checkbox("Simulate immediate stock receipt", key=f"rec_ful_{rid}", value=False)
                        if st.button("✅ Approve Order", key=f"app_{rid}", type="primary", use_container_width=True):
                            RestockService.approve_recommendation(rid, approved_qty=prop_qty, fulfill_immediately=fulfill_now)
                            st.success(f"✓ Approved purchase proposal for {prop_qty} units of {med_name}!")
                            st.rerun()

                    with c_act2:
                        edit_qty = st.number_input("Adjust Quantity", min_value=1, value=prop_qty, step=5, key=f"qty_{rid}")
                        if st.button("✏️ Approve with Edited Qty", key=f"edit_btn_{rid}", use_container_width=True):
                            RestockService.approve_recommendation(rid, approved_qty=int(edit_qty), fulfill_immediately=fulfill_now)
                            st.success(f"✓ Approved revised purchase of {edit_qty} units of {med_name}!")
                            st.rerun()

                    with c_act3:
                        rej_reason = st.text_input("Rejection Reason (optional)", placeholder="e.g. Budget limit, alternate brand in stock", key=f"rej_txt_{rid}")
                        if st.button("❌ Reject Proposal", key=f"rej_btn_{rid}", use_container_width=True):
                            RestockService.reject_recommendation(rid, rejection_reason=rej_reason)
                            st.warning(f"Rejected proposal for {med_name}.")
                            st.rerun()

    with tab_history:
        st.subheader("📜 Historical Restock Decisions")
        all_recs = RestockService.get_all_recommendations(status_filter="All")
        non_pending = [r for r in all_recs if r["status"] != "Pending"]

        if not non_pending:
            st.info("No approved or rejected order records yet.")
        else:
            history_rows = []
            for r in non_pending:
                history_rows.append({
                    "Order ID": r["recommendation_id"],
                    "Medicine": r["medicine_name"],
                    "Recommended": r["recommended_quantity"],
                    "Approved Qty": r["approved_quantity"] or r["recommended_quantity"],
                    "Total Value (INR)": f"{r['estimated_cost']:,.2f}",
                    "Status": r["status"],
                    "Priority": r["priority"],
                    "Date Proposed": r["recommendation_date"],
                    "Processed At": str(r["processed_at"])[:16] if r["processed_at"] else "N/A"
                })

            st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)

            # Option to fulfill approved orders that haven't received stock
            approved_orders = [r for r in non_pending if r["status"] == "Approved"]
            if approved_orders:
                st.markdown("---")
                st.markdown("##### 🚚 Simulate Delivery Arrival for Approved Orders")
                f_map = {f"Order #{r['recommendation_id']}: {r['medicine_name']} ({r['approved_quantity']} units)": r['recommendation_id'] for r in approved_orders}
                sel_order_label = st.selectbox("Select Approved Order to Receive", list(f_map.keys()))
                if st.button("📦 Mark Delivery Received & Increment Inventory"):
                    ord_id = f_map[sel_order_label]
                    RestockService.fulfill_order(ord_id)
                    st.success(f"✓ Stock received and added to inventory catalog!")
                    st.rerun()
