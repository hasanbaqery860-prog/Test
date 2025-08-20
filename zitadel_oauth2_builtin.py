"""
Tutor plugin for Zitadel OAuth2/OIDC integration with Open edX
Uses Open edX's built-in OIDC backend - no custom code needed!
Place this file in: $(tutor config printroot)/plugins/zitadel_oauth2.py
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

# Add built-in OAuth2 backend - no custom code needed!
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# OAuth2 Provider Configuration
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = "{ZITADEL_DOMAIN}"
SOCIAL_AUTH_OIDC_KEY = "{ZITADEL_CLIENT_ID}"
SOCIAL_AUTH_OIDC_SECRET = "{ZITADEL_CLIENT_SECRET}"

# Add to authentication backends (using built-in backend)
AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

# Social auth pipeline - standard Open edX pipeline
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

# Map OIDC standard claims (the built-in backend handles these automatically)
SOCIAL_AUTH_OIDC_USERNAME_KEY = "preferred_username"
SOCIAL_AUTH_OIDC_EMAIL_KEY = "email"
SOCIAL_AUTH_OIDC_FULLNAME_KEY = "name"

# Auto-create accounts for new users
SOCIAL_AUTH_AUTO_CREATE_USERS = True
SKIP_EMAIL_VERIFICATION = True
ALLOW_PUBLIC_ACCOUNT_CREATION = True

# Don't require existing account for OAuth
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

# Enable third party auth
THIRD_PARTY_AUTH = {{
    "ENABLE_THIRD_PARTY_AUTH": True,
    "ENABLE_AUTO_LINK_ACCOUNTS": True,
}}

# CORS settings for Zitadel
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "{ZITADEL_DOMAIN}",
]

# Session configuration
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True

# Optional: Debug mode (disable in production)
# SOCIAL_AUTH_OIDC_DEBUG = True
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

# Use built-in OIDC backend
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = "{ZITADEL_DOMAIN}"
SOCIAL_AUTH_OIDC_KEY = "{ZITADEL_CLIENT_ID}"
SOCIAL_AUTH_OIDC_SECRET = "{ZITADEL_CLIENT_SECRET}"

AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "{ZITADEL_DOMAIN}",
]
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
OAUTH2_PROVIDER_URL = "/oauth2"
MFE_CONFIG_AUTHN_LOGIN_REDIRECT_URL = "/dashboard"
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
            "THIRD_PARTY_AUTH_ONLY_HINT": "oidc"
        }
    )
)

# ===== INSTALLATION MESSAGE =====
print("""
Zitadel OAuth2 Plugin Installed! (Using Built-in OIDC Backend)

Next steps:
1. Update the plugin configuration:
   - ZITADEL_DOMAIN
   - ZITADEL_CLIENT_ID
   - ZITADEL_CLIENT_SECRET

2. Enable the plugin:
   tutor plugins enable zitadel_oauth2
   tutor config save
   tutor images build openedx mfe
   tutor local restart

3. Configure in Django Admin:
   - Go to: https://your-domain/admin
   - Navigate to: Third Party Auth → OAuth2 Provider Config
   - Add provider with:
     * Name: oidc
     * Slug: oidc
     * Backend name: social_core.backends.open_id_connect.OpenIdConnectAuth
     * Client ID/Secret from Zitadel
     * Enabled: ✓

4. In Zitadel, set redirect URI:
   - https://your-domain/auth/complete/oidc/

That's it! No custom backend code needed.
""")