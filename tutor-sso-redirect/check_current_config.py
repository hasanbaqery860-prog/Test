#!/usr/bin/env python3
"""
Check current SSO configuration
"""
import os
import sys
import django

# Set up Django environment
sys.path.append('/openedx/edx-platform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.tutor.production')
django.setup()

from django.conf import settings

print("Current SSO Configuration Check")
print("=" * 70)

print("\n1. SSO Plugin Settings:")
print(f"   SSO_REDIRECT_ENABLED: {getattr(settings, 'SSO_REDIRECT_ENABLED', 'NOT SET')}")
print(f"   SSO_USE_MFE: {getattr(settings, 'SSO_USE_MFE', 'NOT SET')}")
print(f"   SSO_MFE_URL: {getattr(settings, 'SSO_MFE_URL', 'NOT SET')}")
print(f"   SSO_REDIRECT_URL: {getattr(settings, 'SSO_REDIRECT_URL', 'NOT SET')}")

print("\n2. MFE Status:")
print(f"   ENABLE_AUTHN_MICROFRONTEND: {settings.FEATURES.get('ENABLE_AUTHN_MICROFRONTEND', 'NOT SET')}")
print(f"   AUTHN_MICROFRONTEND_URL: {getattr(settings, 'AUTHN_MICROFRONTEND_URL', 'NOT SET')}")

print("\n3. Login URLs:")
print(f"   LOGIN_URL: {settings.LOGIN_URL}")
print(f"   LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")

print("\n4. Middleware Check:")
middleware_list = settings.MIDDLEWARE
sso_middleware = 'lms.djangoapps.sso_redirect.SSORedirectMiddleware'
if sso_middleware in middleware_list:
    position = middleware_list.index(sso_middleware)
    print(f"   ✓ SSO Middleware found at position {position}/{len(middleware_list)}")
else:
    print(f"   ✗ SSO Middleware NOT found!")

print("\n" + "=" * 70)
print("\nTo disable MFE mode, you need to:")
print("1. Run: tutor config save --set SSO_USE_MFE=false")
print("2. Run: tutor config save")
print("3. Run: tutor local restart")
print("\nIf still redirecting to MFE after that, the image needs to be rebuilt:")
print("4. Run: tutor images build openedx")
print("5. Run: tutor local restart")