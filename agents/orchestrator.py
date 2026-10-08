import logging
from typing import Optional
from agents.state import AgentWorkflowState
from agents.inventory_agent import InventoryAnalystAgent
from agents.demand_agent import DemandForecasterAgent
from agents.restock_agent import RestockOptimizationAgent
from agents.procurement_agent import ProcurementComplianceAgent
from database.connection import get_db
from database.models import Medicine

logger = logging.getLogger(__name__)


class HealthSupplyAgentOrchestrator:
    """
    Multi-Agent Workflow Orchestrator:
    User Trigger
      ↓
    1. Inventory Analyst Agent (Scans stock, trends, expiry)
      ↓
    2. Demand Forecaster Agent (ML Random Forest prediction, MAE/RMSE)
      ↓
    3. Restock Optimization Agent (Calculates replenish qty & priority)
      ↓
    4. Procurement / Compliance Agent (Generates PO proposal)
      ↓
    Human Pharmacist Approval (Approve / Edit / Reject)
      ↓
    Database Update
    """
    def __init__(self):
        self.inventory_agent = InventoryAnalystAgent()
        self.demand_agent = DemandForecasterAgent()
        self.restock_agent = RestockOptimizationAgent()
        self.procurement_agent = ProcurementComplianceAgent()

    def run_workflow_for_medicine(self, medicine_id: int, forecast_period: int = 7) -> AgentWorkflowState:
        """Runs the complete 4-agent sequential workflow for a specific medicine."""
        state = AgentWorkflowState(medicine_id=medicine_id, forecast_period=forecast_period)

        logger.info(f"Starting Multi-Agent Workflow for Medicine ID {medicine_id}...")

        # Step 1: Inventory Analyst Agent
        state = self.inventory_agent.run(state)
        if state.status == "error":
            return state

        # Step 2: Demand Forecaster Agent
        state = self.demand_agent.run(state)
        if state.status == "error":
            return state

        # Step 3: Restock Optimization Agent
        state = self.restock_agent.run(state)
        if state.status == "error":
            return state

        # Step 4: Procurement & Compliance Agent
        state = self.procurement_agent.run(state)

        logger.info(f"Multi-Agent Workflow complete for Medicine ID {medicine_id}. State: {state.status}")
        return state

    def run_catalog_scan(self, forecast_period: int = 7) -> list[AgentWorkflowState]:
        """Runs the multi-agent analysis for all medicines currently in catalog."""
        with get_db() as session:
            med_ids = [m.medicine_id for m in session.query(Medicine.medicine_id).all()]

        results = []
        for mid in med_ids:
            st = self.run_workflow_for_medicine(mid, forecast_period)
            results.append(st)
        return results


# Global orchestrator instance
orchestrator = HealthSupplyAgentOrchestrator()
