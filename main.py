import os
import sqlite3
import requests
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from functools import wraps
from flask import Flask, jsonify, render_template, session, redirect, url_for, request
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai

# --- 1. SOZLAMALAR ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "darkline_production_2026")
csrf = CSRFProtect(app)

client = genai.Client(api_key="AIzaSyD_vA-buJCozmyo6P7pquGHBFzvqITNOqM")

# 200 ta ma'lumot uchun manbalar 
RSS_SOURCES = [
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://hackaday.com/blog/feed/",
    "https://cointelegraph.com/rss"
]
WALLET_ADDRESS = "TVJu2skT9L9cvuVhpGDRP63GPWqpp2zqZj"
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
            tier TEXT DEFAULT 'Free')''')
        
        # Xatolarni oldini olish uchun ustunni avtomat qo'shish
        try:
            conn.execute("ALTER TABLE users ADD COLUMN expires_at TIMESTAMP")
            conn.commit()
        except sqlite3.OperationalError:
            pass
            
init_db()

# --- 3. XAVFSIZLIK ---
def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if 'user' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec

# --- 4. SAHIFALAR ---
@app.route("/")
@login_required
def home():
    with get_db_connection() as conn:
        user_data = conn.execute("SELECT tier, expires_at FROM users WHERE username = ?", (session['user'],)).fetchone()
        if user_data and user_data['expires_at']:
            try:
                expiry = datetime.strptime(user_data['expires_at'], '%Y-%m-%d %H:%M:%S.%f')
                if expiry < datetime.now():
                    conn.execute("UPDATE users SET tier = 'Free', expires_at = NULL WHERE username = ?", (session['user'],))
                    conn.commit()
                    session['tier'] = 'Free'
            except (ValueError, TypeError):
                pass
                
    return render_template("index.html", user=session['user'], tier=session.get('tier', 'Free'))

@app.route("/premium")
@login_required
def premium_plans():
    return render_template("pricing.html", user=session['user'], tier=session['tier'])

# --- 5. TO'LOV VA TIZIM ---
@app.route("/api/verify-crypto", methods=['POST'])
@login_required
def verify_crypto():
    tx_hash = request.json.get('tx_hash')
    if not tx_hash: return jsonify({"status": "error", "message": "Hash kod kiritilmadi."})

    try:
        url = f"https://apilist.tronscan.org/api/transaction-info?hash={tx_hash}"
        data = requests.get(url).json()
        
        if data.get('contractRet') == 'SUCCESS' and WALLET_ADDRESS in str(data):
            expiry_date = datetime.now() + timedelta(days=30)
            with get_db_connection() as conn:
                conn.execute("UPDATE users SET tier = 'Premium', expires_at = ? WHERE username = ?", (expiry_date, session['user']))
                conn.commit()
                
            session['tier'] = 'Premium'
            return jsonify({"status": "success", "message": "To'lov tasdiqlandi. Premium faollashdi."})
        else:
            return jsonify({"status": "error", "message": "To'lov topilmadi."})
    except:
        return jsonify({"status": "error", "message": "Tarmoq xatosi."})

# --- 6. MA'LUMOT VA TAHLIL ---
@app.route("/api/feed")
@login_required
def api_feed():
    news_list = []
    for src in RSS_SOURCES:
        try:
            feed = feedparser.parse(src)
            for entry in feed.entries:
                if len(news_list) >= 200: break
                
                img = "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=600&auto=format&fit=crop"
                if 'media_thumbnail' in entry and entry.media_thumbnail: img = entry.media_thumbnail[0]['url']
                elif 'media_content' in entry and entry.media_content: img = entry.media_content[0]['url']
                
                news_list.append({"title": entry.title, "full_link": entry.link, "image": img})
        except: pass
        if len(news_list) >= 200: break
        
    return jsonify({"articles": news_list})

@app.route("/api/full-intel", methods=['POST'])
@login_required
def api_full_intel():
    tier = session.get('tier', 'Free')
    url = request.json.get('url')
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.content, 'html.parser')
        full_text = " ".join([p.get_text() for p in soup.find_all('p')[:15]])
        
        if tier == 'Premium':
            prompt = f"Quyidagi matnni qisqa va aniq faktlarga asoslanib tahlil qilib ber: {full_text}"
            ai_resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            content = f"--- ASOSIY MATN ---\n{full_text}\n\n--- TAHLIL ---\n{ai_resp.text}"
        else:
            content = f"--- ASOSIY MATN ---\n{full_text}\n\n[ Tahlilni ko'rish uchun Premium obuna talab etiladi ]"
            
        return jsonify({"content": content})
    except: 
        return jsonify({"content": "Ma'lumotni olishda xato yuz berdi."}), 500

# --- 7. AVTORIZATSIYA ---
@app.route("/signup", methods=['GET', 'POST'])
@csrf.exempt
def signup():
    if request.method == 'POST':
        u, p = request.form.get('email'), request.form.get('password')
        with get_db_connection() as conn:
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (u, generate_password_hash(p)))
            conn.commit()
        return redirect(url_for('login'))
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
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)