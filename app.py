from flask import (
    Flask, render_template, redirect, url_for, session, flash,
    jsonify, request, send_from_directory
)
import mysql.connector, os
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from PyPDF2 import PdfReader
from datetime import datetime

# ---------- พาธหลัก ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JS_DIR   = BASE_DIR  # ใช้เสิร์ฟ JS จากโฟลเดอร์เดียวกัน

# ---------- สร้างแอป ----------
app = Flask(
    __name__,
    template_folder=BASE_DIR,     # ใช้ไฟล์ .html ในโฟลเดอร์เดียวกับ app.py
    static_folder=BASE_DIR,       # ใช้ไฟล์ static (css/js/img) ในโฟลเดอร์เดียวกัน
    static_url_path="/static"     # เส้นทางเสิร์ฟ static
)
app.secret_key = "change_me_to_random_secret"

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
)

@app.after_request
def _no_cache_html(resp):
    try:
        if resp.mimetype in ("text/html", "application/xhtml+xml"):
            resp.headers["Cache-Control"] = "no-store"
    except Exception:
        pass
    return resp

# ---------- DB CONFIG: รองรับทั้ง local และ remote (SERVER_IP = 192.168.1.4) ----------
SERVER_IP = "192.168.1.4"  # <-- ใส่ IP เครื่องที่รัน MySQL ของคุณ

# ค่าพื้นฐานร่วม (แนะนำให้เปลี่ยนเป็น appuser+รหัสแข็งแรงในโปรดักชัน)
BASE_DB = {
    "port": 3306,
    "user": "root",
    "password": "จๅจภจถจุ",           # แก้ให้ตรงของคุณ
    "database": "seminar",
    "auth_plugin": "mysql_native_password",
    "connection_timeout": 5,
}

def get_conn():
    """
    ลำดับการเชื่อมต่อ:
    1) 127.0.0.1  (กรณี Flask และ MySQL อยู่เครื่องเดียวกัน)
    2) SERVER_IP  (กรณีรันจากเครื่องอื่นใน LAN)
    """
    last_err = None
    try:
        return mysql.connector.connect(host="127.0.0.1", **BASE_DB)
    except mysql.connector.Error as e1:
        last_err = e1
        try:
            return mysql.connector.connect(host=SERVER_IP, **BASE_DB)
        except mysql.connector.Error as e2:
            last_err = e2
    # ถ้าไม่สำเร็จทั้งสองแบบ โยน error ออกไปเพื่อให้เห็นสาเหตุจริงในหน้า /dbping หรือ log
    raise last_err

# ---------- เสิร์ฟไฟล์ JS ----------
@app.route("/js/<path:filename>")
@app.route("/JS/<path:filename>")
def serve_js(filename):
    return send_from_directory(JS_DIR, filename)

# ---------- อัปโหลด ----------
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

EXTRACT_FOLDER = os.path.join(app.config["UPLOAD_FOLDER"], "extracted")
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/extracted/<path:filename>")
def extracted_file(filename):
    return send_from_directory(EXTRACT_FOLDER, filename, as_attachment=True)

# ---------- PAGES ----------
@app.route("/")
def home():
    return redirect(url_for("index") if "user_id" in session else url_for("login_page"))

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")

@app.route("/plan", methods=["GET"])
def plan_page():
    if "user_id" not in session:
        flash("กรุณาเข้าสู่ระบบก่อน", "error")
        return redirect(url_for("login_page"))
    return render_template("plan.html")

@app.route("/success", methods=["GET"])
def success_page():
    if "user_id" not in session:
        flash("กรุณาเข้าสู่ระบบก่อน", "error")
        return redirect(url_for("login_page"))
    return render_template("success.html")

@app.route("/user", methods=["GET"])
def user_page():
    if "user_id" not in session:
        flash("กรุณาเข้าสู่ระบบก่อน", "error")
        return redirect(url_for("login_page"))
    return render_template("user.html")

