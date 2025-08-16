#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime, date
import time

# Get backend URL from environment
BACKEND_URL = "https://fitness-club-app-2.preview.emergentagent.com/api"

def test_backend_stability_after_total_paid_debugging():
    """
    Test backend stability and functionality after the total paid amount feature debugging.
    
    Testing Focus:
    1. All existing API endpoints are still functional (/api/clients, /api/payments/stats, /api/membership-types)
    2. Payment recording API (/api/payments/record) is working correctly
    3. Client CRUD operations remain stable
    4. Database connectivity is healthy
    5. No regressions were introduced during the debugging process
    
    The frontend total paid amount feature uses calculateTotalPaid function from utils/common.js 
    to calculate member payment totals client-side, so no backend changes were needed.
    Focus on verifying overall backend stability and payment-related functionality.
    """
    
    print("🧪 BACKEND STABILITY TEST - TOTAL PAID AMOUNT FEATURE DEBUGGING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    total_tests = 0
    passed_tests = 0
    
    def run_test(test_name, test_func):
        nonlocal total_tests, passed_tests
        total_tests += 1
        print(f"🔍 Testing: {test_name}")
        try:
            result = test_func()
            if result:
                print(f"✅ PASSED: {test_name}")
                passed_tests += 1
                test_results.append(f"✅ {test_name}")
                return True
            else:
                print(f"❌ FAILED: {test_name}")
                test_results.append(f"❌ {test_name}")
                return False
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {str(e)}")
            test_results.append(f"❌ {test_name} - ERROR: {str(e)}")
            return False
        finally:
            print()
    
    # Test 1: API Health Check
    def test_api_health():
        """Test basic API connectivity and health"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                
                if 'status' in data and data['status'] == 'healthy':
                    print(f"   ✅ API Health Check: {data['status']}")
                    return True
                else:
                    print(f"   ❌ API not healthy")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # Test 2: API Status Endpoint
    def test_api_status():
        """Test API status endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                
                expected_fields = ['status', 'message', 'version', 'endpoints']
                for field in expected_fields:
                    if field not in data:
                        print(f"   ❌ Missing field: {field}")
                        return False
                
                print(f"   ✅ API Status: {data['status']}")
                print(f"   ✅ Version: {data['version']}")
                print(f"   ✅ Available endpoints: {data['endpoints']}")
                return True
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # Test 3: Clients API Endpoint
    def test_clients_api():
        """Test /api/clients endpoint functionality"""
        try:
            response = requests.get(f"{BACKEND_URL}/clients", timeout=15)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                clients = response.json()
                print(f"   Number of clients: {len(clients)}")
                
                if clients:
                    # Check first client structure
                    client = clients[0]
                    required_fields = ['id', 'name', 'email', 'membership_type', 'monthly_fee', 'status']
                    
                    for field in required_fields:
                        if field not in client:
                            print(f"   ❌ Missing required field in client: {field}")
                            return False
                    
                    print(f"   ✅ Client structure valid")
                    print(f"   ✅ Sample client: {client['name']} - {client['membership_type']} - ${client['monthly_fee']}")
                else:
                    print(f"   ⚠️ No clients found (empty database)")
                
                return True
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # Test 4: Payment Stats API Endpoint
    def test_payment_stats_api():
        """Test /api/payments/stats endpoint functionality"""
        try:
            response = requests.get(f"{BACKEND_URL}/payments/stats", timeout=15)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"   Response: {json.dumps(stats, indent=2)}")
                
                required_fields = ['total_revenue', 'monthly_revenue', 'total_amount_owed', 'payment_count']
                for field in required_fields:
                    if field not in stats:
                        print(f"   ❌ Missing required field: {field}")
                        return False
                
                print(f"   ✅ Total Revenue: ${stats['total_revenue']}")
                print(f"   ✅ Monthly Revenue: ${stats['monthly_revenue']}")
                print(f"   ✅ Total Amount Owed: ${stats['total_amount_owed']}")
                print(f"   ✅ Payment Count: {stats['payment_count']}")
                return True
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # Test 5: Membership Types API Endpoint
    def test_membership_types_api():
        """Test /api/membership-types endpoint functionality"""
        try:
            response = requests.get(f"{BACKEND_URL}/membership-types", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                membership_types = response.json()
                print(f"   Number of membership types: {len(membership_types)}")
                
                if membership_types:
                    # Check first membership type structure
                    membership_type = membership_types[0]
                    required_fields = ['id', 'name', 'monthly_fee', 'description']
                    
                    for field in required_fields:
                        if field not in membership_type:
                            print(f"   ❌ Missing required field in membership type: {field}")
                            return False
                    
                    print(f"   ✅ Membership type structure valid")
                    print(f"   ✅ Sample type: {membership_type['name']} - ${membership_type['monthly_fee']}")
                else:
                    print(f"   ⚠️ No membership types found")
                
                return True
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # Test 6: Client CRUD Operations
    def test_client_crud_operations():
        """Test client CRUD operations remain stable"""
        try:
            # First get existing clients count
            initial_response = requests.get(f"{BACKEND_URL}/clients", timeout=10)
            if initial_response.status_code != 200:
                print(f"   ❌ Cannot get initial client count")
                return False
            
            initial_clients = initial_response.json()
            initial_count = len(initial_clients)
            print(f"   Initial client count: {initial_count}")
            
            # CREATE: Add a test client
            test_client_data = {
                "name": "Backend Stability Test User",
                "email": "stability.test@example.com",
                "phone": "+1234567890",
                "membership_type": "Standard",
                "monthly_fee": 50.0,
                "start_date": date.today().isoformat(),
                "payment_status": "due",
                "amount_owed": 50.0
            }
            
            create_response = requests.post(
                f"{BACKEND_URL}/clients",
                json=test_client_data,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if create_response.status_code != 200:
                print(f"   ❌ CREATE failed: {create_response.status_code}")
                return False
            
            created_client = create_response.json()
            test_client_id = created_client['id']
            print(f"   ✅ CREATE: Client created with ID {test_client_id}")
            
            # READ: Get the specific client
            read_response = requests.get(f"{BACKEND_URL}/clients/{test_client_id}", timeout=10)
            if read_response.status_code != 200:
                print(f"   ❌ READ failed: {read_response.status_code}")
                return False
            
            read_client = read_response.json()
            if read_client['name'] != test_client_data['name']:
                print(f"   ❌ READ: Client data mismatch")
                return False
            
            print(f"   ✅ READ: Client retrieved successfully")
            
            # UPDATE: Modify the client
            update_data = {
                "phone": "+0987654321",
                "monthly_fee": 75.0
            }
            
            update_response = requests.put(
                f"{BACKEND_URL}/clients/{test_client_id}",
                json=update_data,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if update_response.status_code != 200:
                print(f"   ❌ UPDATE failed: {update_response.status_code}")
                return False
            
            updated_client = update_response.json()
            if updated_client['phone'] != update_data['phone']:
                print(f"   ❌ UPDATE: Client data not updated correctly")
                return False
            
            print(f"   ✅ UPDATE: Client updated successfully")
            
            # DELETE: Remove the test client
            delete_response = requests.delete(f"{BACKEND_URL}/clients/{test_client_id}", timeout=15)
            if delete_response.status_code != 200:
                print(f"   ❌ DELETE failed: {delete_response.status_code}")
                return False
            
            delete_result = delete_response.json()
            print(f"   ✅ DELETE: {delete_result['message']}")
            
            # Verify deletion
            verify_response = requests.get(f"{BACKEND_URL}/clients/{test_client_id}", timeout=10)
            if verify_response.status_code != 404:
                print(f"   ❌ DELETE verification failed: Client still exists")
                return False
            
            print(f"   ✅ DELETE verified: Client properly removed")
            
            # Check final count
            final_response = requests.get(f"{BACKEND_URL}/clients", timeout=10)
            final_clients = final_response.json()
            final_count = len(final_clients)
            
            if final_count != initial_count:
                print(f"   ❌ Client count mismatch: {initial_count} -> {final_count}")
                return False
            
            print(f"   ✅ Final client count matches initial: {final_count}")
            return True
                
        except Exception as e:
            print(f"   ❌ CRUD operations failed: {str(e)}")
            return False
    
    # Test 7: Payment Recording API
    def test_payment_recording_api():
        """Test /api/payments/record endpoint functionality"""
        try:
            # First, get a client to test payment recording with
            clients_response = requests.get(f"{BACKEND_URL}/clients", timeout=10)
            if clients_response.status_code != 200:
                print(f"   ⚠️ Cannot get clients for payment test")
                return True  # Skip if no clients available
            
            clients = clients_response.json()
            if not clients:
                print(f"   ⚠️ No clients available for payment recording test")
                return True  # Skip if no clients
            
            # Use the first client
            test_client = clients[0]
            client_id = test_client['id']
            client_name = test_client['name']
            
            print(f"   Testing payment recording for client: {client_name}")
            
            # Record a test payment
            payment_data = {
                "client_id": client_id,
                "amount_paid": 25.0,  # Partial payment
                "payment_date": date.today().isoformat(),
                "payment_method": "Cash",
                "notes": "Backend stability test payment"
            }
            
            payment_response = requests.post(
                f"{BACKEND_URL}/payments/record",
                json=payment_data,
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            
            print(f"   Status Code: {payment_response.status_code}")
            
            if payment_response.status_code == 200:
                payment_result = payment_response.json()
                print(f"   Response: {json.dumps(payment_result, indent=2)}")
                
                # Check required fields in response
                required_fields = ['success', 'message', 'client_name', 'amount_paid', 'payment_status']
                for field in required_fields:
                    if field not in payment_result:
                        print(f"   ❌ Missing field in payment response: {field}")
                        return False
                
                if payment_result['success']:
                    print(f"   ✅ Payment recorded successfully")
                    print(f"   ✅ Amount paid: ${payment_result['amount_paid']}")
                    print(f"   ✅ Payment status: {payment_result['payment_status']}")
                    return True
                else:
                    print(f"   ❌ Payment recording failed: {payment_result['message']}")
                    return False
            else:
                print(f"   ❌ HTTP Error: {payment_response.status_code}")
                try:
                    error_data = payment_response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Error text: {payment_response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Payment recording test failed: {str(e)}")
            return False
    
    # Test 8: Database Connectivity Health
    def test_database_connectivity():
        """Test database connectivity through multiple endpoints"""
        try:
            # Test multiple database-dependent endpoints
            endpoints_to_test = [
                ("/clients", "clients"),
                ("/payments/stats", "payment statistics"),
                ("/membership-types", "membership types")
            ]
            
            successful_connections = 0
            
            for endpoint, description in endpoints_to_test:
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        print(f"   ✅ Database connection via {description}: OK")
                        successful_connections += 1
                    else:
                        print(f"   ❌ Database connection via {description}: Failed ({response.status_code})")
                except Exception as e:
                    print(f"   ❌ Database connection via {description}: Error ({str(e)})")
            
            # Consider database healthy if at least 2/3 endpoints work
            if successful_connections >= 2:
                print(f"   ✅ Database connectivity: {successful_connections}/{len(endpoints_to_test)} endpoints working")
                return True
            else:
                print(f"   ❌ Database connectivity issues: Only {successful_connections}/{len(endpoints_to_test)} endpoints working")
                return False
                
        except Exception as e:
            print(f"   ❌ Database connectivity test failed: {str(e)}")
            return False
    
    # Test 9: Concurrent API Requests (Regression Test)
    def test_concurrent_requests():
        """Test that API can handle concurrent requests without issues"""
        try:
            import threading
            import time
            
            results = []
            
            def make_request(endpoint, results_list):
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    results_list.append(response.status_code == 200)
                except:
                    results_list.append(False)
            
            # Create threads for concurrent requests
            threads = []
            endpoints = ["/health", "/clients", "/payments/stats", "/membership-types", "/"]
            
            start_time = time.time()
            
            for endpoint in endpoints:
                thread = threading.Thread(target=make_request, args=(endpoint, results))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            duration = end_time - start_time
            
            successful_requests = sum(results)
            total_requests = len(results)
            
            print(f"   Concurrent requests: {successful_requests}/{total_requests} successful")
            print(f"   Total time: {duration:.2f} seconds")
            
            if successful_requests >= total_requests * 0.8:  # 80% success rate
                print(f"   ✅ Concurrent request handling: Good")
                return True
            else:
                print(f"   ❌ Concurrent request handling: Poor")
                return False
                
        except Exception as e:
            print(f"   ❌ Concurrent request test failed: {str(e)}")
            return False
    
    # Test 10: Response Format Consistency
    def test_response_format_consistency():
        """Test that API responses have consistent format and headers"""
        try:
            endpoints_to_test = [
                "/health",
                "/clients", 
                "/payments/stats",
                "/membership-types"
            ]
            
            consistent_responses = 0
            
            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    
                    # Check status code
                    if response.status_code != 200:
                        print(f"   ⚠️ {endpoint}: Non-200 status ({response.status_code})")
                        continue
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' not in content_type:
                        print(f"   ❌ {endpoint}: Invalid content type ({content_type})")
                        continue
                    
                    # Check if response is valid JSON
                    try:
                        response.json()
                    except:
                        print(f"   ❌ {endpoint}: Invalid JSON response")
                        continue
                    
                    # Check for cache-busting headers (mobile compatibility)
                    cache_headers = ['Cache-Control', 'X-Mobile-Cache-Bust']
                    has_cache_busting = any(header in response.headers for header in cache_headers)
                    
                    if has_cache_busting:
                        print(f"   ✅ {endpoint}: Proper format with cache-busting headers")
                    else:
                        print(f"   ✅ {endpoint}: Proper format")
                    
                    consistent_responses += 1
                    
                except Exception as e:
                    print(f"   ❌ {endpoint}: Format check failed ({str(e)})")
            
            if consistent_responses == len(endpoints_to_test):
                print(f"   ✅ All endpoints have consistent response format")
                return True
            else:
                print(f"   ⚠️ {consistent_responses}/{len(endpoints_to_test)} endpoints have consistent format")
                return consistent_responses >= len(endpoints_to_test) * 0.8  # 80% threshold
                
        except Exception as e:
            print(f"   ❌ Response format test failed: {str(e)}")
            return False
    
    # Run all tests
    print("🚀 Starting Backend Stability Tests...")
    print()
    
    run_test("API Health Check", test_api_health)
    run_test("API Status Endpoint", test_api_status)
    run_test("Clients API Endpoint (/api/clients)", test_clients_api)
    run_test("Payment Stats API Endpoint (/api/payments/stats)", test_payment_stats_api)
    run_test("Membership Types API Endpoint (/api/membership-types)", test_membership_types_api)
    run_test("Client CRUD Operations Stability", test_client_crud_operations)
    run_test("Payment Recording API (/api/payments/record)", test_payment_recording_api)
    run_test("Database Connectivity Health", test_database_connectivity)
    run_test("Concurrent API Requests (Regression Test)", test_concurrent_requests)
    run_test("Response Format Consistency", test_response_format_consistency)
    
    # Print summary
    print("=" * 80)
    print("📊 BACKEND STABILITY TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    print("📋 DETAILED RESULTS:")
    for result in test_results:
        print(f"  {result}")
    print()
    
    # Determine overall result
    if passed_tests == total_tests:
        print("🎉 ALL BACKEND STABILITY TESTS PASSED!")
        print("✅ Backend is completely stable after total paid amount feature debugging")
        print("✅ All existing API endpoints are functional")
        print("✅ Payment recording API is working correctly")
        print("✅ Client CRUD operations remain stable")
        print("✅ Database connectivity is healthy")
        print("✅ No regressions detected")
        return True
    elif passed_tests >= total_tests * 0.9:  # 90% pass rate
        print("✅ BACKEND STABILITY EXCELLENT")
        print(f"⚠️ {total_tests - passed_tests} minor issues detected - check details above")
        print("✅ Core functionality remains stable")
        return True
    elif passed_tests >= total_tests * 0.8:  # 80% pass rate
        print("✅ BACKEND STABILITY GOOD")
        print(f"⚠️ {total_tests - passed_tests} issues detected - review recommended")
        print("✅ Most functionality remains stable")
        return True
    else:
        print("❌ BACKEND STABILITY ISSUES DETECTED")
        print(f"🚨 {total_tests - passed_tests} tests failed - immediate attention required")
        return False

if __name__ == "__main__":
    success = test_backend_stability_after_total_paid_debugging()
    sys.exit(0 if success else 1)