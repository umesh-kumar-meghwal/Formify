import os
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

            # Read tables
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
        # IMAGE OCR
        # =========================
        elif ext in (".jpg", ".jpeg", ".png"):

            import cv2
            import numpy as np
            import pytesseract

            # Convert bytes → numpy array
            image_array = np.frombuffer(
                file_bytes,
                np.uint8
            )

            image = cv2.imdecode(
                image_array,
                cv2.IMREAD_COLOR
            )

            if image is None:
                raise FileReadError(
                    "Could not open the image file."
                )

            # Upscale
            image = cv2.resize(
                image,
                None,
                fx=2,
                fy=2,
                interpolation=cv2.INTER_CUBIC
            )

            # Grayscale
            gray = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2GRAY
            )

            # Improve contrast
            gray = cv2.threshold(
                gray,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )[1]

            # OCR
            text = pytesseract.image_to_string(
                gray,
                lang="eng",
                config="--psm 6"
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


    # Remove unnecessary spaces
    text = text.strip()


    # No text found
    if not text:

        raise FileReadError(
            "No readable text was found in the file. "
            "The file may be scanned, image-only, "
            "blurry, or contain no readable text."
        )


    return text