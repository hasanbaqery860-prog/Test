#!/usr/bin/env python
"""
Script to fix the OAuth2 provider ID mismatch
Run this inside the LMS container
"""

from django.conf import settings
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig

print("Fixing OAuth2 provider ID configuration...")

# Get the OIDC provider
try:
    provider = OAuth2ProviderConfig.objects.get(backend_name='social_core.backends.open_id_connect.OpenIdConnectAuth')
    print(f"\nFound provider: {provider.name} (current slug: {provider.slug})")
    
    # Update to match what the system expects
    provider.slug = "oidc"  # This MUST be "oidc" for the backend
    provider.name = "oidc"  # This also should be "oidc"
    provider.enabled = True
    provider.visible_for_unauthenticated_users = True
    provider.skip_registration_form = True
    provider.skip_email_verification = True
    provider.send_to_registration_first = False
    provider.save()
    
    print(f"\n✅ Updated provider:")
    print(f"  - Name: {provider.name}")
    print(f"  - Slug: {provider.slug}")
    print(f"  - Visible for unauthenticated: {provider.visible_for_unauthenticated_users}")
    
except OAuth2ProviderConfig.DoesNotExist:
    print("❌ OAuth2 provider not found! Creating one...")
    provider = OAuth2ProviderConfig.objects.create(
        enabled=True,
        name="oidc",
        slug="oidc",
        backend_name="social_core.backends.open_id_connect.OpenIdConnectAuth",
        skip_registration_form=True,
        skip_email_verification=True,
        send_to_registration_first=False,
        visible_for_unauthenticated_users=True,
        site_id=1
    )
    print("✅ Created new provider")

# Clear cache
from django.core.cache import cache
cache.clear()
print("\n✅ Cache cleared!")

# Check if it's in the primary providers now
from common.djangoapps.third_party_auth import provider
providers = provider.Registry.enabled()
print(f"\n📋 Enabled providers: {[p.name for p in providers]}")

print("\nNow restart the MFE container and try again.")