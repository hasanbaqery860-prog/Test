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
import logging

logger = logging.getLogger(__name__)

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
        # Account MFE URLs
        '/account/settings',
        '/account/settings/',
        # UI login URLs
        '/ui/login',
        '/ui/login/',
        '/ui/login/login',
        '/ui/register',
        '/ui/signin',
        '/ui/signup',
    ]
    
    ALLOWED_URLS = [
        '/logout',
        '/api/user/v1/account/logout_session/',
        '/admin/',
        '/static/',
        '/media/',
        '/heartbeat',
        '/robots.txt',
        '/favicon.ico',
        '/oauth2/',
        '/auth/complete/',
        '/api/csrf/',
        '/csrf/',
    ]
    
    def is_sso_url(self, path):
        '''Check if this is the SSO URL itself'''
        sso_url = getattr(settings, 'SSO_REDIRECT_URL', '/auth/login/oidc/')
        # Remove query parameters for comparison
        clean_path = path.split('?')[0].rstrip('/')
        clean_sso = sso_url.split('?')[0].rstrip('/')
        return clean_path == clean_sso
    
    def should_redirect_url(self, path):
        '''Check if URL should be redirected to SSO'''
        # Never redirect the SSO URL itself
        if self.is_sso_url(path):
            return False
            
        # First check if it's an allowed URL
        for allowed in self.ALLOWED_URLS:
            if path.startswith(allowed.rstrip('/')):
                return False
        
        # Check if the SSO URL is within the path (to allow OAuth flow)
        sso_url = getattr(settings, 'SSO_REDIRECT_URL', '/auth/login/oidc/')
        if sso_url.rstrip('/') in path:
            return False
        
        # Then check if it's an auth URL that needs redirect
        for auth_url in self.AUTH_URLS:
            auth_url_clean = auth_url.rstrip('/')
            if path == auth_url_clean or path.endswith(auth_url_clean):
                return True
            # Also check if path starts with auth URL (for sub-paths)
            if path.startswith(auth_url_clean + '/'):
                return True
        
        # Also check for any URL containing these patterns
        auth_patterns = ['login', 'signin', 'register', 'signup', 'logistration']
        path_lower = path.lower()
        for pattern in auth_patterns:
            if pattern in path_lower and not any(exclude in path for exclude in ['/api/', '/static/', '/auth/complete/']):
                return True
                
        return False
    
    def process_request(self, request):
        if not getattr(settings, 'SSO_REDIRECT_ENABLED', True):
            return None
            
        path = request.path.rstrip('/')
        
        # Add logging for debugging
        logger.debug(f"SSO Redirect: Checking path {path}")
        
        # Check for redirect loop - if we're already at SSO URL, don't redirect
        if self.is_sso_url(path):
            logger.debug(f"SSO Redirect: Already at SSO URL, not redirecting")
            return None
        
        if self.should_redirect_url(path):
            sso_url = getattr(settings, 'SSO_REDIRECT_URL', '/auth/login/oidc/')
            
            # Check if we're already being redirected from this URL (loop detection)
            referer = request.META.get('HTTP_REFERER', '')
            if referer and path in referer:
                logger.warning(f"SSO Redirect: Potential redirect loop detected for {path}")
                return None
            
            next_url = request.GET.get('next', '')
            if next_url:
                redirect_url = f"{sso_url}?next={next_url}"
            else:
                redirect_url = sso_url
                
            logger.info(f"SSO Redirect: Redirecting {path} to {redirect_url}")
            return redirect(redirect_url)
        
        return None
    
    def process_response(self, request, response):
        if response.status_code in [301, 302] and hasattr(response, 'url'):
            redirect_url = response.url
            
            # Don't process if already redirecting to SSO
            if self.is_sso_url(redirect_url):
                return response
            
            # Check if this is redirecting to a login page
            if self.should_redirect_url(redirect_url.split('?')[0]):
                sso_url = getattr(settings, 'SSO_REDIRECT_URL', '/auth/login/oidc/')
                
                # Preserve any 'next' parameter
                if 'next=' in redirect_url:
                    next_param = redirect_url.split('next=')[1].split('&')[0]
                    response['Location'] = f"{sso_url}?next={next_param}"
                else:
                    response['Location'] = sso_url
                    
                logger.info(f"SSO Redirect: Changed redirect from {redirect_url} to {response['Location']}")
        
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

# Add logging for debugging
LOGGING['loggers']['lms.djangoapps.sso_redirect'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}
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