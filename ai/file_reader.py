import os
from io import BytesIO


class FileReadError(Exception):
    """Raised when an uploaded file cannot be turned into text."""


# ---------------------------------------------------------------------------
# OCR settings (optional, via .env)
#   TESSERACT_CMD = C:\Program Files\Tesseract-OCR\tesseract.exe   (Windows only)
#   OCR_LANGS     = eng            (default)  |  eng+hin  (English + Hindi)
# ---------------------------------------------------------------------------
OCR_LANGS = os.getenv("OCR_LANGS", "eng")
TESSERACT_CMD = os.getenv("TESSERACT_CMD")


def _ocr_gemini(file_bytes, ext):
    """
    Fallback OCR using Gemini Vision (used when pytesseract is not available,
    e.g. on Vercel).
    """
    import time
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise FileReadError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)
    mime_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    model = os.getenv("GEMINI_OCR_MODEL", "gemini-3.8-flash")

    prompt = (
        "Extract all readable text from this image.\n"
        "Rules:\n"
        "- Return ONLY the extracted text.\n"
        "- Preserve the original wording, paragraphs and line breaks.\n"
        "- Do not summarize or explain the image.\n"
        "- If there is no readable text, return an empty response."
    )

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    prompt,
                ],
            )
            return response.text or ""
        except Exception as e:
            msg = str(e).upper()
            temporary = any(
                k in msg for k in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")
            )
            if temporary and attempt < max_attempts - 1:
                time.sleep(2 ** (attempt + 1))
            else:
                raise FileReadError(
                    "OCR is temporarily unavailable. "
                    "Please try uploading the image again after a few seconds."
                )


def _ocr_image(file_bytes, ext=".png"):
    """
    Try local Tesseract first. If pytesseract / Tesseract engine is not
    available (e.g. Vercel), fall back to Gemini Vision.
    """
    try:
        import pytesseract  # noqa: F401
        import PIL  # noqa: F401
    except ImportError:
        return _ocr_gemini(file_bytes, ext)

    try:
        return _ocr_tesseract(file_bytes)
    except FileReadError as e:
        # Tesseract engine missing on server -> fallback to Gemini
        if "not installed" in str(e):
            return _ocr_gemini(file_bytes, ext)
        raise


def _ocr_tesseract(file_bytes):
    """
    Extract text from an image using pytesseract (local, free, no API).
    """
    try:
        import pytesseract
        from PIL import Image, ImageOps
    except ImportError:
        raise FileReadError(
            "OCR libraries are missing. Run: pip install pytesseract pillow"
        )

    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    try:
        img = Image.open(BytesIO(file_bytes))

        # Fix phone-camera rotation (EXIF)
        img = ImageOps.exif_transpose(img)

        # Handle transparent PNGs -> white background
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert("RGB")

        # Upscale small images (OCR works better on bigger text)
        min_width = 1500
        if img.width < min_width:
            scale = min_width / img.width
            img = img.resize(
                (int(img.width * scale), int(img.height * scale)),
                Image.LANCZOS,
            )

        # Grayscale + auto contrast improves accuracy
        img = ImageOps.grayscale(img)
        img = ImageOps.autocontrast(img)

        # --oem 3 = default engine, --psm 3 = fully automatic page segmentation
        return pytesseract.image_to_string(
            img,
            lang=OCR_LANGS,
            config="--oem 3 --psm 3",
        )

    except pytesseract.TesseractNotFoundError:
        raise FileReadError(
            "Tesseract OCR engine is not installed on the server. "
            "Install it and (on Windows) set TESSERACT_CMD in .env."
        )
    except pytesseract.TesseractError as e:
        raise FileReadError(
            f"OCR failed (check OCR_LANGS / language pack): {e}"
        )


def extract_text(file_bytes, filename):
    """
    Extract plain text from uploaded file bytes.

    Supported:
    .txt, .md, .pdf, .docx, .jpg, .jpeg, .png
    """

    ext = os.path.splitext(filename)[1].lower()

    try:

        # =========================
        # TXT / MARKDOWN
        # =========================
        if ext in (".txt", ".md"):

            text = file_bytes.decode(
                "utf-8",
                errors="ignore"
            )

        # =========================
        # PDF
        # =========================
        elif ext == ".pdf":

            from pypdf import PdfReader

            reader = PdfReader(
                BytesIO(file_bytes)
            )

            text = "\n".join(
                (page.extract_text() or "")
                for page in reader.pages
            )

        # =========================
        # DOCX
        # =========================
        elif ext == ".docx":

            from docx import Document

            doc = Document(
                BytesIO(file_bytes)
            )

            parts = [
                p.text
                for p in doc.paragraphs
            ]

            for table in doc.tables:
                for row in table.rows:
                    parts.append(
                        " | ".join(
                            cell.text
                            for cell in row.cells
                        )
                    )

            text = "\n".join(parts)

        # =========================
        # IMAGE OCR - PYTESSERACT
        # =========================
        elif ext in (".jpg", ".jpeg", ".png"):

            text = _ocr_image(file_bytes, ext)

        # =========================
        # UNSUPPORTED FILE
        # =========================
        else:

            raise FileReadError(
                f"'{ext}' files cannot be read yet. "
                "Please upload a PDF, DOCX, TXT, MD, "
                "JPG, JPEG or PNG file."
            )

    except FileReadError:
        raise

    except Exception as e:

        raise FileReadError(
            f"Could not read the uploaded file: {e}"
        )

    text = text.strip()

    if not text:

        raise FileReadError(
            "No readable text was found in the file. "
            "The file may be scanned, image-only, "
            "blurry, or contain no readable text."
        )

    return text