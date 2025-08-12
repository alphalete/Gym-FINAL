#!/usr/bin/env python3
"""
Backend Stability Test After Frontend Cleanup
Testing specific endpoints mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime, date

# Backend URL from environment
BACKEND_URL = "https://fitness-app-update.preview.emergentagent.com/api"

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Test a specific endpoint"""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        headers = {'Content-Type': 'application/json'}
        if method == "GET":
            response = requests.get(url, timeout=10, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10, headers=headers)
        else:
            return False, f"Unsupported method: {method}"
            
        if response.status_code == expected_status:
            return True, f"✅ {method} {endpoint} - Status: {response.status_code}"
        else:
            return False, f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}"
            
    except Exception as e:
        return False, f"❌ {method} {endpoint} - Error: {str(e)}"

def main():
    print("🔍 BACKEND STABILITY TEST AFTER FRONTEND CLEANUP")
    print("=" * 60)
    print(f"🕐 Test Started: {datetime.now().isoformat()}")
    print(f"🔧 Backend URL: {BACKEND_URL}")
    print()
    
    # Test core API endpoints mentioned in review request
    tests = [
        ("GET", "/", None, 200),
        ("GET", "/health", None, 200),
        ("GET", "/clients", None, 200),
        ("GET", "/payments/stats", None, 200),
        ("GET", "/membership-types", None, 200),
        ("GET", "/email/templates", None, 200),
        ("GET", "/reminders/stats", None, 200),
    ]
    
    passed = 0
    total = len(tests)
    
    print("🧪 Testing Core API Endpoints:")
    print("-" * 40)
    
    for method, endpoint, data, expected_status in tests:
        success, message = test_endpoint(method, endpoint, data, expected_status)
        print(f"   {message}")
        if success:
            passed += 1
    
    print()
    print("📊 RESULTS:")
    print("-" * 40)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    # Test database connection stability
    print()
    print("🗄️ Database Connection Test:")
    print("-" * 40)
    
    # Get clients to test database read
    success, message = test_endpoint("GET", "/clients")
    if success:
        print("   ✅ Database read operations working")
        
        # Test database write by creating a test client
        test_client = {
            "name": f"Stability Test {datetime.now().strftime('%H%M%S')}",
            "email": f"stability.test.{datetime.now().strftime('%H%M%S')}@example.com",
            "phone": "+1868-555-STABLE",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        success, message = test_endpoint("POST", "/clients", test_client, 200)
        if success:
            print("   ✅ Database write operations working")
        else:
            print(f"   ❌ Database write test failed: {message}")
    else:
        print(f"   ❌ Database read test failed: {message}")
    
    print()
    print("🏁 Backend Stability Test Complete")
    print(f"🕐 Test Ended: {datetime.now().isoformat()}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Backend is stable after frontend cleanup!")
        return True
    else:
        print(f"\n🚨 {total - passed} TESTS FAILED - Backend may have issues!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)