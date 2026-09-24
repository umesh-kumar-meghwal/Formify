from flask import Flask, render_template, request, jsonify
import datetime
import uuid
import os
from dotenv import load_dotenv
from google import genai
from werkzeug.utils import secure_filename
from ai.source_brief import create_source_brief
from ai.pipeline import generate_validated_output
from ai.file_reader import extract_text, FileReadError
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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)