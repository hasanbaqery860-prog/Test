#!/usr/bin/env python3
"""
Performance test for minimal API version
"""

import requests
import time
import statistics

BASE_URL = "http://localhost:8080"
API_KEY = "web_1234567890abcdef"

def test_performance():
    """Test API performance"""
    print("🚀 Testing Minimal API Performance...")
    
    # Test basic request
    headers = {"X-API-Key": API_KEY}
    
    response_times = []
    successful_requests = 0
    total_requests = 100
    
    print(f"Making {total_requests} requests...")
    
    for i in range(total_requests):
        start_time = time.time()
        
        try:
            response = requests.get(f"{BASE_URL}/api/detect/simple", headers=headers)
            if response.status_code == 200:
                successful_requests += 1
                response_times.append((time.time() - start_time) * 1000)  # Convert to ms
        except:
            pass
    
    # Calculate statistics
    if response_times:
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        throughput = successful_requests / (sum(response_times) / 1000)  # req/sec
        
        print(f"\n📊 Performance Results:")
        print(f"  Successful Requests: {successful_requests}/{total_requests}")
        print(f"  Average Response Time: {avg_time:.2f}ms")
        print(f"  Min Response Time: {min_time:.2f}ms")
        print(f"  Max Response Time: {max_time:.2f}ms")
        print(f"  Throughput: {throughput:.0f} req/sec")
        
        # Performance rating
        if avg_time < 1:
            rating = "⭐⭐⭐⭐⭐ Excellent"
        elif avg_time < 5:
            rating = "⭐⭐⭐⭐ Good"
        elif avg_time < 10:
            rating = "⭐⭐⭐ Average"
        else:
            rating = "⭐⭐ Poor"
        
        print(f"  Performance Rating: {rating}")
    else:
        print("❌ No successful requests")

def test_functionality():
    """Test basic functionality"""
    print("\n🔍 Testing Functionality...")
    
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(f"{BASE_URL}/api/detect/simple", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"  IP: {data.get('ip', 'unknown')}")
            print(f"  Browser: {data.get('browser', 'unknown')}")
            print(f"  Response Size: {len(response.content)} bytes")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing Health Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data.get('status', 'unknown')}")
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check Error: {str(e)}")

def main():
    """Run all tests"""
    print("🎯 Minimal API Performance Test")
    print("=" * 40)
    
    test_functionality()
    test_health()
    test_performance()
    
    print("\n💡 Minimal API Benefits:")
    print("  - Ultra-fast response times")
    print("  - Minimal memory usage")
    print("  - Simple deployment")
    print("  - High throughput")
    print("  - Easy maintenance")

if __name__ == "__main__":
    main()