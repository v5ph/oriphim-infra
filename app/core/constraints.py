from typing import List
from app.models import ValidationRequest


LOSS_THRESHOLD = 10_000.0


def check_logic(request: ValidationRequest) -> List[str]:
    violations: List[str] = []

    if request.physics is not None:
        if request.physics.energy_out > request.physics.energy_in:
            violations.append("Conservation of Energy violated")

    if request.financial is not None:
        if request.financial.proposed_loss < -LOSS_THRESHOLD:
            violations.append("VaR loss threshold exceeded")

    return violations
