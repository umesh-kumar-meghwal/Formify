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