#!/usr/bin/env python3
"""
High-Performance IP and Browser Detection API
Supports web frontend and Android app with API key authentication
"""

import bottle
from bottle import request, response, abort
import json
import re
import hashlib
import time
from functools import wraps
from collections import defaultdict
import logging
from typing import Dict, Any, Optional, Tuple
import ipaddress
from user_agents import parse as ua_parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration
from config import get_config

# Get configuration
config = get_config()

# In-memory cache for performance (consider Redis for production)
request_cache = defaultdict(dict)
api_keys = config.get_api_keys()

# Performance metrics
request_stats = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "start_time": time.time()
}

def api_key_required(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.query.get('api_key')
        
        if not api_key:
            abort(401, "API key required")
        
        if api_key not in api_keys.values():
            abort(403, "Invalid API key")
        
        return f(*args, **kwargs)
    return decorated_function

def get_client_ip() -> str:
    """
    High-performance IP detection with proxy support
    Returns the most likely real client IP
    """
    # Check for forwarded headers (common in proxy setups)
    forwarded_headers = [
        'X-Forwarded-For',
        'X-Real-IP',
        'X-Client-IP',
        'CF-Connecting-IP',  # Cloudflare
        'True-Client-IP'
    ]
    
    for header in forwarded_headers:
        ip = request.headers.get(header)
        if ip:
            # Handle multiple IPs in X-Forwarded-For
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            
            # Validate IP format
            try:
                ipaddress.ip_address(ip)
                return ip
            except ValueError:
                continue
    
    # Fallback to direct connection IP
    return request.environ.get('REMOTE_ADDR', 'unknown')

def parse_user_agent(user_agent: str) -> Dict[str, Any]:
    """
    High-performance user agent parsing with caching
    Returns detailed browser and device information
    """
    if not user_agent:
        return {
            "browser": "Unknown",
            "browser_version": "Unknown",
            "os": "Unknown",
            "os_version": "Unknown",
            "device": "Unknown",
            "is_mobile": False,
            "is_tablet": False,
            "is_pc": True
        }
    
    # Use user-agents library for accurate parsing
    ua = ua_parse(user_agent)
    
    return {
        "browser": ua.browser.family,
        "browser_version": ua.browser.version_string,
        "os": ua.os.family,
        "os_version": ua.os.version_string,
        "device": ua.device.family,
        "is_mobile": ua.is_mobile,
        "is_tablet": ua.is_tablet,
        "is_pc": ua.is_pc,
        "user_agent_string": user_agent
    }

def get_request_metadata() -> Dict[str, Any]:
    """
    Extract comprehensive request metadata with caching
    """
    # Create cache key based on request characteristics
    cache_key = f"{get_client_ip()}_{request.headers.get('User-Agent', '')}_{request.method}_{request.url}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    
    # Check cache first
    if cache_hash in request_cache:
        request_stats["cache_hits"] += 1
        return request_cache[cache_hash]
    
    request_stats["cache_misses"] += 1
    
    # Extract all relevant information
    metadata = {
        "timestamp": time.time(),
        "ip_address": get_client_ip(),
        "user_agent_info": parse_user_agent(request.headers.get('User-Agent', '')),
        "request_method": request.method,
        "request_url": request.url,
        "request_path": request.path,
        "request_headers": dict(request.headers),
        "query_params": dict(request.query),
        "content_type": request.content_type,
        "content_length": request.content_length,
        "remote_port": request.environ.get('REMOTE_PORT'),
        "server_protocol": request.environ.get('SERVER_PROTOCOL'),
        "server_name": request.environ.get('SERVER_NAME'),
        "server_port": request.environ.get('SERVER_PORT'),
        "referer": request.headers.get('Referer'),
        "accept_language": request.headers.get('Accept-Language'),
        "accept_encoding": request.headers.get('Accept-Encoding'),
        "connection": request.headers.get('Connection'),
        "cache_control": request.headers.get('Cache-Control'),
        "user_agent_raw": request.headers.get('User-Agent', ''),
        "client_type": detect_client_type(request.headers.get('User-Agent', ''))
    }
    
    # Cache the result (with TTL in production)
    request_cache[cache_hash] = metadata
    
    return metadata

def detect_client_type(user_agent: str) -> str:
    """
    Detect if request is from web frontend, Android app, or other
    """
    if not user_agent:
        return "unknown"
    
    user_agent_lower = user_agent.lower()
    
    # Android app detection
    if any(pattern in user_agent_lower for pattern in [
        'okhttp', 'retrofit', 'android', 'dalvik', 'java'
    ]):
        return "android_app"
    
    # Web browser detection
    if any(pattern in user_agent_lower for pattern in [
        'chrome', 'firefox', 'safari', 'edge', 'opera', 'webkit'
    ]):
        return "web_browser"
    
    # Mobile browser detection
    if any(pattern in user_agent_lower for pattern in [
        'mobile', 'android', 'iphone', 'ipad', 'blackberry'
    ]):
        return "mobile_browser"
    
    return "other"

def get_performance_stats() -> Dict[str, Any]:
    """Get API performance statistics"""
    uptime = time.time() - request_stats["start_time"]
    cache_hit_rate = (request_stats["cache_hits"] / max(request_stats["total_requests"], 1)) * 100
    
    return {
        "total_requests": request_stats["total_requests"],
        "cache_hits": request_stats["cache_hits"],
        "cache_misses": request_stats["cache_misses"],
        "cache_hit_rate": f"{cache_hit_rate:.2f}%",
        "uptime_seconds": uptime,
        "requests_per_second": request_stats["total_requests"] / max(uptime, 1),
        "cache_size": len(request_cache)
    }

# API Routes

@bottle.route('/api/detect', method=['GET', 'POST'])
@api_key_required
def detect_client():
    """Main endpoint for client detection"""
    request_stats["total_requests"] += 1
    
    try:
        metadata = get_request_metadata()
        
        # Add API key info
        api_key = request.headers.get('X-API-Key') or request.query.get('api_key')
        metadata["api_key_type"] = next((k for k, v in api_keys.items() if v == api_key), "unknown")
        
        response.content_type = 'application/json'
        return json.dumps({
            "success": True,
            "data": metadata,
            "timestamp": time.time()
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error in detect_client: {str(e)}")
        abort(500, f"Internal server error: {str(e)}")

@bottle.route('/api/detect/simple', method=['GET', 'POST'])
@api_key_required
def detect_client_simple():
    """Lightweight endpoint for basic detection"""
    request_stats["total_requests"] += 1
    
    try:
        ip = get_client_ip()
        ua_info = parse_user_agent(request.headers.get('User-Agent', ''))
        client_type = detect_client_type(request.headers.get('User-Agent', ''))
        
        response.content_type = 'application/json'
        return json.dumps({
            "ip": ip,
            "browser": ua_info["browser"],
            "browser_version": ua_info["browser_version"],
            "os": ua_info["os"],
            "os_version": ua_info["os_version"],
            "device_type": client_type,
            "is_mobile": ua_info["is_mobile"]
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error in detect_client_simple: {str(e)}")
        abort(500, f"Internal server error: {str(e)}")

@bottle.route('/api/stats', method=['GET'])
@api_key_required
def get_stats():
    """Get API performance statistics"""
    response.content_type = 'application/json'
    return json.dumps({
        "performance": get_performance_stats(),
        "cache_info": {
            "size": len(request_cache),
            "keys": list(request_cache.keys())[:10]  # First 10 keys
        }
    }, indent=2)

@bottle.route('/api/health', method=['GET'])
def health_check():
    """Health check endpoint (no API key required)"""
    response.content_type = 'application/json'
    return json.dumps({
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    })

@bottle.route('/api/clear-cache', method=['POST'])
@api_key_required
def clear_cache():
    """Clear the request cache"""
    global request_cache
    request_cache.clear()
    
    response.content_type = 'application/json'
    return json.dumps({
        "success": True,
        "message": "Cache cleared successfully"
    })

# Error handlers
@bottle.error(401)
def unauthorized(error):
    response.content_type = 'application/json'
    return json.dumps({
        "error": "Unauthorized",
        "message": "API key required",
        "code": 401
    })

@bottle.error(403)
def forbidden(error):
    response.content_type = 'application/json'
    return json.dumps({
        "error": "Forbidden",
        "message": "Invalid API key",
        "code": 403
    })

@bottle.error(404)
def not_found(error):
    response.content_type = 'application/json'
    return json.dumps({
        "error": "Not Found",
        "message": "Endpoint not found",
        "code": 404
    })

@bottle.error(500)
def internal_error(error):
    response.content_type = 'application/json'
    return json.dumps({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "code": 500
    })

if __name__ == '__main__':
    # Run the application with configuration
    bottle.run(app, 
               host=config.HOST, 
               port=config.PORT, 
               debug=config.DEBUG, 
               reloader=config.RELOADER)
