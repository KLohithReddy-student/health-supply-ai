import logging
from agents.state import AgentWorkflowState
from services.restock_service import RestockService

logger = logging.getLogger(__name__)


class RestockOptimizationAgent:
    """
    Agent 3: Restock Optimization Agent
    - Uses predicted demand + current stock + reorder level
    - Considers safety stock and supplier lead time
    - Calculates recommended restocking quantity using:
      Recommended Restock = max(0, Predicted Demand + Safety Stock - Current Stock)
    - Assigns priority and explainable rationale
    """
    def __init__(self):
        self.name = "Restock Optimization Agent"

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if state.status == "error":
            return state

        # Use the RestockService calculation logic
        restock_calc = RestockService.calculate_restock_requirements(
            medicine_id=state.medicine_id,
            forecast_days=state.forecast_period
        )

        state.restock_data = restock_calc

        # User-facing concise activity log
        log_status = (
            "warning" if restock_calc["priority"] in ["Critical", "High"]
            else ("info" if restock_calc["recommended_quantity"] > 0 else "success")
        )

        state.log(
            self.name,
            f"Calculated replenishment ({restock_calc['recommended_quantity']} units, Priority: {restock_calc['priority']}) via: {restock_calc['formula_breakdown']}",
            log_status
        )
        return state
