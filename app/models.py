from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PhysicsPayload(BaseModel):
    energy_in: float = Field(..., ge=0)
    energy_out: float = Field(..., ge=0)


class FinancialPayload(BaseModel):
    proposed_loss: float


class ValidationRequest(BaseModel):
    samples: List[str] = Field(..., min_length=3, max_length=3)
    physics: Optional[PhysicsPayload] = None
    financial: Optional[FinancialPayload] = None
    metrics: Optional[Dict[str, float]] = None
    
    @field_validator('samples')
    @classmethod
    def validate_samples(cls, v: List[str]) -> List[str]:
        if len(v) != 3:
            raise ValueError('samples must contain exactly 3 responses')
        for i, sample in enumerate(v):
            if not sample or not isinstance(sample, str):
                raise ValueError(f'sample[{i}] must be a non-empty string')
        return v


class AgentStateSnapshot(BaseModel):
    system_prompt: str
    context: Dict[str, Any] = Field(default_factory=dict, max_length=100)
    variables: Dict[str, Any] = Field(default_factory=dict, max_length=100)
    
    @field_validator('context', 'variables')
    @classmethod
    def validate_dict_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if len(v) > 100:
            raise ValueError(f'Dictionary cannot exceed 100 keys, got {len(v)}')
        # Prevent deeply nested objects (DoS via JSON parsing)
        import json
        serialized = json.dumps(v)
        if len(serialized) > 1_000_000:  # 1MB limit
            raise ValueError(f'Serialized dict exceeds 1MB limit')
        return v


class AgentIntentRequest(BaseModel):
    tenant_id: Optional[str] = Field(default=None, min_length=1, max_length=128)
    agent_id: str
    intent: str
    desired_state: Optional[str] = None
    samples: List[str] = Field(..., min_length=3, max_length=3)
    physics: Optional[PhysicsPayload] = None
    financial: Optional[FinancialPayload] = None
    metrics: Optional[Dict[str, float]] = None
    chain_of_thought: Optional[List[str]] = None
    state_snapshot: Optional[AgentStateSnapshot] = None
    
    @field_validator('samples')
    @classmethod
    def validate_samples(cls, v: List[str]) -> List[str]:
        if len(v) != 3:
            raise ValueError('samples must contain exactly 3 responses')
        for i, sample in enumerate(v):
            if not sample or not isinstance(sample, str):
                raise ValueError(f'sample[{i}] must be a non-empty string')
        return v


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


class TradeOrder(BaseModel):
    order_id: Optional[str] = None
    symbol: str = Field(..., min_length=1, max_length=32)
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    market_price: Optional[float] = Field(default=None, gt=0)
    market_price_timestamp: Optional[datetime] = None
    leverage_ratio: float = Field(default=1.0, ge=1.0, le=100.0)


class AccountSnapshot(BaseModel):
    capital: float = Field(..., gt=0)
    daily_pnl: float = Field(default=0.0)
    open_positions: Dict[str, float] = Field(default_factory=dict)
    pending_orders: Dict[str, float] = Field(default_factory=dict)
    unsettled_positions: Dict[str, float] = Field(default_factory=dict)
    unsettled_notional: float = Field(default=0.0, ge=0.0)
    current_gross_exposure: float = Field(default=0.0, ge=0.0)
    orders_last_minute: int = Field(default=0, ge=0)
    avg_order_size: float = Field(default=0.0, ge=0.0)
    order_size_stddev: float = Field(default=0.0, ge=0.0)
    as_of: Optional[datetime] = None


class TradePolicyConfig(BaseModel):
    policy_version: str = Field(default="default", min_length=1, max_length=128)
    max_daily_loss: float = Field(default=50000.0, gt=0)
    max_position_size: float = Field(default=1000.0, gt=0)
    max_leverage_ratio: float = Field(default=5.0, ge=1.0)
    max_orders_per_minute: int = Field(default=30, ge=1)
    abnormal_order_zscore: float = Field(default=3.0, ge=1.0)
    max_capital_allocation_pct: float = Field(default=0.25, gt=0.0, le=1.0)
    min_lot_size: float = Field(default=0.0001, gt=0)
    tick_size: Optional[float] = Field(default=None, gt=0)
    max_market_price_age_seconds: int = Field(default=30, ge=1)
    restricted_instruments: List[str] = Field(default_factory=list)
    kill_switch_enabled: bool = Field(default=False)


class PreTradeRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    agent_id: Optional[str] = Field(default=None, min_length=1, max_length=128)
    order: TradeOrder
    account: AccountSnapshot
    policy: TradePolicyConfig


class PreTradeResponse(BaseModel):
    decision_id: str
    decision: str
    reason: str
    triggered_controls: List[str]
    modified_order: Optional[TradeOrder] = None
    created_at: str


class SimulationEvent(BaseModel):
    timestamp: str
    symbol: str = Field(..., min_length=1, max_length=32)
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    expected_pnl: float = Field(default=0.0)
    leverage_ratio: float = Field(default=1.0, ge=1.0, le=100.0)
    drift_score: Optional[float] = Field(default=None, ge=0.0)
    anomaly_score: Optional[float] = Field(default=None, ge=0.0)


class SimulationRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    strategy_name: str = Field(..., min_length=1, max_length=128)
    initial_capital: float = Field(..., gt=0)
    max_drawdown_pct: float = Field(default=0.15, gt=0.0, le=1.0)
    policy: TradePolicyConfig
    events: List[SimulationEvent] = Field(..., min_length=1, max_length=5000)


class SimulationSummary(BaseModel):
    total_events: int
    allowed_count: int
    modified_count: int
    review_count: int
    blocked_count: int
    final_capital: float
    max_drawdown_pct_observed: float
    drawdown_breach: bool
    drift_flags: int
    anomaly_flags: int


class SimulationResponse(BaseModel):
    simulation_id: str
    tenant_id: str
    strategy_name: str
    summary: SimulationSummary
    policy_blocks: List[str]
    created_at: str
