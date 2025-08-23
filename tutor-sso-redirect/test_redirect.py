#!/usr/bin/env python3
"""
Test script to verify SSO redirect is working properly
"""
import requests
import sys


def test_sso_redirect(base_url):
    """Test that login/register URLs redirect to SSO"""
    
    # URLs to test
    test_urls = [
        "/login",
        "/register",
        "/signin",
        "/signup",
    ]
    
    print(f"Testing SSO redirect on {base_url}")
    print("-" * 50)
    
    all_passed = True
    
    for url in test_urls:
        full_url = base_url.rstrip('/') + url
        try:
            # Don't follow redirects automatically
            response = requests.get(full_url, allow_redirects=False, timeout=10)
            
            if response.status_code in [301, 302]:
                redirect_location = response.headers.get('Location', '')
                if '/auth/login/oidc/' in redirect_location:
                    print(f"✓ {url} -> {redirect_location}")
                else:
                    print(f"✗ {url} -> {redirect_location} (unexpected redirect)")
                    all_passed = False
            else:
                print(f"✗ {url} -> Status {response.status_code} (expected redirect)")
                all_passed = False
                
        except Exception as e:
            print(f"✗ {url} -> Error: {str(e)}")
            all_passed = False
    
    print("-" * 50)
    
    if all_passed:
        print("✓ All tests passed! SSO redirect is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check your configuration.")
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_redirect.py <base_url>")
        print("Example: python test_redirect.py http://local.overhang.io")
        sys.exit(1)
    
    base_url = sys.argv[1]
    exit_code = test_sso_redirect(base_url)
    sys.exit(exit_code)