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

# Middleware to handle auth redirects
MIDDLEWARE += ['tutorssoredirect.middleware.SSORedirectMiddleware']

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