from typing import List, Optional
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


class ValidationResponse(BaseModel):
    status: str
    entropy_score: float
    violations: List[str]
