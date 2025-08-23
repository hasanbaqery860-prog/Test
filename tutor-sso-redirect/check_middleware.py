#!/usr/bin/env python3
"""
Script to check if SSO redirect middleware is properly loaded
Run this inside the LMS container
"""

import os
import sys
import django

# Set up Django environment
sys.path.append('/openedx/edx-platform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.tutor.production')
django.setup()

from django.conf import settings

print("Checking SSO Redirect Plugin Configuration")
print("=" * 70)

# Check if middleware is loaded
print("\n1. Middleware Stack (first 10):")
for i, mw in enumerate(settings.MIDDLEWARE[:10]):
    print(f"   {i}: {mw}")

# Check if our middleware is first
if settings.MIDDLEWARE and 'sso_redirect' in settings.MIDDLEWARE[0].lower():
    print("\n✓ SSO Redirect middleware is FIRST in the stack!")
else:
    print("\n✗ SSO Redirect middleware is NOT first in the stack!")

# Check SSO settings
print("\n2. SSO Settings:")
print(f"   SSO_REDIRECT_ENABLED: {getattr(settings, 'SSO_REDIRECT_ENABLED', 'NOT SET')}")
print(f"   SSO_REDIRECT_URL: {getattr(settings, 'SSO_REDIRECT_URL', 'NOT SET')}")
print(f"   LOGIN_URL: {settings.LOGIN_URL}")

# Check authentication settings
print("\n3. Authentication Settings:")
features = [
    'DISABLE_ACCOUNT_REGISTRATION',
    'ENABLE_COMBINED_LOGIN_REGISTRATION',
    'ALLOW_PUBLIC_ACCOUNT_CREATION',
    'ENABLE_AUTHN_MICROFRONTEND',
    'ENABLE_PASSWORD_RESET'
]
for feature in features:
    value = settings.FEATURES.get(feature, 'NOT SET')
    print(f"   {feature}: {value}")

# Check if module exists
print("\n4. Module Check:")
try:
    import lms.djangoapps.sso_redirect
    print("   ✓ sso_redirect module is loaded")
    print(f"   Module location: {lms.djangoapps.sso_redirect.__name__}")
    if hasattr(lms.djangoapps.sso_redirect, 'SSORedirectMiddleware'):
        print("   ✓ SSORedirectMiddleware class exists")
    else:
        print("   ✗ SSORedirectMiddleware class NOT FOUND")
except ImportError as e:
    print(f"   ✗ sso_redirect module NOT loaded: {e}")

print("\n" + "=" * 70)