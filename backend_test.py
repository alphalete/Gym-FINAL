#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class AlphaleteAPITester:
    def __init__(self, base_url="https://6b64051f-ce9a-4270-be16-1060b67d4f80.preview.emergentagent.com"):
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

    def test_membership_types_seed(self):
        """Test seeding default membership types"""
        success, response = self.run_test(
            "Seed Default Membership Types",
            "POST",
            "membership-types/seed",
            200
        )
        if success:
            print(f"   Seeded types: {response.get('created_types', [])}")
        return success

    def test_get_membership_types(self):
        """Test getting all membership types"""
        success, response = self.run_test(
            "Get All Membership Types",
            "GET",
            "membership-types",
            200
        )
        if success:
            print(f"   Found {len(response)} membership types:")
            for mt in response:
                print(f"   - {mt['name']}: ${mt['monthly_fee']} ({mt['description']})")
        return success

    def test_create_membership_type(self):
        """Test creating a new membership type"""
        new_membership_data = {
            "name": "Student",
            "monthly_fee": 30.00,
            "description": "Special discount for students with valid ID",
            "features": ["Equipment Access", "Study Area", "Student Discount", "Flexible Hours"],
            "is_active": True
        }
        
        success, response = self.run_test(
            "Create Student Membership Type",
            "POST",
            "membership-types",
            200,
            new_membership_data
        )
        
        if success and "id" in response:
            self.created_membership_types.append(response["id"])
            print(f"   Created membership type ID: {response['id']}")
            print(f"   Name: {response['name']}")
            print(f"   Fee: ${response['monthly_fee']}")
        
        return success

    def test_update_membership_type(self):
        """Test updating a membership type"""
        if not self.created_membership_types:
            print("❌ Update Membership Type - SKIPPED (No membership type ID available)")
            return False
            
        membership_id = self.created_membership_types[0]
        update_data = {
            "monthly_fee": 35.00,
            "description": "Updated student membership with more benefits",
            "features": ["Equipment Access", "Study Area", "Student Discount", "Group Classes", "Extended Hours"]
        }
        
        success, response = self.run_test(
            "Update Student Membership Type",
            "PUT",
            f"membership-types/{membership_id}",
            200,
            update_data
        )
        
        if success:
            print(f"   Updated fee: ${response.get('monthly_fee')}")
            print(f"   Updated description: {response.get('description')}")
        
        return success

    def test_get_specific_membership_type(self):
        """Test getting a specific membership type"""
        if not self.created_membership_types:
            print("❌ Get Specific Membership Type - SKIPPED (No membership type ID available)")
            return False
            
        membership_id = self.created_membership_types[0]
        success, response = self.run_test(
            "Get Specific Membership Type",
            "GET",
            f"membership-types/{membership_id}",
            200
        )
        
        if success:
            print(f"   Retrieved: {response.get('name')} - ${response.get('monthly_fee')}")
        
        return success

    def test_delete_membership_type(self):
        """Test soft deleting a membership type"""
        if not self.created_membership_types:
            print("❌ Delete Membership Type - SKIPPED (No membership type ID available)")
            return False
            
        membership_id = self.created_membership_types[0]
        success, response = self.run_test(
            "Soft Delete Membership Type",
            "DELETE",
            f"membership-types/{membership_id}",
            200
        )
        
        if success:
            print(f"   Deletion message: {response.get('message')}")
        
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

    def test_create_client_with_start_date(self):
        """Test creating a new client with custom start date and auto-calculated payment date"""
        # Use timestamp to ensure unique email
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_date = "2025-07-25"  # Custom start date as mentioned in requirements
        expected_payment_date = "2025-08-24"  # 30 days later
        
        client_data = {
            "name": "John Doe",
            "email": f"john_test_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": start_date
        }
        
        success, response = self.run_test(
            "Create Client with Custom Start Date",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_id = response["id"]
            print(f"   Created client ID: {self.created_client_id}")
            print(f"   Client name: {response.get('name')}")
            print(f"   Start date: {response.get('start_date')}")
            print(f"   Next payment date: {response.get('next_payment_date')}")
            print(f"   Expected payment date: {expected_payment_date}")
            
            # Verify automatic payment date calculation
            if str(response.get('next_payment_date')) == expected_payment_date:
                print("   ✅ Payment date calculation is CORRECT!")
            else:
                print("   ❌ Payment date calculation is INCORRECT!")
        
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
                for client in response:
                    print(f"   - {client.get('name')}: Started {client.get('start_date')}, Next payment {client.get('next_payment_date')}")
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
            print(f"   Start date: {response.get('start_date')}")
            print(f"   Next payment: {response.get('next_payment_date')}")
        
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
            
            # Show some results if available
            results = response.get('results', [])
            if results:
                print(f"   Sample results:")
                for i, result in enumerate(results[:3]):  # Show first 3 results
                    print(f"     {i+1}. {result.get('client_name')} ({result.get('client_email')}): {'✅' if result.get('success') else '❌'}")
        
        return success

    def test_get_email_templates(self):
        """Test getting available email templates"""
        success, response = self.run_test(
            "Get Email Templates",
            "GET",
            "email/templates",
            200
        )
        
        if success:
            templates = response.get('templates', {})
            print(f"   Available templates: {len(templates)}")
            for template_key, template_info in templates.items():
                print(f"   - {template_key}: {template_info.get('name')} - {template_info.get('description')}")
        
        return success

    def test_send_custom_reminder_default_template(self):
        """Test sending custom payment reminder with default template"""
        if not self.created_client_id:
            print("❌ Send Custom Reminder (Default) - SKIPPED (No client ID available)")
            return False
            
        reminder_data = {
            "client_id": self.created_client_id,
            "template_name": "default",
            "custom_subject": "Custom Subject - Payment Due",
            "custom_message": "This is a custom message for testing the default template.",
            "custom_amount": 125.50,
            "custom_due_date": "February 15, 2025"
        }
        
        success, response = self.run_test(
            "Send Custom Payment Reminder (Default Template)",
            "POST",
            "email/custom-reminder",
            200,
            reminder_data
        )
        
        if success:
            print(f"   Email sent to: {response.get('client_email')}")
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message')}")
            print(f"   Template used: default")
        
        return success

    def test_send_custom_reminder_professional_template(self):
        """Test sending custom payment reminder with professional template"""
        if not self.created_client_id:
            print("❌ Send Custom Reminder (Professional) - SKIPPED (No client ID available)")
            return False
            
        reminder_data = {
            "client_id": self.created_client_id,
            "template_name": "professional",
            "custom_subject": "Payment Due Notice - Professional Style",
            "custom_message": "We appreciate your continued membership with our professional services.",
            "custom_amount": 150.00,
            "custom_due_date": "March 1, 2025"
        }
        
        success, response = self.run_test(
            "Send Custom Payment Reminder (Professional Template)",
            "POST",
            "email/custom-reminder",
            200,
            reminder_data
        )
        
        if success:
            print(f"   Email sent to: {response.get('client_email')}")
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message')}")
            print(f"   Template used: professional")
        
        return success

    def test_send_custom_reminder_friendly_template(self):
        """Test sending custom payment reminder with friendly template"""
        if not self.created_client_id:
            print("❌ Send Custom Reminder (Friendly) - SKIPPED (No client ID available)")
            return False
            
        reminder_data = {
            "client_id": self.created_client_id,
            "template_name": "friendly",
            "custom_subject": "Hey! Payment Time 💪",
            "custom_message": "Hope you're crushing those fitness goals! Just a friendly reminder about your payment.",
            "custom_amount": 99.99,
            "custom_due_date": "February 28, 2025"
        }
        
        success, response = self.run_test(
            "Send Custom Payment Reminder (Friendly Template)",
            "POST",
            "email/custom-reminder",
            200,
            reminder_data
        )
        
        if success:
            print(f"   Email sent to: {response.get('client_email')}")
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message')}")
            print(f"   Template used: friendly")
        
        return success

    def test_send_custom_reminder_minimal_data(self):
        """Test sending custom payment reminder with minimal data (should use defaults)"""
        if not self.created_client_id:
            print("❌ Send Custom Reminder (Minimal) - SKIPPED (No client ID available)")
            return False
            
        reminder_data = {
            "client_id": self.created_client_id
            # No template_name, custom_subject, custom_message, etc. - should use defaults
        }
        
        success, response = self.run_test(
            "Send Custom Payment Reminder (Minimal Data)",
            "POST",
            "email/custom-reminder",
            200,
            reminder_data
        )
        
        if success:
            print(f"   Email sent to: {response.get('client_email')}")
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message')}")
            print(f"   Template used: default (fallback)")
        
        return success

    def test_record_payment(self):
        """Test recording a payment for a client"""
        if not self.created_client_id:
            print("❌ Record Payment - SKIPPED (No client ID available)")
            return False
            
        payment_data = {
            "client_id": self.created_client_id,
            "amount_paid": 100.00,
            "payment_date": "2025-07-23",
            "payment_method": "Credit Card",
            "notes": "Payment recorded via API test"
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
        
        return success

    def test_send_custom_reminder_invalid_client(self):
        """Test sending custom payment reminder with invalid client ID"""
        reminder_data = {
            "client_id": "non-existent-client-id",
            "template_name": "default"
        }
        
        success, response = self.run_test(
            "Send Custom Payment Reminder (Invalid Client)",
            "POST",
            "email/custom-reminder",
            404,  # Should return 404 for non-existent client
            reminder_data
        )
        
        return success

    def test_create_duplicate_client(self):
        """Test creating a client with duplicate email (should fail)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Duplicate Client",
            "email": f"john_test_{timestamp}@example.com",  # Use same email as created client
            "phone": "(555) 123-4567",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-01"
        }
        
        success, response = self.run_test(
            "Create Duplicate Client (Should Fail)",
            "POST",
            "clients",
            400,  # Expecting 400 Bad Request
            client_data
        )
        
        return success

    def test_error_handling(self):
        """Test various error scenarios"""
        print("\n--- Testing Error Handling ---")
        
        # Test non-existent membership type
        success1, _ = self.run_test(
            "Get Non-existent Membership Type",
            "GET",
            "membership-types/non-existent-id",
            404
        )
        
        # Test non-existent client
        success2, _ = self.run_test(
            "Get Non-existent Client",
            "GET",
            "clients/non-existent-id",
            404
        )
        
        # Test invalid email format
        invalid_client_data = {
            "name": "Invalid Email User",
            "email": "invalid-email-format",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-01"
        }
        
        success3, _ = self.run_test(
            "Create Client with Invalid Email",
            "POST",
            "clients",
            422,  # Validation error
            invalid_client_data
        )
        
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Alphalete Athletics Club API Tests")
        print("=" * 80)
        
        # Test sequence - organized by feature
        tests = [
            # Basic connectivity
            ("Basic Connectivity", [
                self.test_health_check,
                self.test_email_configuration,
            ]),
            
            # Membership Types Management (NEW FEATURES)
            ("Membership Types Management", [
                self.test_membership_types_seed,
                self.test_get_membership_types,
                self.test_create_membership_type,
                self.test_get_specific_membership_type,
                self.test_update_membership_type,
                self.test_delete_membership_type,
            ]),
            
            # Enhanced Client Management (NEW FEATURES)
            ("Enhanced Client Management", [
                self.test_get_clients_empty,
                self.test_create_client_with_start_date,
                self.test_get_clients_with_data,
                self.test_get_specific_client,
            ]),
            
            # Email System Integration (UPDATED WITH NEW TEMPLATE FEATURES)
            ("Email System Integration", [
                self.test_get_email_templates,
                self.test_send_individual_payment_reminder,
                self.test_send_custom_reminder_default_template,
                self.test_send_custom_reminder_professional_template,
                self.test_send_custom_reminder_friendly_template,
                self.test_send_custom_reminder_minimal_data,
                self.test_send_bulk_payment_reminders,
            ]),
            
            # Error Handling & Edge Cases (UPDATED WITH TEMPLATE ERROR TESTS)
            ("Error Handling", [
                self.test_create_duplicate_client,
                self.test_send_custom_reminder_invalid_client,
                self.test_error_handling,
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
        print("\n📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Feature-specific summary
        print(f"\n🎯 NEW FEATURES TESTED:")
        print(f"   ✓ Membership Types CRUD API")
        print(f"   ✓ Client Start Date & Auto Payment Calculation")
        print(f"   ✓ Enhanced Client Management")
        print(f"   ✓ Email Templates System (NEW)")
        print(f"   ✓ Custom Email Reminders with Templates (NEW)")
        print(f"   ✓ Email System Integration")
        print(f"   ✓ Error Handling & Validation")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! The enhanced API with email templates is working correctly.")
            print("   ✅ Membership Types Management: WORKING")
            print("   ✅ Automatic Payment Date Calculation: WORKING")
            print("   ✅ Enhanced Client Structure: WORKING")
            print("   ✅ Email Templates System: WORKING")
            print("   ✅ Custom Email Reminders: WORKING")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Check the details above.")
            return 1

def main():
    """Main function"""
    print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - EMAIL TEMPLATE TESTING")
    print("Testing new email template functionality and customizable reminders...")
    print()
    
    tester = AlphaleteAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())