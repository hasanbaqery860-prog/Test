#!/usr/bin/env python3
"""
Debug script to check authentication and session status
Run this inside the LMS container after attempting login
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

User = get_user_model()

print("Authentication Debug Information")
print("=" * 70)

# Check authentication settings
print("\n1. Authentication Settings:")
print(f"   ENABLE_THIRD_PARTY_AUTH: {settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False)}")
print(f"   ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING: {settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH_AUTO_PROVISIONING', False)}")
print(f"   ALLOW_PUBLIC_ACCOUNT_CREATION: {settings.FEATURES.get('ALLOW_PUBLIC_ACCOUNT_CREATION', False)}")
print(f"   SOCIAL_AUTH_AUTO_CREATE_USERS: {getattr(settings, 'SOCIAL_AUTH_AUTO_CREATE_USERS', False)}")

# Check authentication backends
print("\n2. Authentication Backends:")
for i, backend in enumerate(settings.AUTHENTICATION_BACKENDS):
    print(f"   {i}: {backend}")

# Check social auth pipeline
print("\n3. Social Auth Pipeline:")
pipeline = getattr(settings, 'SOCIAL_AUTH_PIPELINE', [])
for i, step in enumerate(pipeline):
    print(f"   {i}: {step}")

# Check session settings
print("\n4. Session Settings:")
print(f"   SESSION_COOKIE_NAME: {settings.SESSION_COOKIE_NAME}")
print(f"   SESSION_COOKIE_DOMAIN: {settings.SESSION_COOKIE_DOMAIN}")
print(f"   SESSION_ENGINE: {settings.SESSION_ENGINE}")
print(f"   LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"   SOCIAL_AUTH_LOGIN_REDIRECT_URL: {getattr(settings, 'SOCIAL_AUTH_LOGIN_REDIRECT_URL', 'NOT SET')}")

# Check users created via social auth
print("\n5. Social Auth Users:")
try:
    social_users = UserSocialAuth.objects.all()[:5]
    if social_users:
        for su in social_users:
            print(f"   User: {su.user.username} | Provider: {su.provider} | UID: {su.uid}")
    else:
        print("   No social auth users found")
except Exception as e:
    print(f"   Error checking social users: {e}")

# Check recent users
print("\n6. Recent Users (last 5):")
try:
    recent_users = User.objects.order_by('-date_joined')[:5]
    for user in recent_users:
        print(f"   {user.username} | Email: {user.email} | Joined: {user.date_joined}")
except Exception as e:
    print(f"   Error checking users: {e}")

print("\n" + "=" * 70)