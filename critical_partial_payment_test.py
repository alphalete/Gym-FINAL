#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class CriticalPartialPaymentTester:
    def __init__(self, base_url="https://alphalete-club.emergent.host"):
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

    def create_test_client(self, name: str, monthly_fee: float, start_date: str) -> str:
        """Create a test client and return client ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        client_data = {
            "name": name,
            "email": f"critical_test_{timestamp}@example.com",
            "phone": f"(555) {len(self.created_clients)+200:03d}-{2000+len(self.created_clients):04d}",
            "membership_type": "Test",
            "monthly_fee": monthly_fee,
            "start_date": start_date,
            "payment_status": "due"
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
            print(f"   📅 Next payment date: {response.get('next_payment_date')}")
            print(f"   💵 Amount owed: {response.get('amount_owed')}")
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
            return response
        else:
            print(f"   ❌ Failed to record payment")
            return {}

    def test_critical_partial_payment_logic(self):
        """
        CRITICAL TEST: Verify that completing partial payments does NOT advance due date
        while fresh full payments DO advance due date
        """
        print("\n" + "="*100)
        print("🚨 CRITICAL PARTIAL PAYMENT DUE DATE ADVANCEMENT TEST")
        print("="*100)
        print("TESTING: Due date advancement depends on payment_amount >= monthly_fee")
        print("NOT just remaining_balance <= 0")
        print("="*100)
        
        # Test 1: Partial Payment Completion (Should NOT advance due date)
        print("\n📋 TEST 1: PARTIAL PAYMENT COMPLETION")
        print("-" * 50)
        
        client1_id = self.create_test_client("Partial Completion Client", 100.0, "2025-01-01")
        if not client1_id:
            return False
            
        # Record partial payment TTD 60
        partial_response = self.record_payment(client1_id, 60.0, "2025-01-15", "Partial TTD 60")
        if not partial_response:
            return False
            
        # Verify partial payment doesn't advance due date
        if partial_response.get('due_date_advanced') != False:
            print(f"   ❌ CRITICAL ERROR: Partial payment should not advance due date")
            return False
        print(f"   ✅ Partial payment correctly does NOT advance due date")
        
        # Record completion payment TTD 40 (total = 100, but this payment < monthly_fee)
        completion_response = self.record_payment(client1_id, 40.0, "2025-01-20", "Completion TTD 40")
        if not completion_response:
            return False
            
        # CRITICAL VERIFICATION: Completion should NOT advance due date
        if completion_response.get('due_date_advanced') != False:
            print(f"   ❌ CRITICAL BUG: Completion payment should NOT advance due date!")
            print(f"   ❌ This is the exact bug the fix was supposed to address!")
            return False
        
        if str(completion_response.get('new_next_payment_date')) != "February 01, 2025":
            print(f"   ❌ CRITICAL BUG: Due date should stay February 1st after completion")
            return False
            
        print(f"   ✅ CRITICAL FIX VERIFIED: Completion payment does NOT advance due date")
        print(f"   ✅ Due date stays February 1st as expected")
        
        # Test 2: Fresh Full Payment (Should advance due date)
        print("\n📋 TEST 2: FRESH FULL PAYMENT")
        print("-" * 50)
        
        client2_id = self.create_test_client("Fresh Full Payment Client", 100.0, "2025-01-01")
        if not client2_id:
            return False
            
        # Record fresh full payment TTD 100
        full_response = self.record_payment(client2_id, 100.0, "2025-01-15", "Fresh Full TTD 100")
        if not full_response:
            return False
            
        # Verify full payment advances due date
        if full_response.get('due_date_advanced') != True:
            print(f"   ❌ CRITICAL ERROR: Fresh full payment should advance due date")
            return False
            
        if str(full_response.get('new_next_payment_date')) != "March 01, 2025":
            print(f"   ❌ CRITICAL ERROR: Due date should advance to March 1st")
            return False
            
        print(f"   ✅ Fresh full payment correctly advances due date to March 1st")
        
        # Test 3: Overpayment (Should advance due date)
        print("\n📋 TEST 3: OVERPAYMENT")
        print("-" * 50)
        
        client3_id = self.create_test_client("Overpayment Client", 100.0, "2025-01-01")
        if not client3_id:
            return False
            
        # Record overpayment TTD 150
        overpay_response = self.record_payment(client3_id, 150.0, "2025-01-15", "Overpayment TTD 150")
        if not overpay_response:
            return False
            
        # Verify overpayment advances due date
        if overpay_response.get('due_date_advanced') != True:
            print(f"   ❌ CRITICAL ERROR: Overpayment should advance due date")
            return False
            
        print(f"   ✅ Overpayment correctly advances due date")
        
        # Test 4: Multiple Partial Completion
        print("\n📋 TEST 4: MULTIPLE PARTIAL COMPLETION")
        print("-" * 50)
        
        client4_id = self.create_test_client("Multiple Partial Client", 100.0, "2025-01-01")
        if not client4_id:
            return False
            
        # Record multiple partials: 30 + 40 + 30 = 100
        self.record_payment(client4_id, 30.0, "2025-01-10", "Partial 1 TTD 30")
        self.record_payment(client4_id, 40.0, "2025-01-15", "Partial 2 TTD 40")
        final_response = self.record_payment(client4_id, 30.0, "2025-01-20", "Final TTD 30")
        
        if not final_response:
            return False
            
        # CRITICAL: Final completion should NOT advance due date
        if final_response.get('due_date_advanced') != False:
            print(f"   ❌ CRITICAL BUG: Multiple partial completion should NOT advance due date")
            return False
            
        if str(final_response.get('new_next_payment_date')) != "February 01, 2025":
            print(f"   ❌ CRITICAL BUG: Due date should stay February 1st")
            return False
            
        print(f"   ✅ Multiple partial completion correctly does NOT advance due date")
        
        # Test 5: Fresh Payment After Completion
        print("\n📋 TEST 5: FRESH PAYMENT AFTER COMPLETION")
        print("-" * 50)
        
        # Use client4 from previous test (due date should still be Feb 1st)
        fresh_after_response = self.record_payment(client4_id, 100.0, "2025-02-01", "Fresh after completion TTD 100")
        
        if not fresh_after_response:
            return False
            
        # This should advance due date since payment_amount >= monthly_fee
        if fresh_after_response.get('due_date_advanced') != True:
            print(f"   ❌ CRITICAL ERROR: Fresh payment after completion should advance due date")
            return False
            
        if str(fresh_after_response.get('new_next_payment_date')) != "March 01, 2025":
            print(f"   ❌ CRITICAL ERROR: Due date should advance to March 1st")
            return False
            
        print(f"   ✅ Fresh payment after completion correctly advances due date")
        
        return True

    def run_all_tests(self):
        """Run all critical partial payment tests"""
        print("\n" + "="*100)
        print("🚨 CRITICAL PARTIAL PAYMENT DUE DATE ADVANCEMENT TESTING")
        print("="*100)
        
        success = self.test_critical_partial_payment_logic()
        
        # Summary
        print("\n" + "="*100)
        print("🎯 CRITICAL TEST SUMMARY")
        print("="*100)
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if success:
            print("\n✅ CRITICAL FIX VERIFICATION: SUCCESS!")
            print("✅ Partial payment completion does NOT advance due date")
            print("✅ Fresh full payments DO advance due date")
            print("✅ Overpayments DO advance due date")
            print("✅ Multiple partial completions do NOT advance due date")
            print("✅ Fresh payments after completion DO advance due date")
            print("✅ CRITICAL LOGIC WORKING: payment_amount >= monthly_fee determines advancement")
            print("\n🎉 THE PARTIAL PAYMENT DUE DATE ADVANCEMENT FIX IS WORKING CORRECTLY!")
        else:
            print("\n❌ CRITICAL FIX VERIFICATION: FAILED!")
            print("❌ Due date advancement logic has bugs")
            print("❌ The fix may not be working as expected")
            
        return success

if __name__ == "__main__":
    tester = CriticalPartialPaymentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)