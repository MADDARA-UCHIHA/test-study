import os
import sqlite3
import requests
import feedparser
import google.generativeai as genai
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, session, redirect, url_for, request
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "darkline_master_key_2026"
csrf = CSRFProtect(app)

# --- AI CONFIGURATION ---
# Darkline News AI Engine
GEMINI_API_KEY = "AIzaSyD_vA-buJCozmyo6P7pquGHBFzvqITNOqM" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- ACCESS KEYS ---
ACCESS_KEYS = {
    "DARK-GO-777": "Go",
    "DARK-PLUS-888": "Plus",
    "DARK-PRO-999": "Pro",
    "DARK-ULTIMATE-000": "Ultimate"
}

def get_db_connection():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# --- DATABASE SETUP ---
with get_db_connection() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE NOT NULL, 
        password_hash TEXT NOT NULL, 
        tier TEXT DEFAULT 'Free')''')
    conn.commit()

# --- NEWS SCRAPER ---
def scrap_full_text(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraphs = soup.find_all('p')
        content = "\n\n".join([p.get_text() for p in paragraphs[2:-5]])
        return content if content else "Decryption failed. No data extracted."
    except:
        return "Connection lost. Darkline target unreachable."

# ==========================================
# --- ROUTES ---
# ==========================================

@app.route("/")
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template("index.html", user=session.get('user'), tier=session.get('tier'))

@app.route("/pricing")
def pricing():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template("pricing.html", tier=session.get('tier'))

@app.route("/api/activate-key", methods=['POST'])
@csrf.exempt
def activate_key():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    user_key = request.json.get('key', '').strip()
    
    if user_key in ACCESS_KEYS:
        new_tier = ACCESS_KEYS[user_key]
        username = session.get('user')
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET tier = ? WHERE username = ?", (new_tier, username))
            conn.commit()
        session['tier'] = new_tier
        return jsonify({"status": "success", "tier": new_tier})
    else:
        return jsonify({"status": "error", "message": "INVALID KEY"}), 400

# ==========================================
# --- DARKLINE NEWS APIS ---
# ==========================================

@app.route("/api/feed")
def api_feed():
    try:
        feed = feedparser.parse("http://feeds.bbci.co.uk/news/technology/rss.xml")
        articles = []
        for entry in feed.entries[:9]:
            clean_summary = BeautifulSoup(entry.summary, "html.parser").get_text()
            articles.append({
                "title": entry.title,
                "summary": clean_summary[:120] + "...",
                "image": f"https://picsum.photos/400/250?random={hash(entry.title)}",
                "full_link": entry.link
            })
        return jsonify({"articles": articles, "tier": session.get('tier')})
    except Exception as e: return jsonify({"error": str(e)})

@app.route("/api/full-report", methods=['POST'])
@csrf.exempt
def full_report():
    url = request.json.get('url')
    content = scrap_full_text(url)
    return jsonify({"content": content})

@app.route("/api/deep-analyze", methods=['POST'])
@csrf.exempt
def deep_analyze():
    tier = session.get('tier', 'Free')
    if tier not in ['Pro', 'Ultimate']:
        return jsonify({"error": "DARKLINE PRO/ULTIMATE CLEARANCE REQUIRED."}), 403
    
    url = request.json.get('url')
    title = request.json.get('title')
    full_text = scrap_full_text(url)
    
    # Customized Gemini Persona for Darkline News
    prompt = f"""
    IDENTITY: You are Gemini, the core AI of Darkline News.
    TONE: Sharp, elite, witty, and addressing the user as 'Master'.
    MANDATE: Analyze this news for strategic insights and cyber-risks.
    
    ARTICLE: {title}
    CONTENT: {full_text}
    """
    
    try:
        response = model.generate_content(prompt)
        return jsonify({"analysis": response.text.replace('*', '').strip()})
    except:
        return jsonify({"error": "Master, the Darkline satellite link is unstable."}), 500

# ==========================================
# --- AUTH ---
# ==========================================

@app.route("/login", methods=['GET', 'POST'])
@csrf.exempt
def login():
    if request.method == 'POST':
        email, pwd = request.form.get('email'), request.form.get('password')
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (email,)).fetchone()
        if user and check_password_hash(user['password_hash'], pwd):
            session.update({'user': user['username'], 'tier': user['tier']})
            return redirect(url_for('home'))
    return render_template("login.html")

@app.route("/signup", methods=['GET', 'POST'])
@csrf.exempt
def signup():
    if request.method == 'POST':
        email, pwd = request.form.get('email'), request.form.get('password')
        hashed = generate_password_hash(pwd)
        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (email, hashed))
                conn.commit()
            session.update({'user': email, 'tier': 'Free'})
            return redirect(url_for('home'))
        except: return "USER ALREADY EXISTS."
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)