import os
import sqlite3
import feedparser
import requests
from bs4 import BeautifulSoup
from functools import wraps
import stripe
from flask import (
    Flask, request, render_template, redirect,
    url_for, session, jsonify, render_template_string
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

from security import security_check, register_login_failure

# ================= APP =================
stripe.api_key = "sk_test_XXXXXXXXXXXXXXXX"
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Ryuzen_Secret_2026")

# CSRF (MUHIM: app'ga ulash)
csrf = CSRFProtect(app)

# ================= DB =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "wallpaper.db")

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
height:100vh;font-family:monospace;text-align:center;">
<h1>⚠️ EMERGENCY MODE<br>SYSTEM SECURED BY RYUZEN TITAN</h1>
</body>
</html>
"""

# ================= SECURITY =================
@app.before_request
def run_security():
    # login/signup/terms/static’da rate-limitni ishlatmaymiz
    if request.endpoint in ("signup", "login", "terms", "accept_terms", "static"):
        return

    if security_check():
        return render_template_string(EMERGENCY_HTML), 503

# ================= DECORATORS =================
def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*a, **kw)
    return wrapper

def terms_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("terms"):
            return redirect(url_for("terms"))
        return fn(*a, **kw)
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

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

# ---------- TERMS ----------
@app.route("/terms")
@login_required
def terms():
    return render_template("terms.html")

@app.route("/accept-terms", methods=["POST"])
@login_required
def accept_terms():
    session["terms"] = True
    return redirect(url_for("home"))

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

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

        session.clear()
        session["user"] = email
        session["terms"] = False
        return redirect(url_for("home"))

    return render_template("signup.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

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
            return redirect(url_for("home"))

        register_login_failure(email)
        return "Invalid email or password", 401

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

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
            r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
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
@app.route("/pay/<plan>")
@app.route("/success")
@login_required
def success():
    # bu yerda DB ga plan yozasan
    return "<h1>✅ Premium aktiv!</h1>"

@login_required
def pay(plan):
    PRICE_IDS = {
        "go": "price_xxx",
        "plus": "price_xxx",
        "pro": "price_xxx",
        "ultimate": "price_xxx",
    }

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{
            "price": PRICE_IDS[plan],
            "quantity": 1
        }],
        success_url="http://localhost:8000/success",
        cancel_url="http://localhost:8000/pricing",
        customer_email=session.get("user")
    )
    return redirect(session.url, code=303)

# ================= RUN =================
if __name__ == "__main__":
    print("Server running on http://localhost:8000")
    from waitress import serve
    serve(app, host="0.0.0.0", port=8000)
