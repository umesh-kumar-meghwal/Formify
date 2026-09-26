from flask import Flask, render_template, request, jsonify, send_file,session,redirect
import datetime
import uuid
import os
import smtplib
import secrets
from dotenv import load_dotenv
from google import genai
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
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
from db import supabase
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "formify-dev-secret-change-this")
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
client = genai.Client(api_key=api_key)

from db import *
print("URL:", SUPABASE_URL)
print("KEY PREFIX:", SUPABASE_SECRET_KEY[:12] if SUPABASE_SECRET_KEY else None)
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/send-otp", methods=["POST"])
def send_otp():
    try:
        email = request.form.get("email", "").strip().lower()
        if not email or "@" not in email:
            return jsonify({"success": False, "message": "A valid email address is required."}), 400

        existing = supabase.table("login").select("email").eq("email", email).execute()
        if existing.data:
            return jsonify({"success": False, "message": "Email is already registered."}), 409

        last_sent = session.get("otp_sent_at")
        if last_sent:
            current_time = datetime.now(timezone.utc).timestamp()
            if current_time - last_sent < 60:
                remaining = int(60 - (current_time - last_sent))
                return jsonify({"success": False, "message": f"Please wait {remaining} seconds before requesting a new OTP."}), 429

        otp = str(secrets.randbelow(900000) + 100000)
        session["otp"] = otp
        session["otp_email"] = email
        session["otp_expires"] = (datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()
        session["otp_sent_at"] = datetime.now(timezone.utc).timestamp()
        session.pop("email_verified", None)

        send_otp_email(email, otp)
        return jsonify({"success": True, "message": "OTP sent successfully to your email."}), 200

    except Exception as e:
        print("SEND OTP ERROR:", e)
        return jsonify({"success": False, "message": "Unable to send OTP at this time."}), 500

def send_otp_email(to_email: str, otp: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("[EMAIL WARNING] SMTP credentials missing. OTP is:", otp)
        return

    msg = EmailMessage()
    msg["Subject"] = "SarvShield Security Verification Code"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg.set_content(f"Your SarvShield verification code is: {otp}\nValid for 10 minutes.")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_EMAIL.strip(), SMTP_PASSWORD.strip())
        server.send_message(msg)


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    try:
        entered_otp = request.form.get("otp", "").strip()
        saved_otp = session.get("otp")
        otp_email = session.get("otp_email")
        expires_at = session.get("otp_expires")

        if not saved_otp or not otp_email:
            return jsonify({"success": False, "message": "Please request an OTP first."}), 400

        if not entered_otp.isdigit() or len(entered_otp) != 6:
            return jsonify({"success": False, "message": "Enter a valid 6-digit OTP."}), 400

        current_time = datetime.now(timezone.utc).timestamp()
        if not expires_at or current_time > expires_at:
            session.pop("otp", None)
            return jsonify({"success": False, "message": "OTP has expired. Please request a new one."}), 400

        if entered_otp != saved_otp:
            return jsonify({"success": False, "message": "Invalid OTP entered."}), 400

        session["email_verified"] = True
        session["verified_email"] = otp_email
        session.pop("otp", None)
        session.pop("otp_expires", None)

        return jsonify({"success": True, "message": "Email verified successfully!"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "email" in session:
            return redirect("/admin-dashboard" if session.get("usertype") == "admin" else "/home")
        return render_template("login.html")

    try:
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required."}), 400

        result = supabase.table("login").select("email, password, usertype").eq("email", email).execute()
        if not result.data:
            return jsonify({"success": False, "message": "Invalid email or password."}), 401

        user = result.data[0]
        stored_password = user.get("password", "")

        is_valid = (
            check_password_hash(stored_password, password)
            if stored_password.startswith(("pbkdf2:", "scrypt:", "bcrypt:"))
            else (stored_password == password)
        )

        if not is_valid:
            return jsonify({"success": False, "message": "Invalid email or password."}), 401

        session["email"] = user["email"]
        session["usertype"] = user["usertype"]
        redirect_url = "/admin-dashboard" if user["usertype"] == "admin" else "/home"

        return jsonify({"success": True, "message": "Login successful!", "redirect": redirect_url}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/user-show", methods=["GET"])
def user_show():
    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")
    try:
        result = supabase.table("user").select("name, email, phone, address, profile_picture").execute()
        return render_template("user-show.html", users=result.data or [])
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    # User login check
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")

    user_email = session.get("email")

    if request.method == "POST":

        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Check empty fields
        if not current_password or not new_password or not confirm_password:
            return render_template(
                "change-password.html",
                error="All fields are required."
            )

        # Check new password confirmation
        if new_password != confirm_password:
            return render_template(
                "change-password.html",
                error="New password and confirm password do not match."
            )

        try:

            # Get current user password
            response = (
                supabase
                .table("login")
                .select("password")
                .eq("email", user_email)
                .single()
                .execute()
            )

            user_data = response.data

            if not user_data:
                return render_template(
                    "change-password.html",
                    error="User not found."
                )

            # Check old password
            if current_password != user_data["password"]:
                return render_template(
                    "change-password.html",
                    error="Current password is incorrect."
                )

            # Update password
            supabase.table("login").update({
                "password": new_password
            }).eq("email", user_email).execute()

            return render_template(
                "change-password.html",
                success="Password changed successfully."
            )

        except Exception as e:

            print("Change Password Error:", e)

            return render_template(
                "change-password.html",
                error="Something went wrong."
            )

    return render_template("change-password.html")



@app.route('/home')
def home_page():
    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")
    
    user_email = session.get("email")

    # 1. Fetch User Profile Info
    user_resp = (
        supabase.table("user")
        .select("profile_picture, email, name")
        .eq("email", user_email)
        .single()
        .execute()
    )
    user_data = user_resp.data or {"email": user_email}

    # 2. Fetch Real Trust Metrics from Supabase
    trust_stats = get_user_real_trust_metrics(user_email)

    return render_template('home.html', data=user_data, stats=trust_stats)

    

    
@app.route("/user-edit/<email>", methods=["GET", "POST"])
def user_edit(email):

    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")

    try:

        # =========================================
        # GET USER
        # =========================================

        if request.method == "GET":

            result = (
                supabase
                .table("user")
                .select(
                    "name, email, phone, address, profile_picture"
                )
                .eq("email", email)
                .execute()
            )

            if not result.data:
                return "User not found", 404

            return render_template(
                "user-edit.html",
                user=result.data[0]
            )


        # =========================================
        # POST / UPDATE USER
        # =========================================

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        update_data = {
            "name": name,
            "phone": phone,
            "address": address
        }


        # =========================================
        # PROFILE PICTURE
        # =========================================

        profile_picture = request.files.get("profile_picture")

        if profile_picture and profile_picture.filename:

            filename = secure_filename(profile_picture.filename)

            allowed_extensions = {
                "jpg",
                "jpeg",
                "png",
                "webp"
            }

            extension = filename.rsplit(".", 1)[-1].lower()

            if extension not in allowed_extensions:

                return jsonify({
                    "success": False,
                    "message": "Only JPG, JPEG, PNG and WEBP images are allowed."
                }), 400


            # =====================================
            # DELETE OLD PROFILE PICTURES
            # =====================================

            bucket = supabase.storage.from_("profile-pictures")

            old_files = bucket.list(email)

            print("Old files:", old_files)


            if old_files:

                old_file_paths = []

                for old_file in old_files:

                    old_file_name = old_file.get("name")

                    if old_file_name:

                        old_file_paths.append(
                            f"{email}/{old_file_name}"
                        )


                if old_file_paths:

                    print(
                        "Deleting old files:",
                        old_file_paths
                    )

                    bucket.remove(old_file_paths)


            # =====================================
            # UPLOAD NEW PROFILE PICTURE
            # =====================================

            file_path = f"{email}/profile.{extension}"

            file_bytes = profile_picture.read()


            bucket.upload(
                file_path,
                file_bytes,
                file_options={
                    "content-type": profile_picture.content_type,
                    "upsert": "true"
                }
            )


            # =====================================
            # GET PUBLIC URL
            # =====================================

            public_url = bucket.get_public_url(file_path)


            update_data["profile_picture"] = public_url


        # =========================================
        # UPDATE USER TABLE
        # =========================================

        result = (
            supabase
            .table("user")
            .update(update_data)
            .eq("email", email)
            .execute()
        )


        print("User Updated:", result)


        return jsonify({
            "success": True,
            "message": "User updated successfully!"
        }), 200


    except Exception as e:

        print("User Edit Error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route("/my-profile", methods=["GET", "POST"])
def my_profile():

    if "email" not in session or session.get("usertype") != "user":
        return redirect("/error")

    user_email = session.get("email")

    try:

        # =========================
        # SAVE PROFILE
        # =========================
        if request.method == "POST":

            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            address = request.form.get("address", "").strip()

            profile_picture = request.files.get("profile_picture")

            update_data = {
                "name": name,
                "phone": phone,
                "address": address
            }

            # =========================
            # PROFILE PICTURE
            # =========================
            if profile_picture and profile_picture.filename:

                filename = secure_filename(profile_picture.filename)

                allowed_extensions = {
                    "jpg",
                    "jpeg",
                    "png",
                    "webp"
                }

                extension = filename.rsplit(".", 1)[-1].lower()

                if extension not in allowed_extensions:
                    return redirect("/my-profile")

                file_path = f"{user_email}/profile.{extension}"

                file_bytes = profile_picture.read()

                # Supabase Storage upload
                supabase.storage \
                    .from_("profile-pictures") \
                    .upload(
                        file_path,
                        file_bytes,
                        {
                            "content-type": profile_picture.content_type,
                            "upsert": "true"
                        }
                    )

                # Public URL
                public_url = (
                    supabase.storage
                    .from_("profile-pictures")
                    .get_public_url(file_path)
                )

                update_data["profile_picture"] = public_url

            # =========================
            # UPDATE USER
            # =========================
            supabase \
                .table("user") \
                .update(update_data) \
                .eq("email", user_email) \
                .execute()

            return redirect("/my-profile")


        # =========================
        # GET PROFILE
        # =========================

        response = (
            supabase
            .table("user")
            .select(
                "email, name, phone, address, profile_picture"
            )
            .eq("email", user_email)
            .single()
            .execute()
        )

        data = response.data

        if not data:
            return redirect("/error")

        return render_template(
            "my-profile.html",
            data=data
        )

    except Exception as e:

        print("My Profile Error:", e)

        return redirect("/error")


   

@app.route("/user-register", methods=["GET", "POST"])
def user_register():
    if request.method == "GET":
        if "email" in session and session.get("usertype") == "user":
            return redirect("/user-dashboard")
        return render_template("user-register.html")

    try:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "").strip()

        if not all([name, email, phone, address, password]):
            return jsonify({"success": False, "message": "All fields are required."}), 400

        if not session.get("email_verified") or session.get("verified_email") != email:
            return jsonify({"success": False, "message": "Please verify your email address first."}), 403

        existing = supabase.table("login").select("email").eq("email", email).execute()
        if existing.data:
            return jsonify({"success": False, "message": "Email already registered."}), 409

        password_hash = generate_password_hash(password)
        supabase.table("user").insert({"name": name, "email": email, "phone": phone, "address": address}).execute()
        supabase.table("login").insert({"email": email, "password": password_hash, "usertype": "user"}).execute()

        session.pop("email_verified", None)
        session.pop("verified_email", None)
        session["email"] = email
        session["usertype"] = "user"

        return jsonify({"success": True, "redirect": "/user-dashboard", "message": "Registration successful!"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500








@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

  
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("404.html"), 500


@app.errorhandler(403)
def forbidden(error):
    return render_template("404.html"), 403



@app.route("/admin-dashboard")
def admin_dashboard():
    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")
    try:
        user_email = session.get("email")
        admin_res = supabase.table("admin").select("*").eq("email", user_email).limit(1).execute()
        data = admin_res.data[0] if admin_res.data else None
        return render_template("admin-dashboard.html", data=data)
    except Exception as e:
        return redirect("/error")




@app.route("/admin-show", methods=["GET"])
def admin_show():
    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")
    try:
        result = supabase.table("admin").select("name, email, phone, address").execute()
        return render_template("admin-show.html", admins=result.data or [])
    except Exception as e:
        return f"Error: {str(e)}", 500
    
@app.route("/admin-register", methods=["GET", "POST"])
def admin_register():
    if "email" not in session or session.get("usertype") != "admin":
        return redirect("/error")

    if request.method == "GET":

        return render_template("admin-register.html")

    try:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not email or not password or not address:
            return jsonify({"success": False, "message": "All fields are required"}), 400

        existing = supabase.table("login").select("email").eq("email", email).execute()
        if existing.data:
            return jsonify({"success": False, "message": "Admin email already registered"}), 409

        supabase.table("admin").insert({"name": name, "email": email, "phone": phone, "address": address}).execute()
        supabase.table("login").insert({"email": email, "password": generate_password_hash(password), "usertype": "admin"}).execute()

        return jsonify({"success": True, "message": "Admin registered successfully!"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500




















@app.route('/transform', methods=["POST","GET"])
def transform_api():
    if "email" in session and session.get("usertype") == "admin":
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
    else:
        return redirect('/error')

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

    Pass ?images=false to skip AI icon generation for a much faster,
    free/instant download.
    """
    data = request.get_json(force=True, silent=True)

    if not data or 'sections' not in data:
        return jsonify({'error': 'Invalid infographic data'}), 400

    generate_images = request.args.get('images', 'true').lower() != 'false'

    try:
        html_path = build_infographic_html(data, generate_images=generate_images)
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