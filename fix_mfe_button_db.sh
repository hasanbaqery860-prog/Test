#!/bin/bash

echo "Fixing Authentik button visibility in MFE..."

# Method 1: Direct MySQL commands
echo -e "\n=== Method 1: Direct MySQL Update ==="
echo "Run this command:"
echo 'docker exec -it $(docker ps --filter "name=tutor_local.*mysql" -q) mysql -uroot -p$(tutor config printvalue MYSQL_ROOT_PASSWORD) -e "
USE openedx;
-- Check current settings
SELECT id, name, slug, enabled, visible_for_unauthenticated_users, secondary, other_settings 
FROM third_party_auth_oauth2providerconfig 
WHERE backend_name = '\''social_core.backends.open_id_connect.OpenIdConnectAuth'\'';

-- Update to fix visibility
UPDATE third_party_auth_oauth2providerconfig 
SET 
    enabled = 1,
    visible_for_unauthenticated_users = 1,
    secondary = 0,
    skip_registration_form = 1,
    skip_email_verification = 1,
    send_to_registration_first = 0,
    other_settings = '\''{}'\''
WHERE backend_name = '\''social_core.backends.open_id_connect.OpenIdConnectAuth'\'';

-- Verify the update
SELECT id, name, slug, enabled, visible_for_unauthenticated_users, secondary 
FROM third_party_auth_oauth2providerconfig 
WHERE backend_name = '\''social_core.backends.open_id_connect.OpenIdConnectAuth'\'';
"'

# Method 2: Django shell commands
echo -e "\n\n=== Method 2: Django Shell Update ==="
echo "Run this command:"
echo 'docker exec -it $(docker ps --filter "name=tutor_local.*lms" -q) python manage.py lms shell'

echo -e "\nThen paste this Python code:"
cat << 'PYTHON_CODE'
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig

# Get or create the provider
provider, created = OAuth2ProviderConfig.objects.get_or_create(
    backend_name='social_core.backends.open_id_connect.OpenIdConnectAuth',
    defaults={
        'name': 'oidc',
        'slug': 'oidc',
        'site_id': 1,
        'enabled': True
    }
)

# Update all settings
provider.enabled = True
provider.visible_for_unauthenticated_users = True
provider.secondary = False  # CRITICAL!
provider.skip_registration_form = True
provider.skip_email_verification = True
provider.send_to_registration_first = False
provider.icon_class = 'fa-sign-in'
provider.icon_image = ''
provider.other_settings = '{}'

# Set OAuth credentials if not already set
if not provider.key:
    provider.key = 'openedx-oauth2-client'  # Replace with your actual client ID
if not provider.secret:
    provider.secret = 'YOUR_CLIENT_SECRET_HERE'  # Replace with your actual secret

provider.save()

print(f"Provider updated: {provider.name}")
print(f"  - Enabled: {provider.enabled}")
print(f"  - Visible: {provider.visible_for_unauthenticated_users}")
print(f"  - Secondary: {provider.secondary}")
print(f"  - Skip registration: {provider.skip_registration_form}")

# Clear all caches
from django.core.cache import cache
cache.clear()
print("\nCache cleared!")

# Force reload provider registry
from common.djangoapps.third_party_auth import provider as provider_module
provider_module.Registry._enabled_provider_ids = None
print("Provider registry reloaded!")

exit()
PYTHON_CODE

# Method 3: One-liner fix
echo -e "\n\n=== Method 3: Quick One-Liner Fix ==="
echo "Run this single command:"
echo 'docker exec -it $(docker ps --filter "name=tutor_local.*lms" -q) python manage.py lms shell -c "
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
p = OAuth2ProviderConfig.objects.get(backend_name='\''social_core.backends.open_id_connect.OpenIdConnectAuth'\'')
p.secondary = False
p.visible_for_unauthenticated_users = True
p.enabled = True
p.save()
from django.core.cache import cache
cache.clear()
print('\''Fixed! Provider is now primary and visible.'\'')"'

# Clear cache and restart
echo -e "\n\n=== After running any method above, do: ==="
echo "1. Clear cache:"
echo "   tutor local exec lms python manage.py lms shell -c 'from django.core.cache import cache; cache.clear()'"
echo ""
echo "2. Restart services:"
echo "   tutor local restart openedx memcached"
echo ""
echo "3. Clear browser cache and cookies for local.openedx.io"
echo ""
echo "4. Visit: http://local.openedx.io:8000/authn/login"