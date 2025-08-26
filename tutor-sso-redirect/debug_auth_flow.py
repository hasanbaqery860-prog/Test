#!/usr/bin/env python3
"""
Comprehensive debug script for Zitadel/OIDC authentication flow
"""
import os
import sys
import django

# Set up Django environment
sys.path.append('/openedx/edx-platform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.tutor.production')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from social_django.models import UserSocialAuth
from django.contrib.sessions.models import Session
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
from datetime import datetime
import json

User = get_user_model()

print("=" * 80)
print("COMPREHENSIVE AUTHENTICATION FLOW DEBUG")
print("=" * 80)

# 1. Check OAuth2 Provider Configuration in Database
print("\n1. OAuth2 Provider Configuration (Database):")
print("-" * 40)
try:
    providers = OAuth2ProviderConfig.objects.all()
    if providers:
        for provider in providers:
            print(f"Provider: {provider.name}")
            print(f"  - Enabled: {provider.enabled}")
            print(f"  - Slug: {provider.slug}")
            print(f"  - Backend: {provider.backend_name}")
            print(f"  - Skip registration: {provider.skip_registration_form}")
            print(f"  - Skip email verification: {provider.skip_email_verification}")
            print(f"  - Client ID: {'SET' if provider.key else 'NOT SET'}")
            print(f"  - Client Secret: {'SET' if provider.secret else 'NOT SET'}")
            print(f"  - Other settings: {provider.other_settings}")
            print()
    else:
        print("  ✗ NO OAuth2 providers configured in database!")
        print("  This is likely the issue - you need to configure the provider in Django admin")
except Exception as e:
    print(f"  Error checking providers: {e}")

# 2. Check OIDC Settings
print("\n2. OIDC Settings (Django Settings):")
print("-" * 40)
oidc_settings = {
    'SOCIAL_AUTH_OIDC_KEY': getattr(settings, 'SOCIAL_AUTH_OIDC_KEY', 'NOT SET'),
    'SOCIAL_AUTH_OIDC_SECRET': 'SET' if getattr(settings, 'SOCIAL_AUTH_OIDC_SECRET', '') else 'NOT SET',
    'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT': getattr(settings, 'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT', 'NOT SET'),
    'SOCIAL_AUTH_OIDC_SCOPE': getattr(settings, 'SOCIAL_AUTH_OIDC_SCOPE', 'NOT SET'),
}
for key, value in oidc_settings.items():
    print(f"  {key}: {value}")

# 3. Check Third Party Auth Feature Flags
print("\n3. Third Party Auth Feature Flags:")
print("-" * 40)
tpa_flags = {
    'ENABLE_THIRD_PARTY_AUTH': settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False),
    'ENABLE_REQUIRE_THIRD_PARTY_AUTH': settings.FEATURES.get('ENABLE_REQUIRE_THIRD_PARTY_AUTH', False),
    'ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING': settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING', False),
    'ALLOW_PUBLIC_ACCOUNT_CREATION': settings.FEATURES.get('ALLOW_PUBLIC_ACCOUNT_CREATION', False),
}
for key, value in tpa_flags.items():
    print(f"  {key}: {value}")

# 4. Authentication Pipeline
print("\n4. Authentication Pipeline:")
print("-" * 40)
pipeline = getattr(settings, 'SOCIAL_AUTH_PIPELINE', [])
for i, step in enumerate(pipeline, 1):
    print(f"  {i}. {step}")

# 5. Authentication Backends
print("\n5. Authentication Backends:")
print("-" * 40)
for backend in settings.AUTHENTICATION_BACKENDS:
    print(f"  - {backend}")

# 6. Session Configuration
print("\n6. Session Configuration:")
print("-" * 40)
session_settings = {
    'SESSION_ENGINE': settings.SESSION_ENGINE,
    'SESSION_COOKIE_NAME': settings.SESSION_COOKIE_NAME,
    'SESSION_COOKIE_DOMAIN': settings.SESSION_COOKIE_DOMAIN,
    'SESSION_COOKIE_PATH': getattr(settings, 'SESSION_COOKIE_PATH', '/'),
    'SESSION_COOKIE_SECURE': getattr(settings, 'SESSION_COOKIE_SECURE', False),
    'SESSION_COOKIE_HTTPONLY': getattr(settings, 'SESSION_COOKIE_HTTPONLY', True),
    'SESSION_COOKIE_SAMESITE': getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax'),
    'SESSION_SAVE_EVERY_REQUEST': getattr(settings, 'SESSION_SAVE_EVERY_REQUEST', False),
}
for key, value in session_settings.items():
    print(f"  {key}: {value}")

