from datetime import date, timedelta
import io
import streamlit as st
import pandas as pd
import plotly.express as px
from ui.components import render_header
from services.sales_service import SalesService
from services.inventory_service import InventoryService


def render_sales_view():
    render_header(
        "Sales Records & Dispensation History",
        "Log Daily Medicine Dispensation, Analyze Sales Velocity & Manage Transactions"
    )

    # 1. Log New Sale Form
    with st.expander("📝 Record New Daily Medicine Sale", expanded=False):
        meds = InventoryService.get_all_medicines()
        if meds:
            med_dict = {f"{m['medicine_name']} (In Stock: {m['current_stock']})": m["medicine_id"] for m in meds}
            with st.form("log_sale_form"):
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    sel_label = st.selectbox("Select Dispensed Medicine*", list(med_dict.keys()))
                    selected_med_id = med_dict[sel_label]
                with sc2:
                    sale_qty = st.number_input("Quantity Dispensed (Units)*", min_value=1, value=5, step=1)
                with sc3:
                    sale_dt = st.date_input("Sale Date*", value=date.today())

                submit_sale = st.form_submit_button("Record Sale & Update Inventory", use_container_width=True)
                if submit_sale:
                    try:
                        res = SalesService.log_sale(
                            medicine_id=selected_med_id,
                            quantity_sold=int(sale_qty),
                            sale_date=sale_dt
                        )
                        st.success(f"✓ Recorded sale of {sale_qty} units for '{res['medicine_name']}'. Remaining stock: {res['remaining_stock']} units.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to record sale: {e}")
        else:
            st.warning("Please seed the inventory before logging sales.")

    # 2. CSV Bulk Import / Export
    with st.expander("📥 Bulk CSV Import / Export"):
        c_imp, c_exp = st.columns(2)
        with c_imp:
            st.markdown("**Import Sales from CSV**")
            uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
            if uploaded_file is not None:
                try:
                    import_df = pd.read_csv(uploaded_file)
                    st.write("Preview of uploaded data:", import_df.head(3))
                    if st.button("Confirm Bulk Import"):
                        imported_count = SalesService.bulk_import_sales(import_df)
                        st.success(f"✓ Successfully imported {imported_count} sales transactions into database!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
        with c_exp:
            st.markdown("**Download Template / Export**")
            sample_template = pd.DataFrame([
                {"medicine_id": 1, "sale_date": date.today().strftime("%Y-%m-%d"), "quantity_sold": 25},
                {"medicine_id": 2, "sale_date": date.today().strftime("%Y-%m-%d"), "quantity_sold": 15}
            ])
            csv_buf = io.StringIO()
            sample_template.to_csv(csv_buf, index=False)
            st.download_button(
                label="📄 Download Sample Sales CSV Template",
                data=csv_buf.getvalue(),
                file_name="sales_template.csv",
                mime="text/csv"
            )

    st.markdown("---")

    # 3. Sales Trend Visualizer
    st.subheader("📈 Daily Dispensation Trend")
    all_meds = InventoryService.get_all_medicines()
    med_filter_options = {"All Medicines": None}
    for m in all_meds:
        med_filter_options[m["medicine_name"]] = m["medicine_id"]

    t_col1, t_col2 = st.columns([2, 1])
    with t_col1:
        sel_chart_med = st.selectbox("Select Medicine to Chart", list(med_filter_options.keys()))
    with t_col2:
        chart_days = st.slider("Time Window (Past Days)", min_value=14, max_value=180, value=60, step=7)

    target_med_id = med_filter_options[sel_chart_med]
    timeline_data = SalesService.get_daily_sales_timeline(medicine_id=target_med_id, days=chart_days)

    if timeline_data:
        t_df = pd.DataFrame(timeline_data)
        fig_timeline = px.line(
            t_df,
            x="date",
            y="quantity",
            labels={"date": "Date", "quantity": "Units Sold"},
            title=f"Dispensation Volume ({sel_chart_med}) - Past {chart_days} Days"
        )
        fig_timeline.update_traces(line_color="#0284c7", line_width=2.5)
        fig_timeline.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            height=320,
            template="plotly_white"
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No sales data available for this selection.")

    st.markdown("---")

    # 4. Sales History Table
    st.subheader("📋 Recent Transaction History")
    sales_history = SalesService.get_sales_history(medicine_id=target_med_id, limit=300)

    if sales_history:
        sh_df = pd.DataFrame(sales_history)
        sh_df["sale_date"] = pd.to_datetime(sh_df["sale_date"]).dt.strftime("%Y-%m-%d")
        sh_df.rename(columns={
            "sales_id": "Sale ID",
            "medicine_name": "Medicine",
            "category": "Category",
            "sale_date": "Date",
            "quantity_sold": "Units Sold",
            "total_revenue": "Revenue (INR)"
        }, inplace=True)

        st.dataframe(
            sh_df[["Sale ID", "Medicine", "Category", "Date", "Units Sold", "Revenue (INR)"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No transaction records found.")
