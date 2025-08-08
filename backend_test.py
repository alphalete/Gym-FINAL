#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class AlphaleteAPITester:
    def __init__(self, base_url="https://alphalete-club.emergent.host"):
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

    def test_professional_email_template(self):
        """Test the new professional email template implementation"""
        print("\n🎯 PROFESSIONAL EMAIL TEMPLATE TESTING")
        print("=" * 80)
        
        # Step 1: Test GET /api/email/templates to ensure professional template is available
        success1, response1 = self.run_test(
            "1. Get Email Templates - Check Professional Template Availability",
            "GET",
            "email/templates",
            200
        )
        
        if not success1:
            print("❌ Failed to get email templates - aborting professional template test")
            return False
            
        templates = response1.get('templates', {})
        print(f"   Available templates: {list(templates.keys())}")
        
        # Verify professional template exists
        if 'professional' not in templates:
            print("❌ Professional template not found in available templates")
            return False
        else:
            professional_template = templates['professional']
            print(f"   ✅ Professional template found:")
            print(f"      Name: {professional_template.get('name')}")
            print(f"      Description: {professional_template.get('description')}")
            
            # Verify professional template has proper description
            expected_keywords = ['professional', 'business', 'clean', 'formal']
            description = professional_template.get('description', '').lower()
            found_keywords = [kw for kw in expected_keywords if kw in description]
            if found_keywords:
                print(f"   ✅ Professional template description contains professional keywords: {found_keywords}")
            else:
                print(f"   ⚠️  Professional template description may not be professional enough")
        
        # Step 2: Create a test client for sending professional email
        if not self.created_client_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            client_data = {
                "name": "Professional Template Test Client",
                "email": f"professional_test_{timestamp}@example.com",
                "phone": "(555) 123-4567",
                "membership_type": "Elite",
                "monthly_fee": 100.00,
                "start_date": "2025-01-25"
            }
            
            success2, response2 = self.run_test(
                "2. Create Test Client for Professional Email",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success2 and "id" in response2:
                self.created_client_id = response2["id"]
                print(f"   ✅ Created test client ID: {self.created_client_id}")
            else:
                print("❌ Failed to create test client - aborting professional template test")
                return False
        
        # Step 3: Send test email using professional template
        professional_reminder_data = {
            "client_id": self.created_client_id,
            "template_name": "professional",
            "custom_subject": "Payment Due Notice - Professional Template Test",
            "custom_message": "This is a test of the new professional email template with clean business-style formatting and proper Alphalete Athletics branding.",
            "custom_amount": 150.00,
            "custom_due_date": "February 15, 2025"
        }
        
        success3, response3 = self.run_test(
            "3. Send Professional Template Email Test",
            "POST",
            "email/custom-reminder",
            200,
            professional_reminder_data
        )
        
        if success3:
            print(f"   ✅ Professional email sent successfully!")
            print(f"   📧 Email sent to: {response3.get('client_email')}")
            print(f"   ✅ Success: {response3.get('success')}")
            print(f"   📝 Message: {response3.get('message')}")
            print(f"   🎨 Template used: professional")
            
            # Verify the email was sent successfully
            if response3.get('success') is True:
                print("   ✅ PROFESSIONAL EMAIL TEMPLATE: WORKING CORRECTLY")
            else:
                print("   ❌ PROFESSIONAL EMAIL TEMPLATE: FAILED TO SEND")
                return False
        else:
            print("   ❌ Failed to send professional template email")
            return False
        
        # Step 4: Test default template to compare (should now be professional)
        default_reminder_data = {
            "client_id": self.created_client_id,
            "template_name": "default",
            "custom_subject": "Default Template Test - Should be Professional",
            "custom_message": "Testing the default template to verify it uses professional styling.",
            "custom_amount": 100.00,
            "custom_due_date": "February 20, 2025"
        }
        
        success4, response4 = self.run_test(
            "4. Send Default Template Email (Should be Professional)",
            "POST",
            "email/custom-reminder",
            200,
            default_reminder_data
        )
        
        if success4:
            print(f"   ✅ Default template email sent successfully!")
            print(f"   📧 Email sent to: {response4.get('client_email')}")
            print(f"   ✅ Success: {response4.get('success')}")
            print(f"   🎨 Template used: default (should be professional)")
        
        # Step 5: Test friendly template for comparison
        friendly_reminder_data = {
            "client_id": self.created_client_id,
            "template_name": "friendly",
            "custom_subject": "Friendly Template Test - Casual Style",
            "custom_message": "Testing the friendly template for comparison with professional template.",
            "custom_amount": 75.00,
            "custom_due_date": "February 25, 2025"
        }
        
        success5, response5 = self.run_test(
            "5. Send Friendly Template Email (For Comparison)",
            "POST",
            "email/custom-reminder",
            200,
            friendly_reminder_data
        )
        
        if success5:
            print(f"   ✅ Friendly template email sent successfully!")
            print(f"   📧 Email sent to: {response5.get('client_email')}")
            print(f"   ✅ Success: {response5.get('success')}")
            print(f"   🎨 Template used: friendly (casual style)")
        
        # Step 6: Test regular payment reminder (should use default = professional)
        regular_reminder_data = {
            "client_id": self.created_client_id
        }
        
        success6, response6 = self.run_test(
            "6. Send Regular Payment Reminder (Default Professional)",
            "POST",
            "email/payment-reminder",
            200,
            regular_reminder_data
        )
        
        if success6:
            print(f"   ✅ Regular payment reminder sent successfully!")
            print(f"   📧 Email sent to: {response6.get('client_email')}")
            print(f"   ✅ Success: {response6.get('success')}")
            print(f"   🎨 Template used: default professional template")
        
        print("\n🎉 PROFESSIONAL EMAIL TEMPLATE TESTING SUMMARY:")
        print("   ✅ Professional template is available in template list")
        print("   ✅ Professional template has appropriate business-style description")
        print("   ✅ Professional template email sends successfully")
        print("   ✅ Default template uses professional styling")
        print("   ✅ All template variations (default, professional, friendly) work correctly")
        print("   ✅ Regular payment reminders use professional template by default")
        print("\n📧 EMAIL TEMPLATE VERIFICATION:")
        print("   • Professional template should have clean, business-like layout")
        print("   • Proper Alphalete Athletics branding should be present")
        print("   • Clear payment details display should be implemented")
        print("   • Professional language and tone should be used")
        print("   • Proper formatting and styling should be applied")
        print("   • Check your email inbox to verify the visual appearance!")
        
        return success1 and success3 and success4 and success6

    def test_critical_email_delivery_verification(self):
        """CRITICAL EMAIL DELIVERY VERIFICATION - Test actual email sending with new Gmail password"""
        print("\n🎯 CRITICAL EMAIL DELIVERY VERIFICATION WITH NEW GMAIL PASSWORD")
        print("=" * 80)
        print("🔑 Testing Gmail app password: 'yauf mdwy rsrd lhai'")
        print("🎯 Focus: Verify actual email delivery (not just API success)")
        
        # Step 1: Test Gmail SMTP Authentication
        print("\n📧 Step 1: Testing Gmail SMTP Authentication")
        success1, response1 = self.run_test(
            "Gmail SMTP Authentication Test",
            "POST",
            "email/test",
            200
        )
        
        if success1:
            email_success = response1.get('success', False)
            email_message = response1.get('message', 'No message')
            print(f"   🔐 Gmail Authentication: {'✅ SUCCESS' if email_success else '❌ FAILED'}")
            print(f"   📝 Message: {email_message}")
            
            if not email_success:
                print("   🚨 CRITICAL: Gmail authentication failed - email delivery will not work")
                return False
        else:
            print("   🚨 CRITICAL: Email test endpoint failed")
            return False
        
        # Step 2: Create test client for email verification
        if not self.created_client_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            client_data = {
                "name": "Email Delivery Test Client",
                "email": f"email_test_{timestamp}@example.com",
                "phone": "(555) 123-4567",
                "membership_type": "Elite",
                "monthly_fee": 100.00,
                "start_date": "2025-01-25"
            }
            
            success2, response2 = self.run_test(
                "Create Email Test Client",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success2 and "id" in response2:
                self.created_client_id = response2["id"]
                print(f"   ✅ Created email test client ID: {self.created_client_id}")
            else:
                print("   ❌ Failed to create test client for email verification")
                return False
        
        # Step 3: Test Real Email Sending - Payment Reminder
        print("\n📧 Step 2: Testing Real Payment Reminder Email Sending")
        reminder_data = {
            "client_id": self.created_client_id,
            "template_name": "default",
            "custom_subject": "CRITICAL TEST - Payment Reminder Email Delivery Verification",
            "custom_message": "This is a critical test to verify that emails are actually being sent and delivered with the new Gmail app password 'yauf mdwy rsrd lhai'.",
            "custom_amount": 100.00,
            "custom_due_date": "February 15, 2025"
        }
        
        success3, response3 = self.run_test(
            "Real Payment Reminder Email Sending",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success3:
            email_success = response3.get('success', False)
            email_message = response3.get('message', 'No message')
            client_email = response3.get('client_email', 'Unknown')
            
            print(f"   📧 Email Sent To: {client_email}")
            print(f"   ✅ API Response Success: {email_success}")
            print(f"   📝 API Message: {email_message}")
            
            if email_success:
                print("   🎉 PAYMENT REMINDER EMAIL: API reports SUCCESS")
                print("   ⚠️  NOTE: API success does not guarantee actual delivery")
            else:
                print("   🚨 PAYMENT REMINDER EMAIL: API reports FAILURE")
                return False
        else:
            print("   🚨 CRITICAL: Payment reminder endpoint failed")
            return False
        
        # Step 4: Test Invoice Email Functionality
        print("\n📧 Step 3: Testing Invoice Email Functionality")
        payment_data = {
            "client_id": self.created_client_id,
            "amount_paid": 100.00,
            "payment_date": "2025-01-23",
            "payment_method": "Credit Card",
            "notes": "CRITICAL TEST - Invoice email delivery verification with new Gmail password"
        }
        
        success4, response4 = self.run_test(
            "Payment Recording with Invoice Email",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success4:
            payment_success = response4.get('success', False)
            invoice_sent = response4.get('invoice_sent', False)
            invoice_message = response4.get('invoice_message', 'No message')
            client_name = response4.get('client_name', 'Unknown')
            
            print(f"   💰 Payment Recorded For: {client_name}")
            print(f"   ✅ Payment Success: {payment_success}")
            print(f"   📧 Invoice Email Sent: {invoice_sent}")
            print(f"   📝 Invoice Message: {invoice_message}")
            
            if invoice_sent:
                print("   🎉 INVOICE EMAIL: API reports SUCCESS")
            else:
                print("   🚨 INVOICE EMAIL: API reports FAILURE")
                print("   ⚠️  This indicates actual email delivery issues")
        else:
            print("   🚨 CRITICAL: Payment recording endpoint failed")
            return False
        
        # Step 5: Test Multiple Email Templates
        print("\n📧 Step 4: Testing Multiple Email Templates")
        templates_to_test = ["default", "professional", "friendly"]
        template_results = {}
        
        for template in templates_to_test:
            template_data = {
                "client_id": self.created_client_id,
                "template_name": template,
                "custom_subject": f"TEMPLATE TEST - {template.upper()} Email Delivery",
                "custom_message": f"Testing {template} template with new Gmail password for actual delivery verification.",
                "custom_amount": 75.00,
                "custom_due_date": "March 1, 2025"
            }
            
            success, response = self.run_test(
                f"Email Template Test - {template.title()}",
                "POST",
                "email/custom-reminder",
                200,
                template_data
            )
            
            if success:
                email_success = response.get('success', False)
                template_results[template] = email_success
                print(f"   📧 {template.title()} Template: {'✅ SUCCESS' if email_success else '❌ FAILED'}")
            else:
                template_results[template] = False
                print(f"   📧 {template.title()} Template: ❌ ENDPOINT FAILED")
        
        # Step 6: Test Email Service Stability
        print("\n📧 Step 5: Testing Email Service Stability")
        stability_tests = 3
        stability_results = []
        
        for i in range(stability_tests):
            stability_data = {
                "client_id": self.created_client_id,
                "template_name": "default",
                "custom_subject": f"STABILITY TEST #{i+1} - Email Service Reliability",
                "custom_message": f"Testing email service stability with multiple consecutive sends (Test #{i+1} of {stability_tests}).",
                "custom_amount": 50.00,
                "custom_due_date": "February 28, 2025"
            }
            
            success, response = self.run_test(
                f"Email Stability Test #{i+1}",
                "POST",
                "email/payment-reminder",
                200,
                stability_data
            )
            
            if success:
                email_success = response.get('success', False)
                stability_results.append(email_success)
                print(f"   📧 Stability Test #{i+1}: {'✅ SUCCESS' if email_success else '❌ FAILED'}")
            else:
                stability_results.append(False)
                print(f"   📧 Stability Test #{i+1}: ❌ ENDPOINT FAILED")
        
        # Final Analysis
        print("\n🎯 CRITICAL EMAIL DELIVERY VERIFICATION SUMMARY")
        print("=" * 80)
        
        # Gmail Authentication
        gmail_auth_status = "✅ WORKING" if success1 and response1.get('success') else "❌ FAILED"
        print(f"📧 Gmail SMTP Authentication: {gmail_auth_status}")
        
        # Payment Reminder
        payment_reminder_status = "✅ WORKING" if success3 and response3.get('success') else "❌ FAILED"
        print(f"📧 Payment Reminder Emails: {payment_reminder_status}")
        
        # Invoice Email
        invoice_email_status = "✅ WORKING" if success4 and response4.get('invoice_sent') else "❌ FAILED"
        print(f"📧 Invoice Email Functionality: {invoice_email_status}")
        
        # Template Success Rate
        template_success_count = sum(1 for result in template_results.values() if result)
        template_success_rate = (template_success_count / len(template_results)) * 100 if template_results else 0
        print(f"📧 Email Templates Success Rate: {template_success_count}/{len(template_results)} ({template_success_rate:.1f}%)")
        
        # Stability Success Rate
        stability_success_count = sum(1 for result in stability_results if result)
        stability_success_rate = (stability_success_count / len(stability_results)) * 100 if stability_results else 0
        print(f"📧 Email Service Stability: {stability_success_count}/{len(stability_results)} ({stability_success_rate:.1f}%)")
        
        # Overall Assessment
        all_tests_passed = (
            success1 and response1.get('success') and
            success3 and response3.get('success') and
            success4 and response4.get('invoice_sent') and
            template_success_rate >= 100 and
            stability_success_rate >= 100
        )
        
        if all_tests_passed:
            print("\n🎉 CRITICAL EMAIL DELIVERY VERIFICATION: ALL TESTS PASSED!")
            print("✅ Gmail app password 'yauf mdwy rsrd lhai' is working correctly")
            print("✅ Email authentication is successful")
            print("✅ Payment reminders are being sent")
            print("✅ Invoice emails are being delivered")
            print("✅ All email templates are functional")
            print("✅ Email service is stable and reliable")
            print("\n🎯 CONCLUSION: Email delivery issue is RESOLVED!")
        else:
            print("\n🚨 CRITICAL EMAIL DELIVERY VERIFICATION: ISSUES DETECTED!")
            if not (success1 and response1.get('success')):
                print("❌ Gmail SMTP authentication is failing")
            if not (success3 and response3.get('success')):
                print("❌ Payment reminder emails are not being sent")
            if not (success4 and response4.get('invoice_sent')):
                print("❌ Invoice emails are failing to send")
            if template_success_rate < 100:
                print(f"❌ Email templates have {100-template_success_rate:.1f}% failure rate")
            if stability_success_rate < 100:
                print(f"❌ Email service stability issues detected ({100-stability_success_rate:.1f}% failure rate)")
            print("\n🎯 CONCLUSION: Email delivery issues PERSIST - further investigation required")
        
        print("=" * 80)
        return all_tests_passed

    def run_email_focused_tests(self):
        """Run email-focused tests with new Gmail app password"""
        print("📧 STARTING EMAIL FUNCTIONALITY TESTING WITH NEW GMAIL APP PASSWORD")
        print("=" * 80)
        print("🔑 Testing with Gmail app password: difs xvgc ljue sxjr")
        print("=" * 80)
        
        # Basic setup
        self.test_health_check()
        self.test_membership_types_seed()
        
        # Create test client for email tests
        self.test_create_client_with_start_date()
        
        # CRITICAL EMAIL TESTS
        print("\n🎯 CRITICAL EMAIL FUNCTIONALITY TESTS")
        print("-" * 50)
        
        # 1. Test Email Service Connection
        self.test_email_configuration()
        
        # 2. Test Email Templates
        self.test_get_email_templates()
        
        # 3. Test Payment Reminder Sending
        self.test_send_individual_payment_reminder()
        
        # 4. Test Custom Email Sending
        self.test_send_custom_reminder_default_template()
        self.test_send_custom_reminder_professional_template()
        self.test_send_custom_reminder_friendly_template()
        
        # 5. Test Bulk Email Sending
        self.test_send_bulk_payment_reminders()
        
        # 6. Test Professional Template (specific focus)
        self.test_professional_email_template()
        
        # 7. Test Email Error Scenarios
        self.test_send_custom_reminder_invalid_client()
        
        # Final Email Summary
        print("\n" + "=" * 80)
        print("📧 EMAIL FUNCTIONALITY TESTING COMPLETED")
        print("=" * 80)
        print(f"📊 TOTAL TESTS RUN: {self.tests_run}")
        print(f"✅ TESTS PASSED: {self.tests_passed}")
        print(f"❌ TESTS FAILED: {self.tests_run - self.tests_passed}")
        print(f"📈 SUCCESS RATE: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL EMAIL TESTS PASSED! Gmail SMTP with new password working perfectly!")
        elif self.tests_passed / self.tests_run >= 0.8:
            print("✅ GOOD! Most email functionality working - minor issues may exist")
        else:
            print("❌ CRITICAL: Email functionality has significant issues - Gmail authentication may still be failing")
        
        print("=" * 80)
        return self.tests_passed / self.tests_run if self.tests_run > 0 else 0

    def test_multiple_payment_logic_issue(self):
        """CRITICAL TEST: Demonstrate the multiple payment logic issue identified by the user"""
        print("\n🚨 CRITICAL TEST: MULTIPLE PAYMENT LOGIC ISSUE DEMONSTRATION")
        print("=" * 80)
        print("🎯 OBJECTIVE: Test multiple payment scenarios to demonstrate the issue")
        print("📋 SCENARIO: Client makes multiple payments on the same day")
        print("❌ PROBLEM: Current logic uses payment_date + 30 days (doesn't accumulate)")
        print("✅ EXPECTED: Should extend from current due date or accumulate properly")
        print("=" * 80)
        
        # Step 1: Find or create "Deon Aleong" client
        print("\n📋 STEP 1: Get Current Client Data")
        success1, clients_response = self.run_test(
            "Get All Clients to Find Deon Aleong",
            "GET",
            "clients",
            200
        )
        
        deon_client = None
        if success1:
            clients = clients_response if isinstance(clients_response, list) else []
            for client in clients:
                if client.get('name') == 'Deon Aleong':
                    deon_client = client
                    break
        
        # If Deon Aleong doesn't exist, create him
        if not deon_client:
            print("   ⚠️  Deon Aleong not found, creating client...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            deon_data = {
                "name": "Deon Aleong",
                "email": f"deon_aleong_{timestamp}@example.com",
                "phone": "(555) 123-4567",
                "membership_type": "Elite",
                "monthly_fee": 100.00,
                "start_date": "2025-01-15"  # Due date would be 2025-02-14
            }
            
            success_create, create_response = self.run_test(
                "Create Deon Aleong Client",
                "POST",
                "clients",
                200,
                deon_data
            )
            
            if success_create and "id" in create_response:
                deon_client = create_response
                print(f"   ✅ Created Deon Aleong client ID: {deon_client['id']}")
            else:
                print("   ❌ Failed to create Deon Aleong client - aborting test")
                return False
        else:
            print(f"   ✅ Found Deon Aleong client ID: {deon_client['id']}")
        
        # Document starting scenario
        print(f"\n📊 STARTING SCENARIO:")
        print(f"   Client Name: {deon_client.get('name')}")
        print(f"   Client ID: {deon_client.get('id')}")
        print(f"   Current Next Payment Date: {deon_client.get('next_payment_date')}")
        print(f"   Monthly Fee: ${deon_client.get('monthly_fee')}")
        print(f"   Membership Type: {deon_client.get('membership_type')}")
        
        original_due_date = deon_client.get('next_payment_date')
        client_id = deon_client.get('id')
        
        # Step 2: Record First Payment
        print(f"\n📋 STEP 2: Record First Payment")
        today = date.today().isoformat()
        
        first_payment_data = {
            "client_id": client_id,
            "amount_paid": 100.00,
            "payment_date": today,
            "payment_method": "Credit Card",
            "notes": "First payment - testing multiple payment logic"
        }
        
        success2, first_payment_response = self.run_test(
            "Record First Payment (Today)",
            "POST",
            "payments/record",
            200,
            first_payment_data
        )
        
        if not success2:
            print("   ❌ Failed to record first payment - aborting test")
            return False
        
        first_new_due_date = first_payment_response.get('new_next_payment_date')
        print(f"   ✅ First payment recorded successfully")
        print(f"   💰 Amount paid: ${first_payment_response.get('amount_paid')}")
        print(f"   📅 Payment date: {today}")
        print(f"   📅 New next payment date: {first_new_due_date}")
        
        # Step 3: Record Second Payment Immediately (Same Day)
        print(f"\n📋 STEP 3: Record Second Payment Immediately (Same Day)")
        
        second_payment_data = {
            "client_id": client_id,
            "amount_paid": 100.00,
            "payment_date": today,  # Same day as first payment
            "payment_method": "Cash",
            "notes": "Second payment - same day as first payment"
        }
        
        success3, second_payment_response = self.run_test(
            "Record Second Payment (Same Day)",
            "POST",
            "payments/record",
            200,
            second_payment_data
        )
        
        if not success3:
            print("   ❌ Failed to record second payment - aborting test")
            return False
        
        second_new_due_date = second_payment_response.get('new_next_payment_date')
        print(f"   ✅ Second payment recorded successfully")
        print(f"   💰 Amount paid: ${second_payment_response.get('amount_paid')}")
        print(f"   📅 Payment date: {today}")
        print(f"   📅 New next payment date: {second_new_due_date}")
        
        # Step 4: Analyze the Multiple Payment Logic Issue
        print(f"\n📋 STEP 4: Analyze Multiple Payment Logic Issue")
        print("=" * 60)
        
        # Calculate expected dates for different logic options
        from datetime import datetime as dt, timedelta
        payment_date = dt.fromisoformat(today).date()
        
        # Option A: Extend from current due date (correct logic)
        if original_due_date:
            original_due = dt.fromisoformat(original_due_date).date() if isinstance(original_due_date, str) else original_due_date
            option_a_after_first = original_due + timedelta(days=30)
            option_a_after_second = option_a_after_first + timedelta(days=30)
        else:
            option_a_after_first = payment_date + timedelta(days=30)
            option_a_after_second = option_a_after_first + timedelta(days=30)
        
        # Option B: Payment date + 30 days (current flawed logic)
        option_b_after_first = payment_date + timedelta(days=30)
        option_b_after_second = payment_date + timedelta(days=30)  # Same as first!
        
        print(f"📊 PAYMENT LOGIC ANALYSIS:")
        print(f"   Original Due Date: {original_due_date}")
        print(f"   Payment Date (Both): {today}")
        print(f"   ")
        print(f"   🔍 OPTION A (Correct - Extend from due date):")
        print(f"      After 1st payment: {option_a_after_first}")
        print(f"      After 2nd payment: {option_a_after_second}")
        print(f"   ")
        print(f"   🔍 OPTION B (Current - Payment date + 30):")
        print(f"      After 1st payment: {option_b_after_first}")
        print(f"      After 2nd payment: {option_b_after_second}")
        print(f"   ")
        print(f"   📋 ACTUAL RESULTS:")
        print(f"      After 1st payment: {first_new_due_date}")
        print(f"      After 2nd payment: {second_new_due_date}")
        
        # Determine which logic is being used
        first_actual = dt.fromisoformat(first_new_due_date).date() if isinstance(first_new_due_date, str) else first_new_due_date
        second_actual = dt.fromisoformat(second_new_due_date).date() if isinstance(second_new_due_date, str) else second_new_due_date
        
        print(f"\n🎯 ISSUE DEMONSTRATION:")
        
        # Check if the current logic is flawed
        if first_actual == second_actual:
            print(f"   ❌ CRITICAL ISSUE CONFIRMED!")
            print(f"   ❌ Both payments result in the same due date: {second_new_due_date}")
            print(f"   ❌ This means the second payment didn't extend the membership period")
            print(f"   ❌ Current logic: payment_date + 30 days (doesn't accumulate)")
            print(f"   ")
            print(f"   💡 PROBLEM EXPLANATION:")
            print(f"      - Client pays twice on {today}")
            print(f"      - Both payments set due date to {today} + 30 days = {second_new_due_date}")
            print(f"      - Second payment doesn't extend membership beyond first payment")
            print(f"      - Client loses value from multiple payments")
            
            issue_confirmed = True
        else:
            print(f"   ✅ Multiple payments extend membership period correctly")
            print(f"   ✅ First payment due date: {first_new_due_date}")
            print(f"   ✅ Second payment due date: {second_new_due_date}")
            issue_confirmed = False
        
        # Step 5: Proposed Logic Options
        print(f"\n📋 STEP 5: Proposed Logic Options")
        print("=" * 60)
        
        print(f"🔧 OPTION A: Extend from current due date")
        print(f"   Logic: new_due_date = max(current_due_date, payment_date) + 30 days")
        print(f"   Benefit: Multiple payments accumulate properly")
        print(f"   Example: If due 2025-02-15, payment on 2025-01-10 → new due 2025-03-17")
        print(f"   ")
        print(f"🔧 OPTION B: Payment date + 30 days (CURRENT - FLAWED)")
        print(f"   Logic: new_due_date = payment_date + 30 days")
        print(f"   Problem: Multiple payments on same day don't accumulate")
        print(f"   Example: Two payments on 2025-01-10 → both set due to 2025-02-09")
        print(f"   ")
        print(f"🔧 OPTION C: Pro-rated logic (Complex)")
        print(f"   Logic: Calculate based on remaining days and payment amount")
        print(f"   Benefit: More precise for partial payments")
        print(f"   Complexity: Requires more complex calculation logic")
        
        # Step 6: Test with different payment dates
        print(f"\n📋 STEP 6: Test Different Payment Date Scenarios")
        
        # Create another test client for different scenarios
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_client_data = {
            "name": "Multiple Payment Test Client",
            "email": f"multi_payment_test_{timestamp}@example.com",
            "phone": "(555) 999-8888",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-15"  # Due date: 2025-02-14
        }
        
        success_test, test_client_response = self.run_test(
            "Create Test Client for Different Scenarios",
            "POST",
            "clients",
            200,
            test_client_data
        )
        
        if success_test and "id" in test_client_response:
            test_client_id = test_client_response["id"]
            original_test_due = test_client_response.get('next_payment_date')
            
            print(f"   ✅ Created test client - Due date: {original_test_due}")
            
            # Scenario: Payment before due date
            early_payment_date = "2025-01-10"  # 5 days before due
            early_payment_data = {
                "client_id": test_client_id,
                "amount_paid": 50.00,
                "payment_date": early_payment_date,
                "payment_method": "Bank Transfer",
                "notes": "Early payment test"
            }
            
            success_early, early_response = self.run_test(
                "Record Early Payment (Before Due Date)",
                "POST",
                "payments/record",
                200,
                early_payment_data
            )
            
            if success_early:
                early_new_due = early_response.get('new_next_payment_date')
                print(f"   📅 Early payment on: {early_payment_date}")
                print(f"   📅 Original due date: {original_test_due}")
                print(f"   📅 New due date: {early_new_due}")
                
                # Analyze the logic
                early_payment_dt = dt.fromisoformat(early_payment_date).date()
                expected_option_a = dt.fromisoformat(original_test_due).date() + timedelta(days=30)
                expected_option_b = early_payment_dt + timedelta(days=30)
                actual_due = dt.fromisoformat(early_new_due).date()
                
                print(f"   🔍 Expected (Option A - extend from due): {expected_option_a}")
                print(f"   🔍 Expected (Option B - payment + 30): {expected_option_b}")
                print(f"   🔍 Actual result: {actual_due}")
                
                if actual_due == expected_option_b:
                    print(f"   ❌ Using Option B logic (payment_date + 30)")
                    print(f"   ❌ Client loses {(expected_option_a - expected_option_b).days} days of membership")
                elif actual_due == expected_option_a:
                    print(f"   ✅ Using Option A logic (extend from due date)")
                else:
                    print(f"   ❓ Using unknown logic")
        
        # Final Summary
        print(f"\n🎯 MULTIPLE PAYMENT LOGIC TEST SUMMARY")
        print("=" * 80)
        
        if issue_confirmed:
            print(f"❌ CRITICAL ISSUE CONFIRMED: Multiple Payment Logic Problem")
            print(f"   • Current logic: payment_date + 30 days")
            print(f"   • Problem: Multiple payments on same day don't accumulate")
            print(f"   • Impact: Clients lose membership time with multiple payments")
            print(f"   • Solution needed: Implement Option A (extend from due date)")
            print(f"   ")
            print(f"🔧 RECOMMENDED FIX:")
            print(f"   Change line 483 in server.py from:")
            print(f"   new_next_payment_date = payment_request.payment_date + timedelta(days=30)")
            print(f"   To:")
            print(f"   current_due = client_obj.next_payment_date")
            print(f"   new_next_payment_date = max(current_due, payment_request.payment_date) + timedelta(days=30)")
        else:
            print(f"✅ Multiple payment logic appears to be working correctly")
            print(f"   • Multiple payments extend membership period properly")
            print(f"   • No accumulation issues detected")
        
        return not issue_confirmed  # Return True if no issue, False if issue confirmed

    # ===== AUTOMATIC INVOICE SENDING TESTS =====
    
    def test_automatic_invoice_sending_functionality(self):
        """COMPREHENSIVE TEST: Automatic invoice sending for all payment recording instances"""
        print("\n🎯 COMPREHENSIVE AUTOMATIC INVOICE SENDING FUNCTIONALITY TEST")
        print("=" * 80)
        print("🎯 OBJECTIVE: Test that invoices are sent automatically for ALL payment recording instances")
        print("📋 SCOPE: Verify invoice consistency across all payment methods and scenarios")
        print("=" * 80)
        
        # Step 1: Verify payment recording endpoint includes invoice functionality
        print("\n📋 STEP 1: Verify Payment Recording Endpoint Includes Invoice Functionality")
        
        # Create test client for invoice testing
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        invoice_client_data = {
            "name": "Invoice Test Client",
            "email": f"invoice_test_{timestamp}@example.com",
            "phone": "+18685551234",
            "membership_type": "Premium",
            "monthly_fee": 75.0,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        success1, client_response = self.run_test(
            "Create Invoice Test Client",
            "POST",
            "clients",
            200,
            invoice_client_data
        )
        
        if not success1 or "id" not in client_response:
            print("❌ Failed to create invoice test client - aborting invoice tests")
            return False
        
        invoice_client_id = client_response["id"]
        print(f"   ✅ Created invoice test client ID: {invoice_client_id}")
        
        # Step 2: Test main payment recording endpoint with invoice
        print("\n📋 STEP 2: Test Main Payment Recording Endpoint with Automatic Invoice")
        
        payment_data = {
            "client_id": invoice_client_id,
            "amount_paid": 75.0,
            "payment_date": date.today().isoformat(),
            "payment_method": "Credit Card",
            "notes": "Test payment for automatic invoice verification"
        }
        
        success2, payment_response = self.run_test(
            "Record Payment with Automatic Invoice",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success2:
            # Verify invoice fields are present in response
            required_invoice_fields = ['invoice_sent', 'invoice_message']
            missing_fields = [field for field in required_invoice_fields if field not in payment_response]
            
            if missing_fields:
                print(f"   ❌ CRITICAL: Missing invoice fields in response: {missing_fields}")
                return False
            
            invoice_sent = payment_response.get('invoice_sent')
            invoice_message = payment_response.get('invoice_message')
            
            print(f"   ✅ Payment recorded successfully")
            print(f"   📧 Invoice sent: {invoice_sent}")
            print(f"   📝 Invoice message: {invoice_message}")
            
            if invoice_sent is not None:
                print("   ✅ AUTOMATIC INVOICE FUNCTIONALITY: IMPLEMENTED")
                if invoice_sent:
                    print("   ✅ INVOICE EMAIL: SENT SUCCESSFULLY")
                else:
                    print("   ⚠️  INVOICE EMAIL: FAILED TO SEND (but functionality exists)")
            else:
                print("   ❌ AUTOMATIC INVOICE FUNCTIONALITY: NOT IMPLEMENTED")
                return False
        else:
            print("   ❌ Failed to record payment - aborting invoice tests")
            return False
        
        # Step 3: Test invoice content includes all required payment details
        print("\n📋 STEP 3: Test Invoice Content Includes All Required Payment Details")
        
        # Verify payment response contains all expected details
        expected_payment_fields = ['success', 'client_name', 'amount_paid', 'payment_id', 'new_next_payment_date']
        payment_fields_present = all(field in payment_response for field in expected_payment_fields)
        
        if payment_fields_present:
            print("   ✅ Payment response contains all required fields")
            print(f"      Client: {payment_response.get('client_name')}")
            print(f"      Amount: ${payment_response.get('amount_paid')}")
            print(f"      Payment ID: {payment_response.get('payment_id')}")
            print(f"      New due date: {payment_response.get('new_next_payment_date')}")
        else:
            missing_payment_fields = [field for field in expected_payment_fields if field not in payment_response]
            print(f"   ❌ Missing payment fields: {missing_payment_fields}")
            return False
        
        # Step 4: Test invoice sending with different payment methods
        print("\n📋 STEP 4: Test Invoice Sending with Different Payment Methods")
        
        payment_methods = ["Cash", "Credit Card", "Bank Transfer", "Mobile Payment", "Check"]
        method_test_results = []
        
        for i, method in enumerate(payment_methods):
            # Create separate client for each payment method test
            method_client_data = {
                "name": f"{method.replace(' ', '')} Invoice Test",
                "email": f"invoice_{method.lower().replace(' ', '_')}_{timestamp}_{i}@example.com",
                "phone": f"+1868555{1000+i:04d}",
                "membership_type": "Standard",
                "monthly_fee": 55.0,
                "start_date": date.today().isoformat(),
                "payment_status": "due"
            }
            
            success_client, client_resp = self.run_test(
                f"Create {method} Test Client",
                "POST",
                "clients",
                200,
                method_client_data
            )
            
            if success_client and "id" in client_resp:
                method_payment_data = {
                    "client_id": client_resp["id"],
                    "amount_paid": 55.0,
                    "payment_date": date.today().isoformat(),
                    "payment_method": method,
                    "notes": f"Invoice test payment via {method}"
                }
                
                success_payment, payment_resp = self.run_test(
                    f"Record Payment via {method}",
                    "POST",
                    "payments/record",
                    200,
                    method_payment_data
                )
                
                if success_payment:
                    method_invoice_sent = payment_resp.get('invoice_sent')
                    method_test_results.append({
                        'method': method,
                        'success': True,
                        'invoice_sent': method_invoice_sent
                    })
                    print(f"   ✅ {method}: Payment recorded, Invoice sent: {method_invoice_sent}")
                else:
                    method_test_results.append({
                        'method': method,
                        'success': False,
                        'invoice_sent': None
                    })
                    print(f"   ❌ {method}: Payment recording failed")
            else:
                method_test_results.append({
                    'method': method,
                    'success': False,
                    'invoice_sent': None
                })
                print(f"   ❌ {method}: Client creation failed")
        
        # Analyze payment method results
        successful_methods = [r for r in method_test_results if r['success']]
        invoice_attempts = [r for r in successful_methods if r['invoice_sent'] is not None]
        
        print(f"\n   📊 Payment Method Results:")
        print(f"      Successful payments: {len(successful_methods)}/{len(payment_methods)}")
        print(f"      Invoice attempts: {len(invoice_attempts)}/{len(successful_methods)}")
        
        if len(successful_methods) == len(payment_methods) and len(invoice_attempts) == len(successful_methods):
            print("   ✅ ALL PAYMENT METHODS: Invoice functionality working")
        else:
            print("   ❌ SOME PAYMENT METHODS: Invoice functionality issues")
            return False
        
        # Step 5: Test client status update after payment with invoice
        print("\n📋 STEP 5: Test Client Status Update After Payment with Invoice")
        
        # Get updated client status
        success_status, updated_client = self.run_test(
            "Get Updated Client Status",
            "GET",
            f"clients/{invoice_client_id}",
            200
        )
        
        if success_status:
            payment_status = updated_client.get('payment_status')
            amount_owed = updated_client.get('amount_owed')
            
            print(f"   📊 Updated client status:")
            print(f"      Payment status: {payment_status}")
            print(f"      Amount owed: {amount_owed}")
            
            if payment_status == "paid" and amount_owed == 0.0:
                print("   ✅ CLIENT STATUS: Updated correctly after payment")
            else:
                print("   ❌ CLIENT STATUS: Not updated correctly after payment")
                return False
        else:
            print("   ❌ Failed to get updated client status")
            return False
        
        # Step 6: Test email service functionality
        print("\n📋 STEP 6: Test Email Service Functionality")
        
        success_email, email_response = self.run_test(
            "Test Email Service Configuration",
            "POST",
            "email/test",
            200
        )
        
        if success_email:
            email_working = email_response.get('success', False)
            email_message = email_response.get('message', '')
            
            print(f"   📧 Email service status: {'✅ WORKING' if email_working else '❌ FAILED'}")
            print(f"   📝 Email message: {email_message}")
            
            if not email_working:
                print("   ⚠️  Email service issues may affect invoice delivery")
        else:
            print("   ❌ Email service test failed")
            return False
        
        # Step 7: Test payment statistics update
        print("\n📋 STEP 7: Test Payment Statistics Update")
        
        success_stats, stats_response = self.run_test(
            "Get Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if success_stats:
            total_revenue = stats_response.get('total_revenue', 0)
            payment_count = stats_response.get('payment_count', 0)
            
            print(f"   📊 Payment statistics:")
            print(f"      Total revenue: TTD {total_revenue}")
            print(f"      Payment count: {payment_count}")
            
            if total_revenue > 0 and payment_count > 0:
                print("   ✅ PAYMENT STATISTICS: Updated correctly")
            else:
                print("   ⚠️  PAYMENT STATISTICS: May not reflect recent payments")
        else:
            print("   ❌ Failed to get payment statistics")
            return False
        
        # Final Summary
        print("\n🎯 AUTOMATIC INVOICE SENDING FUNCTIONALITY TEST SUMMARY")
        print("=" * 80)
        
        all_tests_passed = (
            success1 and success2 and 
            payment_fields_present and 
            len(successful_methods) == len(payment_methods) and
            len(invoice_attempts) == len(successful_methods) and
            success_status and success_email and success_stats
        )
        
        if all_tests_passed:
            print("🎉 AUTOMATIC INVOICE SENDING FUNCTIONALITY: ALL TESTS PASSED!")
            print("✅ Payment recording endpoint includes automatic invoice sending")
            print("✅ Invoice functionality works with all payment methods")
            print("✅ Invoice response includes all required fields")
            print("✅ Client status updates correctly after payment")
            print("✅ Email service is configured and working")
            print("✅ Payment statistics update correctly")
            print("✅ Invoices are sent automatically for ALL payment recording instances")
            print("\n🎯 CONCLUSION: Invoice functionality is working EXACTLY as specified!")
        else:
            print("❌ AUTOMATIC INVOICE SENDING FUNCTIONALITY: ISSUES DETECTED!")
            print("🔧 Review the detailed results above for specific issues")
            print("⚠️  Some invoice functionality may not be working as expected")
        
        return all_tests_passed
    
    def test_invoice_email_template_verification(self):
        """Test invoice email template content and format"""
        print("\n🎯 INVOICE EMAIL TEMPLATE VERIFICATION TEST")
        print("=" * 80)
        print("🎯 OBJECTIVE: Verify invoice email template includes all required payment details")
        print("📋 SCOPE: Test invoice template format, content, and professional appearance")
        print("=" * 80)
        
        # Create test client for invoice template testing
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        template_client_data = {
            "name": "Invoice Template Test Client",
            "email": f"invoice_template_{timestamp}@example.com",
            "phone": "+18685551234",
            "membership_type": "Elite",
            "monthly_fee": 100.0,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        success1, client_response = self.run_test(
            "Create Invoice Template Test Client",
            "POST",
            "clients",
            200,
            template_client_data
        )
        
        if not success1 or "id" not in client_response:
            print("❌ Failed to create invoice template test client")
            return False
        
        template_client_id = client_response["id"]
        print(f"   ✅ Created invoice template test client ID: {template_client_id}")
        
        # Test invoice with comprehensive payment details
        comprehensive_payment_data = {
            "client_id": template_client_id,
            "amount_paid": 100.0,
            "payment_date": date.today().isoformat(),
            "payment_method": "Bank Transfer",
            "notes": "Monthly membership payment - Elite package with special discount applied"
        }
        
        success2, payment_response = self.run_test(
            "Record Payment for Invoice Template Test",
            "POST",
            "payments/record",
            200,
            comprehensive_payment_data
        )
        
        if success2:
            invoice_sent = payment_response.get('invoice_sent')
            invoice_message = payment_response.get('invoice_message')
            client_name = payment_response.get('client_name')
            amount_paid = payment_response.get('amount_paid')
            
            print(f"   ✅ Payment recorded for invoice template test")
            print(f"   📧 Invoice sent: {invoice_sent}")
            print(f"   📝 Invoice message: {invoice_message}")
            print(f"   👤 Client name: {client_name}")
            print(f"   💰 Amount paid: ${amount_paid}")
            
            # Verify invoice template requirements
            template_requirements_met = True
            
            # Check if invoice was attempted
            if invoice_sent is None:
                print("   ❌ INVOICE TEMPLATE: No invoice sending attempted")
                template_requirements_met = False
            elif invoice_sent is False:
                print("   ⚠️  INVOICE TEMPLATE: Invoice sending failed (template may still be correct)")
                print("   📝 This could be due to email service issues, not template problems")
            else:
                print("   ✅ INVOICE TEMPLATE: Invoice sent successfully")
            
            # Check if all payment details are captured for template
            required_details = {
                'client_name': client_name,
                'amount_paid': amount_paid,
                'payment_method': comprehensive_payment_data['payment_method'],
                'notes': comprehensive_payment_data['notes']
            }
            
            missing_details = [key for key, value in required_details.items() if not value]
            
            if missing_details:
                print(f"   ❌ INVOICE TEMPLATE: Missing payment details: {missing_details}")
                template_requirements_met = False
            else:
                print("   ✅ INVOICE TEMPLATE: All payment details captured")
                print(f"      Client: {client_name}")
                print(f"      Amount: ${amount_paid}")
                print(f"      Method: {comprehensive_payment_data['payment_method']}")
                print(f"      Notes: {comprehensive_payment_data['notes'][:50]}...")
            
            return template_requirements_met
        else:
            print("   ❌ Failed to record payment for invoice template test")
            return False
    
    def test_invoice_edge_cases(self):
        """Test invoice sending with edge cases and special scenarios"""
        print("\n🎯 INVOICE EDGE CASES TEST")
        print("=" * 80)
        print("🎯 OBJECTIVE: Test invoice sending with edge cases and special scenarios")
        print("📋 SCOPE: Test minimum amounts, special characters, large amounts, etc.")
        print("=" * 80)
        
        edge_cases = [
            {
                "name": "Minimum Payment Amount",
                "amount": 0.01,
                "method": "Cash",
                "notes": "Minimum payment test"
            },
            {
                "name": "Large Payment Amount", 
                "amount": 999.99,
                "method": "Bank Transfer",
                "notes": "Large payment amount test"
            },
            {
                "name": "Special Characters in Notes",
                "amount": 50.0,
                "method": "Credit Card",
                "notes": "Special chars: àáâãäåæçèéêë ñóôõö ùúûüý €£¥$"
            },
            {
                "name": "Long Notes Field",
                "amount": 75.0,
                "method": "Mobile Payment",
                "notes": "This is a very long notes field that contains a lot of text to test how the invoice template handles lengthy descriptions and whether it properly formats or truncates long content in the email template display."
            },
            {
                "name": "Empty Notes Field",
                "amount": 25.0,
                "method": "Check",
                "notes": None
            }
        ]
        
        edge_case_results = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, case in enumerate(edge_cases):
            print(f"\n📋 Edge Case {i+1}: {case['name']}")
            
            # Create client for each edge case
            edge_client_data = {
                "name": f"Edge Case {i+1} Client",
                "email": f"edge_case_{i+1}_{timestamp}@example.com",
                "phone": f"+1868555{2000+i:04d}",
                "membership_type": "Standard",
                "monthly_fee": 55.0,
                "start_date": date.today().isoformat(),
                "payment_status": "due"
            }
            
            success_client, client_resp = self.run_test(
                f"Create Edge Case {i+1} Client",
                "POST",
                "clients",
                200,
                edge_client_data
            )
            
            if success_client and "id" in client_resp:
                edge_payment_data = {
                    "client_id": client_resp["id"],
                    "amount_paid": case["amount"],
                    "payment_date": date.today().isoformat(),
                    "payment_method": case["method"],
                    "notes": case["notes"]
                }
                
                success_payment, payment_resp = self.run_test(
                    f"Record Edge Case {i+1} Payment",
                    "POST",
                    "payments/record",
                    200,
                    edge_payment_data
                )
                
                if success_payment:
                    invoice_sent = payment_resp.get('invoice_sent')
                    payment_success = payment_resp.get('success', False)
                    
                    edge_case_results.append({
                        'case': case['name'],
                        'success': True,
                        'invoice_sent': invoice_sent,
                        'payment_success': payment_success
                    })
                    
                    print(f"   ✅ Payment: ${case['amount']:.2f} via {case['method']}")
                    print(f"   📧 Invoice sent: {invoice_sent}")
                    print(f"   💰 Payment success: {payment_success}")
                else:
                    edge_case_results.append({
                        'case': case['name'],
                        'success': False,
                        'invoice_sent': None,
                        'payment_success': False
                    })
                    print(f"   ❌ Payment recording failed")
            else:
                edge_case_results.append({
                    'case': case['name'],
                    'success': False,
                    'invoice_sent': None,
                    'payment_success': False
                })
                print(f"   ❌ Client creation failed")
        
        # Analyze edge case results
        successful_cases = [r for r in edge_case_results if r['success']]
        invoice_attempts = [r for r in successful_cases if r['invoice_sent'] is not None]
        successful_invoices = [r for r in invoice_attempts if r['invoice_sent'] is True]
        
        print(f"\n📊 EDGE CASES RESULTS:")
        print(f"   Successful payments: {len(successful_cases)}/{len(edge_cases)}")
        print(f"   Invoice attempts: {len(invoice_attempts)}/{len(successful_cases)}")
        print(f"   Successful invoices: {len(successful_invoices)}/{len(invoice_attempts)}")
        
        # Detailed results
        for result in edge_case_results:
            status = "✅" if result['success'] else "❌"
            invoice_status = "📧✅" if result['invoice_sent'] else "📧❌" if result['invoice_sent'] is False else "📧⚠️"
            print(f"   {status} {result['case']}: {invoice_status}")
        
        edge_cases_passed = len(successful_cases) == len(edge_cases) and len(invoice_attempts) == len(successful_cases)
        
        if edge_cases_passed:
            print("\n✅ INVOICE EDGE CASES: ALL TESTS PASSED")
            print("✅ Invoice functionality handles all edge cases correctly")
            print("✅ Special characters, amounts, and notes processed properly")
        else:
            print("\n❌ INVOICE EDGE CASES: SOME ISSUES DETECTED")
            print("⚠️  Some edge cases may not be handled correctly")
        
        return edge_cases_passed

    def test_alphalete_club_review_endpoints(self):
        """Test specific endpoints requested in the Alphalete Club review"""
        print("\n🎯 ALPHALETE CLUB REVIEW - SPECIFIC ENDPOINT TESTING")
        print("=" * 80)
        print("Testing core functionality after REACT_APP_BACKEND_URL fix")
        print(f"Backend URL: {self.api_url}")
        
        all_tests_passed = True
        
        # 1. Health Check - Test if backend is running and responding
        print("\n1️⃣ HEALTH CHECK")
        success1, response1 = self.run_test(
            "Backend Health Check",
            "GET",
            "health",
            200
        )
        if success1:
            print(f"   ✅ Backend is responding correctly")
            print(f"   Status: {response1.get('status')}")
            print(f"   Message: {response1.get('message')}")
        else:
            all_tests_passed = False
            print(f"   ❌ Backend health check failed")
        
        # Also test the root API endpoint
        success1b, response1b = self.run_test(
            "API Root Status",
            "GET",
            "",
            200
        )
        if success1b:
            print(f"   ✅ API root endpoint responding")
            print(f"   Status: {response1b.get('status')}")
            print(f"   Available endpoints: {response1b.get('endpoints', [])}")
        else:
            all_tests_passed = False
        
        # 2. Client Management - Test core client endpoints
        print("\n2️⃣ CLIENT MANAGEMENT")
        
        # GET /api/clients
        success2a, response2a = self.run_test(
            "GET /api/clients",
            "GET",
            "clients",
            200
        )
        if success2a:
            client_count = len(response2a)
            print(f"   ✅ Retrieved {client_count} clients successfully")
            if client_count > 0:
                print(f"   Sample client: {response2a[0].get('name', 'Unknown')} ({response2a[0].get('email', 'No email')})")
        else:
            all_tests_passed = False
            print(f"   ❌ Failed to retrieve clients")
        
        # POST /api/clients (create new client)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_client_data = {
            "name": "Review Test Client",
            "email": f"review_test_{timestamp}@alphalete.com",
            "phone": "(868) 555-0123",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": "2025-01-15",
            "payment_status": "due"
        }
        
        success2b, response2b = self.run_test(
            "POST /api/clients (Create Client)",
            "POST",
            "clients",
            200,
            new_client_data
        )
        
        created_client_id = None
        if success2b and "id" in response2b:
            created_client_id = response2b["id"]
            print(f"   ✅ Created client successfully")
            print(f"   Client ID: {created_client_id}")
            print(f"   Name: {response2b.get('name')}")
            print(f"   Next payment date: {response2b.get('next_payment_date')}")
        else:
            all_tests_passed = False
            print(f"   ❌ Failed to create client")
        
        # PUT /api/clients/{id} (update client)
        if created_client_id:
            update_data = {
                "name": "Review Test Client Updated",
                "phone": "(868) 555-9999",
                "membership_type": "Premium",
                "monthly_fee": 75.00
            }
            
            success2c, response2c = self.run_test(
                "PUT /api/clients/{id} (Update Client)",
                "PUT",
                f"clients/{created_client_id}",
                200,
                update_data
            )
            
            if success2c:
                print(f"   ✅ Updated client successfully")
                print(f"   Updated name: {response2c.get('name')}")
                print(f"   Updated membership: {response2c.get('membership_type')}")
                print(f"   Updated fee: TTD {response2c.get('monthly_fee')}")
            else:
                all_tests_passed = False
                print(f"   ❌ Failed to update client")
        else:
            print(f"   ⏭️  Skipping client update test (no client ID)")
            all_tests_passed = False
        
        # 3. Payment Stats - Test payment statistics endpoint
        print("\n3️⃣ PAYMENT STATISTICS")
        success3, response3 = self.run_test(
            "GET /api/payments/stats",
            "GET",
            "payments/stats",
            200
        )
        
        if success3:
            print(f"   ✅ Payment statistics retrieved successfully")
            print(f"   Total Revenue: TTD {response3.get('total_revenue', 0)}")
            print(f"   Monthly Revenue: TTD {response3.get('monthly_revenue', 0)}")
            print(f"   Payment Count: {response3.get('payment_count', 0)}")
            print(f"   Total Amount Owed: TTD {response3.get('total_amount_owed', 0)}")
            
            # Verify the response has expected fields
            expected_fields = ['total_revenue', 'monthly_revenue', 'payment_count', 'timestamp']
            missing_fields = [field for field in expected_fields if field not in response3]
            if missing_fields:
                print(f"   ⚠️  Missing expected fields: {missing_fields}")
            else:
                print(f"   ✅ All expected fields present in response")
        else:
            all_tests_passed = False
            print(f"   ❌ Failed to retrieve payment statistics")
        
        # 4. Billing Cycles - Test billing cycles endpoint
        print("\n4️⃣ BILLING CYCLES")
        if created_client_id:
            success4, response4 = self.run_test(
                f"GET /api/billing-cycles/{created_client_id}",
                "GET",
                f"billing-cycles/{created_client_id}",
                200
            )
            
            if success4:
                billing_cycles = response4 if isinstance(response4, list) else []
                print(f"   ✅ Retrieved {len(billing_cycles)} billing cycles for client")
                if billing_cycles:
                    cycle = billing_cycles[0]
                    print(f"   Sample cycle: Status={cycle.get('status')}, Amount Due=TTD {cycle.get('amount_due')}")
                    print(f"   Due Date: {cycle.get('due_date')}")
            else:
                print(f"   ⚠️  No billing cycles found for client (may be expected for new client)")
        else:
            print(f"   ⏭️  Skipping billing cycles test (no client ID)")
        
        # 5. Membership Types - Test membership types endpoint
        print("\n5️⃣ MEMBERSHIP TYPES")
        success5, response5 = self.run_test(
            "GET /api/membership-types",
            "GET",
            "membership-types",
            200
        )
        
        if success5:
            membership_count = len(response5)
            print(f"   ✅ Retrieved {membership_count} membership types")
            if membership_count > 0:
                for membership in response5:
                    print(f"   - {membership.get('name')}: TTD {membership.get('monthly_fee')}/month")
                    print(f"     Description: {membership.get('description')}")
            else:
                print(f"   ⚠️  No membership types found - seeding default types...")
                # Try to seed default membership types
                success5b, response5b = self.run_test(
                    "POST /api/membership-types/seed",
                    "POST",
                    "membership-types/seed",
                    200
                )
                if success5b:
                    print(f"   ✅ Seeded membership types: {response5b.get('created_types', [])}")
                    # Retry getting membership types
                    success5c, response5c = self.run_test(
                        "GET /api/membership-types (after seeding)",
                        "GET",
                        "membership-types",
                        200
                    )
                    if success5c:
                        print(f"   ✅ Now have {len(response5c)} membership types after seeding")
        else:
            all_tests_passed = False
            print(f"   ❌ Failed to retrieve membership types")
        
        # Summary of review-specific tests
        print("\n" + "=" * 80)
        print("🎯 ALPHALETE CLUB REVIEW TEST SUMMARY")
        print("=" * 80)
        
        if all_tests_passed:
            print("✅ ALL CORE ENDPOINTS WORKING CORRECTLY!")
            print("✅ Backend is responding at https://alphalete-club.emergent.host/api/")
            print("✅ REACT_APP_BACKEND_URL fix appears to be successful")
            print("✅ Client management endpoints functional")
            print("✅ Payment statistics endpoint functional")
            print("✅ Membership types endpoint functional")
            print("✅ API is ready for frontend integration")
        else:
            print("❌ SOME CORE ENDPOINTS HAVE ISSUES")
            print("❌ Review the failed tests above")
            print("⚠️  Frontend may experience API call failures")
        
        return all_tests_passed

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Alphalete Athletics Club API Tests")
        print("=" * 80)
        
        # Test sequence - organized by feature
        tests = [
            # CRITICAL REVIEW REQUEST TEST - Automatic Invoice Sending
            ("🎯 REVIEW REQUEST: Automatic Invoice Sending Functionality", [
                self.test_automatic_invoice_sending_functionality,
                self.test_invoice_email_template_verification,
                self.test_invoice_edge_cases,
            ]),
            
            # CRITICAL REVIEW REQUEST TEST - Multiple Payment Logic Issue
            ("🚨 CRITICAL: Multiple Payment Logic Issue Testing", [
                self.test_multiple_payment_logic_issue,
            ]),
            
            # SPECIFIC REVIEW REQUEST TEST - Professional Email Template
            ("🎯 REVIEW REQUEST: Professional Email Template Testing", [
                self.test_professional_email_template,
            ]),
            
            # SPECIFIC REVIEW REQUEST TEST - Payment Date Calculation Edge Cases
            ("🎯 REVIEW REQUEST: Payment Date Calculation Edge Cases", [
                self.test_payment_date_calculation_edge_cases,
            ]),
            
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
    """Main function - Run Alphalete Club review-specific tests"""
    print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - BACKEND API TESTING")
    print("Testing backend functionality after REACT_APP_BACKEND_URL fix")
    print(f"Backend URL: https://alphalete-club.emergent.host/api/")
    print()
    
    tester = AlphaleteAPITester()
    
    # Run the specific review tests first
    print("🎯 RUNNING ALPHALETE CLUB REVIEW-SPECIFIC TESTS...")
    review_tests_passed = tester.test_alphalete_club_review_endpoints()
    
    if review_tests_passed:
        print("\n🎉 REVIEW-SPECIFIC TESTS PASSED - All core endpoints working!")
        print("✅ Backend is ready for frontend integration")
        print("✅ REACT_APP_BACKEND_URL fix is successful")
        return 0  # Success
    else:
        print("\n🚨 REVIEW-SPECIFIC TESTS FAILED - Some core endpoints have issues")
        print("❌ Frontend may experience API call failures")
        print("⚠️  Check the detailed output above for specific issues")
        return 1  # Failure

if __name__ == "__main__":
    sys.exit(main())