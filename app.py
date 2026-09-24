from flask import Flask, render_template, request, jsonify
import datetime
import uuid
import os
from dotenv import load_dotenv
from google import genai
from ai.source_brief import create_source_brief

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
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
                uploaded_file.save(file_path)
                source_text = f"[FILE UPLOADED: {uploaded_file.filename}]. Placeholder extracted text."
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
            source_text = " dfbhabhfafjbfjbfhbva uibdif babvvdahvy8adbvdaadvshbhuhbsdhbs"

            #generated_content = ai_generate(source_text, params, sec_context)
            source_brief = create_source_brief(source_text)
            build_prompt(source_brief,output_type,tone=None,language=None,audience=None,detail_level=None,objective=None,style=None)
            

            response_payload = {
                'status': 'success',
                'generated_at': datetime.datetime.utcnow().isoformat(),
                'outputs': generated_content,
                'request_summary': params
            }

            return jsonify(response_payload)

        except Exception as e:
            print(f"Error in transform_api: {e}")
            return jsonify({'error': 'Internal Server Error. Please try again.'}), 500
    else:
        return render_template('transform.html')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)