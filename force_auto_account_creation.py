#!/usr/bin/env python
"""
Script to force enable automatic account creation for OAuth2
Run this inside the LMS container
"""

from django.conf import settings
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig

print("Checking current OAuth2 configuration...")

# Get the OIDC provider
try:
    provider = OAuth2ProviderConfig.objects.get(backend_name='social_core.backends.open_id_connect.OpenIdConnectAuth')
    print(f"\nFound provider: {provider.name}")
    print(f"Current settings:")
    print(f"  - Enabled: {provider.enabled}")
    print(f"  - Skip registration form: {provider.skip_registration_form}")
    print(f"  - Skip email verification: {provider.skip_email_verification}")
    print(f"  - Send to registration first: {provider.send_to_registration_first}")
    
    # Force the correct settings
    provider.enabled = True
    provider.skip_registration_form = True
    provider.skip_email_verification = True
    provider.send_to_registration_first = False
    provider.save()
    
    print("\n✅ Updated settings:")
    print(f"  - Skip registration form: {provider.skip_registration_form}")
    print(f"  - Skip email verification: {provider.skip_email_verification}")
    print(f"  - Send to registration first: {provider.send_to_registration_first}")
    
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
        site_id=1
    )
    print("✅ Created new provider with auto-creation enabled")

# Check Django settings
print("\n\nChecking Django settings...")
print(f"FEATURES['ENABLE_THIRD_PARTY_AUTH']: {settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False)}")
print(f"FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION']: {settings.FEATURES.get('ENABLE_COMBINED_LOGIN_REGISTRATION', False)}")
print(f"SOCIAL_AUTH_ASSOCIATE_BY_EMAIL: {getattr(settings, 'SOCIAL_AUTH_ASSOCIATE_BY_EMAIL', False)}")

# Clear cache
from django.core.cache import cache
cache.clear()
print("\n✅ Cache cleared!")
print("\nNow try logging in again with Authentik.")