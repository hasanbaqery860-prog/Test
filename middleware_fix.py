
"""
Enhanced session middleware for Open edX SSO
"""
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings

class IPFriendlySessionMiddleware(SessionMiddleware):
    """Session middleware that works with IP addresses"""
    
    def process_request(self, request):
        super().process_request(request)
        
        # Ensure session exists
        if not hasattr(request, 'session') or not request.session:
            request.session = self.SessionStore()
            request.session.create()
        
        # Set session expiry
        if hasattr(request, 'session') and request.session:
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
    
    def process_response(self, request, response):
        response = super().process_response(request, response)
        
        # Fix session cookie for IP access
        if hasattr(request, 'session') and request.session and request.session.modified:
            host = request.get_host()
            if host.replace(':', '').replace('.', '').isdigit():
                # IP address access - set cookie without domain
                response.set_cookie(
                    settings.SESSION_COOKIE_NAME,
                    request.session.session_key,
                    max_age=settings.SESSION_COOKIE_AGE,
                    domain=None,
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=settings.SESSION_COOKIE_HTTPONLY,
                    samesite=settings.SESSION_COOKIE_SAMESITE
                )
        
        return response

class SSORedirectMiddleware:
    """SSO redirect middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Your existing SSO redirect logic here
        return self.get_response(request)
