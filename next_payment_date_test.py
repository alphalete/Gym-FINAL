#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class NextPaymentDateTester:
    def __init__(self, base_url="https://442a58e4-b64f-4824-924a-0c12436c79ea.preview.emergentagent.com"):
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

    def test_initial_client_creation_dates(self):
        """Test 1: Initial Client Creation - Verify next_payment_date is calculated properly (one month ahead)"""
        print("\n🎯 TEST 1: INITIAL CLIENT CREATION - NEXT PAYMENT DATE CALCULATION")
        print("=" * 80)
        
        test_cases = [
            {
                "name": "Jan 15th Client",
                "start_date": "2025-01-15",
                "expected_next_payment": "2025-02-15",
                "description": "Standard monthly increment"
            },
            {
                "name": "Jan 31st Client", 
                "start_date": "2025-01-31",
                "expected_next_payment": "2025-02-28",
                "description": "Month boundary handling (Jan 31 -> Feb 28)"
            },
            {
                "name": "Feb 28th Client",
                "start_date": "2025-02-28", 
                "expected_next_payment": "2025-03-28",
                "description": "February to March"
            },
            {
                "name": "Dec 31st Client",
                "start_date": "2025-12-31",
                "expected_next_payment": "2026-01-31", 
                "description": "Year boundary"
            },
            {
                "name": "Mid-month Client",
                "start_date": "2025-06-15",
                "expected_next_payment": "2025-07-15",
                "description": "Standard mid-month case"
            }
        ]
        
        all_passed = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📅 Test Case {i}: {test_case['name']}")
            print(f"   Start Date: {test_case['start_date']}")
            print(f"   Expected Next Payment: {test_case['expected_next_payment']}")
            print(f"   Description: {test_case['description']}")
            
            client_data = {
                "name": f"Test Client {i} - {test_case['name']}",
                "email": f"test_client_{i}_{timestamp}@example.com",
                "phone": f"(555) {100+i:03d}-{1000+i:04d}",
                "membership_type": "Standard",
                "monthly_fee": 55.00,
                "start_date": test_case['start_date'],
                "payment_status": "due"  # Test with 'due' status to ensure proper calculation
            }
            
            success, response = self.run_test(
                f"Create {test_case['name']}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                self.created_clients.append(response["id"])
                actual_next_payment = str(response.get('next_payment_date'))
                expected_next_payment = test_case['expected_next_payment']
                
                print(f"   Actual Next Payment: {actual_next_payment}")
                
                if actual_next_payment == expected_next_payment:
                    print(f"   ✅ PASSED: Next payment date calculated correctly!")
                else:
                    print(f"   ❌ FAILED: Next payment date calculation incorrect!")
                    print(f"      Expected: {expected_next_payment}")
                    print(f"      Got: {actual_next_payment}")
                    all_passed = False
            else:
                print(f"   ❌ FAILED: Could not create client")
                all_passed = False
        
        return all_passed

    def test_payment_recording_monthly_cycles(self):
        """Test 2: Payment Recording - Verify monthly cycles continue properly"""
        print("\n🎯 TEST 2: PAYMENT RECORDING - MONTHLY CYCLE CONTINUATION")
        print("=" * 80)
        
        if not self.created_clients:
            print("❌ No clients available for payment testing")
            return False
        
        # Use the first created client for payment testing
        test_client_id = self.created_clients[0]
        
        # Get client details first
        success, client_response = self.run_test(
            "Get Client for Payment Testing",
            "GET",
            f"clients/{test_client_id}",
            200
        )
        
        if not success:
            print("❌ Could not retrieve client for payment testing")
            return False
        
        client_name = client_response.get('name')
        initial_next_payment = client_response.get('next_payment_date')
        print(f"   Client: {client_name}")
        print(f"   Initial Next Payment Date: {initial_next_payment}")
        
        # Record multiple payments to test monthly cycle continuation
        payment_tests = [
            {
                "payment_date": "2025-02-15",
                "expected_next_payment": "2025-03-15",
                "description": "First payment - Feb 15 -> Mar 15"
            },
            {
                "payment_date": "2025-03-15", 
                "expected_next_payment": "2025-04-15",
                "description": "Second payment - Mar 15 -> Apr 15"
            },
            {
                "payment_date": "2025-04-15",
                "expected_next_payment": "2025-05-15", 
                "description": "Third payment - Apr 15 -> May 15"
            },
            {
                "payment_date": "2025-05-15",
                "expected_next_payment": "2025-06-15",
                "description": "Fourth payment - May 15 -> Jun 15"
            }
        ]
        
        all_passed = True
        
        for i, payment_test in enumerate(payment_tests, 1):
            print(f"\n💰 Payment {i}: {payment_test['description']}")
            
            payment_data = {
                "client_id": test_client_id,
                "amount_paid": 55.00,
                "payment_date": payment_test['payment_date'],
                "payment_method": "Credit Card",
                "notes": f"Test payment {i} for monthly cycle verification"
            }
            
            success, response = self.run_test(
                f"Record Payment {i}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                actual_next_payment = response.get('new_next_payment_date')
                expected_next_payment = payment_test['expected_next_payment']
                
                print(f"   Payment Date: {payment_test['payment_date']}")
                print(f"   Expected Next Payment: {expected_next_payment}")
                print(f"   Actual Next Payment: {actual_next_payment}")
                
                # Convert date format for comparison (API returns "February 15, 2025" format)
                if actual_next_payment:
                    try:
                        # Parse the returned date format and convert to YYYY-MM-DD
                        parsed_date = datetime.strptime(actual_next_payment, "%B %d, %Y")
                        actual_date_str = parsed_date.strftime("%Y-%m-%d")
                        
                        if actual_date_str == expected_next_payment:
                            print(f"   ✅ PASSED: Monthly cycle continues correctly!")
                        else:
                            print(f"   ❌ FAILED: Monthly cycle broken!")
                            print(f"      Expected: {expected_next_payment}")
                            print(f"      Got: {actual_date_str}")
                            all_passed = False
                    except ValueError as e:
                        print(f"   ❌ FAILED: Could not parse date format: {e}")
                        all_passed = False
                else:
                    print(f"   ❌ FAILED: No next payment date returned")
                    all_passed = False
            else:
                print(f"   ❌ FAILED: Could not record payment {i}")
                all_passed = False
        
        return all_passed

    def test_edge_cases_and_boundaries(self):
        """Test 3: Edge Cases - Month boundaries, leap years, year boundaries"""
        print("\n🎯 TEST 3: EDGE CASES - BOUNDARIES AND SPECIAL DATES")
        print("=" * 80)
        
        edge_test_cases = [
            {
                "name": "Leap Year Feb 29th",
                "start_date": "2024-02-29",  # 2024 is a leap year
                "expected_next_payment": "2024-03-29",
                "description": "Leap year February 29th"
            },
            {
                "name": "Non-Leap Year Feb 28th",
                "start_date": "2025-02-28",  # 2025 is not a leap year
                "expected_next_payment": "2025-03-28",
                "description": "Non-leap year February 28th"
            },
            {
                "name": "April 30th (30-day month)",
                "start_date": "2025-04-30",
                "expected_next_payment": "2025-05-30",
                "description": "30-day month boundary"
            },
            {
                "name": "May 31st to June 30th",
                "start_date": "2025-05-31",
                "expected_next_payment": "2025-06-30",
                "description": "31-day to 30-day month"
            },
            {
                "name": "Year Boundary Dec 15th",
                "start_date": "2025-12-15",
                "expected_next_payment": "2026-01-15",
                "description": "Year boundary crossing"
            }
        ]
        
        all_passed = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, test_case in enumerate(edge_test_cases, 1):
            print(f"\n🔄 Edge Case {i}: {test_case['name']}")
            print(f"   Start Date: {test_case['start_date']}")
            print(f"   Expected Next Payment: {test_case['expected_next_payment']}")
            print(f"   Description: {test_case['description']}")
            
            client_data = {
                "name": f"Edge Test {i} - {test_case['name']}",
                "email": f"edge_test_{i}_{timestamp}@example.com",
                "phone": f"(555) {200+i:03d}-{2000+i:04d}",
                "membership_type": "Premium",
                "monthly_fee": 75.00,
                "start_date": test_case['start_date']
            }
            
            success, response = self.run_test(
                f"Create Edge Case Client - {test_case['name']}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                self.created_clients.append(response["id"])
                actual_next_payment = str(response.get('next_payment_date'))
                expected_next_payment = test_case['expected_next_payment']
                
                print(f"   Actual Next Payment: {actual_next_payment}")
                
                if actual_next_payment == expected_next_payment:
                    print(f"   ✅ PASSED: Edge case handled correctly!")
                else:
                    print(f"   ❌ FAILED: Edge case not handled correctly!")
                    print(f"      Expected: {expected_next_payment}")
                    print(f"      Got: {actual_next_payment}")
                    all_passed = False
            else:
                print(f"   ❌ FAILED: Could not create edge case client")
                all_passed = False
        
        return all_passed

    def test_multiple_consecutive_payments(self):
        """Test 4: Multiple Payments - Test consecutive payments to ensure no date drift"""
        print("\n🎯 TEST 4: MULTIPLE CONSECUTIVE PAYMENTS - NO DATE DRIFT")
        print("=" * 80)
        
        # Create a new client specifically for this test
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Multiple Payments Test Client",
            "email": f"multiple_payments_{timestamp}@example.com",
            "phone": "(555) 999-8888",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": "2025-01-15"
        }
        
        success, response = self.run_test(
            "Create Client for Multiple Payments Test",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success or "id" not in response:
            print("❌ Could not create client for multiple payments test")
            return False
        
        test_client_id = response["id"]
        self.created_clients.append(test_client_id)
        initial_next_payment = response.get('next_payment_date')
        
        print(f"   Created Client ID: {test_client_id}")
        print(f"   Initial Next Payment Date: {initial_next_payment}")
        
        # Expected payment sequence (should maintain 15th of each month)
        expected_sequence = [
            ("2025-02-15", "2025-03-15"),  # Payment 1: Feb 15 -> Mar 15
            ("2025-03-15", "2025-04-15"),  # Payment 2: Mar 15 -> Apr 15
            ("2025-04-15", "2025-05-15"),  # Payment 3: Apr 15 -> May 15
            ("2025-05-15", "2025-06-15"),  # Payment 4: May 15 -> Jun 15
            ("2025-06-15", "2025-07-15"),  # Payment 5: Jun 15 -> Jul 15
            ("2025-07-15", "2025-08-15"),  # Payment 6: Jul 15 -> Aug 15
        ]
        
        all_passed = True
        
        for i, (payment_date, expected_next) in enumerate(expected_sequence, 1):
            print(f"\n💰 Consecutive Payment {i}")
            print(f"   Payment Date: {payment_date}")
            print(f"   Expected Next Payment: {expected_next}")
            
            payment_data = {
                "client_id": test_client_id,
                "amount_paid": 100.00,
                "payment_date": payment_date,
                "payment_method": "Bank Transfer",
                "notes": f"Consecutive payment {i} - testing for date drift"
            }
            
            success, response = self.run_test(
                f"Record Consecutive Payment {i}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                actual_next_payment = response.get('new_next_payment_date')
                
                if actual_next_payment:
                    try:
                        # Parse the returned date format and convert to YYYY-MM-DD
                        parsed_date = datetime.strptime(actual_next_payment, "%B %d, %Y")
                        actual_date_str = parsed_date.strftime("%Y-%m-%d")
                        
                        print(f"   Actual Next Payment: {actual_next_payment} ({actual_date_str})")
                        
                        if actual_date_str == expected_next:
                            print(f"   ✅ PASSED: No date drift detected!")
                        else:
                            print(f"   ❌ FAILED: Date drift detected!")
                            print(f"      Expected: {expected_next}")
                            print(f"      Got: {actual_date_str}")
                            all_passed = False
                    except ValueError as e:
                        print(f"   ❌ FAILED: Could not parse date format: {e}")
                        all_passed = False
                else:
                    print(f"   ❌ FAILED: No next payment date returned")
                    all_passed = False
            else:
                print(f"   ❌ FAILED: Could not record consecutive payment {i}")
                all_passed = False
        
        return all_passed

    def test_payment_status_scenarios(self):
        """Test 5: Payment Status Scenarios - Test both 'paid' and 'due' status on creation"""
        print("\n🎯 TEST 5: PAYMENT STATUS SCENARIOS - 'PAID' VS 'DUE' STATUS")
        print("=" * 80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Test Case 1: Client with payment_status = 'due' (should calculate next payment date)
        print("\n📋 Test Case 1: Client with payment_status = 'due'")
        client_due_data = {
            "name": "Client Due Status Test",
            "email": f"client_due_{timestamp}@example.com",
            "phone": "(555) 111-1111",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": "2025-01-20",
            "payment_status": "due"
        }
        
        success1, response1 = self.run_test(
            "Create Client with 'due' Status",
            "POST",
            "clients",
            200,
            client_due_data
        )
        
        due_test_passed = False
        if success1 and "id" in response1:
            self.created_clients.append(response1["id"])
            actual_next_payment = str(response1.get('next_payment_date'))
            expected_next_payment = "2025-02-20"  # Should be one month ahead
            
            print(f"   Start Date: 2025-01-20")
            print(f"   Payment Status: due")
            print(f"   Expected Next Payment: {expected_next_payment}")
            print(f"   Actual Next Payment: {actual_next_payment}")
            
            if actual_next_payment == expected_next_payment:
                print(f"   ✅ PASSED: 'due' status calculates next payment date correctly!")
                due_test_passed = True
            else:
                print(f"   ❌ FAILED: 'due' status calculation incorrect!")
        
        # Test Case 2: Client with payment_status = 'paid' (should still calculate next payment date)
        print("\n📋 Test Case 2: Client with payment_status = 'paid'")
        client_paid_data = {
            "name": "Client Paid Status Test",
            "email": f"client_paid_{timestamp}@example.com",
            "phone": "(555) 222-2222",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-01-25",
            "payment_status": "paid"
        }
        
        success2, response2 = self.run_test(
            "Create Client with 'paid' Status",
            "POST",
            "clients",
            200,
            client_paid_data
        )
        
        paid_test_passed = False
        if success2 and "id" in response2:
            self.created_clients.append(response2["id"])
            actual_next_payment = str(response2.get('next_payment_date'))
            expected_next_payment = "2025-02-25"  # Should be one month ahead
            
            print(f"   Start Date: 2025-01-25")
            print(f"   Payment Status: paid")
            print(f"   Expected Next Payment: {expected_next_payment}")
            print(f"   Actual Next Payment: {actual_next_payment}")
            
            if actual_next_payment == expected_next_payment:
                print(f"   ✅ PASSED: 'paid' status calculates next payment date correctly!")
                paid_test_passed = True
            else:
                print(f"   ❌ FAILED: 'paid' status calculation incorrect!")
        
        return due_test_passed and paid_test_passed

    def cleanup_test_clients(self):
        """Clean up created test clients"""
        print("\n🧹 CLEANING UP TEST CLIENTS")
        print("=" * 40)
        
        cleanup_success = True
        for client_id in self.created_clients:
            success, response = self.run_test(
                f"Delete Test Client {client_id[:8]}...",
                "DELETE",
                f"clients/{client_id}",
                200
            )
            if not success:
                cleanup_success = False
        
        return cleanup_success

    def run_all_tests(self):
        """Run all next payment date calculation tests"""
        print("🎯 NEXT PAYMENT DATE CALCULATION FIX - COMPREHENSIVE TESTING")
        print("=" * 80)
        print("Testing the complete fix for next payment date calculation issues")
        print("Focus: Initial client creation and payment recording monthly cycles")
        print("=" * 80)
        
        # Run all test suites
        test_results = []
        
        print("\n" + "="*80)
        test_results.append(("Initial Client Creation", self.test_initial_client_creation_dates()))
        
        print("\n" + "="*80)
        test_results.append(("Payment Recording Cycles", self.test_payment_recording_monthly_cycles()))
        
        print("\n" + "="*80)
        test_results.append(("Edge Cases & Boundaries", self.test_edge_cases_and_boundaries()))
        
        print("\n" + "="*80)
        test_results.append(("Multiple Consecutive Payments", self.test_multiple_consecutive_payments()))
        
        print("\n" + "="*80)
        test_results.append(("Payment Status Scenarios", self.test_payment_status_scenarios()))
        
        # Clean up test data
        print("\n" + "="*80)
        cleanup_success = self.cleanup_test_clients()
        
        # Final Results Summary
        print("\n" + "="*80)
        print("🎯 FINAL TEST RESULTS SUMMARY")
        print("=" * 80)
        
        all_passed = True
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}: {test_name}")
            if not result:
                all_passed = False
        
        print(f"\nCleanup: {'✅ SUCCESS' if cleanup_success else '❌ FAILED'}")
        print(f"\nTotal Tests Run: {self.tests_run}")
        print(f"Total Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! Next payment date calculation fix is working correctly!")
            print("✅ Initial client creation calculates next payment date properly")
            print("✅ Payment recording maintains proper monthly cycles")
            print("✅ Edge cases and boundaries handled correctly")
            print("✅ No date drift detected in consecutive payments")
            print("✅ Both 'paid' and 'due' status scenarios work correctly")
        else:
            print("\n❌ SOME TESTS FAILED! Next payment date calculation needs attention!")
            
        return all_passed

if __name__ == "__main__":
    tester = NextPaymentDateTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)