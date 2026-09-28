import os
import time
from io import BytesIO


class FileReadError(Exception):
    """Raised when an uploaded file cannot be turned into text."""


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
        # IMAGE OCR - GEMINI VISION
        # =========================
        elif ext in (".jpg", ".jpeg", ".png"):

            from google import genai
            from google.genai import types

            api_key = os.getenv("GEMINI_API_KEY")

            if not api_key:
                raise FileReadError(
                    "GEMINI_API_KEY is not configured."
                )

            client = genai.Client(
                api_key=api_key
            )

            if ext in (".jpg", ".jpeg"):
                mime_type = "image/jpeg"
            else:
                mime_type = "image/png"

            prompt = """
Extract all readable text from this image.

Rules:
- Return ONLY the extracted text.
- Preserve the original wording.
- Preserve paragraphs and line breaks.
- Do not summarize.
- Do not explain the image.
- Do not add information that is not visible.
- If there is no readable text, return an empty response.
"""

            max_attempts = 3
            text = ""

            for attempt in range(max_attempts):

                try:

                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=[
                            types.Part.from_bytes(
                                data=file_bytes,
                                mime_type=mime_type
                            ),
                            prompt
                        ]
                    )

                    text = response.text or ""
                    break

                except Exception as e:

                    error_message = str(e).upper()

                    temporary_error = (
                        "503" in error_message
                        or "UNAVAILABLE" in error_message
                        or "429" in error_message
                        or "RESOURCE_EXHAUSTED" in error_message
                    )

                    if temporary_error and attempt < max_attempts - 1:

                        wait_time = 2 ** (attempt + 1)

                        print(
                            f"Gemini temporarily unavailable. "
                            f"Retrying in {wait_time}s..."
                        )

                        time.sleep(wait_time)

                    else:
                        raise FileReadError(
                            "Gemini OCR is temporarily unavailable. "
                            "Please try uploading the image again "
                            "after a few seconds."
                        )

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