#!/usr/bin/env python3
"""
Diagnostic script to trace redirect chains and identify loops
"""
import requests
import sys
from urllib.parse import urlparse, parse_qs


def trace_redirects(start_url, max_redirects=10):
    """Trace the redirect chain from a given URL"""
    print(f"\nTracing redirects from: {start_url}")
    print("=" * 70)
    
    session = requests.Session()
    session.max_redirects = 0  # Handle redirects manually
    
    current_url = start_url
    visited_urls = []
    redirect_count = 0
    
    while redirect_count < max_redirects:
        try:
            response = session.get(current_url, allow_redirects=False, timeout=10)
            visited_urls.append((current_url, response.status_code))
            
            print(f"\n[{redirect_count + 1}] URL: {current_url}")
            print(f"    Status: {response.status_code}")
            
            # Check if it's a redirect
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                
                # Handle relative URLs
                if location.startswith('/'):
                    parsed = urlparse(current_url)
                    location = f"{parsed.scheme}://{parsed.netloc}{location}"
                
                print(f"    Redirects to: {location}")
                
                # Check for loops
                if any(location == url for url, _ in visited_urls):
                    print(f"\n⚠️  REDIRECT LOOP DETECTED!")
                    print(f"    URL {location} was already visited")
                    break
                
                current_url = location
                redirect_count += 1
            else:
                # No more redirects
                print(f"\n✓ Final destination reached")
                print(f"  Total redirects: {redirect_count}")
                break
                
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
            break
    
    if redirect_count >= max_redirects:
        print(f"\n⚠️  Maximum redirects ({max_redirects}) reached!")
    
    # Print redirect chain summary
    print("\nRedirect chain:")
    for i, (url, status) in enumerate(visited_urls):
        print(f"  {i + 1}. [{status}] {url}")
    
    return visited_urls


def check_sso_config(base_url):
    """Check SSO configuration endpoints"""
    print(f"\nChecking SSO configuration at {base_url}")
    print("=" * 70)
    
    endpoints_to_check = [
        "/auth/login/oidc/",
        "/auth/complete/oidc/",
        "/oauth2/authorize",
    ]
    
    for endpoint in endpoints_to_check:
        url = base_url.rstrip('/') + endpoint
        try:
            response = requests.get(url, allow_redirects=False, timeout=5)
            print(f"{endpoint}: {response.status_code}")
        except Exception as e:
            print(f"{endpoint}: Error - {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_redirect.py <url>")
        print("Example: python diagnose_redirect.py http://91.107.146.137:8090/ui/login/login")
        sys.exit(1)
    
    test_url = sys.argv[1]
    
    # Trace redirects
    trace_redirects(test_url)
    
    # Check SSO endpoints
    parsed = urlparse(test_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    check_sso_config(base_url)