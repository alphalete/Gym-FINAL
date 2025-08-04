#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class PaymentDateIssueTest:
    def __init__(self, base_url="https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com"):
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

    def test_payment_date_calculation_issue(self):
        """
        Test the specific scenario the user reported about payment date calculation 
        changing incorrectly after first payment recording.
        
        SCENARIO TO TEST:
        1. Create a member without paying (payment_status='due') with start_date January 15th
        2. Verify the next_payment_date is correctly set to February 15th 
        3. Record the first payment with a payment_date that's different from the due date (e.g., February 20th)
        4. Check if the new next_payment_date changes incorrectly
        
        WHAT WE SUSPECT:
        The payment recording logic uses `max(current_due_date, payment_date)` as the base for calculating 
        the next payment date. This means:
        - If someone pays late (Feb 20th instead of Feb 15th), the next payment shifts to March 20th 
          instead of staying March 15th
        - This breaks the consistent monthly billing cycle
        """
        print("\n" + "="*80)
        print("🚨 TESTING USER-REPORTED PAYMENT DATE CALCULATION ISSUE")
        print("="*80)
        print("SCENARIO: Payment date calculation changing incorrectly after first payment recording")
        print("ISSUE: Late payments shift the billing cycle instead of maintaining consistent dates")
        print("="*80)

        # Step 1: Create a member with start_date January 15th and payment_status='due'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_date = "2025-01-15"
        expected_initial_payment_date = "2025-02-15"  # Should be one month ahead
        
        client_data = {
            "name": "Payment Issue Test Client",
            "email": f"payment_issue_test_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": start_date,
            "payment_status": "due"  # Client hasn't paid yet
        }
        
        print(f"\n📅 STEP 1: Creating client with start_date {start_date} and payment_status='due'")
        success1, response1 = self.run_test(
            "Create Client with Start Date Jan 15th (Due Status)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1 or "id" not in response1:
            print("❌ CRITICAL FAILURE: Could not create test client")
            return False
            
        self.test_client_id = response1["id"]
        actual_initial_payment_date = response1.get('next_payment_date')
        
        print(f"   ✅ Created client ID: {self.test_client_id}")
        print(f"   📅 Start date: {response1.get('start_date')}")
        print(f"   💰 Next payment date: {actual_initial_payment_date}")
        print(f"   🎯 Expected payment date: {expected_initial_payment_date}")
        
        # Step 2: Verify the next_payment_date is correctly set to February 15th
        print(f"\n📅 STEP 2: Verifying initial payment date calculation")
        if str(actual_initial_payment_date) == expected_initial_payment_date:
            print("   ✅ INITIAL PAYMENT DATE CALCULATION: CORRECT")
            print(f"   ✅ Client created on {start_date}, next payment due {expected_initial_payment_date}")
        else:
            print("   ❌ INITIAL PAYMENT DATE CALCULATION: INCORRECT")
            print(f"   ❌ Expected: {expected_initial_payment_date}, Got: {actual_initial_payment_date}")
            return False
        
        # Step 3: Record the first payment with a payment_date that's different from the due date
        # Pay 5 days late: February 20th instead of February 15th
        late_payment_date = "2025-02-20"  # 5 days late
        expected_next_payment_date_correct = "2025-03-15"  # Should maintain monthly cycle
        expected_next_payment_date_incorrect = "2025-03-20"  # What the bug would produce
        
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 55.00,
            "payment_date": late_payment_date,
            "payment_method": "Cash",
            "notes": "Testing late payment date calculation issue"
        }
        
        print(f"\n💰 STEP 3: Recording late payment (5 days after due date)")
        print(f"   📅 Original due date: {expected_initial_payment_date}")
        print(f"   📅 Actual payment date: {late_payment_date} (5 days late)")
        print(f"   🎯 CORRECT next payment date should be: {expected_next_payment_date_correct}")
        print(f"   🚨 INCORRECT next payment date would be: {expected_next_payment_date_incorrect}")
        
        success3, response3 = self.run_test(
            "Record Late Payment (Feb 20th instead of Feb 15th)",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success3:
            print("❌ CRITICAL FAILURE: Could not record payment")
            return False
        
        new_next_payment_date = response3.get('new_next_payment_date')
        print(f"   💰 Payment recorded successfully")
        print(f"   📅 New next payment date: {new_next_payment_date}")
        
        # Step 4: Check if the new next_payment_date changes incorrectly
        print(f"\n🔍 STEP 4: Analyzing payment date calculation behavior")
        
        # Convert the response date format to match our expected format
        if new_next_payment_date:
            # The API might return "March 20, 2025" format, convert to "2025-03-20"
            try:
                if "," in new_next_payment_date:
                    # Parse "March 20, 2025" format
                    parsed_date = datetime.strptime(new_next_payment_date, "%B %d, %Y")
                    new_next_payment_date_iso = parsed_date.strftime("%Y-%m-%d")
                else:
                    # Already in ISO format
                    new_next_payment_date_iso = new_next_payment_date
            except:
                new_next_payment_date_iso = new_next_payment_date
        else:
            new_next_payment_date_iso = None
        
        print(f"   📅 New payment date (ISO format): {new_next_payment_date_iso}")
        print(f"   🎯 Expected CORRECT date: {expected_next_payment_date_correct}")
        print(f"   🚨 Expected INCORRECT date: {expected_next_payment_date_incorrect}")
        
        # Determine if the issue exists
        if new_next_payment_date_iso == expected_next_payment_date_correct:
            print("\n✅ PAYMENT DATE CALCULATION: WORKING CORRECTLY!")
            print("   ✅ Late payment did NOT shift the billing cycle")
            print("   ✅ Next payment maintains consistent monthly billing (March 15th)")
            print("   ✅ The reported issue appears to be RESOLVED")
            issue_confirmed = False
        elif new_next_payment_date_iso == expected_next_payment_date_incorrect:
            print("\n🚨 PAYMENT DATE CALCULATION ISSUE: CONFIRMED!")
            print("   ❌ Late payment SHIFTED the billing cycle incorrectly")
            print("   ❌ Next payment moved to March 20th instead of March 15th")
            print("   ❌ This breaks consistent monthly billing cycles")
            print("   🔧 ROOT CAUSE: max(current_due_date, payment_date) logic in payment recording")
            issue_confirmed = True
        else:
            print(f"\n⚠️  UNEXPECTED PAYMENT DATE CALCULATION RESULT!")
            print(f"   ⚠️  Got: {new_next_payment_date_iso}")
            print(f"   ⚠️  Expected either: {expected_next_payment_date_correct} (correct) or {expected_next_payment_date_incorrect} (incorrect)")
            print(f"   ⚠️  This indicates a different calculation logic than expected")
            issue_confirmed = True  # Treat unexpected results as an issue
        
        # Step 5: Verify by getting the client data directly
        print(f"\n🔍 STEP 5: Verifying client data persistence")
        success5, response5 = self.run_test(
            "Get Client Data After Payment",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if success5:
            persisted_next_payment_date = response5.get('next_payment_date')
            print(f"   📅 Persisted next payment date: {persisted_next_payment_date}")
            
            # Convert to ISO format for comparison
            try:
                if persisted_next_payment_date and isinstance(persisted_next_payment_date, str):
                    if len(persisted_next_payment_date) == 10 and persisted_next_payment_date.count('-') == 2:
                        # Already in YYYY-MM-DD format
                        persisted_date_iso = persisted_next_payment_date
                    else:
                        # Try to parse other formats
                        parsed_date = datetime.strptime(persisted_next_payment_date, "%B %d, %Y")
                        persisted_date_iso = parsed_date.strftime("%Y-%m-%d")
                else:
                    persisted_date_iso = str(persisted_next_payment_date)
            except:
                persisted_date_iso = str(persisted_next_payment_date)
            
            print(f"   📅 Persisted date (ISO): {persisted_date_iso}")
            
            if persisted_date_iso == new_next_payment_date_iso:
                print("   ✅ Payment date persistence: CONSISTENT")
            else:
                print("   ❌ Payment date persistence: INCONSISTENT")
                print(f"      Payment response: {new_next_payment_date_iso}")
                print(f"      Client data: {persisted_date_iso}")
        
        # Final summary
        print(f"\n" + "="*80)
        print("🎯 PAYMENT DATE CALCULATION ISSUE TEST SUMMARY")
        print("="*80)
        
        if not issue_confirmed:
            print("✅ RESULT: PAYMENT DATE CALCULATION IS WORKING CORRECTLY")
            print("   • Late payments do not shift the billing cycle")
            print("   • Monthly billing dates remain consistent")
            print("   • The user-reported issue appears to be resolved")
            print("   • Backend logic is functioning as expected")
        else:
            print("🚨 RESULT: PAYMENT DATE CALCULATION ISSUE CONFIRMED")
            print("   • Late payments incorrectly shift the billing cycle")
            print("   • Monthly billing dates become inconsistent")
            print("   • This matches the user's reported problem")
            print("   • Backend logic needs to be fixed")
            print("\n🔧 RECOMMENDED FIX:")
            print("   • Modify payment recording logic in backend/server.py (lines 570-578)")
            print("   • Instead of: base_date = max(current_due_date, payment_date)")
            print("   • Use: base_date = current_due_date  # Always use original due date")
            print("   • This maintains consistent monthly billing cycles")
        
        return not issue_confirmed  # Return True if no issue (working correctly)

    def run_all_tests(self):
        """Run all payment date issue tests"""
        print("🚀 Starting Payment Date Calculation Issue Testing...")
        print("="*80)
        
        # Run the main test
        success = self.test_payment_date_calculation_issue()
        
        # Summary
        print(f"\n" + "="*80)
        print("📊 FINAL TEST SUMMARY")
        print("="*80)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if success:
            print("\n✅ OVERALL RESULT: PAYMENT DATE CALCULATION IS WORKING CORRECTLY")
            print("   The user-reported issue appears to be resolved.")
        else:
            print("\n🚨 OVERALL RESULT: PAYMENT DATE CALCULATION ISSUE CONFIRMED")
            print("   The user-reported issue exists and needs to be fixed.")
        
        return success

if __name__ == "__main__":
    tester = PaymentDateIssueTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)