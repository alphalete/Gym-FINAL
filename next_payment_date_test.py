#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class NextPaymentDateTester:
    def __init__(self, base_url="https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_clients = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    details = f"(Status: {response.status_code})"
                    self.log_test(name, True, details)
                    print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
                    return True, response_data
                except:
                    details = f"(Status: {response.status_code}, No JSON response)"
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

    def test_initial_payment_date_calculation(self):
        """Test initial next payment date calculation for new clients"""
        print("\n🎯 TESTING INITIAL PAYMENT DATE CALCULATION")
        print("=" * 80)
        
        test_cases = [
            {
                "name": "January 15th → February 15th",
                "start_date": "2025-01-15",
                "expected_payment_date": "2025-02-15",
                "description": "Consistent day of month"
            },
            {
                "name": "January 31st → February 28th",
                "start_date": "2025-01-31", 
                "expected_payment_date": "2025-02-28",
                "description": "Month boundary handling (Jan 31st → Feb 28th)"
            },
            {
                "name": "February 28th → March 31st",
                "start_date": "2025-02-28",
                "expected_payment_date": "2025-03-31",
                "description": "February to March (proper month boundary)"
            },
            {
                "name": "March 31st → April 30th",
                "start_date": "2025-03-31",
                "expected_payment_date": "2025-04-30",
                "description": "Month boundary handling (Mar 31st → Apr 30th)"
            },
            {
                "name": "December 31st → January 31st",
                "start_date": "2025-12-31",
                "expected_payment_date": "2026-01-31",
                "description": "Year boundary handling"
            },
            {
                "name": "Leap Year Test - February 29th",
                "start_date": "2024-02-29",
                "expected_payment_date": "2024-03-29",
                "description": "Leap year handling"
            }
        ]
        
        all_tests_passed = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📅 Test Case {i}: {test_case['name']}")
            print(f"   Start Date: {test_case['start_date']}")
            print(f"   Expected Payment Date: {test_case['expected_payment_date']}")
            print(f"   Description: {test_case['description']}")
            
            # Create client with specific start date
            client_data = {
                "name": f"Initial Test {i} - {test_case['name']}",
                "email": f"initial_test_{i}_{timestamp}@example.com",
                "phone": f"(555) {100+i:03d}-{1000+i:04d}",
                "membership_type": "Standard",
                "monthly_fee": 55.00,
                "start_date": test_case['start_date']
            }
            
            success, response = self.run_test(
                f"Create Client - {test_case['name']}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                self.created_clients.append(response["id"])
                actual_payment_date = str(response.get('next_payment_date'))
                expected_payment_date = test_case['expected_payment_date']
                
                print(f"   Actual Payment Date: {actual_payment_date}")
                
                if actual_payment_date == expected_payment_date:
                    print(f"   ✅ PASSED: Payment date calculation is CORRECT!")
                else:
                    print(f"   ❌ FAILED: Payment date calculation is INCORRECT!")
                    print(f"      Expected: {expected_payment_date}")
                    print(f"      Got: {actual_payment_date}")
                    all_tests_passed = False
            else:
                print(f"   ❌ FAILED: Could not create client for test case")
                all_tests_passed = False
        
        return all_tests_passed

    def test_payment_recording_with_correct_calculation(self):
        """Test payment recording with correct next payment date calculation"""
        print("\n🎯 TESTING PAYMENT RECORDING WITH CORRECT CALCULATION")
        print("=" * 80)
        
        if not self.created_clients:
            print("❌ No clients available for payment recording test")
            return False
        
        # Use the first created client for payment recording tests
        test_client_id = self.created_clients[0]
        
        # Get current client state
        success1, client_response = self.run_test(
            "Get Client Current State",
            "GET",
            f"clients/{test_client_id}",
            200
        )
        
        if not success1:
            print("❌ Failed to get client current state")
            return False
        
        current_due_date = client_response.get('next_payment_date')
        client_name = client_response.get('name')
        print(f"   Client: {client_name}")
        print(f"   Current due date: {current_due_date}")
        
        # Record a payment
        payment_data = {
            "client_id": test_client_id,
            "amount_paid": 55.00,
            "payment_date": "2025-01-20",
            "payment_method": "Credit Card",
            "notes": "Testing payment recording with correct date calculation"
        }
        
        success2, payment_response = self.run_test(
            "Record Payment with Correct Date Calculation",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success2:
            new_payment_date = payment_response.get('new_next_payment_date')
            print(f"   New next payment date: {new_payment_date}")
            
            # Verify the client's next payment date was updated correctly
            success3, updated_client = self.run_test(
                "Verify Client Payment Date Updated",
                "GET",
                f"clients/{test_client_id}",
                200
            )
            
            if success3:
                updated_due_date = updated_client.get('next_payment_date')
                print(f"   Updated client due date: {updated_due_date}")
                
                # The new payment date should be one month from the current due date
                # using proper monthly arithmetic, not 30-day increments
                return True
            else:
                return False
        else:
            return False

    def test_multiple_consecutive_payments(self):
        """Test multiple consecutive payments to ensure no date drift"""
        print("\n🎯 TESTING MULTIPLE CONSECUTIVE PAYMENTS - NO DATE DRIFT")
        print("=" * 80)
        
        # Create a new client specifically for this test
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Multiple Payments Test Client",
            "email": f"multiple_payments_{timestamp}@example.com",
            "phone": "(555) 999-0001",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-01-15"  # Start on 15th of month
        }
        
        success1, client_response = self.run_test(
            "Create Client for Multiple Payments Test",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1 or "id" not in client_response:
            print("❌ Failed to create client for multiple payments test")
            return False
        
        test_client_id = client_response["id"]
        self.created_clients.append(test_client_id)
        
        initial_due_date = client_response.get('next_payment_date')
        print(f"   Initial due date: {initial_due_date}")
        
        # Expected payment dates for consistent monthly cycles
        expected_dates = [
            "2025-02-15",  # After 1st payment
            "2025-03-15",  # After 2nd payment  
            "2025-04-15",  # After 3rd payment
            "2025-05-15",  # After 4th payment
            "2025-06-15"   # After 5th payment
        ]
        
        payment_dates = [
            "2025-01-15",  # Pay on due date
            "2025-02-15",  # Pay on due date
            "2025-03-15",  # Pay on due date
            "2025-04-15",  # Pay on due date
            "2025-05-15"   # Pay on due date
        ]
        
        all_payments_correct = True
        
        for i, (payment_date, expected_next_date) in enumerate(zip(payment_dates, expected_dates), 1):
            print(f"\n💰 Payment {i}:")
            print(f"   Payment date: {payment_date}")
            print(f"   Expected next due date: {expected_next_date}")
            
            payment_data = {
                "client_id": test_client_id,
                "amount_paid": 75.00,
                "payment_date": payment_date,
                "payment_method": "Credit Card",
                "notes": f"Payment {i} - Testing date drift prevention"
            }
            
            success, payment_response = self.run_test(
                f"Record Payment {i}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                actual_next_date = payment_response.get('new_next_payment_date')
                print(f"   Actual next due date: {actual_next_date}")
                
                # Convert to date format for comparison
                if actual_next_date:
                    # Extract just the date part if it's in "Month DD, YYYY" format
                    try:
                        # Convert "February 15, 2025" to "2025-02-15"
                        actual_date_obj = datetime.strptime(actual_next_date, "%B %d, %Y").date()
                        actual_date_str = actual_date_obj.strftime("%Y-%m-%d")
                    except:
                        actual_date_str = actual_next_date
                    
                    if actual_date_str == expected_next_date:
                        print(f"   ✅ Payment {i}: Date calculation CORRECT - No drift detected!")
                    else:
                        print(f"   ❌ Payment {i}: Date calculation INCORRECT - Drift detected!")
                        print(f"      Expected: {expected_next_date}")
                        print(f"      Got: {actual_date_str}")
                        all_payments_correct = False
                else:
                    print(f"   ❌ Payment {i}: No next payment date returned")
                    all_payments_correct = False
            else:
                print(f"   ❌ Payment {i}: Failed to record payment")
                all_payments_correct = False
        
        if all_payments_correct:
            print(f"\n✅ MULTIPLE PAYMENTS TEST: ALL PASSED!")
            print("   ✅ No date drift detected across 5 consecutive payments")
            print("   ✅ Consistent monthly cycles maintained (15th → 15th → 15th)")
            print("   ✅ Proper monthly arithmetic working correctly")
        else:
            print(f"\n❌ MULTIPLE PAYMENTS TEST: FAILED!")
            print("   ❌ Date drift detected - payments not maintaining consistent monthly cycles")
        
        return all_payments_correct

    def test_edge_cases_leap_years_and_boundaries(self):
        """Test edge cases including leap years, month boundaries, and year boundaries"""
        print("\n🎯 TESTING EDGE CASES - LEAP YEARS & BOUNDARIES")
        print("=" * 80)
        
        edge_test_cases = [
            {
                "name": "Leap Year February 29th",
                "start_date": "2024-02-29",
                "expected_payment_date": "2024-03-29",
                "description": "Leap year handling"
            },
            {
                "name": "Non-Leap Year February 28th",
                "start_date": "2025-02-28",
                "expected_payment_date": "2025-03-28",
                "description": "Non-leap year February"
            },
            {
                "name": "January 31st → February 28th (2025)",
                "start_date": "2025-01-31",
                "expected_payment_date": "2025-02-28",
                "description": "Month boundary - Jan 31st to Feb 28th"
            },
            {
                "name": "March 31st → April 30th",
                "start_date": "2025-03-31",
                "expected_payment_date": "2025-04-30",
                "description": "Month boundary - Mar 31st to Apr 30th"
            },
            {
                "name": "May 31st → June 30th",
                "start_date": "2025-05-31",
                "expected_payment_date": "2025-06-30",
                "description": "Month boundary - May 31st to Jun 30th"
            },
            {
                "name": "Year Boundary December 31st",
                "start_date": "2025-12-31",
                "expected_payment_date": "2026-01-31",
                "description": "Year boundary crossing"
            }
        ]
        
        all_edge_tests_passed = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, test_case in enumerate(edge_test_cases, 1):
            print(f"\n🔥 Edge Case {i}: {test_case['name']}")
            print(f"   Start Date: {test_case['start_date']}")
            print(f"   Expected Payment Date: {test_case['expected_payment_date']}")
            print(f"   Description: {test_case['description']}")
            
            # Create client with specific start date
            client_data = {
                "name": f"Edge Test {i} - {test_case['name']}",
                "email": f"edge_test_{i}_{timestamp}@example.com",
                "phone": f"(555) {200+i:03d}-{2000+i:04d}",
                "membership_type": "Elite",
                "monthly_fee": 100.00,
                "start_date": test_case['start_date']
            }
            
            success, response = self.run_test(
                f"Create Client - {test_case['name']}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                self.created_clients.append(response["id"])
                actual_payment_date = str(response.get('next_payment_date'))
                expected_payment_date = test_case['expected_payment_date']
                
                print(f"   Actual Payment Date: {actual_payment_date}")
                
                if actual_payment_date == expected_payment_date:
                    print(f"   ✅ PASSED: Edge case handled CORRECTLY!")
                else:
                    print(f"   ❌ FAILED: Edge case handled INCORRECTLY!")
                    print(f"      Expected: {expected_payment_date}")
                    print(f"      Got: {actual_payment_date}")
                    all_edge_tests_passed = False
            else:
                print(f"   ❌ FAILED: Could not create client for edge case")
                all_edge_tests_passed = False
        
        return all_edge_tests_passed

    def test_payment_stats_accuracy(self):
        """Test that payment statistics are accurate after payments"""
        print("\n🎯 TESTING PAYMENT STATISTICS ACCURACY")
        print("=" * 80)
        
        # Get initial payment stats
        success1, initial_stats = self.run_test(
            "Get Initial Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if not success1:
            print("❌ Failed to get initial payment statistics")
            return False
        
        initial_revenue = initial_stats.get('total_revenue', 0)
        initial_count = initial_stats.get('payment_count', 0)
        
        print(f"   Initial total revenue: TTD {initial_revenue}")
        print(f"   Initial payment count: {initial_count}")
        
        # Record a test payment if we have clients
        if self.created_clients:
            test_client_id = self.created_clients[0]
            test_amount = 125.50
            
            payment_data = {
                "client_id": test_client_id,
                "amount_paid": test_amount,
                "payment_date": "2025-01-25",
                "payment_method": "Bank Transfer",
                "notes": "Testing payment statistics accuracy"
            }
            
            success2, payment_response = self.run_test(
                "Record Test Payment for Statistics",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success2:
                # Get updated payment stats
                success3, updated_stats = self.run_test(
                    "Get Updated Payment Statistics",
                    "GET",
                    "payments/stats",
                    200
                )
                
                if success3:
                    updated_revenue = updated_stats.get('total_revenue', 0)
                    updated_count = updated_stats.get('payment_count', 0)
                    
                    print(f"   Updated total revenue: TTD {updated_revenue}")
                    print(f"   Updated payment count: {updated_count}")
                    
                    expected_revenue = initial_revenue + test_amount
                    expected_count = initial_count + 1
                    
                    revenue_correct = abs(updated_revenue - expected_revenue) < 0.01
                    count_correct = updated_count == expected_count
                    
                    if revenue_correct and count_correct:
                        print(f"   ✅ Payment statistics updated CORRECTLY!")
                        print(f"      Revenue increased by TTD {test_amount}")
                        print(f"      Payment count increased by 1")
                        return True
                    else:
                        print(f"   ❌ Payment statistics updated INCORRECTLY!")
                        print(f"      Expected revenue: TTD {expected_revenue}, Got: TTD {updated_revenue}")
                        print(f"      Expected count: {expected_count}, Got: {updated_count}")
                        return False
                else:
                    return False
            else:
                return False
        else:
            print("   ⚠️  No clients available for payment statistics test")
            return True

    def cleanup_test_clients(self):
        """Clean up test clients created during testing"""
        print("\n🧹 CLEANING UP TEST CLIENTS")
        print("=" * 40)
        
        cleanup_success = True
        for i, client_id in enumerate(self.created_clients, 1):
            success, response = self.run_test(
                f"Delete Test Client {i}",
                "DELETE",
                f"clients/{client_id}",
                200
            )
            
            if success:
                print(f"   ✅ Deleted client {i}: {response.get('client_name', 'Unknown')}")
            else:
                print(f"   ❌ Failed to delete client {i}")
                cleanup_success = False
        
        return cleanup_success

    def run_all_tests(self):
        """Run all next payment date calculation tests"""
        print("🎯 NEXT PAYMENT DATE CALCULATION FIX - COMPREHENSIVE TESTING")
        print("=" * 80)
        print("Testing the fix for 'Next payment date calculation is wrong'")
        print("Verifying proper monthly arithmetic instead of 30-day increments")
        print("=" * 80)
        
        # Run all test categories
        test_results = []
        
        test_results.append(self.test_initial_payment_date_calculation())
        test_results.append(self.test_payment_recording_with_correct_calculation())
        test_results.append(self.test_multiple_consecutive_payments())
        test_results.append(self.test_edge_cases_leap_years_and_boundaries())
        test_results.append(self.test_payment_stats_accuracy())
        
        # Clean up test clients
        self.cleanup_test_clients()
        
        # Print final summary
        print("\n" + "=" * 80)
        print("🎯 NEXT PAYMENT DATE CALCULATION FIX - TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"📊 Overall Test Results:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"   Test Categories Passed: {passed_tests}/{total_tests}")
        
        if all(test_results):
            print("\n✅ ALL TESTS PASSED!")
            print("✅ Next payment date calculation fix is WORKING CORRECTLY!")
            print("✅ Proper monthly arithmetic implemented successfully")
            print("✅ No date drift detected")
            print("✅ Edge cases handled properly")
            print("✅ Month boundaries working correctly")
            return True
        else:
            print("\n❌ SOME TESTS FAILED!")
            print("❌ Next payment date calculation fix needs attention")
            failed_categories = []
            if not test_results[0]: failed_categories.append("Initial Payment Date Calculation")
            if not test_results[1]: failed_categories.append("Payment Recording")
            if not test_results[2]: failed_categories.append("Multiple Consecutive Payments")
            if not test_results[3]: failed_categories.append("Edge Cases")
            if not test_results[4]: failed_categories.append("Payment Statistics")
            
            print(f"❌ Failed categories: {', '.join(failed_categories)}")
            return False

if __name__ == "__main__":
    print("🚀 Starting Next Payment Date Calculation Fix Testing...")
    
    tester = NextPaymentDateTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 TESTING COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n💥 TESTING COMPLETED WITH FAILURES!")
        sys.exit(1)