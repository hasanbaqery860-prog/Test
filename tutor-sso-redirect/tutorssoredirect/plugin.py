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
# SSO Redirect Plugin Settings - Enable MFE with auto-redirect to SSO

# Enable the authn MFE
AUTHN_MICROFRONTEND_URL = "http://91.107.146.137:1999/authn"
AUTHN_MICROFRONTEND_DOMAIN = "91.107.146.137:1999"
ENABLE_AUTHN_MICROFRONTEND = True
FEATURES['ENABLE_AUTHN_MICROFRONTEND'] = True

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

# Social auth settings - Use the default Django storage instead of the problematic one
SOCIAL_AUTH_STRATEGY = 'social_django.strategy.DjangoStrategy'
SOCIAL_AUTH_STORAGE = 'social_django.models.DjangoStorage'

# OIDC Configuration
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = '{{ SSO_OIDC_ENDPOINT }}'
SOCIAL_AUTH_OIDC_KEY = '{{ SSO_OIDC_KEY }}'
SOCIAL_AUTH_OIDC_SECRET = '{{ SSO_OIDC_SECRET }}'

# Enable the OIDC backend
THIRD_PARTY_AUTH_BACKENDS = ['social_core.backends.open_id_connect.OpenIdConnectAuth']

# Configure MFE to auto-redirect to OIDC
# This makes the MFE immediately redirect to the SSO provider
AUTHN_REDIRECT_TO_OIDC = True
AUTHN_DEFAULT_REDIRECT_URL = '/auth/login/oidc/'
AUTHN_OIDC_PROVIDER_SLUG = 'oidc'

# Skip showing login/signup forms completely
AUTHN_MINIMAL_HEADER = True
FEATURES['SKIP_EMAIL_VALIDATION'] = True
FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] = False

# Hide all login form elements and force immediate redirect
HIDE_USERNAME_EMAIL_FIELD = True
HIDE_PASSWORD_FIELD = True
THIRD_PARTY_AUTH_ONLY_PROMPT = True
THIRD_PARTY_AUTH_ONLY_HINT = ""

# Force immediate SSO redirect without showing any forms
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
ALWAYS_REDIRECT_TO_THIRD_PARTY_AUTH = True

# Disable local login completely
FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION'] = False
FEATURES['ALLOW_PUBLIC_ACCOUNT_CREATION'] = False
FEATURES['ENABLE_THIRD_PARTY_AUTH_ONLY'] = True

# Additional settings to force SSO-only auth
THIRD_PARTY_AUTH_HINT = 'oidc'
THIRD_PARTY_AUTH_ONLY_HINT = 'oidc'
FEATURES['ENABLE_REQUIRE_THIRD_PARTY_AUTH'] = True
SOCIAL_AUTH_RAISE_EXCEPTIONS = False

# Hide all non-SSO auth options
REGISTRATION_EXTRA_FIELDS = {}
REGISTRATION_FIELD_ORDER = []
FEATURES['ENABLE_ACCOUNT_ACTIVATION_REQUIREMENT'] = False

# Auto-submit the SSO form
AUTHN_PROGRESSIVE_PROFILING_SUPPORT = False
SKIP_AUTHN_MFE_REDIRECT_TIMER = True

# CORS Configuration for login endpoints
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://91.107.146.137:8000",
    "http://91.107.146.137:8001",
    "http://91.107.146.137:1999",
    "http://local.openedx.io:8000",
    "http://local.openedx.io:8001",
    "http://local.openedx.io:1999",
    "http://apps.local.openedx.io:1999",
]

# Additional CORS headers for login refresh
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'use-jwt-cookie',
]

# Additional OIDC settings
SOCIAL_AUTH_OIDC_SCOPE = ['openid', 'profile', 'email']
SOCIAL_AUTH_OIDC_ID_TOKEN_DECRYPTION_KEY = None
SOCIAL_AUTH_OIDC_USERNAME_KEY = 'preferred_username'
SOCIAL_AUTH_OIDC_USE_NONCE = True

# Override the backend to get settings from Django settings instead of DB
def get_oidc_setting(name, default=None):
    '''Get OIDC settings from Django settings'''
    return globals().get(f'SOCIAL_AUTH_OIDC_{name}', default)

# Monkey patch the OIDC backend to use our settings
try:
    from social_core.backends.open_id_connect import OpenIdConnectAuth
    
    # Store original method
    _original_setting = OpenIdConnectAuth.setting
    
    def patched_setting(self, name, default=None):
        # First try to get from our settings
        value = get_oidc_setting(name, None)
        if value is not None:
            return value
        # Fallback to original method
        return _original_setting(self, name, default)
    
    # Apply patch
    OpenIdConnectAuth.setting = patched_setting
    
    # Also patch the oidc_endpoint method to use our endpoint directly
    def patched_oidc_endpoint(self):
        return get_oidc_setting('OIDC_ENDPOINT', '').rstrip('/')
    
    OpenIdConnectAuth.oidc_endpoint = patched_oidc_endpoint
    
except ImportError:
    pass

# AUTO CREATE USERS FROM SSO - THIS IS CRITICAL
SOCIAL_AUTH_AUTO_CREATE_USERS = True
FEATURES['ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING'] = True
FEATURES['ALLOW_PUBLIC_ACCOUNT_CREATION'] = True

