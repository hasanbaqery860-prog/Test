#!/bin/bash

echo "Fixing 403 error and enabling automatic account creation..."

# First, let's add the missing configuration to the plugin
cat >> /workspace/authentik_oauth2_fix.py << 'EOF'
# Additional fix for auto account creation
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Force enable auto account creation
FEATURES["ALLOW_PUBLIC_ACCOUNT_CREATION"] = True
FEATURES["ENABLE_COMBINED_LOGIN_REGISTRATION"] = True

# Disable requiring existing account
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

# Allow OAuth2 users to create accounts
THIRD_PARTY_AUTH = {
    "ENABLE_THIRD_PARTY_AUTH": True,
    "ENABLE_AUTO_LINK_ACCOUNTS": True,
}

# Override the login session endpoint behavior
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
SOCIAL_AUTH_RAISE_EXCEPTIONS = True
SOCIAL_AUTH_BACKEND_ERROR_URL = '/login'
"""
    )
)
EOF

echo -e "\n1. Copy the script to the container and run it:"
echo 'docker cp /workspace/force_auto_account_creation.py $(docker ps --filter "name=tutor_local-lms-1" -q):/openedx/'
echo 'docker exec -it $(docker ps --filter "name=tutor_local-lms-1" -q) python /openedx/force_auto_account_creation.py'

echo -e "\n2. Or use Django admin shell directly:"
echo 'docker exec -it $(docker ps --filter "name=tutor_local-lms-1" -q) python manage.py lms shell'

echo -e "\nThen paste this code:"
cat << 'PYTHON_CODE'
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
provider = OAuth2ProviderConfig.objects.get(backend_name='social_core.backends.open_id_connect.OpenIdConnectAuth')
provider.skip_registration_form = True
provider.skip_email_verification = True
provider.send_to_registration_first = False
provider.save()
print("Settings updated!")
PYTHON_CODE

echo -e "\n3. Clear session and cookies:"
echo "- Clear all cookies for local.openedx.io in your browser"
echo "- Use incognito/private mode for testing"

echo -e "\n4. Direct database update (if above doesn't work):"
echo 'docker exec -it $(docker ps --filter "name=tutor_local-mysql-1" -q) mysql -u root -p'
echo "Then run:"
cat << 'SQL'
USE openedx;
UPDATE third_party_auth_oauth2providerconfig 
SET skip_registration_form = 1, 
    skip_email_verification = 1, 
    send_to_registration_first = 0,
    enabled = 1
WHERE backend_name = 'social_core.backends.open_id_connect.OpenIdConnectAuth';
SQL

echo -e "\n5. Test with direct OAuth URL:"
echo "http://local.openedx.io:8000/auth/login/oidc/?auth_entry=register&next=/dashboard"
echo "(Note: auth_entry=register instead of login)"