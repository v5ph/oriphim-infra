from typing import Optional, Tuple


class PhysicalValidator:
    """
    Hard-constraint validator for physics/finance variables.

    Returns (ok, reason). ok=False means the value violates a hard rule.
    """

    def validate(self, variable: str, value: float) -> Tuple[bool, Optional[str]]:
        var = variable.strip().lower()

        if var in {"temperature", "temp", "kelvin"}:
            if value < 0:
                return False, "Model parameter below minimum bound"

        if var in {"pressure", "pascal", "pa"}:
            if value < 0:
                return False, "Model parameter invalid: negative pressure"

        if var in {"leverage_ratio", "leverage", "debt_to_equity"}:
            if value > 10:
                return False, "Leverage limit breached"

        if var in {"var", "value_at_risk", "proposed_loss"}:
            if value < -10_000:
                return False, "VaR loss limit breached"

        return True, None
