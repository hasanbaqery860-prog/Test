#!/usr/bin/env python3
"""
Test OIDC authentication flow
"""
import requests
import sys
from urllib.parse import urlparse, parse_qs


def test_oidc_flow(base_url):
    """Test the OIDC authentication flow"""
    
    print(f"Testing OIDC Authentication Flow")
    print(f"Base URL: {base_url}")
    print("=" * 70)
    
    session = requests.Session()
    
    # Step 1: Try to access login
    print("\n1. Accessing /login...")
    login_url = f"{base_url}/login"
    response = session.get(login_url, allow_redirects=False)
    
    print(f"   Status: {response.status_code}")
    if response.status_code in [301, 302]:
        location = response.headers.get('Location', '')
        print(f"   Redirects to: {location}")
        
        if '/auth/login/oidc/' in location:
            print("   ✓ Correctly redirects to OIDC endpoint")
        else:
            print("   ✗ Wrong redirect target!")
    
    # Step 2: Check OIDC endpoint
    print("\n2. Checking OIDC endpoint...")
    oidc_url = f"{base_url}/auth/login/oidc/"
    response = session.get(oidc_url, allow_redirects=False)
    
    print(f"   Status: {response.status_code}")
    if response.status_code in [301, 302]:
        location = response.headers.get('Location', '')
        print(f"   Redirects to: {location}")
        
        if 'zitadel' in location.lower() or 'oauth' in location.lower():
            print("   ✓ Redirects to Zitadel/OAuth provider")
        else:
            print("   ? Check if this is your SSO provider")
    elif response.status_code == 200:
        print("   ✗ OIDC endpoint returns 200 - provider might not be configured!")
        if "Can't fetch" in response.text:
            print("   ✗ Error: Provider not configured in Django admin")
    
    # Step 3: Check auth complete endpoint
    print("\n3. Checking auth complete endpoint...")
    complete_url = f"{base_url}/auth/complete/oidc/"
    response = session.get(complete_url, allow_redirects=False)
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print("   ✓ Endpoint exists (400 is expected without valid OAuth response)")
    elif response.status_code == 404:
        print("   ✗ Endpoint not found - third party auth might not be enabled")
    
    # Step 4: Check if third party auth is enabled
    print("\n4. Checking third party auth status...")
    admin_url = f"{base_url}/admin/"
    response = session.get(admin_url, allow_redirects=False)
    if response.status_code in [200, 302]:
        print("   ✓ Admin interface accessible")
    else:
        print("   ? Admin interface not accessible")
    
    print("\n" + "=" * 70)
    print("\nNext steps:")
    print("1. Ensure OIDC provider is configured in Django admin")
    print("2. Check logs: tutor local logs -f lms | grep -E '(social|oauth)'")
    print("3. Try manual login and watch the flow")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_oidc_auth.py <base_url>")
        print("Example: python test_oidc_auth.py http://localhost:8000")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    test_oidc_flow(base_url)