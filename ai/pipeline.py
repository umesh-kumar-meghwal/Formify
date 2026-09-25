import json

from .generators import generate_output
from ai.validator import validate_all  



MAX_ATTEMPTS = 2


def generate_validated_output(
    source_brief,
    output_type,
    tone=None,
    language=None,
    audience=None,
    detail_level=None,
    objective=None,
    style=None,
    max_attempts=MAX_ATTEMPTS,
):
    """
    Generate one output type, validate it with validate_all(),
    and retry if validation fails.

    Returns:
    {
        "output_type": "...",
        "status": "valid" | "needs_review",
        "attempts": int,
        "data": dict | None,          # parsed JSON output for the frontend
        "validation": {...}           # result of validate_all()
    }
    """

   
    if isinstance(source_brief, (dict, list)):
        source_brief_text = json.dumps(
            source_brief, ensure_ascii=False, indent=2
        )
    else:
        source_brief_text = str(source_brief)

    data = None
    validation = {"valid": False, "issues": [], "checks": {}}
    attempt = 0

    for attempt in range(1, max_attempts + 1):
        try:
            response_text = generate_output(
                source_brief=source_brief_text,
                output_type=output_type,
                tone=tone,
                language=language,
                audience=audience,
                detail_level=detail_level,
                objective=objective,
                style=style,
            )

            validation = validate_all(
                response_text=response_text,
                source_brief=source_brief_text,
                expected_output_type=output_type,
                audience=audience,
                tone=tone,
                language=language,
                detail_level=detail_level,
                objective=objective,
                style=style,
            )

            try:
                data = json.loads(response_text)
            except (json.JSONDecodeError, TypeError):
                data = None

        except Exception as e:
            print(f"[{output_type}] Generation or validation failed: {e}")
            data = None
            validation = {
                "valid": False,
                "issues": [f"Generation or validation failed: {e}"],
                "checks": {},
            }

        if validation.get("valid"):
            return {
                "output_type": output_type,
                "status": "valid",
                "attempts": attempt,
                "data": data,
                "validation": validation,
            }

    
    return {
        "output_type": output_type,
        "status": "needs_review",
        "attempts": attempt,
        "data": data,
        "validation": validation,
    }