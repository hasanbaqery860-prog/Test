#!/usr/bin/env python3
"""
Test script for the IP and Browser Detection API
Demonstrates usage with different client types and scenarios
"""

import requests
import json
import time
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8080"
API_KEYS = {
    "web_frontend": "web_1234567890abcdef",
    "android_app": "android_9876543210fedcba",
    "other_project": "other_abcdef1234567890"
}

# Test User Agents
TEST_USER_AGENTS = {
    "chrome_desktop": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "firefox_mobile": "Mozilla/5.0 (Android 13; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0",
    "android_app": "okhttp/4.9.3",
    "safari_ios": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Mobile/15E148 Safari/604.1",
    "edge_desktop": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
}

def test_endpoint(endpoint: str, api_key: str, user_agent: str = None, description: str = "") -> Dict[str, Any]:
    """Test an API endpoint with custom headers"""
    headers = {"X-API-Key": api_key}
    if user_agent:
        headers["User-Agent"] = user_agent
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        result = {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "data": response.json() if response.status_code == 200 else None,
            "error": response.text if response.status_code != 200 else None
        }
        
        print(f"✅ {description}")
        print(f"   Status: {response.status_code}")
        if result["success"]:
            print(f"   Response: {json.dumps(result['data'], indent=2)}")
        else:
            print(f"   Error: {result['error']}")
        print()
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ {description}")
        print(f"   Error: {str(e)}")
        print()
        return {"success": False, "error": str(e)}

def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing Health Check...")
    test_endpoint("/api/health", "", description="Health Check (No Auth Required)")

def test_simple_detection():
    """Test simple detection with different user agents"""
    print("🔍 Testing Simple Detection...")
    
    for ua_name, user_agent in TEST_USER_AGENTS.items():
        test_endpoint(
            "/api/detect/simple",
            API_KEYS["web_frontend"],
            user_agent,
            f"Simple Detection - {ua_name}"
        )

def test_full_detection():
    """Test full detection with different API keys"""
    print("📊 Testing Full Detection...")
    
    for api_key_name, api_key in API_KEYS.items():
        test_endpoint(
            "/api/detect",
            api_key,
            TEST_USER_AGENTS["chrome_desktop"],
            f"Full Detection - {api_key_name}"
        )

def test_performance_stats():
    """Test performance statistics"""
    print("📈 Testing Performance Stats...")
    test_endpoint("/api/stats", API_KEYS["web_frontend"], description="Performance Statistics")

def test_error_scenarios():
    """Test error scenarios"""
    print("⚠️ Testing Error Scenarios...")
    
    # Test without API key
    test_endpoint("/api/detect", "", description="No API Key")
    
    # Test with invalid API key
    test_endpoint("/api/detect", "invalid_key", description="Invalid API Key")
    
    # Test non-existent endpoint
    test_endpoint("/api/nonexistent", API_KEYS["web_frontend"], description="Non-existent Endpoint")

def test_local_development_scenarios():
    """Test scenarios specific to local development and testing"""
    print("🏠 Testing Local Development Scenarios...")
    
    # Test debug endpoint (no auth required)
    test_endpoint("/api/debug/ip-info", "", description="Debug IP Info (No Auth)")
    
    # Test with localhost IP
    headers = {
        "X-API-Key": API_KEYS["web_frontend"],
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/detect/simple", headers=headers)
        print(f"✅ Local Development Test")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Detected IP: {data.get('ip', 'unknown')}")
            print(f"   Is Localhost: {data.get('ip', '') in ['127.0.0.1', 'localhost', '::1']}")
        print()
    except Exception as e:
        print(f"❌ Local Development Test Error: {str(e)}")
        print()
    
    # Test with custom headers that might contain real IP
    custom_headers = {
        "X-API-Key": API_KEYS["web_frontend"],
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Forwarded-For": "203.0.113.1, 192.168.1.100",
        "X-Real-IP": "203.0.113.1",
        "Host": "localhost:8080"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/detect/simple", headers=custom_headers)
        print(f"✅ Custom Headers Test")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Detected IP: {data.get('ip', 'unknown')}")
            print(f"   Expected IP: 203.0.113.1")
        print()
    except Exception as e:
        print(f"❌ Custom Headers Test Error: {str(e)}")
        print()

def test_cache_operations():
    """Test cache operations"""
    print("🗄️ Testing Cache Operations...")
    
    # Clear cache
    try:
        response = requests.post(
            f"{BASE_URL}/api/clear-cache",
            headers={"X-API-Key": API_KEYS["web_frontend"]}
        )
        print(f"✅ Cache Clear")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print()
    except Exception as e:
        print(f"❌ Cache Clear Error: {str(e)}")
        print()

def run_performance_test():
    """Run a simple performance test"""
    print("⚡ Running Performance Test...")
    
    start_time = time.time()
    successful_requests = 0
    total_requests = 10
    
    for i in range(total_requests):
        try:
            response = requests.get(
                f"{BASE_URL}/api/detect/simple",
                headers={"X-API-Key": API_KEYS["web_frontend"]}
            )
            if response.status_code == 200:
                successful_requests += 1
        except:
            pass
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"   Total Requests: {total_requests}")
    print(f"   Successful: {successful_requests}")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Requests/sec: {total_requests/duration:.2f}")
    print()

def main():
    """Run all tests"""
    print("🚀 Starting API Tests...")
    print("=" * 50)
    
    # Test health check first
    test_health_check()
    
    # Test simple detection
    test_simple_detection()
    
    # Test full detection
    test_full_detection()
    
    # Test performance stats
    test_performance_stats()
    
    # Test error scenarios
    test_error_scenarios()
    
    # Test local development scenarios
    test_local_development_scenarios()
    
    # Test cache operations
    test_cache_operations()
    
    # Run performance test
    run_performance_test()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main()