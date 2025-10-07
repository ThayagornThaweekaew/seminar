from flask import (
    Flask, render_template, redirect, url_for, session, flash,
    jsonify, request, send_from_directory
)
import mysql.connector, os
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from datetime import datetime

# ---------- พาธหลัก ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JS_DIR   = BASE_DIR  # ใช้เสิร์ฟ JS จากโฟลเดอร์เดียวกัน

# ---------- โฟลเดอร์อัปโหลด ----------
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTS = {".pdf"}

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
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.after_request
def _no_cache_html(resp):
    try:
        if resp.mimetype in ("text/html", "application/xhtml+xml"):
            resp.headers["Cache-Control"] = "no-store"
    except Exception:
        pass
    return resp

# ---------- DB CONFIG ----------
SERVER_IP = "192.168.1.4"

BASE_DB = {
    "port": 3306,
    "user": "root",
    "password": "จๅจภจถจุ",
    "database": "seminar",
    "auth_plugin": "mysql_native_password",
    "connection_timeout": 5,
}

def get_conn():
    try:
        return mysql.connector.connect(host="127.0.0.1", **BASE_DB)
    except mysql.connector.Error:
        return mysql.connector.connect(host=SERVER_IP, **BASE_DB)

# ---------- เสิร์ฟไฟล์ JS ----------
@app.route("/js/<path:filename>")
@app.route("/JS/<path:filename>")
def serve_js(filename):
    return send_from_directory(JS_DIR, filename)

# ---------- เสิร์ฟไฟล์อัปโหลด ----------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, mimetype="application/pdf", as_attachment=False)

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

    pdf_url = None

    if request.method == "POST":
        if "file" not in request.files or request.files["file"].filename == "":
            flash("❌ กรุณาเลือกไฟล์", "error")
            return redirect(request.url)

        f = request.files["file"]
        filename = f.filename
        ext = os.path.splitext(filename)[1].lower()

        if ext != ".pdf":
            flash("⚠️ รองรับเฉพาะไฟล์ .pdf เท่านั้น", "warning")
            return redirect(request.url)

        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(path)
        pdf_url = url_for("uploaded_file", filename=filename)

    return render_template("index.html", pdf_url=pdf_url)

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
    return render_template("forgot1.html")

@app.route("/forgot1.html")
def _forgot1_alias():
    return redirect(url_for("forgot_page"))

@app.route("/forgot.html")
def _forgot_alias():
    return redirect(url_for("forgot_page"))

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

# ---------- DB INIT ----------
def init_db():
    try:
        conn = get_conn(); cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                subjectID   INT AUTO_INCREMENT PRIMARY KEY,
                userID      INT NOT NULL,
                subjectname VARCHAR(100) NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS focus_logs (
                logID      INT AUTO_INCREMENT PRIMARY KEY,
                userID     INT NOT NULL,
                subjectID  INT NOT NULL,
                timer      INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subjectID) REFERENCES subjects(subjectID)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
    finally:
        try: cur.close(); conn.close()
        except: pass

init_db()

# ---------- API ----------
from flask import abort

def _require_login():
    if "user_id" not in session:
        abort(401, description="not logged in")
    return session["user_id"]

@app.route("/api/subjects", methods=["GET"])
def api_subjects_list():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT subjectID, subjectname FROM subject ORDER BY subjectname")
        rows = cur.fetchall()
        return jsonify(rows), 200
    finally:
        cur.close(); conn.close()

@app.route("/api/subjects", methods=["POST"])
def api_subjects_add():
    _require_login()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(error="กรุณาใส่ชื่อวิชา"), 400

    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO subject (subjectname) VALUES (%s)", (name,))
        new_id = cur.lastrowid
        conn.commit()
        return jsonify({"subjectID": new_id, "subjectname": name}), 201
    finally:
        cur.close(); conn.close()

@app.route("/api/log", methods=["POST"])
def api_log_add():
    user_id = _require_login()
    data = request.get_json(silent=True) or {}
    subjectID = int(data.get("subjectID") or 0)
    minutes   = int(data.get("timer") or 0)
    if subjectID <= 0 or minutes <= 0:
        return jsonify(error="ข้อมูลไม่ครบ"), 400

    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM subject WHERE subjectID=%s", (subjectID,))
        if not cur.fetchone():
            return jsonify(error="subject ไม่ถูกต้อง"), 400

        cur.execute("""
            INSERT INTO dashboard (userID, subjectID, timer, Date)
            VALUES (%s, %s, %s, NOW())
        """, (user_id, subjectID, minutes))
        conn.commit()
        return jsonify(ok=True)
    finally:
        cur.close(); conn.close()

@app.route("/api/logs", methods=["GET"])
def api_logs_list():
    user_id = _require_login()
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT DATE(p.Date) AS Date, p.timer, s.subjectname
            FROM dashboard p
            JOIN subject s ON s.subjectID = p.subjectID
            WHERE p.userID=%s
            ORDER BY p.Date DESC
        """, (user_id,))
        return jsonify(cur.fetchall())
    finally:
        cur.close(); conn.close()

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
