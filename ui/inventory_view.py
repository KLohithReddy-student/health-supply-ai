from datetime import date, timedelta
import streamlit as st
import pandas as pd
from ui.components import render_header, render_kpi, get_priority_badge
from services.inventory_service import InventoryService


def render_inventory_view():
    render_header(
        "Medicine Inventory Management",
        "Catalog Monitoring, Real-Time Stock Tracking & Expiry Surveillance"
    )

    kpis = InventoryService.get_inventory_kpis()

    # Search and Filter Toolbar
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_query = st.text_input("🔍 Search Medicine or Category", placeholder="e.g. Paracetamol, Antibiotic...")
    with f_col2:
        cat_options = ["All"] + kpis["categories"]
        selected_category = st.selectbox("Filter Category", cat_options)
    with f_col3:
        low_stock_only = st.checkbox("Show Low Stock Only", value=False)

    # Fetch medicines
    meds = InventoryService.get_all_medicines(
        category=selected_category,
        low_stock_only=low_stock_only,
        search=search_query
    )

    # Action Accordions: Add New Medicine & Quick Stock Adjustment
    with st.expander("➕ Add New Medicine to Catalog"):
        with st.form("add_medicine_form"):
            ac1, ac2 = st.columns(2)
            with ac1:
                new_name = st.text_input("Medicine Name (with dosage)*", placeholder="e.g. Ciprofloxacin 500mg")
                new_cat = st.selectbox("Category*", [
                    "Analgesic / Antipyretic", "Antibiotic", "Antidiabetic",
                    "Antihistamine / Allergy", "Cardiovascular", "Antacid / Gastrointestinal",
                    "Respiratory / Antitussive", "Hydration", "Vitamins & Supplements", "Other"
                ])
                new_stock = st.number_input("Initial Current Stock*", min_value=0, value=50, step=5)
                new_reorder = st.number_input("Reorder Level Threshold*", min_value=1, value=30, step=5)
            with ac2:
                new_price = st.number_input("Unit Price (INR)*", min_value=0.5, value=45.0, step=5.0)
                new_expiry = st.date_input("Expiry Date*", min_value=date.today(), value=date.today() + timedelta(days=365))
                new_supplier = st.text_input("Distributor / Supplier", value="Apex Pharma Distributors")
                new_lead = st.number_input("Supplier Lead Time (Days)", min_value=1, max_value=30, value=3)

            submit_add = st.form_submit_button("Register Medicine", use_container_width=True)
            if submit_add:
                if not new_name.strip():
                    st.error("Please provide a valid medicine name.")
                else:
                    try:
                        new_id = InventoryService.add_medicine(
                            name=new_name,
                            category=new_cat,
                            current_stock=int(new_stock),
                            reorder_level=int(new_reorder),
                            unit_price=float(new_price),
                            expiry_date=new_expiry,
                            supplier=new_supplier,
                            lead_time=int(new_lead)
                        )
                        st.success(f"✓ Medicine '{new_name}' added successfully (ID: {new_id})!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding medicine: {e}")

    with st.expander("⚡ Quick Stock Adjustment / Reorder Level Edit"):
        if meds:
            med_options = {m["medicine_name"]: m["medicine_id"] for m in meds}
            sel_med_name = st.selectbox("Select Medicine to Adjust", list(med_options.keys()))
            sel_med_id = med_options[sel_med_name]
            sel_med_data = InventoryService.get_medicine_by_id(sel_med_id)

            if sel_med_data:
                qc1, qc2, qc3 = st.columns(3)
                with qc1:
                    adj_stock = st.number_input("Current Stock Units", min_value=0, value=sel_med_data["current_stock"], step=5)
                with qc2:
                    adj_reorder = st.number_input("Reorder Level", min_value=1, value=sel_med_data["reorder_level"], step=5)
                with qc3:
                    adj_price = st.number_input("Unit Price (INR)", min_value=1.0, value=float(sel_med_data["unit_price"]), step=1.0)

                if st.button("Save Changes to Medicine", use_container_width=True):
                    InventoryService.update_medicine(
                        sel_med_id,
                        current_stock=int(adj_stock),
                        reorder_level=int(adj_reorder),
                        unit_price=float(adj_price)
                    )
                    st.success(f"✓ Updated '{sel_med_name}' successfully!")
                    st.rerun()

    st.markdown("---")

    # Inventory Table Display
    st.subheader(f"📋 Inventory Catalog ({len(meds)} items)")

    if meds:
        formatted_list = []
        for m in meds:
            status_badge = (
                "🔴 OUT OF STOCK" if m["current_stock"] == 0
                else ("🟠 LOW STOCK" if m["current_stock"] <= m["reorder_level"] else "🟢 ADEQUATE")
            )
            expiry_badge = (
                f"⚠️ EXPIRED ({abs(m['days_to_expiry'])}d ago)" if m["days_to_expiry"] < 0
                else (f"🟡 Expiring in {m['days_to_expiry']}d" if m["days_to_expiry"] <= 90 else f"{m['expiry_date']}")
            )

            formatted_list.append({
                "ID": m["medicine_id"],
                "Medicine Name": m["medicine_name"],
                "Category": m["category"],
                "Current Stock": m["current_stock"],
                "Reorder Level": m["reorder_level"],
                "Unit Price (INR)": f"{m['unit_price']:.2f}",
                "Inventory Value": f"{m['current_stock'] * m['unit_price']:.2f}",
                "Lead Time": f"{m['lead_time']} days",
                "Expiry Status": expiry_badge,
                "Stock Status": status_badge,
                "Supplier": m["supplier"]
            })

        df_display = pd.DataFrame(formatted_list)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No medicines matched your search/filter criteria.")
