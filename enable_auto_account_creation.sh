#!/bin/bash

echo "Enabling automatic account creation for Authentik OAuth2..."

# Update OAuth2 provider configuration
echo -e "\n1. Updating OAuth2 provider configuration in database:"
tutor local exec mysql mysql -u root -p$(tutor config printvalue MYSQL_ROOT_PASSWORD) -e "
USE openedx;
UPDATE third_party_auth_oauth2providerconfig 
SET 
    skip_registration_form = 1,
    skip_email_verification = 1,
    send_welcome_email = 0,
    send_to_registration_first = 0
WHERE backend_name = 'social_core.backends.open_id_connect.OpenIdConnectAuth';

-- Check the updated configuration
SELECT name, skip_registration_form, skip_email_verification, send_to_registration_first 
FROM third_party_auth_oauth2providerconfig 
WHERE backend_name = 'social_core.backends.open_id_connect.OpenIdConnectAuth';
"

# Apply the configuration changes
echo -e "\n2. Applying configuration changes:"
tutor config save

# Restart services
echo -e "\n3. Restarting services:"
tutor local restart openedx

echo -e "\n4. Clearing cache:"
tutor local exec lms python manage.py lms shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared!')"

echo -e "\n✅ Done! Automatic account creation is now enabled."
echo -e "\nNext login attempt should automatically create an account and log you in."