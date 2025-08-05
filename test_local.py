#!/usr/bin/env python3
"""
Simple test script for local development scenarios
Tests IP detection when REMOTE_ADDR is localhost/127.0.0.1
"""

import requests
import json

# API Configuration
BASE_URL = "http://localhost:8080"
API_KEY = "web_1234567890abcdef"

def test_basic_request():
    """Test basic request without any special headers"""
    print("🔍 Testing Basic Request...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/detect/simple", 
                              headers={"X-API-Key": API_KEY})
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Detected IP: {data.get('ip', 'unknown')}")
            print(f"Browser: {data.get('browser', 'unknown')}")
            print(f"OS: {data.get('os', 'unknown')}")
        else:
            print(f"Error: {response.text}")
        print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print()

def test_with_forwarded_headers():
    """Test with X-Forwarded-For headers"""
    print("🌐 Testing with X-Forwarded-For Headers...")
    
    headers = {
        "X-API-Key": API_KEY,
        "X-Forwarded-For": "203.0.113.1, 192.168.1.100",
        "X-Real-IP": "203.0.113.1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/detect/simple", headers=headers)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Detected IP: {data.get('ip', 'unknown')}")
            print(f"Expected: 203.0.113.1")
            print(f"Success: {data.get('ip') == '203.0.113.1'}")
        else:
            print(f"Error: {response.text}")
        print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print()

def test_debug_endpoint():
    """Test the debug endpoint to see all available information"""
    print("🐛 Testing Debug Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/debug/ip-info")
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Debug Information:")
            print(f"  Remote Addr: {data.get('remote_addr', 'unknown')}")
            print(f"  Detected IP: {data.get('detected_ip', 'unknown')}")
            print(f"  Host Header: {data.get('host_header', 'unknown')}")
            print(f"  User Agent: {data.get('user_agent', 'unknown')}")
            print(f"  Is Development: {data.get('is_development', False)}")
            
            # Show all headers
            print("\nAll Headers:")
            for key, value in data.get('all_headers', {}).items():
                print(f"  {key}: {value}")
        else:
            print(f"Error: {response.text}")
        print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print()

def test_localhost_scenarios():
    """Test various localhost scenarios"""
    print("🏠 Testing Localhost Scenarios...")
    
    scenarios = [
        {
            "name": "Pure Localhost",
            "headers": {"X-API-Key": API_KEY}
        },
        {
            "name": "Localhost with Custom IP",
            "headers": {
                "X-API-Key": API_KEY,
                "X-Forwarded-For": "8.8.8.8",
                "X-Real-IP": "8.8.8.8"
            }
        },
        {
            "name": "Localhost with Private IP",
            "headers": {
                "X-API-Key": API_KEY,
                "X-Forwarded-For": "192.168.1.100",
                "X-Real-IP": "192.168.1.100"
            }
        },
        {
            "name": "Localhost with Multiple IPs",
            "headers": {
                "X-API-Key": API_KEY,
                "X-Forwarded-For": "203.0.113.1, 192.168.1.100, 127.0.0.1",
                "X-Real-IP": "203.0.113.1"
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"Testing: {scenario['name']}")
        try:
            response = requests.get(f"{BASE_URL}/api/detect/simple", 
                                  headers=scenario['headers'])
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Detected IP: {data.get('ip', 'unknown')}")
                print(f"  Success: {data.get('ip') != '127.0.0.1' and data.get('ip') != 'localhost'}")
            else:
                print(f"  Error: {response.status_code}")
        except Exception as e:
            print(f"  Error: {str(e)}")
        print()

def test_infrastructure_tools():
    """Test various infrastructure and API testing tools"""
    print("🛠️ Testing Infrastructure Tools...")
    
    tools = [
        {
            "name": "Postman",
            "headers": {
                "X-API-Key": API_KEY,
                "User-Agent": "PostmanRuntime/7.32.3",
                "X-Postman-Client-IP": "203.0.113.1"
            }
        },
        {
            "name": "Insomnia",
            "headers": {
                "X-API-Key": API_KEY,
                "User-Agent": "Insomnia/8.6.1",
                "X-Insomnia-Client-IP": "203.0.113.2"
            }
        },
        {
            "name": "curl",
            "headers": {
                "X-API-Key": API_KEY,
                "User-Agent": "curl/7.68.0",
                "X-Curl-Client-IP": "203.0.113.3"
            }
        },
        {
            "name": "Python Requests",
            "headers": {
                "X-API-Key": API_KEY,
                "User-Agent": "python-requests/2.28.1"
            }
        },
        {
            "name": "Kubernetes Health Check",
            "headers": {
                "User-Agent": "kube-probe/1.20",
                "X-Request-ID": "k8s-health-123",
                "X-Service-Name": "kube-probe"
            }
        },
        {
            "name": "Prometheus Monitoring",
            "headers": {
                "User-Agent": "Prometheus/2.30.0",
                "X-Request-ID": "prometheus-metrics-456",
                "X-Service-Name": "prometheus"
            }
        },
        {
            "name": "Nginx Load Balancer",
            "headers": {
                "User-Agent": "nginx/1.18.0",
                "X-Forwarded-For": "10.0.0.1, 192.168.1.100",
                "X-Real-IP": "10.0.0.1",
                "X-Request-ID": "nginx-lb-789"
            }
        }
    ]
    
    for tool in tools:
        print(f"Testing: {tool['name']}")
        try:
            response = requests.get(f"{BASE_URL}/api/detect/simple", 
                                  headers=tool['headers'])
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Detected IP: {data.get('ip', 'unknown')}")
                print(f"  Client Type: {data.get('device_type', 'unknown')}")
                print(f"  Browser: {data.get('browser', 'unknown')}")
            else:
                print(f"  Error: {response.status_code}")
        except Exception as e:
            print(f"  Error: {str(e)}")
        print()

def main():
    """Run all local development tests"""
    print("🚀 Starting Local Development Tests...")
    print("=" * 50)
    
    test_basic_request()
    test_with_forwarded_headers()
    test_debug_endpoint()
    test_localhost_scenarios()
    test_infrastructure_tools()
    
    print("🎉 Local development tests completed!")
    print("\n💡 Tips for local development:")
    print("  - Use X-Forwarded-For header to simulate real IPs")
    print("  - Check /api/debug/ip-info for detailed information")
    print("  - The API will prioritize non-localhost IPs when available")
    print("  - Infrastructure tools are automatically detected")
    print("  - Use /api/infrastructure/status for monitoring")

if __name__ == "__main__":
    main()