import logging
from datetime import date, timedelta
from database.connection import get_db
from database.models import Medicine, SalesRecord
from agents.state import AgentWorkflowState

logger = logging.getLogger(__name__)


class InventoryAnalystAgent:
    """
    Agent 1: Inventory Analyst Agent
    - Reads inventory and sales data
    - Checks current stock, reorder level and expiry
    - Identifies recent demand and seasonal trends
    """
    def __init__(self):
        self.name = "Inventory Analyst Agent"

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        with get_db() as session:
            med = session.query(Medicine).filter(Medicine.medicine_id == state.medicine_id).first()
            if not med:
                state.log(self.name, f"Medicine ID {state.medicine_id} not found in database", "error")
                state.status = "error"
                return state

            # Fetch last 30 days of sales
            thirty_days_ago = date.today() - timedelta(days=30)
            sales = (
                session.query(SalesRecord.sale_date, SalesRecord.quantity_sold)
                .filter(SalesRecord.medicine_id == state.medicine_id, SalesRecord.sale_date >= thirty_days_ago)
                .order_by(SalesRecord.sale_date.asc())
                .all()
            )

            current_stock = med.current_stock
            reorder_level = med.reorder_level
            days_to_expiry = (med.expiry_date - date.today()).days
            unit_price = med.unit_price
            lead_time = med.lead_time
            supplier = med.supplier
            med_name = med.medicine_name
            category = med.category

        # Trend analysis
        sales_vals = [s[1] for s in sales]
        if len(sales_vals) >= 14:
            first_half = sum(sales_vals[:len(sales_vals)//2]) / (len(sales_vals)//2)
            second_half = sum(sales_vals[len(sales_vals)//2:]) / (len(sales_vals) - len(sales_vals)//2)
            if second_half > first_half * 1.15:
                trend = "Surging Demand"
            elif second_half < first_half * 0.85:
                trend = "Declining Demand"
            else:
                trend = "Stable Demand"
        else:
            trend = "Steady"

        stock_status = (
            "Stockout" if current_stock == 0
            else ("Critical Low" if current_stock <= (reorder_level * 0.3)
            else ("Low Stock" if current_stock <= reorder_level else "Adequate"))
        )

        state.inventory_data = {
            "medicine_id": state.medicine_id,
            "medicine_name": med_name,
            "category": category,
            "current_stock": current_stock,
            "reorder_level": reorder_level,
            "days_to_expiry": days_to_expiry,
            "stock_status": stock_status,
            "trend": trend,
            "unit_price": unit_price,
            "lead_time": lead_time,
            "supplier": supplier
        }

        # User-facing concise activity log
        state.log(
            self.name,
            f"Retrieved stock data ({current_stock} units, {stock_status}) & detected '{trend}' pattern for {med_name}",
            "warning" if stock_status in ["Critical Low", "Low Stock", "Stockout"] else "success"
        )
        return state
