import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

IMAGES_URL = "https://openrouter.ai/api/v1/images"

# Fast/cheap image model, small square icon-style output.
IMAGE_MODEL = "google/gemini-2.5-flash-image"

# Keep requests bounded — image generation is much slower than text.
REQUEST_TIMEOUT_SECONDS = 60


def generate_icon_image(prompt_text):
    """
    Generate a single small flat-style icon/illustration for the given
    prompt text and return (base64_string, media_type), or (None, None)
    if generation fails for any reason (missing key, timeout, API error,
    credits exhausted, etc.) — callers should treat this as "skip the
    image" rather than crash.
    """

    if not OPENROUTER_API_KEY:
        print("Image generation skipped: OPENROUTER_API_KEY not set.")
        return None, None

    full_prompt = (
        f"Simple flat vector icon illustration representing: {prompt_text}. "
        "Minimal, clean, modern corporate style, indigo and white color "
        "palette, centered, plain white background, no text, no watermark."
    )

    try:
        response = requests.post(
            IMAGES_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": IMAGE_MODEL,
                "prompt": full_prompt,
                "n": 1,
                "aspect_ratio": "1:1",
                "quality": "low",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code != 200:
            print(f"Image generation failed ({response.status_code}): {response.text[:300]}")
            return None, None

        result = response.json()
        images = result.get("data") or []

        if not images:
            print("Image generation returned no images.")
            return None, None

        image = images[0]
        return image.get("b64_json"), image.get("media_type", "image/png")

    except requests.exceptions.RequestException as e:
        print(f"Image generation request failed: {e}")
        return None, None