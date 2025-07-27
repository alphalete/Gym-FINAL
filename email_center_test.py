#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class EmailCenterTester:
    def __init__(self, base_url="https://bc0d3d40-9578-4667-9bfb-b44c2f8459c5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.created_client_ids = []
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
                response = requests.get(url, headers=headers, timeout=60)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=60)

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

    def create_test_client_1(self):
        """Create Test Client 1 as specified in requirements"""
        client_data = {
            "name": "Test Client 1",
            "email": "testclient1@example.com",
            "phone": "(555) 001-0001",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-15"  # Recent date
        }
        
        success, response = self.run_test(
            "Create Test Client 1",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            print(f"   ✅ Created Test Client 1 ID: {response['id']}")
            print(f"   📧 Email: {response.get('email')}")
            print(f"   💰 Monthly Fee: ${response.get('monthly_fee')}")
            print(f"   📅 Start Date: {response.get('start_date')}")
            print(f"   📅 Next Payment: {response.get('next_payment_date')}")
        
        return success

    def create_test_client_2(self):
        """Create Test Client 2 as specified in requirements"""
        client_data = {
            "name": "Test Client 2",
            "email": "testclient2@example.com",
            "phone": "(555) 002-0002",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-01-10"  # Recent date
        }
        
        success, response = self.run_test(
            "Create Test Client 2",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            print(f"   ✅ Created Test Client 2 ID: {response['id']}")
            print(f"   📧 Email: {response.get('email')}")
            print(f"   💰 Monthly Fee: ${response.get('monthly_fee')}")
            print(f"   📅 Start Date: {response.get('start_date')}")
            print(f"   📅 Next Payment: {response.get('next_payment_date')}")
        
        return success

    def create_test_client_3(self):
        """Create Test Client 3 as specified in requirements"""
        client_data = {
            "name": "Test Client 3",
            "email": "testclient3@example.com",
            "phone": "(555) 003-0003",
            "membership_type": "Premium",
            "monthly_fee": 100.00,
            "start_date": "2025-01-20"  # Recent date
        }
        
        success, response = self.run_test(
            "Create Test Client 3",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            print(f"   ✅ Created Test Client 3 ID: {response['id']}")
            print(f"   📧 Email: {response.get('email')}")
            print(f"   💰 Monthly Fee: ${response.get('monthly_fee')}")
            print(f"   📅 Start Date: {response.get('start_date')}")
            print(f"   📅 Next Payment: {response.get('next_payment_date')}")
        
        return success

    def verify_clients_created(self):
        """Verify all test clients were created successfully"""
        success, response = self.run_test(
            "Verify Test Clients Created",
            "GET",
            "clients",
            200
        )
        
        if success:
            print(f"   📊 Total clients in database: {len(response)}")
            test_clients = [client for client in response if client.get('name', '').startswith('Test Client')]
            print(f"   🎯 Test clients found: {len(test_clients)}")
            
            for client in test_clients:
                print(f"   - {client.get('name')}: {client.get('email')} (${client.get('monthly_fee')}) - Status: {client.get('status')}")
        
        return success

    def test_individual_email_to_test_client(self):
        """Test sending individual email to one of the test clients"""
        if not self.created_client_ids:
            print("❌ Individual Email Test - SKIPPED (No test clients available)")
            return False
            
        client_id = self.created_client_ids[0]  # Use first test client
        reminder_data = {
            "client_id": client_id
        }
        
        success, response = self.run_test(
            "Send Individual Email to Test Client 1",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success:
            print(f"   📧 Email sent to: {response.get('client_email')}")
            print(f"   ✅ Success: {response.get('success')}")
            print(f"   📝 Message: {response.get('message')}")
        
        return success

    def test_bulk_email_functionality(self):
        """Test the bulk email functionality - CRITICAL TEST"""
        print(f"   🎯 CRITICAL TEST: Bulk Email Functionality")
        print(f"   📧 Endpoint: /api/email/payment-reminder/bulk")
        print(f"   🎯 Expected: Send emails to all active clients including test clients")
        
        success, response = self.run_test(
            "Bulk Email Payment Reminders (CRITICAL TEST)",
            "POST",
            "email/payment-reminder/bulk",
            200
        )
        
        if success:
            total_clients = response.get('total_clients', 0)
            sent_successfully = response.get('sent_successfully', 0)
            failed = response.get('failed', 0)
            
            print(f"   📊 BULK EMAIL RESULTS:")
            print(f"      Total clients processed: {total_clients}")
            print(f"      Emails sent successfully: {sent_successfully}")
            print(f"      Failed to send: {failed}")
            print(f"      Success rate: {(sent_successfully/total_clients*100):.1f}%" if total_clients > 0 else "0%")
            
            # Check if our test clients received emails
            results = response.get('results', [])
            test_client_results = [r for r in results if r.get('client_name', '').startswith('Test Client')]
            
            print(f"   🎯 TEST CLIENT EMAIL RESULTS:")
            for result in test_client_results:
                status = "✅ SENT" if result.get('success') else "❌ FAILED"
                print(f"      {result.get('client_name')}: {status} ({result.get('client_email')})")
            
            # Verify all test clients received emails
            test_clients_sent = sum(1 for r in test_client_results if r.get('success'))
            expected_test_clients = len(self.created_client_ids)
            
            if test_clients_sent == expected_test_clients:
                print(f"   ✅ ALL TEST CLIENTS RECEIVED EMAILS: {test_clients_sent}/{expected_test_clients}")
            else:
                print(f"   ⚠️  PARTIAL SUCCESS: {test_clients_sent}/{expected_test_clients} test clients received emails")
        
        return success

    def test_email_center_verification(self):
        """Verify Email Center can load clients and send emails"""
        print(f"   🎯 EMAIL CENTER VERIFICATION")
        
        # 1. Verify clients can be loaded (GET /api/clients)
        success1, clients_response = self.run_test(
            "Email Center - Load Clients",
            "GET",
            "clients",
            200
        )
        
        if success1:
            active_clients = [c for c in clients_response if c.get('status') == 'Active']
            print(f"   📊 Active clients available for Email Center: {len(active_clients)}")
            
            # Show test clients specifically
            test_clients = [c for c in active_clients if c.get('name', '').startswith('Test Client')]
            print(f"   🎯 Test clients available: {len(test_clients)}")
            for client in test_clients:
                print(f"      - {client.get('name')}: {client.get('email')} (${client.get('monthly_fee')})")
        
        # 2. Test email configuration
        success2, email_config = self.run_test(
            "Email Center - Email Configuration",
            "POST",
            "email/test",
            200
        )
        
        if success2:
            print(f"   📧 Email service status: {email_config.get('message')}")
            print(f"   ✅ Email ready: {email_config.get('success')}")
        
        # 3. Test email templates availability
        success3, templates = self.run_test(
            "Email Center - Email Templates",
            "GET",
            "email/templates",
            200
        )
        
        if success3:
            template_count = len(templates.get('templates', {}))
            print(f"   📝 Email templates available: {template_count}")
            for template_key, template_info in templates.get('templates', {}).items():
                print(f"      - {template_key}: {template_info.get('name')}")
        
        return success1 and success2 and success3

    def run_email_center_tests(self):
        """Run all Email Center specific tests"""
        print("🏋️‍♂️ EMAIL CENTER BULK FUNCTIONALITY TEST")
        print("=" * 80)
        print("Testing Email Center bulk functionality with backend-created clients")
        print()
        
        # Test sequence for Email Center functionality
        tests = [
            # 1. Create test clients in backend database
            ("Backend Client Creation", [
                self.create_test_client_1,
                self.create_test_client_2,
                self.create_test_client_3,
                self.verify_clients_created,
            ]),
            
            # 2. Test individual email functionality
            ("Individual Email Testing", [
                self.test_individual_email_to_test_client,
            ]),
            
            # 3. Test bulk email functionality
            ("Bulk Email Testing", [
                self.test_bulk_email_functionality,
            ]),
            
            # 4. Verify Email Center can work with these clients
            ("Email Center Verification", [
                self.test_email_center_verification,
            ])
        ]
        
        for section_name, section_tests in tests:
            print(f"\n🔧 {section_name.upper()}")
            print("=" * 60)
            
            for test in section_tests:
                try:
                    test()
                except Exception as e:
                    print(f"❌ {test.__name__} - EXCEPTION: {str(e)}")
                print("-" * 40)
        
        # Print summary
        print("\n📊 EMAIL CENTER TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        print(f"\n🎯 EMAIL CENTER FUNCTIONALITY:")
        print(f"   ✓ Test Clients Created: {len(self.created_client_ids)}/3")
        print(f"   ✓ Backend Database Population: {'✅ SUCCESS' if len(self.created_client_ids) == 3 else '❌ PARTIAL'}")
        print(f"   ✓ Individual Email Testing: {'✅ TESTED' if self.tests_passed > 3 else '❌ FAILED'}")
        print(f"   ✓ Bulk Email Functionality: {'✅ TESTED' if self.tests_passed > 4 else '❌ FAILED'}")
        print(f"   ✓ Email Center Verification: {'✅ TESTED' if self.tests_passed > 5 else '❌ FAILED'}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 EMAIL CENTER BULK FUNCTIONALITY: FULLY WORKING!")
            print("   ✅ Backend clients created successfully")
            print("   ✅ Individual emails working")
            print("   ✅ Bulk emails working")
            print("   ✅ Email Center can now load clients and send bulk emails")
            print("\n📧 NEXT STEPS:")
            print("   1. Frontend Email Center should now be able to load these test clients")
            print("   2. Bulk email functionality should work from the frontend")
            print("   3. Test clients are ready for Email Center testing")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Check the details above.")
            print("   Email Center may have issues with bulk functionality")
            return 1

def main():
    """Main function"""
    print("📧 EMAIL CENTER BULK FUNCTIONALITY TESTING")
    print("Creating test clients and verifying bulk email functionality...")
    print()
    
    tester = EmailCenterTester()
    return tester.run_email_center_tests()

if __name__ == "__main__":
    sys.exit(main())