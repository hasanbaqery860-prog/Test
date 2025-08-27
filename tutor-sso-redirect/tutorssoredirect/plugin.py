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
    ("SSO_USE_MFE", True),  # Use MFE for authentication
    ("SSO_MFE_URL", "http://apps.local.openedx.io:1999"),  # MFE URL
    ("SSO_REDIRECT_URL", "/auth/login/oidc/"),  # Backend SSO URL
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
# SSO Redirect Plugin Settings - Work with MFE for Zitadel authentication

# Enable the authn MFE
AUTHN_MICROFRONTEND_URL = '{{ SSO_MFE_URL }}'
AUTHN_MICROFRONTEND_DOMAIN = 'apps.local.openedx.io:1999'
ENABLE_AUTHN_MICROFRONTEND = True
FEATURES['ENABLE_AUTHN_MICROFRONTEND'] = True

# Configure MFE to show third-party auth
AUTHN_MICROFRONTEND_THIRD_PARTY_AUTH_ENABLED = True
AUTHN_MICROFRONTEND_THIRD_PARTY_AUTH_ONLY = True  # Only show third-party auth, hide username/password

# Ensure MFE can communicate with LMS
MFE_CONFIG = {
    "BASE_URL": "http://apps.local.openedx.io:1999",
    "LMS_BASE_URL": "http://91.107.146.137:8000",
    "LOGIN_ISSUE_SUPPORT_LINK": "",
    "ENABLE_THIRD_PARTY_AUTH": True,
    "THIRD_PARTY_AUTH_ONLY": True,
    "AUTHN_MINIMAL_HEADER": True,
}

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

# Create custom pipeline module
import sys
from types import ModuleType

# Custom pipeline step to ensure proper login
def ensure_user_login(backend, user, response, *args, **kwargs):
    '''Custom pipeline step to ensure user is properly logged in'''
    if user and backend:
        from django.contrib.auth import login
        # Get the request from the strategy
        request = backend.strategy.request
        if request and user.is_active:
            # Ensure user backend is set
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            # Force login
            login(request, user)
            # Force session save
            request.session.save()
            request.session.modified = True
            # Set session expiry
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            # Log the successful login
            import logging
            logger = logging.getLogger('lms.djangoapps.sso_redirect')
            logger.info(f"SSO Login: Successfully logged in user {user.username} (ID: {user.id})")
    return {}

# Enhanced login completion function
def complete_social_login(backend, user, response, request, *args, **kwargs):
    '''Enhanced login completion to ensure session persistence'''
    if user and request:
        from django.contrib.auth import login
        import logging
        logger = logging.getLogger('lms.djangoapps.sso_redirect')
        
        try:
            # Set the authentication backend
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            
            # Perform the login
            login(request, user)
            
            # Ensure session is created and saved
            if not request.session.session_key:
                request.session.create()
            
            # Force session save with explicit flags
            request.session.modified = True
            request.session.save(force_insert=True)
            
            # Set session cookie explicitly
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            
            logger.info(f"SSO: User {user.username} logged in successfully, session key: {request.session.session_key}")
            
        except Exception as e:
            logger.error(f"SSO: Error during login completion: {str(e)}")
            raise
    
    return {}

# Create a module to hold the pipeline function
pipeline_module = ModuleType('lms.djangoapps.sso_pipeline')
pipeline_module.ensure_user_login = ensure_user_login
pipeline_module.complete_social_login = complete_social_login

# Add to sys.modules
sys.modules['lms.djangoapps.sso_pipeline'] = pipeline_module

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
    
    # Our custom login steps
    'lms.djangoapps.sso_pipeline.ensure_user_login',
    'lms.djangoapps.sso_pipeline.complete_social_login',
)

# Session and cookie settings for SSO
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days
SESSION_SAVE_EVERY_REQUEST = True  # Changed to True to ensure session is saved
SESSION_COOKIE_DOMAIN = None  # Changed to None for better compatibility
SESSION_COOKIE_HTTPONLY = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False  # Set to True only if using HTTPS

# Ensure login redirect works
{% if SSO_USE_MFE %}
# Force MFE authn URL (not just /login)
LOGIN_URL = '{{ SSO_MFE_URL }}/authn/login'
# Override any Django defaults
LOGOUT_URL = '/logout'
{% else %}
LOGIN_URL = '{{ SSO_REDIRECT_URL }}'
{% endif %}
LOGIN_REDIRECT_URL = '/dashboard'
LOGOUT_REDIRECT_URL = '/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_INACTIVE_USER_URL = '/dashboard'

