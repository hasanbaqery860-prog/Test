"""
Tutor plugin for SSO redirect
Disables Open edX login/register and redirects all auth to SSO
"""
from glob import glob
import os
import pkg_resources

from tutor import hooks

from .__about__ import __version__

########################################
# CONFIGURATION
########################################

hooks.Filters.CONFIG_DEFAULTS.add_items([
    # Plugin settings
    ("SSO_REDIRECT_ENABLED", True),
    ("SSO_REDIRECT_URL", "/auth/login/oidc/"),  # Default SSO URL
])

########################################
# PATCHES
########################################

# Add patches to openedx-lms-common-settings
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-common-settings", """
# SSO Redirect Plugin Settings
# Disable standard login/registration
FEATURES['DISABLE_ACCOUNT_REGISTRATION'] = True
FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION'] = False
FEATURES['ALLOW_PUBLIC_ACCOUNT_CREATION'] = False

# Define the SSO redirect middleware inline
from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

class SSORedirectMiddleware(MiddlewareMixin):
    '''Middleware to redirect authentication requests to SSO'''
    
    AUTH_URLS = [
        '/login',
        '/register',
        '/signin',
        '/signup',
        '/user_api/v1/account/login_session/',
        '/api/user/v1/account/login_session/',
        '/user_api/v2/account/login_session/',
        '/api/user/v2/account/login_session/',
        '/auth/login/',
        '/auth/complete/',
        '/create_account',
        '/user_api/v1/account/registration/',
        '/api/user/v1/account/registration/',
        # Authn MFE URLs
        '/authn/login',
        '/authn/register',
        '/authn/login/',
        '/authn/register/',
        '/authn/logistration',
        '/authn/logistration/',
        # Account MFE URLs that might redirect to login
        '/account/settings',
        '/account/settings/',
    ]
    
    ALLOWED_URLS = [
        '/auth/login/oidc/',  # Allow the SSO endpoint itself
        '/auth/complete/',     # OAuth completion URLs
        '/logout',
        '/api/user/v1/account/logout_session/',
        '/admin/',
        '/api/',
        '/static/',
        '/media/',
        '/heartbeat',
        '/robots.txt',
        '/favicon.ico',
        # Allow OAuth2 provider URLs
        '/oauth2/',
        '/auth/complete/azuread-oauth2/',
        '/auth/complete/google-oauth2/',
        '/auth/complete/github/',
        '/auth/complete/facebook/',
    ]
    
    def should_redirect_url(self, path):
        '''Check if URL should be redirected to SSO'''
        # First check if it's an allowed URL
        for allowed in self.ALLOWED_URLS:
            if path.startswith(allowed.rstrip('/')):
                return False
        
        # Then check if it's an auth URL that needs redirect
        for auth_url in self.AUTH_URLS:
            if path == auth_url.rstrip('/') or path.endswith(auth_url.rstrip('/')):
                return True
        
        # Also check for any URL containing these patterns
        auth_patterns = ['login', 'signin', 'register', 'signup', 'logistration']
        for pattern in auth_patterns:
            if pattern in path and '/api/' not in path and '/static/' not in path:
                # Extra check to avoid redirecting API calls or static files
                return True
                
        return False
    
    def process_request(self, request):
        if not getattr(settings, 'SSO_REDIRECT_ENABLED', True):
            return None
            
        path = request.path.rstrip('/')
        
        if self.should_redirect_url(path):
            sso_url = getattr(settings, 'SSO_REDIRECT_URL', '/auth/login/oidc/')
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(f"{sso_url}?next={next_url}")
            else:
                return redirect(sso_url)
        
        return None
    
    def process_response(self, request, response):
        if response.status_code in [301, 302] and hasattr(response, 'url'):
            redirect_url = response.url
            
            # Check if this is redirecting to a login page
            if self.should_redirect_url(redirect_url.split('?')[0]):
                sso_url = getattr(settings, 'SSO_REDIRECT_URL', '/auth/login/oidc/')
                
                # Preserve any 'next' parameter
                if 'next=' in redirect_url:
                    next_param = redirect_url.split('next=')[1].split('&')[0]
                    response['Location'] = f"{sso_url}?next={next_param}"
                else:
                    response['Location'] = sso_url
        
        return response

# Add middleware to the middleware stack
MIDDLEWARE += ['lms.djangoapps.sso_redirect.SSORedirectMiddleware']

# Create a module to hold the middleware
import sys
from types import ModuleType

# Create the module
sso_redirect_module = ModuleType('lms.djangoapps.sso_redirect')
sso_redirect_module.SSORedirectMiddleware = SSORedirectMiddleware

# Add to sys.modules
sys.modules['lms.djangoapps.sso_redirect'] = sso_redirect_module

# Redirect settings
LOGIN_URL = '{{ SSO_REDIRECT_URL }}'
LOGIN_REDIRECT_URL = '/dashboard'
LOGOUT_REDIRECT_URL = '/'

# Disable password reset
FEATURES['ENABLE_PASSWORD_RESET'] = False
FEATURES['ENABLE_CHANGE_USER_PASSWORD_ADMIN'] = False
FEATURES['ENABLE_ACCOUNT_PASSWORD_RESET'] = False

# Disable account activation
FEATURES['ENABLE_ACCOUNT_ACTIVATION'] = False
FEATURES['SKIP_EMAIL_VERIFICATION'] = True

# Registration redirect
REGISTRATION_REDIRECT_URL = '{{ SSO_REDIRECT_URL }}'

# Additional settings
SSO_REDIRECT_ENABLED = {{ SSO_REDIRECT_ENABLED }}
SSO_REDIRECT_URL = '{{ SSO_REDIRECT_URL }}'

# Disable the authn MFE or redirect it
AUTHN_MICROFRONTEND_URL = None
AUTHN_MICROFRONTEND_DOMAIN = None

# Force authentication through main LMS
FEATURES['DISABLE_ENTERPRISE_LOGIN'] = True
"""),
])

# Add patches to openedx-cms-common-settings
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-cms-common-settings", """
# SSO Redirect Plugin Settings for CMS
FEATURES['DISABLE_STUDIO_SSO_OVER_LMS'] = False
FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION'] = False

# Redirect CMS login to SSO
LOGIN_URL = '{{ SSO_REDIRECT_URL }}'
"""),
])

########################################
# TEMPLATE PATCHES
########################################

# Path to patches directory
patches_dir = pkg_resources.resource_filename(
    "tutorssoredirect", "patches"
)

# Automatically load patches
for patch_file in glob(os.path.join(patches_dir, "*.yml")):
    with open(patch_file) as f:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(patch_file)[:-4], f.read()))