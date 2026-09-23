from ai.gemini_client import client, MODEL_NAME
import json

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

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return json.loads(response.text)