# ---------- INDEX ----------
@app.route("/index", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        flash("กรุณาเข้าสู่ระบบก่อน", "error")
        return redirect(url_for("login_page"))

    reading_text = None
    download_url = None
    pdf_url = None

    if request.method == "POST":
        if "file" not in request.files or request.files["file"].filename == "":
            flash("❌ กรุณาเลือกไฟล์", "error")
            return redirect(request.url)

        f = request.files["file"]
        filename = f.filename
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(path)

        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == ".txt":
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    reading_text = fh.read()
            elif ext == ".csv":
                df = pd.read_csv(path)
                reading_text = df.to_string(index=False)
            elif ext in [".xls", ".xlsx"]:
                df = pd.read_excel(path)
                reading_text = df.to_string(index=False)
            elif ext == ".pdf":
                pdf_url = url_for("uploaded_file", filename=filename)
                reader = PdfReader(path)
                pieces = []
                for i in range(len(reader.pages)):
                    text = reader.pages[i].extract_text() or ""
                    pieces.append(text.strip())
                reading_text = "\n\n".join(pieces).strip()
            else:
                flash("รองรับเฉพาะ .txt, .csv, .xls, .xlsx, .pdf", "warning")
                return redirect(request.url)

            if reading_text:
                base = os.path.splitext(os.path.basename(filename))[0]
                outname = f"{base}_extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                outpath = os.path.join(EXTRACT_FOLDER, outname)
                with open(outpath, "w", encoding="utf-8", errors="ignore") as out:
                    out.write(reading_text)
                download_url = url_for("extracted_file", filename=outname)
        except Exception as e:
            flash(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}", "error")
            return redirect(request.url)

    return render_template("index.html", reading_text=reading_text, download_url=download_url, pdf_url=pdf_url)

# ---------- AUTH ----------
@app.route("/signup", methods=["POST"])
def signup_submit():
    username = request.form.get("username", "").strip()
    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm  = request.form.get("confirm", "")

    if not username or not email or not password:
        flash("กรอกข้อมูลให้ครบ", "error"); return redirect(url_for("signup_page"))
    if password != confirm:
        flash("รหัสผ่านไม่ตรงกัน", "error"); return redirect(url_for("signup_page"))
    if len(password) < 8:
        flash("รหัสผ่านต้องอย่างน้อย 8 ตัวอักษร", "error"); return redirect(url_for("signup_page"))

    pwd_hash = generate_password_hash(password)
    try:
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT userID FROM user_login WHERE email=%s", (email,))
        if cur.fetchone():
            flash("อีเมลนี้ถูกใช้งานแล้ว", "warning")
            return redirect(url_for("signup_page"))

        cur.execute("""
            INSERT INTO user_login (username, email, password, role)
            VALUES (%s, %s, %s, %s)
        """, (username, email, pwd_hash, "Member"))
        conn.commit()
        flash("สมัครสมาชิกสำเร็จ! เข้าสู่ระบบได้เลย", "success")
        return redirect(url_for("login_page"))
    except mysql.connector.Error as e:
        flash(f"เกิดข้อผิดพลาดฐานข้อมูล: {e}", "error")
        return redirect(url_for("signup_page"))
    finally:
        try: cur.close(); conn.close()
        except: pass

@app.route("/login", methods=["POST"])
def login_submit():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    try:
        conn = get_conn(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT userID, username, password, role FROM user_login WHERE email=%s", (email,))
        user = cur.fetchone()

        if not user or not check_password_hash(user["password"], password):
            flash("อีเมลหรือรหัสผ่านไม่ถูกต้อง", "error")
            return redirect(url_for("login_page"))

        session["user_id"] = user["userID"]
        session["username"] = user["username"]
        session["role"] = user["role"]

        app.logger.info("LOGIN OK user_id=%s", session.get("user_id"))
        flash("เข้าสู่ระบบสำเร็จ", "success")
        return redirect(url_for("index"))
    except mysql.connector.Error as e:
        flash(f"เกิดข้อผิดพลาดฐานข้อมูล: {e}", "error")
        return redirect(url_for("login_page"))
    finally:
        try: cur.close(); conn.close()
        except: pass

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

# ---------- DEBUG/TOOLS ----------
@app.route("/whoami")
def whoami():
    return {
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "role": session.get("role")
    }

@app.route("/forgot", methods=["GET"])
def forgot_page():
    # ใช้ forgot1.html ที่คุณมีอยู่แล้ว
    return render_template("forgot1.html")

# aliases ให้พิมพ์ /forgot1.html หรือ /forgot.html ก็มาได้
@app.route("/forgot1.html")
def _forgot1_alias():
    return redirect(url_for("forgot_page"))

@app.route("/forgot.html")
def _forgot_alias():
    return redirect(url_for("forgot_page"))

# เอ็นด์พอยต์เช็คการเชื่อมต่อฐานข้อมูลอย่างรวดเร็ว
@app.route("/dbping")
def dbping():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close(); conn.close()
        return jsonify(ok=True, server_ip=SERVER_IP)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

# ---------- RUN ----------
if __name__ == "__main__":
    # หมายเหตุ: ถ้าจะให้เครื่องอื่นเข้าเว็บ Flask ได้ ให้ run แบบ host=0.0.0.0
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context="adhoc")
