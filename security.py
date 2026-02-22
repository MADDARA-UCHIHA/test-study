import time
import re
from collections import defaultdict
from typing import Optional, Any
from flask import request, abort

# ================= CONFIG =================
RATE_LIMIT = 30
RATE_WINDOW = 60
EMERGENCY_THRESHOLD = 150

MAX_LOGIN_FAILS = 6
LOCKOUT_SECONDS = 10 * 60

# ================= STATE (RAM) =================
ip_requests = defaultdict(list)
global_stats = {"count": 0, "start_time": time.time()}

login_fails = defaultdict(list)
login_lock = {}

# ================= PATTERNS =================
_SQL_PATTERNS = [
    r"\bSELECT\b", r"\bUNION\b", r"\bDELETE\b", r"\bUPDATE\b",
    r"\bINSERT\b", r"\bDROP\b", r"OR\s+1\s*=\s*1",
    r"--", r"/\*", r"\*/"
]

# ================= HELPERS =================
def clean_input(data: Any):
    """Basic SQLi + XSS check (safe, recursive)."""
    if data is None:
        return

    if isinstance(data, dict):
        for v in data.values():
            clean_input(v)
        return

    if isinstance(data, list):
        for v in data:
            clean_input(v)
        return

    s = str(data)

    for pattern in _SQL_PATTERNS:
        if re.search(pattern, s, re.IGNORECASE):
            print(f"[DLP] SQLi blocked: {s!r}")
            abort(403)

    return s.replace("<", "&lt;").replace(">", "&gt;")

def _key_for_login(username: Optional[str]):
    ip = request.remote_addr or "unknown"
    if username:
        return f"user:{username.lower().strip()}"
    return f"ip:{ip}"

def register_login_failure(username: Optional[str] = None):
    now = time.time()
    key = _key_for_login(username)

    lock_until = login_lock.get(key)
    if lock_until and now < lock_until:
        abort(429)

    login_fails[key] = [t for t in login_fails[key] if now - t < LOCKOUT_SECONDS]
    login_fails[key].append(now)

    if len(login_fails[key]) >= MAX_LOGIN_FAILS:
        login_lock[key] = now + LOCKOUT_SECONDS
        print(f"[LOGIN LOCK] {key} for {LOCKOUT_SECONDS}s")
        abort(429)

def reset_login_failures(username: Optional[str] = None):
    key = _key_for_login(username)
    login_fails.pop(key, None)
    login_lock.pop(key, None)

# ================= MAIN MIDDLEWARE =================
def security_check():
    """
    before_request ichida chaqiriladi.
    True -> Emergency Mode
    False -> normal davom etadi
    """
    now = time.time()
    ip = request.remote_addr or "unknown"

    # -------- GLOBAL TRAFFIC --------
    if now - global_stats["start_time"] > RATE_WINDOW:
        global_stats["count"] = 0
        global_stats["start_time"] = now

    global_stats["count"] += 1
    if global_stats["count"] > EMERGENCY_THRESHOLD:
        print("[EMERGENCY] Global traffic spike")
        return True

    # -------- PER-IP RATE LIMIT --------
    ip_requests[ip] = [t for t in ip_requests[ip] if now - t < RATE_WINDOW]
    ip_requests[ip].append(now)

    if len(ip_requests[ip]) > RATE_LIMIT:
        print(f"[RATE LIMIT] {ip}")
        abort(429)

    # -------- INPUT SCAN --------
    if request.method == "POST":
        for v in request.form.values():
            clean_input(v)

        if request.is_json:
            payload = request.get_json(silent=True)
            clean_input(payload)

    return False
