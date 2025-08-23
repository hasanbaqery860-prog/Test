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
# SSO Redirect Plugin Settings - FUCK THE MFE, WE'RE GOING DIRECT TO SSO

# COMPLETELY DISABLE THE FUCKING AUTHN MFE
AUTHN_MICROFRONTEND_URL = None
AUTHN_MICROFRONTEND_DOMAIN = None
ENABLE_AUTHN_MICROFRONTEND = False
FEATURES['ENABLE_AUTHN_MICROFRONTEND'] = False

# Disable all the login/register bullshit
FEATURES['DISABLE_ACCOUNT_REGISTRATION'] = True
FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION'] = False
FEATURES['ALLOW_PUBLIC_ACCOUNT_CREATION'] = False
FEATURES['SHOW_REGISTRATION_LINKS'] = False
FEATURES['ENABLE_MKTG_SITE'] = False

# Define the SSO redirect middleware inline
from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponsePermanentRedirect
import logging

logger = logging.getLogger(__name__)

class SSORedirectMiddleware(MiddlewareMixin):
    '''Middleware to redirect authentication requests to SSO'''
    
    def process_request(self, request):
        if not getattr(settings, 'SSO_REDIRECT_ENABLED', True):
            return None
            
        path = request.path.lower().rstrip('/')
        
        # List of auth-related URLs to intercept
        auth_patterns = [
            '/login',
            '/signin', 
            '/register',
            '/signup',
            '/logistration',
            '/authn',
            '/user_api/v1/account/login_session',
            '/api/user/v1/account/login_session',
            '/create_account',
            '/ui/login',
        ]
        
        # Check if this is an auth URL
        is_auth_url = False
        for pattern in auth_patterns:
            if pattern in path or path.endswith(pattern):
                is_auth_url = True
                break
        
        if is_auth_url:
            # Skip if it's an API endpoint we need to keep
            skip_patterns = ['/api/csrf/', '/static/', '/media/', '/admin/', '/oauth2/', '/auth/complete/', '/logout']
            if any(skip in path for skip in skip_patterns):
                return None
            
            # Get the full SSO URL
            sso_url = getattr(settings, 'SSO_REDIRECT_URL', '/auth/login/oidc/')
            
            # Make it absolute if it's relative
            if sso_url.startswith('/'):
                protocol = 'https' if request.is_secure() else 'http'
                host = request.get_host()
                sso_url = f"{protocol}://{host}{sso_url}"
            
            # Check if this is already the SSO URL
            if request.build_absolute_uri().startswith(sso_url):
                return None
            
            # Log the redirect
            logger.info(f"SSO Redirect: INTERCEPTING {request.path} -> {sso_url}")
            
            # Preserve next parameter
            next_url = request.GET.get('next', '')
            if next_url:
                redirect_url = f"{sso_url}?next={next_url}"
            else:
                redirect_url = sso_url
            
            # Use permanent redirect
            return HttpResponsePermanentRedirect(redirect_url)
        
        return None

# Create a module to hold the middleware
import sys
from types import ModuleType

# Create the module
sso_redirect_module = ModuleType('lms.djangoapps.sso_redirect')
sso_redirect_module.SSORedirectMiddleware = SSORedirectMiddleware

# Add to sys.modules
sys.modules['lms.djangoapps.sso_redirect'] = sso_redirect_module

# Insert middleware at the BEGINNING of the stack
MIDDLEWARE = ['lms.djangoapps.sso_redirect.SSORedirectMiddleware'] + MIDDLEWARE

# Force all login URLs to our SSO
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

# Disable enterprise login
FEATURES['DISABLE_ENTERPRISE_LOGIN'] = True

# IMPORTANT: Override the authn MFE URL pattern to prevent legacy from redirecting to MFE
AUTHN_MICROFRONTEND_URL = ''
AUTHN_MICROFRONTEND_DOMAIN = ''

# Override account MFE settings too
ACCOUNT_MICROFRONTEND_URL = None

# Logging
LOGGING['loggers']['lms.djangoapps.sso_redirect'] = {
    'handlers': ['console'],
    'level': 'INFO',
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

# Insert middleware at the beginning for CMS too
MIDDLEWARE = ['lms.djangoapps.sso_redirect.SSORedirectMiddleware'] + MIDDLEWARE
"""),
])

# Production settings to ensure MFE is disabled
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-production-settings", """
# ABSOLUTELY NO MFE FOR AUTH
AUTHN_MICROFRONTEND_URL = None
AUTHN_MICROFRONTEND_DOMAIN = None
ENABLE_AUTHN_MICROFRONTEND = False
"""),
])

# Development settings
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-development-settings", """
# ABSOLUTELY NO MFE FOR AUTH IN DEV
AUTHN_MICROFRONTEND_URL = None
AUTHN_MICROFRONTEND_DOMAIN = None
ENABLE_AUTHN_MICROFRONTEND = False
"""),
])

########################################
# URL OVERRIDES
########################################

# Path to patches directory
patches_dir = pkg_resources.resource_filename(
    "tutorssoredirect", "patches"
)

# Automatically load patches
for patch_file in glob(os.path.join(patches_dir, "*.yml")):
    with open(patch_file) as f:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(patch_file)[:-4], f.read()))