"""
SSO Redirect Middleware
Intercepts login and registration requests and redirects to SSO
"""
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class SSORedirectMiddleware(MiddlewareMixin):
    """
    Middleware to redirect authentication requests to SSO
    """
    
    # URLs that should be redirected to SSO
    AUTH_URLS = [
        '/login',
        '/register',
        '/signin',
        '/signup',
        '/user_api/v1/account/login_session/',
        '/api/user/v1/account/login_session/',
        '/user_api/v2/account/login_session/',
        '/api/user/v2/account/login_session/',
    ]
    
    # URLs that should be allowed (whitelist)
    ALLOWED_URLS = [
        '/auth/',  # Allow all third-party auth URLs
        '/logout',
        '/api/user/v1/account/logout_session/',
        '/admin/',  # Django admin
        '/api/',  # API endpoints
        '/static/',  # Static files
        '/media/',  # Media files
        '/heartbeat',  # Health check
        '/robots.txt',
        '/favicon.ico',
    ]
    
    def process_request(self, request):
        """
        Process incoming requests and redirect auth requests to SSO
        """
        # Skip if SSO redirect is disabled
        if not getattr(settings, 'SSO_REDIRECT_ENABLED', True):
            return None
            
        path = request.path.rstrip('/')
        
        # Allow whitelisted URLs
        for allowed in self.ALLOWED_URLS:
            if path.startswith(allowed.rstrip('/')):
                return None
        
        # Check if this is an authentication URL that should be redirected
        for auth_url in self.AUTH_URLS:
            if path == auth_url.rstrip('/') or path.endswith(auth_url.rstrip('/')):
                # Get the SSO endpoint from settings
                sso_endpoint = getattr(settings, 'SSO_OIDC_ENDPOINT', '/auth/login/oidc/')
                
                # Preserve the 'next' parameter if it exists
                next_url = request.GET.get('next', '')
                if next_url:
                    return redirect(f"{sso_endpoint}?next={next_url}")
                else:
                    return redirect(sso_endpoint)
        
        return None
    
    def process_response(self, request, response):
        """
        Process responses to handle any additional SSO-related logic
        """
        # Check if this is a redirect to login/register pages
        if response.status_code in [301, 302] and hasattr(response, 'url'):
            redirect_url = response.url
            
            # If redirecting to a login/register page, redirect to SSO instead
            for auth_url in self.AUTH_URLS:
                if auth_url in redirect_url:
                    sso_endpoint = getattr(settings, 'SSO_OIDC_ENDPOINT', '/auth/login/oidc/')
                    
                    # Preserve any 'next' parameter
                    if 'next=' in redirect_url:
                        next_param = redirect_url.split('next=')[1].split('&')[0]
                        response['Location'] = f"{sso_endpoint}?next={next_param}"
                    else:
                        response['Location'] = sso_endpoint
                    break
        
        return response