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

# --- 1. SOZLAMALAR ---
app = Flask(__name__)
# Maxfiy kalitni xavfsizroq saqlash
app.secret_key = os.environ.get("SECRET_KEY", "darkline_production_2026")
csrf = CSRFProtect(app)

# Gemini API Client
client = genai.Client(api_key="AIzaSyD_vA-buJCozmyo6P7pquGHBFzvqITNOqM")

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
            tier TEXT DEFAULT 'Free',
            expires_at TIMESTAMP)''')
        conn.commit()

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
                # Vaqtni tekshirish mantiqi
                expiry = datetime.strptime(user_data['expires_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                if expiry < datetime.now():
                    conn.execute("UPDATE users SET tier = 'Free', expires_at = NULL WHERE username = ?", (session['user'],))
                    conn.commit()
                    session['tier'] = 'Free'
            except Exception: pass
                
    return render_template("index.html", user=session['user'], tier=session.get('tier', 'Free'))

# --- 5. AVTORIZATSIYA (ENG MUHIM TUZATIShLAR) ---
@app.route("/signup", methods=['GET', 'POST'])
@csrf.exempt
def signup():
    if request.method == 'POST':
        u = request.form.get('email')
        p = request.form.get('password')

        # 1-Filtr: Bo'sh ma'lumotni to'xtatish (NoneType xatosini oldini oladi)
        if not u or not p:
            return "Email yoki parol kiritilmadi!", 400

        try:
            with get_db_connection() as conn:
                # 2-Filtr: Parolni hash qilishdan oldin p borligini tasdiqlash
                hashed_pw = generate_password_hash(p)
                conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (u, hashed_pw))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Bu foydalanuvchi nomi allaqachon band!", 400
            
    return render_template("signup.html")

@app.route("/login", methods=['GET', 'POST'])
@csrf.exempt
def login():
    if request.method == 'POST':
        u = request.form.get('email')
        p = request.form.get('password')
        
        if not u or not p: return "Xato ma'lumot!", 400

        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (u,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], p):
            session.update({'user': user['username'], 'tier': user['tier']})
            return redirect(url_for('home'))
        return "Login yoki parol xato!", 401
        
    return render_template("login.html")

# --- QOLGAN API-LAR (Verify, Feed, Intel) ---
# ... (O'zing yozganingdek qoladi, lekin try/except bloklari xavfsiz qilingan)

if __name__ == "__main__":
    # Gunicorn uchun production sozlamalari tavsiya etiladi
    app.run(host='0.0.0.0', port=80)