import json

from .gemini_client import generate_with_gemini


# =========================================================
# TOP-LEVEL OUTPUT SCHEMAS
# =========================================================

OUTPUT_SCHEMAS = {
    "executive_summary": {
        "output_type",
        "title",
        "overview",
        "key_findings",
        "main_risks",
        "recommended_actions",
    },

    "advisory": {
        "output_type",
        "title",
        "purpose",
        "situation",
        "key_information",
        "risks_or_considerations",
        "recommended_actions",
        "limitations_or_unknowns",
    },

    "linkedin_post": {
        "output_type",
        "title",
        "opening",
        "body_sections",
        "call_to_action",
        "hashtags",
    },

    "twitter_x_post": {
        "output_type",
        "title",
        "format",
        "posts",
        "hashtags",
    },

    "presentation": {
        "output_type",
        "title",
        "slides",
    },

    "infographic": {
        "output_type",
        "title",
        "subtitle",
        "key_messages",
        "sections",
        "overall_layout",
        "footer",
    },

    "video_package": {
        "output_type",
        "title",
        "description",
        "total_duration",
        "script",
        "storyboard",
    },
        "incident_report": {
        "output_type",
        "title",
        "summary",
        "incident_details",
        "timeline",
        "affected_systems_or_entities",
        "impact",
        "response_actions_taken",
        "recommendations",
        "unresolved_or_unknown",
    },
}


# =========================================================
# FIELD DATA TYPES
# =========================================================

FIELD_TYPES = {
    "executive_summary": {
        "title": str,
        "overview": str,
        "key_findings": list,
        "main_risks": list,
        "recommended_actions": list,
    },

    "advisory": {
        "title": str,
        "purpose": str,
        "situation": str,
        "key_information": list,
        "risks_or_considerations": list,
        "recommended_actions": list,
        "limitations_or_unknowns": list,
    },

    "linkedin_post": {
        "title": str,
        "opening": str,
        "body_sections": list,
        "call_to_action": str,
        "hashtags": list,
    },

    "twitter_x_post": {
        "title": str,
        "format": str,
        "posts": list,
        "hashtags": list,
    },

    "presentation": {
        "title": str,
        "slides": list,
    },

    "infographic": {
        "title": str,
        "subtitle": str,
        "key_messages": list,
        "sections": list,
        "overall_layout": str,
        "footer": str,
    },

    "video_package": {
        "title": str,
        "description": str,
        "total_duration": str,
        "script": str,
        "storyboard": list,
    },
        "incident_report": {
        "title": str,
        "summary": str,
        "incident_details": str,
        "timeline": list,
        "affected_systems_or_entities": list,
        "impact": str,
        "response_actions_taken": list,
        "recommendations": list,
        "unresolved_or_unknown": list,
    },
}



OPTIONAL_EMPTY_FIELDS = {
    "executive_summary": {"main_risks", "recommended_actions"},
    "advisory": {
        "risks_or_considerations",
        "recommended_actions",
        "limitations_or_unknowns",
    },
    "linkedin_post": {"call_to_action", "hashtags"},
    "twitter_x_post": {"hashtags"},
    "presentation": set(),
    "infographic": {"subtitle", "footer"},
    "video_package": set(),
}


# =========================================================
# NESTED SCHEMAS
# =========================================================

NESTED_SCHEMAS = {
    "presentation": {
        "slides": {
            "required_fields": {
                "slide_number": int,
                "title": str,
                "content": list,
                "speaker_notes": str,
            }
        }
    },

    "twitter_x_post": {
        "posts": {
            "required_fields": {
                "position": int,
                "content": str,
            }
        }
    },

    "infographic": {
        "sections": {
            "required_fields": {
                "section_number": int,
                "heading": str,
                "content": list,
                "key_message": str,
                "visual_type": str,
                "visual_data": list,
                "layout_recommendation": str,
            }
        }
    },

    "video_package": {
        "storyboard": {
            "required_fields": {
                "scene_number": int,
                "scene_title": str,
                "purpose": str,
                "duration": str,
                "narration": str,
                "on_screen_text": list,
                "subtitles": str,
                "visual_description": str,
                "visual_recommendations": list,
                "transition": str,
            }
        }
    },
}


# =========================================================
# JSON PARSING
# =========================================================

def parse_json_response(response_text):
    """
    Parse Gemini's generated response into a Python dictionary.
    """

    if not response_text:
        return {
            "valid": False,
            "data": None,
            "issues": ["Empty response received."],
        }

    try:
        data = json.loads(response_text)

        if not isinstance(data, dict):
            return {
                "valid": False,
                "data": None,
                "issues": ["Response must be a JSON object."],
            }

        return {
            "valid": True,
            "data": data,
            "issues": [],
        }

    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "data": None,
            "issues": [f"Invalid JSON: {str(e)}"],
        }


