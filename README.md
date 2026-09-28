# Formify

Setup instructions for running Formify locally and deploying it on Vercel.

## Prerequisites

- Python 3.12
- Git
- A [Gemini API key](https://aistudio.google.com/)
- A [Supabase](https://supabase.com/) project
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords) (used to send OTP emails)

## 1. Clone the repository

```bash
git clone https://github.com/umesh-kumar-meghwal/Formify.git
cd Formify
```

## 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` should include at least:

```
flask
python-dotenv
google-genai
supabase
pypdf
python-docx
python-pptx
requests
pillow
numpy
rapidocr-onnxruntime
opencv-python-headless
```

## 4. Configure environment variables

Create a `.env` file in the project root:

```env
FLASK_SECRET_KEY=change-this-to-a-long-random-string

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODELS=gemini-3.8-flash,gemini-3.5-flash-lite

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your_supabase_secret_key

SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

`GEMINI_MODELS` is optional. Models are tried in order, and if one is overloaded or out of quota, the next one is used.

Do not commit `.env` to GitHub. Make sure it is listed in `.gitignore`.

## 5. Run the app

```bash
python app.py
```

Open http://localhost:5000

## Deploying to Vercel

1. Push the project to GitHub and import it in Vercel.
2. Add every variable from the `.env` example in **Project Settings, Environment Variables**.
3. Keep dependencies small (function size limit is 500 MB). Use `opencv-python-headless`, and do not add `torch`, `easyocr` or `opencv-python`.
4. If the build installs the regular `opencv-python` (pulled in by RapidOCR), add a `pyproject.toml` in the project root:

   ```toml
   [tool.uv]
   override-dependencies = ["opencv-python ; sys_platform == 'never'"]
   ```

5. Redeploy after changing environment variables.
