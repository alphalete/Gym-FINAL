#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class PaymentDateFixTester:
    def __init__(self, base_url="https://442a58e4-b64f-4824-924a-0c12436c79ea.preview.emergentagent.com"):
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

    def test_payment_date_calculation_fix(self):
        """
        CRITICAL TEST: Test the exact scenario from the review request
        
        SCENARIO TO TEST:
        1. Create client with start_date "2025-01-15" and payment_status="due"
        2. Verify next_payment_date is correctly "2025-02-15"
        3. Record payment with payment_date "2025-02-20" (5 days late)
        4. Verify new next_payment_date is "2025-03-15" (NOT "2025-03-20")
        
        EXPECTED RESULTS:
        - ✅ Consistent billing cycles: Jan 15th → Feb 15th → Mar 15th (regardless of payment timing)
        - ✅ Late payments don't shift future billing dates
        - ✅ Professional billing experience with predictable due dates
        - ✅ No billing cycle drift
        """
        print("\n🎯 CRITICAL PAYMENT DATE CALCULATION FIX TEST")
        print("=" * 80)
        print("Testing the exact scenario from the review request:")
        print("1. Create client with start_date '2025-01-15' and payment_status='due'")
        print("2. Verify next_payment_date is correctly '2025-02-15'")
        print("3. Record payment with payment_date '2025-02-20' (5 days late)")
        print("4. Verify new next_payment_date is '2025-03-15' (NOT '2025-03-20')")
        print("=" * 80)
        
        # Step 1: Create client with start_date "2025-01-15" and payment_status="due"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Payment Date Fix Test Client",
            "email": f"payment_fix_test_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": "2025-01-15",
            "payment_status": "due"
        }
        
        success1, response1 = self.run_test(
            "STEP 1: Create client with start_date '2025-01-15' and payment_status='due'",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1 or "id" not in response1:
            print("❌ CRITICAL FAILURE: Could not create test client")
            return False
            
        self.test_client_id = response1["id"]
        print(f"   ✅ Created test client ID: {self.test_client_id}")
        print(f"   📅 Start date: {response1.get('start_date')}")
        print(f"   💰 Next payment date: {response1.get('next_payment_date')}")
        print(f"   📋 Payment status: {response1.get('payment_status')}")
        
        # Step 2: Verify next_payment_date is correctly "2025-02-15"
        expected_initial_payment_date = "2025-02-15"
        actual_initial_payment_date = str(response1.get('next_payment_date'))
        
        print(f"\n🔍 STEP 2: Verify initial payment date calculation")
        print(f"   Expected: {expected_initial_payment_date}")
        print(f"   Actual: {actual_initial_payment_date}")
        
        if actual_initial_payment_date == expected_initial_payment_date:
            print("   ✅ STEP 2 PASSED: Initial payment date is correct (2025-02-15)")
        else:
            print("   ❌ STEP 2 FAILED: Initial payment date is incorrect")
            print(f"      Expected: {expected_initial_payment_date}")
            print(f"      Got: {actual_initial_payment_date}")
            return False
        
        # Step 3: Record payment with payment_date "2025-02-20" (5 days late)
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 55.00,
            "payment_date": "2025-02-20",  # 5 days late (due was 2025-02-15)
            "payment_method": "Cash",
            "notes": "Late payment - testing billing cycle consistency"
        }
        
        success3, response3 = self.run_test(
            "STEP 3: Record late payment on '2025-02-20' (5 days after due date)",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success3:
            print("❌ CRITICAL FAILURE: Could not record payment")
            return False
            
        print(f"   ✅ Payment recorded successfully")
        print(f"   💰 Amount paid: ${response3.get('amount_paid')}")
        print(f"   📅 Payment date: 2025-02-20 (5 days late)")
        print(f"   🔄 New next payment date: {response3.get('new_next_payment_date')}")
        
        # Step 4: Verify new next_payment_date is "2025-03-15" (NOT "2025-03-20")
        expected_new_payment_date = "March 15, 2025"  # API returns formatted date
        actual_new_payment_date = response3.get('new_next_payment_date')
        
        print(f"\n🎯 STEP 4: CRITICAL VERIFICATION - Billing cycle consistency")
        print(f"   Expected: {expected_new_payment_date} (maintains monthly cycle)")
        print(f"   Actual: {actual_new_payment_date}")
        print(f"   ❌ Should NOT be: March 20, 2025 (would indicate billing drift)")
        
        # Check if the new payment date maintains the billing cycle
        if actual_new_payment_date == expected_new_payment_date:
            print("   ✅ STEP 4 PASSED: Billing cycle consistency maintained!")
            print("   ✅ Late payment did NOT shift future billing dates")
            print("   ✅ Professional billing experience preserved")
            print("   ✅ No billing cycle drift detected")
            
            # Additional verification: Get client to confirm the date is persisted
            success4, response4 = self.run_test(
                "VERIFICATION: Get client to confirm payment date persistence",
                "GET",
                f"clients/{self.test_client_id}",
                200
            )
            
            if success4:
                persisted_payment_date = response4.get('next_payment_date')
                print(f"   📋 Persisted next payment date: {persisted_payment_date}")
                
                # Convert to same format for comparison
                if persisted_payment_date == "2025-03-15":
                    print("   ✅ PERSISTENCE VERIFIED: Payment date correctly stored in database")
                    return True
                else:
                    print("   ❌ PERSISTENCE FAILED: Payment date not correctly stored")
                    return False
            else:
                print("   ❌ Could not verify persistence")
                return False
                
        else:
            print("   ❌ STEP 4 FAILED: Billing cycle consistency NOT maintained!")
            print("   ❌ Late payment shifted future billing dates (billing drift)")
            print("   ❌ This breaks professional billing experience")
            
            # Check if it's the old broken behavior
            if "March 20, 2025" in str(actual_new_payment_date):
                print("   🚨 DETECTED OLD BROKEN BEHAVIOR: Payment date shifted by late payment")
                print("   🔧 FIX NEEDED: Payment recording logic should use current_due_date, not max(current_due_date, payment_date)")
            
            return False

    def test_multiple_consecutive_payments(self):
        """
        Test multiple consecutive payments to ensure no billing drift over time
        """
        if not self.test_client_id:
            print("❌ Multiple payments test skipped - no test client available")
            return False
            
        print(f"\n🔄 TESTING MULTIPLE CONSECUTIVE PAYMENTS")
        print("Testing that multiple payments maintain consistent monthly billing cycles")
        print("=" * 60)
        
        # Record several more payments to test consistency
        payment_scenarios = [
            {
                "date": "2025-03-18",  # 3 days late
                "expected_next": "April 15, 2025",
                "description": "Second payment (3 days late)"
            },
            {
                "date": "2025-04-12",  # 3 days early
                "expected_next": "May 15, 2025", 
                "description": "Third payment (3 days early)"
            },
            {
                "date": "2025-05-15",  # On time
                "expected_next": "June 15, 2025",
                "description": "Fourth payment (on time)"
            }
        ]
        
        all_passed = True
        
        for i, scenario in enumerate(payment_scenarios, 2):
            payment_data = {
                "client_id": self.test_client_id,
                "amount_paid": 55.00,
                "payment_date": scenario["date"],
                "payment_method": "Credit Card",
                "notes": f"Testing consecutive payment #{i} - {scenario['description']}"
            }
            
            success, response = self.run_test(
                f"Payment #{i}: {scenario['description']} on {scenario['date']}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                actual_next = response.get('new_next_payment_date')
                expected_next = scenario['expected_next']
                
                print(f"   📅 Payment date: {scenario['date']}")
                print(f"   🎯 Expected next: {expected_next}")
                print(f"   📋 Actual next: {actual_next}")
                
                if actual_next == expected_next:
                    print(f"   ✅ Payment #{i} maintains billing cycle consistency")
                else:
                    print(f"   ❌ Payment #{i} breaks billing cycle consistency")
                    all_passed = False
            else:
                print(f"   ❌ Payment #{i} failed to record")
                all_passed = False
        
        if all_passed:
            print(f"\n✅ MULTIPLE PAYMENTS TEST PASSED!")
            print("   ✅ All consecutive payments maintain 15th of month billing cycle")
            print("   ✅ Early payments don't shift billing dates")
            print("   ✅ Late payments don't shift billing dates") 
            print("   ✅ On-time payments maintain schedule")
            print("   ✅ No billing cycle drift detected over multiple payments")
        else:
            print(f"\n❌ MULTIPLE PAYMENTS TEST FAILED!")
            print("   ❌ Billing cycle drift detected over multiple payments")
            
        return all_passed

    def run_all_tests(self):
        """Run all payment date calculation fix tests"""
        print("🚀 STARTING PAYMENT DATE CALCULATION FIX TESTS")
        print("=" * 80)
        
        # Test the main scenario from the review request
        test1_passed = self.test_payment_date_calculation_fix()
        
        # Test multiple consecutive payments for consistency
        test2_passed = self.test_multiple_consecutive_payments()
        
        # Summary
        print(f"\n📊 TEST SUMMARY")
        print("=" * 40)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if test1_passed and test2_passed:
            print(f"\n🎉 ALL CRITICAL TESTS PASSED!")
            print("✅ Payment date calculation fix is working correctly")
            print("✅ Billing cycle consistency is maintained")
            print("✅ Late payments don't cause billing drift")
            print("✅ Professional billing experience is preserved")
            print("✅ User's reported issue is COMPLETELY RESOLVED")
        else:
            print(f"\n🚨 CRITICAL TESTS FAILED!")
            if not test1_passed:
                print("❌ Main payment date calculation fix is NOT working")
                print("❌ User's reported issue is NOT resolved")
            if not test2_passed:
                print("❌ Multiple payment consistency is broken")
                print("❌ Billing cycle drift detected")
            
        return test1_passed and test2_passed

if __name__ == "__main__":
    print("🎯 PAYMENT DATE CALCULATION FIX TESTER")
    print("Testing the specific fix for user-reported payment date issue")
    print("=" * 80)
    
    tester = PaymentDateFixTester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n✅ PAYMENT DATE FIX VERIFICATION: SUCCESSFUL")
        sys.exit(0)
    else:
        print(f"\n❌ PAYMENT DATE FIX VERIFICATION: FAILED")
        sys.exit(1)