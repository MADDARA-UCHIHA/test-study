import os
import sqlite3
import requests
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from functools import wraps
from flask import Flask, jsonify, render_template, session, redirect, url_for, request, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai
from dotenv import load_dotenv

# --- 1. SOZLAMALAR ---
load_dotenv() # .env faylini yuklash [cite: 2026-02-24]
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "darkline_master_key_2026")
csrf = CSRFProtect(app)

# Gemini API Client - Endi xavfsiz! [cite: 2026-02-25]
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

RSS_SOURCES = [
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://hackaday.com/blog/feed/",
    "https://cointelegraph.com/rss"
]
DB_PATH = "darkline_v2.db"

# --- 2. MA'LUMOTLAR BAZASI ---
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
            expires_at TIMESTAMP)''')
        
        try:
            conn.execute('''CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT,
                image TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        except sqlite3.OperationalError:
            pass
        conn.commit()

init_db()

# --- 3. XAVFSIZLIK ---
def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if 'user' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec

# --- 4. ASOSIY YO'LLAR (ROUTES) ---

@app.route("/")
@login_required
def home():
    # Tizim statusi endi kodingdan emas, keshdan keladi [cite: 2026-02-25]
    with get_db_connection() as conn:
        user_data = conn.execute("SELECT tier, expires_at FROM users WHERE username = ?", (session['user'],)).fetchone()
        if user_data and user_data['expires_at']:
            try:
                expiry = datetime.strptime(user_data['expires_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                if expiry < datetime.now():
                    conn.execute("UPDATE users SET tier = 'Free', expires_at = NULL WHERE username = ?", (session['user'],))
                    conn.commit()
                    session['tier'] = 'Free'
            except Exception: pass
            
    return render_template("index.html", user=session['user'], tier=session.get('tier', 'Free'))

@app.route("/pricing")
@login_required
def pricing():
    return render_template("pricing.html", user=session['user'], tier=session.get('tier', 'Free'))

@app.route("/terms")
def terms():
    return render_template("terms.html") 

# --- 5. AVTORIZATSIYA ---

@app.route("/signup", methods=['GET', 'POST'])
@csrf.exempt
def signup():
    if request.method == 'POST':
        u = request.form.get('email')
        p = request.form.get('password')
        if not u or not p: return "Email/Password bo'sh!", 400
        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                            (u, generate_password_hash(p)))
                conn.commit()
            return redirect(url_for('terms')) 
        except sqlite3.IntegrityError: return "Bu email band!", 400
    return render_template("signup.html")

@app.route("/login", methods=['GET', 'POST'])
@csrf.exempt
def login():
    if request.method == 'POST':
        u, p = request.form.get('email'), request.form.get('password')
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (u,)).fetchone()
        if user and check_password_hash(user['password_hash'], p):
            session.update({'user': user['username'], 'tier': user['tier']})
            return redirect(url_for('home'))
        return "Xato login yoki parol!", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- 6. API VA KESH (YANGILIKLAR) ---

@app.route("/api/update-cache")
def update_cache():
    news_list = []
    for src in RSS_SOURCES:
        try:
            feed = feedparser.parse(src)
            for entry in feed.entries[:25]:
                img = "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=600"
                news_list.append((entry.title, entry.link, img))
        except: continue
    
    if news_list:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM news_cache")
            conn.executemany("INSERT INTO news_cache (title, link, image) VALUES (?, ?, ?)", news_list)
            conn.commit()
    return jsonify({"status": "ok", "count": len(news_list)})

@app.route("/api/feed")
@login_required
def api_feed():
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM news_cache ORDER BY id DESC").fetchall()
    return jsonify({"articles": [dict(r) for r in rows]})

# --- 7. AI TAHLILI ---
@app.route("/api/full-intel", methods=['POST'])
@login_required
def api_full_intel():
    tier = session.get('tier', 'Free')
    url = request.json.get('url')
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.content, 'html.parser')
        full_text = " ".join([p.get_text() for p in soup.find_all('p')[:10]])
        
        if tier in ['Pro', 'Ultimate', 'Premium']:
            prompt = f"Quyidagi matnni qisqa va aniq faktlarga asoslanib tahlil qilib ber: {full_text}"
            ai_resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            content = f"--- ASOSIY MATN ---\n{full_text}\n\n--- TAHLIL ---\n{ai_resp.text}"
        else:
            content = f"--- ASOSIY MATN ---\n{full_text}\n\n[ Tahlilni ko'rish uchun Premium obuna talab etiladi ]"
            
        return jsonify({"content": content})
    except Exception as e: 
        return jsonify({"content": "Ma'lumotni olishda xato yuz berdi."}), 500

# --- 8. SHOPIFY WEBHOOK ---

@app.route("/webhook/shopify", methods=['POST'])
@csrf.exempt
def shopify_webhook():
    data = request.get_json()
    topic = request.headers.get('X-Shopify-Topic')
    
    if topic == 'orders/paid':
        email = data.get('email')
        line_items = data.get('line_items', [])
        for item in line_items:
            tier_name = 'Free'
            if "Pro" in item['name']: tier_name = 'Pro'
            elif "Ultimate" in item['name']: tier_name = 'Ultimate'
            
            if tier_name != 'Free':
                expiry = datetime.now() + timedelta(days=30)
                with get_db_connection() as conn:
                    conn.execute("UPDATE users SET tier = ?, expires_at = ? WHERE username = ?", 
                                (tier_name, expiry.strftime('%Y-%m-%d %H:%M:%S'), email))
                    conn.commit()
        return jsonify({"success": True}), 200
    return jsonify({"ignored": True}), 200

if __name__ == "__main__":
    # Port 80 va 0.0.0.0 orqali dunyoga eshik ochamiz [cite: 2026-02-23]
    app.run(host='0.0.0.0', port=80)