#!/usr/bin/env python3
"""
Verify authentication fix for OIDC/Zitadel integration
Run this after applying the plugin update
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
from datetime import datetime

User = get_user_model()

print("Authentication Fix Verification")
print("=" * 70)

# Check if custom pipeline is loaded
print("\n1. Checking Custom Pipeline:")
pipeline = getattr(settings, 'SOCIAL_AUTH_PIPELINE', [])
custom_step = 'lms.djangoapps.sso_pipeline.ensure_user_login'
if custom_step in pipeline:
    print(f"   ✓ Custom pipeline step '{custom_step}' is configured")
    print(f"   Position: {pipeline.index(custom_step) + 1}/{len(pipeline)}")
else:
    print(f"   ✗ Custom pipeline step '{custom_step}' NOT found!")

# Check session settings
print("\n2. Session Configuration:")
print(f"   SESSION_SAVE_EVERY_REQUEST: {settings.SESSION_SAVE_EVERY_REQUEST}")
print(f"   SESSION_COOKIE_DOMAIN: {settings.SESSION_COOKIE_DOMAIN}")
print(f"   SESSION_ENGINE: {settings.SESSION_ENGINE}")
print(f"   SESSION_COOKIE_NAME: {settings.SESSION_COOKIE_NAME}")
print(f"   SESSION_COOKIE_AGE: {settings.SESSION_COOKIE_AGE} seconds")

# Check if login user pipeline is present
if 'social_django.pipeline.login_user' in pipeline:
    print("   ✓ social_django.pipeline.login_user is in pipeline")
else:
    print("   ✗ social_django.pipeline.login_user NOT in pipeline!")

# Check redirect URLs
print("\n3. Redirect URLs:")
print(f"   LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"   SOCIAL_AUTH_LOGIN_REDIRECT_URL: {getattr(settings, 'SOCIAL_AUTH_LOGIN_REDIRECT_URL', 'NOT SET')}")
print(f"   SOCIAL_AUTH_NEW_USER_REDIRECT_URL: {getattr(settings, 'SOCIAL_AUTH_NEW_USER_REDIRECT_URL', 'NOT SET')}")

# Check active sessions
print("\n4. Active Sessions:")
try:
    active_sessions = Session.objects.filter(expire_date__gte=datetime.now())
    print(f"   Total active sessions: {active_sessions.count()}")
    
    # Check for recent social auth users with sessions
    recent_social_users = UserSocialAuth.objects.select_related('user').order_by('-id')[:5]
    if recent_social_users:
        print("\n5. Recent Social Auth Users:")
        for su in recent_social_users:
            print(f"   User: {su.user.username} | Email: {su.user.email}")
            print(f"   Provider: {su.provider} | UID: {su.uid}")
            print(f"   Last login: {su.user.last_login}")
            print("   ---")
    else:
        print("\n5. No social auth users found yet")
        
except Exception as e:
    print(f"   Error checking sessions: {e}")

print("\n6. Authentication Backend Check:")
for backend in settings.AUTHENTICATION_BACKENDS:
    print(f"   - {backend}")
    
# Check if OIDC is properly configured
print("\n7. OIDC Configuration:")
print(f"   SOCIAL_AUTH_OIDC_KEY: {'SET' if getattr(settings, 'SOCIAL_AUTH_OIDC_KEY', '') else 'NOT SET'}")
print(f"   SOCIAL_AUTH_OIDC_SECRET: {'SET' if getattr(settings, 'SOCIAL_AUTH_OIDC_SECRET', '') else 'NOT SET'}")
print(f"   SOCIAL_AUTH_OIDC_OIDC_ENDPOINT: {getattr(settings, 'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT', 'NOT SET')}")

print("\n" + "=" * 70)
print("\nTroubleshooting:")
print("1. If custom pipeline step is missing, restart services")
print("2. Check Django admin for OIDC provider configuration")
print("3. Monitor logs during login: tutor local logs -f lms | grep -E 'SSO|social|oidc'")
print("4. Clear browser cookies and try logging in again")
print("5. Ensure Zitadel redirect URL is: http://91.107.146.137:8000/auth/complete/oidc/")