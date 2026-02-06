    import time
import re
from collections import defaultdict
from flask import request, abort

RATE_LIMIT = 30
RATE_WINDOW = 60
EMERGENCY_THRESHOLD = 150

ip_requests = defaultdict(list)
global_stats = {"count": 0, "start": time.time()}

def security_check():
    now = time.time()
    ip = request.remote_addr or "unknown"

    # global traffic
    if now - global_stats["start"] > RATE_WINDOW:
        global_stats["count"] = 0
        global_stats["start"] = now

    global_stats["count"] += 1
    if global_stats["count"] > EMERGENCY_THRESHOLD:
        return True

    # rate limit per IP
    ip_requests[ip] = [t for t in ip_requests[ip] if now - t < RATE_WINDOW]
    ip_requests[ip].append(now)

    if len(ip_requests[ip]) > RATE_LIMIT:
        abort(429)

    # simple SQLi detect
    for v in request.values.values():
        if re.search(r"(union|select|drop|or 1=1)", v, re.I):
            abort(403)

    return False
