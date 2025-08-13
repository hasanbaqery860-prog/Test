#!/bin/bash

echo "=== Creating Authentik OAuth2 Provider ==="

echo "Run this command to create the provider:"
echo ""
echo 'tutor local exec lms python manage.py lms shell -c "
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
from django.contrib.sites.models import Site

# Get the default site
site = Site.objects.get_current()

# Create the OAuth2 provider
provider = OAuth2ProviderConfig.objects.create(
    site=site,
    name=\"oidc\",
    slug=\"oidc\",
    backend_name=\"social_core.backends.open_id_connect.OpenIdConnectAuth\",
    key=\"openedx-oauth2-client\",  # Replace with your Authentik client ID
    secret=\"YOUR_CLIENT_SECRET_HERE\",  # Replace with your Authentik client secret
    enabled=True,
    visible_for_unauthenticated_users=True,
    secondary=False,  # IMPORTANT: Must be False to show as primary button
    skip_registration_form=True,
    skip_email_verification=True,
    send_to_registration_first=False,
    icon_class=\"fa-sign-in\",
    other_settings=\"{}\"
)

print(\"✅ Provider created successfully!\")
print(f\"Name: {provider.name}\")
print(f\"Slug: {provider.slug}\")
print(f\"Enabled: {provider.enabled}\")
print(f\"Secondary: {provider.secondary}\")
print(f\"Visible: {provider.visible_for_unauthenticated_users}\")

# Clear cache
from django.core.cache import cache
cache.clear()
print(\"\\n✅ Cache cleared!\")"'

echo -e "\n\n⚠️  IMPORTANT: Before running the command above:"
echo "1. Replace 'openedx-oauth2-client' with your actual Authentik Client ID"
echo "2. Replace 'YOUR_CLIENT_SECRET_HERE' with your actual Authentik Client Secret"
echo ""
echo "After creating the provider:"
echo "1. tutor local restart openedx"
echo "2. Clear browser cache"
echo "3. Visit: http://local.openedx.io:8000/authn/login"