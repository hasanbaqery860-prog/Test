#!/usr/bin/env python3
"""
Test if MFE is accessible
"""
import requests
import sys

def test_mfe_availability(mfe_url="http://apps.local.openedx.io:1999"):
    """Test if MFE is running and accessible"""
    print(f"Testing MFE availability at: {mfe_url}")
    print("-" * 60)
    
    # Test different MFE endpoints
    endpoints = [
        "/",
        "/authn/login",
        "/learning",
    ]
    
    for endpoint in endpoints:
        url = f"{mfe_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5, allow_redirects=False)
            print(f"\n{url}")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✓ Accessible")
                # Check if it's actually the MFE
                if "microfrontend" in response.text.lower() or "mfe" in response.text.lower():
                    print(f"  ✓ Confirmed MFE content")
                else:
                    print(f"  ? Content doesn't look like MFE")
            elif response.status_code in [301, 302]:
                print(f"  → Redirects to: {response.headers.get('Location', 'Unknown')}")
            else:
                print(f"  ✗ Not accessible")
        except requests.exceptions.ConnectionError:
            print(f"\n{url}")
            print(f"  ✗ Connection refused - MFE might not be running")
        except requests.exceptions.Timeout:
            print(f"\n{url}")
            print(f"  ✗ Timeout - MFE might be slow or not responding")
        except Exception as e:
            print(f"\n{url}")
            print(f"  ✗ Error: {str(e)}")
    
    print("\n" + "-" * 60)
    print("\nIf MFE is not accessible:")
    print("1. Check if MFE container is running: docker ps | grep mfe")
    print("2. Start MFE: tutor local start -d mfe")
    print("3. Check MFE logs: tutor local logs -f mfe")
    print("4. Rebuild MFE if needed: tutor images build mfe")
    print("\nAlternatively, disable MFE mode in the plugin:")
    print("  tutor config save --set SSO_USE_MFE=false")
    print("  tutor local restart")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_mfe_availability(sys.argv[1])
    else:
        test_mfe_availability()