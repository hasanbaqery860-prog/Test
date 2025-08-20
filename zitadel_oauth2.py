"""
Tutor plugin for Zitadel OAuth2/OIDC integration with Open edX
Place this file in: $(tutor config printroot)/plugins/zitadel_oauth2.py

This plugin enables Zitadel authentication for Open edX with automatic account creation.
Supports SMS OTP through Zitadel actions (no additional server needed).
"""
from tutor import hooks

# ===== PLUGIN CONFIGURATION =====
# Update these values with your Zitadel instance details
ZITADEL_DOMAIN = "https://auth.yourdomain.com"  # Your Zitadel domain
ZITADEL_CLIENT_ID = "YOUR_CLIENT_ID"  # From Zitadel application
ZITADEL_CLIENT_SECRET = "YOUR_CLIENT_SECRET"  # From Zitadel application

# ===== LMS CONFIGURATION =====
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        f"""
# ===== ZITADEL OAUTH2 CONFIGURATION =====
# Enable third party authentication
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ENABLE_COMBINED_LOGIN_REGISTRATION"] = True
FEATURES["ALLOW_PUBLIC_ACCOUNT_CREATION"] = True

# Add OAuth2 backend
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# OAuth2 Provider Configuration
SOCIAL_AUTH_ZITADEL_KEY = "{ZITADEL_CLIENT_ID}"
SOCIAL_AUTH_ZITADEL_SECRET = "{ZITADEL_CLIENT_SECRET}"
SOCIAL_AUTH_ZITADEL_ENDPOINT = "{ZITADEL_DOMAIN}"

# OpenID Connect settings
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = SOCIAL_AUTH_ZITADEL_ENDPOINT
SOCIAL_AUTH_OIDC_KEY = SOCIAL_AUTH_ZITADEL_KEY
SOCIAL_AUTH_OIDC_SECRET = SOCIAL_AUTH_ZITADEL_SECRET

# Add to authentication backends
AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

# Social auth pipeline with Open edX specific handlers
SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'common.djangoapps.third_party_auth.pipeline.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'common.djangoapps.third_party_auth.pipeline.set_logged_in_cookies',
    'common.djangoapps.third_party_auth.pipeline.login_analytics',
]

# Additional settings for Zitadel integration
SOCIAL_AUTH_OIDC_USERNAME_KEY = "preferred_username"
SOCIAL_AUTH_OIDC_EMAIL_KEY = "email"
SOCIAL_AUTH_OIDC_FULLNAME_KEY = "name"

# Map OIDC claims to user fields
SOCIAL_AUTH_OIDC_USERINFO_TO_EXTRA_DATA = [
    "email",
    "preferred_username",
    "name",
    "given_name",
    "family_name",
    "phone",
    "phone_verified",
    "locale",
    "picture"
]

# Username handling
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

# Don't require existing account for OAuth
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

# Enable third party auth account linking
THIRD_PARTY_AUTH = {{
    "ENABLE_THIRD_PARTY_AUTH": True,
    "ENABLE_AUTO_LINK_ACCOUNTS": True,
}}

# Force provider to be primary
THIRD_PARTY_AUTH_ONLY_PROVIDER = "oidc"
THIRD_PARTY_AUTH_HINT = "oidc"

# Disable enterprise login if not needed
ENABLE_ENTERPRISE_INTEGRATION = False

# CORS settings for Zitadel
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "{ZITADEL_DOMAIN}",
]

# Set the backend name for the login button
SOCIAL_AUTH_OIDC_CUSTOM_NAME = "Zitadel"

# Make provider visible on login page
THIRD_PARTY_AUTH_PROVIDERS = [{{
    "id": "oidc",
    "name": "Sign in with Zitadel",
    "iconClass": "fa-sign-in",
    "loginUrl": "/auth/login/oidc/?auth_entry=register",
    "registerUrl": "/auth/login/oidc/?auth_entry=register"
}}]

# Enable provider display
THIRD_PARTY_AUTH_ENABLE_THIRD_PARTY_AUTH = True
THIRD_PARTY_AUTH_SHOW_IN_LOGIN_PAGE = True

# Session configuration for better OAuth experience
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True

# Optional: Debug mode (disable in production)
# SOCIAL_AUTH_OIDC_DEBUG = True
# LOGGING['handlers']['console']['level'] = 'DEBUG'
"""
    )
)

