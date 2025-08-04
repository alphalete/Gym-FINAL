#!/usr/bin/env python3

import requests
import json
from datetime import datetime

class PaymentDateTester:
    def __init__(self):
        self.base_url = "https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
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

    def test_payment_date_calculation(self):
        """Test payment date calculation for exactly 30 calendar days"""
        print("🎯 PAYMENT DATE CALCULATION - EXACTLY 30 CALENDAR DAYS")
        print("=" * 60)
        
        # Test cases as specified in the review request
        test_cases = [
            {
                "name": "Normal Month (January)",
                "start_date": "2025-01-15",
                "expected_payment_date": "2025-02-14"
            },
            {
                "name": "Month End (January 31st)",
                "start_date": "2025-01-31", 
                "expected_payment_date": "2025-03-02"
            },
            {
                "name": "February (28 days)",
                "start_date": "2025-02-01",
                "expected_payment_date": "2025-03-03"
            },
            {
                "name": "February 28th (non-leap year)",
                "start_date": "2025-02-28",
                "expected_payment_date": "2025-03-30"
            },
            {
                "name": "Year Boundary",
                "start_date": "2025-12-31",
                "expected_payment_date": "2026-01-30"
            },
            {
                "name": "June 15th",
                "start_date": "2025-06-15",
                "expected_payment_date": "2025-07-15"
            },
            {
                "name": "April 1st",
                "start_date": "2025-04-01",
                "expected_payment_date": "2025-05-01"
            },
            {
                "name": "September 30th",
                "start_date": "2025-09-30",
                "expected_payment_date": "2025-10-30"
            }
        ]
        
        all_tests_passed = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📅 Test Case {i}: {test_case['name']}")
            print(f"   Start Date: {test_case['start_date']}")
            print(f"   Expected Payment Date: {test_case['expected_payment_date']}")
            
            # Create client with specific start date
            client_data = {
                "name": f"Payment Test {i} - {test_case['name']}",
                "email": f"payment_test_{i}_{timestamp}@example.com",
                "phone": f"(555) {100+i:03d}-{1000+i:04d}",
                "membership_type": "Standard",
                "monthly_fee": 50.00,
                "start_date": test_case['start_date']
            }
            
            try:
                url = f"{self.api_url}/clients"
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=client_data, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    actual_payment_date = str(response_data.get('next_payment_date'))
                    expected_payment_date = test_case['expected_payment_date']
                    
                    print(f"   Actual Payment Date: {actual_payment_date}")
                    
                    if actual_payment_date == expected_payment_date:
                        self.log_test(f"{test_case['name']}", True, "Payment date calculation is EXACTLY 30 calendar days!")
                    else:
                        self.log_test(f"{test_case['name']}", False, f"Expected: {expected_payment_date}, Got: {actual_payment_date}")
                        all_tests_passed = False
                else:
                    self.log_test(f"{test_case['name']}", False, f"HTTP {response.status_code}: {response.text[:100]}")
                    all_tests_passed = False
                    
            except Exception as e:
                self.log_test(f"{test_case['name']}", False, f"Exception: {str(e)}")
                all_tests_passed = False
        
        print(f"\n🎯 PAYMENT DATE CALCULATION SUMMARY:")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if all_tests_passed:
            print("✅ ALL EDGE CASES PASSED!")
            print("✅ Payment date calculation is EXACTLY 30 calendar days from start date")
        else:
            print("❌ SOME EDGE CASES FAILED!")
            print("❌ Payment date calculation needs review")
        
        return all_tests_passed

def main():
    """Main function"""
    print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - PAYMENT DATE CALCULATION TESTING")
    print("Testing payment date calculation logic for exactly 30 calendar days...")
    print()
    
    tester = PaymentDateTester()
    success = tester.test_payment_date_calculation()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())