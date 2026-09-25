"""
Connects the Formify frontend (transform.html / transform.js) with the
backend pipeline without changing either side.

- Frontend output keys  -> backend output types
- Frontend setting values -> readable labels for the prompts
- Backend JSON output   -> {type, title, content, grounded, evidence}
  which is exactly what transform.js renders.
"""

# =========================================================
# OUTPUT TYPE MAPPING  (frontend data-output -> backend type)
# =========================================================

OUTPUT_TYPE_MAP = {
    "executive-summary": "executive_summary",
    "technical-advisory": "advisory",
    "linkedin-post": "linkedin_post",
    "x-post": "twitter_x_post",
    "infographic": "infographic",
    "presentation": "presentation",
    "incident-report": "incident_report",
}

OUTPUT_TITLES = {
    "executive-summary": "Executive Summary",
    "technical-advisory": "Technical Advisory",
    "linkedin-post": "LinkedIn Post",
    "x-post": "X Post",
    "infographic": "Infographic",
    "presentation": "Presentation",
    "incident-report": "Incident Report",
}


def to_backend_type(frontend_type):
    return OUTPUT_TYPE_MAP.get(frontend_type)


# =========================================================
# SETTING LABELS  (dropdown value -> readable text)
# =========================================================

SETTING_LABELS = {
    "audience": {
        "security-leadership": "Government & Security Leadership",
        "soc-teams": "Cybersecurity / SOC Teams",
        "field-teams": "Incident Response / Field Teams",
        "policy-stakeholders": "Government / Policy Stakeholders",
        "media": "Media & Journalists",
        "general-public": "General Public",
        "employees": "Employees / Internal Staff",
    },
    "language": {
        "english": "English",
        "hindi": "Hindi (Devanagari script)",
        "hinglish": "Hinglish (Hindi and English mixed, written in Roman script)",
    },
    "objective": {
        "inform": "Inform",
        "awareness": "Raise awareness",
        "action": "Drive action",
        "warn": "Warn / alert",
        "persuade": "Persuade",
        "trust": "Build trust",
    },
    "style": {
        "clear": "Clear and direct",
        "storytelling": "Storytelling",
        "data-driven": "Data-driven",
        "conversational": "Conversational",
        "formal": "Formal",
    },
}


def setting_label(kind, value):
    if not value:
        return None

    labels = SETTING_LABELS.get(kind, {})

    return labels.get(value, value.replace("-", " ").capitalize())


# =========================================================
# BACKEND JSON -> READABLE TEXT
# =========================================================

def _label(key):
    return str(key).replace("_", " ").title()


def _is_scalar(value):
    return not isinstance(value, (dict, list))


def _render_value(value, indent=0):
    pad = "  " * indent
    lines = []

    if isinstance(value, dict):
        for key, item in value.items():
            if _is_scalar(item):
                if item in ("", None):
                    continue
                lines.append(f"{pad}{_label(key)}: {item}")
            else:
                sub = _render_value(item, indent + 1)
                if sub:
                    lines.append(f"{pad}{_label(key)}:")
                    lines.extend(sub)

    elif isinstance(value, list):
        for item in value:
            if _is_scalar(item):
                lines.append(f"{pad}- {item}")
            else:
                sub = _render_value(item, indent + 1)
                if sub:
                    lines.extend(sub)
                    lines.append("")

    return lines


def format_content(data):
    lines = []

    title = data.get("title")
    if title:
        lines.extend([str(title), ""])

    for key, value in data.items():
        if key in ("output_type", "title"):
            continue

        if _is_scalar(value):
            if value in ("", None):
                continue
            lines.extend([_label(key).upper(), str(value), ""])
        else:
            body = _render_value(value)
            if body:
                lines.append(_label(key).upper())
                lines.extend(body)
                lines.append("")

    return "\n".join(lines).strip()


# =========================================================
# BUILD ONE FRONTEND OUTPUT OBJECT
# =========================================================

def build_frontend_output(frontend_type, result):
    """
    result = return value of generate_validated_output()
    """

    data = result.get("data")
    validation = result.get("validation") or {}
    checks = validation.get("checks") or {}
    issues = validation.get("issues") or []

    if isinstance(data, dict):
        content = format_content(data)
    else:
        content = "This output could not be generated. Please try again."

    evidence = ""
    if issues:
        evidence = "Validation notes: " + " • ".join(str(i) for i in issues)

    return {
        "type": frontend_type,
        "title": OUTPUT_TITLES.get(frontend_type, frontend_type),
        "content": content,
        "grounded": bool(checks.get("source_grounding")),
        "evidence": evidence,
        "status": result.get("status"),
        "data": data,
    }


def build_unsupported_output(frontend_type):
    return {
        "type": frontend_type,
        "title": OUTPUT_TITLES.get(frontend_type, frontend_type),
        "content": "This output type is not supported yet.",
        "grounded": False,
        "evidence": "",
        "status": "unsupported",
        "data": None,
    }