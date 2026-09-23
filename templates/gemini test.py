import os
from dotenv import load_dotenv
from google import genai

# Load API key
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY nahi mili.")
    exit()

# Connect to Gemini
client = genai.Client(api_key=api_key)

# Simple connectivity test
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Hello Gemini! Reply with: Connectivity successful."
)

print("Gemini Response:")
print(response.text)

source_text = """
The system accepts plain text, PDF, DOCX, TXT, PPTX, images, audio, and video
as possible input sources.

For text-based PDFs, text can be extracted using PyPDF2, pdfplumber, or PyMuPDF.
For scanned PDFs, the PDF is converted into images and OCR is used to extract text.

The system first creates a summary, key facts, and a do-not-invent list
before generating the final content.
"""

prompt = f"""
You are a source-understanding assistant.

Analyze ONLY the source provided below.

Give me:
1. SUMMARY — 3 to 5 bullet points
2. KEY FACTS — exact facts, numbers, names, and technical details
3. DO NOT INVENT — information that must not be added if it is not present in the source
4. MISSING INFORMATION — important information that is not available in the source

Rules:
- Use only the information present in the source.
- Do not add information from your own knowledge.
- Do not make assumptions.
- Keep facts accurate.

SOURCE:
{source_text}
"""
response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt
)

print(response.text)

test_prompt = f"""
Based ONLY on the source below, answer these questions:

1. What is the exact name of the system?
2. Who developed the system?
3. Which organization owns the system?

Strict rule:
If the information is not present in the source, say:
"Information not available in source."

Do not guess or use outside knowledge.

SOURCE:
{source_text}
"""

test_response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=test_prompt
)

print("\n--- HALLUCINATION TEST ---")
print(test_response.text)