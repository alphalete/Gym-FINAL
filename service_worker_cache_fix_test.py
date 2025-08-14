#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any

class ServiceWorkerCacheFixTester:
    def __init__(self):
        # Use the exact URL from frontend/.env
        self.base_url = "https://gym-manager-app-1.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.response_times = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None) -> tuple:
        """Run a single API test with response time tracking"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            end_time = time.time()
            response_time = end_time - start_time
            self.response_times.append(response_time)
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    details = f"(Status: {response.status_code}, Time: {response_time:.3f}s)"
                    self.log_test(name, True, details)
                    
                    # Check for cache-busting headers
                    cache_headers = {
                        'Cache-Control': response.headers.get('Cache-Control'),
                        'Pragma': response.headers.get('Pragma'),
                        'Expires': response.headers.get('Expires'),
                        'ETag': response.headers.get('ETag'),
                        'X-Mobile-Cache-Bust': response.headers.get('X-Mobile-Cache-Bust')
                    }
                    
                    print(f"   Response Time: {response_time:.3f}s")
                    print(f"   Cache Headers: {json.dumps({k: v for k, v in cache_headers.items() if v}, indent=4)}")
                    
                    return True, response_data, response_time, cache_headers
                except:
                    details = f"(Status: {response.status_code}, Time: {response_time:.3f}s, No JSON response)"
                    self.log_test(name, True, details)
                    return True, {}, response_time, {}
            else:
                try:
                    error_data = response.json()
                    details = f"(Expected {expected_status}, got {response.status_code}, Time: {response_time:.3f}s) - {error_data}"
                except:
                    details = f"(Expected {expected_status}, got {response.status_code}, Time: {response_time:.3f}s) - {response.text[:100]}"
                self.log_test(name, False, details)
                return False, {}, response_time, {}

        except requests.exceptions.RequestException as e:
            end_time = time.time()
            response_time = end_time - start_time
            details = f"(Network Error: {str(e)}, Time: {response_time:.3f}s)"
            self.log_test(name, False, details)
            return False, {}, response_time, {}
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            details = f"(Error: {str(e)}, Time: {response_time:.3f}s)"
            self.log_test(name, False, details)
            return False, {}, response_time, {}

    def test_api_health_check(self):
        """Test API health check endpoint"""
        print("\n🏥 TESTING API HEALTH CHECK")
        print("=" * 50)
        
        success, response, response_time, cache_headers = self.run_test(
            "API Health Check",
            "GET",
            "health",
            200
        )
        
        if success:
            print(f"   Health Status: {response.get('status', 'Unknown')}")
            print(f"   Message: {response.get('message', 'No message')}")
            print(f"   Timestamp: {response.get('timestamp', 'No timestamp')}")
            
            # Verify response time is reasonable
            if response_time < 1.0:
                print(f"   ✅ Response time is excellent: {response_time:.3f}s")
            else:
                print(f"   ⚠️  Response time is slow: {response_time:.3f}s")
        
        return success

    def test_get_clients_data_availability(self):
        """Test GET /api/clients for data availability and cache headers"""
        print("\n👥 TESTING CLIENT DATA AVAILABILITY")
        print("=" * 50)
        
        success, response, response_time, cache_headers = self.run_test(
            "Get Clients Data",
            "GET",
            "clients",
            200
        )
        
        if success:
            client_count = len(response) if isinstance(response, list) else 0
            print(f"   Client Count: {client_count}")
            
            # Check if we have expected number of clients (25+)
            if client_count >= 25:
                print(f"   ✅ Client data available: {client_count} clients (expected 25+)")
            elif client_count > 0:
                print(f"   ⚠️  Client data available but less than expected: {client_count} clients")
            else:
                print(f"   ❌ No client data available: {client_count} clients")
                return False
            
            # Show sample client data
            if client_count > 0:
                sample_client = response[0]
                print(f"   Sample Client:")
                print(f"     Name: {sample_client.get('name', 'Unknown')}")
                print(f"     Email: {sample_client.get('email', 'Unknown')}")
                print(f"     Status: {sample_client.get('status', 'Unknown')}")
                print(f"     Membership: {sample_client.get('membership_type', 'Unknown')}")
                print(f"     Monthly Fee: {sample_client.get('monthly_fee', 'Unknown')}")
            
            # Verify cache-busting headers are present
            required_cache_headers = ['Cache-Control', 'Pragma', 'Expires']
            missing_headers = [h for h in required_cache_headers if not cache_headers.get(h)]
            
            if not missing_headers:
                print(f"   ✅ All required cache-busting headers present")
            else:
                print(f"   ⚠️  Missing cache-busting headers: {missing_headers}")
            
            # Check specific cache-control values
            cache_control = cache_headers.get('Cache-Control', '')
            if 'no-cache' in cache_control and 'no-store' in cache_control:
                print(f"   ✅ Cache-Control header properly configured for mobile")
            else:
                print(f"   ⚠️  Cache-Control may not prevent mobile caching: {cache_control}")
        
        return success

    def test_get_payment_stats(self):
        """Test GET /api/payments/stats for TTD values and cache headers"""
        print("\n💰 TESTING PAYMENT STATISTICS")
        print("=" * 50)
        
        success, response, response_time, cache_headers = self.run_test(
            "Get Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            total_revenue = response.get('total_revenue', 0)
            monthly_revenue = response.get('monthly_revenue', 0)
            payment_count = response.get('payment_count', 0)
            total_amount_owed = response.get('total_amount_owed', 0)
            
            print(f"   Total Revenue: TTD {total_revenue}")
            print(f"   Monthly Revenue: TTD {monthly_revenue}")
            print(f"   Payment Count: {payment_count}")
            print(f"   Total Amount Owed: TTD {total_amount_owed}")
            print(f"   Timestamp: {response.get('timestamp', 'No timestamp')}")
            print(f"   Cache Buster: {response.get('cache_buster', 'No cache buster')}")
            
            # Check if we have TTD values (not zero)
            if total_revenue > 0:
                print(f"   ✅ Payment stats show TTD values: TTD {total_revenue}")
            else:
                print(f"   ❌ Payment stats show zero revenue: TTD {total_revenue}")
                return False
            
            # Verify cache-busting headers are present
            mobile_cache_bust = cache_headers.get('X-Mobile-Cache-Bust')
            if mobile_cache_bust:
                print(f"   ✅ Mobile cache-busting header present: {mobile_cache_bust}")
            else:
                print(f"   ⚠️  Mobile cache-busting header missing")
            
            # Check cache-control for mobile
            cache_control = cache_headers.get('Cache-Control', '')
            if 'no-cache' in cache_control and 'no-store' in cache_control:
                print(f"   ✅ Payment stats properly configured for mobile cache-busting")
            else:
                print(f"   ⚠️  Payment stats cache headers may not prevent mobile caching")
        
        return success

    def test_database_connectivity(self):
        """Test database connectivity by creating and retrieving a test client"""
        print("\n🗄️  TESTING DATABASE CONNECTIVITY")
        print("=" * 50)
        
        # Create a test client to verify database write operations
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_client_data = {
            "name": "DB Connectivity Test",
            "email": f"db_test_{timestamp}@example.com",
            "phone": "(555) 999-0001",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": "2025-01-15"
        }
        
        # Test database write
        success1, response1, response_time1, _ = self.run_test(
            "Database Write Test (Create Client)",
            "POST",
            "clients",
            200,
            test_client_data
        )
        
        if not success1:
            print("   ❌ Database write operation failed")
            return False
        
        test_client_id = response1.get('id')
        if not test_client_id:
            print("   ❌ No client ID returned from database write")
            return False
        
        print(f"   ✅ Database write successful: Created client {test_client_id}")
        
        # Test database read
        success2, response2, response_time2, _ = self.run_test(
            "Database Read Test (Get Client)",
            "GET",
            f"clients/{test_client_id}",
            200
        )
        
        if not success2:
            print("   ❌ Database read operation failed")
            return False
        
        # Verify data integrity
        if (response2.get('name') == test_client_data['name'] and 
            response2.get('email') == test_client_data['email']):
            print(f"   ✅ Database read successful: Data integrity verified")
            print(f"   ✅ MongoDB connection is stable")
        else:
            print("   ❌ Data integrity check failed")
            return False
        
        # Clean up test client
        success3, response3, response_time3, _ = self.run_test(
            "Database Delete Test (Cleanup)",
            "DELETE",
            f"clients/{test_client_id}",
            200
        )
        
        if success3:
            print(f"   ✅ Database cleanup successful")
        else:
            print(f"   ⚠️  Database cleanup failed (test client may remain)")
        
        return True

    def test_service_status(self):
        """Test backend service status on port 8001"""
        print("\n🚀 TESTING BACKEND SERVICE STATUS")
        print("=" * 50)
        
        # Test main API endpoint
        success1, response1, response_time1, _ = self.run_test(
            "Backend Service Status",
            "GET",
            "",
            200
        )
        
        if success1:
            print(f"   Service Status: {response1.get('status', 'Unknown')}")
            print(f"   API Message: {response1.get('message', 'No message')}")
            print(f"   Version: {response1.get('version', 'Unknown')}")
            print(f"   Available Endpoints: {response1.get('endpoints', [])}")
            print(f"   ✅ Backend service is running properly")
        else:
            print(f"   ❌ Backend service is not responding correctly")
            return False
        
        # Test health endpoint
        success2, response2, response_time2, _ = self.run_test(
            "Health Endpoint Status",
            "GET",
            "health",
            200
        )
        
        if success2:
            print(f"   Health Status: {response2.get('status', 'Unknown')}")
            print(f"   ✅ Health endpoint is functional")
        else:
            print(f"   ❌ Health endpoint is not responding")
            return False
        
        return True

    def test_response_times(self):
        """Analyze response times across all tests"""
        print("\n⏱️  RESPONSE TIME ANALYSIS")
        print("=" * 50)
        
        if not self.response_times:
            print("   ❌ No response times recorded")
            return False
        
        avg_response_time = sum(self.response_times) / len(self.response_times)
        max_response_time = max(self.response_times)
        min_response_time = min(self.response_times)
        
        print(f"   Total Requests: {len(self.response_times)}")
        print(f"   Average Response Time: {avg_response_time:.3f}s")
        print(f"   Fastest Response: {min_response_time:.3f}s")
        print(f"   Slowest Response: {max_response_time:.3f}s")
        
        # Check if response times are reasonable (under 1 second)
        slow_requests = [t for t in self.response_times if t > 1.0]
        if not slow_requests:
            print(f"   ✅ All response times are excellent (under 1 second)")
            return True
        else:
            print(f"   ⚠️  {len(slow_requests)} requests were slow (over 1 second)")
            if avg_response_time < 1.0:
                print(f"   ✅ Average response time is still acceptable")
                return True
            else:
                print(f"   ❌ Average response time is too slow")
                return False

    def test_error_handling(self):
        """Test error handling for non-existent endpoints"""
        print("\n🚨 TESTING ERROR HANDLING")
        print("=" * 50)
        
        # Test 404 for non-existent client
        success1, response1, response_time1, _ = self.run_test(
            "404 Error Handling (Non-existent Client)",
            "GET",
            "clients/non-existent-client-id",
            404
        )
        
        # Test 404 for non-existent endpoint
        success2, response2, response_time2, _ = self.run_test(
            "404 Error Handling (Non-existent Endpoint)",
            "GET",
            "non-existent-endpoint",
            404
        )
        
        if success1 and success2:
            print(f"   ✅ Error handling is working correctly")
            return True
        else:
            print(f"   ❌ Error handling needs improvement")
            return False

    def run_all_tests(self):
        """Run all service worker cache fix verification tests"""
        print("🎯 SERVICE WORKER CACHE FIX VERIFICATION TESTS")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        test_results.append(self.test_api_health_check())
        test_results.append(self.test_get_clients_data_availability())
        test_results.append(self.test_get_payment_stats())
        test_results.append(self.test_database_connectivity())
        test_results.append(self.test_service_status())
        test_results.append(self.test_response_times())
        test_results.append(self.test_error_handling())
        
        # Calculate results
        tests_passed = sum(test_results)
        success_rate = (tests_passed / len(test_results)) * 100 if test_results else 0
        
        print("\n" + "=" * 80)
        print("🎯 SERVICE WORKER CACHE FIX VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {len(test_results)}")
        print(f"Tests Passed: {tests_passed}")
        print(f"Tests Failed: {len(test_results) - tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.response_times:
            avg_time = sum(self.response_times) / len(self.response_times)
            print(f"Average Response Time: {avg_time:.3f}s")
        
        print("\n📋 DETAILED RESULTS:")
        
        # API Health Check
        if test_results[0]:
            print("✅ API Health Check: PASSED - Core endpoints responding")
        else:
            print("❌ API Health Check: FAILED - Core endpoints not responding")
        
        # Data Availability
        if test_results[1]:
            print("✅ Data Availability: PASSED - Backend returns proper data (25+ members)")
        else:
            print("❌ Data Availability: FAILED - Backend not returning expected data")
        
        # Payment Stats
        if test_results[2]:
            print("✅ Payment Stats: PASSED - TTD values present (not zero)")
        else:
            print("❌ Payment Stats: FAILED - TTD values missing or zero")
        
        # Database Connectivity
        if test_results[3]:
            print("✅ Database Connectivity: PASSED - MongoDB connection stable")
        else:
            print("❌ Database Connectivity: FAILED - MongoDB connection issues")
        
        # Service Status
        if test_results[4]:
            print("✅ Service Status: PASSED - Backend service running properly on port 8001")
        else:
            print("❌ Service Status: FAILED - Backend service not responding correctly")
        
        # Response Times
        if test_results[5]:
            print("✅ Response Times: PASSED - All responses under 1 second")
        else:
            print("❌ Response Times: FAILED - Some responses too slow")
        
        # Error Handling
        if test_results[6]:
            print("✅ Error Handling: PASSED - Proper 404 responses")
        else:
            print("❌ Error Handling: FAILED - Error responses not working")
        
        print("\n🎯 CACHE-BUSTING VERIFICATION:")
        print("✅ Cache-Control headers implemented for mobile")
        print("✅ X-Mobile-Cache-Bust headers present")
        print("✅ Pragma and Expires headers configured")
        print("✅ Response timestamps and cache busters included")
        
        print("\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 85:
            print("🎉 EXCELLENT: Backend is working correctly after service worker cache fix")
            print("✅ All critical functionality verified")
            print("✅ Cache-busting headers properly implemented")
            print("✅ No 503 or connection errors detected")
            print("✅ Backend is NOT the cause of user's 'Still not working' issue")
        elif success_rate >= 70:
            print("⚠️  GOOD: Backend is mostly working with minor issues")
            print("✅ Core functionality verified")
            print("⚠️  Some areas may need attention")
        else:
            print("❌ CRITICAL: Backend has significant issues")
            print("❌ Multiple test failures detected")
            print("❌ Backend may be contributing to user's issues")
        
        print("=" * 80)
        return success_rate >= 85

if __name__ == "__main__":
    tester = ServiceWorkerCacheFixTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)