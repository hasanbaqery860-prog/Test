#!/usr/bin/env python3
"""
Comprehensive fix for Open edX SSO session issues
This script provides multiple solutions to fix the session handling problem
"""

import os
import sys

def create_session_fix():
    """Create a comprehensive session fix"""
    
    fix_content = '''
# Comprehensive Session Fix for Open edX SSO
# This patch addresses the session cookie domain issue when accessing via IP address

# 1. Fix session cookie settings
SESSION_COOKIE_DOMAIN = None  # Allow cookies for any domain/IP
SESSION_COOKIE_SECURE = False  # Allow HTTP for development
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True  # Force session save
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days

# 2. Ensure proper middleware order
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',  # Must be first
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
] + [m for m in MIDDLEWARE if 'SessionMiddleware' not in m]

# 3. Enhanced session middleware for IP-based access
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse

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

# 4. Replace session middleware
MIDDLEWARE = ['lms.djangoapps.sso_redirect.IPFriendlySessionMiddleware'] + [m for m in MIDDLEWARE if 'SessionMiddleware' not in m]

# 5. Social auth session handling
SOCIAL_AUTH_SESSION_EXPIRATION = False  # Don't expire social auth sessions
SOCIAL_AUTH_FORCE_POST_DISCONNECT = False
SOCIAL_AUTH_SANITIZE_REDIRECTS = False

# 6. Force login after social auth
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'social_django.pipeline.login_user',  # This is crucial!
)

# 7. Auto-create users and force login
SOCIAL_AUTH_AUTO_CREATE_USERS = True
FEATURES['ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING'] = True
FEATURES['ALLOW_PUBLIC_ACCOUNT_CREATION'] = True

# 8. Redirect settings
LOGIN_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_INACTIVE_USER_URL = '/dashboard'

# 9. Username settings
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email', 'first_name', 'last_name']

# 10. Logging for debugging
LOGGING['loggers']['django.contrib.sessions'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}

LOGGING['loggers']['social'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}
'''
    
    return fix_content

def create_middleware_module():
    """Create the middleware module"""
    
    middleware_content = '''
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
'''
    
    return middleware_content

def main():
    """Main function to create the fix"""
    
    print("Creating comprehensive session fix for Open edX SSO...")
    
    # Create the session fix
    session_fix = create_session_fix()
    
    # Create the middleware module
    middleware_module = create_middleware_module()
    
    # Write the files
    with open('session_fix.py', 'w') as f:
        f.write(session_fix)
    
    with open('middleware_fix.py', 'w') as f:
        f.write(middleware_module)
    
    print("✅ Session fix files created:")
    print("  - session_fix.py: Contains the session configuration")
    print("  - middleware_fix.py: Contains the enhanced middleware")
    
    print("\n📋 Next steps:")
    print("1. Apply the session_fix.py configuration to your Django settings")
    print("2. Replace the session middleware with IPFriendlySessionMiddleware")
    print("3. Restart your Open edX services")
    print("4. Clear browser cookies and test the authentication flow")
    
    print("\n🔧 Quick fix commands:")
    print("# Set session cookie domain to None")
    print("tutor config save --set SESSION_COOKIE_DOMAIN=None")
    print("tutor config save --set SESSION_COOKIE_SECURE=False")
    print("tutor config save --set SESSION_SAVE_EVERY_REQUEST=True")
    print("tutor local restart")

if __name__ == "__main__":
    main()