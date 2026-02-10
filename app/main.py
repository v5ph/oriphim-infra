from fastapi import FastAPI, HTTPException
from app.models import ValidationRequest, ValidationResponse
from app.core.entropy import semantic_entropy
from app.core.constraints import check_logic

app = FastAPI(title="Oriphim V-Layer", version="1.0")


@app.post("/v1/validate", response_model=ValidationResponse)
def validate(request: ValidationRequest) -> ValidationResponse:
    entropy_score = semantic_entropy(request.samples)
    violations = check_logic(request)

    if entropy_score > 0.4 or violations:
        raise HTTPException(
            status_code=403,
            detail={
                "status": "Logic Violation",
                "entropy_score": entropy_score,
                "violations": violations,
            },
        )

    return ValidationResponse(
        status="OK",
        entropy_score=entropy_score,
        violations=[],
    )
