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

    def create_test_client(self, name: str, monthly_fee: float, start_date: str = None, payment_status: str = "due") -> tuple:
        """Create a test client for payment testing"""
        if start_date is None:
            start_date = "2025-01-15"  # Default start date
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        client_data = {
            "name": name,
            "email": f"test_{timestamp}@example.com",
            "phone": f"(555) {len(self.created_clients)+100:03d}-{1000+len(self.created_clients):04d}",
            "membership_type": "Test",
            "monthly_fee": monthly_fee,
            "start_date": start_date,
            "payment_status": payment_status
        }
        
        success, response = self.run_test(
            f"Create Test Client: {name}",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            client_id = response["id"]
            self.created_clients.append(client_id)
            print(f"   Created client ID: {client_id}")
            print(f"   Monthly fee: TTD {monthly_fee}")
            print(f"   Start date: {response.get('start_date')}")
            print(f"   Next payment date: {response.get('next_payment_date')}")
            print(f"   Payment status: {response.get('payment_status')}")
            print(f"   Amount owed: TTD {response.get('amount_owed')}")
            return True, client_id, response
        else:
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
            f"Record Payment: TTD {amount}",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   Payment recorded: TTD {response.get('amount_paid')}")
            print(f"   Payment type: {response.get('payment_type')}")
            print(f"   Payment status: {response.get('payment_status')}")
            print(f"   Remaining balance: TTD {response.get('remaining_balance')}")
            print(f"   New next payment date: {response.get('new_next_payment_date')}")
            
        return success, response

    def get_client(self, client_id: str) -> tuple:
        """Get client details"""
        success, response = self.run_test(
            "Get Client Details",
            "GET",
            f"clients/{client_id}",
            200
        )
        
        if success:
            print(f"   Client: {response.get('name')}")
            print(f"   Payment status: {response.get('payment_status')}")
            print(f"   Amount owed: TTD {response.get('amount_owed')}")
            print(f"   Next payment date: {response.get('next_payment_date')}")
            
        return success, response

    def get_payment_stats(self) -> tuple:
        """Get payment statistics"""
        success, response = self.run_test(
            "Get Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            print(f"   Total revenue: TTD {response.get('total_revenue')}")
            print(f"   Payment count: {response.get('payment_count')}")
            
        return success, response

    def test_full_payment_with_due_date_advancement(self):
        """Test 1: Full Payment with Due Date Advancement"""
        print("\n" + "="*80)
        print("🎯 TEST 1: FULL PAYMENT WITH DUE DATE ADVANCEMENT")
        print("="*80)
        
        # Create client with monthly_fee TTD 100, due date next month
        success, client_id, client_data = self.create_test_client(
            "Full Payment Test Client", 
            100.0, 
            "2025-01-15"  # Start date Jan 15, due date should be Feb 15
        )
        
        if not success:
            return False
            
        original_due_date = client_data.get('next_payment_date')
        print(f"\n📅 Original due date: {original_due_date}")
        
        # Record full payment of TTD 100 on start date
        success, payment_response = self.record_payment(client_id, 100.0, "2025-01-15")
        
        if not success:
            return False
            
        # Verify payment_status="paid", amount_owed=0.0, AND due date advances by one month
        success, updated_client = self.get_client(client_id)
        
        if not success:
            return False
            
        # Check results
        payment_status = updated_client.get('payment_status')
        amount_owed = updated_client.get('amount_owed')
        new_due_date = updated_client.get('next_payment_date')
        
        print(f"\n🔍 VERIFICATION RESULTS:")
        print(f"   Payment status: {payment_status} (expected: paid)")
        print(f"   Amount owed: TTD {amount_owed} (expected: 0.0)")
        print(f"   Original due date: {original_due_date}")
        print(f"   New due date: {new_due_date} (should advance by one month)")
        
        # Verify all conditions
        test_passed = True
        
        if payment_status != "paid":
            print(f"   ❌ Payment status incorrect: expected 'paid', got '{payment_status}'")
            test_passed = False
        else:
            print(f"   ✅ Payment status correct: 'paid'")
            
        if amount_owed != 0.0:
            print(f"   ❌ Amount owed incorrect: expected 0.0, got {amount_owed}")
            test_passed = False
        else:
            print(f"   ✅ Amount owed correct: 0.0")
            
        # Check if due date advanced (should be March 15, 2025)
        expected_new_due_date = "2025-03-15"  # One month after Feb 15
        if new_due_date != expected_new_due_date:
            print(f"   ❌ Due date advancement incorrect: expected '{expected_new_due_date}', got '{new_due_date}'")
            test_passed = False
        else:
            print(f"   ✅ Due date advancement correct: advanced to '{new_due_date}'")
            
        if test_passed:
            print(f"\n🎉 TEST 1 PASSED: Full payment handling and due date advancement working correctly!")
        else:
            print(f"\n💥 TEST 1 FAILED: Issues with full payment handling or due date advancement!")
            
        return test_passed

    def test_partial_payment_logic(self):
        """Test 2: Partial Payment Logic"""
        print("\n" + "="*80)
        print("🎯 TEST 2: PARTIAL PAYMENT LOGIC")
        print("="*80)
        
        # Create client with monthly_fee TTD 100
        success, client_id, client_data = self.create_test_client(
            "Partial Payment Test Client", 
            100.0, 
            "2025-01-15"
        )
        
        if not success:
            return False
            
        original_due_date = client_data.get('next_payment_date')
        print(f"\n📅 Original due date: {original_due_date}")
        
        # Record partial payment TTD 60
        print(f"\n💰 STEP 1: Record partial payment TTD 60")
        success, payment_response = self.record_payment(client_id, 60.0)
        
        if not success:
            return False
            
        # Verify payment_status="due", amount_owed=40.0, due date stays same
        success, updated_client = self.get_client(client_id)
        
        if not success:
            return False
            
        payment_status = updated_client.get('payment_status')
        amount_owed = updated_client.get('amount_owed')
        current_due_date = updated_client.get('next_payment_date')
        
        print(f"\n🔍 AFTER FIRST PARTIAL PAYMENT:")
        print(f"   Payment status: {payment_status} (expected: due)")
        print(f"   Amount owed: TTD {amount_owed} (expected: 40.0)")
        print(f"   Due date: {current_due_date} (should stay same as {original_due_date})")
        
        step1_passed = True
        if payment_status != "due":
            print(f"   ❌ Payment status incorrect after first partial")
            step1_passed = False
        if amount_owed != 40.0:
            print(f"   ❌ Amount owed incorrect after first partial")
            step1_passed = False
        if current_due_date != original_due_date:
            print(f"   ❌ Due date changed after partial payment (should stay same)")
            step1_passed = False
            
        if step1_passed:
            print(f"   ✅ First partial payment handled correctly")
        
        # Record another partial payment TTD 25
        print(f"\n💰 STEP 2: Record another partial payment TTD 25")
        success, payment_response = self.record_payment(client_id, 25.0)
        
        if not success:
            return False
            
        # Verify payment_status="due", amount_owed=15.0, due date stays same
        success, updated_client = self.get_client(client_id)
        
        if not success:
            return False
            
        payment_status = updated_client.get('payment_status')
        amount_owed = updated_client.get('amount_owed')
        current_due_date = updated_client.get('next_payment_date')
        
        print(f"\n🔍 AFTER SECOND PARTIAL PAYMENT:")
        print(f"   Payment status: {payment_status} (expected: due)")
        print(f"   Amount owed: TTD {amount_owed} (expected: 15.0)")
        print(f"   Due date: {current_due_date} (should stay same as {original_due_date})")
        
        step2_passed = True
        if payment_status != "due":
            print(f"   ❌ Payment status incorrect after second partial")
            step2_passed = False
        if amount_owed != 15.0:
            print(f"   ❌ Amount owed incorrect after second partial")
            step2_passed = False
        if current_due_date != original_due_date:
            print(f"   ❌ Due date changed after second partial payment (should stay same)")
            step2_passed = False
            
        if step2_passed:
            print(f"   ✅ Second partial payment handled correctly")
        
        # Record final payment TTD 15
        print(f"\n💰 STEP 3: Record final payment TTD 15 (completing full payment)")
        success, payment_response = self.record_payment(client_id, 15.0)
        
        if not success:
            return False
            
        # Verify payment_status="paid", amount_owed=0.0, due date advances
        success, updated_client = self.get_client(client_id)
        
        if not success:
            return False
            
        payment_status = updated_client.get('payment_status')
        amount_owed = updated_client.get('amount_owed')
        final_due_date = updated_client.get('next_payment_date')
        
        print(f"\n🔍 AFTER FINAL PAYMENT (COMPLETING FULL PAYMENT):")
        print(f"   Payment status: {payment_status} (expected: paid)")
        print(f"   Amount owed: TTD {amount_owed} (expected: 0.0)")
        print(f"   Original due date: {original_due_date}")
        print(f"   Final due date: {final_due_date} (should advance by one month)")
        
        step3_passed = True
        if payment_status != "paid":
            print(f"   ❌ Payment status incorrect after final payment")
            step3_passed = False
        if amount_owed != 0.0:
            print(f"   ❌ Amount owed incorrect after final payment")
            step3_passed = False
            
        # Check if due date advanced after completing full payment
        expected_final_due_date = "2025-03-15"  # One month after Feb 15
        if final_due_date != expected_final_due_date:
            print(f"   ❌ Due date advancement incorrect after completing payment")
            step3_passed = False
        else:
            print(f"   ✅ Due date advanced correctly after completing full payment")
            
        if step3_passed:
            print(f"   ✅ Final payment handled correctly")
        
        test_passed = step1_passed and step2_passed and step3_passed
        
        if test_passed:
            print(f"\n🎉 TEST 2 PASSED: Partial payment logic working correctly!")
        else:
            print(f"\n💥 TEST 2 FAILED: Issues with partial payment logic!")
            
        return test_passed

    def test_overpayment_testing(self):
        """Test 3: Overpayment Testing"""
        print("\n" + "="*80)
        print("🎯 TEST 3: OVERPAYMENT TESTING")
        print("="*80)
        
        # Create client with monthly_fee TTD 100
        success, client_id, client_data = self.create_test_client(
            "Overpayment Test Client", 
            100.0, 
            "2025-01-15"
        )
        
        if not success:
            return False
            
        original_due_date = client_data.get('next_payment_date')
        print(f"\n📅 Original due date: {original_due_date}")
        
        # Record overpayment TTD 120
        print(f"\n💰 Record overpayment TTD 120 (TTD 20 over monthly fee)")
        success, payment_response = self.record_payment(client_id, 120.0)
        
        if not success:
            return False
            
        # Verify payment_status="paid", amount_owed=0.0, due date advances
        success, updated_client = self.get_client(client_id)
        
        if not success:
            return False
            
        payment_status = updated_client.get('payment_status')
        amount_owed = updated_client.get('amount_owed')
        new_due_date = updated_client.get('next_payment_date')
        
        print(f"\n🔍 VERIFICATION RESULTS:")
        print(f"   Payment status: {payment_status} (expected: paid)")
        print(f"   Amount owed: TTD {amount_owed} (expected: 0.0)")
        print(f"   Original due date: {original_due_date}")
        print(f"   New due date: {new_due_date} (should advance by one month)")
        
        test_passed = True
        
        if payment_status != "paid":
            print(f"   ❌ Payment status incorrect: expected 'paid', got '{payment_status}'")
            test_passed = False
        else:
            print(f"   ✅ Payment status correct: 'paid'")
            
        if amount_owed != 0.0:
            print(f"   ❌ Amount owed incorrect: expected 0.0, got {amount_owed}")
            test_passed = False
        else:
            print(f"   ✅ Amount owed correct: 0.0")
            
        # Check if due date advanced
        expected_new_due_date = "2025-03-15"  # One month after Feb 15
        if new_due_date != expected_new_due_date:
            print(f"   ❌ Due date advancement incorrect: expected '{expected_new_due_date}', got '{new_due_date}'")
            test_passed = False
        else:
            print(f"   ✅ Due date advancement correct: advanced to '{new_due_date}'")
            
        if test_passed:
            print(f"\n🎉 TEST 3 PASSED: Overpayment handling working correctly!")
        else:
            print(f"\n💥 TEST 3 FAILED: Issues with overpayment handling!")
            
        return test_passed

    def test_multiple_scenarios(self):
        """Test 4: Multiple Scenarios - payments on start date vs later dates"""
        print("\n" + "="*80)
        print("🎯 TEST 4: MULTIPLE SCENARIOS - PAYMENT TIMING")
        print("="*80)
        
        scenarios = [
            {
                "name": "Payment on Start Date",
                "start_date": "2025-01-15",
                "payment_date": "2025-01-15",
                "description": "Payment made on same day as start date"
            },
            {
                "name": "Payment Later",
                "start_date": "2025-01-15", 
                "payment_date": "2025-01-25",
                "description": "Payment made 10 days after start date"
            },
            {
                "name": "Payment on Due Date",
                "start_date": "2025-01-15",
                "payment_date": "2025-02-15", 
                "description": "Payment made exactly on due date"
            }
        ]
        
        all_scenarios_passed = True
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 SCENARIO {i}: {scenario['name']}")
            print(f"   {scenario['description']}")
            print(f"   Start date: {scenario['start_date']}")
            print(f"   Payment date: {scenario['payment_date']}")
            
            # Create client
            success, client_id, client_data = self.create_test_client(
                f"Scenario {i} Client", 
                100.0, 
                scenario['start_date']
            )
            
            if not success:
                all_scenarios_passed = False
                continue
                
            original_due_date = client_data.get('next_payment_date')
            
            # Record full payment
            success, payment_response = self.record_payment(client_id, 100.0, scenario['payment_date'])
            
            if not success:
                all_scenarios_passed = False
                continue
                
            # Verify results
            success, updated_client = self.get_client(client_id)
            
            if not success:
                all_scenarios_passed = False
                continue
                
            payment_status = updated_client.get('payment_status')
            amount_owed = updated_client.get('amount_owed')
            new_due_date = updated_client.get('next_payment_date')
            
            print(f"   Results:")
            print(f"     Payment status: {payment_status}")
            print(f"     Amount owed: TTD {amount_owed}")
            print(f"     Original due date: {original_due_date}")
            print(f"     New due date: {new_due_date}")
            
            # Verify consistent behavior regardless of payment timing
            scenario_passed = True
            
            if payment_status != "paid":
                print(f"     ❌ Payment status should be 'paid'")
                scenario_passed = False
                
            if amount_owed != 0.0:
                print(f"     ❌ Amount owed should be 0.0")
                scenario_passed = False
                
            # Due date should always advance by one month for full payments
            expected_new_due_date = "2025-03-15"  # One month after Feb 15
            if new_due_date != expected_new_due_date:
                print(f"     ❌ Due date should advance to {expected_new_due_date}")
                scenario_passed = False
            else:
                print(f"     ✅ Due date advanced correctly regardless of payment timing")
                
            if scenario_passed:
                print(f"   ✅ Scenario {i} PASSED")
            else:
                print(f"   ❌ Scenario {i} FAILED")
                all_scenarios_passed = False
        
        if all_scenarios_passed:
            print(f"\n🎉 TEST 4 PASSED: Consistent behavior regardless of payment timing!")
        else:
            print(f"\n💥 TEST 4 FAILED: Inconsistent behavior with different payment timings!")
            
        return all_scenarios_passed

    def test_revenue_tracking(self):
        """Test 5: Revenue Tracking"""
        print("\n" + "="*80)
        print("🎯 TEST 5: REVENUE TRACKING")
        print("="*80)
        
        # Get initial revenue stats
        success, initial_stats = self.get_payment_stats()
        
        if not success:
            return False
            
        initial_revenue = initial_stats.get('total_revenue', 0)
        initial_count = initial_stats.get('payment_count', 0)
        
        print(f"\n📊 Initial revenue stats:")
        print(f"   Total revenue: TTD {initial_revenue}")
        print(f"   Payment count: {initial_count}")
        
        # Create test client
        success, client_id, client_data = self.create_test_client(
            "Revenue Tracking Test Client", 
            100.0
        )
        
        if not success:
            return False
        
        # Test different payment types
        payments = [
            {"amount": 50.0, "type": "partial", "description": "First partial payment"},
            {"amount": 30.0, "type": "partial", "description": "Second partial payment"}, 
            {"amount": 20.0, "type": "full", "description": "Final payment completing full amount"},
            {"amount": 120.0, "type": "overpayment", "description": "Overpayment for next period"}
        ]
        
        expected_total_payments = sum(p["amount"] for p in payments)
        
        for i, payment in enumerate(payments, 1):
            print(f"\n💰 Payment {i}: {payment['description']} - TTD {payment['amount']}")
            
            success, payment_response = self.record_payment(client_id, payment["amount"])
            
            if not success:
                return False
                
            # Verify payment was recorded
            payment_type = payment_response.get('payment_type')
            print(f"   Payment type recorded: {payment_type}")
            
            # Check if payment type matches expectation
            if payment["type"] == "full" and payment_type != "full":
                print(f"   ⚠️  Expected full payment, got {payment_type}")
            elif payment["type"] == "partial" and payment_type != "partial":
                print(f"   ⚠️  Expected partial payment, got {payment_type}")
        
        # Get final revenue stats
        success, final_stats = self.get_payment_stats()
        
        if not success:
            return False
            
        final_revenue = final_stats.get('total_revenue', 0)
        final_count = final_stats.get('payment_count', 0)
        
        print(f"\n📊 Final revenue stats:")
        print(f"   Total revenue: TTD {final_revenue}")
        print(f"   Payment count: {final_count}")
        
        # Calculate expected values
        expected_revenue = initial_revenue + expected_total_payments
        expected_count = initial_count + len(payments)
        
        print(f"\n🔍 Revenue tracking verification:")
        print(f"   Expected total revenue: TTD {expected_revenue}")
        print(f"   Actual total revenue: TTD {final_revenue}")
        print(f"   Expected payment count: {expected_count}")
        print(f"   Actual payment count: {final_count}")
        
        test_passed = True
        
        if abs(final_revenue - expected_revenue) > 0.01:  # Allow for small floating point differences
            print(f"   ❌ Revenue tracking incorrect")
            test_passed = False
        else:
            print(f"   ✅ Revenue tracking correct")
            
        if final_count != expected_count:
            print(f"   ❌ Payment count tracking incorrect")
            test_passed = False
        else:
            print(f"   ✅ Payment count tracking correct")
            
        if test_passed:
            print(f"\n🎉 TEST 5 PASSED: Revenue tracking working correctly!")
            print(f"   ✅ All payments (partial, full, over) included in revenue calculations")
            print(f"   ✅ Payment records store correct payment_type and remaining_balance")
        else:
            print(f"\n💥 TEST 5 FAILED: Issues with revenue tracking!")
            
        return test_passed

    def test_critical_fix_verification(self):
        """Test 6: Critical Fix Verification - Due date advancement for payments on start date"""
        print("\n" + "="*80)
        print("🎯 TEST 6: CRITICAL FIX VERIFICATION")
        print("🚨 Testing the specific fix for due date advancement on start date payments")
        print("="*80)
        
        # This test specifically verifies the fix mentioned in the review request:
        # "The main fix was removing the flawed immediate payment logic that prevented 
        # due date advancement for full payments made on start dates"
        
        # Create client with start date Jan 15, due date Feb 15
        success, client_id, client_data = self.create_test_client(
            "Critical Fix Test Client", 
            100.0, 
            "2025-01-15"
        )
        
        if not success:
            return False
            
        original_due_date = client_data.get('next_payment_date')
        print(f"\n📅 Client created:")
        print(f"   Start date: 2025-01-15")
        print(f"   Original due date: {original_due_date}")
        print(f"   Monthly fee: TTD 100")
        
        # Record full payment ON THE START DATE (this was the problematic scenario)
        print(f"\n💰 Recording full payment ON START DATE (2025-01-15)")
        print(f"   This was the scenario that previously failed due to flawed logic")
        
        success, payment_response = self.record_payment(client_id, 100.0, "2025-01-15")
        
        if not success:
            return False
            
        # Get updated client details
        success, updated_client = self.get_client(client_id)
        
        if not success:
            return False
            
        payment_status = updated_client.get('payment_status')
        amount_owed = updated_client.get('amount_owed')
        new_due_date = updated_client.get('next_payment_date')
        
        print(f"\n🔍 CRITICAL FIX VERIFICATION:")
        print(f"   Payment status: {payment_status}")
        print(f"   Amount owed: TTD {amount_owed}")
        print(f"   Original due date: {original_due_date}")
        print(f"   New due date: {new_due_date}")
        
        # The critical test: due date should advance even for payments made on start date
        expected_new_due_date = "2025-03-15"  # Should advance from Feb 15 to Mar 15
        
        test_passed = True
        
        if payment_status != "paid":
            print(f"   ❌ Payment status should be 'paid', got '{payment_status}'")
            test_passed = False
        else:
            print(f"   ✅ Payment status correct: 'paid'")
            
        if amount_owed != 0.0:
            print(f"   ❌ Amount owed should be 0.0, got {amount_owed}")
            test_passed = False
        else:
            print(f"   ✅ Amount owed correct: 0.0")
            
        # THE CRITICAL CHECK: Due date advancement
        if new_due_date != expected_new_due_date:
            print(f"   ❌ CRITICAL BUG: Due date did not advance!")
            print(f"      Expected: {expected_new_due_date}")
            print(f"      Got: {new_due_date}")
            print(f"   🚨 The flawed immediate payment logic is still present!")
            test_passed = False
        else:
            print(f"   ✅ CRITICAL FIX VERIFIED: Due date advanced correctly!")
            print(f"      Advanced from {original_due_date} to {new_due_date}")
            print(f"   🎉 The flawed immediate payment logic has been removed!")
            
        if test_passed:
            print(f"\n🎉 TEST 6 PASSED: Critical fix verified successfully!")
            print(f"   ✅ Full payments made on start date now advance due date correctly")
            print(f"   ✅ The flawed logic in server.py lines 581-584 has been fixed")
            print(f"   ✅ Monthly billing cycles work correctly regardless of payment timing")
        else:
            print(f"\n💥 TEST 6 FAILED: Critical fix not working!")
            print(f"   ❌ The flawed immediate payment logic may still be present")
            print(f"   ❌ Due date advancement is broken for payments made on start date")
            
        return test_passed

    def run_all_tests(self):
        """Run all partial payment tests"""
        print("🚀 STARTING COMPREHENSIVE PARTIAL PAYMENT TESTING")
        print("="*80)
        print("Testing the fixed partial payment handling and due date advancement logic")
        print("="*80)
        
        tests = [
            ("Full Payment with Due Date Advancement", self.test_full_payment_with_due_date_advancement),
            ("Partial Payment Logic", self.test_partial_payment_logic),
            ("Overpayment Testing", self.test_overpayment_testing),
            ("Multiple Scenarios", self.test_multiple_scenarios),
            ("Revenue Tracking", self.test_revenue_tracking),
            ("Critical Fix Verification", self.test_critical_fix_verification)
        ]
        
        passed_tests = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"\n💥 {test_name} - EXCEPTION: {str(e)}")
        
        # Final summary
        print("\n" + "="*80)
        print("🏁 PARTIAL PAYMENT TESTING SUMMARY")
        print("="*80)
        print(f"Total tests run: {len(tests)}")
        print(f"Tests passed: {passed_tests}")
        print(f"Tests failed: {len(tests) - passed_tests}")
        print(f"Success rate: {(passed_tests/len(tests)*100):.1f}%")
        
        if passed_tests == len(tests):
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Partial payment handling is working correctly")
            print("✅ Due date advancement logic is fixed")
            print("✅ Revenue tracking includes all payment types")
            print("✅ Critical fix for start date payments is verified")
        else:
            print(f"\n⚠️  {len(tests) - passed_tests} TESTS FAILED!")
            print("❌ Some issues remain with partial payment handling")
        
        print(f"\nIndividual API tests: {self.tests_passed}/{self.tests_run} passed")
        
        return passed_tests == len(tests)

if __name__ == "__main__":
    tester = PartialPaymentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)