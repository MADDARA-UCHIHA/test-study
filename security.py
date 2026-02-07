import time
import re
from collections import defaultdict
from flask import request, abort

# --------------------
# CONFIG
# --------------------
RATE_LIMIT = 30            # so'rov / RATE_WINDOW
RATE_WINDOW = 60           # sekund
EMERGENCY_THRESHOLD = 150  # global so'rov / RATE_WINDOW

# login brute-force
MAX_LOGIN_FAILS = 6        # ketma-ket xato urinish
LOCKOUT_SECONDS = 10 * 60  # 10 daqiqa blok

# --------------------
# STATE (RAM)
# --------------------
ip_requests = defaultdict(list)  # {ip: [timestamps]}
global_stats = {"count": 0, "start_time": time.time()}

login_fails = defaultdict(list)  # {key(ip or username): [timestamps]}
login_lock = {}                  # {key: lock_until_timestamp}

# --------------------
# HELPERS
# --------------------
_SQL_PATTERNS = [
    r"\bSELECT\b", r"\bUNION\b", r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b",
    r"\bDROP\b", r"OR\s+1=1", r"--", r";--", r"/\*", r"\*/"
]

def clean_input(data):
    """Oddiy DLP: SQLi pattern + XSS minimal escape (form input uchun)."""
    if data is None:
        return data

    s = str(data)

    # SQLi pattern check (basic)
    for pattern in _SQL_PATTERNS:
        if re.search(pattern, s, re.IGNORECASE):
            print(f"[DLP] SQLi attempt blocked: {s!r}")
            abort(403)

    # XSS minimal escape
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    return s

def _key_for_login(username: str | None):
    """Login abuse uchun key: username bo'lsa username, bo'lmasa IP."""
    ip = request.remote_addr or "unknown"
    if username:
        return f"user:{username.lower().strip()}"
    return f"ip:{ip}"

def register_login_failure(username: str | None = None):
    """
    main.py login xato bo'lganda chaqiradi.
    Lock bo'lsa 429/403 qaytaradi.
    """
    now = time.time()
    key = _key_for_login(username)

    # avval lock tekshir
    lock_until = login_lock.get(key)
    if lock_until and now < lock_until:
        abort(429)  # Too Many Requests (temporary lock)

    # window ichidagi fail'larni qoldiramiz
    login_fails[key] = [t for t in login_fails[key] if now - t < LOCKOUT_SECONDS]
    login_fails[key].append(now)

    if len(login_fails[key]) >= MAX_LOGIN_FAILS:
        login_lock[key] = now + LOCKOUT_SECONDS
        print(f"[LOGIN LOCK] {key} locked for {LOCKOUT_SECONDS}s")
        abort(429)

def reset_login_failures(username: str | None = None):
    """Login muvaffaqiyatli bo'lsa tozalash uchun (xohlasang main.py’da chaqirasan)."""
    key = _key_for_login(username)
    login_fails.pop(key, None)
    login_lock.pop(key, None)

# --------------------
# MAIN SECURITY MIDDLEWARE
# --------------------
def security_check():
    """
    Har request boshida chaqiriladi (before_request).
    True qaytsa -> Emergency ON deb hisobla.
    """
    now = time.time()
    ip = request.remote_addr or "unknown"

    # 1) Global traffic monitor
    if now - global_stats["start_time"] > RATE_WINDOW:
        global_stats["count"] = 0
        global_stats["start_time"] = now

    global_stats["count"] += 1
    if global_stats["count"] > EMERGENCY_THRESHOLD:
        print("[EMERGENCY] High traffic detected!")
        return True

    # 2) Per-IP rate limit
    ip_requests[ip] = [t for t in ip_requests[ip] if now - t < RATE_WINDOW]
    ip_requests[ip].append(now)
    if len(ip_requests[ip]) > RATE_LIMIT:
        print(f"[RATE LIMIT] {ip} blocked")
        abort(429)

    # 3) POST input scan
    if request.method == "POST":
        # form-data
        for key in request.form:
            clean_input(request.form[key])
        # json
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            if isinstance(payload, dict):
                for k, v in payload.items():
                    clean_input(v)

    return False
