#!/usr/bin/env python3
"""
Total Amount Owed Calculation Testing
=====================================

Test the new "Total Amount Owed" calculation in the /api/payments/stats endpoint
to verify it correctly shows outstanding balances after partial payments.

TESTING SCOPE:
1. Payment Stats Endpoint Verification
2. Partial Payment Amount Owed Calculation  
3. Multiple Clients Outstanding Balances
4. Full Payment Verification
5. Zero Balance Handling
"""

import requests
import json
from datetime import date, datetime
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class TotalAmountOwedTester:
    def __init__(self):
        self.test_clients = []
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        print(result)
        self.test_results.append(result)
        return passed
    
    def cleanup_test_clients(self):
        """Clean up test clients created during testing"""
        print("\n🧹 CLEANING UP TEST CLIENTS...")
        for client_id in self.test_clients:
            try:
                response = requests.delete(f"{API_BASE}/clients/{client_id}")
                if response.status_code == 200:
                    print(f"   Deleted test client: {client_id}")
            except Exception as e:
                print(f"   Failed to delete client {client_id}: {str(e)}")
        self.test_clients.clear()
    
    def create_test_client(self, name, monthly_fee, payment_status="due"):
        """Create a test client and return client data"""
        client_data = {
            "name": name,
            "email": f"{name.lower().replace(' ', '_')}@totalowed.test",
            "phone": "555-0123",
            "membership_type": "Test",
            "monthly_fee": monthly_fee,
            "start_date": date.today().isoformat(),
            "payment_status": payment_status
        }
        
        response = requests.post(f"{API_BASE}/clients", json=client_data)
        if response.status_code == 200:
            client = response.json()
            self.test_clients.append(client['id'])
            return client
        else:
            raise Exception(f"Failed to create client: {response.text}")
    
    def record_payment(self, client_id, amount):
        """Record a payment for a client"""
        payment_data = {
            "client_id": client_id,
            "amount_paid": amount,
            "payment_date": date.today().isoformat(),
            "payment_method": "Test Payment",
            "notes": "Test payment for total amount owed verification"
        }
        
        response = requests.post(f"{API_BASE}/payments/record", json=payment_data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to record payment: {response.text}")
    
    def get_payment_stats(self):
        """Get payment statistics"""
        response = requests.get(f"{API_BASE}/payments/stats")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get payment stats: {response.text}")
    
    def get_client(self, client_id):
        """Get client details"""
        response = requests.get(f"{API_BASE}/clients/{client_id}")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get client: {response.text}")
    
    def test_payment_stats_endpoint_verification(self):
        """Test 1: Payment Stats Endpoint Verification"""
        print("\n🎯 TEST 1: PAYMENT STATS ENDPOINT VERIFICATION")
        
        try:
            stats = self.get_payment_stats()
            
            # Verify endpoint returns total_amount_owed field
            has_field = 'total_amount_owed' in stats
            self.log_test("Payment stats endpoint returns total_amount_owed field", 
                         has_field, f"Stats keys: {list(stats.keys())}")
            
            # Verify field is numeric
            if has_field:
                is_numeric = isinstance(stats['total_amount_owed'], (int, float))
                self.log_test("total_amount_owed is numeric", 
                             is_numeric, f"Value: {stats['total_amount_owed']} (type: {type(stats['total_amount_owed'])})")
            
            return has_field and (not has_field or is_numeric)
            
        except Exception as e:
            self.log_test("Payment stats endpoint verification", False, f"Error: {str(e)}")
            return False
    
    def test_partial_payment_calculation(self):
        """Test 2: Partial Payment Amount Owed Calculation"""
        print("\n🎯 TEST 2: PARTIAL PAYMENT AMOUNT OWED CALCULATION")
        
        try:
            # Get initial stats
            initial_stats = self.get_payment_stats()
            initial_owed = initial_stats.get('total_amount_owed', 0)
            
            # Create client with TTD 100 monthly fee
            client = self.create_test_client("Partial Payment Client", 100.0)
            client_id = client['id']
            
            # Verify client initially owes TTD 100
            client_data = self.get_client(client_id)
            initial_amount_owed = client_data.get('amount_owed', 0)
            self.log_test("Client initially owes monthly fee", 
                         initial_amount_owed == 100.0, 
                         f"Expected: 100.0, Got: {initial_amount_owed}")
            
            # Check stats include the new client's debt
            stats_after_client = self.get_payment_stats()
            expected_owed = initial_owed + 100.0
            actual_owed = stats_after_client.get('total_amount_owed', 0)
            self.log_test("Stats include new client's debt", 
                         actual_owed == expected_owed,
                         f"Expected: {expected_owed}, Got: {actual_owed}")
            
            # Make partial payment TTD 60 (client should owe TTD 40)
            payment_result = self.record_payment(client_id, 60.0)
            self.log_test("Partial payment recorded successfully", 
                         payment_result.get('success', False),
                         f"Payment type: {payment_result.get('payment_type', 'unknown')}")
            
            # Verify client now owes TTD 40
            client_after_partial = self.get_client(client_id)
            remaining_owed = client_after_partial.get('amount_owed', 0)
            self.log_test("Client owes TTD 40 after TTD 60 partial payment", 
                         remaining_owed == 40.0,
                         f"Expected: 40.0, Got: {remaining_owed}")
            
            # Check stats reflect TTD 40 remaining balance
            stats_after_partial = self.get_payment_stats()
            expected_total_after_partial = initial_owed + 40.0
            actual_total_after_partial = stats_after_partial.get('total_amount_owed', 0)
            self.log_test("Stats show TTD 40 remaining balance", 
                         actual_total_after_partial == expected_total_after_partial,
                         f"Expected: {expected_total_after_partial}, Got: {actual_total_after_partial}")
            
            # Make another partial payment TTD 25 (client should owe TTD 15)
            payment_result2 = self.record_payment(client_id, 25.0)
            self.log_test("Second partial payment recorded successfully", 
                         payment_result2.get('success', False))
            
            # Verify client now owes TTD 15
            client_after_second_partial = self.get_client(client_id)
            final_remaining = client_after_second_partial.get('amount_owed', 0)
            self.log_test("Client owes TTD 15 after second TTD 25 partial payment", 
                         final_remaining == 15.0,
                         f"Expected: 15.0, Got: {final_remaining}")
            
            # Check stats reflect TTD 15 remaining balance
            stats_final = self.get_payment_stats()
            expected_final_total = initial_owed + 15.0
            actual_final_total = stats_final.get('total_amount_owed', 0)
            self.log_test("Stats show TTD 15 remaining balance", 
                         actual_final_total == expected_final_total,
                         f"Expected: {expected_final_total}, Got: {actual_final_total}")
            
            return True
            
        except Exception as e:
            self.log_test("Partial payment calculation test", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_clients_outstanding_balances(self):
        """Test 3: Multiple Clients Outstanding Balances"""
        print("\n🎯 TEST 3: MULTIPLE CLIENTS OUTSTANDING BALANCES")
        
        try:
            # Get initial stats
            initial_stats = self.get_payment_stats()
            initial_owed = initial_stats.get('total_amount_owed', 0)
            
            # Create Client A: Will owe TTD 40 after partial payment
            client_a = self.create_test_client("Client A Outstanding", 100.0)
            self.record_payment(client_a['id'], 60.0)  # Pay TTD 60, owe TTD 40
            
            # Create Client B: Will owe full TTD 100 (no payments)
            client_b = self.create_test_client("Client B Outstanding", 100.0)
            
            # Create Client C: Will be paid in full (owe TTD 0)
            client_c = self.create_test_client("Client C Outstanding", 100.0)
            self.record_payment(client_c['id'], 100.0)  # Pay full amount
            
            # Verify individual client states
            client_a_data = self.get_client(client_a['id'])
            client_b_data = self.get_client(client_b['id'])
            client_c_data = self.get_client(client_c['id'])
            
            a_owes = client_a_data.get('amount_owed', 0)
            b_owes = client_b_data.get('amount_owed', 0)
            c_owes = client_c_data.get('amount_owed', 0)
            
            self.log_test("Client A owes TTD 40", a_owes == 40.0, f"Got: {a_owes}")
            self.log_test("Client B owes TTD 100", b_owes == 100.0, f"Got: {b_owes}")
            self.log_test("Client C owes TTD 0", c_owes == 0.0, f"Got: {c_owes}")
            
            # Verify total_amount_owed = TTD 140 (40 + 100 + 0)
            stats = self.get_payment_stats()
            expected_total = initial_owed + 140.0  # 40 + 100 + 0
            actual_total = stats.get('total_amount_owed', 0)
            
            self.log_test("Total amount owed = TTD 140 (40 + 100 + 0)", 
                         actual_total == expected_total,
                         f"Expected: {expected_total}, Got: {actual_total}")
            
            return True
            
        except Exception as e:
            self.log_test("Multiple clients outstanding balances test", False, f"Error: {str(e)}")
            return False
    
    def test_full_payment_verification(self):
        """Test 4: Full Payment Verification"""
        print("\n🎯 TEST 4: FULL PAYMENT VERIFICATION")
        
        try:
            # Get initial stats
            initial_stats = self.get_payment_stats()
            initial_owed = initial_stats.get('total_amount_owed', 0)
            
            # Create client with partial payment scenario
            client = self.create_test_client("Full Payment Client", 100.0)
            client_id = client['id']
            
            # Make partial payment TTD 60 (owes TTD 40)
            self.record_payment(client_id, 60.0)
            
            # Verify client owes TTD 40
            client_partial = self.get_client(client_id)
            partial_owed = client_partial.get('amount_owed', 0)
            self.log_test("Client owes TTD 40 after partial payment", 
                         partial_owed == 40.0, f"Got: {partial_owed}")
            
            # Check stats include TTD 40
            stats_partial = self.get_payment_stats()
            expected_with_partial = initial_owed + 40.0
            actual_with_partial = stats_partial.get('total_amount_owed', 0)
            self.log_test("Stats include TTD 40 from partial payment", 
                         actual_with_partial == expected_with_partial,
                         f"Expected: {expected_with_partial}, Got: {actual_with_partial}")
            
            # Complete payment with remaining TTD 40
            completion_result = self.record_payment(client_id, 40.0)
            self.log_test("Completion payment recorded successfully", 
                         completion_result.get('success', False))
            
            # Verify client now owes TTD 0
            client_paid = self.get_client(client_id)
            final_owed = client_paid.get('amount_owed', 0)
            self.log_test("Client owes TTD 0 after completion payment", 
                         final_owed == 0.0, f"Got: {final_owed}")
            
            # Verify payment status is 'paid'
            payment_status = client_paid.get('payment_status', '')
            self.log_test("Client payment status is 'paid'", 
                         payment_status == 'paid', f"Got: {payment_status}")
            
            # Check that total_amount_owed decreased by TTD 40
            stats_final = self.get_payment_stats()
            expected_after_completion = initial_owed  # Back to initial (no debt from this client)
            actual_after_completion = stats_final.get('total_amount_owed', 0)
            self.log_test("Total amount owed decreased by TTD 40", 
                         actual_after_completion == expected_after_completion,
                         f"Expected: {expected_after_completion}, Got: {actual_after_completion}")
            
            return True
            
        except Exception as e:
            self.log_test("Full payment verification test", False, f"Error: {str(e)}")
            return False
    
    def test_zero_balance_handling(self):
        """Test 5: Zero Balance Handling"""
        print("\n🎯 TEST 5: ZERO BALANCE HANDLING")
        
        try:
            # Get initial stats
            initial_stats = self.get_payment_stats()
            initial_owed = initial_stats.get('total_amount_owed', 0)
            
            # Create multiple clients with different payment states
            client_paid = self.create_test_client("Zero Balance Client", 75.0)
            client_unpaid = self.create_test_client("Positive Balance Client", 50.0)
            
            # Pay client_paid in full
            self.record_payment(client_paid['id'], 75.0)
            
            # Leave client_unpaid unpaid
            
            # Verify individual states
            paid_data = self.get_client(client_paid['id'])
            unpaid_data = self.get_client(client_unpaid['id'])
            
            paid_owes = paid_data.get('amount_owed', 0)
            unpaid_owes = unpaid_data.get('amount_owed', 0)
            
            self.log_test("Paid client has amount_owed = 0", 
                         paid_owes == 0.0, f"Got: {paid_owes}")
            self.log_test("Unpaid client has amount_owed > 0", 
                         unpaid_owes > 0, f"Got: {unpaid_owes}")
            
            # Verify only positive balances contribute to total
            stats = self.get_payment_stats()
            expected_total = initial_owed + unpaid_owes  # Only unpaid client contributes
            actual_total = stats.get('total_amount_owed', 0)
            
            self.log_test("Only clients with positive balances contribute to total", 
                         actual_total == expected_total,
                         f"Expected: {expected_total}, Got: {actual_total}")
            
            # Test edge case: overpayment
            overpay_client = self.create_test_client("Overpay Client", 60.0)
            self.record_payment(overpay_client['id'], 80.0)  # Pay more than owed
            
            overpay_data = self.get_client(overpay_client['id'])
            overpay_owes = overpay_data.get('amount_owed', 0)
            
            self.log_test("Overpaid client has amount_owed = 0", 
                         overpay_owes == 0.0, f"Got: {overpay_owes}")
            
            # Verify overpaid client doesn't contribute to total
            stats_after_overpay = self.get_payment_stats()
            expected_after_overpay = initial_owed + unpaid_owes  # Still only unpaid client
            actual_after_overpay = stats_after_overpay.get('total_amount_owed', 0)
            
            self.log_test("Overpaid client doesn't contribute to total amount owed", 
                         actual_after_overpay == expected_after_overpay,
                         f"Expected: {expected_after_overpay}, Got: {actual_after_overpay}")
            
            return True
            
        except Exception as e:
            self.log_test("Zero balance handling test", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all total amount owed tests"""
        print("🚀 STARTING TOTAL AMOUNT OWED CALCULATION TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        
        try:
            # Run all test scenarios
            self.test_payment_stats_endpoint_verification()
            self.test_partial_payment_calculation()
            self.test_multiple_clients_outstanding_balances()
            self.test_full_payment_verification()
            self.test_zero_balance_handling()
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {str(e)}")
        
        finally:
            # Clean up test data
            self.cleanup_test_clients()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TOTAL AMOUNT OWED TESTING SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 ALL TESTS PASSED! Total Amount Owed calculation is working perfectly!")
        elif success_rate >= 80:
            print(f"\n✅ MOSTLY SUCCESSFUL! {success_rate:.1f}% of tests passed.")
        else:
            print(f"\n❌ SIGNIFICANT ISSUES DETECTED! Only {success_rate:.1f}% of tests passed.")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"   {result}")
        
        return success_rate == 100

if __name__ == "__main__":
    tester = TotalAmountOwedTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)