# Force override Django's default login URL behavior
import django.conf.global_settings
django.conf.global_settings.LOGIN_URL = LOGIN_URL

# Additional session security settings
SOCIAL_AUTH_SESSION_EXPIRATION = False
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False  # Set to True if using HTTPS

# Force session to be created on login
SOCIAL_AUTH_ALWAYS_ASSOCIATE = True

# Username generation from email
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email', 'first_name', 'last_name']
SOCIAL_AUTH_SANITIZE_REDIRECTS = False

# Store authentication state in session
SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = ['next', 'auth_entry', 'redirect_state']

# Ensure proper OIDC response mode
SOCIAL_AUTH_OIDC_RESPONSE_MODE = 'query'

# Force login through social auth
SOCIAL_AUTH_FORCE_POST_DISCONNECT = False

# Define the SSO redirect middleware inline
from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponsePermanentRedirect
import logging

logger = logging.getLogger(__name__)

class SSORedirectMiddleware(MiddlewareMixin):
    '''Middleware to redirect authentication requests to MFE'''
    
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
            '/user_api/v1/account/login_session',
            '/api/user/v1/account/login_session',
            '/create_account',
            '/ui/login',
            '/accounts/login',  # Django default login URL
        ]
        
        # Check if this is an auth URL
        is_auth_url = False
        for pattern in auth_patterns:
            if pattern in path or path.endswith(pattern):
                is_auth_url = True
                break
        
        if is_auth_url:
            # Skip if it's an API endpoint we need to keep or MFE URLs
            skip_patterns = ['/api/csrf/', '/static/', '/media/', '/admin/', '/oauth2/', '/auth/complete/', '/logout', '/auth/login/oidc/', '/authn/']
            if any(skip in path for skip in skip_patterns):
                return None
            
            # Check if we should use MFE
            use_mfe = getattr(settings, 'SSO_USE_MFE', True)
            
            if use_mfe:
                # Redirect to MFE authn app
                mfe_url = getattr(settings, 'SSO_MFE_URL', 'http://apps.local.openedx.io:1999')
                redirect_url = f"{mfe_url}/authn/login?next=%2F"
                
                # Preserve next parameter if provided
                next_url = request.GET.get('next', '')
                if next_url and next_url != '/':
                    from urllib.parse import quote
                    redirect_url = f"{mfe_url}/authn/login?next={quote(next_url, safe='')}"
                
                # Log the redirect
                logger.info(f"SSO Redirect: INTERCEPTING {request.path} -> {redirect_url}")
                
                # Use permanent redirect
                return HttpResponsePermanentRedirect(redirect_url)
            else:
                # Direct SSO redirect (old behavior)
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

# Note: OIDC provider configuration is handled by the configure_oidc_provider.py script
# Run: tutor local exec lms python /openedx/configure_oidc_provider.py

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

# Production settings to ensure MFE is configured correctly
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-production-settings", """
# Configure MFE for authentication
{% if SSO_USE_MFE %}
AUTHN_MICROFRONTEND_URL = '{{ SSO_MFE_URL }}'
AUTHN_MICROFRONTEND_DOMAIN = 'apps.local.openedx.io:1999'
ENABLE_AUTHN_MICROFRONTEND = True
{% else %}
AUTHN_MICROFRONTEND_URL = None
AUTHN_MICROFRONTEND_DOMAIN = None
ENABLE_AUTHN_MICROFRONTEND = False
{% endif %}

# Ensure third-party auth is enabled in production
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
FEATURES['ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING'] = True

# Session settings for production
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Ensure social auth redirects work properly
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/dashboard'

# Additional security for production
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False  # Set to True if using HTTPS
SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = ['next']
"""),
])

# Development settings
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-development-settings", """
# Configure MFE for authentication in dev
{% if SSO_USE_MFE %}
AUTHN_MICROFRONTEND_URL = '{{ SSO_MFE_URL }}'
AUTHN_MICROFRONTEND_DOMAIN = 'apps.local.openedx.io:1999'
ENABLE_AUTHN_MICROFRONTEND = True
{% else %}
AUTHN_MICROFRONTEND_URL = None
AUTHN_MICROFRONTEND_DOMAIN = None
ENABLE_AUTHN_MICROFRONTEND = False
{% endif %}

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