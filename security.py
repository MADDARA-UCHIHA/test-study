import time
import re
from collections import defaultdict, deque
from flask import request, abort

# ================= CONFIG =================
RATE_LIMIT = 60            # 1 IP → 60 request
RATE_WINDOW = 60           # 60 sekund

LOGIN_ATTEMPTS = 5         # 5 marta xato login
LOGIN_WINDOW = 300         # 5 minut
BLOCK_TIME = 900           # 15 minut blok

GLOBAL_LIMIT = 500         # umumiy trafik
GLOBAL_WINDOW = 60

# ================= STATE =================
ip_requests = defaultdict(deque)
login_failures = defaultdict(deque)
blocked_ips = {}
global_requests = deque()

# ================= HELPERS =================
def now():
    return time.time()

def cleanup(queue, window):
    while queue and now() - queue[0] > window:
        queue.popleft()

# ================= CORE =================
def security_check():
    ip = request.headers.get(
        "X-Forwarded-For",
        request.remote_addr
    )
    t = now()

    # -------- BLOCKED IP --------
    if ip in blocked_ips:
        if t < blocked_ips[ip]:
            abort(403)
        else:
            del blocked_ips[ip]

    # -------- GLOBAL RATE --------
    cleanup(global_requests, GLOBAL_WINDOW)
    global_requests.append(t)

    if len(global_requests) > GLOBAL_LIMIT:
        return True  # emergency ON

    # -------- IP RATE LIMIT --------
    cleanup(ip_requests[ip], RATE_WINDOW)
    ip_requests[ip].append(t)

    if len(ip_requests[ip]) > RATE_LIMIT:
        abort(429)

    # -------- LOGIN BRUTE FORCE --------
    if request.endpoint == "login" and request.method == "POST":
        cleanup(login_failures[ip], LOGIN_WINDOW)

        if len(login_failures[ip]) >= LOGIN_ATTEMPTS:
            blocked_ips[ip] = t + BLOCK_TIME
            abort(403)

    # -------- INPUT FILTER --------
    if request.method == "POST":
        for _, value in request.form.items():
            if not is_safe(value):
                abort(403)

    return False  # emergency OFF

# ================= REGISTER LOGIN FAIL =================
def register_login_failure(ip):
    cleanup(login_failures[ip], LOGIN_WINDOW)
    login_failures[ip].append(now())

# ================= INPUT SANITY =================
def is_safe(data):
    if not data:
        return True

    data = str(data)

    patterns = [
        r"(\bor\b|\band\b)\s+\d+=\d+",
        r"union\s+select",
        r"select\s+.*from",
        r"drop\s+table",
        r"--",
        r";",
        r"<script",
        r"</script>",
        r"javascript:",
    ]

    for p in patterns:
        if re.search(p, data, re.IGNORECASE):
            return False

    return True
