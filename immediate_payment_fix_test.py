#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class ImmediatePaymentFixTester:
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

    def test_scenario_1_immediate_payment(self):
        """
        SCENARIO 1 (Immediate Payment - Already Confirmed Working):
        1. Create client with start_date "2025-01-15" 
        2. Verify initial next_payment_date is "2025-02-15"
        3. Record payment with payment_date "2025-01-15" (same day - immediate payment)
        4. Verify next_payment_date stays "2025-02-15" (does NOT advance)
        """
        print("\n" + "="*80)
        print("🎯 SCENARIO 1: IMMEDIATE PAYMENT (SAME DAY AS JOIN)")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Step 1: Create client with start_date "2025-01-15"
        client_data = {
            "name": f"Immediate Payment Test {timestamp}",
            "email": f"immediate_test_{timestamp}@example.com",
            "phone": "(555) 100-0001",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": "2025-01-15",
            "payment_status": "due"
        }
        
        success1, response1 = self.run_test(
            "1.1 Create Client with Start Date 2025-01-15",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1 or "id" not in response1:
            print("❌ Failed to create client - aborting scenario 1")
            return False
            
        client_id = response1["id"]
        self.created_clients.append(client_id)
        
        # Step 2: Verify initial next_payment_date is "2025-02-15"
        initial_next_payment = response1.get('next_payment_date')
        expected_initial_payment = "2025-02-15"
        
        print(f"   📅 Start Date: {response1.get('start_date')}")
        print(f"   💰 Initial Next Payment Date: {initial_next_payment}")
        print(f"   🎯 Expected Initial Payment Date: {expected_initial_payment}")
        
        if str(initial_next_payment) != expected_initial_payment:
            print(f"❌ Initial payment date calculation incorrect!")
            return False
        
        print("   ✅ Initial payment date calculation CORRECT!")
        
        # Step 3: Record immediate payment on same day (2025-01-15)
        payment_data = {
            "client_id": client_id,
            "amount_paid": 55.00,
            "payment_date": "2025-01-15",  # Same day as start_date - IMMEDIATE PAYMENT
            "payment_method": "Cash",
            "notes": "Immediate payment on join date - should NOT advance due date"
        }
        
        success2, response2 = self.run_test(
            "1.2 Record Immediate Payment (Same Day as Join)",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success2:
            print("❌ Failed to record immediate payment")
            return False
        
        # Step 4: Verify next_payment_date stays "2025-02-15" (does NOT advance)
        new_next_payment = response2.get('new_next_payment_date')
        expected_after_immediate = "February 15, 2025"  # Should stay the same
        
        print(f"   💰 Next Payment Date After Immediate Payment: {new_next_payment}")
        print(f"   🎯 Expected After Immediate Payment: {expected_after_immediate}")
        
        if str(new_next_payment) != expected_after_immediate:
            print(f"❌ IMMEDIATE PAYMENT LOGIC FAILED!")
            print(f"   Expected: {expected_after_immediate}")
            print(f"   Got: {new_next_payment}")
            return False
        
        print("   ✅ IMMEDIATE PAYMENT LOGIC WORKING CORRECTLY!")
        print("   ✅ Payment on join date covers current month, due date stays same")
        
        return True

    def test_scenario_2_regular_monthly_payment(self):
        """
        SCENARIO 2 (Regular Monthly Payment):
        1. Create client with start_date "2025-01-15" 
        2. Verify initial next_payment_date is "2025-02-15"
        3. Record payment with payment_date "2025-02-20" (after due date - regular payment)
        4. Verify next_payment_date correctly advances to "2025-03-15"
        """
        print("\n" + "="*80)
        print("🎯 SCENARIO 2: REGULAR MONTHLY PAYMENT (AFTER DUE DATE)")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Step 1: Create client with start_date "2025-01-15"
        client_data = {
            "name": f"Regular Payment Test {timestamp}",
            "email": f"regular_test_{timestamp}@example.com",
            "phone": "(555) 200-0002",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-01-15",
            "payment_status": "due"
        }
        
        success1, response1 = self.run_test(
            "2.1 Create Client with Start Date 2025-01-15",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1 or "id" not in response1:
            print("❌ Failed to create client - aborting scenario 2")
            return False
            
        client_id = response1["id"]
        self.created_clients.append(client_id)
        
        # Step 2: Verify initial next_payment_date is "2025-02-15"
        initial_next_payment = response1.get('next_payment_date')
        expected_initial_payment = "2025-02-15"
        
        print(f"   📅 Start Date: {response1.get('start_date')}")
        print(f"   💰 Initial Next Payment Date: {initial_next_payment}")
        print(f"   🎯 Expected Initial Payment Date: {expected_initial_payment}")
        
        if str(initial_next_payment) != expected_initial_payment:
            print(f"❌ Initial payment date calculation incorrect!")
            return False
        
        print("   ✅ Initial payment date calculation CORRECT!")
        
        # Step 3: Record regular payment after due date (2025-02-20)
        payment_data = {
            "client_id": client_id,
            "amount_paid": 75.00,
            "payment_date": "2025-02-20",  # 5 days after due date - REGULAR PAYMENT
            "payment_method": "Credit Card",
            "notes": "Regular payment after due date - should advance due date"
        }
        
        success2, response2 = self.run_test(
            "2.2 Record Regular Payment (After Due Date)",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success2:
            print("❌ Failed to record regular payment")
            return False
        
        # Step 4: Verify next_payment_date advances to "2025-03-15"
        new_next_payment = response2.get('new_next_payment_date')
        expected_after_regular = "March 15, 2025"  # Should advance by one month
        
        print(f"   💰 Next Payment Date After Regular Payment: {new_next_payment}")
        print(f"   🎯 Expected After Regular Payment: {expected_after_regular}")
        
        if str(new_next_payment) != expected_after_regular:
            print(f"❌ REGULAR PAYMENT LOGIC FAILED!")
            print(f"   Expected: {expected_after_regular}")
            print(f"   Got: {new_next_payment}")
            return False
        
        print("   ✅ REGULAR PAYMENT LOGIC WORKING CORRECTLY!")
        print("   ✅ Payment after due date advances to next month")
        
        return True

    def test_scenario_3_early_payment(self):
        """
        SCENARIO 3 (Early Payment):
        1. Create client with start_date "2025-01-15"
        2. Verify initial next_payment_date is "2025-02-15"  
        3. Record payment with payment_date "2025-02-10" (before due date but not immediate)
        4. Verify next_payment_date correctly advances to "2025-03-15"
        """
        print("\n" + "="*80)
        print("🎯 SCENARIO 3: EARLY PAYMENT (BEFORE DUE DATE)")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Step 1: Create client with start_date "2025-01-15"
        client_data = {
            "name": f"Early Payment Test {timestamp}",
            "email": f"early_test_{timestamp}@example.com",
            "phone": "(555) 300-0003",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": "2025-01-15",
            "payment_status": "due"
        }
        
        success1, response1 = self.run_test(
            "3.1 Create Client with Start Date 2025-01-15",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1 or "id" not in response1:
            print("❌ Failed to create client - aborting scenario 3")
            return False
            
        client_id = response1["id"]
        self.created_clients.append(client_id)
        
        # Step 2: Verify initial next_payment_date is "2025-02-15"
        initial_next_payment = response1.get('next_payment_date')
        expected_initial_payment = "2025-02-15"
        
        print(f"   📅 Start Date: {response1.get('start_date')}")
        print(f"   💰 Initial Next Payment Date: {initial_next_payment}")
        print(f"   🎯 Expected Initial Payment Date: {expected_initial_payment}")
        
        if str(initial_next_payment) != expected_initial_payment:
            print(f"❌ Initial payment date calculation incorrect!")
            return False
        
        print("   ✅ Initial payment date calculation CORRECT!")
        
        # Step 3: Record early payment before due date (2025-02-10)
        payment_data = {
            "client_id": client_id,
            "amount_paid": 100.00,
            "payment_date": "2025-02-10",  # 5 days before due date - EARLY PAYMENT
            "payment_method": "Bank Transfer",
            "notes": "Early payment before due date - should advance due date"
        }
        
        success2, response2 = self.run_test(
            "3.2 Record Early Payment (Before Due Date)",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success2:
            print("❌ Failed to record early payment")
            return False
        
        # Step 4: Verify next_payment_date advances to "2025-03-15"
        new_next_payment = response2.get('new_next_payment_date')
        expected_after_early = "March 15, 2025"  # Should advance by one month
        
        print(f"   💰 Next Payment Date After Early Payment: {new_next_payment}")
        print(f"   🎯 Expected After Early Payment: {expected_after_early}")
        
        if str(new_next_payment) != expected_after_early:
            print(f"❌ EARLY PAYMENT LOGIC FAILED!")
            print(f"   Expected: {expected_after_early}")
            print(f"   Got: {new_next_payment}")
            return False
        
        print("   ✅ EARLY PAYMENT LOGIC WORKING CORRECTLY!")
        print("   ✅ Payment before due date advances to next month")
        
        return True

    def test_scenario_4_multiple_payments(self):
        """
        SCENARIO 4 (Multiple Payments):
        1. Create client with start_date "2025-01-15"
        2. Record immediate payment on "2025-01-15" → should stay "2025-02-15"
        3. Record regular payment on "2025-02-20" → should advance to "2025-03-15"
        4. Record regular payment on "2025-03-25" → should advance to "2025-04-15"
        """
        print("\n" + "="*80)
        print("🎯 SCENARIO 4: MULTIPLE CONSECUTIVE PAYMENTS")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Step 1: Create client with start_date "2025-01-15"
        client_data = {
            "name": f"Multiple Payment Test {timestamp}",
            "email": f"multiple_test_{timestamp}@example.com",
            "phone": "(555) 400-0004",
            "membership_type": "VIP",
            "monthly_fee": 150.00,
            "start_date": "2025-01-15",
            "payment_status": "due"
        }
        
        success1, response1 = self.run_test(
            "4.1 Create Client with Start Date 2025-01-15",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1 or "id" not in response1:
            print("❌ Failed to create client - aborting scenario 4")
            return False
            
        client_id = response1["id"]
        self.created_clients.append(client_id)
        
        # Verify initial next_payment_date is "2025-02-15"
        initial_next_payment = response1.get('next_payment_date')
        expected_initial_payment = "2025-02-15"
        
        print(f"   📅 Start Date: {response1.get('start_date')}")
        print(f"   💰 Initial Next Payment Date: {initial_next_payment}")
        
        if str(initial_next_payment) != expected_initial_payment:
            print(f"❌ Initial payment date calculation incorrect!")
            return False
        
        print("   ✅ Initial payment date calculation CORRECT!")
        
        # Step 2: Record immediate payment on join date (2025-01-15)
        payment_data_1 = {
            "client_id": client_id,
            "amount_paid": 150.00,
            "payment_date": "2025-01-15",  # Same day as start_date - IMMEDIATE PAYMENT
            "payment_method": "Cash",
            "notes": "Payment #1: Immediate payment on join date"
        }
        
        success2, response2 = self.run_test(
            "4.2 Record Payment #1 (Immediate - Same Day as Join)",
            "POST",
            "payments/record",
            200,
            payment_data_1
        )
        
        if not success2:
            print("❌ Failed to record payment #1")
            return False
        
        # Verify next_payment_date stays "2025-02-15"
        payment1_next_date = response2.get('new_next_payment_date')
        expected_after_payment1 = "February 15, 2025"
        
        print(f"   💰 After Payment #1: {payment1_next_date}")
        print(f"   🎯 Expected After Payment #1: {expected_after_payment1}")
        
        if str(payment1_next_date) != expected_after_payment1:
            print(f"❌ Payment #1 logic failed!")
            return False
        
        print("   ✅ Payment #1 (Immediate) - Due date stays same ✓")
        
        # Step 3: Record regular payment on "2025-02-20"
        payment_data_2 = {
            "client_id": client_id,
            "amount_paid": 150.00,
            "payment_date": "2025-02-20",  # After due date - REGULAR PAYMENT
            "payment_method": "Credit Card",
            "notes": "Payment #2: Regular payment after due date"
        }
        
        success3, response3 = self.run_test(
            "4.3 Record Payment #2 (Regular - After Due Date)",
            "POST",
            "payments/record",
            200,
            payment_data_2
        )
        
        if not success3:
            print("❌ Failed to record payment #2")
            return False
        
        # Verify next_payment_date advances to "2025-03-15"
        payment2_next_date = response3.get('new_next_payment_date')
        expected_after_payment2 = "March 15, 2025"
        
        print(f"   💰 After Payment #2: {payment2_next_date}")
        print(f"   🎯 Expected After Payment #2: {expected_after_payment2}")
        
        if str(payment2_next_date) != expected_after_payment2:
            print(f"❌ Payment #2 logic failed!")
            return False
        
        print("   ✅ Payment #2 (Regular) - Due date advances to next month ✓")
        
        # Step 4: Record regular payment on "2025-03-25"
        payment_data_3 = {
            "client_id": client_id,
            "amount_paid": 150.00,
            "payment_date": "2025-03-25",  # After due date - REGULAR PAYMENT
            "payment_method": "Bank Transfer",
            "notes": "Payment #3: Regular payment after due date"
        }
        
        success4, response4 = self.run_test(
            "4.4 Record Payment #3 (Regular - After Due Date)",
            "POST",
            "payments/record",
            200,
            payment_data_3
        )
        
        if not success4:
            print("❌ Failed to record payment #3")
            return False
        
        # Verify next_payment_date advances to "2025-04-15"
        payment3_next_date = response4.get('new_next_payment_date')
        expected_after_payment3 = "April 15, 2025"
        
        print(f"   💰 After Payment #3: {payment3_next_date}")
        print(f"   🎯 Expected After Payment #3: {expected_after_payment3}")
        
        if str(payment3_next_date) != expected_after_payment3:
            print(f"❌ Payment #3 logic failed!")
            return False
        
        print("   ✅ Payment #3 (Regular) - Due date advances to next month ✓")
        
        print("\n   🎉 MULTIPLE PAYMENTS SCENARIO COMPLETE!")
        print("   ✅ Immediate payment (same day) - Due date stays same")
        print("   ✅ Regular payment #1 - Due date advances")
        print("   ✅ Regular payment #2 - Due date advances")
        print("   ✅ Consistent monthly billing cycle maintained")
        
        return True

    def test_regression_normal_payment_advancement(self):
        """
        REGRESSION TEST: Ensure normal payment advancement still works correctly
        Test various payment scenarios to ensure no regressions
        """
        print("\n" + "="*80)
        print("🎯 REGRESSION TEST: NORMAL PAYMENT ADVANCEMENT")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Test Case 1: Payment on exact due date
        client_data_1 = {
            "name": f"Regression Test 1 {timestamp}",
            "email": f"regression1_{timestamp}@example.com",
            "phone": "(555) 500-0001",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": "2025-01-10",
            "payment_status": "due"
        }
        
        success1, response1 = self.run_test(
            "R1.1 Create Client (Due Date Payment Test)",
            "POST",
            "clients",
            200,
            client_data_1
        )
        
        if success1 and "id" in response1:
            client_id_1 = response1["id"]
            self.created_clients.append(client_id_1)
            
            # Payment on exact due date
            payment_data_1 = {
                "client_id": client_id_1,
                "amount_paid": 55.00,
                "payment_date": "2025-02-09",  # Exact due date
                "payment_method": "Cash",
                "notes": "Payment on exact due date"
            }
            
            success1b, response1b = self.run_test(
                "R1.2 Payment on Exact Due Date",
                "POST",
                "payments/record",
                200,
                payment_data_1
            )
            
            if success1b:
                next_payment = response1b.get('new_next_payment_date')
                expected = "March 10, 2025"  # Should advance (Feb 10 + 1 month = Mar 10)
                
                if str(next_payment) == expected:
                    print("   ✅ Payment on due date advances correctly")
                else:
                    print(f"   ❌ Payment on due date failed: Expected {expected}, Got {next_payment}")
                    return False
        
        # Test Case 2: Late payment (after due date)
        client_data_2 = {
            "name": f"Regression Test 2 {timestamp}",
            "email": f"regression2_{timestamp}@example.com",
            "phone": "(555) 500-0002",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-01-20",
            "payment_status": "due"
        }
        
        success2, response2 = self.run_test(
            "R2.1 Create Client (Late Payment Test)",
            "POST",
            "clients",
            200,
            client_data_2
        )
        
        if success2 and "id" in response2:
            client_id_2 = response2["id"]
            self.created_clients.append(client_id_2)
            
            # Late payment
            payment_data_2 = {
                "client_id": client_id_2,
                "amount_paid": 75.00,
                "payment_date": "2025-03-01",  # 10 days late
                "payment_method": "Credit Card",
                "notes": "Late payment - 10 days after due date"
            }
            
            success2b, response2b = self.run_test(
                "R2.2 Late Payment (10 Days After Due)",
                "POST",
                "payments/record",
                200,
                payment_data_2
            )
            
            if success2b:
                next_payment = response2b.get('new_next_payment_date')
                expected = "March 20, 2025"  # Should advance from original due date (Feb 20 + 1 month = Mar 20)
                
                if str(next_payment) == expected:
                    print("   ✅ Late payment advances correctly")
                else:
                    print(f"   ❌ Late payment failed: Expected {expected}, Got {next_payment}")
                    return False
        
        print("   ✅ REGRESSION TESTS PASSED - Normal payment advancement working")
        return True

    def test_edge_cases_immediate_payment_detection(self):
        """
        Test edge cases for immediate payment detection logic
        """
        print("\n" + "="*80)
        print("🎯 EDGE CASES: IMMEDIATE PAYMENT DETECTION")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Edge Case 1: Payment one day after join (should be regular, not immediate)
        client_data_1 = {
            "name": f"Edge Case 1 {timestamp}",
            "email": f"edge1_{timestamp}@example.com",
            "phone": "(555) 600-0001",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": "2025-01-15",
            "payment_status": "due"
        }
        
        success1, response1 = self.run_test(
            "E1.1 Create Client (One Day After Join Test)",
            "POST",
            "clients",
            200,
            client_data_1
        )
        
        if success1 and "id" in response1:
            client_id_1 = response1["id"]
            self.created_clients.append(client_id_1)
            
            # Payment one day after join
            payment_data_1 = {
                "client_id": client_id_1,
                "amount_paid": 55.00,
                "payment_date": "2025-01-16",  # One day after join
                "payment_method": "Cash",
                "notes": "Payment one day after join - should be regular payment"
            }
            
            success1b, response1b = self.run_test(
                "E1.2 Payment One Day After Join",
                "POST",
                "payments/record",
                200,
                payment_data_1
            )
            
            if success1b:
                next_payment = response1b.get('new_next_payment_date')
                expected = "March 15, 2025"  # Should advance (regular payment)
                
                if str(next_payment) == expected:
                    print("   ✅ Payment one day after join treated as regular payment")
                else:
                    print(f"   ❌ Payment one day after join failed: Expected {expected}, Got {next_payment}")
                    return False
        
        # Edge Case 2: Payment exactly on due date (should be regular)
        client_data_2 = {
            "name": f"Edge Case 2 {timestamp}",
            "email": f"edge2_{timestamp}@example.com",
            "phone": "(555) 600-0002",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-01-15",
            "payment_status": "due"
        }
        
        success2, response2 = self.run_test(
            "E2.1 Create Client (Payment on Due Date Test)",
            "POST",
            "clients",
            200,
            client_data_2
        )
        
        if success2 and "id" in response2:
            client_id_2 = response2["id"]
            self.created_clients.append(client_id_2)
            
            # Payment exactly on due date
            payment_data_2 = {
                "client_id": client_id_2,
                "amount_paid": 75.00,
                "payment_date": "2025-02-15",  # Exactly on due date
                "payment_method": "Credit Card",
                "notes": "Payment exactly on due date - should be regular payment"
            }
            
            success2b, response2b = self.run_test(
                "E2.2 Payment Exactly on Due Date",
                "POST",
                "payments/record",
                200,
                payment_data_2
            )
            
            if success2b:
                next_payment = response2b.get('new_next_payment_date')
                expected = "March 15, 2025"  # Should advance (regular payment)
                
                if str(next_payment) == expected:
                    print("   ✅ Payment on due date treated as regular payment")
                else:
                    print(f"   ❌ Payment on due date failed: Expected {expected}, Got {next_payment}")
                    return False
        
        print("   ✅ EDGE CASES PASSED - Immediate payment detection working correctly")
        return True

    def cleanup_test_clients(self):
        """Clean up test clients created during testing"""
        print("\n" + "="*80)
        print("🧹 CLEANING UP TEST CLIENTS")
        print("="*80)
        
        cleanup_success = True
        for client_id in self.created_clients:
            success, response = self.run_test(
                f"Cleanup Client {client_id[:8]}...",
                "DELETE",
                f"clients/{client_id}",
                200
            )
            if not success:
                cleanup_success = False
        
        if cleanup_success:
            print(f"   ✅ Successfully cleaned up {len(self.created_clients)} test clients")
        else:
            print(f"   ⚠️  Some cleanup operations failed")
        
        return cleanup_success

    def run_all_tests(self):
        """Run all immediate payment fix tests"""
        print("\n" + "🎯" * 40)
        print("COMPREHENSIVE IMMEDIATE PAYMENT FIX TESTING")
        print("🎯" * 40)
        
        test_results = []
        
        # Run all test scenarios
        test_results.append(("Scenario 1: Immediate Payment", self.test_scenario_1_immediate_payment()))
        test_results.append(("Scenario 2: Regular Monthly Payment", self.test_scenario_2_regular_monthly_payment()))
        test_results.append(("Scenario 3: Early Payment", self.test_scenario_3_early_payment()))
        test_results.append(("Scenario 4: Multiple Payments", self.test_scenario_4_multiple_payments()))
        test_results.append(("Regression: Normal Payment Advancement", self.test_regression_normal_payment_advancement()))
        test_results.append(("Edge Cases: Immediate Payment Detection", self.test_edge_cases_immediate_payment_detection()))
        
        # Cleanup
        test_results.append(("Cleanup Test Clients", self.cleanup_test_clients()))
        
        # Print final summary
        print("\n" + "="*80)
        print("🎯 IMMEDIATE PAYMENT FIX TEST SUMMARY")
        print("="*80)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}: {test_name}")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! IMMEDIATE PAYMENT FIX IS WORKING CORRECTLY!")
            print("✅ Immediate payments (same day as join) do not advance due date")
            print("✅ Regular payments (after join date) advance due date normally")
            print("✅ Multiple payment scenarios work correctly")
            print("✅ No regressions in normal payment functionality")
            print("✅ Edge cases handled properly")
        else:
            print(f"\n❌ {total_tests - passed_tests} TESTS FAILED - IMMEDIATE PAYMENT FIX NEEDS ATTENTION")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    print("🚀 Starting Immediate Payment Fix Comprehensive Testing...")
    
    tester = ImmediatePaymentFixTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)