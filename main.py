import os
import sqlite3
import feedparser
import requests

from bs4 import BeautifulSoup
from flask import (
    Flask, render_template, request,
    redirect, url_for, session,
    jsonify, render_template_string
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect

from security import security_check

# ================== APP ==================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Ryuzen_Titan_Secret_2026")

csrf = CSRFProtect(app)

# ================== DB (RAILWAY SAFE) ==================
DB_PATH = "/tmp/wallpaper.db"

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    return db

# ================== EMERGENCY PAGE ==================
EMERGENCY_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>SYSTEM CRITICAL</title>
<style>
body{
 background:black;color:red;
 display:flex;justify-content:center;
 align-items:center;height:100vh;
 font-family:monospace;
 text-align:center;
}
</style>
</head>
<body>
<h1>⚠️ EMERGENCY MODE<br>SYSTEM SECURED BY RYUZEN TITAN</h1>
</body>
</html>
"""

# ================== SECURITY (AUTH SAFE) ==================
@app.before_request
def run_security():
    if request.endpoint in (
        "login", "signup", "terms",
        "accept_terms", "static"
    ):
        return

    if security_check():
        return render_template_string(EMERGENCY_HTML), 503

# ================== DECORATORS ==================
def login_required(fn):
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

def terms_required(fn):
    def wrapper(*args, **kwargs):
        if not session.get("terms"):
            return redirect(url_for("terms"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

# ================== ROUTES ==================

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
        try:
            username = request.form.get("username")
            password = request.form.get("password")

            if not username or not password:
                return "Missing fields", 400

            hashed = generate_password_hash(password)

            db = get_db()
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed)
            )
            db.commit()
            db.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            return "Username already exists", 409
        except Exception as e:
            print("SIGNUP ERROR:", e)
            return "Signup failed", 500

    return render_template("signup.html")

# ---------- LOGIN ----------
@csrf.exempt
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")

            db = get_db()
            row = db.execute(
                "SELECT password FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            db.close()

            if row and check_password_hash(row[0], password):
                session.clear()
                session["user"] = username
                session["terms"] = False
                return redirect("/")

            return "Invalid credentials", 401

        except Exception as e:
            print("LOGIN ERROR:", e)
            return "Login failed", 500

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- API FEED (IMAGES ENABLED) ----------
@app.route("/api/feed")
@login_required
@terms_required
def api_feed():
    limit = int(request.args.get("limit", 20))
    items = []
    seen = set()

    FEEDS = [
        ("BBC", "https://feeds.bbci.co.uk/news/rss.xml"),
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
        ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ]

    def get_image_from_page(url):
        try:
            r = requests.get(
                url,
                timeout=5,
                headers={"User-Agent": "Mozilla/5.0"}
            )
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

            image = ""
            if hasattr(e, "media_thumbnail"):
                image = e.media_thumbnail[0].get("url", "")

            if not image:
                image = get_image_from_page(link)

            items.append({
                "source": source,
                "title": getattr(e, "title", ""),
                "link": link,
                "image": image
            })

            if len(items) >= limit:
                break
        if len(items) >= limit:
            break

    return jsonify({
        "count": len(items),
        "articles": items
    })

# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
