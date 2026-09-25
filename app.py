from flask import Flask, render_template, request, jsonify, send_file
import datetime
import uuid
import os
from dotenv import load_dotenv
from google import genai
from werkzeug.utils import secure_filename
from ai.source_brief import create_source_brief
from ai.pipeline import generate_validated_output
from ai.file_reader import extract_text, FileReadError
from ai.ppt_export import build_presentation_pptx
from ai.infographic_export import build_infographic_html
from ai.docx_export import build_report_docx
from ai.frontend_adapter import (
    to_backend_type,
    setting_label,
    build_frontend_output,
    build_unsupported_output,
)

app = Flask(__name__)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = genai.Client(api_key=api_key)



@app.route("/")
def home():
    return render_template("index.html")


@app.route('/transform', methods=["POST","GET"])
def transform_api():
    if request.method == "POST":
       
        try:
            uploaded_file = request.files.get('sourceFile')
            pasted_text = request.form.get('source_content_raw')

            source_text = ""

            if uploaded_file and uploaded_file.filename != '':
                safe_name = f"{uuid.uuid4().hex}_{secure_filename(uploaded_file.filename)}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
                uploaded_file.save(file_path)
                source_text = extract_text(file_path)
            elif pasted_text and pasted_text.strip():
                source_text = pasted_text.strip()
            else:
                return jsonify({'error': 'No source content or file provided'}), 400

            params = {
                'output_types': request.form.getlist('output_types'),
                'audience': request.form.get('audience'),
                'tone': request.form.get('tone'),
                'language': request.form.get('language'),
                'detailLevel': request.form.get('detailLevel'),
                'objective': request.form.get('objective'),
                'style': request.form.get('style'),
                'additional_instructions': request.form.get('additionalInstructions')
            }

            if not params['output_types']:
                return jsonify({'error': 'No output types selected'}), 400

            sec_context = {
                'threat_category': request.form.get('threat_category'),
                'severity_level': request.form.get('severity_level'),
                'affected_sectors': request.form.getlist('affected_sectors')
            }
            

            # 1) Source Brief (ek baar banta hai, sab outputs ke liye use hota hai)
            source_brief = create_source_brief(source_text)

            # 2) Har selected output type ke liye: generate -> validate -> retry
            generated_content = []

            for frontend_type in params['output_types']:
                backend_type = to_backend_type(frontend_type)

                if backend_type is None:
                    generated_content.append(build_unsupported_output(frontend_type))
                    continue

                result = generate_validated_output(
                    source_brief=source_brief,
                    output_type=backend_type,
                    tone=setting_label('tone', params['tone']),
                    language=setting_label('language', params['language']),
                    audience=setting_label('audience', params['audience']),
                    detail_level=setting_label('detailLevel', params['detailLevel']),
                    objective=setting_label('objective', params['objective']),
                    style=setting_label('style', params['style']),
                )

                generated_content.append(
                    build_frontend_output(frontend_type, result)
                )

            response_payload = {
                'status': 'success',
                'generated_at': datetime.datetime.utcnow().isoformat(),
                'source_brief': source_brief,
                'outputs': generated_content,
                'request_summary': params
            }

            return jsonify(response_payload)

        except FileReadError as e:
            return jsonify({'error': str(e)}), 400

        except Exception as e:
            print(f"Error in transform_api: {e}")
            return jsonify({'error': 'Internal Server Error. Please try again.'}), 500
    else:
        return render_template('transform.html')

@app.route('/download/presentation', methods=["POST"])
def download_presentation():
    """
    Takes the presentation JSON (the 'data' field already returned by
    /transform for a presentation output) and returns a real .pptx file.
    """
    data = request.get_json(force=True, silent=True)

    if not data or 'slides' not in data:
        return jsonify({'error': 'Invalid presentation data'}), 400

    try:
        pptx_path = build_presentation_pptx(data)
    except Exception as e:
        print(f"PPTX export error: {e}")
        return jsonify({'error': 'Could not build the PowerPoint file'}), 500

    return send_file(
        pptx_path,
        as_attachment=True,
        download_name="presentation.pptx",
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@app.route('/download/infographic', methods=["POST"])
def download_infographic():
    """
    Takes the infographic JSON (the 'data' field already returned by
    /transform for an infographic output) and returns a styled .html file.
    """
    data = request.get_json(force=True, silent=True)

    if not data or 'sections' not in data:
        return jsonify({'error': 'Invalid infographic data'}), 400

    try:
        html_path = build_infographic_html(data)
    except Exception as e:
        print(f"Infographic export error: {e}")
        return jsonify({'error': 'Could not build the infographic file'}), 500

    return send_file(
        html_path,
        as_attachment=True,
        download_name="infographic.html",
        mimetype="text/html",
    )


@app.route('/download/report', methods=["POST"])
def download_report():
    """
    Takes the executive_summary or advisory JSON (the 'data' field already
    returned by /transform) and returns a real .docx file.
    """
    data = request.get_json(force=True, silent=True)

    if not data or 'title' not in data:
        return jsonify({'error': 'Invalid report data'}), 400

    try:
        docx_path = build_report_docx(data)
    except Exception as e:
        print(f"DOCX export error: {e}")
        return jsonify({'error': 'Could not build the Word document'}), 500

    return send_file(
        docx_path,
        as_attachment=True,
        download_name="report.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)