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

# Mock cybersecurity source
source_text = """
A phishing campaign has been targeting employees through fake Microsoft
365 login emails. The emails contain a link to a fraudulent login page
designed to steal usernames and passwords. Employees are advised not to
click suspicious links and to verify the sender before entering credentials.
"""

# Executive Summary prompt
prompt = (
    "You are the AI content transformation engine for Formify.\n\n"
    "Your task is to create an Executive Summary from the provided source.\n\n"
    "SOURCE:\n"
    + source_text
    + "\n\n"
    "Create a clear and professional Executive Summary.\n\n"
    "Include:\n"
    "1. Overview\n"
    "2. Key Findings\n"
    "3. Main Risks\n"
    "4. Recommended Actions\n\n"
    "Rules:\n"
    "- Use only information supported by the source.\n"
    "- Do not invent facts, statistics, dates, names, or technical details.\n"
    "- Keep the summary concise and easy to understand.\n"
    "- Preserve the meaning of the original source.\n"
    "- If important information is missing, do not guess it."
)

# Generate Executive Summary
response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt
)

print("\n===== FORMIFY EXECUTIVE SUMMARY =====\n")
print(response.text)