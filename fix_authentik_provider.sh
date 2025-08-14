#!/bin/bash

echo "Fixing Authentik OAuth2 Provider Configuration..."

# Check current provider status
echo -e "\n1. Checking current OAuth2 provider status:"
tutor local exec mysql mysql -u root -p$(tutor config printvalue MYSQL_ROOT_PASSWORD) -e "
USE openedx;
SELECT id, name, slug, enabled, backend_name, site_id FROM third_party_auth_oauth2providerconfig WHERE backend_name LIKE '%open_id_connect%';
"

# Enable the provider
echo -e "\n2. Enabling the OAuth2 provider:"
tutor local exec mysql mysql -u root -p$(tutor config printvalue MYSQL_ROOT_PASSWORD) -e "
USE openedx;
UPDATE third_party_auth_oauth2providerconfig 
SET enabled = 1 
WHERE backend_name = 'social_core.backends.open_id_connect.OpenIdConnectAuth';
"

# Verify the change
echo -e "\n3. Verifying the provider is now enabled:"
tutor local exec mysql mysql -u root -p$(tutor config printvalue MYSQL_ROOT_PASSWORD) -e "
USE openedx;
SELECT id, name, slug, enabled, backend_name FROM third_party_auth_oauth2providerconfig WHERE backend_name LIKE '%open_id_connect%';
"

# Clear cache
echo -e "\n4. Clearing Django cache:"
tutor local exec lms python manage.py lms shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared!')"

# Restart services
echo -e "\n5. Restarting services:"
tutor local restart openedx

echo -e "\n✅ Done! The Authentik login should now work. Try logging in again."