# User creation pipeline - Use standard social_core pipeline with session creation
SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it
    'social_core.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru
    'social_core.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid
    'social_core.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated
    'social_core.pipeline.social_auth.social_user',

    # Make up a username if one is not provided
    'social_core.pipeline.user.get_username',

    # Create a user if one doesn't exist
    'social_core.pipeline.user.create_user',

    # Create the user<->social association
    'social_core.pipeline.social_auth.associate_user',

    # Populate user data
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    
    # Force login - this should create the session
    'social_django.pipeline.login_user',
)

# Session and cookie settings for SSO
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_DOMAIN = ""  # Set to empty to work with all subdomains
SESSION_COOKIE_HTTPONLY = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Ensure login redirect goes to MFE first
LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/dashboard'
LOGOUT_REDIRECT_URL = '/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_INACTIVE_USER_URL = '/dashboard'

# Username generation from email
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email', 'first_name', 'last_name']
SOCIAL_AUTH_SANITIZE_REDIRECTS = False

# Force login through social auth
SOCIAL_AUTH_FORCE_POST_DISCONNECT = False

# Ensure login_refresh works properly
LOGIN_REFRESH_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'

# JWT Cookie settings for login refresh
JWT_AUTH_COOKIE_HEADER_PAYLOAD = 'edx-jwt-cookie-header-payload'
JWT_AUTH_COOKIE_SIGNATURE = 'edx-jwt-cookie-signature'
JWT_AUTH_REFRESH_COOKIE = 'edx-jwt-refresh-cookie'

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
        if hasattr(request, 'user') and request.user.is_authenticated:
            return None
            
        # List of auth-related URLs to intercept
        auth_patterns = [
            '/login',
            '/signin', 
            '/register',
            '/signup',
            '/logistration',
            # Don't intercept /authn to allow MFE to load first
            # '/authn',
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
            skip_patterns = [
                '/api/csrf/', 
                '/static/', 
                '/media/', 
                '/admin/', 
                '/oauth2/', 
                '/auth/complete/', 
                '/logout', 
                '/auth/login/oidc/',
                '/login_refresh',  # Skip login refresh to avoid CORS issues
                '/api/user/v2/account/login_session/',  # API endpoints
                '/api/mobile/',
                '/heartbeat',
            ]
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
# Enable middleware for immediate redirect
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

# Enable MFE URL pattern for legacy to redirect to MFE
AUTHN_MICROFRONTEND_URL = "http://91.107.146.137:1999/authn"
AUTHN_MICROFRONTEND_DOMAIN = "91.107.146.137:1999"

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

LOGGING['loggers']['oauth2_provider'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}

LOGGING['loggers']['common.djangoapps.third_party_auth'] = {
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

# Redirect CMS login to MFE first
LOGIN_URL = '/login'

# Insert middleware at the beginning for CMS too
# Enable middleware for immediate redirect
MIDDLEWARE = ['lms.djangoapps.sso_redirect.SSORedirectMiddleware'] + MIDDLEWARE
"""),
])

# Production settings to ensure MFE is disabled
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-production-settings", """
# Enable MFE FOR AUTH
AUTHN_MICROFRONTEND_URL = "http://apps.local.openedx.io:1999/authn"
AUTHN_MICROFRONTEND_DOMAIN = "apps.local.openedx.io:1999"
ENABLE_AUTHN_MICROFRONTEND = True

# Ensure third-party auth is enabled in production
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
FEATURES['ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING'] = True

# Session settings for production
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'
"""),
])

# Add custom JavaScript for immediate redirect
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-common-settings", """
# JavaScript to force immediate SSO redirect
AUTHN_CUSTOM_JS_FOOTER = '''
<script>
(function() {
    // Force immediate redirect to SSO if on authn pages
    if (window.location.pathname.includes('/authn/') || 
        window.location.pathname.includes('/login') ||
        window.location.pathname.includes('/register')) {
        
        // Check if we have tpa_hint or should redirect
        const urlParams = new URLSearchParams(window.location.search);
        const tpaHint = urlParams.get('tpa_hint');
        
        if (tpaHint === 'oidc' || !window.location.href.includes('/auth/login/oidc/')) {
            // Find and click the SSO button immediately
            setTimeout(function() {
                const ssoButton = document.querySelector('[data-provider-id="oidc"]') || 
                                 document.querySelector('a[href*="/auth/login/oidc/"]') ||
                                 document.querySelector('button[class*="oidc"]');
                if (ssoButton) {
                    ssoButton.click();
                } else {
                    // Direct redirect if no button found
                    window.location.href = '/auth/login/oidc/?next=' + encodeURIComponent(urlParams.get('next') || '/dashboard');
                }
            }, 100);
        }
    }
})();
</script>
'''
"""),
])

# Development settings
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-development-settings", """
# Enable MFE FOR AUTH IN DEV
AUTHN_MICROFRONTEND_URL = "http://apps.local.openedx.io:1999/authn"
AUTHN_MICROFRONTEND_DOMAIN = "apps.local.openedx.io:1999"
ENABLE_AUTHN_MICROFRONTEND = True

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