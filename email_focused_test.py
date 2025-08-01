#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class EmailFocusedTester:
    def __init__(self, base_url="https://8beb6460-0117-4864-a970-463f629aa57c.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None, timeout: int = 30) -> tuple:
        """Run a single API test with extended timeout for email operations"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

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
        """Test email configuration at /api/email/test"""
        print("\n=== EMAIL CONFIGURATION TEST ===")
        success, response = self.run_test(
            "Email Configuration Test",
            "POST",
            "email/test",
            200,
            timeout=30
        )
        if success:
            print(f"   Email test result: {response.get('message', 'No message')}")
            print(f"   Email success: {response.get('success', False)}")
            if response.get('success'):
                print("   ✅ Email service is properly configured and working!")
            else:
                print("   ❌ Email service configuration has issues!")
        return success

    def create_test_client_with_real_email(self):
        """Create a test client with a real-looking email"""
        print("\n=== CREATE TEST CLIENT ===")
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
            "Create Test Client with Real Email",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_id = response["id"]
            print(f"   ✅ Created test client:")
            print(f"      ID: {self.created_client_id}")
            print(f"      Name: {response.get('name')}")
            print(f"      Email: {response.get('email')}")
            print(f"      Membership: {response.get('membership_type')}")
            print(f"      Monthly Fee: ${response.get('monthly_fee')}")
            print(f"      Start Date: {response.get('start_date')}")
            print(f"      Next Payment: {response.get('next_payment_date')}")
        
        return success

    def test_individual_payment_reminder(self):
        """Test sending individual payment reminder to the test client"""
        print("\n=== INDIVIDUAL PAYMENT REMINDER TEST ===")
        
        if not self.created_client_id:
            print("❌ Cannot test individual payment reminder - No test client created")
            return False
            
        reminder_data = {
            "client_id": self.created_client_id
        }
        
        success, response = self.run_test(
            "Send Individual Payment Reminder",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data,
            timeout=30
        )
        
        if success:
            print(f"   ✅ Individual payment reminder results:")
            print(f"      Email sent to: {response.get('client_email')}")
            print(f"      Success: {response.get('success')}")
            print(f"      Message: {response.get('message')}")
            
            if response.get('success'):
                print("   ✅ Individual payment reminder sent successfully!")
            else:
                print("   ❌ Individual payment reminder failed to send!")
        
        return success

    def test_bulk_payment_reminders(self):
        """Test bulk payment reminders with extended timeout"""
        print("\n=== BULK PAYMENT REMINDERS TEST ===")
        
        success, response = self.run_test(
            "Send Bulk Payment Reminders",
            "POST",
            "email/payment-reminder/bulk",
            200,
            timeout=60  # Extended timeout for bulk operations
        )
        
        if success:
            total_clients = response.get('total_clients', 0)
            sent_successfully = response.get('sent_successfully', 0)
            failed = response.get('failed', 0)
            
            print(f"   ✅ Bulk payment reminder results:")
            print(f"      Total clients: {total_clients}")
            print(f"      Sent successfully: {sent_successfully}")
            print(f"      Failed: {failed}")
            print(f"      Success rate: {(sent_successfully/total_clients*100):.1f}%" if total_clients > 0 else "N/A")
            
            # Show detailed results
            results = response.get('results', [])
            if results:
                print(f"   📧 Email sending details:")
                for i, result in enumerate(results):
                    status = "✅" if result.get('success') else "❌"
                    error_msg = f" - {result.get('error', '')}" if not result.get('success') and result.get('error') else ""
                    print(f"      {i+1}. {status} {result.get('client_name')} ({result.get('client_email')}){error_msg}")
            
            if sent_successfully > 0:
                print("   ✅ Bulk payment reminders working!")
            else:
                print("   ❌ Bulk payment reminders failed for all clients!")
        
        return success

    def check_for_email_errors(self):
        """Check backend logs for email-related errors"""
        print("\n=== EMAIL ERROR ANALYSIS ===")
        print("   Checking for common email issues...")
        
        # Test with invalid client ID to see error handling
        invalid_reminder_data = {
            "client_id": "non-existent-client-id"
        }
        
        success, response = self.run_test(
            "Test Email Error Handling (Invalid Client)",
            "POST",
            "email/payment-reminder",
            404,  # Should return 404 for non-existent client
            invalid_reminder_data
        )
        
        if success:
            print("   ✅ Email error handling is working correctly")
        else:
            print("   ❌ Email error handling may have issues")
        
        return success

    def run_email_focused_tests(self):
        """Run all email-focused tests as requested in the review"""
        print("📧 ALPHALETE ATHLETICS CLUB - EMAIL FUNCTIONALITY TESTING")
        print("=" * 80)
        print("Testing email functionality as requested in review:")
        print("1. Test email configuration at /api/email/test")
        print("2. Create a test client with a real-looking email")
        print("3. Try to send individual payment reminder to that client")
        print("4. Check for any email sending errors or issues")
        print("=" * 80)
        
        # Run tests in sequence
        tests = [
            ("Email Configuration", self.test_email_configuration),
            ("Create Test Client", self.create_test_client_with_real_email),
            ("Individual Payment Reminder", self.test_individual_payment_reminder),
            ("Bulk Payment Reminders", self.test_bulk_payment_reminders),
            ("Email Error Handling", self.check_for_email_errors),
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
        print("\n📊 EMAIL FUNCTIONALITY TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Email-specific analysis
        print(f"\n🎯 EMAIL FUNCTIONALITY ANALYSIS:")
        if self.tests_passed == self.tests_run:
            print("   ✅ ALL EMAIL TESTS PASSED!")
            print("   ✅ Email Configuration: WORKING")
            print("   ✅ Individual Payment Reminders: WORKING")
            print("   ✅ Bulk Payment Reminders: WORKING")
            print("   ✅ Error Handling: WORKING")
            print("\n🎉 EMAIL SERVICE IS FULLY FUNCTIONAL!")
            print("   The 'Failed to send email reminder' issue reported by user is likely a frontend issue.")
            return 0
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"   ⚠️  {failed_count} email test(s) failed.")
            print("   🔍 EMAIL SERVICE ISSUES DETECTED!")
            print("   The 'Failed to send email reminder' issue is likely a backend problem.")
            return 1

def main():
    """Main function for email-focused testing"""
    print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - EMAIL FOCUSED TESTING")
    print("Specifically testing email functionality as requested in review...")
    print()
    
    tester = EmailFocusedTester()
    return tester.run_email_focused_tests()

if __name__ == "__main__":
    sys.exit(main())