import json

from .generators import generate_output
from .validator import validate_all  # <-- apni validation file ka naam yahan match karo


# Ek output ke liye kitni baar generate + validate try karna hai.
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