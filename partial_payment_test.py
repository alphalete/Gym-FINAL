#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class PartialPaymentTester:
    def __init__(self, base_url="https://442a58e4-b64f-4824-924a-0c12436c79ea.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_clients = []  # Store created client IDs for cleanup

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

    def create_test_client(self, name: str, monthly_fee: float, payment_status: str = "due") -> tuple:
        """Create a test client for payment testing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        client_data = {
            "name": name,
            "email": f"test_{timestamp}@example.com",
            "phone": f"(555) {len(self.created_clients)+100:03d}-{1000+len(self.created_clients):04d}",
            "membership_type": "Standard",
            "monthly_fee": monthly_fee,
            "start_date": date.today().isoformat(),
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
            print(f"   Created client ID: {client_id}")
            print(f"   Payment Status: {response.get('payment_status')}")
            print(f"   Amount Owed: {response.get('amount_owed')}")
            print(f"   Next Payment Date: {response.get('next_payment_date')}")
            return True, client_id, response
        
        return False, None, {}

    def record_payment(self, client_id: str, amount: float, payment_date: str = None) -> tuple:
        """Record a payment for a client"""
        if payment_date is None:
            payment_date = date.today().isoformat()
            
        payment_data = {
            "client_id": client_id,
            "amount_paid": amount,
            "payment_date": payment_date,
            "payment_method": "Test Payment",
            "notes": f"Test payment of TTD {amount}"
        }
        
        success, response = self.run_test(
            f"Record Payment - TTD {amount}",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        return success, response

    def get_client_details(self, client_id: str) -> tuple:
        """Get client details"""
        success, response = self.run_test(
            "Get Client Details",
            "GET",
            f"clients/{client_id}",
            200
        )
        
        return success, response

    def get_payment_stats(self) -> tuple:
        """Get payment statistics"""
        success, response = self.run_test(
            "Get Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        return success, response

    def test_full_payment_scenario(self):
        """Test full payment handling"""
        print("\n" + "="*80)
        print("🎯 TESTING FULL PAYMENT SCENARIO")
        print("="*80)
        
        # Create client with TTD 100 monthly fee
        success, client_id, client_data = self.create_test_client("Full Payment Client", 100.0)
        if not success:
            return False
            
        # Verify initial state
        initial_payment_status = client_data.get('payment_status')
        initial_amount_owed = client_data.get('amount_owed')
        initial_next_payment_date = client_data.get('next_payment_date')
        
        print(f"\n📊 INITIAL STATE:")
        print(f"   Payment Status: {initial_payment_status}")
        print(f"   Amount Owed: TTD {initial_amount_owed}")
        print(f"   Next Payment Date: {initial_next_payment_date}")
        
        if initial_payment_status != "due" or initial_amount_owed != 100.0:
            print("❌ Initial state incorrect - client should be 'due' with amount_owed=100.0")
            return False
            
        # Record full payment of TTD 100
        success, payment_response = self.record_payment(client_id, 100.0)
        if not success:
            return False
            
        print(f"\n💰 PAYMENT RECORDED:")
        print(f"   Amount Paid: TTD {payment_response.get('amount_paid')}")
        print(f"   Payment Type: {payment_response.get('payment_type')}")
        print(f"   Remaining Balance: TTD {payment_response.get('remaining_balance')}")
        print(f"   Payment Status: {payment_response.get('payment_status')}")
        print(f"   New Next Payment Date: {payment_response.get('new_next_payment_date')}")
        
        # Verify payment response
        if (payment_response.get('payment_type') != 'full' or 
            payment_response.get('remaining_balance') != 0.0 or
            payment_response.get('payment_status') != 'paid'):
            print("❌ Payment response incorrect for full payment")
            return False
            
        # Get updated client details
        success, updated_client = self.get_client_details(client_id)
        if not success:
            return False
            
        print(f"\n📊 UPDATED CLIENT STATE:")
        print(f"   Payment Status: {updated_client.get('payment_status')}")
        print(f"   Amount Owed: TTD {updated_client.get('amount_owed')}")
        print(f"   Next Payment Date: {updated_client.get('next_payment_date')}")
        
        # Verify client was updated correctly
        if (updated_client.get('payment_status') != 'paid' or 
            updated_client.get('amount_owed') != 0.0):
            print("❌ Client state not updated correctly after full payment")
            return False
            
        # Verify next payment date advanced
        if updated_client.get('next_payment_date') == initial_next_payment_date:
            print("❌ Next payment date should advance after full payment")
            return False
            
        print("✅ FULL PAYMENT SCENARIO: ALL TESTS PASSED!")
        return True

    def test_partial_payment_scenario(self):
        """Test partial payment handling"""
        print("\n" + "="*80)
        print("🎯 TESTING PARTIAL PAYMENT SCENARIO")
        print("="*80)
        
        # Create client with TTD 100 monthly fee
        success, client_id, client_data = self.create_test_client("Partial Payment Client", 100.0)
        if not success:
            return False
            
        initial_next_payment_date = client_data.get('next_payment_date')
        
        # Record first partial payment of TTD 50
        print("\n💰 RECORDING FIRST PARTIAL PAYMENT (TTD 50)")
        success, payment_response1 = self.record_payment(client_id, 50.0)
        if not success:
            return False
            
        print(f"   Payment Type: {payment_response1.get('payment_type')}")
        print(f"   Remaining Balance: TTD {payment_response1.get('remaining_balance')}")
        print(f"   Payment Status: {payment_response1.get('payment_status')}")
        
        # Verify first partial payment
        if (payment_response1.get('payment_type') != 'partial' or 
            payment_response1.get('remaining_balance') != 50.0 or
            payment_response1.get('payment_status') != 'due'):
            print("❌ First partial payment response incorrect")
            return False
            
        # Get client details after first partial payment
        success, client_after_first = self.get_client_details(client_id)
        if not success:
            return False
            
        print(f"\n📊 CLIENT STATE AFTER FIRST PARTIAL PAYMENT:")
        print(f"   Payment Status: {client_after_first.get('payment_status')}")
        print(f"   Amount Owed: TTD {client_after_first.get('amount_owed')}")
        print(f"   Next Payment Date: {client_after_first.get('next_payment_date')}")
        
        # Verify client state after first partial payment
        if (client_after_first.get('payment_status') != 'due' or 
            client_after_first.get('amount_owed') != 50.0):
            print("❌ Client state incorrect after first partial payment")
            return False
            
        # Verify next payment date did NOT advance
        if client_after_first.get('next_payment_date') != initial_next_payment_date:
            print("❌ Next payment date should NOT advance for partial payments")
            return False
            
        # Record second partial payment of TTD 30
        print("\n💰 RECORDING SECOND PARTIAL PAYMENT (TTD 30)")
        success, payment_response2 = self.record_payment(client_id, 30.0)
        if not success:
            return False
            
        print(f"   Payment Type: {payment_response2.get('payment_type')}")
        print(f"   Remaining Balance: TTD {payment_response2.get('remaining_balance')}")
        print(f"   Payment Status: {payment_response2.get('payment_status')}")
        
        # Verify second partial payment
        if (payment_response2.get('payment_type') != 'partial' or 
            payment_response2.get('remaining_balance') != 20.0 or
            payment_response2.get('payment_status') != 'due'):
            print("❌ Second partial payment response incorrect")
            return False
            
        # Get client details after second partial payment
        success, client_after_second = self.get_client_details(client_id)
        if not success:
            return False
            
        print(f"\n📊 CLIENT STATE AFTER SECOND PARTIAL PAYMENT:")
        print(f"   Payment Status: {client_after_second.get('payment_status')}")
        print(f"   Amount Owed: TTD {client_after_second.get('amount_owed')}")
        print(f"   Next Payment Date: {client_after_second.get('next_payment_date')}")
        
        # Verify client state after second partial payment
        if (client_after_second.get('payment_status') != 'due' or 
            client_after_second.get('amount_owed') != 20.0):
            print("❌ Client state incorrect after second partial payment")
            return False
            
        # Record final payment of TTD 20 (completing the payment)
        print("\n💰 RECORDING FINAL PAYMENT (TTD 20) - COMPLETING PAYMENT")
        success, payment_response3 = self.record_payment(client_id, 20.0)
        if not success:
            return False
            
        print(f"   Payment Type: {payment_response3.get('payment_type')}")
        print(f"   Remaining Balance: TTD {payment_response3.get('remaining_balance')}")
        print(f"   Payment Status: {payment_response3.get('payment_status')}")
        
        # Verify final payment
        if (payment_response3.get('payment_type') != 'full' or 
            payment_response3.get('remaining_balance') != 0.0 or
            payment_response3.get('payment_status') != 'paid'):
            print("❌ Final payment response incorrect")
            return False
            
        # Get final client details
        success, final_client = self.get_client_details(client_id)
        if not success:
            return False
            
        print(f"\n📊 FINAL CLIENT STATE:")
        print(f"   Payment Status: {final_client.get('payment_status')}")
        print(f"   Amount Owed: TTD {final_client.get('amount_owed')}")
        print(f"   Next Payment Date: {final_client.get('next_payment_date')}")
        
        # Verify final client state
        if (final_client.get('payment_status') != 'paid' or 
            final_client.get('amount_owed') != 0.0):
            print("❌ Final client state incorrect")
            return False
            
        # Verify next payment date advanced after completing payment
        if final_client.get('next_payment_date') == initial_next_payment_date:
            print("❌ Next payment date should advance after completing payment")
            return False
            
        print("✅ PARTIAL PAYMENT SCENARIO: ALL TESTS PASSED!")
        return True

    def test_overpayment_scenario(self):
        """Test overpayment handling"""
        print("\n" + "="*80)
        print("🎯 TESTING OVERPAYMENT SCENARIO")
        print("="*80)
        
        # Create client with TTD 100 monthly fee
        success, client_id, client_data = self.create_test_client("Overpayment Client", 100.0)
        if not success:
            return False
            
        initial_next_payment_date = client_data.get('next_payment_date')
        
        # Record overpayment of TTD 150
        print("\n💰 RECORDING OVERPAYMENT (TTD 150)")
        success, payment_response = self.record_payment(client_id, 150.0)
        if not success:
            return False
            
        print(f"   Payment Type: {payment_response.get('payment_type')}")
        print(f"   Remaining Balance: TTD {payment_response.get('remaining_balance')}")
        print(f"   Payment Status: {payment_response.get('payment_status')}")
        
        # Verify overpayment response
        if (payment_response.get('payment_type') != 'full' or 
            payment_response.get('remaining_balance') != 0.0 or
            payment_response.get('payment_status') != 'paid'):
            print("❌ Overpayment response incorrect")
            return False
            
        # Get client details after overpayment
        success, updated_client = self.get_client_details(client_id)
        if not success:
            return False
            
        print(f"\n📊 CLIENT STATE AFTER OVERPAYMENT:")
        print(f"   Payment Status: {updated_client.get('payment_status')}")
        print(f"   Amount Owed: TTD {updated_client.get('amount_owed')}")
        print(f"   Next Payment Date: {updated_client.get('next_payment_date')}")
        
        # Verify client state after overpayment
        if (updated_client.get('payment_status') != 'paid' or 
            updated_client.get('amount_owed') != 0.0):
            print("❌ Client state incorrect after overpayment")
            return False
            
        # Verify next payment date advanced
        if updated_client.get('next_payment_date') == initial_next_payment_date:
            print("❌ Next payment date should advance after overpayment")
            return False
            
        print("✅ OVERPAYMENT SCENARIO: ALL TESTS PASSED!")
        return True

    def test_payment_record_verification(self):
        """Test payment record storage and verification"""
        print("\n" + "="*80)
        print("🎯 TESTING PAYMENT RECORD VERIFICATION")
        print("="*80)
        
        # Get initial payment stats
        success, initial_stats = self.get_payment_stats()
        if not success:
            return False
            
        initial_revenue = initial_stats.get('total_revenue', 0)
        initial_count = initial_stats.get('payment_count', 0)
        
        print(f"\n📊 INITIAL PAYMENT STATS:")
        print(f"   Total Revenue: TTD {initial_revenue}")
        print(f"   Payment Count: {initial_count}")
        
        # Create client and record multiple payments
        success, client_id, client_data = self.create_test_client("Payment Record Client", 100.0)
        if not success:
            return False
            
        # Record partial payment
        success, partial_response = self.record_payment(client_id, 60.0)
        if not success:
            return False
            
        # Record completing payment
        success, full_response = self.record_payment(client_id, 40.0)
        if not success:
            return False
            
        # Get updated payment stats
        success, updated_stats = self.get_payment_stats()
        if not success:
            return False
            
        final_revenue = updated_stats.get('total_revenue', 0)
        final_count = updated_stats.get('payment_count', 0)
        
        print(f"\n📊 UPDATED PAYMENT STATS:")
        print(f"   Total Revenue: TTD {final_revenue}")
        print(f"   Payment Count: {final_count}")
        
        # Verify revenue calculation includes all payments
        expected_revenue = initial_revenue + 60.0 + 40.0
        expected_count = initial_count + 2
        
        if final_revenue != expected_revenue:
            print(f"❌ Revenue calculation incorrect. Expected: TTD {expected_revenue}, Got: TTD {final_revenue}")
            return False
            
        if final_count != expected_count:
            print(f"❌ Payment count incorrect. Expected: {expected_count}, Got: {final_count}")
            return False
            
        print("✅ PAYMENT RECORD VERIFICATION: ALL TESTS PASSED!")
        return True

    def test_edge_cases(self):
        """Test edge cases for partial payments"""
        print("\n" + "="*80)
        print("🎯 TESTING EDGE CASES")
        print("="*80)
        
        # Test exact amount payment after partials
        print("\n🔍 TESTING EXACT AMOUNT PAYMENT AFTER PARTIALS")
        success, client_id, client_data = self.create_test_client("Edge Case Client", 75.0)
        if not success:
            return False
            
        # Record partial payment of TTD 25
        success, response1 = self.record_payment(client_id, 25.0)
        if not success:
            return False
            
        # Record exact remaining amount (TTD 50)
        success, response2 = self.record_payment(client_id, 50.0)
        if not success:
            return False
            
        if (response2.get('payment_type') != 'full' or 
            response2.get('remaining_balance') != 0.0 or
            response2.get('payment_status') != 'paid'):
            print("❌ Exact amount payment after partial failed")
            return False
            
        # Test multiple consecutive partial payments
        print("\n🔍 TESTING MULTIPLE CONSECUTIVE PARTIAL PAYMENTS")
        success, client_id2, client_data2 = self.create_test_client("Multiple Partial Client", 200.0)
        if not success:
            return False
            
        partial_amounts = [30.0, 40.0, 50.0, 80.0]  # Total: 200.0
        expected_remaining = [170.0, 130.0, 80.0, 0.0]
        
        for i, (amount, expected) in enumerate(zip(partial_amounts, expected_remaining)):
            success, response = self.record_payment(client_id2, amount)
            if not success:
                return False
                
            if i < 3:  # First 3 should be partial
                if (response.get('payment_type') != 'partial' or 
                    response.get('remaining_balance') != expected or
                    response.get('payment_status') != 'due'):
                    print(f"❌ Multiple partial payment {i+1} failed")
                    return False
            else:  # Last should be full
                if (response.get('payment_type') != 'full' or 
                    response.get('remaining_balance') != 0.0 or
                    response.get('payment_status') != 'paid'):
                    print(f"❌ Final payment in multiple partial sequence failed")
                    return False
                    
        print("✅ EDGE CASES: ALL TESTS PASSED!")
        return True

    def cleanup_test_clients(self):
        """Clean up created test clients"""
        print(f"\n🧹 CLEANING UP {len(self.created_clients)} TEST CLIENTS...")
        
        for client_id in self.created_clients:
            try:
                success, response = self.run_test(
                    f"Delete Test Client {client_id}",
                    "DELETE",
                    f"clients/{client_id}",
                    200
                )
                if success:
                    print(f"   ✅ Deleted client {client_id}")
                else:
                    print(f"   ❌ Failed to delete client {client_id}")
            except Exception as e:
                print(f"   ❌ Error deleting client {client_id}: {str(e)}")

    def run_all_tests(self):
        """Run all partial payment tests"""
        print("🎯 PARTIAL PAYMENT HANDLING FIX - COMPREHENSIVE TESTING")
        print("="*80)
        print("Testing backend payment recording system for partial payment handling")
        print("="*80)
        
        all_tests_passed = True
        
        # Run all test scenarios
        test_methods = [
            self.test_full_payment_scenario,
            self.test_partial_payment_scenario,
            self.test_overpayment_scenario,
            self.test_payment_record_verification,
            self.test_edge_cases
        ]
        
        for test_method in test_methods:
            try:
                if not test_method():
                    all_tests_passed = False
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {str(e)}")
                all_tests_passed = False
        
        # Cleanup
        self.cleanup_test_clients()
        
        # Final summary
        print("\n" + "="*80)
        print("🎯 PARTIAL PAYMENT TESTING SUMMARY")
        print("="*80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if all_tests_passed:
            print("\n✅ ALL PARTIAL PAYMENT TESTS PASSED!")
            print("✅ Full payments: payment_status='paid', amount_owed=0.0, due_date advances")
            print("✅ Partial payments: payment_status='due', amount_owed=remaining_balance, due_date stays same")
            print("✅ Revenue tracking correctly includes all payment amounts")
            print("✅ Payment records distinguish between full/partial payments")
            print("✅ Edge cases handled correctly")
        else:
            print("\n❌ SOME PARTIAL PAYMENT TESTS FAILED!")
            print("❌ Review the failed tests above for details")
        
        return all_tests_passed

if __name__ == "__main__":
    tester = PartialPaymentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)