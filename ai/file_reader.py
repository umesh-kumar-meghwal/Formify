import os
from io import BytesIO


class FileReadError(Exception):
    """Raised when an uploaded file cannot be turned into text."""


# ---------------------------------------------------------------------------
# IMAGE OCR - RapidOCR (pure pip, no Gemini, no Tesseract binary, works on Vercel)
# ---------------------------------------------------------------------------
_ocr_engine = None


def _get_ocr_engine():
    """Load the OCR engine once and reuse it (loading is the slow part)."""
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            raise FileReadError(
                "OCR library is missing. Add 'rapidocr-onnxruntime' and "
                "'pillow' to requirements.txt"
            )
        _ocr_engine = RapidOCR()
    return _ocr_engine


def _ocr_image(file_bytes):
    """Extract text from an image using RapidOCR."""
    try:
        import numpy as np
        from PIL import Image, ImageOps
    except ImportError:
        raise FileReadError(
            "Image libraries are missing. Add 'pillow' and 'numpy' to requirements.txt"
        )

    img = Image.open(BytesIO(file_bytes))

    # Fix phone-camera rotation (EXIF)
    img = ImageOps.exif_transpose(img)

    # Transparent PNG -> white background
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    else:
        img = img.convert("RGB")

    # Limit huge images (saves memory / time on serverless)
    max_side = 2500
    if max(img.size) > max_side:
        scale = max_side / max(img.size)
        img = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.LANCZOS,
        )

    engine = _get_ocr_engine()
    result, _ = engine(np.array(img))

    if not result:
        return ""

    # result item = [box, text, confidence]; sort top-to-bottom, left-to-right
    result = sorted(result, key=lambda r: (round(r[0][0][1] / 15), r[0][0][0]))

    lines = []
    last_row = None
    current = []
    for box, txt, _score in result:
        row = round(box[0][1] / 15)
        if last_row is not None and row != last_row:
            lines.append(" ".join(current))
            current = []
        current.append(txt)
        last_row = row
    if current:
        lines.append(" ".join(current))

    return "\n".join(lines)


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
        # IMAGE OCR - RAPIDOCR
        # =========================
        elif ext in (".jpg", ".jpeg", ".png"):

            text = _ocr_image(file_bytes)

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