# ===== CMS CONFIGURATION =====
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-cms-common-settings",
        f"""
# ===== ZITADEL OAUTH2 CONFIGURATION FOR CMS =====
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ALLOW_PUBLIC_ACCOUNT_CREATION"] = True

THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# Use the same OAuth2 settings as LMS
SOCIAL_AUTH_ZITADEL_KEY = "{ZITADEL_CLIENT_ID}"
SOCIAL_AUTH_ZITADEL_SECRET = "{ZITADEL_CLIENT_SECRET}"
SOCIAL_AUTH_ZITADEL_ENDPOINT = "{ZITADEL_DOMAIN}"

SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = SOCIAL_AUTH_ZITADEL_ENDPOINT
SOCIAL_AUTH_OIDC_KEY = SOCIAL_AUTH_ZITADEL_KEY
SOCIAL_AUTH_OIDC_SECRET = SOCIAL_AUTH_ZITADEL_SECRET

AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

# Don't require existing account for OAuth
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

# CORS settings for CMS
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "{ZITADEL_DOMAIN}",
]

# Session configuration
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
"""
    )
)

# ===== MFE CONFIGURATION =====
hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-lms-production-settings",
        """
# Enable third party auth in MFE
ENABLE_THIRD_PARTY_AUTH = True

# Configure OAuth2 provider settings for MFE
OAUTH2_PROVIDER_URL = "/oauth2"
MFE_CONFIG_AUTHN_LOGIN_REDIRECT_URL = "/dashboard"

# Add Zitadel as login option
LOGIN_REDIRECT_WHITELIST.append("{{ SOCIAL_AUTH_ZITADEL_ENDPOINT }}")
"""
    )
)

# Add MFE environment variables
hooks.Filters.CONFIG_OVERRIDES.add_item(
    (
        "mfe",
        {
            "ENABLE_THIRD_PARTY_AUTH": True,
            "AUTHN_MINIMAL_HEADER": False,
            "DISABLE_ENTERPRISE_LOGIN": True,
            "SHOW_CONFIGURABLE_EDX_FIELDS": False,
            "THIRD_PARTY_AUTH_ONLY_HINT": "oidc",
            "LOGIN_ISSUE_SUPPORT_LINK": "",
            "ENABLE_PROGRESSIVE_PROFILING": False
        }
    )
)

# Force MFE authn to display third party auth
hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-lms-development-settings",
        f"""
# Force third party auth display in development
AUTHN_MICROFRONTEND_URL = "http://apps.local.openedx.io:1999/authn"
AUTHN_MICROFRONTEND_DOMAIN = "apps.local.openedx.io/authn"

# Add provider info to MFE config
MFE_CONFIG["THIRD_PARTY_AUTH_PROVIDERS"] = [{{
    "id": "oidc",
    "name": "Zitadel",
    "iconClass": "fa-sign-in",
    "loginUrl": "/auth/login/oidc/?auth_entry=register",
    "registerUrl": "/auth/login/oidc/?auth_entry=register"
}}]
"""
    )
)

# ===== ADDITIONAL PATCHES FOR PRODUCTION =====
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-production-settings",
        """
# Production security settings for Zitadel OAuth
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Ensure proper cookie handling
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
"""
    )
)

# ===== INSTALLATION MESSAGE =====
print("""
Zitadel OAuth2 Plugin Installed!

Next steps:
1. Update the plugin configuration at the top of this file:
   - ZITADEL_DOMAIN
   - ZITADEL_CLIENT_ID
   - ZITADEL_CLIENT_SECRET

2. Enable the plugin:
   tutor plugins enable zitadel_oauth2
   tutor config save
   tutor images build openedx mfe
   tutor local restart

3. Configure OAuth2 provider in Django Admin:
   - Go to: https://your-domain/admin
   - Navigate to: Third Party Auth → OAuth2 Provider Config
   - Add provider with backend name: social_core.backends.open_id_connect.OpenIdConnectAuth

4. In Zitadel, ensure redirect URIs include:
   - https://your-domain/auth/complete/oidc/

5. Test login at:
   - https://your-domain/login
   - Direct: https://your-domain/auth/login/oidc/?auth_entry=register&next=/dashboard
""")