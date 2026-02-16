from typing import List, Protocol
from app.models import ValidationRequest


class _RequestLike(Protocol):
    physics: object | None
    financial: object | None
    metrics: object | None
from app.core.physical_validator import PhysicalValidator


LOSS_THRESHOLD = 10_000.0


def check_logic(request: ValidationRequest | _RequestLike) -> List[str]:
    violations: List[str] = []
    validator = PhysicalValidator()

    if request.physics is not None:
        if request.physics.energy_out > request.physics.energy_in:
            violations.append("Conservation of Energy violated")
        ok, reason = validator.validate("temperature", request.physics.energy_in)
        if not ok and reason:
            violations.append(reason)

    if request.financial is not None:
        if request.financial.proposed_loss < -LOSS_THRESHOLD:
            violations.append("VaR loss threshold exceeded")
        ok, reason = validator.validate("proposed_loss", request.financial.proposed_loss)
        if not ok and reason:
            violations.append(reason)

    if request.metrics:
        for name, value in request.metrics.items():
            ok, reason = validator.validate(name, value)
            if not ok and reason:
                violations.append(reason)

    return violations
