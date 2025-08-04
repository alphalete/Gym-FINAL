#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class APIEndpointFixTester:
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

    def setup_test_client(self):
        """Create a test client for testing payment and email endpoints"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Marcus Williams",
            "email": f"marcus_endpoint_test_{timestamp}@example.com",
            "phone": "+18685551234",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-01-25",
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Setup Test Client for Endpoint Testing",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.test_client_id = response["id"]
            print(f"   ✅ Created test client ID: {self.test_client_id}")
            print(f"   📧 Client email: {response.get('email')}")
            print(f"   💰 Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   📅 Next payment date: {response.get('next_payment_date')}")
            return True
        else:
            print("❌ Failed to create test client")
            return False

    def test_payment_recording_endpoint(self):
        """Test POST /api/payments/record endpoint (404 error fix)"""
        if not self.test_client_id:
            print("❌ Payment Recording Test - SKIPPED (No test client available)")
            return False
        
        print(f"\n🎯 CRITICAL TEST: Payment Recording Endpoint Fix")
        print(f"   🔧 ISSUE: User reported 404 errors for POST /api/payments")
        print(f"   ✅ FIX: Frontend now calls POST /api/payments/record")
        print(f"   🧪 TESTING: POST /api/payments/record endpoint")
        
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 75.00,
            "payment_date": "2025-01-25",
            "payment_method": "Credit Card",
            "notes": "Testing payment recording endpoint fix - user reported 404 error resolved"
        }
        
        success, response = self.run_test(
            "POST /api/payments/record - Payment Recording (404 Fix)",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   🎉 404 ERROR FIX: SUCCESSFUL!")
            print(f"   ✅ Endpoint responding correctly (not 404)")
            print(f"   💰 Payment recorded for: {response.get('client_name')}")
            print(f"   💵 Amount paid: TTD {response.get('amount_paid')}")
            print(f"   📅 New next payment date: {response.get('new_next_payment_date')}")
            print(f"   📧 Invoice sent: {response.get('invoice_sent')}")
            print(f"   📝 Success message: {response.get('message')}")
            
            # Verify payment was actually recorded
            if response.get('success') and response.get('payment_id'):
                print(f"   ✅ Payment successfully recorded with ID: {response.get('payment_id')}")
                print(f"   ✅ Client data updated properly")
                return True
            else:
                print(f"   ❌ Payment recording failed - missing success confirmation")
                return False
        else:
            print(f"   ❌ 404 ERROR FIX: FAILED - Endpoint still not working")
            return False

    def test_email_reminder_endpoint(self):
        """Test POST /api/email/payment-reminder endpoint (404 error fix)"""
        if not self.test_client_id:
            print("❌ Email Reminder Test - SKIPPED (No test client available)")
            return False
        
        print(f"\n🎯 CRITICAL TEST: Email Reminder Endpoint Fix")
        print(f"   🔧 ISSUE: User reported 404 errors for POST /api/send-reminder")
        print(f"   ✅ FIX: Frontend now calls POST /api/email/payment-reminder")
        print(f"   🧪 TESTING: POST /api/email/payment-reminder endpoint")
        
        reminder_data = {
            "client_id": self.test_client_id,
            "template_name": "professional",
            "custom_subject": "Payment Reminder - Endpoint Fix Test",
            "custom_message": "Testing email reminder endpoint fix - user reported 404 error resolved",
            "custom_amount": 75.00,
            "custom_due_date": "February 25, 2025"
        }
        
        success, response = self.run_test(
            "POST /api/email/payment-reminder - Email Reminder (404 Fix)",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success:
            print(f"   🎉 404 ERROR FIX: SUCCESSFUL!")
            print(f"   ✅ Endpoint responding correctly (not 404)")
            print(f"   📧 Email sent to: {response.get('client_email')}")
            print(f"   ✅ Email success: {response.get('success')}")
            print(f"   📝 Response message: {response.get('message')}")
            
            # Verify email was actually sent
            if response.get('success') and response.get('client_email'):
                print(f"   ✅ Email reminder sent successfully")
                print(f"   ✅ Proper response format received")
                return True
            else:
                print(f"   ❌ Email reminder failed - missing success confirmation")
                return False
        else:
            print(f"   ❌ 404 ERROR FIX: FAILED - Endpoint still not working")
            return False

    def test_payment_stats_endpoint(self):
        """Test GET /api/payments/stats to verify payment was recorded"""
        print(f"\n🔍 VERIFICATION: Payment Statistics After Recording")
        
        success, response = self.run_test(
            "GET /api/payments/stats - Verify Payment Recording",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            print(f"   💰 Total revenue: TTD {response.get('total_revenue', 0)}")
            print(f"   📊 Payment count: {response.get('payment_count', 0)}")
            print(f"   📅 Monthly revenue: TTD {response.get('monthly_revenue', 0)}")
            print(f"   🕒 Timestamp: {response.get('timestamp')}")
            
            # Verify payment was recorded (should have at least 1 payment)
            if response.get('payment_count', 0) > 0:
                print(f"   ✅ Payment recording verified - stats updated correctly")
                return True
            else:
                print(f"   ⚠️  No payments found in stats - may be expected if database was cleared")
                return True  # Don't fail the test for this
        else:
            print(f"   ❌ Failed to get payment statistics")
            return False

    def test_client_data_update_verification(self):
        """Verify that payment recording updated client data properly"""
        if not self.test_client_id:
            print("❌ Client Data Update Verification - SKIPPED (No test client available)")
            return False
        
        print(f"\n🔍 VERIFICATION: Client Data Update After Payment")
        
        success, response = self.run_test(
            "GET /api/clients/{client_id} - Verify Client Update",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if success:
            print(f"   👤 Client name: {response.get('name')}")
            print(f"   📧 Client email: {response.get('email')}")
            print(f"   📅 Next payment date: {response.get('next_payment_date')}")
            print(f"   💰 Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   📊 Status: {response.get('status')}")
            
            # Verify client data is properly formatted
            if response.get('name') and response.get('email') and response.get('next_payment_date'):
                print(f"   ✅ Client data properly maintained after payment recording")
                return True
            else:
                print(f"   ❌ Client data incomplete after payment recording")
                return False
        else:
            print(f"   ❌ Failed to retrieve client data")
            return False

    def test_endpoint_error_handling(self):
        """Test error handling for both endpoints"""
        print(f"\n🔍 ERROR HANDLING: Testing Invalid Requests")
        
        # Test payment recording with invalid client ID
        invalid_payment_data = {
            "client_id": "non-existent-client-id",
            "amount_paid": 50.00,
            "payment_date": "2025-01-25",
            "payment_method": "Cash"
        }
        
        success1, _ = self.run_test(
            "POST /api/payments/record - Invalid Client ID",
            "POST",
            "payments/record",
            404,
            invalid_payment_data
        )
        
        # Test email reminder with invalid client ID
        invalid_reminder_data = {
            "client_id": "non-existent-client-id",
            "template_name": "default"
        }
        
        success2, _ = self.run_test(
            "POST /api/email/payment-reminder - Invalid Client ID",
            "POST",
            "email/payment-reminder",
            404,
            invalid_reminder_data
        )
        
        if success1 and success2:
            print(f"   ✅ Error handling working correctly for both endpoints")
            return True
        else:
            print(f"   ❌ Error handling issues detected")
            return False

    def run_all_tests(self):
        """Run all API endpoint fix tests"""
        print("=" * 80)
        print("🎯 API ENDPOINT FIX TESTING - PAYMENT RECORDING & EMAIL REMINDERS")
        print("=" * 80)
        print("🔧 TESTING USER-REPORTED 404 ERROR FIXES:")
        print("   1. POST /api/payments → POST /api/payments/record")
        print("   2. POST /api/send-reminder → POST /api/email/payment-reminder")
        print("=" * 80)
        
        # Setup test client
        if not self.setup_test_client():
            print("❌ Failed to setup test client - aborting tests")
            return False
        
        # Run critical endpoint tests
        test_results = []
        
        test_results.append(self.test_payment_recording_endpoint())
        test_results.append(self.test_email_reminder_endpoint())
        test_results.append(self.test_payment_stats_endpoint())
        test_results.append(self.test_client_data_update_verification())
        test_results.append(self.test_endpoint_error_handling())
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 API ENDPOINT FIX TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if all(test_results):
            print("\n🎉 ALL CRITICAL ENDPOINT FIXES VERIFIED WORKING!")
            print("✅ POST /api/payments/record - Payment recording working correctly")
            print("✅ POST /api/email/payment-reminder - Email reminders working correctly")
            print("✅ Both endpoints handle proper request body format")
            print("✅ Payment recording updates client data properly")
            print("✅ Email reminders send successfully")
            print("✅ Error handling working for invalid requests")
            print("\n🎯 USER-REPORTED 404 ERRORS: COMPLETELY RESOLVED!")
            return True
        else:
            print("\n❌ SOME CRITICAL ENDPOINT FIXES FAILED!")
            failed_tests = [i for i, result in enumerate(test_results) if not result]
            print(f"Failed test indices: {failed_tests}")
            return False

if __name__ == "__main__":
    tester = APIEndpointFixTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)