import os
import uuid

from pptx import Presentation


GENERATED_DIR = "generated_files"


def build_presentation_pptx(data):
    """
    Convert the Formify 'presentation' JSON (from PRESENTATION_PROMPT) into
    an actual .pptx file and return its path.

    Expected shape:
    {
        "output_type": "presentation",
        "title": "...",
        "slides": [
            {
                "slide_number": 1,
                "title": "...",
                "content": ["point 1", "point 2"],
                "speaker_notes": "..."
            },
            ...
        ]
    }
    """

    os.makedirs(GENERATED_DIR, exist_ok=True)

    prs = Presentation()

    # ---- Title slide ----
    title_layout = prs.slide_layouts[0]
    title_slide = prs.slides.add_slide(title_layout)
    title_slide.shapes.title.text = data.get("title") or "Presentation"

    # ---- Content slides ----
    content_layout = prs.slide_layouts[1]  # "Title and Content"

    for slide_data in data.get("slides", []):

        slide = prs.slides.add_slide(content_layout)
        slide.shapes.title.text = slide_data.get("title") or ""

        body_placeholder = slide.placeholders[1]
        text_frame = body_placeholder.text_frame
        text_frame.clear()

        points = slide_data.get("content") or []

        if not points:
            points = [""]

        for index, point in enumerate(points):
            paragraph = (
                text_frame.paragraphs[0] if index == 0
                else text_frame.add_paragraph()
            )
            # Assign to run.text (not paragraph.text) so formatting
            # is not collapsed to a single unstyled run.
            run = paragraph.add_run()
            run.text = str(point)

        notes = slide_data.get("speaker_notes")
        if notes:
            slide.notes_slide.notes_text_frame.text = notes

    filename = f"{uuid.uuid4().hex}.pptx"
    output_path = os.path.join(GENERATED_DIR, filename)
    prs.save(output_path)

    return output_path