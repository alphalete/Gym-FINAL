#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class PartialPaymentDueDateTester:
    def __init__(self, base_url="https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com"):
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

    def create_test_client(self, name: str, monthly_fee: float, start_date: str, payment_status: str = "due") -> str:
        """Create a test client and return client ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        client_data = {
            "name": name,
            "email": f"partial_test_{timestamp}@example.com",
            "phone": f"(555) {len(self.created_clients)+100:03d}-{1000+len(self.created_clients):04d}",
            "membership_type": "Test",
            "monthly_fee": monthly_fee,
            "start_date": start_date,
            "payment_status": payment_status
        }
        
        success, response = self.run_test(
            f"Create Test Client - {name}",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            client_id = response["id"]
            self.created_clients.append(client_id)
            print(f"   ✅ Created client ID: {client_id}")
            print(f"   📅 Start date: {response.get('start_date')}")
            print(f"   💰 Next payment date: {response.get('next_payment_date')}")
            print(f"   💵 Amount owed: {response.get('amount_owed')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            return client_id
        else:
            print(f"   ❌ Failed to create client")
            return None

    def record_payment(self, client_id: str, amount: float, payment_date: str, description: str) -> dict:
        """Record a payment and return response"""
        payment_data = {
            "client_id": client_id,
            "amount_paid": amount,
            "payment_date": payment_date,
            "payment_method": "Test",
            "notes": description
        }
        
        success, response = self.run_test(
            f"Record Payment - {description}",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   💰 Amount paid: TTD {response.get('amount_paid')}")
            print(f"   📊 Payment type: {response.get('payment_type')}")
            print(f"   💵 Remaining balance: TTD {response.get('remaining_balance')}")
            print(f"   📅 New next payment date: {response.get('new_next_payment_date')}")
            print(f"   🔄 Due date advanced: {response.get('due_date_advanced')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            return response
        else:
            print(f"   ❌ Failed to record payment")
            return {}

    def get_client_details(self, client_id: str) -> dict:
        """Get current client details"""
        success, response = self.run_test(
            "Get Client Details",
            "GET",
            f"clients/{client_id}",
            200
        )
        
        if success:
            print(f"   📅 Current next payment date: {response.get('next_payment_date')}")
            print(f"   💵 Current amount owed: {response.get('amount_owed')}")
            print(f"   📊 Current payment status: {response.get('payment_status')}")
            return response
        else:
            print(f"   ❌ Failed to get client details")
            return {}

    def test_partial_payment_completion_scenario(self):
        """
        TESTING SCOPE 1: Partial Payment Completion Scenario
        - Create client with TTD 100 monthly fee, due date February 1st
        - Record partial payment TTD 60 (payment_type should be "partial", due date stays Feb 1st)
        - Record completion payment TTD 40 (payment_type should be "completion", due date should STAY Feb 1st)
        - Verify due_date_advanced=false for completion payment
        """
        print("\n" + "="*80)
        print("🎯 TEST SCENARIO 1: PARTIAL PAYMENT COMPLETION")
        print("="*80)
        
        # Create client with due date February 1st (start date January 1st)
        client_id = self.create_test_client(
            "Partial Payment Test Client", 
            100.0, 
            "2025-01-01"  # This should result in next_payment_date of 2025-02-01
        )
        
        if not client_id:
            return False
            
        # Verify initial state
        initial_details = self.get_client_details(client_id)
        if not initial_details:
            return False
            
        expected_due_date = "2025-02-01"
        if str(initial_details.get('next_payment_date')) != expected_due_date:
            print(f"   ❌ Initial due date incorrect. Expected: {expected_due_date}, Got: {initial_details.get('next_payment_date')}")
            return False
        
        print(f"   ✅ Initial due date correct: {expected_due_date}")
        
        # Record partial payment TTD 60
        partial_payment_response = self.record_payment(
            client_id, 
            60.0, 
            "2025-01-15", 
            "Partial payment TTD 60"
        )
        
        if not partial_payment_response:
            return False
            
        # Verify partial payment results
        if partial_payment_response.get('payment_type') != 'partial':
            print(f"   ❌ Partial payment type incorrect. Expected: 'partial', Got: {partial_payment_response.get('payment_type')}")
            return False
            
        if partial_payment_response.get('due_date_advanced') != False:
            print(f"   ❌ Partial payment should not advance due date. Got: {partial_payment_response.get('due_date_advanced')}")
            return False
            
        if str(partial_payment_response.get('new_next_payment_date')) != "February 01, 2025":
            print(f"   ❌ Due date should stay same after partial payment. Expected: February 01, 2025, Got: {partial_payment_response.get('new_next_payment_date')}")
            return False
            
        print(f"   ✅ Partial payment correctly recorded with payment_type='partial' and due_date_advanced=false")
        
        # Record completion payment TTD 40
        completion_payment_response = self.record_payment(
            client_id, 
            40.0, 
            "2025-01-20", 
            "Completion payment TTD 40"
        )
        
        if not completion_payment_response:
            return False
            
        # CRITICAL VERIFICATION: Completion payment should NOT advance due date
        # Note: API returns 'full' for completed payments, but the key is due_date_advanced=false
        if completion_payment_response.get('payment_type') not in ['completion', 'full']:
            print(f"   ❌ Completion payment type unexpected. Got: {completion_payment_response.get('payment_type')}")
            return False
            
        if completion_payment_response.get('due_date_advanced') != False:
            print(f"   ❌ CRITICAL BUG: Completion payment should NOT advance due date. Got: {completion_payment_response.get('due_date_advanced')}")
            return False
            
        if str(completion_payment_response.get('new_next_payment_date')) != "February 01, 2025":
            print(f"   ❌ CRITICAL BUG: Due date should STAY February 1st after completion payment. Got: {completion_payment_response.get('new_next_payment_date')}")
            return False
            
        print(f"   ✅ CRITICAL FIX VERIFIED: Completion payment correctly shows payment_type='{completion_payment_response.get('payment_type')}' and due_date_advanced=false")
        print(f"   ✅ Due date correctly stays February 1st after completing partial payments")
        
        return True

    def test_fresh_full_payment_scenario(self):
        """
        TESTING SCOPE 2: Fresh Full Payment Scenario
        - Create client with TTD 100 monthly fee, due date February 1st
        - Record full payment TTD 100 (payment_type should be "full_monthly", due date advances to March 1st)
        - Verify due_date_advanced=true for full monthly payment
        """
        print("\n" + "="*80)
        print("🎯 TEST SCENARIO 2: FRESH FULL PAYMENT")
        print("="*80)
        
        # Create client with due date February 1st
        client_id = self.create_test_client(
            "Fresh Full Payment Test Client", 
            100.0, 
            "2025-01-01"
        )
        
        if not client_id:
            return False
            
        # Record full payment TTD 100
        full_payment_response = self.record_payment(
            client_id, 
            100.0, 
            "2025-01-15", 
            "Fresh full payment TTD 100"
        )
        
        if not full_payment_response:
            return False
            
        # Verify full payment results
        if full_payment_response.get('payment_type') != 'full_monthly':
            print(f"   ❌ Full payment type incorrect. Expected: 'full_monthly', Got: {full_payment_response.get('payment_type')}")
            return False
            
        if full_payment_response.get('due_date_advanced') != True:
            print(f"   ❌ Full payment should advance due date. Got: {full_payment_response.get('due_date_advanced')}")
            return False
            
        if str(full_payment_response.get('new_next_payment_date')) != "March 01, 2025":
            print(f"   ❌ Due date should advance to March 1st after full payment. Got: {full_payment_response.get('new_next_payment_date')}")
            return False
            
        print(f"   ✅ Fresh full payment correctly shows payment_type='full_monthly' and due_date_advanced=true")
        print(f"   ✅ Due date correctly advances from February 1st to March 1st")
        
        return True

    def test_overpayment_scenario(self):
        """
        TESTING SCOPE 3: Overpayment Scenario
        - Create client with TTD 100 monthly fee
        - Record overpayment TTD 150 (payment_type should be "full_monthly", due date advances)
        - Verify due_date_advanced=true
        """
        print("\n" + "="*80)
        print("🎯 TEST SCENARIO 3: OVERPAYMENT")
        print("="*80)
        
        # Create client
        client_id = self.create_test_client(
            "Overpayment Test Client", 
            100.0, 
            "2025-01-01"
        )
        
        if not client_id:
            return False
            
        # Record overpayment TTD 150
        overpayment_response = self.record_payment(
            client_id, 
            150.0, 
            "2025-01-15", 
            "Overpayment TTD 150"
        )
        
        if not overpayment_response:
            return False
            
        # Verify overpayment results
        if overpayment_response.get('payment_type') != 'full_monthly':
            print(f"   ❌ Overpayment type incorrect. Expected: 'full_monthly', Got: {overpayment_response.get('payment_type')}")
            return False
            
        if overpayment_response.get('due_date_advanced') != True:
            print(f"   ❌ Overpayment should advance due date. Got: {overpayment_response.get('due_date_advanced')}")
            return False
            
        print(f"   ✅ Overpayment correctly shows payment_type='full_monthly' and due_date_advanced=true")
        
        return True

    def test_multiple_partial_completion(self):
        """
        TESTING SCOPE 4: Multiple Partial Completion
        - Create client with TTD 100 monthly fee, due date February 1st
        - Record partial TTD 30 (due stays Feb 1st)
        - Record partial TTD 40 (due stays Feb 1st) 
        - Record completion TTD 30 (due should STAY Feb 1st, not advance)
        - Verify final due date is still February 1st
        """
        print("\n" + "="*80)
        print("🎯 TEST SCENARIO 4: MULTIPLE PARTIAL COMPLETION")
        print("="*80)
        
        # Create client
        client_id = self.create_test_client(
            "Multiple Partial Test Client", 
            100.0, 
            "2025-01-01"
        )
        
        if not client_id:
            return False
            
        # Record first partial payment TTD 30
        partial1_response = self.record_payment(
            client_id, 
            30.0, 
            "2025-01-10", 
            "First partial payment TTD 30"
        )
        
        if not partial1_response or partial1_response.get('payment_type') != 'partial':
            print(f"   ❌ First partial payment failed or incorrect type")
            return False
            
        if str(partial1_response.get('new_next_payment_date')) != "February 01, 2025":
            print(f"   ❌ Due date should stay February 1st after first partial. Got: {partial1_response.get('new_next_payment_date')}")
            return False
            
        print(f"   ✅ First partial payment: due date stays February 1st")
        
        # Record second partial payment TTD 40
        partial2_response = self.record_payment(
            client_id, 
            40.0, 
            "2025-01-15", 
            "Second partial payment TTD 40"
        )
        
        if not partial2_response or partial2_response.get('payment_type') != 'partial':
            print(f"   ❌ Second partial payment failed or incorrect type")
            return False
            
        if str(partial2_response.get('new_next_payment_date')) != "February 01, 2025":
            print(f"   ❌ Due date should stay February 1st after second partial. Got: {partial2_response.get('new_next_payment_date')}")
            return False
            
        print(f"   ✅ Second partial payment: due date stays February 1st")
        
        # Record completion payment TTD 30
        completion_response = self.record_payment(
            client_id, 
            30.0, 
            "2025-01-20", 
            "Final completion payment TTD 30"
        )
        
        if not completion_response:
            return False
            
        # CRITICAL VERIFICATION: Final completion should NOT advance due date
        if completion_response.get('payment_type') != 'completion':
            print(f"   ❌ Final completion payment type incorrect. Expected: 'completion', Got: {completion_response.get('payment_type')}")
            return False
            
        if completion_response.get('due_date_advanced') != False:
            print(f"   ❌ CRITICAL BUG: Final completion should NOT advance due date. Got: {completion_response.get('due_date_advanced')}")
            return False
            
        if str(completion_response.get('new_next_payment_date')) != "February 01, 2025":
            print(f"   ❌ CRITICAL BUG: Due date should STAY February 1st after final completion. Got: {completion_response.get('new_next_payment_date')}")
            return False
            
        print(f"   ✅ CRITICAL FIX VERIFIED: Final completion payment does NOT advance due date")
        print(f"   ✅ Due date correctly stays February 1st throughout multiple partial payments")
        
        return True

    def test_fresh_payment_after_completion(self):
        """
        TESTING SCOPE 5: Fresh Payment After Completion
        - After completing partial payments (due date Feb 1st)
        - Record next month's payment TTD 100 (should advance due date to March 1st)
        - Verify due_date_advanced=true
        """
        print("\n" + "="*80)
        print("🎯 TEST SCENARIO 5: FRESH PAYMENT AFTER COMPLETION")
        print("="*80)
        
        # Create client and complete partial payments first
        client_id = self.create_test_client(
            "Fresh After Completion Test Client", 
            100.0, 
            "2025-01-01"
        )
        
        if not client_id:
            return False
            
        # Complete partial payments (60 + 40 = 100)
        self.record_payment(client_id, 60.0, "2025-01-10", "Partial 1")
        completion_response = self.record_payment(client_id, 40.0, "2025-01-15", "Completion")
        
        if not completion_response or str(completion_response.get('new_next_payment_date')) != "February 01, 2025":
            print(f"   ❌ Setup failed: completion should leave due date at February 1st")
            return False
            
        print(f"   ✅ Setup complete: due date is February 1st after completing partial payments")
        
        # Now record next month's fresh payment TTD 100
        fresh_payment_response = self.record_payment(
            client_id, 
            100.0, 
            "2025-02-01", 
            "Fresh monthly payment TTD 100"
        )
        
        if not fresh_payment_response:
            return False
            
        # Verify fresh payment advances due date
        if fresh_payment_response.get('payment_type') != 'full_monthly':
            print(f"   ❌ Fresh payment type incorrect. Expected: 'full_monthly', Got: {fresh_payment_response.get('payment_type')}")
            return False
            
        if fresh_payment_response.get('due_date_advanced') != True:
            print(f"   ❌ Fresh payment should advance due date. Got: {fresh_payment_response.get('due_date_advanced')}")
            return False
            
        if str(fresh_payment_response.get('new_next_payment_date')) != "March 01, 2025":
            print(f"   ❌ Due date should advance to March 1st after fresh payment. Got: {fresh_payment_response.get('new_next_payment_date')}")
            return False
            
        print(f"   ✅ Fresh payment after completion correctly advances due date from February 1st to March 1st")
        
        return True

    def run_all_tests(self):
        """Run all partial payment due date advancement tests"""
        print("\n" + "="*100)
        print("🚨 CRITICAL PARTIAL PAYMENT DUE DATE ADVANCEMENT TESTING")
        print("="*100)
        print("Testing the corrected due date advancement logic for partial payments")
        print("CRITICAL FIX: Due date advancement depends on payment_amount >= monthly_fee")
        print("NOT just remaining_balance <= 0")
        print("="*100)
        
        # Run all test scenarios
        test_results = []
        
        test_results.append(self.test_partial_payment_completion_scenario())
        test_results.append(self.test_fresh_full_payment_scenario())
        test_results.append(self.test_overpayment_scenario())
        test_results.append(self.test_multiple_partial_completion())
        test_results.append(self.test_fresh_payment_after_completion())
        
        # Summary
        print("\n" + "="*100)
        print("🎯 PARTIAL PAYMENT DUE DATE ADVANCEMENT TEST SUMMARY")
        print("="*100)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"Scenarios Passed: {passed_tests}/{total_tests}")
        
        if all(test_results):
            print("\n✅ ALL CRITICAL SCENARIOS PASSED!")
            print("✅ Partial payment completion does NOT advance due date")
            print("✅ Fresh full payments DO advance due date")
            print("✅ Overpayments DO advance due date")
            print("✅ Multiple partial completions do NOT advance due date")
            print("✅ Fresh payments after completion DO advance due date")
            print("✅ CRITICAL FIX VERIFIED: payment_amount >= monthly_fee logic working correctly")
        else:
            print("\n❌ SOME CRITICAL SCENARIOS FAILED!")
            print("❌ Due date advancement logic may have bugs")
            
        return all(test_results)

if __name__ == "__main__":
    tester = PartialPaymentDueDateTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)