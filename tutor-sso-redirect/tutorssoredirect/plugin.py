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
    # Add any plugin-specific settings here
    ("SSO_REDIRECT_ENABLED", True),
    ("SSO_OIDC_ENDPOINT", "/auth/login/oidc/"),
    ("SSO_PROVIDER_NAME", "azuread-oauth2"),  # Default provider, can be changed
])

hooks.Filters.CONFIG_UNIQUE.add_items([
    # Add unique configuration items here
])

hooks.Filters.CONFIG_OVERRIDES.add_items([
    # Override any existing settings here
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
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True

# Configure authentication backends
AUTHENTICATION_BACKENDS = (
    'social_core.backends.azuread.AzureADOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# Middleware to handle auth redirects
MIDDLEWARE += ['tutorssoredirect.middleware.SSORedirectMiddleware']

# Social auth configuration
SOCIAL_AUTH_STRATEGY = 'third_party_auth.strategy.ConfigurationModelStrategy'
SOCIAL_AUTH_STORAGE = 'third_party_auth.models.OAuth2ProviderConfig'

# Redirect settings
LOGIN_URL = '{{ SSO_OIDC_ENDPOINT }}'
LOGIN_REDIRECT_URL = '/dashboard'
LOGOUT_REDIRECT_URL = '/'

# Disable password reset
FEATURES['ENABLE_PASSWORD_RESET'] = False
"""),
    ("openedx-lms-production-settings", """
# Production SSO settings
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SESSION_COOKIE_SECURE = True
"""),
])

# Add patches to openedx-cms-common-settings
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-cms-common-settings", """
# SSO Redirect Plugin Settings for CMS
FEATURES['DISABLE_STUDIO_SSO_OVER_LMS'] = False
FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION'] = False

# Use same authentication backends as LMS
AUTHENTICATION_BACKENDS = (
    'social_core.backends.azuread.AzureADOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# Redirect CMS login to LMS SSO
LOGIN_URL = '/auth/login/oidc/'
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

########################################
# TEMPLATE RENDERING
########################################

# Load templates
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    pkg_resources.resource_filename("tutorssoredirect", "templates")
)

# Add variables to be available in templates
hooks.Filters.ENV_TEMPLATE_VARIABLES.add_items([
    ("sso_redirect_version", __version__),
])

########################################
# PLUGIN INITIALIZATION
########################################

@hooks.Filters.COMPOSE_MOUNTS.add()
def _mount_sso_redirect_middleware(mounts, path_basename):
    """
    Mount the middleware directory to the containers
    """
    if path_basename == "openedx":
        middleware_path = pkg_resources.resource_filename(
            "tutorssoredirect", "openedx"
        )
        if os.path.exists(middleware_path):
            mounts.append((middleware_path, "/openedx/tutorssoredirect"))
    return mounts