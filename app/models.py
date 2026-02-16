from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PhysicsPayload(BaseModel):
    energy_in: float = Field(..., ge=0)
    energy_out: float = Field(..., ge=0)


class FinancialPayload(BaseModel):
    proposed_loss: float


class ValidationRequest(BaseModel):
    samples: List[str]
    physics: Optional[PhysicsPayload] = None
    financial: Optional[FinancialPayload] = None
    metrics: Optional[Dict[str, float]] = None


class AgentStateSnapshot(BaseModel):
    system_prompt: str
    context: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)


class AgentIntentRequest(BaseModel):
    agent_id: str
    intent: str
    desired_state: Optional[str] = None
    samples: List[str]
    physics: Optional[PhysicsPayload] = None
    financial: Optional[FinancialPayload] = None
    metrics: Optional[Dict[str, float]] = None
    chain_of_thought: Optional[List[str]] = None
    state_snapshot: Optional[AgentStateSnapshot] = None


class ValidationResponse(BaseModel):
    status: str
    entropy_score: float
    violations: List[str]


class IntentAck(BaseModel):
    request_id: str
    status: str
    received_at: str


class ParallelValidationStatus(BaseModel):
    request_id: str
    status_code: int
    action: str
    divergence_score: float
    violations: List[str]
    recommendation: str
    context_reset: bool
    latency_ms: float
    created_at: str


class RewindResponse(BaseModel):
    agent_id: str
    snapshot_id: Optional[int]
    restored: bool
    restored_at: Optional[str]
    system_prompt: Optional[str]
    context: Optional[Dict[str, Any]]
    variables: Optional[Dict[str, Any]]


class ComplianceExportResponse(BaseModel):
    agent_id: Optional[str]
    export_id: str
