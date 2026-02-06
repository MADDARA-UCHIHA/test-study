import os
import sqlite3
import feedparser

from flask import (
    Flask, render_template, request,
    redirect, url_for, session,
    jsonify, render_template_string
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect

from security import security_check

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Ryuzen_Titan_Secret_2026")
csrf = CSRFProtect(app)

# ---------- DB ----------
def get_db():
    return sqlite3.connect("wallpaper.db")

# ---------- EMERGENCY ----------
EMERGENCY_HTML = """
<html><body style="background:black;color:red;
display:flex;justify-content:center;align-items:center;height:100vh;">
<h1>⚠️ EMERGENCY MODE<br>SYSTEM SECURED BY RYUZEN TITAN</h1>
</body></html>
"""

@app.before_request
def run_security():
    if security_check():
        return render_template_string(EMERGENCY_HTML), 503

# ---------- LOGIN REQUIRED ----------
def login_required(fn):
    def wrap(*a, **kw):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*a, **kw)
    wrap.__name__ = fn.__name__
    return wrap

# ---------- ROUTES ----------
@app.route("/")
@login_required
def home():
    feed = feedparser.parse("https://feeds.bbci.co.uk/news/rss.xml")
    return render_template("index.html", articles=feed.entries[:20])

@app.route("/shop")
def shop():
    return render_template("shop.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u = request.form["username"]
        p = generate_password_hash(request.form["password"])
        db = get_db()
        db.execute("INSERT INTO users(username,password) VALUES(?,?)", (u,p))
        db.commit()
        db.close()
        return redirect("/login")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        db = get_db()
        row = db.execute(
            "SELECT password FROM users WHERE username=?",(u,)
        ).fetchone()
        db.close()
        if row and check_password_hash(row[0], p):
            session["user"] = u
            return redirect("/")
        return "Login failed", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/api/feed")
@login_required
def api_feed():
    feed = feedparser.parse ("BBC", "https://feeds.bbci.co.uk/news/rss.xml"),
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
        ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml")
    return jsonify([{"title":e.title,"link":e.link} for e in feed.entries[:10]])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
