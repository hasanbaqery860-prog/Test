"""
Tutor plugin for SSO redirect
Disables Open edX login/register and redirects all auth to SSO
"""
from glob import glob
import os
import pkg_resources

from tutor import hooks

from .__about__ import __version__

# Configuration
hooks.Filters.CONFIG_DEFAULTS.add_items([
    ("SSO_REDIRECT_ENABLED", True),
    ("SSO_REDIRECT_URL", "/auth/login/oidc/"),
    ("SSO_OIDC_KEY", ""),
    ("SSO_OIDC_SECRET", ""),
    ("SSO_OIDC_ENDPOINT", ""),
])

# LMS common settings patch content
LMS_COMMON_SETTINGS = """
# SSO Redirect Plugin Settings

# Enable MFE
AUTHN_MICROFRONTEND_URL = "http://91.107.146.137:1999/authn"
AUTHN_MICROFRONTEND_DOMAIN = "91.107.146.137:1999"
ENABLE_AUTHN_MICROFRONTEND = True
FEATURES['ENABLE_AUTHN_MICROFRONTEND'] = True

# Third party auth settings
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
FEATURES['ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING'] = True
FEATURES['ALLOW_PUBLIC_ACCOUNT_CREATION'] = True

# OIDC Configuration
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = '{{ SSO_OIDC_ENDPOINT }}'
SOCIAL_AUTH_OIDC_KEY = '{{ SSO_OIDC_KEY }}'
SOCIAL_AUTH_OIDC_SECRET = '{{ SSO_OIDC_SECRET }}'

# Authentication backends
AUTHENTICATION_BACKENDS = (
    'social_core.backends.open_id_connect.OpenIdConnectAuth',
    'django.contrib.auth.backends.ModelBackend',
)

# Social auth settings
SOCIAL_AUTH_STRATEGY = 'social_django.strategy.DjangoStrategy'
SOCIAL_AUTH_STORAGE = 'social_django.models.DjangoStorage'

# Backend configuration
THIRD_PARTY_AUTH_BACKENDS = ['social_core.backends.open_id_connect.OpenIdConnectAuth']

# Pipeline
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
    'social_django.pipeline.login_user',
)

# Session settings
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Login URLs
LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'

# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://91.107.146.137:8000",
    "http://91.107.146.137:8001",
    "http://91.107.146.137:1999",
]

# User creation
SOCIAL_AUTH_AUTO_CREATE_USERS = True
FEATURES['SKIP_EMAIL_VERIFICATION'] = True
"""

# URL redirect patch content
URL_REDIRECT_PATCH = """
from django.urls import re_path
from django.http import HttpResponseRedirect
from django.conf import settings

def mfe_sso_redirect(request):
    mfe_url = getattr(settings, 'AUTHN_MICROFRONTEND_URL', 'http://91.107.146.137:1999/authn')
    next_url = request.GET.get('next', '/dashboard')
    return HttpResponseRedirect(f"{mfe_url}/login?next={next_url}&tpa_hint=oidc")

auth_redirects = [
    re_path(r'^login/?$', mfe_sso_redirect),
    re_path(r'^register/?$', mfe_sso_redirect),
    re_path(r'^signin/?$', mfe_sso_redirect),
    re_path(r'^signup/?$', mfe_sso_redirect),
]

urlpatterns = auth_redirects + urlpatterns
"""

# Add patches
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-common-settings", LMS_COMMON_SETTINGS),
])

hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-urls", URL_REDIRECT_PATCH),
])

# MFE environment patches
hooks.Filters.ENV_PATCHES.add_items([
    ("mfe-env-production", """
LOGIN_ISSUE_SUPPORT_LINK=''
DISABLE_ENTERPRISE_LOGIN=true
ENABLE_PROGRESSIVE_PROFILING_ON_AUTHN=false
"""),
])

# Load additional patches from files
patches_dir = pkg_resources.resource_filename("tutorssoredirect", "patches")
for patch_file in glob(os.path.join(patches_dir, "*.yml")):
    with open(patch_file) as f:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(patch_file)[:-4], f.read()))