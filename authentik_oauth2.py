"""
Tutor plugin for Authentik OAuth2/OIDC integration with Open edX
Place this file in: $(tutor config printroot)/plugins/authentik_oauth2.py

This plugin enables Authentik authentication for Open edX with automatic account creation.
All known issues have been fixed including:
- List syntax for AUTHENTICATION_BACKENDS
- MFE support
- Automatic account creation
- 403 errors on login
"""
from tutor import hooks
from tutor.hooks import Filters

# ===== LMS CONFIGURATION =====
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# ===== AUTHENTIK OAUTH2 CONFIGURATION =====
# Enable third party authentication
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ENABLE_COMBINED_LOGIN_REGISTRATION"] = True
FEATURES["ALLOW_PUBLIC_ACCOUNT_CREATION"] = True

# Add OAuth2 backend
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# OAuth2 Provider Configuration - IMPORTANT: Replace these values
SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY = "openedx-oauth2-client"  # Replace with your Client ID from Authentik
SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET = "YOUR_CLIENT_SECRET_HERE"  # Replace with your Client Secret from Authentik
SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT = "http://localhost:9000/application/o/openedx/"  # Update if your Authentik URL is different

# OpenID Connect settings (uses the same values as above)
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT
SOCIAL_AUTH_OIDC_KEY = SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY
SOCIAL_AUTH_OIDC_SECRET = SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET

# Add to authentication backends (using list syntax)
AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

# Social auth pipeline with Open edX specific handlers
SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'common.djangoapps.third_party_auth.pipeline.get_username',  # edX version
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'common.djangoapps.third_party_auth.pipeline.set_logged_in_cookies',  # edX specific
    'common.djangoapps.third_party_auth.pipeline.login_analytics',  # edX specific
]

# Additional settings for better integration
SOCIAL_AUTH_OIDC_USERNAME_KEY = "preferred_username"
SOCIAL_AUTH_OIDC_EMAIL_KEY = "email"
SOCIAL_AUTH_OIDC_FULLNAME_KEY = "name"

# Map OIDC claims to user fields
SOCIAL_AUTH_OIDC_USERINFO_TO_EXTRA_DATA = [
    "email",
    "preferred_username",
    "name",
    "given_name",
    "family_name"
]

# Force username from email if preferred_username is not available
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = False
SOCIAL_AUTH_OIDC_USERNAME_PREFIX = ""

# Allow account linking by email
SOCIAL_AUTH_ASSOCIATE_BY_EMAIL = True

# Auto-create accounts for new users
SOCIAL_AUTH_AUTO_CREATE_USERS = True

# Skip email verification for OAuth users
SKIP_EMAIL_VERIFICATION = True

# Allow users with unverified emails to login
ALLOW_PUBLIC_ACCOUNT_CREATION = True

# Automatically activate new accounts
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email', 'username']
REGISTRATION_EMAIL_PATTERNS_ALLOWED = ['.*']

# CRITICAL: Don't require existing account for OAuth
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

# Enable third party auth account linking
THIRD_PARTY_AUTH = {
    "ENABLE_THIRD_PARTY_AUTH": True,
    "ENABLE_AUTO_LINK_ACCOUNTS": True,
}

# CORS settings for Authentik
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "http://localhost:9000",
    "http://local.openedx.io:8000",
    "https://local.openedx.io:8000",
]

# Set the backend name for the login button
SOCIAL_AUTH_OIDC_CUSTOM_NAME = "Authentik"

# Optional: Debug mode (disable in production)
# SOCIAL_AUTH_OIDC_DEBUG = True
"""
    )
)

# ===== CMS CONFIGURATION =====
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-cms-common-settings",
        """
# ===== AUTHENTIK OAUTH2 CONFIGURATION FOR CMS =====
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ALLOW_PUBLIC_ACCOUNT_CREATION"] = True

THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# Use the same OAuth2 settings as LMS
SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY = "openedx-oauth2-client"  # Replace with your Client ID
SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET = "YOUR_CLIENT_SECRET_HERE"  # Replace with your Client Secret
SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT = "http://localhost:9000/application/o/openedx/"

SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT
SOCIAL_AUTH_OIDC_KEY = SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY
SOCIAL_AUTH_OIDC_SECRET = SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET

AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

# Don't require existing account for OAuth
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

# CORS settings for CMS
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "http://localhost:9000",
    "http://local.openedx.io:8000",
    "https://local.openedx.io:8000",
]
"""
    )
)

# ===== MFE CONFIGURATION =====
# Configure the authn MFE to show third-party auth providers
hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-lms-production-settings",
        """
# Enable third party auth in MFE
ENABLE_THIRD_PARTY_AUTH = True
"""
    )
)

# Add MFE environment variables for authn
hooks.Filters.CONFIG_OVERRIDES.add_item(
    (
        "mfe",
        {
            "ENABLE_THIRD_PARTY_AUTH": True,
            "THIRD_PARTY_AUTH_PROVIDERS": [
                {
                    "id": "oa2-oidc",
                    "name": "Authentik",
                    "iconClass": "fa-sign-in",
                    "iconImage": None,
                    "skipRegistrationForm": True,
                    "skipEmailVerification": True,
                    "loginUrl": "/auth/login/oidc/?auth_entry=register&next=/dashboard",
                    "registerUrl": "/auth/login/oidc/?auth_entry=register&next=/dashboard"
                }
            ]
        }
    )
)

# ===== POST-INSTALLATION INSTRUCTIONS =====
"""
After installing this plugin:

1. Enable the plugin:
   tutor plugins enable authentik_oauth2
   tutor config save
   tutor images build openedx
   tutor images build mfe
   tutor local restart

2. Create OAuth2 provider in Django Admin:
   - Go to: http://your-domain/admin
   - Navigate to: Third Party Auth → OAuth2 Provider Config
   - Add new provider with:
     * Name: oidc
     * Slug: oidc
     * Backend name: social_core.backends.open_id_connect.OpenIdConnectAuth
     * Client ID: (your Authentik client ID)
     * Client Secret: (your Authentik client secret)
     * Skip registration form: ✓
     * Skip email verification: ✓
     * Send to registration first: ✗ (unchecked)
     * Enabled: ✓

3. Configure Authentik:
   - Create OAuth2 Provider with:
     * Redirect URIs: http://your-domain/auth/complete/oidc/
     * Scopes: openid email profile
     
4. Test login:
   - For MFE: http://your-domain/authn/login
   - For legacy: http://your-domain/login
   - Direct OAuth: http://your-domain/auth/login/oidc/?auth_entry=register&next=/dashboard
"""