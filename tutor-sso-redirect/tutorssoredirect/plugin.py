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
    # OIDC Provider settings
    ("SSO_OIDC_KEY", ""),  # Client ID from Zitadel
    ("SSO_OIDC_SECRET", ""),  # Client Secret from Zitadel
    ("SSO_OIDC_ENDPOINT", ""),  # Zitadel OIDC endpoint
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
FEATURES['DISABLE_ACCOUNT_REGISTRATION'] = False  # Actually ENABLE for SSO users
FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION'] = False
FEATURES['ALLOW_PUBLIC_ACCOUNT_CREATION'] = True  # Allow SSO to create accounts
FEATURES['SHOW_REGISTRATION_LINKS'] = False
FEATURES['ENABLE_MKTG_SITE'] = False

# ENABLE THIRD PARTY AUTH - THIS IS FUCKING IMPORTANT
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
FEATURES['ENABLE_REQUIRE_THIRD_PARTY_AUTH'] = False

# Configure authentication backends - ADD OIDC BACKEND
AUTHENTICATION_BACKENDS = (
    'social_core.backends.open_id_connect.OpenIdConnectAuth',  # Generic OIDC backend
    'django.contrib.auth.backends.ModelBackend',  # Keep default backend as fallback
)

# Social auth settings
SOCIAL_AUTH_STRATEGY = 'third_party_auth.strategy.ConfigurationModelStrategy'
SOCIAL_AUTH_STORAGE = 'third_party_auth.models.OAuth2ProviderConfig'

# OIDC Configuration
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = '{{ SSO_OIDC_ENDPOINT }}'
SOCIAL_AUTH_OIDC_KEY = '{{ SSO_OIDC_KEY }}'
SOCIAL_AUTH_OIDC_SECRET = '{{ SSO_OIDC_SECRET }}'

# Enable the OIDC backend
THIRD_PARTY_AUTH_BACKENDS = ['social_core.backends.open_id_connect.OpenIdConnectAuth']

# Additional OIDC settings
SOCIAL_AUTH_OIDC_SCOPE = ['openid', 'profile', 'email']
SOCIAL_AUTH_OIDC_ID_TOKEN_DECRYPTION_KEY = None
SOCIAL_AUTH_OIDC_USERNAME_KEY = 'preferred_username'
SOCIAL_AUTH_OIDC_USE_NONCE = True

# AUTO CREATE USERS FROM SSO - THIS IS CRITICAL
SOCIAL_AUTH_AUTO_CREATE_USERS = True
FEATURES['ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING'] = True
FEATURES['ALLOW_PUBLIC_ACCOUNT_CREATION'] = True

# User creation pipeline
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
    'third_party_auth.pipeline.ensure_user_information',
    'third_party_auth.pipeline.set_logged_in_cookies',  # THIS IS IMPORTANT FOR SESSION
    'third_party_auth.pipeline.login_analytics',
)

# Session and cookie settings for SSO
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_DOMAIN = ""  # Set to empty to work with all subdomains
SESSION_COOKIE_HTTPONLY = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Ensure login redirect works
LOGIN_URL = '{{ SSO_REDIRECT_URL }}'
LOGIN_REDIRECT_URL = '/dashboard'
LOGOUT_REDIRECT_URL = '/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'

# Username generation from email
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email', 'first_name', 'last_name']

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
        
        # Skip if user is already authenticated
        if request.user.is_authenticated:
            return None
            
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
            skip_patterns = ['/api/csrf/', '/static/', '/media/', '/admin/', '/oauth2/', '/auth/complete/', '/logout', '/auth/login/oidc/']
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

# Log social auth for debugging
LOGGING['loggers']['social'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}

LOGGING['loggers']['third_party_auth'] = {
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
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True

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

# Ensure third-party auth is enabled in production
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
FEATURES['ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING'] = True

# Session settings for production
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'
"""),
])

# Development settings
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-development-settings", """
# ABSOLUTELY NO MFE FOR AUTH IN DEV
AUTHN_MICROFRONTEND_URL = None
AUTHN_MICROFRONTEND_DOMAIN = None
ENABLE_AUTHN_MICROFRONTEND = False

# Ensure third-party auth is enabled in dev
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
FEATURES['ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING'] = True
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