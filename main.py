import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, session, render_template_string
import security # security.py dan mantiqni olamiz
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

from security import security_check
app = Flask(__name__)
app.secret_key = "Ryuzen_Titan_Secret_2026"
def get_db():
    return sqlite3.connect("wallpaper.db")

# 🚨 EMERGENCY EKRANI (CSS animatsiyasi bilan)
EMERGENCY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SYSTEM CRITICAL</title>
    <style>
        body { background-color: black; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .warning {
            color: red; font-family: 'Courier New', monospace; font-size: 40px; font-weight: bold;
            animation: blink 0.8s infinite; text-align: center; border: 5px solid red; padding: 20px;
        }
        @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.1;} 100% {opacity: 1;} }
    </style>
</head>
<body>
    <div class="warning">⚠️ EMERGENCY MODE: ATTACK DETECTED ⚠️<br>
    <span style="font-size: 20px;">SYSTEM SECURED BY RYUZEN TITAN</span></div>
</body>
</html>
"""

# 🛡 HAR BIR SO'ROVDAN OLDIN SECURITY TEKSHIRADI
@app.before_request
def run_security():
    # security_check() endi True yoki False qaytaradi
    is_emergency = security.security_check()
    if is_emergency:
        return render_template_string(EMERGENCY_HTML), 503

def get_image_from_article(url):
    try:
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "lxml")
        og = soup.find("meta", property="og:image")
        return og["content"] if og else ""
    except:
        return ""

# --- YO'LLAR (ROUTES) ---

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/shop")
def shop():
    return render_template("shop.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Login urinishi: {email}")
        return jsonify({"status": "received", "email": email})
    return render_template("login.html")

@app.route("/api/feed")
def get_feed():
    limit = int(request.args.get('limit', 10))
    items = []
    seen = set()
    FEEDS = [
        ("BBC", "https://feeds.bbci.co.uk/news/rss.xml"),
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
        ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml")
    ]
    for source, url in FEEDS:
        f = feedparser.parse(url)
        for e in f.entries:
            link = getattr(e, "link", "")
            if not link or link in seen: continue
            seen.add(link)
            image = ""
            if hasattr(e, "media_thumbnail"): image = e.media_thumbnail[0].get("url", "")
            elif not image: image = get_image_from_article(link)
            items.append({"source": source, "title": getattr(e, "title", ""), "link": link, "image": image})
            if len(items) >= limit: break
    return jsonify({"count": len(items), "articles": items})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
    from flask import Flask, render_template, request, redirect, session


app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET"
csrf = CSRFProtect(app)

def db():
    return sqlite3.connect("users.db")

@app.before_request
def protect():
    security_check()

@app.route("/")
def home():
    return "Home page"

# ===== SIGNUP =====
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed = generate_password_hash(password)

        con = db()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        con.commit()
        con.close()

        return redirect("/login")

    return render_template("signup.html")

# ===== LOGIN =====
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = db()
        cur = con.cursor()
        cur.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,)
        )
        row = cur.fetchone()
        con.close()

        if row and check_password_hash(row[0], password):
            session["user"] = username
            return redirect("/")
        return "Login failed", 401

    return render_template("login.html")
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
