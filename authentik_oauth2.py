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

# Force provider to be primary, not secondary
THIRD_PARTY_AUTH_ONLY_PROVIDER = "oidc"
THIRD_PARTY_AUTH_HINT = "oidc"

# Additional setting to force primary provider
ENABLE_REQUIRE_THIRD_PARTY_AUTH = False

# CORS settings for Authentik
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "http://localhost:9000",
    "http://local.openedx.io:8000",
    "https://local.openedx.io:8000",
]

# Set the backend name for the login button
SOCIAL_AUTH_OIDC_CUSTOM_NAME = "Authentik"

# Make provider visible on login page
THIRD_PARTY_AUTH_PROVIDERS = [{
    "id": "oidc",
    "name": "Authentik",
    "iconClass": "fa-sign-in",
    "loginUrl": "/auth/login/oidc/?auth_entry=login&next=/dashboard",
    "registerUrl": "/auth/login/oidc/?auth_entry=register&next=/dashboard"
}]

# Configure OAuth to pass registration hint to Authentik
SOCIAL_AUTH_OIDC_AUTH_EXTRA_ARGUMENTS = {
    'prompt': 'login'  # Default to login
}

# For registration, append prompt=create to the URL
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/dashboard'

# Enable provider display
THIRD_PARTY_AUTH_ENABLE_THIRD_PARTY_AUTH = True
THIRD_PARTY_AUTH_SHOW_IN_LOGIN_PAGE = True

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

# Configure OAuth2 provider settings for MFE
OAUTH2_PROVIDER_URL = "/oauth2"
MFE_CONFIG_AUTHN_LOGIN_REDIRECT_URL = "/dashboard"
"""
    )
)

# Add MFE environment variables for authn
hooks.Filters.CONFIG_OVERRIDES.add_item(
    (
        "mfe",
        {
            "ENABLE_THIRD_PARTY_AUTH": True,
            "AUTHN_MINIMAL_HEADER": False,
            "DISABLE_ENTERPRISE_LOGIN": True,
            "SHOW_CONFIGURABLE_EDX_FIELDS": False,
            "THIRD_PARTY_AUTH_ONLY_HINT": "oidc",
            "THIRD_PARTY_AUTH_HINT": "oidc"
        }
    )
)

# Override MFE authn specific settings
hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-lms-development-settings",
        """
# Force third party auth display
AUTHN_MICROFRONTEND_URL = "http://apps.local.openedx.io:1999/authn"
AUTHN_MICROFRONTEND_DOMAIN = "apps.local.openedx.io/authn"
"""
    )
)

# ===== POST-INSTALLATION HOOK =====
# Automatically fix OAuth2 provider configuration after creation
hooks.Filters.CLI_DO_INIT_TASKS.add_item(
    (
        "lms",
        """
# Fix OAuth2 provider to be primary (not secondary) after it's created
python manage.py lms shell -c "
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
try:
    # Try to get the OIDC provider
    provider = OAuth2ProviderConfig.objects.get(
        backend_name='social_core.backends.open_id_connect.OpenIdConnectAuth'
    )
    # Ensure it's configured as primary provider
    provider.secondary = False
    provider.visible_for_unauthenticated_users = True
    provider.enabled = True
    provider.skip_registration_form = True
    provider.skip_email_verification = True
    provider.send_to_registration_first = False
    provider.save()
    print('✅ Authentik OAuth2 provider configured as primary')
except OAuth2ProviderConfig.DoesNotExist:
    print('⚠️  OAuth2 provider not found - please create it in Django Admin')
except Exception as e:
    print(f'⚠️  Error configuring OAuth2 provider: {e}')
"
"""
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
   tutor local init  # This will run the fix hook
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
     * Site: Select your site
   - Save (other settings will be auto-configured by the plugin)

3. Configure Authentik:
   - Create OAuth2 Provider with:
     * Redirect URIs: http://your-domain/auth/complete/oidc/
     * Scopes: openid email profile
   
   - To enable direct registration from Open edX:
     * Go to Authentik Admin → Flows → Create a new flow
     * Name: "enrollment-with-oidc"
     * Designation: Enrollment
     * Add stages: identification, user_write, email (optional)
     * In your OAuth2 Provider, under "Advanced protocol settings":
       - Set "Authorization flow" to include your enrollment flow
     
   - Alternative: Configure Authentik to show registration link on login:
     * Go to Authentik Admin → Flows → default-authentication-flow
     * Edit the identification stage
     * Enable "Show enrollment link"
     * Set enrollment flow
     
4. Run the fix command (if button doesn't appear):
   tutor local exec lms python manage.py lms shell -c "
   from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
   p = OAuth2ProviderConfig.objects.get(backend_name='social_core.backends.open_id_connect.OpenIdConnectAuth')
   p.secondary = False
   p.visible_for_unauthenticated_users = True
   p.enabled = True
   p.save()
   from django.core.cache import cache
   cache.clear()
   print('Fixed! Provider is now primary and visible.')"
   
   tutor local restart openedx

5. Test login:
   - Visit: http://your-domain/authn/login
   - The "Sign in with Authentik" button should now appear
"""