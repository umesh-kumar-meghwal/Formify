import os


class FileReadError(Exception):
    """Raised when an uploaded file cannot be turned into text."""


def extract_text(file_path):
    """
    Extract plain text from an uploaded file.
    Supported: .txt, .md, .pdf (text-based), .docx
    """

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext in (".txt", ".md"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        elif ext == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text = "\n".join(
                (page.extract_text() or "") for page in reader.pages
            )

        elif ext == ".docx":
            from docx import Document

            doc = Document(file_path)
            parts = [p.text for p in doc.paragraphs]

            for table in doc.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))

            text = "\n".join(parts)

        else:
            raise FileReadError(
                f"'{ext}' files cannot be read yet. Please upload a PDF, "
                f"DOCX, TXT or MD file, or paste the text instead."
            )

    except FileReadError:
        raise
    except Exception as e:
        raise FileReadError(f"Could not read the uploaded file: {e}")

    text = text.strip()

    if not text:
        raise FileReadError(
            "No readable text was found in the file (it may be scanned or "
            "image-only). Please paste the text instead."
        )

    return text