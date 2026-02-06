import os
import sqlite3
import feedparser
from flask_wtf.csrf import CSRFError
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

# ================== DB ==================
def get_db():
    return sqlite3.connect("wallpaper.db")

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
}
</style>
</head>
<body>
<h1>⚠️ EMERGENCY MODE<br>SYSTEM SECURED BY RYUZEN TITAN</h1>
</body>
</html>
"""

# ================== SECURITY ==================
@app.before_request
def run_security():
    if security_check():
        return render_template_string(EMERGENCY_HTML), 503

# ================== LOGIN REQUIRED ==================
def login_required(fn):
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

# ================== TERMS CHECK ==================
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

@app.route("/terms")
@login_required
def terms():
    return render_template("terms.html")

@app.route("/accept-terms", methods=["POST"])
@login_required
def accept_terms():
    session["terms"] = True
    return redirect("/")

# ================== SIGNUP ==================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users(username, password) VALUES (?, ?)",
                (username, password)
            )
            db.commit()
            db.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists", 409

    return render_template("signup.html")

# ================== LOGIN ==================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

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

        return "Login failed", 401

    return render_template("login.html")

# ================== LOGOUT ==================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================== API FEED ==================
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

    for source, url in FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            link = getattr(e, "link", "")
            if not link or link in seen:
                continue

            seen.add(link)
            items.append({
                "source": source,
                "title": getattr(e, "title", ""),
                "link": link
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


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template("csrf_error.html"), 400

