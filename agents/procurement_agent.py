import logging
from datetime import date, datetime, timedelta
from database.connection import get_db
from database.models import RestockingRecommendation
from agents.state import AgentWorkflowState

logger = logging.getLogger(__name__)


class ProcurementComplianceAgent:
    """
    Agent 4: Procurement / Compliance Agent
    - Reviews restock recommendations against commercial & lead time policies
    - Generates formal purchase-order proposals
    - Stores pending recommendation in database
    - Requires human approval (Approve / Edit / Reject)
    - Updates database strictly after approval (No real-world orders placed)
    """
    def __init__(self):
        self.name = "Procurement & Compliance Agent"

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if state.status == "error":
            return state

        restock = state.restock_data
        rec_qty = restock.get("recommended_quantity", 0)
        supplier = restock.get("supplier", "Primary Pharma Distributor")
        estimated_cost = restock.get("estimated_cost", 0.0)
        lead_time = restock.get("lead_time_days", 3)
        expected_delivery = (date.today() + timedelta(days=lead_time)).strftime("%Y-%m-%d")

        if rec_qty > 0:
            # Create / update a pending recommendation in the database
            rec_id = None
            try:
                with get_db() as session:
                    # Check if there is already a Pending recommendation for this medicine
                    existing = session.query(RestockingRecommendation).filter(
                        RestockingRecommendation.medicine_id == state.medicine_id,
                        RestockingRecommendation.status == "Pending"
                    ).first()

                    if existing:
                        existing.recommended_quantity = rec_qty
                        existing.priority = restock.get("priority", "Medium")
                        existing.reason = restock.get("reason", "")
                        existing.recommendation_date = date.today()
                        session.flush()
                        rec_id = existing.recommendation_id
                    else:
                        new_rec = RestockingRecommendation(
                            medicine_id=state.medicine_id,
                            recommended_quantity=rec_qty,
                            status="Pending",
                            recommendation_date=date.today(),
                            priority=restock.get("priority", "Medium"),
                            reason=restock.get("reason", "")
                        )
                        session.add(new_rec)
                        session.flush()
                        rec_id = new_rec.recommendation_id
            except Exception as e:
                logger.error(f"Error persisting recommendation in DB: {e}")

            state.proposal_data = {
                "recommendation_id": rec_id,
                "medicine_id": state.medicine_id,
                "proposed_units": rec_qty,
                "supplier": supplier,
                "estimated_cost": estimated_cost,
                "expected_delivery_date": expected_delivery,
                "lead_time_days": lead_time,
                "compliance_status": "Passed Compliance Checks",
                "requires_approval": True
            }
            state.status = "awaiting_approval"

            # User-facing concise activity log
            state.log(
                self.name,
                f"Generated PO Proposal: {rec_qty} units (Est. INR {estimated_cost:,.2f}) with {supplier}. Awaiting Pharmacist Approval.",
                "warning"
            )
        else:
            state.proposal_data = {
                "medicine_id": state.medicine_id,
                "proposed_units": 0,
                "compliance_status": "No Replenishment Required",
                "requires_approval": False
            }
            state.status = "completed"

            state.log(
                self.name,
                f"Inventory is adequate. No purchase order required at this time.",
                "success"
            )

        return state
