#!/usr/bin/env python3

import requests
import json
from datetime import datetime

class ClientUpdateTester:
    def __init__(self):
        self.base_url = "https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com"
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

    def test_client_update_payment_recalculation(self):
        """Test client start date update and automatic payment date recalculation"""
        print("🎯 CLIENT START DATE UPDATE & PAYMENT DATE RECALCULATION")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Step 1: Create a test client with initial start date
        initial_start_date = "2025-01-15"
        expected_initial_payment_date = "2025-02-14"
        
        client_data = {
            "name": "Update Test Client",
            "email": f"update_test_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": initial_start_date
        }
        
        print(f"\n📅 Step 1: Create client with start date {initial_start_date}")
        
        try:
            url = f"{self.api_url}/clients"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=client_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                client_id = response_data.get('id')
                actual_initial_payment_date = str(response_data.get('next_payment_date'))
                
                print(f"   Created client ID: {client_id}")
                print(f"   Initial start date: {response_data.get('start_date')}")
                print(f"   Initial payment date: {actual_initial_payment_date}")
                print(f"   Expected payment date: {expected_initial_payment_date}")
                
                if actual_initial_payment_date == expected_initial_payment_date:
                    self.log_test("Initial payment date calculation", True)
                else:
                    self.log_test("Initial payment date calculation", False, f"Expected: {expected_initial_payment_date}, Got: {actual_initial_payment_date}")
                    return False
                    
            else:
                self.log_test("Create test client", False, f"HTTP {response.status_code}: {response.text[:100]}")
                return False
                
        except Exception as e:
            self.log_test("Create test client", False, f"Exception: {str(e)}")
            return False
        
        # Step 2: Update the client's start date
        new_start_date = "2025-01-26"
        expected_new_payment_date = "2025-02-25"
        
        update_data = {
            "start_date": new_start_date
        }
        
        print(f"\n📅 Step 2: Update client start date to {new_start_date}")
        
        try:
            url = f"{self.api_url}/clients/{client_id}"
            response = requests.put(url, json=update_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                actual_new_payment_date = str(response_data.get('next_payment_date'))
                
                print(f"   Updated start date: {response_data.get('start_date')}")
                print(f"   Recalculated payment date: {actual_new_payment_date}")
                print(f"   Expected payment date: {expected_new_payment_date}")
                
                if actual_new_payment_date == expected_new_payment_date:
                    self.log_test("Payment date recalculation", True)
                else:
                    self.log_test("Payment date recalculation", False, f"Expected: {expected_new_payment_date}, Got: {actual_new_payment_date}")
                    return False
                    
            else:
                self.log_test("Update client start date", False, f"HTTP {response.status_code}: {response.text[:100]}")
                return False
                
        except Exception as e:
            self.log_test("Update client start date", False, f"Exception: {str(e)}")
            return False
        
        # Step 3: Test multiple date updates to verify consistency
        test_updates = [
            ("2025-03-01", "2025-03-31"),  # March to March
            ("2025-02-01", "2025-03-03"),  # February to March
            ("2025-12-31", "2026-01-30"),  # Year boundary
            ("2025-06-15", "2025-07-15"),  # Mid-month
        ]
        
        print(f"\n📅 Step 3: Test multiple date updates")
        
        for i, (test_start_date, expected_payment_date) in enumerate(test_updates, 1):
            update_data = {"start_date": test_start_date}
            
            try:
                response = requests.put(url, json=update_data, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    actual_payment_date = str(response_data.get('next_payment_date'))
                    
                    print(f"   Update {i}: {test_start_date} → {actual_payment_date} (expected: {expected_payment_date})")
                    
                    if actual_payment_date == expected_payment_date:
                        self.log_test(f"Date update {i} ({test_start_date})", True)
                    else:
                        self.log_test(f"Date update {i} ({test_start_date})", False, f"Expected: {expected_payment_date}, Got: {actual_payment_date}")
                        return False
                        
                else:
                    self.log_test(f"Date update {i} ({test_start_date})", False, f"HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log_test(f"Date update {i} ({test_start_date})", False, f"Exception: {str(e)}")
                return False
        
        print(f"\n🎯 CLIENT UPDATE SUMMARY:")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL UPDATE TESTS PASSED!")
            print("✅ Start date updates trigger automatic payment date recalculation")
            print("✅ Payment date recalculation is exactly 30 calendar days")
            print("✅ Multiple date scenarios work correctly")
            return True
        else:
            print("❌ SOME UPDATE TESTS FAILED!")
            return False

def main():
    """Main function"""
    print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - CLIENT UPDATE TESTING")
    print("Testing client start date update and payment date recalculation...")
    print()
    
    tester = ClientUpdateTester()
    success = tester.test_client_update_payment_recalculation()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())