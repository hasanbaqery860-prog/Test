#!/usr/bin/env python3
"""
Test script to verify both legacy and MFE routes redirect to SSO
"""
import requests
import sys


def test_redirects(legacy_url, mfe_url):
    """Test both legacy and MFE authentication routes"""
    
    print("Testing SSO Redirects")
    print("=" * 70)
    
    # Test URLs
    test_cases = [
        ("Legacy login", f"{legacy_url}/login"),
        ("Legacy register", f"{legacy_url}/register"),
        ("Legacy API login", f"{legacy_url}/user_api/v1/account/login_session/"),
        ("MFE authn login", f"{mfe_url}/authn/login"),
        ("MFE authn register", f"{mfe_url}/authn/register"),
    ]
    
    for name, url in test_cases:
        try:
            response = requests.get(url, allow_redirects=False, timeout=10)
            
            print(f"\n{name}:")
            print(f"  URL: {url}")
            print(f"  Status: {response.status_code}")
            
            if response.status_code in [301, 302]:
                location = response.headers.get('Location', '')
                print(f"  Redirects to: {location}")
                
                # Check if it's redirecting to SSO (should contain /auth/login/oidc/)
                if '/auth/login/oidc/' in location:
                    print("  ✓ CORRECT - Redirects to SSO")
                elif 'apps.local.openedx.io' in location or ':1999' in location:
                    print("  ✗ WRONG - Redirects to MFE!")
                else:
                    print("  ? Unknown redirect target")
            else:
                print("  ✗ No redirect - something's wrong!")
                
        except Exception as e:
            print(f"\n{name}:")
            print(f"  Error: {str(e)}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_both_routes.py <legacy_url> <mfe_url>")
        print("Example: python test_both_routes.py http://localhost:8000 http://apps.local.openedx.io:1999")
        sys.exit(1)
    
    legacy_url = sys.argv[1].rstrip('/')
    mfe_url = sys.argv[2].rstrip('/')
    
    test_redirects(legacy_url, mfe_url)