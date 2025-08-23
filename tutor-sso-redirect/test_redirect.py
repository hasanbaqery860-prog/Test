#!/usr/bin/env python3
"""
Test script to verify SSO redirect is working properly
"""
import requests
import sys


def test_sso_redirect(base_url, expected_redirect="/auth/login/oidc/"):
    """Test that login/register URLs redirect to SSO"""
    
    # URLs to test
    test_urls = [
        "/login",
        "/register",
        "/signin",
        "/signup",
    ]
    
    print(f"Testing SSO redirect on {base_url}")
    print(f"Expected redirect: {expected_redirect}")
    print("-" * 50)
    
    all_passed = True
    
    for url in test_urls:
        full_url = base_url.rstrip('/') + url
        try:
            # Don't follow redirects automatically
            response = requests.get(full_url, allow_redirects=False, timeout=10)
            
            if response.status_code in [301, 302]:
                redirect_location = response.headers.get('Location', '')
                if expected_redirect in redirect_location:
                    print(f"✓ {url} -> {redirect_location}")
                else:
                    print(f"✗ {url} -> {redirect_location} (expected {expected_redirect})")
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
    if len(sys.argv) < 2:
        print("Usage: python test_redirect.py <base_url> [expected_redirect]")
        print("Example: python test_redirect.py http://local.overhang.io")
        print("Example: python test_redirect.py http://local.overhang.io /custom/sso/")
        sys.exit(1)
    
    base_url = sys.argv[1]
    expected_redirect = sys.argv[2] if len(sys.argv) > 2 else "/auth/login/oidc/"
    
    exit_code = test_sso_redirect(base_url, expected_redirect)
    sys.exit(exit_code)