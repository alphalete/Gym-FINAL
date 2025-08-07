#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class PartialPaymentTester:
    def __init__(self, base_url="https://alphalete-club.emergent.host"):
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

    def test_create_test_client(self):
        """Create test client 'TEST_PARTIAL' with TTD 1000 monthly fee"""
        print("\n🎯 STEP 1: CREATE TEST CLIENT")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "TEST_PARTIAL",
            "email": f"test_partial_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Premium",
            "monthly_fee": 1000.0,
            "start_date": "2025-01-15",
            "payment_status": "due"  # Explicitly set as unpaid
        }
        
        success, response = self.run_test(
            "Create TEST_PARTIAL Client with TTD 1000 Monthly Fee",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.test_client_id = response["id"]
            print(f"   ✅ Created test client ID: {self.test_client_id}")
            print(f"   📝 Client name: {response.get('name')}")
            print(f"   💰 Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            print(f"   💳 Amount owed: TTD {response.get('amount_owed')}")
            
            # Verify initial state
            if response.get('amount_owed') == 1000.0:
                print("   ✅ Initial amount_owed correctly set to TTD 1000")
            else:
                print(f"   ❌ Initial amount_owed incorrect: Expected TTD 1000, Got TTD {response.get('amount_owed')}")
                return False
                
            if response.get('payment_status') == 'due':
                print("   ✅ Initial payment_status correctly set to 'due'")
            else:
                print(f"   ❌ Initial payment_status incorrect: Expected 'due', Got '{response.get('payment_status')}'")
                return False
        
        return success

    def test_verify_initial_client_state(self):
        """Verify initial client shows amount_owed = TTD 1000"""
        print("\n🎯 STEP 2: VERIFY INITIAL CLIENT STATE")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client ID available")
            return False
            
        success, response = self.run_test(
            "Verify Initial Client State",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if success:
            print(f"   📝 Client name: {response.get('name')}")
            print(f"   💰 Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            print(f"   💳 Amount owed: TTD {response.get('amount_owed')}")
            
            # Verify client shows amount_owed = TTD 1000
            if response.get('amount_owed') == 1000.0:
                print("   ✅ Client correctly shows amount_owed = TTD 1000")
            else:
                print(f"   ❌ Client amount_owed incorrect: Expected TTD 1000, Got TTD {response.get('amount_owed')}")
                return False
                
            if response.get('payment_status') == 'due':
                print("   ✅ Client correctly shows payment_status = 'due'")
            else:
                print(f"   ❌ Client payment_status incorrect: Expected 'due', Got '{response.get('payment_status')}'")
                return False
        
        return success

    def test_make_partial_payment(self):
        """Make partial payment of TTD 600 for the client"""
        print("\n🎯 STEP 3: MAKE PARTIAL PAYMENT TTD 600")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client ID available")
            return False
            
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 600.0,
            "payment_date": "2025-01-20",
            "payment_method": "Cash",
            "notes": "Partial payment test - TTD 600 of TTD 1000"
        }
        
        success, response = self.run_test(
            "Record Partial Payment TTD 600",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   💰 Amount paid: TTD {response.get('amount_paid')}")
            print(f"   📊 Payment type: {response.get('payment_type')}")
            print(f"   💳 Remaining balance: TTD {response.get('remaining_balance')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            print(f"   📅 Due date advanced: {response.get('due_date_advanced')}")
            
            # Verify partial payment response
            if response.get('payment_type') == 'partial':
                print("   ✅ Payment correctly identified as 'partial'")
            else:
                print(f"   ❌ Payment type incorrect: Expected 'partial', Got '{response.get('payment_type')}'")
                return False
                
            if response.get('remaining_balance') == 400.0:
                print("   ✅ Remaining balance correctly calculated as TTD 400")
            else:
                print(f"   ❌ Remaining balance incorrect: Expected TTD 400, Got TTD {response.get('remaining_balance')}")
                return False
                
            if response.get('payment_status') == 'due':
                print("   ✅ Payment status correctly remains 'due'")
            else:
                print(f"   ❌ Payment status incorrect: Expected 'due', Got '{response.get('payment_status')}'")
                return False
                
            if response.get('due_date_advanced') == False:
                print("   ✅ Due date correctly NOT advanced for partial payment")
            else:
                print(f"   ❌ Due date advancement incorrect: Expected False, Got {response.get('due_date_advanced')}")
                return False
        
        return success

    def test_verify_client_after_partial_payment(self):
        """Verify client's amount_owed is updated to TTD 400 (not TTD 1000)"""
        print("\n🎯 STEP 4: VERIFY CLIENT DATA AFTER PARTIAL PAYMENT")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client ID available")
            return False
            
        success, response = self.run_test(
            "Verify Client Data After Partial Payment",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if success:
            print(f"   📝 Client name: {response.get('name')}")
            print(f"   💰 Monthly fee: TTD {response.get('monthly_fee')} (should remain unchanged)")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            print(f"   💳 Amount owed: TTD {response.get('amount_owed')} (CRITICAL - should be TTD 400)")
            
            # CRITICAL VERIFICATION: amount_owed should be TTD 400, not TTD 1000
            if response.get('amount_owed') == 400.0:
                print("   ✅ CRITICAL SUCCESS: Client amount_owed correctly updated to TTD 400")
                print("   ✅ Frontend logic 'client.amount_owed || client.monthly_fee' would use TTD 400")
                print("   ✅ Client should display 'OWES TTD 400' not 'OWES TTD 1000'")
            else:
                print(f"   ❌ CRITICAL FAILURE: Client amount_owed incorrect!")
                print(f"      Expected: TTD 400 (remaining balance after TTD 600 payment)")
                print(f"      Got: TTD {response.get('amount_owed')}")
                print(f"   ❌ Frontend would show incorrect amount!")
                return False
                
            if response.get('payment_status') == 'due':
                print("   ✅ Payment status correctly remains 'due'")
            else:
                print(f"   ❌ Payment status incorrect: Expected 'due', Got '{response.get('payment_status')}'")
                return False
                
            if response.get('monthly_fee') == 1000.0:
                print("   ✅ Monthly fee correctly unchanged at TTD 1000")
            else:
                print(f"   ❌ Monthly fee changed unexpectedly: Expected TTD 1000, Got TTD {response.get('monthly_fee')}")
                return False
        
        return success

    def test_verify_clients_list_data(self):
        """Verify GET /api/clients returns updated client data"""
        print("\n🎯 STEP 5: VERIFY CLIENTS LIST DATA")
        print("=" * 60)
        
        success, response = self.run_test(
            "Get All Clients and Find Test Client",
            "GET",
            "clients",
            200
        )
        
        if success:
            # Find our test client in the list
            test_client = None
            for client in response:
                if client.get('id') == self.test_client_id:
                    test_client = client
                    break
            
            if test_client:
                print(f"   📝 Found test client: {test_client.get('name')}")
                print(f"   💰 Monthly fee: TTD {test_client.get('monthly_fee')}")
                print(f"   📊 Payment status: {test_client.get('payment_status')}")
                print(f"   💳 Amount owed: TTD {test_client.get('amount_owed')}")
                
                # Verify client data in list
                if test_client.get('amount_owed') == 400.0:
                    print("   ✅ Client in list correctly shows amount_owed = TTD 400")
                else:
                    print(f"   ❌ Client in list shows incorrect amount_owed: Expected TTD 400, Got TTD {test_client.get('amount_owed')}")
                    return False
                    
                if test_client.get('payment_status') == 'due':
                    print("   ✅ Client in list correctly shows payment_status = 'due'")
                else:
                    print(f"   ❌ Client in list shows incorrect payment_status: Expected 'due', Got '{test_client.get('payment_status')}'")
                    return False
            else:
                print("   ❌ Test client not found in clients list")
                return False
        
        return success

    def test_second_partial_payment(self):
        """Make second partial payment TTD 200"""
        print("\n🎯 STEP 6: MAKE SECOND PARTIAL PAYMENT TTD 200")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client ID available")
            return False
            
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 200.0,
            "payment_date": "2025-01-25",
            "payment_method": "Credit Card",
            "notes": "Second partial payment test - TTD 200 of remaining TTD 400"
        }
        
        success, response = self.run_test(
            "Record Second Partial Payment TTD 200",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   💰 Amount paid: TTD {response.get('amount_paid')}")
            print(f"   📊 Payment type: {response.get('payment_type')}")
            print(f"   💳 Remaining balance: TTD {response.get('remaining_balance')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            
            # Verify second partial payment
            if response.get('remaining_balance') == 200.0:
                print("   ✅ Remaining balance correctly calculated as TTD 200")
            else:
                print(f"   ❌ Remaining balance incorrect: Expected TTD 200, Got TTD {response.get('remaining_balance')}")
                return False
        
        return success

    def test_verify_client_after_second_partial(self):
        """Verify amount_owed becomes TTD 200"""
        print("\n🎯 STEP 7: VERIFY CLIENT AFTER SECOND PARTIAL PAYMENT")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client ID available")
            return False
            
        success, response = self.run_test(
            "Verify Client After Second Partial Payment",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if success:
            print(f"   💳 Amount owed: TTD {response.get('amount_owed')} (should be TTD 200)")
            print(f"   📊 Payment status: {response.get('payment_status')} (should be 'due')")
            
            if response.get('amount_owed') == 200.0:
                print("   ✅ Client correctly shows 'OWES TTD 200'")
            else:
                print(f"   ❌ Client amount_owed incorrect: Expected TTD 200, Got TTD {response.get('amount_owed')}")
                return False
        
        return success

    def test_final_payment(self):
        """Make final payment TTD 200 to complete payment"""
        print("\n🎯 STEP 8: MAKE FINAL PAYMENT TTD 200")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client ID available")
            return False
            
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 200.0,
            "payment_date": "2025-01-30",
            "payment_method": "Bank Transfer",
            "notes": "Final payment test - completing TTD 1000 total"
        }
        
        success, response = self.run_test(
            "Record Final Payment TTD 200",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   💰 Amount paid: TTD {response.get('amount_paid')}")
            print(f"   📊 Payment type: {response.get('payment_type')}")
            print(f"   💳 Remaining balance: TTD {response.get('remaining_balance')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            
            # Verify final payment completes the balance
            if response.get('remaining_balance') == 0.0:
                print("   ✅ Remaining balance correctly becomes TTD 0")
            else:
                print(f"   ❌ Remaining balance incorrect: Expected TTD 0, Got TTD {response.get('remaining_balance')}")
                return False
                
            if response.get('payment_status') == 'paid':
                print("   ✅ Payment status correctly becomes 'paid'")
            else:
                print(f"   ❌ Payment status incorrect: Expected 'paid', Got '{response.get('payment_status')}'")
                return False
        
        return success

    def test_verify_final_client_state(self):
        """Verify amount_owed becomes TTD 0 and payment_status becomes 'paid'"""
        print("\n🎯 STEP 9: VERIFY FINAL CLIENT STATE")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client ID available")
            return False
            
        success, response = self.run_test(
            "Verify Final Client State",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if success:
            print(f"   💳 Amount owed: TTD {response.get('amount_owed')} (should be TTD 0)")
            print(f"   📊 Payment status: {response.get('payment_status')} (should be 'paid')")
            
            if response.get('amount_owed') == 0.0:
                print("   ✅ Client correctly shows amount_owed = TTD 0")
            else:
                print(f"   ❌ Client amount_owed incorrect: Expected TTD 0, Got TTD {response.get('amount_owed')}")
                return False
                
            if response.get('payment_status') == 'paid':
                print("   ✅ Client correctly shows payment_status = 'paid'")
            else:
                print(f"   ❌ Client payment_status incorrect: Expected 'paid', Got '{response.get('payment_status')}'")
                return False
        
        return success

    def run_all_tests(self):
        """Run all partial payment tests"""
        print("🎯 PARTIAL PAYMENT STATUS DISPLAY TESTING")
        print("=" * 80)
        print("Testing the specific issue: Individual client cards showing incorrect")
        print("'OWES' amounts after partial payments")
        print("=" * 80)
        
        tests = [
            self.test_create_test_client,
            self.test_verify_initial_client_state,
            self.test_make_partial_payment,
            self.test_verify_client_after_partial_payment,
            self.test_verify_clients_list_data,
            self.test_second_partial_payment,
            self.test_verify_client_after_second_partial,
            self.test_final_payment,
            self.test_verify_final_client_state
        ]
        
        for test in tests:
            if not test():
                print(f"\n❌ Test failed: {test.__name__}")
                break
        
        print(f"\n🎯 PARTIAL PAYMENT TESTING SUMMARY")
        print("=" * 60)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n✅ ALL TESTS PASSED!")
            print("✅ Partial payment handling is working correctly")
            print("✅ Client amount_owed updates properly after partial payments")
            print("✅ Frontend should display correct remaining balances")
            print("✅ Individual client cards should show correct 'OWES' amounts")
        else:
            print(f"\n❌ {self.tests_run - self.tests_passed} TESTS FAILED!")
            print("❌ Partial payment handling has issues")
            print("❌ Client payment status display may be incorrect")

if __name__ == "__main__":
    tester = PartialPaymentTester()
    tester.run_all_tests()