# 📝 Formify

**AI-Powered Content Transformation & Document Generation Platform**

Formify converts text, documents, PDFs and images into structured content using AI, OCR and document-processing tools.

## 🔗 Project Links

- **GitHub:** https://github.com/umesh-kumar-meghwal/Formify
- **Live Demo:** https://formify-orcin.vercel.app/

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, REST APIs
- **AI:** Google Gemini
- **Document Processing:** PyPDF, python-docx, python-pptx
- **OCR / Image Processing:** Tesseract OCR, OpenCV
- **Database & Storage:** Supabase
- **Frontend:** HTML, CSS, JavaScript
- **Authentication:** Flask Sessions + Email OTP

---

# ⚙️ Setup Instructions

## 1. Clone the Repository

```bash
git clone https://github.com/umesh-kumar-meghwal/Formify.git
cd Formify
```

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Install Tesseract OCR

Formify uses Tesseract OCR for extracting text from images.

Install **Tesseract OCR** separately on your system and make sure the Tesseract executable is available in your system PATH.

---

## 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_secret_key

GEMINI_API_KEY=your_gemini_api_key

SMTP_EMAIL=your_email
SMTP_PASSWORD=your_app_password

FLASK_SECRET_KEY=your_secret_key
```

### Required Services

- **Supabase** — Database and Storage
- **Google Gemini API** — AI content generation
- **SMTP/Gmail** — Email OTP verification

> Never commit your `.env` file or expose API keys and passwords publicly.

---

## 6. Run the Application

```bash
python app.py
```

The application will run at:

```text
http://127.0.0.1:5000
```

Open this URL in your browser.

---

## 📄 Supported Processing

Formify supports processing source content and generating:

- Summaries
- Reports
- Presentations
- Infographics
- Structured content

### Processing Flow

```text
User Input
    ↓
Content / File Extraction
    ↓
OCR (when required)
    ↓
Source Analysis
    ↓
AI Transformation
    ↓
Output Validation
    ↓
Generated Output
```

---

## 📦 Main Dependencies

The project uses the dependencies listed in `requirements.txt`, including:

```text
flask
python-dotenv
google-genai
supabase
pypdf
python-docx
python-pptx
requests
rapidocr-onnxruntime
opencv-python-headless
pillow
numpy
```

---

## 🔐 Security

- Keep credentials inside environment variables.
- Do not commit `.env` to GitHub.
- Use a secure `FLASK_SECRET_KEY` in production.
- Use a Gmail App Password or valid SMTP credentials for email OTP.

---

## 📌 Project Information

**Project:** Formify  
**Category:** AI / Content Transformation  
**Platform:** Web Application

---

## 🚀 Formify

**Transform Information into Meaningful Content.**
