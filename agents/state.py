from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class AgentLogEntry:
    agent: str
    action: str
    status: str  # "success", "warning", "info", "error"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "action": self.action,
            "status": self.status,
            "timestamp": self.timestamp
        }


@dataclass
class AgentWorkflowState:
    medicine_id: int
    forecast_period: int = 7
    inventory_data: dict = field(default_factory=dict)
    forecast_data: dict = field(default_factory=dict)
    restock_data: dict = field(default_factory=dict)
    proposal_data: dict = field(default_factory=dict)
    status: str = "initialized"  # "initialized", "analyzing", "awaiting_approval", "completed", "rejected"
    activity_logs: list[AgentLogEntry] = field(default_factory=list)

    def log(self, agent: str, action: str, status: str = "success"):
        self.activity_logs.append(AgentLogEntry(agent=agent, action=action, status=status))

    def to_dict(self) -> dict:
        return {
            "medicine_id": self.medicine_id,
            "forecast_period": self.forecast_period,
            "inventory_data": self.inventory_data,
            "forecast_data": self.forecast_data,
            "restock_data": self.restock_data,
            "proposal_data": self.proposal_data,
            "status": self.status,
            "activity_logs": [log.to_dict() for log in self.activity_logs]
        }
