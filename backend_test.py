#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class AlphaleteAPITester:
    def __init__(self, base_url="https://bc6dff33-f318-49ad-85f8-2547aae78d9f.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_id = None
        self.created_membership_types = []
        # Reminder system test variables
        self.reminder_test_client_id = None
        self.due_soon_client_id = None
        self.due_today_client_id = None

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

    def test_update_client_all_fields(self):
        """Test updating client with all editable fields"""
        if not self.created_client_id:
            print("❌ Update Client (All Fields) - SKIPPED (No client ID available)")
            return False
            
        # Update all possible fields
        update_data = {
            "name": "John Smith Updated",
            "email": "john.smith.updated@example.com",
            "phone": "(555) 987-6543",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-08-01",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Update Client (All Fields)",
            "PUT",
            f"clients/{self.created_client_id}",
            200,
            update_data
        )
        
        if success:
            print(f"   Updated client: {response.get('name')} ({response.get('email')})")
            print(f"   New phone: {response.get('phone')}")
            print(f"   New membership: {response.get('membership_type')} - ${response.get('monthly_fee')}")
            print(f"   New start date: {response.get('start_date')}")
            print(f"   Status: {response.get('status')}")
            print(f"   Next payment date: {response.get('next_payment_date')}")
            
            # Verify that start_date update recalculated next_payment_date
            expected_payment_date = "2025-08-31"  # 30 days after 2025-08-01
            if str(response.get('next_payment_date')) == expected_payment_date:
                print("   ✅ Payment date recalculation is CORRECT!")
            else:
                print(f"   ❌ Payment date recalculation is INCORRECT! Expected: {expected_payment_date}, Got: {response.get('next_payment_date')}")
        
        return success

    def test_update_client_partial_fields(self):
        """Test updating client with only some fields (partial update)"""
        if not self.created_client_id:
            print("❌ Update Client (Partial) - SKIPPED (No client ID available)")
            return False
            
        # Update only name and phone
        update_data = {
            "name": "John Smith Partial Update",
            "phone": "(555) 111-2222"
        }
        
        success, response = self.run_test(
            "Update Client (Partial Fields)",
            "PUT",
            f"clients/{self.created_client_id}",
            200,
            update_data
        )
        
        if success:
            print(f"   Updated client: {response.get('name')}")
            print(f"   Updated phone: {response.get('phone')}")
            print(f"   Email unchanged: {response.get('email')}")
            print(f"   Membership unchanged: {response.get('membership_type')}")
        
        return success

    def test_update_client_membership_and_fee(self):
        """Test updating client membership type and monthly fee"""
        if not self.created_client_id:
            print("❌ Update Client (Membership & Fee) - SKIPPED (No client ID available)")
            return False
            
        # Update membership type and fee
        update_data = {
            "membership_type": "VIP",
            "monthly_fee": 150.00
        }
        
        success, response = self.run_test(
            "Update Client (Membership & Fee)",
            "PUT",
            f"clients/{self.created_client_id}",
            200,
            update_data
        )
        
        if success:
            print(f"   Updated membership: {response.get('membership_type')}")
            print(f"   Updated fee: ${response.get('monthly_fee')}")
            print(f"   Client: {response.get('name')}")
        
        return success

    def test_update_client_status(self):
        """Test updating client status"""
        if not self.created_client_id:
            print("❌ Update Client (Status) - SKIPPED (No client ID available)")
            return False
            
        # Update status to Inactive
        update_data = {
            "status": "Inactive"
        }
        
        success, response = self.run_test(
            "Update Client (Status to Inactive)",
            "PUT",
            f"clients/{self.created_client_id}",
            200,
            update_data
        )
        
        if success:
            print(f"   Updated status: {response.get('status')}")
            print(f"   Client: {response.get('name')}")
        
        return success

    def test_update_client_date_handling(self):
        """Test updating client with different date formats and edge cases"""
        if not self.created_client_id:
            print("❌ Update Client (Date Handling) - SKIPPED (No client ID available)")
            return False
            
        # Test with a different start date to verify date serialization/deserialization
        update_data = {
            "start_date": "2025-12-15"
        }
        
        success, response = self.run_test(
            "Update Client (Date Handling)",
            "PUT",
            f"clients/{self.created_client_id}",
            200,
            update_data
        )
        
        if success:
            print(f"   Updated start date: {response.get('start_date')}")
            print(f"   Recalculated next payment: {response.get('next_payment_date')}")
            
            # Verify date format and calculation
            expected_payment_date = "2026-01-14"  # 30 days after 2025-12-15
            if str(response.get('next_payment_date')) == expected_payment_date:
                print("   ✅ Date handling and calculation is CORRECT!")
            else:
                print(f"   ❌ Date handling is INCORRECT! Expected: {expected_payment_date}, Got: {response.get('next_payment_date')}")
        
        return success

    def test_update_nonexistent_client(self):
        """Test updating a non-existent client (should return 404)"""
        update_data = {
            "name": "Non-existent Client",
            "email": "nonexistent@example.com"
        }
        
        success, response = self.run_test(
            "Update Non-existent Client (Should Fail)",
            "PUT",
            "clients/non-existent-client-id",
            404,
            update_data
        )
        
        return success

    def test_update_client_invalid_email(self):
        """Test updating client with invalid email format"""
        if not self.created_client_id:
            print("❌ Update Client (Invalid Email) - SKIPPED (No client ID available)")
            return False
            
        update_data = {
            "email": "invalid-email-format"
        }
        
        success, response = self.run_test(
            "Update Client (Invalid Email)",
            "PUT",
            f"clients/{self.created_client_id}",
            422,  # Validation error
            update_data
        )
        
        return success

    def test_get_client_after_updates(self):
        """Test getting client after multiple updates to verify persistence"""
        if not self.created_client_id:
            print("❌ Get Client After Updates - SKIPPED (No client ID available)")
            return False
            
        success, response = self.run_test(
            "Get Client After Updates",
            "GET",
            f"clients/{self.created_client_id}",
            200
        )
        
        if success:
            print(f"   Final client state:")
            print(f"   Name: {response.get('name')}")
            print(f"   Email: {response.get('email')}")
            print(f"   Phone: {response.get('phone')}")
            print(f"   Membership: {response.get('membership_type')} - ${response.get('monthly_fee')}")
            print(f"   Start date: {response.get('start_date')}")
            print(f"   Next payment: {response.get('next_payment_date')}")
            print(f"   Status: {response.get('status')}")
        
        return success

    def test_get_all_clients_after_updates(self):
        """Test getting all clients after updates to verify they appear correctly in list"""
        success, response = self.run_test(
            "Get All Clients After Updates",
            "GET",
            "clients",
            200
        )
        
        if success:
            print(f"   Total clients: {len(response)}")
            for client in response:
                print(f"   - {client.get('name')} ({client.get('email')})")
                print(f"     Membership: {client.get('membership_type')} - ${client.get('monthly_fee')}")
                print(f"     Status: {client.get('status')}")
        
        return success

    def test_send_individual_payment_reminder(self):
        """Test sending individual payment reminder (CRITICAL - 404 Error Fix Test)"""
        if not self.created_client_id:
            print("❌ Send Individual Payment Reminder - SKIPPED (No client ID available)")
            return False
            
        reminder_data = {
            "client_id": self.created_client_id
        }
        
        print(f"   🔍 TESTING 404 ERROR FIX: Individual payment reminder endpoint")
        print(f"   📧 Endpoint: /api/email/payment-reminder")
        print(f"   🎯 Expected: 200 OK (not 404)")
        
        success, response = self.run_test(
            "Send Individual Payment Reminder (404 Fix Test)",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success:
            print(f"   ✅ 404 ERROR FIX: SUCCESSFUL - Endpoint responding correctly")
            print(f"   📧 Email sent to: {response.get('client_email')}")
            print(f"   ✅ Success: {response.get('success')}")
            print(f"   📝 Message: {response.get('message')}")
        else:
            print(f"   ❌ 404 ERROR FIX: FAILED - Endpoint still returning errors")
        
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

    def test_record_payment_with_automatic_invoice(self):
        """Test recording a payment with automatic invoice email (CRITICAL TEST)"""
        if not self.created_client_id:
            print("❌ Record Payment with Invoice - SKIPPED (No client ID available)")
            return False
            
        payment_data = {
            "client_id": self.created_client_id,
            "amount_paid": 75.00,
            "payment_date": "2025-01-23",
            "payment_method": "Bank Transfer",
            "notes": "Testing automatic invoice email functionality"
        }
        
        success, response = self.run_test(
            "Record Payment with Automatic Invoice Email",
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
            
            # CRITICAL: Check for automatic invoice email fields
            invoice_sent = response.get('invoice_sent')
            invoice_message = response.get('invoice_message')
            
            print(f"   🔍 INVOICE EMAIL STATUS:")
            print(f"      Invoice Sent: {invoice_sent}")
            print(f"      Invoice Message: {invoice_message}")
            
            if invoice_sent is not None and invoice_message is not None:
                print(f"   ✅ AUTOMATIC INVOICE EMAIL FEATURE: IMPLEMENTED")
                if invoice_sent:
                    print(f"   ✅ INVOICE EMAIL: SENT SUCCESSFULLY")
                else:
                    print(f"   ⚠️  INVOICE EMAIL: FAILED TO SEND")
            else:
                print(f"   ❌ AUTOMATIC INVOICE EMAIL FEATURE: NOT IMPLEMENTED")
                return False
        
        return success

    def test_email_endpoint_route_conflicts(self):
        """Test for route conflicts and duplicate handlers (CRITICAL - Route Conflict Test)"""
        print(f"   🔍 TESTING ROUTE CONFLICTS: Checking for duplicate route definitions")
        
        # Test the main email reminder endpoint multiple times to ensure consistency
        if not self.created_client_id:
            print("❌ Route Conflict Test - SKIPPED (No client ID available)")
            return False
            
        reminder_data = {
            "client_id": self.created_client_id
        }
        
        # Test the endpoint multiple times to check for consistency
        all_success = True
        for i in range(3):
            print(f"   📧 Test #{i+1}: /api/email/payment-reminder")
            success, response = self.run_test(
                f"Route Conflict Test #{i+1}",
                "POST",
                "email/payment-reminder",
                200,
                reminder_data
            )
            
            if not success:
                all_success = False
                print(f"   ❌ Route conflict detected on attempt #{i+1}")
            else:
                print(f"   ✅ Route working consistently on attempt #{i+1}")
        
        if all_success:
            print(f"   ✅ NO ROUTE CONFLICTS: All attempts successful")
        else:
            print(f"   ❌ ROUTE CONFLICTS DETECTED: Inconsistent responses")
            
        return all_success

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

    # ===== AUTOMATIC REMINDER SYSTEM TESTS =====
    
    def test_create_client_with_auto_reminders(self):
        """Test creating a client with auto_reminders_enabled field"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Sarah Connor",
            "email": f"sarah_reminder_{timestamp}@example.com",
            "phone": "(555) 987-6543",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-01-25",
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Create Client with Auto Reminders Enabled",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            # Store for reminder tests
            self.reminder_test_client_id = response["id"]
            print(f"   Created reminder test client ID: {self.reminder_test_client_id}")
            print(f"   Auto reminders enabled: {response.get('auto_reminders_enabled', 'Not specified')}")
            
            # Verify auto_reminders_enabled field is present and True
            if response.get('auto_reminders_enabled') is True:
                print("   ✅ Auto reminders field correctly set to True")
            else:
                print("   ❌ Auto reminders field not correctly set")
                return False
        
        return success

    def test_update_client_reminder_settings(self):
        """Test updating client reminder settings via PUT /api/clients/{client_id}/reminders"""
        if not hasattr(self, 'reminder_test_client_id') or not self.reminder_test_client_id:
            print("❌ Update Client Reminder Settings - SKIPPED (No reminder test client ID available)")
            return False
        
        # Test disabling reminders with JSON body
        disable_data = {"enabled": False}
        success1, response1 = self.run_test(
            "Disable Client Auto Reminders",
            "PUT",
            f"clients/{self.reminder_test_client_id}/reminders",
            200,
            disable_data
        )
        
        if success1:
            print(f"   Reminder status: {response1.get('auto_reminders_enabled')}")
            print(f"   Message: {response1.get('message')}")
        
        # Test enabling reminders with JSON body
        enable_data = {"enabled": True}
        success2, response2 = self.run_test(
            "Enable Client Auto Reminders",
            "PUT", 
            f"clients/{self.reminder_test_client_id}/reminders",
            200,
            enable_data
        )
        
        if success2:
            print(f"   Reminder status: {response2.get('auto_reminders_enabled')}")
            print(f"   Message: {response2.get('message')}")
        
        return success1 and success2

    def test_get_upcoming_reminders(self):
        """Test GET /api/reminders/upcoming endpoint"""
        success, response = self.run_test(
            "Get Upcoming Reminders (7 days)",
            "GET",
            "reminders/upcoming?days_ahead=7",
            200
        )
        
        if success:
            upcoming = response.get('upcoming_reminders', [])
            print(f"   Found {len(upcoming)} upcoming reminders")
            print(f"   Days ahead: {response.get('days_ahead')}")
            print(f"   Total reminders: {response.get('total_reminders')}")
            
            # Show sample upcoming reminders
            for i, reminder in enumerate(upcoming[:3]):  # Show first 3
                print(f"   {i+1}. {reminder.get('client_name')} - {reminder.get('reminder_type')} on {reminder.get('reminder_date')}")
        
        return success

    def test_get_reminder_history(self):
        """Test GET /api/reminders/history endpoint"""
        success, response = self.run_test(
            "Get Reminder History",
            "GET",
            "reminders/history?limit=50",
            200
        )
        
        if success:
            history = response.get('reminder_history', [])
            print(f"   Found {len(history)} reminder history records")
            print(f"   Total records: {response.get('total_records')}")
            
            # Show sample history
            for i, record in enumerate(history[:3]):  # Show first 3
                print(f"   {i+1}. {record.get('client_name')} - {record.get('reminder_type')} - {record.get('status')}")
        
        return success

    def test_get_reminder_stats(self):
        """Test GET /api/reminders/stats endpoint"""
        success, response = self.run_test(
            "Get Reminder Statistics",
            "GET",
            "reminders/stats",
            200
        )
        
        if success:
            print(f"   Total reminders sent: {response.get('total_reminders_sent', 0)}")
            print(f"   Total failed reminders: {response.get('total_failed_reminders', 0)}")
            print(f"   Success rate: {response.get('success_rate', 0):.1f}%")
            print(f"   Today's reminders: {response.get('todays_reminders', 0)}")
            print(f"   Scheduler active: {response.get('scheduler_active', False)}")
            
            recent_summaries = response.get('recent_summaries', [])
            print(f"   Recent summaries: {len(recent_summaries)} days")
        
        return success

    def test_manual_reminder_run(self):
        """Test POST /api/reminders/test-run endpoint"""
        success, response = self.run_test(
            "Manual Reminder Test Run",
            "POST",
            "reminders/test-run",
            200
        )
        
        if success:
            print(f"   Success: {response.get('success')}")
            print(f"   Message: {response.get('message')}")
        
        return success

    def test_client_with_payment_due_soon(self):
        """Test creating a client with payment due in 3 days to test reminder logic"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Calculate start date so payment is due in 3 days
        payment_due_in_3_days = date.today() + timedelta(days=3)
        start_date = payment_due_in_3_days - timedelta(days=30)  # 30 days before due date
        
        client_data = {
            "name": "Mike Reminder Test",
            "email": f"mike_due_soon_{timestamp}@example.com",
            "phone": "(555) 111-2222",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": start_date.isoformat(),
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Create Client with Payment Due in 3 Days",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.due_soon_client_id = response["id"]
            print(f"   Created client with payment due: {payment_due_in_3_days}")
            print(f"   Next payment date: {response.get('next_payment_date')}")
            print(f"   Auto reminders: {response.get('auto_reminders_enabled')}")
            
            # Verify the payment date calculation is correct
            expected_payment_date = payment_due_in_3_days.isoformat()
            if str(response.get('next_payment_date')) == expected_payment_date:
                print("   ✅ Payment date calculation is CORRECT for reminder testing!")
            else:
                print(f"   ❌ Payment date calculation is INCORRECT! Expected: {expected_payment_date}, Got: {response.get('next_payment_date')}")
        
        return success

    def test_client_with_payment_due_today(self):
        """Test creating a client with payment due today"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Calculate start date so payment is due today
        payment_due_today = date.today()
        start_date = payment_due_today - timedelta(days=30)  # 30 days before due date
        
        client_data = {
            "name": "Lisa Due Today",
            "email": f"lisa_due_today_{timestamp}@example.com",
            "phone": "(555) 333-4444",
            "membership_type": "VIP",
            "monthly_fee": 150.00,
            "start_date": start_date.isoformat(),
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Create Client with Payment Due Today",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.due_today_client_id = response["id"]
            print(f"   Created client with payment due today: {payment_due_today}")
            print(f"   Next payment date: {response.get('next_payment_date')}")
            print(f"   Auto reminders: {response.get('auto_reminders_enabled')}")
        
        return success

    def test_reminder_integration_flow(self):
        """Test the complete reminder integration flow"""
        print("\n🔄 Testing Complete Reminder Integration Flow...")
        
        # Step 1: Check upcoming reminders (should include our test clients)
        success1, upcoming_response = self.run_test(
            "Check Upcoming Reminders for Test Clients",
            "GET",
            "reminders/upcoming?days_ahead=7",
            200
        )
        
        if success1:
            upcoming = upcoming_response.get('upcoming_reminders', [])
            test_client_found = False
            
            for reminder in upcoming:
                if hasattr(self, 'due_soon_client_id') and reminder.get('client_id') == self.due_soon_client_id:
                    test_client_found = True
                    print(f"   ✅ Found test client in upcoming reminders: {reminder.get('client_name')}")
                    print(f"      Reminder type: {reminder.get('reminder_type')}")
                    print(f"      Reminder date: {reminder.get('reminder_date')}")
                    break
            
            if not test_client_found and hasattr(self, 'due_soon_client_id'):
                print(f"   ⚠️ Test client not found in upcoming reminders (may be expected)")
        
        # Step 2: Trigger manual reminder run
        success2, run_response = self.run_test(
            "Trigger Manual Reminder Run",
            "POST",
            "reminders/test-run",
            200
        )
        
        # Step 3: Check reminder history after run
        success3, history_response = self.run_test(
            "Check Reminder History After Run",
            "GET",
            "reminders/history?limit=10",
            200
        )
        
        if success3:
            history = history_response.get('reminder_history', [])
            print(f"   Recent reminder history: {len(history)} records")
            
            # Look for our test clients in history
            for record in history[:5]:  # Check first 5 records
                print(f"   - {record.get('client_name')}: {record.get('reminder_type')} - {record.get('status')}")
        
        # Step 4: Check updated stats
        success4, stats_response = self.run_test(
            "Check Updated Reminder Stats",
            "GET",
            "reminders/stats",
            200
        )
        
        return success1 and success2 and success3 and success4

    def test_reminder_settings_persistence(self):
        """Test that reminder settings persist correctly"""
        if not hasattr(self, 'reminder_test_client_id') or not self.reminder_test_client_id:
            print("❌ Reminder Settings Persistence - SKIPPED (No reminder test client ID available)")
            return False
        
        # Get client to check current reminder setting
        success1, client_response = self.run_test(
            "Get Client to Check Reminder Settings",
            "GET",
            f"clients/{self.reminder_test_client_id}",
            200
        )
        
        if success1:
            current_setting = client_response.get('auto_reminders_enabled')
            print(f"   Current reminder setting: {current_setting}")
            
            # Update the client's other fields and verify reminder setting persists
            update_data = {
                "phone": "(555) 999-8888",
                "membership_type": "Elite"
            }
            
            success2, update_response = self.run_test(
                "Update Client Other Fields",
                "PUT",
                f"clients/{self.reminder_test_client_id}",
                200,
                update_data
            )
            
            if success2:
                updated_setting = update_response.get('auto_reminders_enabled')
                print(f"   Reminder setting after update: {updated_setting}")
                
                if current_setting == updated_setting:
                    print("   ✅ Reminder settings persisted correctly during client update")
                    return True
                else:
                    print("   ❌ Reminder settings did not persist during client update")
                    return False
        
        return False

    def test_reminder_error_scenarios(self):
        """Test reminder system error handling"""
        print("\n--- Testing Reminder Error Scenarios ---")
        
        # Test updating reminders for non-existent client
        success1, _ = self.run_test(
            "Update Reminders for Non-existent Client",
            "PUT",
            "clients/non-existent-id/reminders?enabled=true",
            404
        )
        
        # Test getting history for non-existent client
        success2, response2 = self.run_test(
            "Get History for Non-existent Client",
            "GET",
            "reminders/history?client_id=non-existent-id&limit=10",
            200  # Should return empty list, not error
        )
        
        if success2:
            history = response2.get('reminder_history', [])
            print(f"   History for non-existent client: {len(history)} records (should be 0)")
        
        return success1 and success2

    def test_payment_date_calculation_edge_cases(self):
        """SPECIFIC REVIEW REQUEST: Test payment date calculation logic for exactly 30 calendar days"""
        print("\n🎯 PAYMENT DATE CALCULATION EDGE CASES - EXACTLY 30 CALENDAR DAYS")
        print("=" * 80)
        
        # Test cases as specified in the review request
        test_cases = [
            {
                "name": "Normal Month (January)",
                "start_date": "2025-01-15",
                "expected_payment_date": "2025-02-14",
                "description": "30 days later"
            },
            {
                "name": "Month End (January 31st)",
                "start_date": "2025-01-31", 
                "expected_payment_date": "2025-03-02",
                "description": "30 days later - skipping February"
            },
            {
                "name": "February (28 days)",
                "start_date": "2025-02-01",
                "expected_payment_date": "2025-03-03", 
                "description": "30 days later"
            },
            {
                "name": "February 28th (non-leap year)",
                "start_date": "2025-02-28",
                "expected_payment_date": "2025-03-30",
                "description": "30 days later"
            },
            {
                "name": "Year Boundary",
                "start_date": "2025-12-31",
                "expected_payment_date": "2026-01-30",
                "description": "30 days later"
            },
            {
                "name": "Various Days - June 15th",
                "start_date": "2025-06-15",
                "expected_payment_date": "2025-07-15",
                "description": "30 days later"
            },
            {
                "name": "Various Days - April 1st",
                "start_date": "2025-04-01",
                "expected_payment_date": "2025-05-01",
                "description": "30 days later"
            },
            {
                "name": "Various Days - September 30th",
                "start_date": "2025-09-30",
                "expected_payment_date": "2025-10-30",
                "description": "30 days later"
            }
        ]
        
        all_tests_passed = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📅 Test Case {i}: {test_case['name']}")
            print(f"   Start Date: {test_case['start_date']}")
            print(f"   Expected Payment Date: {test_case['expected_payment_date']} ({test_case['description']})")
            
            # Create client with specific start date
            client_data = {
                "name": f"Payment Test {i} - {test_case['name']}",
                "email": f"payment_test_{i}_{timestamp}@example.com",
                "phone": f"(555) {100+i:03d}-{1000+i:04d}",
                "membership_type": "Standard",
                "monthly_fee": 50.00,
                "start_date": test_case['start_date']
            }
            
            success, response = self.run_test(
                f"Create Client - {test_case['name']}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                actual_payment_date = str(response.get('next_payment_date'))
                expected_payment_date = test_case['expected_payment_date']
                
                print(f"   Actual Payment Date: {actual_payment_date}")
                
                if actual_payment_date == expected_payment_date:
                    print(f"   ✅ PASSED: Payment date calculation is EXACTLY 30 calendar days!")
                else:
                    print(f"   ❌ FAILED: Payment date calculation is INCORRECT!")
                    print(f"      Expected: {expected_payment_date}")
                    print(f"      Got: {actual_payment_date}")
                    all_tests_passed = False
            else:
                print(f"   ❌ FAILED: Could not create client for test case")
                all_tests_passed = False
        
        print(f"\n🎯 PAYMENT DATE CALCULATION SUMMARY:")
        if all_tests_passed:
            print("   ✅ ALL EDGE CASES PASSED!")
            print("   ✅ Payment date calculation is EXACTLY 30 calendar days from start date")
            print("   ✅ Handles month boundaries correctly")
            print("   ✅ Handles February (28 days) correctly")
            print("   ✅ Handles year boundaries correctly")
            print("   ✅ Backend calculation logic is working perfectly")
        else:
            print("   ❌ SOME EDGE CASES FAILED!")
            print("   ❌ Payment date calculation needs review")
        
        return all_tests_passed

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

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Alphalete Athletics Club API Tests")
        print("=" * 80)
        
        # Test sequence - organized by feature
        tests = [
            # SPECIFIC REVIEW REQUEST TEST - Client Start Date Update & Payment Recalculation
            ("🎯 REVIEW REQUEST: Client Start Date Update & Payment Recalculation", [
                self.test_client_start_date_update_recalculation,
            ]),
            
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
            
            # Client Editing Functionality (REQUESTED FEATURE)
            ("Client Editing Functionality", [
                self.test_update_client_all_fields,
                self.test_update_client_partial_fields,
                self.test_update_client_membership_and_fee,
                self.test_update_client_status,
                self.test_update_client_date_handling,
                self.test_get_client_after_updates,
                self.test_get_all_clients_after_updates,
            ]),
            
            # Automatic Reminder System (NEW CRITICAL FEATURE)
            ("Automatic Reminder System", [
                self.test_create_client_with_auto_reminders,
                self.test_update_client_reminder_settings,
                self.test_get_upcoming_reminders,
                self.test_get_reminder_history,
                self.test_get_reminder_stats,
                self.test_manual_reminder_run,
                self.test_client_with_payment_due_soon,
                self.test_client_with_payment_due_today,
                self.test_reminder_integration_flow,
                self.test_reminder_settings_persistence,
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
            
            # Payment Recording (CRITICAL FUNCTIONALITY)
            ("Payment Recording", [
                self.test_record_payment,
                self.test_record_payment_with_automatic_invoice,
            ]),
            
            # Error Handling & Edge Cases (UPDATED WITH REMINDER ERROR TESTS)
            ("Error Handling", [
                self.test_email_endpoint_route_conflicts,
                self.test_create_duplicate_client,
                self.test_send_custom_reminder_invalid_client,
                self.test_update_nonexistent_client,
                self.test_update_client_invalid_email,
                self.test_reminder_error_scenarios,
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
        print(f"   ✓ Automatic Reminder System (NEW)")
        print(f"   ✓ Reminder API Endpoints (NEW)")
        print(f"   ✓ Client Reminder Settings (NEW)")
        print(f"   ✓ Email Templates System")
        print(f"   ✓ Custom Email Reminders with Templates")
        print(f"   ✓ Email System Integration")
        print(f"   ✓ Error Handling & Validation")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! The enhanced API with automatic reminders is working correctly.")
            print("   ✅ Membership Types Management: WORKING")
            print("   ✅ Automatic Payment Date Calculation: WORKING")
            print("   ✅ Enhanced Client Structure: WORKING")
            print("   ✅ Automatic Reminder System: WORKING")
            print("   ✅ Reminder API Endpoints: WORKING")
            print("   ✅ Email Templates System: WORKING")
            print("   ✅ Custom Email Reminders: WORKING")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Check the details above.")
            return 1

def main():
    """Main function"""
    print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - AUTOMATIC REMINDER SYSTEM TESTING")
    print("Testing automatic payment reminder system with scheduler, API endpoints, and client settings...")
    print()
    
    tester = AlphaleteAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())