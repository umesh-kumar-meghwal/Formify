import fitz
import re

pdf_path = "report.pdf"

doc = fitz.open(pdf_path)

text = ""

for page in doc:
    text += page.get_text()

# Text cleaning
text = text.replace("\r", "\n")
text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r"\n\s*\n+", "\n\n", text)
text = text.strip()

print("PDF opened successfully!")
print("Number of pages:", len(doc))

print("\n--- CLEANED TEXT ---\n")
print(text)