# =========================================================
# TOP-LEVEL STRUCTURE VALIDATION
# =========================================================

def validate_structure(data, expected_output_type):
    """
    Validate output type and required top-level fields.
    """

    issues = []

    if expected_output_type not in OUTPUT_SCHEMAS:
        return {
            "valid": False,
            "issues": [
                f"Unsupported output type: {expected_output_type}"
            ],
        }

    expected_fields = OUTPUT_SCHEMAS[expected_output_type]

    actual_output_type = data.get("output_type")

    if actual_output_type != expected_output_type:
        issues.append(
            f"Incorrect output_type. Expected "
            f"'{expected_output_type}', received "
            f"'{actual_output_type}'."
        )

    missing_fields = expected_fields - set(data.keys())

    if missing_fields:
        issues.append(
            "Missing required fields: "
            + ", ".join(sorted(missing_fields))
        )

    extra_fields = set(data.keys()) - expected_fields

    if extra_fields:
        issues.append(
            "Unexpected fields: "
            + ", ".join(sorted(extra_fields))
        )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


# =========================================================
# FIELD TYPE + EMPTY CONTENT VALIDATION
# =========================================================

def validate_field_types(data, output_type):
    """
    Validate field data types and detect empty required content.

    Fields listed in OPTIONAL_EMPTY_FIELDS for this output_type are
    allowed to be an empty string/list -- the prompt itself tells the
    model to leave them empty when the source doesn't support them, so
    an empty value there is a correct answer, not a validation failure.
    """

    issues = []

    expected_fields = FIELD_TYPES.get(output_type, {})
    optional_fields = OPTIONAL_EMPTY_FIELDS.get(output_type, set())

    for field, expected_type in expected_fields.items():

        if field not in data:
            continue

        value = data[field]

        if value is None:
            issues.append(
                f"Field '{field}' cannot be null."
            )
            continue

        if not isinstance(value, expected_type):
            issues.append(
                f"Field '{field}' must be of type "
                f"{expected_type.__name__}."
            )
            continue

        if field in optional_fields:
            continue

        if isinstance(value, str) and not value.strip():
            issues.append(
                f"Field '{field}' cannot be empty."
            )

        elif isinstance(value, list) and len(value) == 0:
            issues.append(
                f"Field '{field}' cannot be an empty list."
            )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


# =========================================================
# NESTED STRUCTURE VALIDATION
# =========================================================

def validate_nested_structure(data, output_type):
    """
    Validate the structure of nested objects inside generated output.
    """

    issues = []

    schema = NESTED_SCHEMAS.get(output_type, {})

    for list_field, config in schema.items():

        items = data.get(list_field)

        if not isinstance(items, list):
            continue

        required_fields = config["required_fields"]

        for index, item in enumerate(items, start=1):

            if not isinstance(item, dict):
                issues.append(
                    f"Item {index} in '{list_field}' "
                    f"must be an object."
                )
                continue

            missing_fields = (
                set(required_fields.keys()) - set(item.keys())
            )

            if missing_fields:
                issues.append(
                    f"Item {index} in '{list_field}' is missing: "
                    + ", ".join(sorted(missing_fields))
                )

            extra_fields = (
                set(item.keys()) - set(required_fields.keys())
            )

            if extra_fields:
                issues.append(
                    f"Item {index} in '{list_field}' "
                    f"has unexpected fields: "
                    + ", ".join(sorted(extra_fields))
                )

            for field, expected_type in required_fields.items():

                if field not in item:
                    continue

                value = item[field]

                if value is None:
                    issues.append(
                        f"Item {index} in '{list_field}', "
                        f"field '{field}' cannot be null."
                    )
                    continue

                if not isinstance(value, expected_type):
                    issues.append(
                        f"Item {index} in '{list_field}', "
                        f"field '{field}' must be "
                        f"{expected_type.__name__}."
                    )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


# =========================================================
# SEQUENCE + OUTPUT-SPECIFIC CONSISTENCY
# =========================================================

