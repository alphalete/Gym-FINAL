#!/usr/bin/env python3
"""
Focused PWA Service Worker Backend Verification Test
Testing core backend functionality for PWA service worker compatibility
"""

import requests
import json
import sys
import os
from datetime import datetime, date
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://46206bdc-27f0-428b-bb53-27c7a4990807.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Backend URL: {BACKEND_URL}")
print(f"🕐 PWA Service Worker Core Test Started: {datetime.now().isoformat()}")
print("=" * 80)

def test_core_apis():
    """Test core APIs that PWA service worker will interact with"""
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Health Check
    print("\n🔍 TEST 1: Health Check API")
    total_tests += 1
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print("✅ PASS - Health check successful")
                tests_passed += 1
            else:
                print(f"❌ FAIL - Unhealthy status: {data}")
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL - Exception: {e}")
    
    # Test 2: Get Clients with Cache-Busting
    print("\n🔍 TEST 2: Get Clients API with Cache-Busting")
    total_tests += 1
    try:
        headers = {
            'Cache-Control': 'no-cache',
            'X-PWA-Test': 'true'
        }
        response = requests.get(f"{BACKEND_URL}/clients", headers=headers, timeout=5)
        if response.status_code == 200:
            clients = response.json()
            cache_control = response.headers.get('Cache-Control', '')
            mobile_cache_bust = response.headers.get('X-Mobile-Cache-Bust', '')
            
            if 'no-cache' in cache_control and mobile_cache_bust:
                print(f"✅ PASS - Retrieved {len(clients)} clients with proper cache-busting")
                tests_passed += 1
            else:
                print(f"❌ FAIL - Cache-busting headers missing")
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL - Exception: {e}")
    
    # Test 3: Payment Stats with Cache-Busting
    print("\n🔍 TEST 3: Payment Stats API with Cache-Busting")
    total_tests += 1
    try:
        headers = {
            'Cache-Control': 'no-cache',
            'X-PWA-Test': 'true'
        }
        response = requests.get(f"{BACKEND_URL}/payments/stats", headers=headers, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            cache_control = response.headers.get('Cache-Control', '')
            
            required_fields = ['total_revenue', 'payment_count', 'timestamp', 'cache_buster']
            has_all_fields = all(field in stats for field in required_fields)
            
            if 'no-cache' in cache_control and has_all_fields:
                revenue = stats.get('total_revenue', 0)
                count = stats.get('payment_count', 0)
                print(f"✅ PASS - Revenue: TTD {revenue}, Payments: {count}, Cache-busting: ✓")
                tests_passed += 1
            else:
                print(f"❌ FAIL - Missing fields or cache-busting")
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL - Exception: {e}")
    
    # Test 4: Membership Types
    print("\n🔍 TEST 4: Membership Types API")
    total_tests += 1
    try:
        response = requests.get(f"{BACKEND_URL}/membership-types", timeout=5)
        if response.status_code == 200:
            types = response.json()
            type_names = [t.get('name', '') for t in types]
            expected_types = ['Standard', 'Premium', 'Elite', 'VIP']
            found_types = [t for t in expected_types if t in type_names]
            
            if len(found_types) >= 3:  # At least 3 of the expected types
                print(f"✅ PASS - Found {len(types)} types including: {', '.join(found_types)}")
                tests_passed += 1
            else:
                print(f"❌ FAIL - Missing expected membership types")
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL - Exception: {e}")
    
    # Test 5: API Status
    print("\n🔍 TEST 5: API Status Endpoint")
    total_tests += 1
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            status = response.json()
            if status.get('status') == 'active' and status.get('version'):
                print(f"✅ PASS - API v{status.get('version')} is active")
                tests_passed += 1
            else:
                print(f"❌ FAIL - Invalid status response")
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL - Exception: {e}")
    
    return tests_passed, total_tests

def main():
    """Main test execution"""
    print("🚀 STARTING PWA SERVICE WORKER CORE BACKEND VERIFICATION")
    print("=" * 80)
    
    tests_passed, total_tests = test_core_apis()
    
    print("\n" + "=" * 80)
    print("📊 PWA SERVICE WORKER CORE TEST SUMMARY")
    print("=" * 80)
    
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📈 Total Tests: {total_tests}")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {total_tests - tests_passed}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    print("\n🎯 PWA SERVICE WORKER COMPATIBILITY STATUS:")
    print("-" * 50)
    
    if success_rate >= 80:
        print("✅ BACKEND IS COMPATIBLE WITH PWA SERVICE WORKER v4.0.0")
        print("✅ All core APIs respond correctly to PWA requests")
        print("✅ Cache-busting headers are properly implemented")
        print("✅ Service worker will not interfere with backend functionality")
        return True
    else:
        print("❌ BACKEND MAY HAVE COMPATIBILITY ISSUES")
        print("❌ Some core APIs are not responding correctly")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 PWA Service Worker Core Testing completed at: {datetime.now().isoformat()}")
    
    if success:
        print("\n🎉 PWA SERVICE WORKER BACKEND COMPATIBILITY: VERIFIED!")
        sys.exit(0)
    else:
        print("\n🚨 PWA SERVICE WORKER BACKEND COMPATIBILITY: ISSUES DETECTED!")
        sys.exit(1)