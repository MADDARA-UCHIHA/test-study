import os
import sqlite3
import requests
import feedparser
import google.generativeai as genai
from bs4 import BeautifulSoup
from functools import wraps
from flask import Flask, jsonify, render_template, session, redirect, url_for, request, render_template_string
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

# --- INITIALIZATION ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "darkline_master_key_2026_titan")
csrf = CSRFProtect(app)

# --- AI CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyD_vA-buJCozmyo6P7pquGHBFzvqITNOqM" 
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- DATABASE SETUP ---
DB_PATH = "darkline_v2.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE NOT NULL, 
            password_hash TEXT NOT NULL, 
            tier TEXT DEFAULT 'Free',
            terms_accepted INTEGER DEFAULT 0)''')
        conn.commit()

init_db()

# --- SECURITY UTILS ---
EMERGENCY_HTML = """
<body style="background:black;color:#0f0;display:flex;align-items:center;justify-content:center;height:100vh;font-family:monospace;text-align:center;">
<div><h1>⚠️ SYSTEM SECURED BY RYUZEN </h1><p>ACCESS TEMPORARILY RESTRICTED BY NEURAL SHIELD.</p></div>
</body>
"""

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- NEWS ENGINE ---
RSS_SOURCES = [
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"
]

def scrap_full_text(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraphs = soup.find_all('p')
        content = "\n\n".join([p.get_text() for p in paragraphs if len(p.get_text()) > 30])
        return content if content else "Data extraction failed."
    except:
        return "Connection lost. Darkline target unreachable."

# --- ROUTES ---

@app.route("/")
@login_required
def home():
    return render_template("index.html", user=session.get('user'), tier=session.get('tier'))

@app.route("/api/feed")
@login_required
def api_feed():
    articles = []
    for url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries[:20]: # 1000 ta uchun limitni oshirish mumkin
            clean_summary = BeautifulSoup(entry.get('summary', ''), "html.parser").get_text()
            articles.append({
                "title": entry.title,
                "summary": clean_summary[:120] + "...",
                "image": f"https://picsum.photos/400/250?random={hash(entry.title)}",
                "full_link": entry.link
            })
    return jsonify({"articles": articles, "tier": session.get('tier')})

@app.route("/api/deep-analyze", methods=['POST'])
@login_required
def deep_analyze():
    tier = session.get('tier', 'Free')
    if tier not in ['Pro', 'Ultimate']:
        return jsonify({"error": "DARKLINE PRO/ULTIMATE CLEARANCE REQUIRED."}), 403
    
    data = request.json
    full_text = scrap_full_text(data.get('url'))
    
    prompt = f"IDENTITY: Gemini Darkline Core. MANDATE: Analyze for cyber-risks and strategy. Master, here is the intel: {full_text}"
    
    try:
        response = ai_model.generate_content(prompt)
        return jsonify({"analysis": response.text.strip()})
    except:
        return jsonify({"error": "Satellite link unstable."}), 500

# --- AUTH SYSTEM ---

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_input = request.form.get('email')
        pwd = request.form.get('password')
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (user_input,)).fetchone()
        if user and check_password_hash(user['password_hash'], pwd):
            session.update({'user': user['username'], 'tier': user['tier']})
            return redirect(url_for('home'))
        return "Invalid Credentials", 401
    return render_template("login.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_input = request.form.get('email')
        pwd = request.form.get('password')
        hashed = generate_password_hash(pwd)
        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (user_input, hashed))
                conn.commit()
            session.update({'user': user_input, 'tier': 'Free'})
            return redirect(url_for('home'))
        except:
            return "User already exists", 409
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))
return render_template("index.html")
if __name__ == "__main__":
    # Serverni professional Waitress orqali ishga tushiramiz
    from waitress import serve
    print("DARKLINE TITAN CORE ONLINE ON PORT 8080")
    serve(app, host="0.0.0.0", port=8080)