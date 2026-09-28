import json
import re

from ai.gemini_client import generate_with_gemini


def _parse_json(text):
    """Parse JSON even if the model wraps it in ```json fences."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def create_source_brief(source_text):

    prompt = f"""
You are the source analysis module of Formify.

Analyze the provided source and return a structured Source Brief.

SOURCE:
{source_text}

Return ONLY valid JSON with this structure:

{{
    "title": "",
    "source_type": "",
    "primary_language": "",
    "domain": "",
    "core_summary": "",
    "key_facts": [],
    "risks": [],
    "recommended_actions": [],
    "entities": [],
    "limitations_or_unknowns": []
}}

Rules:
- Use only information supported by the source.
- Do not invent facts, names, dates, statistics, or details.
- If information is missing, keep the relevant field empty.
- Preserve the meaning of the source.
"""

    response_text = generate_with_gemini(prompt)

    return _parse_json(response_text)