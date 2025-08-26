#!/usr/bin/env python3
"""
Test authentication flow and session handling
"""
import requests
import sys
from urllib.parse import urlparse, parse_qs

def test_auth_flow(base_url):
    """Test the complete authentication flow"""
    
    print(f"Testing Authentication Flow")
    print(f"Base URL: {base_url}")
    print("=" * 70)
    
    session = requests.Session()
    
    # Step 1: Access the main page
    print("\n1. Accessing main page...")
    response = session.get(base_url)
    print(f"   Status: {response.status_code}")
    
    # Check if we have a session cookie
    session_cookie = session.cookies.get('sessionid')
    if session_cookie:
        print(f"   ✓ Session cookie present: {session_cookie[:20]}...")
    else:
        print("   ✗ No session cookie found")
    
    # Step 2: Try to access login
    print("\n2. Accessing /login...")
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
    
    # Step 3: Check OIDC endpoint
    print("\n3. Checking OIDC endpoint...")
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
    
    # Step 4: Check session cookie after OIDC redirect
    session_cookie_after = session.cookies.get('sessionid')
    if session_cookie_after:
        print(f"   ✓ Session cookie maintained: {session_cookie_after[:20]}...")
        if session_cookie_after != session_cookie:
            print("   ✓ Session cookie updated")
        else:
            print("   - Session cookie unchanged")
    else:
        print("   ✗ Session cookie lost after OIDC redirect")
    
    # Step 5: Check auth complete endpoint
    print("\n4. Checking auth complete endpoint...")
    complete_url = f"{base_url}/auth/complete/oidc/"
    response = session.get(complete_url, allow_redirects=False)
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print("   ✓ Endpoint exists (400 is expected without valid OAuth response)")
    elif response.status_code == 404:
        print("   ✗ Endpoint not found - third party auth might not be enabled")
    elif response.status_code in [301, 302]:
        location = response.headers.get('Location', '')
        print(f"   Redirects to: {location}")
    
    # Step 6: Check final session state
    print("\n5. Final session state...")
    final_session_cookie = session.cookies.get('sessionid')
    if final_session_cookie:
        print(f"   ✓ Final session cookie: {final_session_cookie[:20]}...")
    else:
        print("   ✗ No final session cookie")
    
    # Step 7: Check if we can access protected content
    print("\n6. Testing protected content access...")
    dashboard_url = f"{base_url}/dashboard"
    response = session.get(dashboard_url, allow_redirects=False)
    
    print(f"   Dashboard status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Dashboard accessible (user authenticated)")
    elif response.status_code in [301, 302]:
        location = response.headers.get('Location', '')
        print(f"   Redirects to: {location}")
        if '/login' in location or '/auth' in location:
            print("   ✗ User not authenticated - redirected to login")
        else:
            print("   ? Unexpected redirect")
    else:
        print(f"   ? Unexpected status: {response.status_code}")
    
    print("\n" + "=" * 70)
    print("\nDiagnosis:")
    
    if not session_cookie:
        print("❌ No session cookie created - session handling issue")
    elif session_cookie != final_session_cookie:
        print("❌ Session cookie changed during flow - potential session loss")
    else:
        print("✅ Session cookie maintained throughout flow")
    
    print("\nRecommendations:")
    print("1. Clear browser cookies and try again")
    print("2. Check if accessing via domain name instead of IP helps")
    print("3. Ensure SESSION_COOKIE_DOMAIN is set to None in settings")
    print("4. Check browser developer tools for cookie issues")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_auth_flow.py <base_url>")
        print("Example: python test_auth_flow.py http://91.107.146.137:8000")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    test_auth_flow(base_url)