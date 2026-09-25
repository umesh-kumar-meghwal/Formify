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

MODEL_NAME = "gemini-3.5-flash-lite"

# 503 (model overloaded) is temporary. Retry a few times with a short
# backoff before giving up, instead of failing the whole request.
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


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


def generate_with_gemini(prompt: str) -> str:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            return _clean_json_text(response.text)

        except genai_errors.ServerError as e:
            # 503 / 500-range: model overloaded or temporary server issue.
            last_error = e
            print(f"Gemini server error (attempt {attempt}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

        except genai_errors.ClientError as e:
            # 4xx: bad request, invalid key, quota, etc. Retrying won't help.
            raise

    # All retries used up — surface the last error so the caller
    # (pipeline.py) records it in the validation issues.
    raise last_error