from typing import Callable, TypeVar, Any
from app.core.constraints import check_logic
from app.core.entropy import hallucination_divergence
from app.models import ValidationRequest

T = TypeVar("T")


def constraint_wrapper(func: Callable[..., T]) -> Callable[..., T]:
    def _inner(*args: Any, **kwargs: Any) -> T:
        result: T = func(*args, **kwargs)

        request: ValidationRequest = kwargs.get("validation_request")
        if request is None:
            return result

        entropy_score = hallucination_divergence(request.samples)
        violations = check_logic(request)

        if entropy_score > 0.4 or violations:
            raise ValueError(
                {
                    "status": "Logic Violation",
                    "entropy_score": entropy_score,
                    "violations": violations,
                }
            )

        return result

    return _inner
