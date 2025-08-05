#!/usr/bin/env python3
"""
Ultra-High Performance IP and Browser Detection API
Minimal overhead, maximum speed
"""

import bottle
from bottle import request, response, abort
import json
import time
from functools import wraps

# Minimal API keys
API_KEYS = ["web_1234567890abcdef", "android_9876543210fedcba", "other_abcdef1234567890"]

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.query.get('api_key')
        if not api_key or api_key not in API_KEYS:
            abort(401, "Invalid API key")
        return f(*args, **kwargs)
    return decorated_function

def get_ip_fast():
    """Ultra-fast IP detection"""
    # Check X-Forwarded-For first (most common)
    ip = request.headers.get('X-Forwarded-For')
    if ip:
        return ip.split(',')[0].strip()
    
    # Check X-Real-IP
    ip = request.headers.get('X-Real-IP')
    if ip:
        return ip
    
    # Fallback to REMOTE_ADDR
    return request.environ.get('REMOTE_ADDR', 'unknown')

def get_browser_fast(ua):
    """Ultra-fast browser detection"""
    if not ua:
        return "Unknown"
    
    ua_lower = ua.lower()
    if 'chrome' in ua_lower:
        return "Chrome"
    elif 'firefox' in ua_lower:
        return "Firefox"
    elif 'safari' in ua_lower:
        return "Safari"
    elif 'edge' in ua_lower:
        return "Edge"
    elif 'postman' in ua_lower:
        return "Postman"
    elif 'curl' in ua_lower:
        return "curl"
    elif 'python' in ua_lower:
        return "Python"
    else:
        return "Unknown"

@bottle.route('/api/detect', method=['GET', 'POST'])
@api_key_required
def detect():
    """Fast detection"""
    ip = get_ip_fast()
    ua = request.headers.get('User-Agent', '')
    browser = get_browser_fast(ua)
    
    response.content_type = 'application/json'
    return json.dumps({
        "ip": ip,
        "browser": browser,
        "timestamp": time.time()
    })

@bottle.route('/api/detect/simple', method=['GET', 'POST'])
@api_key_required
def detect_simple():
    """Ultra-fast simple detection"""
    ip = get_ip_fast()
    ua = request.headers.get('User-Agent', '')
    browser = get_browser_fast(ua)
    
    response.content_type = 'application/json'
    return json.dumps({
        "ip": ip,
        "browser": browser
    })

@bottle.route('/api/health', method=['GET'])
def health():
    """Health check"""
    response.content_type = 'application/json'
    return json.dumps({"status": "ok"})

if __name__ == '__main__':
    bottle.run(app, host='0.0.0.0', port=8080, debug=False, reloader=False)