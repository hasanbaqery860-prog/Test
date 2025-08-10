"""
Tutor plugin for Authentik OAuth2/OIDC integration with Open edX
Place this file in: $(tutor config printroot)/plugins/authentik_oauth2.py
"""
from tutor import hooks

# OAuth2 configuration for Authentik
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# ===== AUTHENTIK OAUTH2 CONFIGURATION =====
# Enable third party authentication
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ENABLE_COMBINED_LOGIN_REGISTRATION"] = True

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

# Add to authentication backends
AUTHENTICATION_BACKENDS = (
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
) + AUTHENTICATION_BACKENDS

# Social auth pipeline
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# Additional settings for better integration
SOCIAL_AUTH_OIDC_USERNAME_KEY = "preferred_username"
SOCIAL_AUTH_OIDC_EMAIL_KEY = "email"
SOCIAL_AUTH_OIDC_FULLNAME_KEY = "name"

# Allow account linking by email
SOCIAL_AUTH_ASSOCIATE_BY_EMAIL = True

# CORS settings for Authentik
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "http://localhost:9000",
]

# Optional: Debug mode (disable in production)
# SOCIAL_AUTH_OIDC_DEBUG = True
"""
    )
)

# Add the same configuration for CMS
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-cms-common-settings",
        """
# ===== AUTHENTIK OAUTH2 CONFIGURATION FOR CMS =====
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True

THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# Use the same OAuth2 settings as LMS
SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY = "openedx-oauth2-client"  # Replace with your Client ID
SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET = "YOUR_CLIENT_SECRET_HERE"  # Replace with your Client Secret
SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT = "http://localhost:9000/application/o/openedx/"

SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT
SOCIAL_AUTH_OIDC_KEY = SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY
SOCIAL_AUTH_OIDC_SECRET = SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET

AUTHENTICATION_BACKENDS = (
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
) + AUTHENTICATION_BACKENDS

# CORS settings for CMS
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "http://localhost:9000",
]
"""
    )
)

# Add login hint configuration
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Auto-redirect to Authentik for login (optional)
# Uncomment the following line to automatically redirect to Authentik
# SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'
# THIRD_PARTY_AUTH_HINT = 'oidc'
"""
    )
)

# Configure the authentication URL name
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Set the backend name for the login button
SOCIAL_AUTH_OIDC_CUSTOM_NAME = "Authentik"
"""
    )
)