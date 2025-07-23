#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class AlphaleteAPITester:
    def __init__(self, base_url="https://fb00d889-1c53-45d5-932b-d9d4fc2cee22.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_id = None
        self.created_membership_types = []

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
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

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

    def test_health_check(self):
        """Test API health check"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        if success and "message" in response:
            print(f"   Health message: {response['message']}")
        return success

    def test_email_configuration(self):
        """Test email configuration"""
        success, response = self.run_test(
            "Email Configuration Test",
            "POST",
            "email/test",
            200
        )
        if success:
            print(f"   Email test result: {response.get('message', 'No message')}")
            print(f"   Email success: {response.get('success', False)}")
        return success

    def test_get_clients_empty(self):
        """Test getting clients (should be empty initially)"""
        success, response = self.run_test(
            "Get Clients (Initial)",
            "GET",
            "clients",
            200
        )
        if success:
            print(f"   Initial client count: {len(response)}")
        return success

    def test_create_client(self):
        """Test creating a new client"""
        # Use timestamp to ensure unique email
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Sarah Wilson",
            "email": f"sarah_test_{timestamp}@test.com",
            "phone": "(555) 987-6543",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "next_payment_date": "2025-08-20"
        }
        
        success, response = self.run_test(
            "Create Client",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_id = response["id"]
            print(f"   Created client ID: {self.created_client_id}")
            print(f"   Client name: {response.get('name')}")
            print(f"   Client email: {response.get('email')}")
        
        return success

    def test_get_clients_with_data(self):
        """Test getting clients after creating one"""
        success, response = self.run_test(
            "Get Clients (With Data)",
            "GET",
            "clients",
            200
        )
        if success:
            print(f"   Client count after creation: {len(response)}")
            if len(response) > 0:
                print(f"   First client: {response[0].get('name')} ({response[0].get('email')})")
        return success

    def test_get_specific_client(self):
        """Test getting a specific client"""
        if not self.created_client_id:
            print("❌ Get Specific Client - SKIPPED (No client ID available)")
            return False
            
        success, response = self.run_test(
            "Get Specific Client",
            "GET",
            f"clients/{self.created_client_id}",
            200
        )
        
        if success:
            print(f"   Retrieved client: {response.get('name')} ({response.get('email')})")
        
        return success

    def test_send_individual_payment_reminder(self):
        """Test sending individual payment reminder"""
        if not self.created_client_id:
            print("❌ Send Individual Payment Reminder - SKIPPED (No client ID available)")
            return False
            
        reminder_data = {
            "client_id": self.created_client_id
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
        
        return success

    def test_send_bulk_payment_reminders(self):
        """Test sending bulk payment reminders"""
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
        
        return success

    def test_create_duplicate_client(self):
        """Test creating a client with duplicate email (should fail)"""
        client_data = {
            "name": "Sarah Wilson Duplicate",
            "email": "johndoe@example.com",  # Use existing email from database
            "phone": "(555) 123-4567",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "next_payment_date": "2025-09-15"
        }
        
        success, response = self.run_test(
            "Create Duplicate Client (Should Fail)",
            "POST",
            "clients",
            400,  # Expecting 400 Bad Request
            client_data
        )
        
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Alphalete Athletics Club API Tests")
        print("=" * 60)
        
        # Test sequence
        tests = [
            self.test_health_check,
            self.test_email_configuration,
            self.test_get_clients_empty,
            self.test_create_client,
            self.test_get_clients_with_data,
            self.test_get_specific_client,
            self.test_send_individual_payment_reminder,
            self.test_send_bulk_payment_reminders,
            self.test_create_duplicate_client,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ {test.__name__} - EXCEPTION: {str(e)}")
            print("-" * 40)
        
        # Print summary
        print("\n📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! API is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Check the details above.")
            return 1

def main():
    """Main function"""
    print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - API TESTING")
    print("Testing backend API functionality...")
    print()
    
    tester = AlphaleteAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())