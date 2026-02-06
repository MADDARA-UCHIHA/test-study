# security.py
import time
import re
from collections import defaultdict
from flask import request, abort

RATE_LIMIT = 30
RATE_WINDOW = 60
EMERGENCY_THRESHOLD = 150

ip_requests = defaultdict(list)
global_stats = {"count": 0, "start_time": time.time()}

SQL_PATTERNS = [
    r"union\s+select",
    r"or\s+1\s*=\s*1",
    r"drop\s+table",
    r"--",
]

def detect_attack(value):
    for p in SQL_PATTERNS:
        if re.search(p, str(value), re.IGNORECASE):
            print(f"[ALERT] Suspicious input blocked: {value}")
            abort(403)

def security_check():
    now = time.time()
    ip = request.remote_addr

    # Global traffic monitor
    if now - global_stats["start_time"] > RATE_WINDOW:
        global_stats["count"] = 0
        global_stats["start_time"] = now

    global_stats["count"] += 1
    if global_stats["count"] > EMERGENCY_THRESHOLD:
        print("[EMERGENCY] Traffic spike detected")
        abort(503)

    # Rate limit per IP
    ip_requests[ip] = [t for t in ip_requests[ip] if now - t < RATE_WINDOW]
    ip_requests[ip].append(now)

    if len(ip_requests[ip]) > RATE_LIMIT:
        abort(429)

    # Detect suspicious POST input (signal only)
    if request.method == "POST":
        for v in request.form.values():
            detect_attack(v)
