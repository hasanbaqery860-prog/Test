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
from django.http import HttpResponsePermanentRedirect
import logging

logger = logging.getLogger(__name__)

class SSORedirectMiddleware(MiddlewareMixin):
    '''Middleware to redirect authentication requests to SSO'''
    
    def process_request(self, request):
        if not getattr(settings, 'SSO_REDIRECT_ENABLED', True):
            return None
            
        path = request.path.lower().rstrip('/')
        
        # Very aggressive pattern matching for any login-related URL
        auth_keywords = ['login', 'signin', 'register', 'signup', 'logistration', 'authn']
        
        # Check if path contains any auth keyword
        if any(keyword in path for keyword in auth_keywords):
            # Skip if it's an API, static, or allowed URL
            skip_patterns = ['/api/', '/static/', '/media/', '/admin/', '/oauth2/', '/auth/complete/', '/logout']
            if any(skip in path for skip in skip_patterns):
                return None
            
            # Check if this is already the SSO URL
            sso_url = getattr(settings, 'SSO_REDIRECT_URL', '/auth/login/oidc/')
            if sso_url.rstrip('/') in path:
                return None
            
            # Log the redirect
            logger.info(f"SSO Redirect: Intercepting {request.path} -> {sso_url}")
            
            # Preserve next parameter
            next_url = request.GET.get('next', '')
            if next_url:
                redirect_url = f"{sso_url}?next={next_url}"
            else:
                redirect_url = sso_url
            
            # Use permanent redirect to ensure browsers cache it
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

# Insert middleware at the BEGINNING of the stack to catch requests early
MIDDLEWARE = ['lms.djangoapps.sso_redirect.SSORedirectMiddleware'] + MIDDLEWARE

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
    'level': 'INFO',
    'propagate': False,
}

# Override any login-related view classes
try:
    from django.contrib.auth import views as auth_views
    from django.shortcuts import redirect as django_redirect
    
    # Monkey-patch login view
    original_login = auth_views.LoginView.as_view
    auth_views.LoginView.as_view = lambda **kwargs: lambda request: django_redirect('{{ SSO_REDIRECT_URL }}')
except Exception:
    pass

# Disable all login forms
FEATURES['SHOW_REGISTRATION_LINKS'] = False
FEATURES['ENABLE_MKTG_SITE'] = False
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

########################################
# ADDITIONAL SETTINGS PATCHES
########################################

# Add a patch that runs after all other patches to ensure our middleware is first
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-final-settings", """
# Ensure SSO redirect middleware is absolutely first
if 'lms.djangoapps.sso_redirect.SSORedirectMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('lms.djangoapps.sso_redirect.SSORedirectMiddleware')
MIDDLEWARE.insert(0, 'lms.djangoapps.sso_redirect.SSORedirectMiddleware')

# Log final middleware order for debugging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Final MIDDLEWARE order: {MIDDLEWARE[:5]}...")  # Log first 5 middlewares
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