#!/usr/bin/env python3
"""
High-Performance IP and Browser Detection API - Optimized Version
Minimal information gathering for maximum speed
"""

import bottle
from bottle import request, response, abort
import json
import time
from functools import wraps
from collections import defaultdict
import logging
from typing import Dict, Any
import ipaddress
from user_agents import parse as ua_parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Minimal configuration
API_KEYS = {
    "web": "web_1234567890abcdef",
    "android": "android_9876543210fedcba", 
    "other": "other_abcdef1234567890"
}

# Simple cache for performance
request_cache = {}

def api_key_required(f):
    """Simple API key check"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.query.get('api_key')
        if not api_key or api_key not in API_KEYS.values():
            abort(401, "Invalid API key")
        return f(*args, **kwargs)
    return decorated_function

def get_client_ip() -> str:
    """
    Fast IP detection - only essential headers
    """
    # Check most common headers first
    for header in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']:
        ip = request.headers.get(header)
        if ip:
            # Take first IP if multiple
            ip = ip.split(',')[0].strip()
            try:
                ip_obj = ipaddress.ip_address(ip)
                if not ip_obj.is_loopback:
                    return ip
            except ValueError:
                continue
    
    # Fallback to REMOTE_ADDR
    remote_addr = request.environ.get('REMOTE_ADDR')
    if remote_addr and remote_addr not in ['127.0.0.1', 'localhost', '::1']:
        return remote_addr
    
    return 'unknown'

def parse_user_agent_fast(user_agent: str) -> Dict[str, str]:
    """
    Fast user agent parsing - only essential info
    """
    if not user_agent:
        return {"browser": "Unknown", "os": "Unknown"}
    
    try:
        ua = ua_parse(user_agent)
        return {
            "browser": ua.browser.family,
            "os": ua.os.family
        }
    except:
        return {"browser": "Unknown", "os": "Unknown"}

def detect_client_type_fast(user_agent: str) -> str:
    """
    Fast client type detection - minimal patterns
    """
    if not user_agent:
        return "unknown"
    
    ua_lower = user_agent.lower()
    
    # Quick checks for common patterns
    if any(x in ua_lower for x in ['postman', 'insomnia', 'curl', 'python-requests']):
        return "api_tool"
    if any(x in ua_lower for x in ['okhttp', 'android', 'dalvik']):
        return "android_app"
    if any(x in ua_lower for x in ['chrome', 'firefox', 'safari', 'edge']):
        return "web_browser"
    if any(x in ua_lower for x in ['mobile', 'iphone', 'ipad']):
        return "mobile_browser"
    
    return "other"

# API Routes

@bottle.route('/api/detect', method=['GET', 'POST'])
@api_key_required
def detect_client():
    """Fast detection endpoint - minimal data"""
    try:
        ip = get_client_ip()
        ua_info = parse_user_agent_fast(request.headers.get('User-Agent', ''))
        client_type = detect_client_type_fast(request.headers.get('User-Agent', ''))
        
        response.content_type = 'application/json'
        return json.dumps({
            "ip": ip,
            "browser": ua_info["browser"],
            "os": ua_info["os"],
            "client_type": client_type,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        abort(500, "Internal error")

@bottle.route('/api/detect/simple', method=['GET', 'POST'])
@api_key_required
def detect_client_simple():
    """Ultra-fast simple detection"""
    try:
        ip = get_client_ip()
        ua = request.headers.get('User-Agent', '')
        
        # Fast browser detection
        browser = "Unknown"
        if 'chrome' in ua.lower():
            browser = "Chrome"
        elif 'firefox' in ua.lower():
            browser = "Firefox"
        elif 'safari' in ua.lower():
            browser = "Safari"
        elif 'edge' in ua.lower():
            browser = "Edge"
        
        response.content_type = 'application/json'
        return json.dumps({
            "ip": ip,
            "browser": browser
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        abort(500, "Internal error")

@bottle.route('/api/health', method=['GET'])
def health_check():
    """Minimal health check"""
    response.content_type = 'application/json'
    return json.dumps({"status": "ok"})

# Error handlers
@bottle.error(401)
def unauthorized(error):
    response.content_type = 'application/json'
    return json.dumps({"error": "Unauthorized"})

@bottle.error(500)
def internal_error(error):
    response.content_type = 'application/json'
    return json.dumps({"error": "Internal error"})

if __name__ == '__main__':
    bottle.run(app, host='0.0.0.0', port=8080, debug=False, reloader=False)