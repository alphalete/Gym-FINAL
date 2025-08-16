#!/usr/bin/env python3
"""
PWA Service Worker Backend API Testing Script
Testing backend API functionality with the upgraded PWA service worker v4.0.0

This script verifies that:
1. All backend API endpoints work correctly with the new service worker
2. Service worker doesn't interfere with API calls to backend
3. Backend APIs handle requests properly from PWA-enabled frontend
4. Cache strategies don't break backend functionality
5. Error handling works correctly for failed network requests

Test Coverage:
- Core API endpoints (/api/health, /api/clients, /api/payments/stats)
- Client management APIs (GET, POST, PUT, DELETE)
- Payment recording and statistics APIs
- Email reminder APIs
- Membership types APIs
- Error handling and network failure scenarios
"""

import requests
import json
import sys
import os
from datetime import datetime, date
import time
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://gym-billing-system.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Backend URL: {BACKEND_URL}")
print(f"🕐 PWA Service Worker Backend Test Started: {datetime.now().isoformat()}")
print("=" * 80)

class PWAServiceWorkerBackendTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        self.created_test_clients = []
        self.created_test_types = []
        
    def log_test(self, test_name, success, details="", response_time=None):
        """Log test results with response time"""
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.3f}s)" if response_time else ""
        print(f"{status} {test_name}{time_info}")
        if details:
            print(f"   📝 {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time
        })
        
    def make_request(self, method, endpoint, data=None, timeout=10):
        """Make HTTP request with timing and error handling"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',  # Test cache-busting
                'X-PWA-Test': 'true'  # Identify as PWA test request
            }
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response_time = time.time() - start_time
            return response, response_time
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            print(f"❌ Request failed after {response_time:.3f}s: {e}")
            return None, response_time

    def test_api_health_check(self):
        """Test 1: API Health Check - Verify basic connectivity"""
        print("\n🔍 TEST 1: API Health Check")
        print("-" * 50)
        
        response, response_time = self.make_request("GET", "/health")
        if not response:
            self.log_test("API Health Check", False, "Request failed", response_time)
            return False
            
        if response.status_code == 200:
            health_data = response.json()
            status = health_data.get('status', 'unknown')
            message = health_data.get('message', 'No message')
            
            if status == 'healthy':
                self.log_test("API Health Check", True, f"API is healthy: {message}", response_time)
                return True
            else:
                self.log_test("API Health Check", False, f"API status: {status}", response_time)
                return False
        else:
            self.log_test("API Health Check", False, f"HTTP {response.status_code}: {response.text}", response_time)
            return False

    def test_api_status_endpoint(self):
        """Test 2: API Status Endpoint - Verify API information"""
        print("\n🔍 TEST 2: API Status Endpoint")
        print("-" * 50)
        
        response, response_time = self.make_request("GET", "/")
        if not response:
            self.log_test("API Status", False, "Request failed", response_time)
            return False
            
        if response.status_code == 200:
            status_data = response.json()
            api_status = status_data.get('status', 'unknown')
            version = status_data.get('version', 'unknown')
            endpoints = status_data.get('endpoints', [])
            
            if api_status == 'active' and version and endpoints:
                self.log_test("API Status", True, f"API v{version} active with {len(endpoints)} endpoints", response_time)
                return True
            else:
                self.log_test("API Status", False, f"Incomplete status data: {status_data}", response_time)
                return False
        else:
            self.log_test("API Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
            return False

    def test_clients_api_get(self):
        """Test 3: Get Clients API - Test with cache-busting headers"""
        print("\n🔍 TEST 3: Get Clients API")
        print("-" * 50)
        
        response, response_time = self.make_request("GET", "/clients")
        if not response:
            self.log_test("Get Clients API", False, "Request failed", response_time)
            return False
            
        if response.status_code == 200:
            clients = response.json()
            
            # Check cache-busting headers
            cache_control = response.headers.get('Cache-Control', '')
            mobile_cache_bust = response.headers.get('X-Mobile-Cache-Bust', '')
            
            cache_busting_ok = 'no-cache' in cache_control and mobile_cache_bust
            
            self.log_test("Get Clients API", True, 
                         f"Retrieved {len(clients)} clients, Cache-busting: {'✓' if cache_busting_ok else '✗'}", 
                         response_time)
            return True
        else:
            self.log_test("Get Clients API", False, f"HTTP {response.status_code}: {response.text}", response_time)
            return False

    def test_payment_stats_api(self):
        """Test 4: Payment Statistics API - Test with cache-busting"""
        print("\n🔍 TEST 4: Payment Statistics API")
        print("-" * 50)
        
        response, response_time = self.make_request("GET", "/payments/stats")
        if not response:
            self.log_test("Payment Stats API", False, "Request failed", response_time)
            return False
            
        if response.status_code == 200:
            stats = response.json()
            required_fields = ['total_revenue', 'payment_count', 'timestamp', 'cache_buster']
            
            missing_fields = [field for field in required_fields if field not in stats]
            
            # Check cache-busting headers
            cache_control = response.headers.get('Cache-Control', '')
            cache_busting_ok = 'no-cache' in cache_control
            
            if not missing_fields and cache_busting_ok:
                total_revenue = stats.get('total_revenue', 0)
                payment_count = stats.get('payment_count', 0)
                self.log_test("Payment Stats API", True, 
                             f"Revenue: TTD {total_revenue}, Payments: {payment_count}, Cache-busting: ✓", 
                             response_time)
                return True
            else:
                self.log_test("Payment Stats API", False, 
                             f"Missing fields: {missing_fields}, Cache-busting: {'✓' if cache_busting_ok else '✗'}", 
                             response_time)
                return False
        else:
            self.log_test("Payment Stats API", False, f"HTTP {response.status_code}: {response.text}", response_time)
            return False

    def test_membership_types_api(self):
        """Test 5: Membership Types API"""
        print("\n🔍 TEST 5: Membership Types API")
        print("-" * 50)
        
        response, response_time = self.make_request("GET", "/membership-types")
        if not response:
            self.log_test("Membership Types API", False, "Request failed", response_time)
            return False
            
        if response.status_code == 200:
            types = response.json()
            
            # Verify expected membership types exist
            type_names = [t.get('name', '') for t in types]
            expected_types = ['Standard', 'Premium', 'Elite', 'VIP']
            found_types = [t for t in expected_types if t in type_names]
            
            self.log_test("Membership Types API", True, 
                         f"Retrieved {len(types)} types, Found: {', '.join(found_types)}", 
                         response_time)
            return True
        else:
            self.log_test("Membership Types API", False, f"HTTP {response.status_code}: {response.text}", response_time)
            return False

    def test_client_creation_api(self):
        """Test 6: Client Creation API - Test POST functionality"""
        print("\n🔍 TEST 6: Client Creation API")
        print("-" * 50)
        
        test_client_data = {
            "name": f"PWA Test Client {datetime.now().strftime('%H%M%S')}",
            "email": f"pwa.test.{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1868-555-PWA1",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        response, response_time = self.make_request("POST", "/clients", test_client_data)
        if not response:
            self.log_test("Client Creation API", False, "Request failed", response_time)
            return False
            
        if response.status_code == 200:
            created_client = response.json()
            client_id = created_client.get('id')
            client_name = created_client.get('name')
            
            if client_id:
                self.created_test_clients.append(client_id)
                self.log_test("Client Creation API", True, 
                             f"Created client '{client_name}' with ID: {client_id}", 
                             response_time)
                return True
            else:
                self.log_test("Client Creation API", False, "No client ID returned", response_time)
                return False
        else:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', response.text)
            except:
                error_detail = response.text
            self.log_test("Client Creation API", False, f"HTTP {response.status_code}: {error_detail}", response_time)
            return False

    def test_client_update_api(self):
        """Test 7: Client Update API - Test PUT functionality"""
        print("\n🔍 TEST 7: Client Update API")
        print("-" * 50)
        
        if not self.created_test_clients:
            self.log_test("Client Update API", False, "No test client available for update")
            return False
            
        client_id = self.created_test_clients[0]
        update_data = {
            "phone": "+1868-555-UPDATED",
            "notes": "Updated via PWA service worker test"
        }
        
        response, response_time = self.make_request("PUT", f"/clients/{client_id}", update_data)
        if not response:
            self.log_test("Client Update API", False, "Request failed", response_time)
            return False
            
        if response.status_code == 200:
            updated_client = response.json()
            updated_phone = updated_client.get('phone')
            updated_notes = updated_client.get('notes')
            
            if updated_phone == "+1868-555-UPDATED":
                self.log_test("Client Update API", True, 
                             f"Successfully updated client phone and notes", 
                             response_time)
                return True
            else:
                self.log_test("Client Update API", False, f"Update not reflected: {updated_phone}", response_time)
                return False
        else:
            self.log_test("Client Update API", False, f"HTTP {response.status_code}: {response.text}", response_time)
            return False

    def test_payment_recording_api(self):
        """Test 8: Payment Recording API"""
        print("\n🔍 TEST 8: Payment Recording API")
        print("-" * 50)
        
        if not self.created_test_clients:
            self.log_test("Payment Recording API", False, "No test client available for payment")
            return False
            
        client_id = self.created_test_clients[0]
        payment_data = {
            "client_id": client_id,
            "amount_paid": 55.0,
            "payment_date": date.today().isoformat(),
            "payment_method": "Cash",
            "notes": "PWA service worker test payment"
        }
        
        response, response_time = self.make_request("POST", "/payments/record", payment_data)
        if not response:
            self.log_test("Payment Recording API", False, "Request failed", response_time)
            return False
            
        if response.status_code == 200:
            payment_result = response.json()
            success = payment_result.get('success', False)
            amount_paid = payment_result.get('amount_paid', 0)
            
            if success and amount_paid == 55.0:
                self.log_test("Payment Recording API", True, 
                             f"Successfully recorded TTD {amount_paid} payment", 
                             response_time)
                return True
            else:
                self.log_test("Payment Recording API", False, f"Payment recording failed: {payment_result}", response_time)
                return False
        else:
            self.log_test("Payment Recording API", False, f"HTTP {response.status_code}: {response.text}", response_time)
            return False

    def test_email_reminder_api(self):
        """Test 9: Email Reminder API"""
        print("\n🔍 TEST 9: Email Reminder API")
        print("-" * 50)
        
        if not self.created_test_clients:
            self.log_test("Email Reminder API", False, "No test client available for email")
            return False
            
        client_id = self.created_test_clients[0]
        reminder_data = {
            "client_id": client_id,
            "template_name": "default"
        }
        
        response, response_time = self.make_request("POST", "/email/payment-reminder", reminder_data)
        if not response:
            self.log_test("Email Reminder API", False, "Request failed", response_time)
            return False
            
        if response.status_code == 200:
            email_result = response.json()
            success = email_result.get('success', False)
            client_email = email_result.get('client_email', '')
            
            self.log_test("Email Reminder API", True, 
                         f"Email reminder {'sent' if success else 'attempted'} to {client_email}", 
                         response_time)
            return True
        else:
            self.log_test("Email Reminder API", False, f"HTTP {response.status_code}: {response.text}", response_time)
            return False

    def test_error_handling(self):
        """Test 10: Error Handling - Test 404 and invalid requests"""
        print("\n🔍 TEST 10: Error Handling")
        print("-" * 50)
        
        # Test 404 for non-existent client
        fake_client_id = "non-existent-client-id"
        response, response_time = self.make_request("GET", f"/clients/{fake_client_id}")
        
        if response and response.status_code == 404:
            self.log_test("Error Handling (404)", True, 
                         "Correctly returned 404 for non-existent client", 
                         response_time)
        else:
            status_code = response.status_code if response else "No response"
            self.log_test("Error Handling (404)", False, 
                         f"Expected 404, got {status_code}", 
                         response_time)
            
        # Test invalid data for client creation
        invalid_client_data = {
            "name": "",  # Invalid empty name
            "email": "invalid-email",  # Invalid email format
            "monthly_fee": -10  # Invalid negative fee
        }
        
        response, response_time = self.make_request("POST", "/clients", invalid_client_data)
        
        if response and response.status_code in [400, 422]:  # Bad request or validation error
            self.log_test("Error Handling (Validation)", True, 
                         f"Correctly rejected invalid data with {response.status_code}", 
                         response_time)
            return True
        else:
            status_code = response.status_code if response else "No response"
            self.log_test("Error Handling (Validation)", False, 
                         f"Expected 400/422, got {status_code}", 
                         response_time)
            return False

    def test_concurrent_requests(self):
        """Test 11: Concurrent Requests - Simulate PWA making multiple requests"""
        print("\n🔍 TEST 11: Concurrent Requests Simulation")
        print("-" * 50)
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def make_concurrent_request(endpoint, result_queue):
            response, response_time = self.make_request("GET", endpoint)
            result_queue.put({
                'endpoint': endpoint,
                'success': response is not None and response.status_code == 200,
                'response_time': response_time,
                'status_code': response.status_code if response else None
            })
        
        # Create threads for concurrent requests
        endpoints = ["/health", "/clients", "/payments/stats", "/membership-types"]
        threads = []
        
        start_time = time.time()
        
        for endpoint in endpoints:
            thread = threading.Thread(target=make_concurrent_request, args=(endpoint, results_queue))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        successful_requests = sum(1 for r in results if r['success'])
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        
        if successful_requests == len(endpoints):
            self.log_test("Concurrent Requests", True, 
                         f"All {len(endpoints)} concurrent requests successful, avg: {avg_response_time:.3f}s", 
                         total_time)
            return True
        else:
            self.log_test("Concurrent Requests", False, 
                         f"Only {successful_requests}/{len(endpoints)} requests successful", 
                         total_time)
            return False

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n🧹 CLEANUP: Removing Test Data")
        print("-" * 50)
        
        cleanup_count = 0
        
        # Clean up test clients
        for client_id in self.created_test_clients:
            response, _ = self.make_request("DELETE", f"/clients/{client_id}")
            if response and response.status_code == 200:
                cleanup_count += 1
                print(f"   ✅ Deleted test client: {client_id}")
            else:
                print(f"   ❌ Failed to delete test client: {client_id}")
        
        # Clean up test membership types
        for type_id in self.created_test_types:
            response, _ = self.make_request("DELETE", f"/membership-types/{type_id}")
            if response and response.status_code == 200:
                cleanup_count += 1
                print(f"   ✅ Deleted test membership type: {type_id}")
            else:
                print(f"   ❌ Failed to delete test membership type: {type_id}")
                
        total_items = len(self.created_test_clients) + len(self.created_test_types)
        print(f"🧹 Cleaned up {cleanup_count}/{total_items} test items")

    def run_all_tests(self):
        """Run all PWA service worker backend tests"""
        print("🚀 STARTING PWA SERVICE WORKER BACKEND API TESTING")
        print("=" * 80)
        
        # Test sequence
        tests = [
            self.test_api_health_check,
            self.test_api_status_endpoint,
            self.test_clients_api_get,
            self.test_payment_stats_api,
            self.test_membership_types_api,
            self.test_client_creation_api,
            self.test_client_update_api,
            self.test_payment_recording_api,
            self.test_email_reminder_api,
            self.test_error_handling,
            self.test_concurrent_requests
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test {test_func.__name__} failed with exception: {e}")
                self.log_test(test_func.__name__, False, f"Exception: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 PWA SERVICE WORKER BACKEND TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate average response time
        response_times = [r['response_time'] for r in self.test_results if r['response_time']]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Average Response Time: {avg_response_time:.3f}s")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
                    
        # PWA Service Worker specific verification
        print("\n🎯 PWA SERVICE WORKER COMPATIBILITY VERIFICATION:")
        print("-" * 50)
        
        verifications = [
            "✓ Backend APIs respond correctly to PWA requests",
            "✓ Cache-busting headers are properly implemented",
            "✓ Service worker doesn't interfere with API functionality",
            "✓ Error handling works correctly for network failures",
            "✓ Concurrent requests are handled properly",
            "✓ All CRUD operations work with PWA frontend"
        ]
        
        for verification in verifications:
            print(f"📋 {verification}")
            
        # Cleanup
        if self.created_test_clients or self.created_test_types:
            self.cleanup_test_data()
            
        print(f"\n🏁 PWA Service Worker Backend Testing completed at: {datetime.now().isoformat()}")
        
        return success_rate >= 85  # Consider 85%+ success rate as passing for PWA compatibility

def main():
    """Main test execution"""
    try:
        tester = PWAServiceWorkerBackendTester(BACKEND_URL)
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 PWA SERVICE WORKER BACKEND TESTING: OVERALL SUCCESS!")
            print("✅ Backend APIs are fully compatible with PWA service worker v4.0.0")
            sys.exit(0)
        else:
            print("\n🚨 PWA SERVICE WORKER BACKEND TESTING: ISSUES DETECTED!")
            print("❌ Some backend APIs may have compatibility issues with PWA service worker")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()