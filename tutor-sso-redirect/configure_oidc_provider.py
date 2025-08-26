#!/usr/bin/env python3
"""
Script to automatically configure OIDC provider in the database
This ensures the provider is properly configured for Zitadel
"""
import os
import sys
import django
import json

# Set up Django environment
sys.path.append('/openedx/edx-platform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.tutor.production')
django.setup()

from django.conf import settings
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
from django.contrib.sites.models import Site

def configure_oidc_provider():
    """Configure or update OIDC provider in database"""
    
    print("Configuring OIDC Provider for Zitadel...")
    print("=" * 60)
    
    # Get the default site
    try:
        site = Site.objects.get_current()
    except:
        site = Site.objects.first()
    
    if not site:
        print("❌ Error: No site configured!")
        return False
    
    # Get settings from environment
    client_id = getattr(settings, 'SOCIAL_AUTH_OIDC_KEY', '')
    client_secret = getattr(settings, 'SOCIAL_AUTH_OIDC_SECRET', '')
    oidc_endpoint = getattr(settings, 'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT', '')
    
    if not all([client_id, client_secret, oidc_endpoint]):
        print("❌ Error: Missing OIDC configuration in settings!")
        print(f"  Client ID: {'SET' if client_id else 'NOT SET'}")
        print(f"  Client Secret: {'SET' if client_secret else 'NOT SET'}")
        print(f"  OIDC Endpoint: {oidc_endpoint if oidc_endpoint else 'NOT SET'}")
        return False
    
    # Check if provider already exists
    try:
        provider = OAuth2ProviderConfig.objects.get(slug='oidc')
        print("✓ Found existing OIDC provider, updating...")
        created = False
    except OAuth2ProviderConfig.DoesNotExist:
        provider = OAuth2ProviderConfig(slug='oidc')
        print("✓ Creating new OIDC provider...")
        created = True
    
    # Configure the provider
    provider.enabled = True
    provider.name = 'oidc'
    provider.site = site
    provider.skip_registration_form = True
    provider.skip_email_verification = True
    provider.send_welcome_email = False
    provider.visible = True
    provider.enable_sso_id_verification = False
    provider.backend_name = 'social_core.backends.open_id_connect.OpenIdConnectAuth'
    provider.key = client_id
    provider.secret = client_secret
    
    # Set other settings
    other_settings = {
        "OIDC_ENDPOINT": oidc_endpoint.rstrip('/')
    }
    provider.other_settings = json.dumps(other_settings)
    
    # Save the provider
    provider.save()
    
    if created:
        print("✅ Successfully created OIDC provider!")
    else:
        print("✅ Successfully updated OIDC provider!")
    
    # Display the configuration
    print("\nProvider Configuration:")
    print(f"  Name: {provider.name}")
    print(f"  Slug: {provider.slug}")
    print(f"  Backend: {provider.backend_name}")
    print(f"  Client ID: {provider.key}")
    print(f"  Skip registration: {provider.skip_registration_form}")
    print(f"  Skip email verification: {provider.skip_email_verification}")
    print(f"  OIDC Endpoint: {oidc_endpoint}")
    
    return True


def verify_configuration():
    """Verify the OIDC configuration is working"""
    print("\nVerifying configuration...")
    print("-" * 60)
    
    # Check if provider is enabled
    try:
        provider = OAuth2ProviderConfig.objects.get(slug='oidc', enabled=True)
        print("✅ OIDC provider is enabled")
    except OAuth2ProviderConfig.DoesNotExist:
        print("❌ OIDC provider not found or not enabled!")
        return False
    
    # Check authentication backends
    if 'social_core.backends.open_id_connect.OpenIdConnectAuth' in settings.AUTHENTICATION_BACKENDS:
        print("✅ OpenIdConnectAuth backend is configured")
    else:
        print("❌ OpenIdConnectAuth backend not in AUTHENTICATION_BACKENDS!")
        return False
    
    # Check third party auth is enabled
    if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False):
        print("✅ Third party auth is enabled")
    else:
        print("❌ ENABLE_THIRD_PARTY_AUTH is False!")
        return False
    
    return True


if __name__ == '__main__':
    print("OIDC Provider Configuration Script")
    print("=" * 60)
    
    if configure_oidc_provider():
        if verify_configuration():
            print("\n✅ OIDC provider is properly configured!")
            print("\nNext steps:")
            print("1. Restart LMS: tutor local restart lms")
            print("2. Clear browser cookies")
            print("3. Try logging in again at http://91.107.146.137:8000/")
            print("\nMake sure your Zitadel application has this redirect URL:")
            print("  http://91.107.146.137:8000/auth/complete/oidc/")
        else:
            print("\n❌ Configuration verification failed!")
    else:
        print("\n❌ Failed to configure OIDC provider!")