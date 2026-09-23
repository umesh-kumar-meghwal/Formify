from .gemini_client import generate_with_gemini

from .prompts import (
    MASTER_SYSTEM_RULES,
    SOURCE_GROUNDING_RULES,
    OPERATOR_SETTINGS_RULES,
    MISSING_INFORMATION_RULES,
    OUTPUT_JSON_RULES,
    EXECUTIVE_SUMMARY_PROMPT,
    ADVISORY_PROMPT,
    LINKEDIN_POST_PROMPT,
    TWITTER_X_POST_PROMPT,
    PRESENTATION_PROMPT,
    INFOGRAPHIC_PROMPT,
    VIDEO_PACKAGE_PROMPT,
)


# =========================================================
# OUTPUT PROMPT MAP
# =========================================================

PROMPT_MAP = {
    "executive_summary": EXECUTIVE_SUMMARY_PROMPT,
    "advisory": ADVISORY_PROMPT,
    "linkedin_post": LINKEDIN_POST_PROMPT,
    "twitter_x_post": TWITTER_X_POST_PROMPT,
    "presentation": PRESENTATION_PROMPT,
    "infographic": INFOGRAPHIC_PROMPT,
    "video_package": VIDEO_PACKAGE_PROMPT,
}


# =========================================================
# BUILD GENERATION PROMPT
# =========================================================

def build_prompt(
    source_brief,
    output_type,
    tone=None,
    language=None,
    audience=None,
    detail_level=None,
    objective=None,
    style=None,
):
    if output_type not in PROMPT_MAP:
        raise ValueError(
            f"Unsupported output type: {output_type}"
        )

    output_prompt = PROMPT_MAP[output_type]

    prompt = f"""
{MASTER_SYSTEM_RULES}

{SOURCE_GROUNDING_RULES}

{OPERATOR_SETTINGS_RULES}

{MISSING_INFORMATION_RULES}

{OUTPUT_JSON_RULES}

SOURCE BRIEF:
{source_brief}

OPERATOR SETTINGS:
Target Audience: {audience or "Not specified"}
Tone: {tone or "Not specified"}
Language: {language or "English"}
Detail Level: {detail_level or "Not specified"}
Communication Objective: {objective or "Not specified"}
Content Style: {style or "Not specified"}

OUTPUT-SPECIFIC INSTRUCTIONS:
{output_prompt}
"""

    return prompt


# =========================================================
# GENERATE OUTPUT
# =========================================================

def generate_output(
    source_brief,
    output_type,
    tone=None,
    language=None,
    audience=None,
    detail_level=None,
    objective=None,
    style=None,
):
    prompt = build_prompt(
        source_brief=source_brief,
        output_type=output_type,
        tone=tone,
        language=language,
        audience=audience,
        detail_level=detail_level,
        objective=objective,
        style=style,
    )

    response = generate_with_gemini(prompt)

    return response