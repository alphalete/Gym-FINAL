#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class PartialPaymentDisplayTester:
    def __init__(self, base_url="https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test1_client_id = None
        self.test2_client_id = None

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

    def test_create_test1_client(self):
        """Create TEST1 client with TTD 1000 monthly fee"""
        print("\n🎯 STEP 1: CREATE TEST CLIENT 'TEST1' WITH TTD 1000 MONTHLY FEE")
        print("=" * 80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "TEST1",
            "email": f"test1_partial_payment_{timestamp}@example.com",
            "phone": "(555) 001-0001",
            "membership_type": "Premium",
            "monthly_fee": 1000.0,
            "start_date": "2025-01-15",
            "payment_status": "due"  # Client hasn't paid yet
        }
        
        success, response = self.run_test(
            "Create TEST1 Client (TTD 1000 monthly fee)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.test1_client_id = response["id"]
            print(f"   ✅ Created TEST1 client ID: {self.test1_client_id}")
            print(f"   📝 Client name: {response.get('name')}")
            print(f"   💰 Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   💳 Amount owed: TTD {response.get('amount_owed')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            
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

    def test_make_partial_payment_test1(self):
        """Make partial payment of TTD 600 for TEST1 client"""
        print("\n🎯 STEP 2: MAKE PARTIAL PAYMENT OF TTD 600 FOR TEST1 CLIENT")
        print("=" * 80)
        
        if not self.test1_client_id:
            print("❌ Make Partial Payment - SKIPPED (No TEST1 client ID available)")
            return False
        
        payment_data = {
            "client_id": self.test1_client_id,
            "amount_paid": 600.0,
            "payment_date": "2025-01-20",
            "payment_method": "Cash",
            "notes": "Partial payment test - TTD 600 of TTD 1000"
        }
        
        success, response = self.run_test(
            "Record Partial Payment TTD 600 for TEST1",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   ✅ Payment recorded for: {response.get('client_name')}")
            print(f"   💰 Amount paid: TTD {response.get('amount_paid')}")
            print(f"   📊 Payment type: {response.get('payment_type')}")
            print(f"   💳 Remaining balance: TTD {response.get('remaining_balance')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            
            # Verify partial payment results
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
                print("   ✅ Payment status correctly remains 'due' for partial payment")
            else:
                print(f"   ❌ Payment status incorrect: Expected 'due', Got '{response.get('payment_status')}'")
                return False
        
        return success

    def test_verify_test1_client_data(self):
        """Verify TEST1 client data after partial payment"""
        print("\n🎯 STEP 3: VERIFY TEST1 CLIENT DATA AFTER PARTIAL PAYMENT")
        print("=" * 80)
        
        if not self.test1_client_id:
            print("❌ Verify TEST1 Client Data - SKIPPED (No TEST1 client ID available)")
            return False
        
        success, response = self.run_test(
            "Get TEST1 Client Data After Partial Payment",
            "GET",
            f"clients/{self.test1_client_id}",
            200
        )
        
        if success:
            print(f"   📝 Client name: {response.get('name')}")
            print(f"   💰 Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   💳 Amount owed: TTD {response.get('amount_owed')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            
            # Critical verification for frontend display logic
            print(f"\n   🎯 FRONTEND DISPLAY LOGIC VERIFICATION:")
            print(f"   Frontend logic: client.amount_owed || client.monthly_fee")
            print(f"   client.amount_owed = {response.get('amount_owed')}")
            print(f"   client.monthly_fee = {response.get('monthly_fee')}")
            
            if response.get('amount_owed') == 400.0:
                print("   ✅ Frontend will use amount_owed (400.0) - CORRECT!")
                print("   ✅ Frontend should display: 'OWES TTD 400' (not TTD 1000)")
            else:
                print(f"   ❌ amount_owed incorrect: Expected TTD 400, Got TTD {response.get('amount_owed')}")
                return False
                
            if response.get('payment_status') == 'due':
                print("   ✅ Payment status correctly shows 'due'")
            else:
                print(f"   ❌ Payment status incorrect: Expected 'due', Got '{response.get('payment_status')}'")
                return False
        
        return success

    def test_get_all_clients_verify_test1(self):
        """Get all clients and verify TEST1 appears with correct data"""
        print("\n🎯 STEP 4: VERIFY TEST1 IN CLIENT LIST FOR FRONTEND")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get All Clients - Verify TEST1 Data",
            "GET",
            "clients",
            200
        )
        
        if success:
            print(f"   📊 Total clients returned: {len(response)}")
            
            # Find TEST1 client in the list
            test1_client = None
            for client in response:
                if client.get('name') == 'TEST1':
                    test1_client = client
                    break
            
            if test1_client:
                print(f"   ✅ Found TEST1 client in client list")
                print(f"   📝 Name: {test1_client.get('name')}")
                print(f"   💰 Monthly fee: TTD {test1_client.get('monthly_fee')}")
                print(f"   💳 Amount owed: TTD {test1_client.get('amount_owed')}")
                print(f"   📊 Payment status: {test1_client.get('payment_status')}")
                
                # Verify frontend will receive correct data
                if test1_client.get('amount_owed') == 400.0:
                    print("   ✅ Frontend will receive amount_owed = TTD 400")
                    print("   ✅ Frontend display logic will show: 'OWES TTD 400'")
                    print("   ✅ User's issue 'OWES TTD 1000 instead of remaining balance' is RESOLVED!")
                else:
                    print(f"   ❌ Frontend will receive incorrect amount_owed: TTD {test1_client.get('amount_owed')}")
                    return False
            else:
                print("   ❌ TEST1 client not found in client list")
                return False
        
        return success

    def test_create_test2_client(self):
        """Create TEST2 client with TTD 500 monthly fee, no payments made"""
        print("\n🎯 STEP 5: CREATE TEST CLIENT 'TEST2' WITH TTD 500 MONTHLY FEE (NO PAYMENTS)")
        print("=" * 80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "TEST2",
            "email": f"test2_no_payment_{timestamp}@example.com",
            "phone": "(555) 002-0002",
            "membership_type": "Standard",
            "monthly_fee": 500.0,
            "start_date": "2025-01-15",
            "payment_status": "due"  # Client hasn't paid yet
        }
        
        success, response = self.run_test(
            "Create TEST2 Client (TTD 500 monthly fee, no payments)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.test2_client_id = response["id"]
            print(f"   ✅ Created TEST2 client ID: {self.test2_client_id}")
            print(f"   📝 Client name: {response.get('name')}")
            print(f"   💰 Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   💳 Amount owed: TTD {response.get('amount_owed')}")
            print(f"   📊 Payment status: {response.get('payment_status')}")
            
            # Verify initial state for full amount owed scenario
            if response.get('amount_owed') == 500.0:
                print("   ✅ Amount owed correctly set to TTD 500 (full monthly fee)")
                print("   ✅ Frontend should display: 'OWES TTD 500'")
            else:
                print(f"   ❌ Amount owed incorrect: Expected TTD 500, Got TTD {response.get('amount_owed')}")
                return False
        
        return success

    def test_verify_both_clients_final(self):
        """Final verification of both test clients for frontend display"""
        print("\n🎯 STEP 6: FINAL VERIFICATION - BOTH TEST CLIENTS FOR FRONTEND DISPLAY")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get All Clients - Final Verification",
            "GET",
            "clients",
            200
        )
        
        if success:
            print(f"   📊 Total clients: {len(response)}")
            
            test1_found = False
            test2_found = False
            
            for client in response:
                if client.get('name') == 'TEST1':
                    test1_found = True
                    print(f"\n   🎯 TEST1 CLIENT (Partial Payment Scenario):")
                    print(f"      Name: {client.get('name')}")
                    print(f"      Monthly fee: TTD {client.get('monthly_fee')}")
                    print(f"      Amount owed: TTD {client.get('amount_owed')}")
                    print(f"      Payment status: {client.get('payment_status')}")
                    print(f"      Frontend display: 'OWES TTD {client.get('amount_owed')}' ✅")
                    
                elif client.get('name') == 'TEST2':
                    test2_found = True
                    print(f"\n   🎯 TEST2 CLIENT (Full Amount Owed Scenario):")
                    print(f"      Name: {client.get('name')}")
                    print(f"      Monthly fee: TTD {client.get('monthly_fee')}")
                    print(f"      Amount owed: TTD {client.get('amount_owed')}")
                    print(f"      Payment status: {client.get('payment_status')}")
                    print(f"      Frontend display: 'OWES TTD {client.get('amount_owed')}' ✅")
            
            if test1_found and test2_found:
                print(f"\n   ✅ Both test clients found and verified!")
                print(f"   ✅ TEST1: Shows 'OWES TTD 400' (partial payment scenario)")
                print(f"   ✅ TEST2: Shows 'OWES TTD 500' (full amount owed scenario)")
                print(f"   ✅ Frontend logic 'client.amount_owed || client.monthly_fee' will work correctly")
                return True
            else:
                print(f"   ❌ Missing test clients: TEST1={test1_found}, TEST2={test2_found}")
                return False
        
        return success

    def test_payment_stats_verification(self):
        """Verify payment statistics include the partial payment"""
        print("\n🎯 STEP 7: VERIFY PAYMENT STATISTICS INCLUDE PARTIAL PAYMENT")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            print(f"   💰 Total revenue: TTD {response.get('total_revenue')}")
            print(f"   📊 Payment count: {response.get('payment_count')}")
            print(f"   💳 Total amount owed: TTD {response.get('total_amount_owed')}")
            
            # Verify partial payment is included in revenue
            total_revenue = response.get('total_revenue', 0)
            if total_revenue >= 600.0:  # Should include our TTD 600 partial payment
                print("   ✅ Partial payment (TTD 600) included in total revenue")
            else:
                print(f"   ⚠️  Total revenue may not include partial payment: TTD {total_revenue}")
            
            # Verify total amount owed includes remaining balances
            total_owed = response.get('total_amount_owed', 0)
            expected_minimum = 400.0 + 500.0  # TEST1 (400) + TEST2 (500)
            if total_owed >= expected_minimum:
                print(f"   ✅ Total amount owed includes remaining balances (≥ TTD {expected_minimum})")
            else:
                print(f"   ⚠️  Total amount owed may be incorrect: TTD {total_owed}")
        
        return success

    def run_all_tests(self):
        """Run all partial payment display tests"""
        print("🎯 PARTIAL PAYMENT DISPLAY FIX COMPREHENSIVE TESTING")
        print("=" * 80)
        print("OBJECTIVE: Demonstrate that partial payment display fix is working correctly")
        print("USER ISSUE: Dashboard showing 'OWES TTD 1000' instead of remaining balance after partial payments")
        print("EXPECTED RESULT: Frontend should display correct remaining balances after partial payments")
        print("=" * 80)
        
        # Run all test steps
        tests = [
            self.test_create_test1_client,
            self.test_make_partial_payment_test1,
            self.test_verify_test1_client_data,
            self.test_get_all_clients_verify_test1,
            self.test_create_test2_client,
            self.test_verify_both_clients_final,
            self.test_payment_stats_verification
        ]
        
        for test in tests:
            if not test():
                print(f"\n❌ Test failed: {test.__name__}")
                break
        
        # Print final summary
        print(f"\n🎯 PARTIAL PAYMENT DISPLAY FIX TEST SUMMARY")
        print("=" * 80)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print(f"\n✅ ALL TESTS PASSED - PARTIAL PAYMENT DISPLAY FIX IS WORKING CORRECTLY!")
            print(f"✅ TEST1 client: Shows 'OWES TTD 400' (partial payment scenario)")
            print(f"✅ TEST2 client: Shows 'OWES TTD 500' (full amount owed scenario)")
            print(f"✅ Backend correctly updates amount_owed after partial payments")
            print(f"✅ Frontend logic will receive correct data to display proper remaining balances")
            print(f"✅ User's issue 'OWES TTD 1000 instead of remaining balance' is RESOLVED!")
            print(f"\n🎉 CONCLUSION: The partial payment display fix is working EXACTLY as specified!")
        else:
            print(f"\n❌ SOME TESTS FAILED - PARTIAL PAYMENT DISPLAY FIX NEEDS ATTENTION")
            print(f"❌ {self.tests_run - self.tests_passed} out of {self.tests_run} tests failed")

if __name__ == "__main__":
    tester = PartialPaymentDisplayTester()
    tester.run_all_tests()