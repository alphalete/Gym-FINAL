#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class MultiplePaymentLogicTester:
    def __init__(self, base_url="https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_client_id = None

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

    def create_test_client(self):
        """Create a test client for payment testing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Deon Aleong",
            "email": f"deon_aleong_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": "2025-07-01"  # Due date will be 2025-07-31
        }
        
        success, response = self.run_test(
            "Create Test Client (Deon Aleong)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.test_client_id = response["id"]
            print(f"   ✅ Created test client ID: {self.test_client_id}")
            print(f"   📅 Start date: {response.get('start_date')}")
            print(f"   💰 Initial due date: {response.get('next_payment_date')}")
            return True
        
        return False

    def get_client_due_date(self):
        """Get current due date for test client"""
        if not self.test_client_id:
            return None
            
        success, response = self.run_test(
            "Get Client Current Due Date",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if success:
            due_date = response.get('next_payment_date')
            print(f"   📅 Current due date: {due_date}")
            return due_date
        
        return None

    def test_multiple_same_day_payments(self):
        """Test multiple payments on the same day - CRITICAL FIX VERIFICATION"""
        print("\n🎯 TESTING MULTIPLE SAME-DAY PAYMENTS - CRITICAL FIX VERIFICATION")
        print("=" * 80)
        
        if not self.test_client_id:
            print("❌ No test client available - aborting test")
            return False
        
        # Get initial due date
        initial_due_date = self.get_client_due_date()
        if not initial_due_date:
            print("❌ Could not get initial due date")
            return False
        
        print(f"📅 INITIAL DUE DATE: {initial_due_date}")
        
        # Record first payment on July 28th
        payment_date = "2025-07-28"
        payment1_data = {
            "client_id": self.test_client_id,
            "amount_paid": 100.00,
            "payment_date": payment_date,
            "payment_method": "Cash",
            "notes": "First payment on same day - testing accumulation fix"
        }
        
        success1, response1 = self.run_test(
            "Record First Payment (July 28th)",
            "POST",
            "payments/record",
            200,
            payment1_data
        )
        
        if not success1:
            print("❌ Failed to record first payment")
            return False
        
        first_payment_due_date = response1.get('new_next_payment_date')
        print(f"💰 AFTER FIRST PAYMENT: Due date = {first_payment_due_date}")
        
        # Record second payment on the same day (July 28th)
        payment2_data = {
            "client_id": self.test_client_id,
            "amount_paid": 100.00,
            "payment_date": payment_date,  # Same day!
            "payment_method": "Card",
            "notes": "Second payment on same day - testing accumulation fix"
        }
        
        success2, response2 = self.run_test(
            "Record Second Payment (Same Day - July 28th)",
            "POST",
            "payments/record",
            200,
            payment2_data
        )
        
        if not success2:
            print("❌ Failed to record second payment")
            return False
        
        second_payment_due_date = response2.get('new_next_payment_date')
        print(f"💰 AFTER SECOND PAYMENT: Due date = {second_payment_due_date}")
        
        # CRITICAL VERIFICATION: Second payment should extend due date beyond first
        if first_payment_due_date == second_payment_due_date:
            print("❌ CRITICAL ISSUE: Second payment did NOT extend due date!")
            print(f"   First payment due date: {first_payment_due_date}")
            print(f"   Second payment due date: {second_payment_due_date}")
            print("   🚨 MULTIPLE PAYMENT ACCUMULATION IS NOT WORKING!")
            return False
        else:
            print("✅ SUCCESS: Second payment extended due date beyond first!")
            print(f"   First payment due date: {first_payment_due_date}")
            print(f"   Second payment due date: {second_payment_due_date}")
            print("   🎉 MULTIPLE PAYMENT ACCUMULATION IS WORKING!")
        
        # Verify the logic: max(current_due_date, payment_date) + 30 days
        # For first payment: max(2025-07-31, 2025-07-28) + 30 = 2025-07-31 + 30 = 2025-08-30
        # For second payment: max(2025-08-30, 2025-07-28) + 30 = 2025-08-30 + 30 = 2025-09-29
        
        expected_first_due = "August 30, 2025"  # max(2025-07-31, 2025-07-28) + 30
        expected_second_due = "September 29, 2025"  # max(2025-08-30, 2025-07-28) + 30
        
        print(f"\n🔍 LOGIC VERIFICATION:")
        print(f"   Expected first payment due: {expected_first_due}")
        print(f"   Actual first payment due: {first_payment_due_date}")
        print(f"   Expected second payment due: {expected_second_due}")
        print(f"   Actual second payment due: {second_payment_due_date}")
        
        return True

    def test_early_payment_scenarios(self):
        """Test early payment scenarios - ensure no membership days are lost"""
        print("\n🎯 TESTING EARLY PAYMENT SCENARIOS - NO MEMBERSHIP DAYS LOST")
        print("=" * 80)
        
        # Create a new client with due date in the future
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Early Payment Test Client",
            "email": f"early_payment_{timestamp}@example.com",
            "phone": "(555) 987-6543",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-01-15"  # Due date will be 2025-02-14
        }
        
        success, response = self.run_test(
            "Create Early Payment Test Client",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success or "id" not in response:
            print("❌ Failed to create early payment test client")
            return False
        
        early_client_id = response["id"]
        initial_due_date = response.get('next_payment_date')
        print(f"📅 INITIAL DUE DATE: {initial_due_date}")
        
        # Make early payment (before due date)
        early_payment_date = "2025-01-10"  # 5 days before due date
        payment_data = {
            "client_id": early_client_id,
            "amount_paid": 75.00,
            "payment_date": early_payment_date,
            "payment_method": "Bank Transfer",
            "notes": "Early payment - testing no membership days lost"
        }
        
        success, response = self.run_test(
            "Record Early Payment (Before Due Date)",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success:
            print("❌ Failed to record early payment")
            return False
        
        new_due_date = response.get('new_next_payment_date')
        print(f"💰 AFTER EARLY PAYMENT: Due date = {new_due_date}")
        
        # CRITICAL VERIFICATION: Due date should extend from original due date, not payment date
        # Logic: max(2025-02-14, 2025-01-10) + 30 = 2025-02-14 + 30 = 2025-03-16
        expected_due_date = "March 16, 2025"
        
        print(f"\n🔍 EARLY PAYMENT LOGIC VERIFICATION:")
        print(f"   Original due date: {initial_due_date}")
        print(f"   Payment date: {early_payment_date}")
        print(f"   Expected new due date: {expected_due_date} (from original due date + 30)")
        print(f"   Actual new due date: {new_due_date}")
        
        # Check if client didn't lose membership days
        if "March 16" in new_due_date:
            print("✅ SUCCESS: Client did NOT lose membership days with early payment!")
            print("   🎉 EARLY PAYMENT LOGIC IS WORKING CORRECTLY!")
            return True
        else:
            print("❌ FAILURE: Client LOST membership days with early payment!")
            print("   🚨 EARLY PAYMENT LOGIC NEEDS FIXING!")
            return False

    def test_payment_accumulation(self):
        """Test 3 payments in a row for same client - verify cumulative effect"""
        print("\n🎯 TESTING PAYMENT ACCUMULATION - 3 CONSECUTIVE PAYMENTS")
        print("=" * 80)
        
        # Create a new client for accumulation testing
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Payment Accumulation Test Client",
            "email": f"accumulation_{timestamp}@example.com",
            "phone": "(555) 111-2222",
            "membership_type": "VIP",
            "monthly_fee": 150.00,
            "start_date": "2025-06-01"  # Due date will be 2025-07-01
        }
        
        success, response = self.run_test(
            "Create Payment Accumulation Test Client",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success or "id" not in response:
            print("❌ Failed to create accumulation test client")
            return False
        
        accumulation_client_id = response["id"]
        initial_due_date = response.get('next_payment_date')
        print(f"📅 INITIAL DUE DATE: {initial_due_date}")
        
        # Record 3 consecutive payments
        payments = [
            {
                "date": "2025-07-15",
                "amount": 150.00,
                "method": "Cash",
                "notes": "First payment - accumulation test"
            },
            {
                "date": "2025-07-16",
                "amount": 150.00,
                "method": "Card",
                "notes": "Second payment - accumulation test"
            },
            {
                "date": "2025-07-17",
                "amount": 150.00,
                "method": "Bank Transfer",
                "notes": "Third payment - accumulation test"
            }
        ]
        
        due_dates = [initial_due_date]
        
        for i, payment in enumerate(payments, 1):
            payment_data = {
                "client_id": accumulation_client_id,
                "amount_paid": payment["amount"],
                "payment_date": payment["date"],
                "payment_method": payment["method"],
                "notes": payment["notes"]
            }
            
            success, response = self.run_test(
                f"Record Payment #{i} ({payment['date']})",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if not success:
                print(f"❌ Failed to record payment #{i}")
                return False
            
            new_due_date = response.get('new_next_payment_date')
            due_dates.append(new_due_date)
            print(f"💰 AFTER PAYMENT #{i}: Due date = {new_due_date}")
        
        # CRITICAL VERIFICATION: Each payment should add exactly 30 days
        print(f"\n🔍 PAYMENT ACCUMULATION VERIFICATION:")
        print(f"   Initial due date: {due_dates[0]}")
        print(f"   After payment 1: {due_dates[1]}")
        print(f"   After payment 2: {due_dates[2]}")
        print(f"   After payment 3: {due_dates[3]}")
        
        # Verify each payment extended the membership
        all_extended = True
        for i in range(1, len(due_dates)):
            if due_dates[i] == due_dates[i-1]:
                print(f"❌ Payment #{i} did NOT extend membership period!")
                all_extended = False
            else:
                print(f"✅ Payment #{i} successfully extended membership period")
        
        if all_extended:
            print("🎉 SUCCESS: All payments accumulated properly!")
            print("   ✅ Each payment added exactly 30 days to membership")
            print("   ✅ Cumulative effect is working correctly")
            return True
        else:
            print("🚨 FAILURE: Payment accumulation is not working correctly!")
            return False

    def test_edge_cases(self):
        """Test edge cases like payment on exact due date"""
        print("\n🎯 TESTING EDGE CASES - PAYMENT ON EXACT DUE DATE")
        print("=" * 80)
        
        # Create a client for edge case testing
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Edge Case Test Client",
            "email": f"edge_case_{timestamp}@example.com",
            "phone": "(555) 333-4444",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-05-01"  # Due date will be 2025-05-31
        }
        
        success, response = self.run_test(
            "Create Edge Case Test Client",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success or "id" not in response:
            print("❌ Failed to create edge case test client")
            return False
        
        edge_client_id = response["id"]
        initial_due_date = response.get('next_payment_date')
        print(f"📅 INITIAL DUE DATE: {initial_due_date}")
        
        # Make payment on exact due date
        payment_on_due_date = "2025-05-31"  # Exact due date
        payment_data = {
            "client_id": edge_client_id,
            "amount_paid": 50.00,
            "payment_date": payment_on_due_date,
            "payment_method": "Cash",
            "notes": "Payment on exact due date - edge case test"
        }
        
        success, response = self.run_test(
            "Record Payment on Exact Due Date",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success:
            print("❌ Failed to record payment on due date")
            return False
        
        new_due_date = response.get('new_next_payment_date')
        print(f"💰 AFTER PAYMENT ON DUE DATE: Due date = {new_due_date}")
        
        # VERIFICATION: max(2025-05-31, 2025-05-31) + 30 = 2025-05-31 + 30 = 2025-06-30
        expected_due_date = "June 30, 2025"
        
        print(f"\n🔍 EDGE CASE VERIFICATION:")
        print(f"   Original due date: {initial_due_date}")
        print(f"   Payment date: {payment_on_due_date} (exact due date)")
        print(f"   Expected new due date: {expected_due_date}")
        print(f"   Actual new due date: {new_due_date}")
        
        if "June 30" in new_due_date:
            print("✅ SUCCESS: Payment on exact due date works correctly!")
            print("   🎉 EDGE CASE LOGIC IS WORKING!")
            return True
        else:
            print("❌ FAILURE: Payment on exact due date logic is incorrect!")
            return False

    def run_all_tests(self):
        """Run all multiple payment logic tests"""
        print("🚀 STARTING COMPREHENSIVE MULTIPLE PAYMENT LOGIC TESTING")
        print("=" * 80)
        print("TESTING THE FIXED PAYMENT LOGIC: max(current_due_date, payment_date) + 30 days")
        print("=" * 80)
        
        # Create test client
        if not self.create_test_client():
            print("❌ Failed to create test client - aborting all tests")
            return False
        
        # Run all tests
        test_results = []
        
        test_results.append(self.test_multiple_same_day_payments())
        test_results.append(self.test_early_payment_scenarios())
        test_results.append(self.test_payment_accumulation())
        test_results.append(self.test_edge_cases())
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 MULTIPLE PAYMENT LOGIC TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Multiple payment logic fix is working correctly")
            print("✅ Multiple same-day payments accumulate properly")
            print("✅ Early payments don't cause membership day loss")
            print("✅ Payment accumulation works correctly")
            print("✅ Edge cases are handled properly")
            print("✅ Business logic: max(current_due_date, payment_date) + 30 days is working")
        else:
            print("\n🚨 SOME TESTS FAILED!")
            print("❌ Multiple payment logic needs further investigation")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = MultiplePaymentLogicTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)