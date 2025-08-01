#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class FocusedClientUpdateTester:
    def __init__(self, base_url="https://a2eb3b6a-2c20-4e9f-b52b-bd4f318d28fc.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

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

    def test_client_start_date_update_recalculation(self):
        """SPECIFIC TEST: Test client start date update and automatic next payment date recalculation"""
        print("\n🎯 SPECIFIC TEST: Client Start Date Update & Payment Date Recalculation")
        print("=" * 80)
        
        # Step 1: Create a test client with specific start date (2025-01-15)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        initial_start_date = "2025-01-15"
        expected_initial_payment_date = "2025-02-14"  # 30 days after start date
        
        client_data = {
            "name": "Start Date Test Client",
            "email": f"startdate_test_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": initial_start_date
        }
        
        success1, response1 = self.run_test(
            "1. Create Client with Start Date 2025-01-15",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1 or "id" not in response1:
            print("❌ Failed to create test client - aborting start date test")
            return False
            
        test_client_id = response1["id"]
        print(f"   ✅ Created test client ID: {test_client_id}")
        print(f"   📅 Initial start date: {response1.get('start_date')}")
        print(f"   💰 Initial next payment date: {response1.get('next_payment_date')}")
        
        # Verify initial payment date calculation
        if str(response1.get('next_payment_date')) == expected_initial_payment_date:
            print("   ✅ Initial payment date calculation is CORRECT!")
        else:
            print(f"   ❌ Initial payment date calculation is INCORRECT! Expected: {expected_initial_payment_date}, Got: {response1.get('next_payment_date')}")
            return False
        
        # Step 2: Verify the next payment date is calculated correctly (should be 30 days after start date)
        success2, response2 = self.run_test(
            "2. Verify Initial Payment Date Calculation",
            "GET",
            f"clients/{test_client_id}",
            200
        )
        
        if success2:
            print(f"   📅 Verified start date: {response2.get('start_date')}")
            print(f"   💰 Verified next payment date: {response2.get('next_payment_date')}")
            
            if str(response2.get('next_payment_date')) == expected_initial_payment_date:
                print("   ✅ Payment date verification PASSED!")
            else:
                print(f"   ❌ Payment date verification FAILED!")
                return False
        
        # Step 3: Update the client's start date to a different date (2025-01-26)
        new_start_date = "2025-01-26"
        expected_new_payment_date = "2025-02-25"  # 30 days after new start date
        
        update_data = {
            "start_date": new_start_date
        }
        
        success3, response3 = self.run_test(
            "3. Update Client Start Date to 2025-01-26",
            "PUT",
            f"clients/{test_client_id}",
            200,
            update_data
        )
        
        if success3:
            print(f"   📅 Updated start date: {response3.get('start_date')}")
            print(f"   💰 Recalculated next payment date: {response3.get('next_payment_date')}")
            
            # Verify the next payment date is recalculated automatically
            if str(response3.get('next_payment_date')) == expected_new_payment_date:
                print("   ✅ Payment date RECALCULATION is CORRECT!")
            else:
                print(f"   ❌ Payment date RECALCULATION is INCORRECT! Expected: {expected_new_payment_date}, Got: {response3.get('next_payment_date')}")
                return False
        else:
            return False
        
        # Step 4: Verify the next payment date is recalculated automatically
        success4, response4 = self.run_test(
            "4. Verify Payment Date Recalculation Persistence",
            "GET",
            f"clients/{test_client_id}",
            200
        )
        
        if success4:
            print(f"   📅 Persisted start date: {response4.get('start_date')}")
            print(f"   💰 Persisted next payment date: {response4.get('next_payment_date')}")
            
            if str(response4.get('next_payment_date')) == expected_new_payment_date:
                print("   ✅ Payment date recalculation PERSISTENCE is CORRECT!")
            else:
                print(f"   ❌ Payment date recalculation PERSISTENCE is INCORRECT!")
                return False
        
        # Step 5: Test with different start dates to ensure the calculation works correctly
        test_dates = [
            ("2025-03-01", "2025-03-31"),  # March to March (31 days in March)
            ("2025-02-01", "2025-03-03"),  # February to March (28 days in Feb 2025)
            ("2025-12-31", "2026-01-30"),  # Year boundary
            ("2025-06-15", "2025-07-15"),  # Mid-month
        ]
        
        for i, (test_start_date, expected_payment_date) in enumerate(test_dates, 5):
            update_data = {"start_date": test_start_date}
            
            success, response = self.run_test(
                f"{i}. Test Start Date {test_start_date}",
                "PUT",
                f"clients/{test_client_id}",
                200,
                update_data
            )
            
            if success:
                actual_payment_date = str(response.get('next_payment_date'))
                print(f"   📅 Start date: {test_start_date}")
                print(f"   💰 Expected payment date: {expected_payment_date}")
                print(f"   💰 Actual payment date: {actual_payment_date}")
                
                if actual_payment_date == expected_payment_date:
                    print(f"   ✅ Date calculation for {test_start_date} is CORRECT!")
                else:
                    print(f"   ❌ Date calculation for {test_start_date} is INCORRECT!")
                    return False
            else:
                return False
        
        print("\n🎉 CLIENT START DATE UPDATE & PAYMENT RECALCULATION TEST: ALL PASSED!")
        print("   ✅ Initial payment date calculation works correctly")
        print("   ✅ Start date updates trigger automatic payment date recalculation")
        print("   ✅ Payment date recalculation persists correctly")
        print("   ✅ Multiple date scenarios work correctly")
        print("   ✅ Backend functionality (lines 332-334 in server.py) is working as expected")
        
        return True

    def run_focused_test(self):
        """Run the focused client update test"""
        print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - CLIENT UPDATE FUNCTIONALITY TEST")
        print("Testing client start date update and automatic payment date recalculation...")
        print()
        
        success = self.test_client_start_date_update_recalculation()
        
        # Print summary
        print("\n📊 FOCUSED TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if success:
            print("\n🎉 CLIENT UPDATE FUNCTIONALITY TEST: PASSED!")
            print("   ✅ The backend correctly handles start date updates")
            print("   ✅ Payment dates are automatically recalculated")
            print("   ✅ The functionality in server.py lines 332-334 is working correctly")
            return 0
        else:
            print("\n❌ CLIENT UPDATE FUNCTIONALITY TEST: FAILED!")
            print("   ❌ Issues found with start date update or payment recalculation")
            return 1

def main():
    """Main function"""
    tester = FocusedClientUpdateTester()
    return tester.run_focused_test()

if __name__ == "__main__":
    sys.exit(main())