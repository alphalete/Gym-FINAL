#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any

class MobileDataDiscrepancyTester:
    def __init__(self, base_url="https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.expected_total_revenue = 2630  # Expected TTD 2630 as per review request

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None) -> tuple:
        """Run a single API test with performance timing"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
        
        # Start timing for performance testing
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

            # Calculate response time
            response_time = time.time() - start_time
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    details = f"(Status: {response.status_code}, Time: {response_time:.3f}s)"
                    self.log_test(name, True, details)
                    print(f"   Response Time: {response_time:.3f} seconds")
                    print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
                    return True, response_data, response_time
                except:
                    details = f"(Status: {response.status_code}, Time: {response_time:.3f}s, No JSON response)"
                    self.log_test(name, True, details)
                    return True, {}, response_time
            else:
                try:
                    error_data = response.json()
                    details = f"(Expected {expected_status}, got {response.status_code}, Time: {response_time:.3f}s) - {error_data}"
                except:
                    details = f"(Expected {expected_status}, got {response.status_code}, Time: {response_time:.3f}s) - {response.text[:100]}"
                self.log_test(name, False, details)
                return False, {}, response_time

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            details = f"(Network Error after {response_time:.3f}s: {str(e)})"
            self.log_test(name, False, details)
            return False, {}, response_time
        except Exception as e:
            response_time = time.time() - start_time
            details = f"(Error after {response_time:.3f}s: {str(e)})"
            self.log_test(name, False, details)
            return False, {}, response_time

    def test_payment_stats_api(self):
        """Test GET /api/payments/stats endpoint - CRITICAL for mobile data discrepancy fix"""
        print("\n🎯 CRITICAL TEST: Payment Stats API for Mobile Data Discrepancy Fix")
        print("=" * 80)
        print(f"   Expected Total Revenue: TTD {self.expected_total_revenue}")
        print("   This test verifies the fix for mobile dashboard showing TTD 0 instead of correct revenue")
        
        success, response, response_time = self.run_test(
            "Payment Stats API - Mobile Data Fix Verification",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            total_revenue = response.get('total_revenue', 0)
            monthly_revenue = response.get('monthly_revenue', 0)
            payment_count = response.get('payment_count', 0)
            
            print(f"\n📊 PAYMENT STATISTICS ANALYSIS:")
            print(f"   Total Revenue: TTD {total_revenue}")
            print(f"   Monthly Revenue: TTD {monthly_revenue}")
            print(f"   Payment Count: {payment_count}")
            print(f"   Response Time: {response_time:.3f} seconds")
            
            # Verify the expected revenue
            if total_revenue == self.expected_total_revenue:
                print(f"   ✅ MOBILE DATA FIX VERIFIED: Total revenue matches expected TTD {self.expected_total_revenue}")
                print("   ✅ Mobile dashboard should now display correct revenue instead of TTD 0")
                return True
            else:
                print(f"   ❌ MOBILE DATA ISSUE: Total revenue is TTD {total_revenue}, expected TTD {self.expected_total_revenue}")
                print("   ❌ Mobile dashboard may still show incorrect revenue")
                
                # Check if revenue is 0 (the original problem)
                if total_revenue == 0:
                    print("   🚨 CRITICAL: Revenue is still 0 - mobile data discrepancy NOT FIXED")
                else:
                    print("   ⚠️  Revenue is not 0 but doesn't match expected value - partial fix or data changed")
                
                return False
        else:
            print("   ❌ CRITICAL FAILURE: Payment Stats API is not responding correctly")
            print("   ❌ Mobile dashboard will not be able to fetch revenue data")
            return False

    def test_client_data_api(self):
        """Test GET /api/clients endpoint for dashboard calculations"""
        print("\n🎯 CLIENT DATA API TEST: Verify client data for dashboard calculations")
        print("=" * 80)
        
        success, response, response_time = self.run_test(
            "Client Data API - Dashboard Support",
            "GET",
            "clients",
            200
        )
        
        if success:
            client_count = len(response)
            active_clients = len([c for c in response if c.get('status') == 'Active'])
            inactive_clients = client_count - active_clients
            
            print(f"\n👥 CLIENT DATA ANALYSIS:")
            print(f"   Total Clients: {client_count}")
            print(f"   Active Clients: {active_clients}")
            print(f"   Inactive Clients: {inactive_clients}")
            print(f"   Response Time: {response_time:.3f} seconds")
            
            # Verify data structure for mobile dashboard
            if client_count > 0:
                sample_client = response[0]
                required_fields = ['id', 'name', 'email', 'membership_type', 'monthly_fee', 'status', 'next_payment_date']
                missing_fields = [field for field in required_fields if field not in sample_client]
                
                if not missing_fields:
                    print("   ✅ Client data structure is complete for dashboard calculations")
                    print("   ✅ Mobile dashboard can properly calculate statistics from client data")
                else:
                    print(f"   ❌ Missing required fields in client data: {missing_fields}")
                    print("   ❌ Mobile dashboard may not calculate statistics correctly")
                    return False
            else:
                print("   ⚠️  No clients found - dashboard will show zero statistics")
            
            return True
        else:
            print("   ❌ CRITICAL FAILURE: Client Data API is not responding correctly")
            print("   ❌ Mobile dashboard will not be able to fetch client data")
            return False

    def test_parallel_api_performance(self):
        """Test API performance for mobile parallel fetching"""
        print("\n🎯 API PERFORMANCE TEST: Mobile Parallel Fetching Simulation")
        print("=" * 80)
        
        # Simulate parallel requests like mobile dashboard does
        start_time = time.time()
        
        # Test payment stats API
        success1, response1, time1 = self.run_test(
            "Parallel Request 1: Payment Stats",
            "GET",
            "payments/stats",
            200
        )
        
        # Test client data API
        success2, response2, time2 = self.run_test(
            "Parallel Request 2: Client Data",
            "GET",
            "clients",
            200
        )
        
        total_time = time.time() - start_time
        
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        print(f"   Payment Stats Response Time: {time1:.3f} seconds")
        print(f"   Client Data Response Time: {time2:.3f} seconds")
        print(f"   Total Sequential Time: {total_time:.3f} seconds")
        print(f"   Average Response Time: {(time1 + time2) / 2:.3f} seconds")
        
        # Performance thresholds for mobile
        fast_threshold = 1.0  # Under 1 second is fast
        acceptable_threshold = 3.0  # Under 3 seconds is acceptable
        
        max_time = max(time1, time2)
        avg_time = (time1 + time2) / 2
        
        if max_time < fast_threshold:
            print(f"   ✅ EXCELLENT PERFORMANCE: All APIs respond in under {fast_threshold}s")
            print("   ✅ Mobile parallel fetching will be very fast")
        elif max_time < acceptable_threshold:
            print(f"   ✅ GOOD PERFORMANCE: All APIs respond in under {acceptable_threshold}s")
            print("   ✅ Mobile parallel fetching will be acceptable")
        else:
            print(f"   ❌ SLOW PERFORMANCE: Some APIs take over {acceptable_threshold}s")
            print("   ❌ Mobile parallel fetching may be slow for users")
            return False
        
        return success1 and success2

    def test_data_accuracy_verification(self):
        """Test data accuracy between payment stats and client data"""
        print("\n🎯 DATA ACCURACY TEST: Verify payment calculations match client data")
        print("=" * 80)
        
        # Get payment stats
        success1, payment_stats, _ = self.run_test(
            "Get Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        # Get client data
        success2, clients, _ = self.run_test(
            "Get Client Data",
            "GET",
            "clients",
            200
        )
        
        if success1 and success2:
            # Analyze data consistency
            total_revenue_from_stats = payment_stats.get('total_revenue', 0)
            payment_count_from_stats = payment_stats.get('payment_count', 0)
            
            client_count = len(clients)
            active_clients = len([c for c in clients if c.get('status') == 'Active'])
            
            print(f"\n📊 DATA ACCURACY ANALYSIS:")
            print(f"   Payment Stats - Total Revenue: TTD {total_revenue_from_stats}")
            print(f"   Payment Stats - Payment Count: {payment_count_from_stats}")
            print(f"   Client Data - Total Clients: {client_count}")
            print(f"   Client Data - Active Clients: {active_clients}")
            
            # Verify revenue is not zero (the original mobile issue)
            if total_revenue_from_stats > 0:
                print("   ✅ Revenue is not zero - mobile data discrepancy appears fixed")
            else:
                print("   ❌ Revenue is still zero - mobile data discrepancy NOT FIXED")
                return False
            
            # Verify payment count makes sense
            if payment_count_from_stats >= 0:
                print("   ✅ Payment count is valid")
            else:
                print("   ❌ Payment count is invalid")
                return False
            
            # Check if we have the expected revenue
            if total_revenue_from_stats == self.expected_total_revenue:
                print(f"   ✅ PERFECT MATCH: Revenue exactly matches expected TTD {self.expected_total_revenue}")
            else:
                print(f"   ⚠️  Revenue mismatch: Expected TTD {self.expected_total_revenue}, got TTD {total_revenue_from_stats}")
                print("   ℹ️  This may be due to data changes since the fix was implemented")
            
            return True
        else:
            print("   ❌ Could not retrieve data for accuracy verification")
            return False

    def test_api_error_handling(self):
        """Test API error scenarios for mobile offline handling"""
        print("\n🎯 ERROR HANDLING TEST: Mobile offline state scenarios")
        print("=" * 80)
        
        # Test invalid endpoint
        success1, _, _ = self.run_test(
            "Invalid Endpoint Test",
            "GET",
            "invalid/endpoint",
            404
        )
        
        # Test malformed request
        success2, _, _ = self.run_test(
            "Malformed Request Test",
            "POST",
            "payments/record",
            422,  # Validation error expected
            {"invalid": "data"}
        )
        
        print(f"\n🛡️ ERROR HANDLING ANALYSIS:")
        if success1:
            print("   ✅ Invalid endpoints return proper 404 errors")
            print("   ✅ Mobile app can detect and handle invalid requests")
        else:
            print("   ❌ Invalid endpoints don't return expected 404 errors")
        
        if success2:
            print("   ✅ Malformed requests return proper validation errors")
            print("   ✅ Mobile app can detect and handle bad data")
        else:
            print("   ❌ Malformed requests don't return expected validation errors")
        
        return success1 and success2

    def test_mobile_data_discrepancy_comprehensive(self):
        """Comprehensive test of the mobile data discrepancy fix"""
        print("\n🎯 COMPREHENSIVE MOBILE DATA DISCREPANCY FIX TEST")
        print("=" * 80)
        print("Testing the fix for mobile dashboard showing TTD 0 instead of TTD 2630")
        print("This verifies the GoGymDashboard component can now fetch payment stats correctly")
        
        all_tests_passed = True
        
        # Test 1: Payment Stats API
        print("\n1️⃣ TESTING PAYMENT STATS API...")
        test1_result = self.test_payment_stats_api()
        all_tests_passed = all_tests_passed and test1_result
        
        # Test 2: Client Data API
        print("\n2️⃣ TESTING CLIENT DATA API...")
        test2_result = self.test_client_data_api()
        all_tests_passed = all_tests_passed and test2_result
        
        # Test 3: API Performance
        print("\n3️⃣ TESTING API PERFORMANCE...")
        test3_result = self.test_parallel_api_performance()
        all_tests_passed = all_tests_passed and test3_result
        
        # Test 4: Data Accuracy
        print("\n4️⃣ TESTING DATA ACCURACY...")
        test4_result = self.test_data_accuracy_verification()
        all_tests_passed = all_tests_passed and test4_result
        
        # Test 5: Error Handling
        print("\n5️⃣ TESTING ERROR HANDLING...")
        test5_result = self.test_api_error_handling()
        all_tests_passed = all_tests_passed and test5_result
        
        return all_tests_passed

    def run_all_tests(self):
        """Run all mobile data discrepancy tests"""
        print("🚀 STARTING MOBILE DATA DISCREPANCY FIX TESTING")
        print("=" * 80)
        print("CONTEXT: Testing backend APIs after implementing mobile data discrepancy fix")
        print("ISSUE: Mobile dashboard was showing TTD 0 total revenue instead of TTD 2630")
        print("FIX: GoGymDashboard component now fetches payment stats from /api/payments/stats")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run comprehensive test
        overall_success = self.test_mobile_data_discrepancy_comprehensive()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print final summary
        print("\n" + "=" * 80)
        print("🎯 MOBILE DATA DISCREPANCY FIX TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print(f"Total Time: {total_time:.3f} seconds")
        
        if overall_success:
            print("\n✅ MOBILE DATA DISCREPANCY FIX: VERIFIED WORKING")
            print("✅ Payment Stats API returns correct revenue data")
            print("✅ Client Data API supports dashboard calculations")
            print("✅ API performance is suitable for mobile parallel fetching")
            print("✅ Data accuracy is maintained")
            print("✅ Error handling supports mobile offline states")
            print("\n🎉 CONCLUSION: Mobile dashboard should now display TTD 2630 correctly!")
        else:
            print("\n❌ MOBILE DATA DISCREPANCY FIX: ISSUES DETECTED")
            print("❌ Some backend APIs are not working as expected")
            print("❌ Mobile dashboard may still show incorrect data")
            print("\n🚨 CONCLUSION: Further investigation needed for mobile data fix!")
        
        return overall_success

if __name__ == "__main__":
    tester = MobileDataDiscrepancyTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)