import pymupdf
import re


STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "was",
    "were",
    "what",
    "how",
    "why"
}


def clean_text(text):
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


def tokenize(text):
    words = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        text.lower()
    )

    return set(words)


def chunk_text(
    text,
    page_number,
    start_chunk_id,
    chunk_size=800
):

    words = text.split()

    chunks = []

    for i in range(
        0,
        len(words),
        chunk_size
    ):

        chunk = " ".join(
            words[i:i + chunk_size]
        )

        chunks.append({
            "chunk_id":
                start_chunk_id + len(chunks),

            "page":
                page_number,

            "text":
                chunk
        })

    return chunks


def retrieve_chunks(
    chunks,
    query,
    top_k=3
):

    query_lower = query.lower().strip()

    query_words = [
        word
        for word in query_lower.split()
        if word not in STOPWORDS
    ]

    scored_chunks = []

    for chunk in chunks:

        chunk_text_lower = (
            chunk["text"].lower()
        )

        chunk_tokens = tokenize(
            chunk["text"]
        )

        score = 0

        # Exact phrase match
        if query_lower in chunk_text_lower:

            score += 20

        # Individual word matching
        matched_words = 0

        for word in query_words:

            if word in chunk_tokens:

                matched_words += 1
                score += 5

        # Require meaningful match
        if len(query_words) > 1:

            if matched_words < 2:
                continue

        elif matched_words < 1:

            continue

        scored_chunks.append(
            (score, chunk)
        )

    # Highest score first
    scored_chunks.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    results = []

    for score, chunk in scored_chunks[:top_k]:

        result = chunk.copy()

        result["score"] = score

        results.append(result)

    return results


def build_rag_context(
    retrieved_chunks
):

    context = ""

    for chunk in retrieved_chunks:

        context += (
            f"\n[Source: report.pdf | "
            f"Page: {chunk['page']} | "
            f"Chunk: {chunk['chunk_id']} | "
            f"Score: {chunk['score']}]\n"
        )

        context += chunk["text"]

        context += "\n"

    return context.strip()


def build_llm_prompt(
    query,
    rag_context
):

    prompt = f"""
You are an AI assistant working with a trusted source document.
User Query:
{query}
Instructions:
1. Answer the query using only the provided source context.
2. Do not invent information that is not present in the source.
3. If the source does not contain enough information, clearly say so.
4. Keep the answer concise and relevant.
5. Mention the source page when useful.
Source Context:
----------------
{rag_context}
----------------
Answer:
"""

    return prompt.strip()


def process_document(
    pdf_path,
    query
):

    doc = pymupdf.open(
        pdf_path
    )

    all_chunks = []

    next_chunk_id = 1

    # --------------------------------
    # Process every page
    # --------------------------------

    for page_number, page in enumerate(
        doc,
        start=1
    ):

        page_text = page.get_text()

        page_text = clean_text(
            page_text
        )

        page_chunks = chunk_text(
            page_text,
            page_number,
            next_chunk_id
        )

        all_chunks.extend(
            page_chunks
        )

        next_chunk_id += len(
            page_chunks
        )

    # --------------------------------
    # Retrieve relevant chunks
    # --------------------------------

    results = retrieve_chunks(
        all_chunks,
        query
    )

    # --------------------------------
    # Build RAG context
    # --------------------------------

    rag_context = build_rag_context(
        results
    )

    # --------------------------------
    # Build LLM-ready prompt
    # --------------------------------

    llm_prompt = build_llm_prompt(
        query,
        rag_context
    )

    return {
        "pages":
            len(doc),

        "total_chunks":
            len(all_chunks),

        "query":
            query,

        "retrieved_context":
            results,

        "rag_context":
            rag_context,

        "llm_prompt":
            llm_prompt
    }


# ====================================
# TESTING
# ====================================

if __name__ == "__main__":

    query = "multifactor authentication"

    result = process_document(
        "report.pdf",
        query
    )

    print("\n" + "=" * 60)
    print("SEARCH QUERY:")
    print(query)
    print("=" * 60)

    print("\nRETRIEVED CHUNKS:")

    for i, context in enumerate(
        result["retrieved_context"]
    ):

        print(
            f"\n--- Retrieved Context {i + 1} ---"
        )

        print(
            "Chunk ID:",
            context["chunk_id"]
        )

        print(
            "Page:",
            context["page"]
        )

        print(
            "Score:",
            context["score"]
        )

        print("\nText:")

        print(
            context["text"][:500]
        )

    print("\n" + "=" * 60)
    print("LLM READY PROMPT")
    print("=" * 60)

    print(
        result["llm_prompt"]
    )