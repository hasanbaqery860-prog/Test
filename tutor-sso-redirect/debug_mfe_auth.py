#!/usr/bin/env python3
"""
Debug script to check MFE authentication configuration
"""
import os
import sys
import django

# Set up Django environment
sys.path.append('/openedx/edx-platform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.tutor.production')
django.setup()

from django.conf import settings

print("MFE Authentication Configuration Debug")
print("=" * 70)

print("\n1. MFE Configuration:")
print(f"   ENABLE_AUTHN_MICROFRONTEND: {settings.FEATURES.get('ENABLE_AUTHN_MICROFRONTEND', False)}")
print(f"   AUTHN_MICROFRONTEND_URL: {getattr(settings, 'AUTHN_MICROFRONTEND_URL', 'NOT SET')}")
print(f"   AUTHN_MICROFRONTEND_DOMAIN: {getattr(settings, 'AUTHN_MICROFRONTEND_DOMAIN', 'NOT SET')}")

print("\n2. Third Party Auth in MFE:")
print(f"   AUTHN_MICROFRONTEND_THIRD_PARTY_AUTH_ENABLED: {getattr(settings, 'AUTHN_MICROFRONTEND_THIRD_PARTY_AUTH_ENABLED', False)}")
print(f"   AUTHN_MICROFRONTEND_THIRD_PARTY_AUTH_ONLY: {getattr(settings, 'AUTHN_MICROFRONTEND_THIRD_PARTY_AUTH_ONLY', False)}")

print("\n3. MFE Config:")
mfe_config = getattr(settings, 'MFE_CONFIG', {})
if mfe_config:
    for key, value in mfe_config.items():
        print(f"   {key}: {value}")
else:
    print("   MFE_CONFIG not set")

print("\n4. Plugin Settings:")
print(f"   SSO_USE_MFE: {getattr(settings, 'SSO_USE_MFE', 'NOT SET')}")
print(f"   SSO_MFE_URL: {getattr(settings, 'SSO_MFE_URL', 'NOT SET')}")
print(f"   SSO_REDIRECT_URL: {getattr(settings, 'SSO_REDIRECT_URL', 'NOT SET')}")

print("\n5. LMS Host Configuration:")
print(f"   LMS_HOST: {getattr(settings, 'LMS_HOST', 'NOT SET')}")
print(f"   LMS_ROOT_URL: {getattr(settings, 'LMS_ROOT_URL', 'NOT SET')}")

print("\n" + "=" * 70)
print("\nTroubleshooting Empty MFE Page:")
print("1. Check if MFE is running: tutor local status")
print("2. Check MFE logs: tutor local logs -f mfe")
print("3. Access MFE directly: http://apps.local.openedx.io:1999")
print("4. Check browser console for JavaScript errors")
print("5. Ensure hosts file has: 127.0.0.1 apps.local.openedx.io")
print("\nIf MFE is not loading:")
print("- The MFE container might not be running")
print("- The MFE might need to be rebuilt: tutor images build mfe")
print("- Try accessing: http://apps.local.openedx.io:1999/learning")