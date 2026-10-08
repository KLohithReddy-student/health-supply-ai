import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from agents.orchestrator import orchestrator
from agents.state import AgentWorkflowState
from services.restock_service import RestockService
from services.inventory_service import InventoryService


def test_agent_workflow_execution():
    # 1. Run full workflow for medicine ID 1
    state = orchestrator.run_workflow_for_medicine(medicine_id=1, forecast_period=7)

    # 2. Check workflow state
    assert state.medicine_id == 1
    assert "stock_status" in state.inventory_data
    assert "total_predicted_demand" in state.forecast_data
    assert "recommended_quantity" in state.restock_data
    assert "requires_approval" in state.proposal_data

    # 3. Check activity logs
    assert len(state.activity_logs) == 4, f"Expected 4 agent log entries, got {len(state.activity_logs)}"
    agent_names = [log.agent for log in state.activity_logs]
    assert "Inventory Analyst Agent" in agent_names
    assert "Demand Forecaster Agent" in agent_names
    assert "Restock Optimization Agent" in agent_names
    assert "Procurement & Compliance Agent" in agent_names

    print("✓ test_agent_workflow_execution PASSED (All 4 agents executed in sequence)")


def test_human_approval_lifecycle():
    # 1. Run workflow to generate a pending proposal
    state = orchestrator.run_workflow_for_medicine(medicine_id=2, forecast_period=7)
    rec_id = state.proposal_data.get("recommendation_id")

    if rec_id:
        # Test Edit and Approve
        orig_med = InventoryService.get_medicine_by_id(2)
        initial_stock = orig_med["current_stock"]

        success = RestockService.approve_recommendation(
            recommendation_id=rec_id,
            approved_qty=50,
            fulfill_immediately=True
        )
        assert success is True, "Approval should succeed"

        updated_med = InventoryService.get_medicine_by_id(2)
        assert updated_med["current_stock"] == initial_stock + 50, "Stock should increment by approved 50 units"

    print("✓ test_human_approval_lifecycle PASSED (HITL Edit & Approval confirmed)")


if __name__ == "__main__":
    test_agent_workflow_execution()
    test_human_approval_lifecycle()
