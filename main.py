import os
import sqlite3
import feedparser
import requests
from bs4 import BeautifulSoup
# main.py
from koyeb import Sandbox

sandbox = Sandbox.create(
  image="ubuntu",
  name="hello-world",
  wait_ready=True,
)

result = sandbox.exec("echo 'Hello World'")
print(result.stdout.strip())

sandbox.delete()
from flask import (
    Flask, render_template, request,
    redirect, url_for, session,
    jsonify, render_template_string
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect

from security import security_check, register_login_failure

# ================= APP =================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Ryuzen_Titan_Secret_2026")
csrf = CSRFProtect(app)

# ================= DB =================
DB_PATH = "/tmp/wallpaper.db"

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    return db

# ================= EMERGENCY =================
EMERGENCY_HTML = """
<!DOCTYPE html>
<html>
<body style="background:black;color:red;
display:flex;align-items:center;justify-content:center;
height:100vh;font-family:monospace;">
<h1>⚠️ EMERGENCY MODE<br>SYSTEM SECURED BY RYUZEN TITAN</h1>
</body>
</html>
"""

# ================= SECURITY =================
@app.before_request
def run_security():
  if request.endpoint in (
    "signup", "terms",
    "accept_terms", "static"
):
    return

    if security_check():
        return render_template_string(EMERGENCY_HTML), 503

# ================= DECORATORS =================
def login_required(fn):
    def wrapper(*a, **kw):
        if "user" not in session:
            return redirect("/login")
        return fn(*a, **kw)
    wrapper.__name__ = fn.__name__
    return wrapper

def terms_required(fn):
    def wrapper(*a, **kw):
        if not session.get("terms"):
            return redirect("/terms")
        return fn(*a, **kw)
    wrapper.__name__ = fn.__name__
    return wrapper

# ================= ROUTES =================
@app.route("/")
@login_required
@terms_required
def home():
    return render_template("index.html")

@app.route("/shop")
def shop():
    return render_template("shop.html")

# ---------- TERMS ----------
@app.route("/terms")
@login_required
def terms():
    return render_template("terms.html")

@csrf.exempt
@app.route("/accept-terms", methods=["POST"])
@login_required
def accept_terms():
    session["terms"] = True
    return redirect("/")

# ---------- SIGNUP ----------
@csrf.exempt
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Missing fields", 400

        hashed = generate_password_hash(password)

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, hashed)
            )
            db.commit()
            db.close()
        except sqlite3.IntegrityError:
            return "Email already registered", 409

        # AUTO LOGIN
        session.clear()
        session["user"] = email
        session["terms"] = False
        return redirect("/")

    return render_template("signup.html")

# ---------- LOGIN ----------
@csrf.exempt
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        db = get_db()
        row = db.execute(
            "SELECT password FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        db.close()

        if row and check_password_hash(row[0], password):
            session.clear()
            session["user"] = email
            session["terms"] = False
            return redirect("/")

        # ❗ LOGIN XATO — BRUTE FORCE HISOBLANADI
        register_login_failure(
            request.headers.get("X-Forwarded-For", request.remote_addr)
        )
        return "Invalid email or password", 401

    return render_template("login.html")
@app.route('/signup', methods=['POST'])
def signup():
    data = request.form.to_dict()
    
    # Hammasini bitta matnga yig'amiz va Gemini'ga beramiz
    full_input = f"User: {data.get('username')}, Email: {data.get('email')}"
    
    if titan_ai_check(full_input):
        return "<h1>🚨 TITAN AI: Hujum to'xtatildi! Siz bloklandingiz.</h1>", 403

    # ... qolgan kod ...
# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- NEWS API ----------
@app.route("/api/feed")
@login_required
@terms_required
def api_feed():
    limit = int(request.args.get("limit", 20))
    items, seen = [], set()

    FEEDS = [
        ("BBC", "https://feeds.bbci.co.uk/news/rss.xml"),
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
        ("BBC Tech", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ]

    def get_image(url):
        try:
            r = requests.get(url, timeout=5,
                             headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            og = soup.find("meta", property="og:image")
            return og["content"] if og else ""
        except:
            return ""

    for source, feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        for e in feed.entries:
            link = getattr(e, "link", "")
            if not link or link in seen:
                continue
            seen.add(link)

            img = ""
            if hasattr(e, "media_thumbnail"):
                img = e.media_thumbnail[0].get("url", "")
            if not img:
                img = get_image(link)

            items.append({
                "source": source,
                "title": getattr(e, "title", ""),
                "link": link,
                "image": img
            })
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break

    return jsonify({"count": len(items), "articles": items})

# ================= RUN =================
if __name__ == "__main__":
    # Koyeb PORT o'zgaruvchisini o'zi beradi, biz uni o'qib olishimiz kerak
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)




