#!/usr/bin/env python3
"""Test script for the Soukchay API."""

import os
import sys
import requests
import time

# Add the api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_health():
    """Test health endpoint."""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_workers():
    """Test workers endpoint."""
    try:
        response = requests.get("http://localhost:8000/workers")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Workers endpoint returned {len(data)} records")
            if data:
                print(f"Sample worker: {data[0].get('data_id', 'N/A')}")
            return True
        else:
            print(f"❌ Workers endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Workers endpoint error: {e}")
        return False

def test_stats():
    """Test stats endpoint."""
    try:
        response = requests.get("http://localhost:8000/workers/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats endpoint passed")
            print(f"Total workers: {data.get('total', 0)}")
            print(f"By status: {data.get('by_status', {})}")
            return True
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Soukchay API...")
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health),
        ("Workers", test_workers),
        ("Stats", test_stats),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n🔍 Testing {name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {name} failed")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())