def validate_sequence(data, output_type):
    """
    Validate sequential numbering and output-specific consistency rules.
    """

    issues = []

    if output_type == "presentation":

        slides = data.get("slides", [])

        numbers = [
            slide.get("slide_number")
            for slide in slides
            if isinstance(slide, dict)
        ]

        expected = list(range(1, len(numbers) + 1))

        if numbers != expected:
            issues.append(
                "Presentation slide numbers must be sequential "
                "starting from 1."
            )

    elif output_type == "twitter_x_post":

        posts = data.get("posts", [])

        positions = [
            post.get("position")
            for post in posts
            if isinstance(post, dict)
        ]

        expected = list(range(1, len(positions) + 1))

        if positions != expected:
            issues.append(
                "X post positions must be sequential "
                "starting from 1."
            )

        post_format = data.get("format")

        if post_format not in {"single_post", "thread"}:
            issues.append(
                "Twitter/X format must be "
                "'single_post' or 'thread'."
            )

        if post_format == "single_post" and len(posts) != 1:
            issues.append(
                "A single_post must contain exactly one post."
            )

        if post_format == "thread" and len(posts) < 2:
            issues.append(
                "A thread must contain at least two posts."
            )

    elif output_type == "infographic":

        sections = data.get("sections", [])

        numbers = [
            section.get("section_number")
            for section in sections
            if isinstance(section, dict)
        ]

        expected = list(range(1, len(numbers) + 1))

        if numbers != expected:
            issues.append(
                "Infographic section numbers must be sequential "
                "starting from 1."
            )

    elif output_type == "video_package":

        storyboard = data.get("storyboard", [])

        numbers = [
            scene.get("scene_number")
            for scene in storyboard
            if isinstance(scene, dict)
        ]

        expected = list(range(1, len(numbers) + 1))

        if numbers != expected:
            issues.append(
                "Video scene numbers must be sequential "
                "starting from 1."
            )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }




GROUNDING_VALIDATION_PROMPT = """
You are the validation engine for Formify.

Your task is to verify whether the generated output is factually grounded
in the provided Source Brief.

SOURCE BRIEF:
{source_brief}

GENERATED OUTPUT:
{generated_output}

Check the generated output for:

1. Unsupported factual claims.
2. Hallucinated or fabricated information.
3. Fabricated names, dates, numbers, statistics, quotes, events, or entities.
4. Claims that contradict the Source Brief.
5. Changes in the meaning of the source.
6. Important limitations or uncertainties from the source being incorrectly
   presented as certain facts.
7. Recommendations being presented as established facts.
8. Missing information being guessed or filled with unsupported information.
9. Information outside the factual scope of the Source Brief.

Return ONLY valid JSON using exactly this structure:

{{
    "valid": true,
    "issues": [],
    "unsupported_claims": [],
    "contradictions": [],
    "missing_or_distorted_information": []
}}

Rules:

- "valid" must be false if any significant unsupported claim,
  hallucination, contradiction, or factual distortion is found.
- Do not flag stylistic differences as factual errors.
- Do not require the generated output to copy the Source Brief word-for-word.
- Faithful paraphrasing is allowed.
- If a claim is supported by the Source Brief, do not flag it.
- If information is genuinely unavailable, do not assume it.
- Return valid JSON only.
"""

def validate_source_grounding(source_brief, generated_output):
    """
    Use Gemini to verify the generated output against the Source Brief.
    """

    prompt = GROUNDING_VALIDATION_PROMPT.format(
        source_brief=source_brief,
        generated_output=generated_output,
    )

    response = generate_with_gemini(prompt)

    parsed = parse_json_response(response)

    if not parsed["valid"]:
        return {
            "valid": False,
            "issues": parsed["issues"],
            "unsupported_claims": [],
            "contradictions": [],
            "missing_or_distorted_information": [],
        }

    return parsed["data"]


# =========================================================
# OPERATOR SETTINGS VALIDATION
# =========================================================
#
# Same fix applied here: JSON example braces escaped as {{ / }}.

OPERATOR_SETTINGS_VALIDATION_PROMPT = """
You are the validation engine for Formify.

Your task is to verify whether the generated output follows the
operator's requested settings.

OPERATOR SETTINGS:

Target Audience:
{audience}

Tone:
{tone}

Language:
{language}

Detail Level:
{detail_level}

Communication Objective:
{objective}

Content Style:
{style}

GENERATED OUTPUT:
{generated_output}

Check whether the generated output appropriately follows every
operator setting that was actually provided.

Rules:

1. If a setting is "Not specified", do not treat it as a failure.
2. Check the requested language.
3. Check whether the tone matches the requested tone.
4. Check whether the content is appropriate for the target audience.
5. Check whether the level of detail is appropriate.
6. Check whether the communication objective is satisfied.
7. Check whether the requested content style is followed.
8. Do not treat factual differences from the settings as errors when
   the source does not support the requested content.
9. Operator settings must never override source-grounding requirements.
10. Do not flag minor stylistic differences unless they meaningfully
    violate the requested setting.

Return ONLY valid JSON using exactly this structure:

{{
    "valid": true,
    "issues": [],
    "setting_violations": []
}}

Rules for the result:

- "valid" must be false if one or more provided operator settings are
  meaningfully violated.
- "issues" contains concise explanations of the problems.
- "setting_violations" identifies which settings were not followed.
- Return valid JSON only.
"""