# 7. Login URLs
print("\n7. Login/Redirect URLs:")
print("-" * 40)
urls = {
    'LOGIN_URL': settings.LOGIN_URL,
    'LOGIN_REDIRECT_URL': settings.LOGIN_REDIRECT_URL,
    'LOGOUT_REDIRECT_URL': getattr(settings, 'LOGOUT_REDIRECT_URL', '/'),
    'SOCIAL_AUTH_LOGIN_REDIRECT_URL': getattr(settings, 'SOCIAL_AUTH_LOGIN_REDIRECT_URL', 'NOT SET'),
    'SOCIAL_AUTH_NEW_USER_REDIRECT_URL': getattr(settings, 'SOCIAL_AUTH_NEW_USER_REDIRECT_URL', 'NOT SET'),
}
for key, value in urls.items():
    print(f"  {key}: {value}")

# 8. Recent Social Auth Activity
print("\n8. Recent Social Auth Activity:")
print("-" * 40)
try:
    social_auths = UserSocialAuth.objects.select_related('user').order_by('-modified')[:5]
    if social_auths:
        for sa in social_auths:
            print(f"  User: {sa.user.username} ({sa.user.email})")
            print(f"    Provider: {sa.provider}")
            print(f"    UID: {sa.uid}")
            print(f"    Last login: {sa.user.last_login}")
            print(f"    Modified: {sa.modified}")
            print()
    else:
        print("  No social auth records found")
except Exception as e:
    print(f"  Error: {e}")

# 9. Active Sessions
print("\n9. Active Sessions:")
print("-" * 40)
try:
    active_sessions = Session.objects.filter(expire_date__gte=datetime.now()).count()
    print(f"  Total active sessions: {active_sessions}")
except Exception as e:
    print(f"  Error: {e}")

# 10. Middleware Check
print("\n10. Middleware Configuration:")
print("-" * 40)
sso_middleware = 'lms.djangoapps.sso_redirect.SSORedirectMiddleware'
if sso_middleware in settings.MIDDLEWARE:
    position = settings.MIDDLEWARE.index(sso_middleware)
    print(f"  ✓ SSO Redirect Middleware found at position {position}")
    print(f"  Total middleware: {len(settings.MIDDLEWARE)}")
else:
    print(f"  ✗ SSO Redirect Middleware NOT found!")

print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY:")
print("=" * 80)

# Check for common issues
issues = []

if not OAuth2ProviderConfig.objects.filter(enabled=True, slug='oidc').exists():
    issues.append("❌ No enabled OIDC provider in database - Configure in Django admin!")

if not getattr(settings, 'SOCIAL_AUTH_OIDC_KEY', ''):
    issues.append("❌ SOCIAL_AUTH_OIDC_KEY not set in settings")

if not settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False):
    issues.append("❌ ENABLE_THIRD_PARTY_AUTH is False")

if 'social_core.backends.open_id_connect.OpenIdConnectAuth' not in settings.AUTHENTICATION_BACKENDS:
    issues.append("❌ OpenIdConnectAuth backend not in AUTHENTICATION_BACKENDS")

if not getattr(settings, 'SESSION_SAVE_EVERY_REQUEST', False):
    issues.append("⚠️  SESSION_SAVE_EVERY_REQUEST is False - sessions might not persist")

if issues:
    print("\nIssues found:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n✅ Basic configuration looks OK")

print("\nNext steps to debug:")
print("1. Check Django admin at /admin/third_party_auth/oauth2providerconfig/")
print("2. Monitor logs: tutor local logs -f lms | grep -E 'social|oauth|oidc|SSO'")
print("3. Check browser developer tools for cookies after login attempt")
print("4. Try the test script: python /openedx/test_oidc_auth.py http://91.107.146.137:8000")