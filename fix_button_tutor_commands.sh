#!/bin/bash

echo "=== Fix Authentik Button Visibility using Tutor Commands ==="

# Method 1: Quick fix using Tutor
echo -e "\n1. QUICKEST FIX - Run this single command:"
echo ""
echo 'tutor local exec lms python manage.py lms shell -c "
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
try:
    p = OAuth2ProviderConfig.objects.get(backend_name=\"social_core.backends.open_id_connect.OpenIdConnectAuth\")
    p.secondary = False
    p.visible_for_unauthenticated_users = True
    p.enabled = True
    p.skip_registration_form = True
    p.skip_email_verification = True
    p.send_to_registration_first = False
    p.save()
    print(\"✅ Fixed! Provider is now primary and visible.\")
    print(f\"Provider: {p.name}, Secondary: {p.secondary}, Visible: {p.visible_for_unauthenticated_users}\")
except OAuth2ProviderConfig.DoesNotExist:
    print(\"❌ Provider not found! Create it in Django Admin first.\")
from django.core.cache import cache
cache.clear()
print(\"✅ Cache cleared!\")"'

echo -e "\n\n2. Alternative - Interactive Python shell:"
echo "tutor local exec lms python manage.py lms shell"
echo ""
echo "Then paste:"
echo '
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
p = OAuth2ProviderConfig.objects.get(backend_name="social_core.backends.open_id_connect.OpenIdConnectAuth")
p.secondary = False
p.visible_for_unauthenticated_users = True
p.enabled = True
p.save()
print(f"Fixed! Secondary: {p.secondary}")
exit()
'

echo -e "\n\n3. MySQL Database Update using Tutor:"
echo 'tutor local exec mysql mysql -u root -p$(tutor config printvalue MYSQL_ROOT_PASSWORD) openedx -e "UPDATE third_party_auth_oauth2providerconfig SET secondary = 0, visible_for_unauthenticated_users = 1, enabled = 1 WHERE backend_name = \"social_core.backends.open_id_connect.OpenIdConnectAuth\";"'

echo -e "\n\n4. After any method above:"
echo "   tutor local restart openedx"
echo "   tutor local restart memcached"
echo ""
echo "5. Clear browser cache and visit: http://local.openedx.io:8000/authn/login"