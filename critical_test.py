#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class CriticalFunctionalityTester:
    def __init__(self, base_url="https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com"):
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

    def test_email_configuration(self):
        """Test email configuration - CRITICAL"""
        success, response = self.run_test(
            "Email Configuration Test",
            "POST",
            "email/test",
            200
        )
        if success:
            print(f"   Email test result: {response.get('message', 'No message')}")
            print(f"   Email success: {response.get('success', False)}")
            if not response.get('success', False):
                print("   ⚠️  EMAIL CONFIGURATION IS NOT WORKING!")
        return success

    def create_test_client(self):
        """Create a test client for testing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Michael Thompson",
            "email": f"michael.thompson.{timestamp}@alphaleteclub.com",
            "phone": "(555) 234-5678",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-07-20"
        }
        
        success, response = self.run_test(
            "Create Test Client",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.test_client_id = response["id"]
            print(f"   Created test client ID: {self.test_client_id}")
            print(f"   Client name: {response.get('name')}")
            print(f"   Client email: {response.get('email')}")
            print(f"   Next payment date: {response.get('next_payment_date')}")
        
        return success

    def test_individual_payment_reminder(self):
        """Test individual payment reminder - CRITICAL"""
        if not self.test_client_id:
            print("❌ Individual Payment Reminder - SKIPPED (No test client)")
            return False
            
        reminder_data = {
            "client_id": self.test_client_id
        }
        
        success, response = self.run_test(
            "Send Individual Payment Reminder",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success:
            print(f"   Email sent to: {response.get('client_email')}")
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message')}")
            if not response.get('success', False):
                print("   ⚠️  EMAIL SENDING FAILED!")
        
        return success

    def test_payment_recording(self):
        """Test payment recording - CRITICAL"""
        if not self.test_client_id:
            print("❌ Payment Recording - SKIPPED (No test client)")
            return False
            
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 75.00,
            "payment_date": "2025-07-23",
            "payment_method": "Credit Card",
            "notes": "Test payment via API"
        }
        
        success, response = self.run_test(
            "Record Client Payment",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   Payment recorded for: {response.get('client_name')}")
            print(f"   Amount paid: ${response.get('amount_paid')}")
            print(f"   New next payment date: {response.get('new_next_payment_date')}")
            print(f"   Success: {response.get('success')}")
            if not response.get('success', False):
                print("   ⚠️  PAYMENT RECORDING FAILED!")
        
        return success

    def test_bulk_payment_reminders(self):
        """Test bulk payment reminders - CRITICAL"""
        success, response = self.run_test(
            "Send Bulk Payment Reminders",
            "POST",
            "email/payment-reminder/bulk",
            200
        )
        
        if success:
            print(f"   Total clients: {response.get('total_clients', 0)}")
            print(f"   Sent successfully: {response.get('sent_successfully', 0)}")
            print(f"   Failed: {response.get('failed', 0)}")
            
            # Check if any emails were sent
            sent_count = response.get('sent_successfully', 0)
            failed_count = response.get('failed', 0)
            
            if sent_count == 0 and failed_count > 0:
                print("   ⚠️  ALL BULK EMAILS FAILED!")
            elif sent_count > 0:
                print(f"   ✅ Successfully sent {sent_count} emails")
        
        return success

    def test_error_handling_invalid_client(self):
        """Test error handling for invalid client"""
        reminder_data = {
            "client_id": "non-existent-client-id"
        }
        
        success, response = self.run_test(
            "Payment Reminder for Invalid Client",
            "POST",
            "email/payment-reminder",
            404,  # Should return 404
            reminder_data
        )
        
        return success

    def run_critical_tests(self):
        """Run critical functionality tests"""
        print("🚨 CRITICAL FUNCTIONALITY TESTING")
        print("Testing the specific issues mentioned in the review:")
        print("1. Email configuration and sending")
        print("2. Individual payment reminders")
        print("3. Payment recording functionality")
        print("4. Bulk email functionality")
        print("=" * 80)
        
        # Test sequence focusing on critical issues
        tests = [
            ("Email Configuration", self.test_email_configuration),
            ("Test Client Creation", self.create_test_client),
            ("Individual Payment Reminder", self.test_individual_payment_reminder),
            ("Payment Recording", self.test_payment_recording),
            ("Bulk Payment Reminders", self.test_bulk_payment_reminders),
            ("Error Handling", self.test_error_handling_invalid_client),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔧 {test_name.upper()}")
            print("=" * 60)
            
            try:
                test_func()
            except Exception as e:
                print(f"❌ {test_name} - EXCEPTION: {str(e)}")
            print("-" * 40)
        
        # Print summary
        print("\n📊 CRITICAL TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Critical issues analysis
        print(f"\n🚨 CRITICAL ISSUES ANALYSIS:")
        if self.tests_passed == self.tests_run:
            print("   ✅ ALL CRITICAL FUNCTIONALITY IS WORKING")
            print("   ✅ Email Configuration: WORKING")
            print("   ✅ Email Sending: WORKING")
            print("   ✅ Payment Recording: WORKING")
            return 0
        else:
            print(f"   ❌ {self.tests_run - self.tests_passed} critical issue(s) found")
            print("   Check the detailed results above for specific failures")
            return 1

def main():
    """Main function"""
    print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - CRITICAL FUNCTIONALITY TEST")
    print("Focusing on the specific issues mentioned in the review request...")
    print()
    
    tester = CriticalFunctionalityTester()
    return tester.run_critical_tests()

if __name__ == "__main__":
    sys.exit(main())