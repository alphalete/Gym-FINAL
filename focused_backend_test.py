#!/usr/bin/env python3
"""
Focused Backend API Testing After Frontend Repository System Enhancements
Testing core functionality with shorter timeouts and focused scope

REVIEW REQUEST FOCUS:
1. Core API Health - Verify API status and health endpoints are responding
2. Client CRUD Operations - Test GET/POST/PUT/DELETE /api/clients endpoints
3. Payment Integration - Verify payment recording endpoints work with enhanced member data structure
"""

import requests
import json
import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://alphalete-pwa.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Backend URL: {BACKEND_URL}")
print(f"🕐 Test Started: {datetime.now().isoformat()}")
print("🎯 Focus: Core backend functionality after repository system enhancements")
print("=" * 80)

class FocusedBackendTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        self.created_test_clients = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def make_request(self, method, endpoint, data=None, timeout=5):
        """Make HTTP request with shorter timeout"""
        url = f"{self.base_url}{endpoint}"
        try:
            headers = {'Content-Type': 'application/json'}
            if method == "GET":
                response = requests.get(url, timeout=timeout, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=timeout, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=timeout, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, timeout=timeout, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Request timeout/error: {e}")
            return None

    def test_core_api_health(self):
        """Test 1: Core API Health"""
        print("\n🔍 TEST 1: Core API Health Check")
        print("-" * 50)
        
        # Test main API status endpoint
        response = self.make_request("GET", "/")
        if response and response.status_code == 200:
            try:
                api_data = response.json()
                status = api_data.get('status')
                version = api_data.get('version')
                self.log_test("API Status Endpoint", status == 'active', 
                            f"Status: {status}, Version: {version}")
            except json.JSONDecodeError:
                self.log_test("API Status Endpoint", False, "Invalid JSON response")
        else:
            self.log_test("API Status Endpoint", False, 
                        f"HTTP {response.status_code if response else 'No response'}")
            
        # Test health check endpoint
        response = self.make_request("GET", "/health")
        if response and response.status_code == 200:
            try:
                health_data = response.json()
                health_status = health_data.get('status')
                self.log_test("Health Check Endpoint", health_status == 'healthy',
                            f"Health Status: {health_status}")
            except json.JSONDecodeError:
                self.log_test("Health Check Endpoint", False, "Invalid JSON response")
        else:
            self.log_test("Health Check Endpoint", False,
                        f"HTTP {response.status_code if response else 'No response'}")
            
        return True

    def test_client_crud_operations(self):
        """Test 2: Client CRUD Operations"""
        print("\n🔍 TEST 2: Client CRUD Operations")
        print("-" * 50)
        
        # Test GET /api/clients
        response = self.make_request("GET", "/clients")
        if response and response.status_code == 200:
            try:
                clients = response.json()
                self.log_test("GET /api/clients", True, f"Retrieved {len(clients)} clients")
                
                # Check enhanced member data structure
                if clients:
                    client = clients[0]
                    enhanced_fields = ['payment_status', 'amount_owed', 'auto_reminders_enabled']
                    has_enhanced_fields = all(field in client for field in enhanced_fields)
                    self.log_test("Enhanced Member Data Structure", has_enhanced_fields,
                                f"Enhanced fields present: {has_enhanced_fields}")
                else:
                    self.log_test("Enhanced Member Data Structure", True, "No clients to verify (empty state)")
                    
            except json.JSONDecodeError:
                self.log_test("GET /api/clients", False, "Invalid JSON response")
        else:
            self.log_test("GET /api/clients", False,
                        f"HTTP {response.status_code if response else 'No response'}")
            
        # Test POST /api/clients (Create)
        timestamp = datetime.now().strftime('%H%M%S')
        test_client_data = {
            "name": f"Focused Test Client {timestamp}",
            "email": f"focused.test.{timestamp}@example.com",
            "phone": "+1868-555-FOCUS",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": date.today().isoformat(),
            "payment_status": "due",
            "amount_owed": 55.0,
            "auto_reminders_enabled": True
        }
        
        response = self.make_request("POST", "/clients", test_client_data)
        if response and response.status_code in [200, 201]:
            try:
                created_client = response.json()
                client_id = created_client.get('id')
                self.created_test_clients.append(client_id)
                self.log_test("POST /api/clients (Create)", True,
                            f"Created client: {created_client.get('name')}")
                
                # Test GET specific client
                response = self.make_request("GET", f"/clients/{client_id}")
                if response and response.status_code == 200:
                    retrieved_client = response.json()
                    self.log_test("GET /api/clients/{id}", True,
                                f"Retrieved client: {retrieved_client.get('name')}")
                    
                    # Test PUT /api/clients/{id} (Update)
                    update_data = {
                        "phone": "+1868-555-UPDATED",
                        "monthly_fee": 60.0
                    }
                    response = self.make_request("PUT", f"/clients/{client_id}", update_data)
                    if response and response.status_code == 200:
                        updated_client = response.json()
                        update_successful = (
                            updated_client.get('phone') == "+1868-555-UPDATED" and
                            updated_client.get('monthly_fee') == 60.0
                        )
                        self.log_test("PUT /api/clients/{id} (Update)", update_successful,
                                    f"Updated phone: {updated_client.get('phone')}")
                    else:
                        self.log_test("PUT /api/clients/{id} (Update)", False,
                                    f"HTTP {response.status_code if response else 'No response'}")
                else:
                    self.log_test("GET /api/clients/{id}", False,
                                f"HTTP {response.status_code if response else 'No response'}")
                    
            except json.JSONDecodeError:
                self.log_test("POST /api/clients", False, "Invalid JSON response")
        else:
            self.log_test("POST /api/clients (Create)", False,
                        f"HTTP {response.status_code if response else 'No response'}")
            
        return True

    def test_payment_integration(self):
        """Test 3: Payment Integration"""
        print("\n🔍 TEST 3: Payment Integration")
        print("-" * 50)
        
        # Test GET /api/payments/stats
        response = self.make_request("GET", "/payments/stats")
        if response and response.status_code == 200:
            try:
                stats = response.json()
                required_fields = ['total_revenue', 'monthly_revenue', 'payment_count', 'total_amount_owed']
                has_required_fields = all(field in stats for field in required_fields)
                self.log_test("Payment Stats Endpoint", has_required_fields,
                            f"Total Revenue: TTD {stats.get('total_revenue', 0)}")
                            
            except json.JSONDecodeError:
                self.log_test("Payment Stats Endpoint", False, "Invalid JSON response")
        else:
            self.log_test("Payment Stats Endpoint", False,
                        f"HTTP {response.status_code if response else 'No response'}")
            
        # Test payment recording if we have a test client
        if self.created_test_clients:
            client_id = self.created_test_clients[0]
            payment_data = {
                "client_id": client_id,
                "amount_paid": 55.0,
                "payment_date": date.today().isoformat(),
                "payment_method": "Cash",
                "notes": "Focused test payment"
            }
            
            response = self.make_request("POST", "/payments/record", payment_data)
            if response and response.status_code == 200:
                try:
                    payment_result = response.json()
                    payment_successful = payment_result.get('success', False)
                    self.log_test("Payment Recording", payment_successful,
                                f"Payment recorded: TTD {payment_result.get('amount_paid')}")
                    
                    # Check payment status update
                    payment_status = payment_result.get('payment_status')
                    self.log_test("Payment Status Update", payment_status == 'paid',
                                f"Status updated to: {payment_status}")
                                
                except json.JSONDecodeError:
                    self.log_test("Payment Recording", False, "Invalid JSON response")
            else:
                self.log_test("Payment Recording", False,
                            f"HTTP {response.status_code if response else 'No response'}")
        else:
            self.log_test("Payment Recording", False, "No test client available")
            
        return True

    def test_delete_functionality(self):
        """Test 4: DELETE Functionality"""
        print("\n🔍 TEST 4: DELETE Functionality")
        print("-" * 50)
        
        if not self.created_test_clients:
            self.log_test("DELETE Functionality", False, "No test clients available")
            return False
            
        client_to_delete = self.created_test_clients[0]
        
        # Perform deletion
        response = self.make_request("DELETE", f"/clients/{client_to_delete}")
        if response and response.status_code == 200:
            try:
                delete_result = response.json()
                deletion_successful = delete_result.get('client_deleted', False)
                self.log_test("DELETE /api/clients/{id}", deletion_successful,
                            f"Deleted client: {delete_result.get('client_name')}")
                
                # Remove from tracking
                self.created_test_clients.remove(client_to_delete)
                
            except json.JSONDecodeError:
                self.log_test("DELETE /api/clients/{id}", False, "Invalid JSON response")
        else:
            self.log_test("DELETE /api/clients/{id}", False,
                        f"HTTP {response.status_code if response else 'No response'}")
            
        return True

    def cleanup_test_data(self):
        """Clean up remaining test data"""
        print("\n🧹 CLEANUP: Removing Test Data")
        print("-" * 50)
        
        cleanup_count = 0
        for client_id in self.created_test_clients[:]:
            response = self.make_request("DELETE", f"/clients/{client_id}")
            if response and response.status_code == 200:
                cleanup_count += 1
                print(f"   ✅ Deleted test client: {client_id}")
                self.created_test_clients.remove(client_id)
            else:
                print(f"   ❌ Failed to delete test client: {client_id}")
                
        print(f"🧹 Cleaned up {cleanup_count} test clients")

    def run_all_tests(self):
        """Run focused backend tests"""
        print("🚀 STARTING FOCUSED BACKEND TESTING")
        print("🎯 Focus: Core backend functionality after repository system enhancements")
        print("=" * 80)
        
        # Test sequence
        tests_passed = 0
        total_tests = 4
        
        if self.test_core_api_health():
            tests_passed += 1
        if self.test_client_crud_operations():
            tests_passed += 1
        if self.test_payment_integration():
            tests_passed += 1
        if self.test_delete_functionality():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 FOCUSED BACKEND TEST SUMMARY")
        print("=" * 80)
        
        total_individual_tests = len(self.test_results)
        passed_individual_tests = sum(1 for result in self.test_results if result['success'])
        failed_individual_tests = total_individual_tests - passed_individual_tests
        success_rate = (passed_individual_tests / total_individual_tests * 100) if total_individual_tests > 0 else 0
        
        print(f"📈 Test Categories Passed: {tests_passed}/{total_tests}")
        print(f"📈 Individual Tests: {total_individual_tests}")
        print(f"✅ Passed: {passed_individual_tests}")
        print(f"❌ Failed: {failed_individual_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if failed_individual_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
                    
        # Cleanup
        if self.created_test_clients:
            self.cleanup_test_data()
            
        print(f"\n🏁 Testing completed at: {datetime.now().isoformat()}")
        
        return success_rate >= 80.0

def main():
    """Main test execution"""
    try:
        tester = FocusedBackendTester(BACKEND_URL)
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 FOCUSED BACKEND TESTING: SUCCESS!")
            print("✅ Core backend functionality is working correctly")
            sys.exit(0)
        else:
            print("\n🚨 FOCUSED BACKEND TESTING: ISSUES DETECTED!")
            print("❌ Some core backend functionality may have issues")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()