def validate_operator_settings_with_ai(
    generated_output,
    audience=None,
    tone=None,
    language=None,
    detail_level=None,
    objective=None,
    style=None,
):
    """
    Use Gemini to verify whether the generated output follows
    the provided operator settings.
    """

    prompt = OPERATOR_SETTINGS_VALIDATION_PROMPT.format(
        audience=audience or "Not specified",
        tone=tone or "Not specified",
        language=language or "Not specified",
        detail_level=detail_level or "Not specified",
        objective=objective or "Not specified",
        style=style or "Not specified",
        generated_output=generated_output,
    )

    response = generate_with_gemini(prompt)

    parsed = parse_json_response(response)

    if not parsed["valid"]:
        return {
            "valid": False,
            "issues": parsed["issues"],
            "setting_violations": [],
        }

    return parsed["data"]


# =========================================================
# FINAL VALIDATION FUNCTION
# =========================================================

def validate_all(
    response_text,
    source_brief,
    expected_output_type,
    audience=None,
    tone=None,
    language=None,
    detail_level=None,
    objective=None,
    style=None,
):
    """
    Run all Formify validation checks and return one final result.
    """

    all_issues = []

    # -----------------------------------------------------
    # 1. JSON validation
    # -----------------------------------------------------

    parsed = parse_json_response(response_text)

    if not parsed["valid"]:
        return {
            "valid": False,
            "issues": parsed["issues"],
            "checks": {
                "json": False,
                "structure": False,
                "field_types": False,
                "nested_structure": False,
                "sequence": False,
                "source_grounding": False,
                "operator_settings": False,
            },
        }

    data = parsed["data"]

    # -----------------------------------------------------
    # 2. Top-level structure
    # -----------------------------------------------------

    structure_result = validate_structure(
        data,
        expected_output_type,
    )

    all_issues.extend(structure_result["issues"])

    # -----------------------------------------------------
    # 3. Field types
    # -----------------------------------------------------

    field_type_result = validate_field_types(
        data,
        expected_output_type,
    )

    all_issues.extend(field_type_result["issues"])

    # -----------------------------------------------------
    # 4. Nested structure
    # -----------------------------------------------------

    nested_result = validate_nested_structure(
        data,
        expected_output_type,
    )

    all_issues.extend(nested_result["issues"])

    # -----------------------------------------------------
    # 5. Sequence / consistency
    # -----------------------------------------------------

    sequence_result = validate_sequence(
        data,
        expected_output_type,
    )

    all_issues.extend(sequence_result["issues"])

    # -----------------------------------------------------
    # 6. Source grounding
    # -----------------------------------------------------

    grounding_result = validate_source_grounding(
        source_brief,
        response_text,
    )

    grounding_valid = grounding_result.get("valid", False)

    if not grounding_valid:
        all_issues.extend(
            grounding_result.get("issues", [])
        )

    all_issues.extend(
        grounding_result.get("unsupported_claims", [])
    )

    all_issues.extend(
        grounding_result.get("contradictions", [])
    )

    all_issues.extend(
        grounding_result.get("missing_or_distorted_information", [])
    )

    # -----------------------------------------------------
    # 7. Operator settings
    # -----------------------------------------------------

    operator_result = validate_operator_settings_with_ai(
        generated_output=response_text,
        audience=audience,
        tone=tone,
        language=language,
        detail_level=detail_level,
        objective=objective,
        style=style,
    )

    operator_valid = operator_result.get("valid", False)

    if not operator_valid:
        all_issues.extend(
            operator_result.get("issues", [])
        )

    all_issues.extend(
        operator_result.get("setting_violations", [])
    )

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    return {
        "valid": len(all_issues) == 0,
        "issues": all_issues,
        "checks": {
            "json": True,
            "structure": structure_result["valid"],
            "field_types": field_type_result["valid"],
            "nested_structure": nested_result["valid"],
            "sequence": sequence_result["valid"],
            "source_grounding": grounding_valid,
            "operator_settings": operator_valid,
        },
    }