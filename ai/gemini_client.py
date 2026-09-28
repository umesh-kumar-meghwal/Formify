import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=API_KEY)

# ---------------------------------------------------------------------------
# Models are tried in this order. If one is overloaded (503), out of quota
# (429) or not found (404), the next one is tried automatically.
# Override from Vercel / .env without touching code:
#   GEMINI_MODELS=gemini-3.8-flash,gemini-2.5-flash,gemini-2.5-flash-lite
# (check https://ai.dev/rate-limit for models available on your key)
# ---------------------------------------------------------------------------
DEFAULT_MODELS = "gemini-3.8-flash,gemini-2.5-flash,gemini-2.5-flash-lite"

MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_MODELS", DEFAULT_MODELS).split(",")
    if m.strip()
]

# Full passes over the model list before giving up (keep small: Vercel has
# a function time limit).
MAX_ROUNDS = 2
ROUND_DELAY_SECONDS = 3

# After a model fails with 503/429, skip it for this long so the next
# requests do not waste calls (and quota) on it.
COOLDOWN_SECONDS = 60
_cooldown_until = {}


def _clean_json_text(text):
    """
    Safety net: remove ```json ... ``` fences if the model adds them,
    so json.loads() in the validators / source brief never breaks.
    """
    if not text:
        return text

    text = text.strip()

    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rstrip()
        if text.endswith("```"):
            text = text[:-3]

    return text.strip()


def _available_models():
    """Models not in cooldown. If all are cooling down, try all anyway."""
    now = time.time()
    ready = [m for m in MODELS if _cooldown_until.get(m, 0) <= now]
    return ready or list(MODELS)


def generate_with_gemini(prompt: str) -> str:
    last_error = None

    for round_no in range(1, MAX_ROUNDS + 1):

        for model in _available_models():
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True
                        ),
                    ),
                )
                return _clean_json_text(response.text)

            except genai_errors.ServerError as e:
                # 500 / 503: overloaded or temporary server issue
                last_error = e
                _cooldown_until[model] = time.time() + COOLDOWN_SECONDS
                print(f"[GEMINI] {model} server error, trying next model: {e}")

            except genai_errors.ClientError as e:
                code = getattr(e, "code", None)

                # 429 = quota, 404 = model name not available for this key
                if code in (429, 404):
                    last_error = e
                    _cooldown_until[model] = time.time() + COOLDOWN_SECONDS
                    print(f"[GEMINI] {model} unavailable ({code}), trying next model")
                    continue

                # 400 / 401 / 403: bad request or key problem, retrying won't help
                raise

        if round_no < MAX_ROUNDS:
            time.sleep(ROUND_DELAY_SECONDS)

    # Every model failed - surface the last error so pipeline.py records it
    raise last_error