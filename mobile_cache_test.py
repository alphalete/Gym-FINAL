#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any
import time

class MobileCacheIssueAPITester:
    def __init__(self, base_url="https://276b2f1f-9d6e-4215-a382-5da8671edad7.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.revenue_values = []
        self.client_counts = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> tuple:
        """Run a single API test with mobile-specific headers"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        
        # Default headers with mobile cache-busting
        default_headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'If-None-Match': '*',
            'User-Agent': 'Mobile-Cache-Test/1.0'
        }
        
        if headers:
            default_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Headers: {json.dumps(default_headers, indent=2)}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=30)

            response_time = time.time() - start_time
            success = response.status_code == expected_status
            
            print(f"   Response Time: {response_time:.3f}s")
            print(f"   Response Headers:")
            for header, value in response.headers.items():
                if 'cache' in header.lower() or 'etag' in header.lower() or 'expires' in header.lower():
                    print(f"      {header}: {value}")
            
            if success:
                try:
                    response_data = response.json()
                    details = f"(Status: {response.status_code}, Time: {response_time:.3f}s)"
                    self.log_test(name, True, details)
                    print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
                    return True, response_data
                except:
                    details = f"(Status: {response.status_code}, No JSON response, Time: {response_time:.3f}s)"
                    self.log_test(name, True, details)
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    details = f"(Expected {expected_status}, got {response.status_code}) - {error_data}"
                except:
                    details = f"(Expected {expected_status}, got {response.status_code}) - {response.text[:100]}"
                self.log_test(name, False, details)
                return False, {}

        except requests.exceptions.RequestException as e:
            details = f"(Network Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}
        except Exception as e:
            details = f"(Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}

    def test_payment_stats_consistency(self):
        """Test GET /api/payments/stats multiple times to check for consistency"""
        print("\n🎯 MOBILE CACHE ISSUE TEST: Payment Stats Consistency")
        print("=" * 80)
        
        revenue_values = []
        payment_counts = []
        
        for i in range(5):
            success, response = self.run_test(
                f"Payment Stats Request #{i+1}",
                "GET",
                "payments/stats",
                200
            )
            
            if success:
                total_revenue = response.get('total_revenue', 0)
                payment_count = response.get('payment_count', 0)
                timestamp = response.get('timestamp', 'N/A')
                cache_buster = response.get('cache_buster', 'N/A')
                
                revenue_values.append(total_revenue)
                payment_counts.append(payment_count)
                
                print(f"   Request #{i+1}: Revenue=TTD {total_revenue}, Count={payment_count}")
                print(f"   Timestamp: {timestamp}")
                print(f"   Cache Buster: {cache_buster}")
                
                # Small delay between requests
                time.sleep(0.5)
        
        # Check consistency
        unique_revenues = set(revenue_values)
        unique_counts = set(payment_counts)
        
        print(f"\n📊 CONSISTENCY ANALYSIS:")
        print(f"   Revenue values: {revenue_values}")
        print(f"   Unique revenue values: {list(unique_revenues)}")
        print(f"   Payment counts: {payment_counts}")
        print(f"   Unique payment counts: {list(unique_counts)}")
        
        if len(unique_revenues) == 1 and len(unique_counts) == 1:
            print("   ✅ DATA CONSISTENCY: PERFECT - All requests returned identical values")
            current_revenue = list(unique_revenues)[0]
            current_count = list(unique_counts)[0]
            
            # Check if this matches user's reported issue
            if current_revenue == 5000:
                print("   ⚠️  MOBILE ISSUE DETECTED: Revenue shows TTD 5000 (user's reported stale value)")
            elif current_revenue == 2630:
                print("   ✅ MOBILE ISSUE RESOLVED: Revenue shows TTD 2630 (expected current value)")
            else:
                print(f"   ℹ️  CURRENT REVENUE: TTD {current_revenue} (different from both reported values)")
                
            return True
        else:
            print("   ❌ DATA INCONSISTENCY: Different values returned across requests")
            return False

    def test_clients_count_consistency(self):
        """Test GET /api/clients multiple times to check client count consistency"""
        print("\n🎯 MOBILE CACHE ISSUE TEST: Client Count Consistency")
        print("=" * 80)
        
        client_counts = []
        active_counts = []
        
        for i in range(5):
            success, response = self.run_test(
                f"Clients Request #{i+1}",
                "GET",
                "clients",
                200
            )
            
            if success:
                total_clients = len(response)
                active_clients = len([c for c in response if c.get('status') == 'Active'])
                
                client_counts.append(total_clients)
                active_counts.append(active_clients)
                
                print(f"   Request #{i+1}: Total={total_clients}, Active={active_clients}")
                
                # Show sample client data
                if response and len(response) > 0:
                    sample_client = response[0]
                    print(f"   Sample client: {sample_client.get('name')} - {sample_client.get('email')}")
                
                # Small delay between requests
                time.sleep(0.5)
        
        # Check consistency
        unique_totals = set(client_counts)
        unique_actives = set(active_counts)
        
        print(f"\n📊 CLIENT COUNT ANALYSIS:")
        print(f"   Total client counts: {client_counts}")
        print(f"   Unique total counts: {list(unique_totals)}")
        print(f"   Active client counts: {active_counts}")
        print(f"   Unique active counts: {list(unique_actives)}")
        
        if len(unique_totals) == 1 and len(unique_actives) == 1:
            print("   ✅ CLIENT COUNT CONSISTENCY: PERFECT - All requests returned identical counts")
            current_total = list(unique_totals)[0]
            current_active = list(unique_actives)[0]
            
            # Check if this matches user's reported issue
            if current_total == 0:
                print("   ⚠️  MOBILE ISSUE DETECTED: Client count shows 0 (user's reported stale value)")
            else:
                print(f"   ✅ MOBILE ISSUE STATUS: Client count shows {current_total} total, {current_active} active")
                
            return True
        else:
            print("   ❌ CLIENT COUNT INCONSISTENCY: Different counts returned across requests")
            return False

    def test_cache_busting_headers(self):
        """Test that cache-busting headers are being set correctly by backend"""
        print("\n🎯 MOBILE CACHE ISSUE TEST: Cache-Busting Headers Verification")
        print("=" * 80)
        
        endpoints_to_test = [
            ("payments/stats", "Payment Stats"),
            ("clients", "Clients List")
        ]
        
        all_headers_correct = True
        
        for endpoint, name in endpoints_to_test:
            success, response = self.run_test(
                f"Cache Headers Test - {name}",
                "GET",
                endpoint,
                200
            )
            
            if success:
                # Check for cache-busting headers in the actual response
                print(f"\n   📋 CACHE HEADERS ANALYSIS for {name}:")
                
                # We need to make a raw request to check response headers
                url = f"{self.api_url}/{endpoint}"
                raw_response = requests.get(url, timeout=30)
                
                expected_headers = {
                    'Cache-Control': ['no-cache', 'no-store', 'must-revalidate'],
                    'Pragma': ['no-cache'],
                    'Expires': ['0']
                }
                
                headers_found = {}
                for header_name, expected_values in expected_headers.items():
                    actual_value = raw_response.headers.get(header_name, 'NOT FOUND')
                    headers_found[header_name] = actual_value
                    
                    print(f"      {header_name}: {actual_value}")
                    
                    # Check if expected values are present
                    if actual_value != 'NOT FOUND':
                        has_expected = any(val in actual_value.lower() for val in expected_values)
                        if has_expected:
                            print(f"         ✅ Contains expected cache-busting values")
                        else:
                            print(f"         ❌ Missing expected cache-busting values: {expected_values}")
                            all_headers_correct = False
                    else:
                        print(f"         ❌ Header not found")
                        all_headers_correct = False
                
                # Check for mobile-specific headers
                mobile_headers = ['X-Mobile-Cache-Bust', 'ETag', 'Last-Modified', 'Vary']
                for header in mobile_headers:
                    value = raw_response.headers.get(header, 'NOT FOUND')
                    print(f"      {header}: {value}")
                    if value != 'NOT FOUND':
                        print(f"         ✅ Mobile-specific header present")
        
        if all_headers_correct:
            print("\n   ✅ CACHE-BUSTING HEADERS: ALL CORRECT")
            print("   ✅ Backend is setting proper cache-busting headers")
        else:
            print("\n   ❌ CACHE-BUSTING HEADERS: SOME MISSING OR INCORRECT")
            print("   ❌ Backend cache-busting implementation needs review")
        
        return all_headers_correct

    def test_database_operations_impact(self):
        """Test if recent database operations might have affected the data"""
        print("\n🎯 MOBILE CACHE ISSUE TEST: Database Operations Impact")
        print("=" * 80)
        
        # Step 1: Get current state
        success1, stats_before = self.run_test(
            "Get Payment Stats Before Test Operation",
            "GET",
            "payments/stats",
            200
        )
        
        success2, clients_before = self.run_test(
            "Get Clients Before Test Operation",
            "GET",
            "clients",
            200
        )
        
        if not (success1 and success2):
            print("❌ Failed to get initial state - aborting database impact test")
            return False
        
        initial_revenue = stats_before.get('total_revenue', 0)
        initial_client_count = len(clients_before)
        
        print(f"   📊 INITIAL STATE:")
        print(f"      Revenue: TTD {initial_revenue}")
        print(f"      Client Count: {initial_client_count}")
        
        # Step 2: Create a test client to simulate database operation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_client_data = {
            "name": "Mobile Cache Test Client",
            "email": f"mobile_cache_test_{timestamp}@example.com",
            "phone": "(555) 999-0001",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-25"
        }
        
        success3, create_response = self.run_test(
            "Create Test Client (Database Operation)",
            "POST",
            "clients",
            200,
            test_client_data
        )
        
        if not success3:
            print("❌ Failed to create test client")
            return False
        
        test_client_id = create_response.get('id')
        print(f"   ✅ Created test client ID: {test_client_id}")
        
        # Step 3: Record a payment for the test client
        payment_data = {
            "client_id": test_client_id,
            "amount_paid": 50.00,
            "payment_date": "2025-01-25",
            "payment_method": "Test Payment",
            "notes": "Mobile cache test payment"
        }
        
        success4, payment_response = self.run_test(
            "Record Test Payment (Database Operation)",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success4:
            print("❌ Failed to record test payment")
            return False
        
        print(f"   ✅ Recorded payment: TTD {payment_data['amount_paid']}")
        
        # Step 4: Check if data is immediately updated
        success5, stats_after = self.run_test(
            "Get Payment Stats After Operations",
            "GET",
            "payments/stats",
            200
        )
        
        success6, clients_after = self.run_test(
            "Get Clients After Operations",
            "GET",
            "clients",
            200
        )
        
        if success5 and success6:
            final_revenue = stats_after.get('total_revenue', 0)
            final_client_count = len(clients_after)
            
            print(f"\n   📊 FINAL STATE:")
            print(f"      Revenue: TTD {final_revenue}")
            print(f"      Client Count: {final_client_count}")
            
            print(f"\n   📊 CHANGES:")
            revenue_change = final_revenue - initial_revenue
            client_change = final_client_count - initial_client_count
            
            print(f"      Revenue Change: TTD {revenue_change}")
            print(f"      Client Count Change: {client_change}")
            
            # Verify expected changes
            expected_revenue_change = 50.00  # The payment we recorded
            expected_client_change = 1  # The client we created
            
            if abs(revenue_change - expected_revenue_change) < 0.01 and client_change == expected_client_change:
                print("   ✅ DATABASE OPERATIONS: IMMEDIATE UPDATE WORKING")
                print("   ✅ Data changes are reflected immediately in API responses")
                
                # Clean up - delete the test client
                success7, delete_response = self.run_test(
                    "Clean Up - Delete Test Client",
                    "DELETE",
                    f"clients/{test_client_id}",
                    200
                )
                
                if success7:
                    print(f"   ✅ Cleanup completed - deleted test client and payment records")
                
                return True
            else:
                print("   ❌ DATABASE OPERATIONS: UPDATE DELAY OR INCONSISTENCY")
                print(f"   ❌ Expected revenue change: TTD {expected_revenue_change}, got: TTD {revenue_change}")
                print(f"   ❌ Expected client change: {expected_client_change}, got: {client_change}")
                return False
        
        return False

    def test_mobile_specific_scenarios(self):
        """Test mobile-specific scenarios that might cause caching issues"""
        print("\n🎯 MOBILE CACHE ISSUE TEST: Mobile-Specific Scenarios")
        print("=" * 80)
        
        # Test 1: Rapid successive requests (mobile app behavior)
        print("\n   📱 Test 1: Rapid Successive Requests")
        rapid_results = []
        
        for i in range(3):
            success, response = self.run_test(
                f"Rapid Request #{i+1}",
                "GET",
                "payments/stats",
                200
            )
            if success:
                rapid_results.append(response.get('total_revenue', 0))
            time.sleep(0.1)  # Very short delay
        
        if len(set(rapid_results)) == 1:
            print("   ✅ Rapid requests return consistent data")
        else:
            print(f"   ❌ Rapid requests return inconsistent data: {rapid_results}")
        
        # Test 2: Different User-Agent headers (mobile vs desktop)
        print("\n   📱 Test 2: Different User-Agent Headers")
        
        mobile_headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'}
        desktop_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        success_mobile, mobile_response = self.run_test(
            "Mobile User-Agent Request",
            "GET",
            "payments/stats",
            200,
            headers=mobile_headers
        )
        
        success_desktop, desktop_response = self.run_test(
            "Desktop User-Agent Request",
            "GET",
            "payments/stats",
            200,
            headers=desktop_headers
        )
        
        if success_mobile and success_desktop:
            mobile_revenue = mobile_response.get('total_revenue', 0)
            desktop_revenue = desktop_response.get('total_revenue', 0)
            
            if mobile_revenue == desktop_revenue:
                print(f"   ✅ User-Agent doesn't affect data: TTD {mobile_revenue}")
            else:
                print(f"   ❌ User-Agent affects data: Mobile=TTD {mobile_revenue}, Desktop=TTD {desktop_revenue}")
        
        # Test 3: Connection simulation (mobile network conditions)
        print("\n   📱 Test 3: Connection Quality Simulation")
        
        # Test with different timeout values to simulate mobile network
        timeouts = [5, 10, 30]
        timeout_results = []
        
        for timeout in timeouts:
            try:
                url = f"{self.api_url}/payments/stats"
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    data = response.json()
                    timeout_results.append(data.get('total_revenue', 0))
                    print(f"   Timeout {timeout}s: TTD {data.get('total_revenue', 0)}")
            except requests.exceptions.Timeout:
                print(f"   Timeout {timeout}s: REQUEST TIMEOUT")
                timeout_results.append(None)
            except Exception as e:
                print(f"   Timeout {timeout}s: ERROR - {str(e)}")
                timeout_results.append(None)
        
        valid_results = [r for r in timeout_results if r is not None]
        if len(set(valid_results)) <= 1:
            print("   ✅ Network conditions don't affect data consistency")
        else:
            print(f"   ❌ Network conditions affect data: {valid_results}")
        
        return True

    def run_comprehensive_mobile_cache_test(self):
        """Run comprehensive mobile cache issue testing"""
        print("🎯 COMPREHENSIVE MOBILE CACHE ISSUE TESTING")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"API endpoint: {self.api_url}")
        print("=" * 80)
        
        # Run all mobile cache-specific tests
        test_results = []
        
        test_results.append(self.test_payment_stats_consistency())
        test_results.append(self.test_clients_count_consistency())
        test_results.append(self.test_cache_busting_headers())
        test_results.append(self.test_database_operations_impact())
        test_results.append(self.test_mobile_specific_scenarios())
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 MOBILE CACHE ISSUE TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"📊 Individual API Tests: {self.tests_passed}/{self.tests_run} passed")
        
        if success_rate >= 80:
            print("✅ MOBILE CACHE ISSUE STATUS: LIKELY RESOLVED")
            print("✅ Backend APIs are responding consistently with proper cache-busting")
        else:
            print("❌ MOBILE CACHE ISSUE STATUS: STILL PRESENT")
            print("❌ Backend APIs show inconsistencies or cache-busting issues")
        
        # Specific findings for the user's reported issue
        print("\n🔍 SPECIFIC FINDINGS FOR USER'S REPORTED ISSUE:")
        print("   User reported: Mobile device shows 'TTD 5000' revenue and '0 members'")
        
        if hasattr(self, 'revenue_values') and self.revenue_values:
            current_revenue = self.revenue_values[-1] if self.revenue_values else "Unknown"
            print(f"   Current backend revenue: TTD {current_revenue}")
            
            if current_revenue == 5000:
                print("   ⚠️  ISSUE CONFIRMED: Backend still returning stale TTD 5000 value")
            elif current_revenue == 2630:
                print("   ✅ ISSUE RESOLVED: Backend returning expected TTD 2630 value")
            else:
                print(f"   ℹ️  CURRENT STATE: Backend returning TTD {current_revenue}")
        
        if hasattr(self, 'client_counts') and self.client_counts:
            current_clients = self.client_counts[-1] if self.client_counts else "Unknown"
            print(f"   Current backend client count: {current_clients}")
            
            if current_clients == 0:
                print("   ⚠️  ISSUE CONFIRMED: Backend returning 0 clients")
            else:
                print(f"   ✅ CLIENT COUNT: Backend returning {current_clients} clients")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = MobileCacheIssueAPITester()
    success = tester.run_comprehensive_mobile_cache_test()
    sys.exit(0 if success else 1)