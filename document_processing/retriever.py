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


def retrieve_chunks(chunks, query, top_k=3):
    query_lower = query.lower()
    query_words = query_lower.split()

    scored_chunks = []

    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = 0

        # Exact phrase match gets higher priority
        if query_lower in chunk_lower:
            score += 10

        # Individual word matching
        for word in query_words:
            if word in chunk_lower:
                score += 1

        scored_chunks.append((score, chunk))

    # Highest score first
    scored_chunks.sort(reverse=True, key=lambda x: x[0])

    return [chunk for score, chunk in scored_chunks[:top_k]]


# Open PDF
doc = fitz.open("report.pdf")

text = ""

for page in doc:
    text += page.get_text()


# Clean extracted text
text = clean_text(text)


# Create chunks
chunks = chunk_text(text)


# Search query
query = "principle of least privilege"


# Retrieve relevant chunks
results = retrieve_chunks(chunks, query)


# Display results
print("PDF opened successfully!")
print("Number of pages:", len(doc))
print("Total chunks:", len(chunks))
print("\nSearch Query:", query)

for i, result in enumerate(results):
    print(f"\n--- Result {i + 1} ---")
    print(result[:500])


