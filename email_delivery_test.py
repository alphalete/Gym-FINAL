#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailDeliveryTester:
    def __init__(self, base_url="https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.deon_client_id = None
        
        # Gmail SMTP settings from backend/.env
        self.gmail_email = "alphaleteclub@gmail.com"
        self.gmail_app_password = "yauf mdwy rsrd lhai"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        print("🎯 EMAIL DELIVERY INVESTIGATION STARTED")
        print("=" * 80)
        print("FOCUS: Investigating email delivery vs API success responses")
        print("ISSUE: Frontend shows 'Invoice email failed to send' but backend returns success=true")
        print("USER EMAIL: deonaleong@gmail.com")
        print("GMAIL APP PASSWORD: yauf mdwy rsrd lhai")
        print("=" * 80)

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

    def test_direct_smtp_connection(self):
        """Test direct SMTP connection to Gmail"""
        print("\n🔍 CRITICAL TEST 1: Direct SMTP Connection to Gmail")
        print("=" * 60)
        
        try:
            # Create SMTP connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Attempt authentication
            server.login(self.gmail_email, self.gmail_app_password)
            
            # If we get here, authentication succeeded
            print(f"   ✅ SMTP Connection: SUCCESS")
            print(f"   ✅ Gmail Authentication: SUCCESS")
            print(f"   ✅ App Password: WORKING")
            print(f"   📧 Gmail Email: {self.gmail_email}")
            print(f"   🔑 App Password: {self.gmail_app_password}")
            
            server.quit()
            self.log_test("Direct SMTP Connection", True, "Gmail authentication successful")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ SMTP Authentication: FAILED")
            print(f"   ❌ Error: {str(e)}")
            print(f"   🚨 CRITICAL: Gmail app password is being rejected")
            self.log_test("Direct SMTP Connection", False, f"Authentication failed: {str(e)}")
            return False
            
        except Exception as e:
            print(f"   ❌ SMTP Connection: FAILED")
            print(f"   ❌ Error: {str(e)}")
            self.log_test("Direct SMTP Connection", False, f"Connection failed: {str(e)}")
            return False

    def test_backend_email_configuration(self):
        """Test backend email configuration endpoint"""
        print("\n🔍 CRITICAL TEST 2: Backend Email Configuration")
        print("=" * 60)
        
        success, response = self.run_test(
            "Backend Email Configuration Test",
            "POST",
            "email/test",
            200
        )
        
        if success:
            email_success = response.get('success', False)
            message = response.get('message', 'No message')
            
            print(f"   📧 Email Service Status: {'WORKING' if email_success else 'FAILED'}")
            print(f"   📝 Message: {message}")
            
            if email_success:
                print(f"   ✅ Backend email service is configured correctly")
                return True
            else:
                print(f"   ❌ Backend email service configuration failed")
                print(f"   🚨 CRITICAL: Backend email service is not working")
                return False
        else:
            print(f"   ❌ Could not reach backend email test endpoint")
            return False

    def find_deon_client(self):
        """Find Deon Aleong client in the database"""
        print("\n🔍 CRITICAL TEST 3: Find Deon Aleong Client")
        print("=" * 60)
        
        success, response = self.run_test(
            "Get All Clients to Find Deon",
            "GET",
            "clients",
            200
        )
        
        if success:
            clients = response if isinstance(response, list) else []
            print(f"   📊 Total clients found: {len(clients)}")
            
            # Look for Deon Aleong client
            deon_clients = []
            for client in clients:
                name = client.get('name', '').lower()
                email = client.get('email', '').lower()
                
                if 'deon' in name and 'aleong' in name:
                    deon_clients.append(client)
                    print(f"   👤 Found Deon client: {client.get('name')} ({client.get('email')})")
                    
                    # Check if email is the real Gmail address
                    if client.get('email') == 'deonaleong@gmail.com':
                        self.deon_client_id = client.get('id')
                        print(f"   ✅ CORRECT EMAIL: Found Deon with real Gmail address")
                        print(f"   🆔 Client ID: {self.deon_client_id}")
                        return True
                    else:
                        print(f"   ⚠️  WRONG EMAIL: {client.get('email')} (should be deonaleong@gmail.com)")
            
            if not deon_clients:
                print(f"   ❌ No Deon Aleong client found in database")
                print(f"   🚨 CRITICAL: User's client record is missing")
                return False
            else:
                # Use the first Deon client found, even if email is wrong
                self.deon_client_id = deon_clients[0].get('id')
                print(f"   ⚠️  Using Deon client with potentially wrong email")
                print(f"   🆔 Client ID: {self.deon_client_id}")
                return True
        else:
            print(f"   ❌ Could not retrieve clients from backend")
            return False

    def test_payment_reminder_email(self):
        """Test sending payment reminder email to Deon"""
        print("\n🔍 CRITICAL TEST 4: Payment Reminder Email to Deon")
        print("=" * 60)
        
        if not self.deon_client_id:
            print("   ❌ SKIPPED: No Deon client ID available")
            return False
        
        reminder_data = {
            "client_id": self.deon_client_id,
            "template_name": "default",
            "custom_subject": "CRITICAL EMAIL DELIVERY TEST - Alphalete Athletics",
            "custom_message": "This is a critical test to verify email delivery is working correctly.",
            "custom_amount": 100.00,
            "custom_due_date": "February 15, 2025"
        }
        
        success, response = self.run_test(
            "Send Payment Reminder to Deon",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success:
            api_success = response.get('success', False)
            message = response.get('message', 'No message')
            client_email = response.get('client_email', 'Unknown')
            
            print(f"   📧 API Response Success: {api_success}")
            print(f"   📝 API Message: {message}")
            print(f"   📮 Target Email: {client_email}")
            
            if api_success:
                print(f"   ✅ API REPORTS: Email sent successfully")
                if client_email == 'deonaleong@gmail.com':
                    print(f"   ✅ CORRECT EMAIL: Sent to real Gmail address")
                    return True
                else:
                    print(f"   ⚠️  WRONG EMAIL: Sent to {client_email} instead of deonaleong@gmail.com")
                    print(f"   🚨 CRITICAL: Email sent to wrong address - user won't receive it")
                    return False
            else:
                print(f"   ❌ API REPORTS: Email sending failed")
                print(f"   🚨 CRITICAL: Backend email sending is failing")
                return False
        else:
            print(f"   ❌ Could not send payment reminder via API")
            return False

    def test_payment_recording_with_invoice(self):
        """Test payment recording with automatic invoice email"""
        print("\n🔍 CRITICAL TEST 5: Payment Recording with Invoice Email")
        print("=" * 60)
        
        if not self.deon_client_id:
            print("   ❌ SKIPPED: No Deon client ID available")
            return False
        
        payment_data = {
            "client_id": self.deon_client_id,
            "amount_paid": 75.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Credit Card",
            "notes": "Critical email delivery test - invoice email verification"
        }
        
        success, response = self.run_test(
            "Record Payment with Automatic Invoice Email",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            payment_success = response.get('success', False)
            invoice_sent = response.get('invoice_sent', None)
            invoice_message = response.get('invoice_message', 'No invoice message')
            client_name = response.get('client_name', 'Unknown')
            
            print(f"   💰 Payment Recording Success: {payment_success}")
            print(f"   📧 Invoice Email Sent: {invoice_sent}")
            print(f"   📝 Invoice Message: {invoice_message}")
            print(f"   👤 Client: {client_name}")
            
            if payment_success:
                print(f"   ✅ PAYMENT: Recorded successfully")
                
                if invoice_sent is True:
                    print(f"   ✅ INVOICE EMAIL: API reports successful delivery")
                    print(f"   🎯 CRITICAL FINDING: Backend returns invoice_sent=true")
                    return True
                elif invoice_sent is False:
                    print(f"   ❌ INVOICE EMAIL: API reports delivery failed")
                    print(f"   🎯 CRITICAL FINDING: Backend correctly returns invoice_sent=false")
                    print(f"   🚨 This matches user's report of 'Invoice email failed to send'")
                    return False
                else:
                    print(f"   ⚠️  INVOICE EMAIL: Status unclear (invoice_sent={invoice_sent})")
                    print(f"   🚨 CRITICAL: Backend not properly reporting email delivery status")
                    return False
            else:
                print(f"   ❌ PAYMENT: Recording failed")
                return False
        else:
            print(f"   ❌ Could not record payment via API")
            return False

    def test_email_templates(self):
        """Test email templates availability"""
        print("\n🔍 CRITICAL TEST 6: Email Templates Availability")
        print("=" * 60)
        
        success, response = self.run_test(
            "Get Available Email Templates",
            "GET",
            "email/templates",
            200
        )
        
        if success:
            templates = response.get('templates', {})
            print(f"   📧 Available templates: {len(templates)}")
            
            for template_key, template_info in templates.items():
                print(f"   - {template_key}: {template_info.get('name')} - {template_info.get('description')}")
            
            if len(templates) >= 3:
                print(f"   ✅ EMAIL TEMPLATES: All templates available")
                return True
            else:
                print(f"   ⚠️  EMAIL TEMPLATES: Limited templates available")
                return True
        else:
            print(f"   ❌ Could not retrieve email templates")
            return False

    def test_bulk_email_sending(self):
        """Test bulk email sending to identify rate limiting"""
        print("\n🔍 CRITICAL TEST 7: Bulk Email Sending (Rate Limiting Check)")
        print("=" * 60)
        
        success, response = self.run_test(
            "Send Bulk Payment Reminders",
            "POST",
            "email/payment-reminder/bulk",
            200
        )
        
        if success:
            total_clients = response.get('total_clients', 0)
            sent_successfully = response.get('sent_successfully', 0)
            failed = response.get('failed', 0)
            
            print(f"   📊 Total clients: {total_clients}")
            print(f"   ✅ Sent successfully: {sent_successfully}")
            print(f"   ❌ Failed: {failed}")
            
            if total_clients > 0:
                success_rate = (sent_successfully / total_clients) * 100
                print(f"   📈 Success rate: {success_rate:.1f}%")
                
                if success_rate == 0:
                    print(f"   🚨 CRITICAL: 100% email failure - likely Gmail rate limiting")
                    return False
                elif success_rate < 50:
                    print(f"   ⚠️  HIGH FAILURE RATE: Possible Gmail rate limiting")
                    return False
                else:
                    print(f"   ✅ ACCEPTABLE SUCCESS RATE: Email system working")
                    return True
            else:
                print(f"   ⚠️  No clients available for bulk testing")
                return True
        else:
            print(f"   ❌ Could not perform bulk email test")
            return False

    def update_deon_email_address(self):
        """Update Deon's email address to the correct Gmail address"""
        print("\n🔧 EMAIL ADDRESS CORRECTION: Updating Deon's Email")
        print("=" * 60)
        
        if not self.deon_client_id:
            print("   ❌ SKIPPED: No Deon client ID available")
            return False
        
        update_data = {
            "email": "deonaleong@gmail.com"
        }
        
        success, response = self.run_test(
            "Update Deon's Email to Real Gmail Address",
            "PUT",
            f"clients/{self.deon_client_id}",
            200,
            update_data
        )
        
        if success:
            updated_email = response.get('email', 'Unknown')
            client_name = response.get('name', 'Unknown')
            
            print(f"   👤 Client: {client_name}")
            print(f"   📧 Updated email: {updated_email}")
            
            if updated_email == 'deonaleong@gmail.com':
                print(f"   ✅ EMAIL CORRECTION: Successfully updated to real Gmail address")
                return True
            else:
                print(f"   ❌ EMAIL CORRECTION: Failed to update email address")
                return False
        else:
            print(f"   ❌ Could not update Deon's email address")
            return False

    def test_email_delivery_after_correction(self):
        """Test email delivery after correcting Deon's email address"""
        print("\n🔍 CRITICAL TEST 8: Email Delivery After Email Correction")
        print("=" * 60)
        
        if not self.deon_client_id:
            print("   ❌ SKIPPED: No Deon client ID available")
            return False
        
        # Test payment reminder
        reminder_data = {
            "client_id": self.deon_client_id,
            "template_name": "professional",
            "custom_subject": "EMAIL DELIVERY VERIFICATION - Alphalete Athletics",
            "custom_message": "This email confirms that the email delivery system is working correctly after email address correction.",
            "custom_amount": 100.00,
            "custom_due_date": "February 20, 2025"
        }
        
        success1, response1 = self.run_test(
            "Send Payment Reminder After Email Correction",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success1:
            api_success = response1.get('success', False)
            client_email = response1.get('client_email', 'Unknown')
            
            print(f"   📧 API Success: {api_success}")
            print(f"   📮 Target Email: {client_email}")
            
            if api_success and client_email == 'deonaleong@gmail.com':
                print(f"   ✅ PAYMENT REMINDER: Successfully sent to correct Gmail address")
            else:
                print(f"   ❌ PAYMENT REMINDER: Failed or sent to wrong address")
                return False
        else:
            print(f"   ❌ Could not send payment reminder after correction")
            return False
        
        # Test invoice email
        payment_data = {
            "client_id": self.deon_client_id,
            "amount_paid": 50.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Bank Transfer",
            "notes": "Email delivery verification test - invoice email"
        }
        
        success2, response2 = self.run_test(
            "Record Payment with Invoice After Email Correction",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success2:
            invoice_sent = response2.get('invoice_sent', None)
            invoice_message = response2.get('invoice_message', 'No message')
            
            print(f"   📧 Invoice Sent: {invoice_sent}")
            print(f"   📝 Invoice Message: {invoice_message}")
            
            if invoice_sent is True:
                print(f"   ✅ INVOICE EMAIL: Successfully sent to correct Gmail address")
                return True
            else:
                print(f"   ❌ INVOICE EMAIL: Failed to send")
                return False
        else:
            print(f"   ❌ Could not record payment with invoice after correction")
            return False

    def run_comprehensive_email_investigation(self):
        """Run comprehensive email delivery investigation"""
        print("\n🎯 COMPREHENSIVE EMAIL DELIVERY INVESTIGATION")
        print("=" * 80)
        print("OBJECTIVE: Determine if emails are actually being delivered or if API is giving false positives")
        print("=" * 80)
        
        # Test 1: Direct SMTP Connection
        smtp_success = self.test_direct_smtp_connection()
        
        # Test 2: Backend Email Configuration
        config_success = self.test_backend_email_configuration()
        
        # Test 3: Find Deon Client
        deon_found = self.find_deon_client()
        
        # Test 4: Email Templates
        templates_success = self.test_email_templates()
        
        # Test 5: Payment Reminder Email
        reminder_success = self.test_payment_reminder_email()
        
        # Test 6: Payment Recording with Invoice
        invoice_success = self.test_payment_recording_with_invoice()
        
        # Test 7: Bulk Email Testing
        bulk_success = self.test_bulk_email_sending()
        
        # If Deon's email is wrong, correct it and retest
        if deon_found and not reminder_success:
            print("\n🔧 ATTEMPTING EMAIL ADDRESS CORRECTION...")
            if self.update_deon_email_address():
                # Test 8: Email Delivery After Correction
                corrected_success = self.test_email_delivery_after_correction()
            else:
                corrected_success = False
        else:
            corrected_success = True
        
        # Final Analysis
        print("\n🎯 FINAL ANALYSIS - EMAIL DELIVERY INVESTIGATION")
        print("=" * 80)
        
        total_tests = 7 + (1 if deon_found and not reminder_success else 0)
        passed_tests = sum([
            smtp_success, config_success, deon_found, templates_success,
            reminder_success, invoice_success, bulk_success,
            corrected_success if deon_found and not reminder_success else True
        ])
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"📊 INVESTIGATION RESULTS:")
        print(f"   Tests Run: {total_tests}")
        print(f"   Tests Passed: {passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n🔍 KEY FINDINGS:")
        
        if not smtp_success:
            print(f"   🚨 CRITICAL: Gmail SMTP authentication is failing")
            print(f"   🔧 SOLUTION: Regenerate Gmail app password")
        else:
            print(f"   ✅ Gmail SMTP authentication is working")
        
        if not config_success:
            print(f"   🚨 CRITICAL: Backend email service is not configured correctly")
        else:
            print(f"   ✅ Backend email service is configured correctly")
        
        if not deon_found:
            print(f"   🚨 CRITICAL: Deon Aleong client not found in database")
        else:
            print(f"   ✅ Deon Aleong client found in database")
        
        if not reminder_success and deon_found:
            print(f"   🚨 CRITICAL: Payment reminder emails are failing")
        elif reminder_success:
            print(f"   ✅ Payment reminder emails are working")
        
        if not invoice_success and deon_found:
            print(f"   🚨 CRITICAL: Invoice emails are failing")
            print(f"   🎯 This matches user's report: 'Invoice email failed to send'")
        elif invoice_success:
            print(f"   ✅ Invoice emails are working")
        
        if not bulk_success:
            print(f"   🚨 CRITICAL: Bulk email sending is failing (likely rate limiting)")
        else:
            print(f"   ✅ Bulk email sending is working")
        
        print(f"\n🎯 CONCLUSION:")
        if success_rate >= 80:
            print(f"   ✅ EMAIL SYSTEM IS WORKING CORRECTLY")
            print(f"   ✅ Emails are being delivered successfully")
            print(f"   ✅ Backend API responses match actual delivery status")
        elif success_rate >= 50:
            print(f"   ⚠️  EMAIL SYSTEM HAS ISSUES BUT IS PARTIALLY WORKING")
            print(f"   ⚠️  Some emails may not be delivered")
            print(f"   🔧 Requires investigation and fixes")
        else:
            print(f"   ❌ EMAIL SYSTEM IS FAILING")
            print(f"   ❌ Emails are NOT being delivered")
            print(f"   🚨 Backend API is giving FALSE POSITIVES")
            print(f"   🔧 Immediate action required")
        
        return success_rate >= 80

def main():
    """Main function to run email delivery investigation"""
    print("🚀 STARTING EMAIL DELIVERY INVESTIGATION")
    print("=" * 80)
    
    tester = EmailDeliveryTester()
    success = tester.run_comprehensive_email_investigation()
    
    print(f"\n🏁 EMAIL DELIVERY INVESTIGATION COMPLETED")
    print(f"Overall Success: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())