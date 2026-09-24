import fitz
import re


def clean_text(text):
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def chunk_text(text, chunk_size=800):
    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


# Open PDF
doc = fitz.open("report.pdf")

text = ""

for page in doc:
    text += page.get_text()

# Clean text
text = clean_text(text)

# Create chunks
chunks = chunk_text(text)

print("PDF opened successfully!")
print("Number of pages:", len(doc))
print("Total chunks:", len(chunks))

for i, chunk in enumerate(chunks[:3]):
    print(f"\n--- Chunk {i + 1} ---")
    print(chunk[:500])