import sqlite3
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- 1. MA'LUMOTLAR BAZASI (DATABASE) SOZLAMALARI ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Natijalarni dictionary ko'rinishida olish uchun
    return conn

# Jadvallarni yaratish (Faqat bir marta ishga tushadi)
with get_db_connection() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL DEFAULT 1000.0  -- Boshlanishiga virtual pul
        )
    ''')
    conn.commit()

# --- 2. RO'YXATDAN O'TISH (REGISTRATION) ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username va parol kerak!"}), 400
        
    hashed_pw = generate_password_hash(password)
    
    try:
        with get_db_connection() as conn:
            # Parameterized Query - SQL Injection-dan himoya!
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
        return jsonify({"message": "Ro'yxatdan muvaffaqiyatli o'tdingiz!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Bunday foydalanuvchi allaqachon bor!"}), 400

# --- 3. KIRISH (LOGIN) ---
from flask import Flask, render_template, request, redirect, url_for

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # HTML formadagi 'name' atributi bo'yicha ma'lumotni olamiz
        user_email = request.form.get('email')
        user_password = request.form.get('password')
        
        # Bu yerda bazaga tekshirish kodi bo'ladi (Parameterized Query bilan!)
        print(f"Login urunishi: {user_email}") 
        
        return f"Salom {user_email}, tizimga kirishga harakat qildingiz!"
    
    # Agar shunchaki sahifaga kirilsa (GET), HTML faylni ko'rsatamiz
    return render_template('login.html')

# --- 4. QIDIRUV (SEARCH - BIZNING TESTIMIZ UCHUN) ---
@app.route('/api/feed')
def search():
    q = request.args.get('q', '')
    with get_db_connection() as conn:
        # Eski zaif kod o'rniga xavfsiz variant
        query = "SELECT * FROM users WHERE username LIKE ?"
        results = conn.execute(query, ('%' + q + '%',)).fetchall()
        
    return jsonify([dict(row) for row in results])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)


app = Flask(__name__)

@app.route('/login')
def login_page():
    # Bu funksiya templates/login.html faylini qidiradi
    return render_template('login.html')

# Boyagi login mantiqi (API)
@app.route('/api/login', methods=['POST'])
def login_api():
    # ... (bazaga tekshirish kodi)
    pass