#!/usr/bin/env python3

"""
CRITICAL EMAIL DELIVERY INVESTIGATION
=====================================

This test investigates the critical email delivery issue where backend returns 
success=true but emails are not actually being sent or received.

Focus Areas:
1. Test actual email delivery end-to-end
2. Debug Gmail SMTP authentication in detail  
3. Backend email service deep dive
4. Test different email scenarios
5. Real-time email monitoring
"""

import requests
import sys
import json
import time
import smtplib
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class CriticalEmailDeliveryTester:
    def __init__(self, base_url="https://413cf26f-b3f7-4bfe-b0d4-96a01530ff67.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_id = None
        
        # Gmail SMTP settings from backend/.env
        self.gmail_email = "alphaleteclub@gmail.com"
        self.gmail_app_password = "yauf mdwy rsrd lhai"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        print("🚨 CRITICAL EMAIL DELIVERY INVESTIGATION STARTED")
        print("=" * 80)
        print(f"📧 Gmail Email: {self.gmail_email}")
        print(f"🔑 App Password: {self.gmail_app_password}")
        print(f"🌐 SMTP Server: {self.smtp_server}:{self.smtp_port}")
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
        """Test direct SMTP connection to Gmail with detailed debugging"""
        print("\n🔍 TESTING DIRECT SMTP CONNECTION TO GMAIL")
        print("=" * 60)
        
        try:
            print(f"📧 Connecting to {self.smtp_server}:{self.smtp_port}")
            print(f"🔑 Using email: {self.gmail_email}")
            print(f"🔑 App password length: {len(self.gmail_app_password)}")
            
            # Create SMTP connection with debug output
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.set_debuglevel(2)  # Maximum debug output
            
            print("🔐 Starting TLS encryption...")
            server.starttls()
            
            print("🔑 Attempting Gmail authentication...")
            server.login(self.gmail_email, self.gmail_app_password.replace(' ', ''))
            
            print("✅ SMTP CONNECTION SUCCESSFUL!")
            print("✅ Gmail authentication working!")
            
            server.quit()
            self.log_test("Direct SMTP Connection Test", True, "Gmail authentication successful")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP AUTHENTICATION FAILED: {e}")
            print(f"❌ Error code: {e.smtp_code}")
            print(f"❌ Error message: {e.smtp_error}")
            self.log_test("Direct SMTP Connection Test", False, f"Authentication failed: {e}")
            return False
            
        except smtplib.SMTPServerDisconnected as e:
            print(f"❌ SMTP SERVER DISCONNECTED: {e}")
            self.log_test("Direct SMTP Connection Test", False, f"Server disconnected: {e}")
            return False
            
        except Exception as e:
            print(f"❌ SMTP CONNECTION ERROR: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            self.log_test("Direct SMTP Connection Test", False, f"Connection error: {e}")
            return False

    def test_send_direct_test_email(self):
        """Send a direct test email to verify actual delivery"""
        print("\n🔍 TESTING DIRECT EMAIL SENDING")
        print("=" * 60)
        
        try:
            # Create test email
            msg = MIMEMultipart()
            msg['Subject'] = f"CRITICAL EMAIL DELIVERY TEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            msg['From'] = f"Alphalete Athletics Club <{self.gmail_email}>"
            msg['To'] = self.gmail_email  # Send to self for testing
            
            # Create HTML body
            html_body = f"""
            <html>
            <body>
                <h2>🚨 CRITICAL EMAIL DELIVERY TEST</h2>
                <p><strong>Test Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Purpose:</strong> Verify actual email delivery capability</p>
                <p><strong>Gmail Account:</strong> {self.gmail_email}</p>
                <p><strong>SMTP Server:</strong> {self.smtp_server}:{self.smtp_port}</p>
                <p>If you receive this email, Gmail SMTP delivery is working correctly.</p>
            </body>
            </html>
            """
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            print(f"📧 Sending test email to: {self.gmail_email}")
            print(f"📧 Subject: {msg['Subject']}")
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.gmail_email, self.gmail_app_password.replace(' ', ''))
                server.send_message(msg)
            
            print("✅ DIRECT EMAIL SENT SUCCESSFULLY!")
            print("📧 Check your Gmail inbox to verify actual delivery")
            self.log_test("Direct Email Sending Test", True, "Email sent successfully")
            return True
            
        except Exception as e:
            print(f"❌ DIRECT EMAIL SENDING FAILED: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            self.log_test("Direct Email Sending Test", False, f"Email sending failed: {e}")
            return False

    def test_backend_email_configuration(self):
        """Test backend email configuration endpoint"""
        print("\n🔍 TESTING BACKEND EMAIL CONFIGURATION")
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
            
            print(f"📧 Backend email test result: {email_success}")
            print(f"📧 Backend message: {message}")
            
            if email_success:
                print("✅ BACKEND EMAIL CONFIGURATION: WORKING")
                return True
            else:
                print("❌ BACKEND EMAIL CONFIGURATION: FAILED")
                return False
        else:
            print("❌ BACKEND EMAIL CONFIGURATION: ENDPOINT ERROR")
            return False

    def create_test_client(self):
        """Create a test client for email testing"""
        print("\n🔍 CREATING TEST CLIENT FOR EMAIL TESTING")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Email Test Client",
            "email": self.gmail_email,  # Use Gmail account for testing
            "phone": "(555) 123-4567",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": "2025-01-25",
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Create Test Client for Email Testing",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_id = response["id"]
            print(f"✅ Created test client ID: {self.created_client_id}")
            print(f"📧 Client email: {response.get('email')}")
            return True
        else:
            print("❌ Failed to create test client")
            return False

    def test_payment_reminder_email_delivery(self):
        """Test payment reminder email delivery end-to-end"""
        print("\n🔍 TESTING PAYMENT REMINDER EMAIL DELIVERY")
        print("=" * 60)
        
        if not self.created_client_id:
            print("❌ No test client available - skipping payment reminder test")
            return False
        
        reminder_data = {
            "client_id": self.created_client_id,
            "template_name": "default",
            "custom_subject": "CRITICAL EMAIL DELIVERY TEST - Payment Reminder",
            "custom_message": "This is a critical test to verify actual email delivery capability.",
            "custom_amount": 100.00,
            "custom_due_date": "February 15, 2025"
        }
        
        print(f"📧 Sending payment reminder to client: {self.created_client_id}")
        print(f"📧 Email will be sent to: {self.gmail_email}")
        
        success, response = self.run_test(
            "Payment Reminder Email Delivery Test",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success:
            email_success = response.get('success', False)
            message = response.get('message', 'No message')
            client_email = response.get('client_email', 'Unknown')
            
            print(f"📧 Backend response success: {email_success}")
            print(f"📧 Backend message: {message}")
            print(f"📧 Target email: {client_email}")
            
            if email_success:
                print("✅ BACKEND REPORTS: EMAIL SENT SUCCESSFULLY")
                print("📧 Check Gmail inbox to verify actual delivery")
                return True
            else:
                print("❌ BACKEND REPORTS: EMAIL SENDING FAILED")
                return False
        else:
            print("❌ PAYMENT REMINDER API CALL FAILED")
            return False

    def test_custom_reminder_email_delivery(self):
        """Test custom reminder email delivery"""
        print("\n🔍 TESTING CUSTOM REMINDER EMAIL DELIVERY")
        print("=" * 60)
        
        if not self.created_client_id:
            print("❌ No test client available - skipping custom reminder test")
            return False
        
        reminder_data = {
            "client_id": self.created_client_id,
            "template_name": "professional",
            "custom_subject": "CRITICAL EMAIL DELIVERY TEST - Custom Reminder",
            "custom_message": "This is a critical test using professional template to verify actual email delivery.",
            "custom_amount": 150.00,
            "custom_due_date": "March 1, 2025"
        }
        
        print(f"📧 Sending custom reminder to client: {self.created_client_id}")
        print(f"📧 Using professional template")
        
        success, response = self.run_test(
            "Custom Reminder Email Delivery Test",
            "POST",
            "email/custom-reminder",
            200,
            reminder_data
        )
        
        if success:
            email_success = response.get('success', False)
            message = response.get('message', 'No message')
            
            print(f"📧 Backend response success: {email_success}")
            print(f"📧 Backend message: {message}")
            
            if email_success:
                print("✅ BACKEND REPORTS: CUSTOM EMAIL SENT SUCCESSFULLY")
                return True
            else:
                print("❌ BACKEND REPORTS: CUSTOM EMAIL SENDING FAILED")
                return False
        else:
            print("❌ CUSTOM REMINDER API CALL FAILED")
            return False

    def test_payment_recording_with_invoice_email(self):
        """Test payment recording with automatic invoice email"""
        print("\n🔍 TESTING PAYMENT RECORDING WITH INVOICE EMAIL")
        print("=" * 60)
        
        if not self.created_client_id:
            print("❌ No test client available - skipping payment recording test")
            return False
        
        payment_data = {
            "client_id": self.created_client_id,
            "amount_paid": 100.00,
            "payment_date": "2025-01-25",
            "payment_method": "Credit Card",
            "notes": "CRITICAL EMAIL DELIVERY TEST - Invoice Email"
        }
        
        print(f"📧 Recording payment for client: {self.created_client_id}")
        print(f"📧 This should trigger automatic invoice email")
        
        success, response = self.run_test(
            "Payment Recording with Invoice Email Test",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            payment_success = response.get('success', False)
            invoice_sent = response.get('invoice_sent', False)
            invoice_message = response.get('invoice_message', 'No invoice message')
            
            print(f"💰 Payment recording success: {payment_success}")
            print(f"📧 Invoice email sent: {invoice_sent}")
            print(f"📧 Invoice message: {invoice_message}")
            
            if payment_success and invoice_sent:
                print("✅ PAYMENT RECORDED AND INVOICE EMAIL SENT")
                return True
            elif payment_success and not invoice_sent:
                print("⚠️  PAYMENT RECORDED BUT INVOICE EMAIL FAILED")
                return False
            else:
                print("❌ PAYMENT RECORDING FAILED")
                return False
        else:
            print("❌ PAYMENT RECORDING API CALL FAILED")
            return False

    def test_bulk_email_sending(self):
        """Test bulk email sending functionality"""
        print("\n🔍 TESTING BULK EMAIL SENDING")
        print("=" * 60)
        
        success, response = self.run_test(
            "Bulk Email Sending Test",
            "POST",
            "email/payment-reminder/bulk",
            200
        )
        
        if success:
            total_clients = response.get('total_clients', 0)
            sent_successfully = response.get('sent_successfully', 0)
            failed = response.get('failed', 0)
            
            print(f"📊 Total clients: {total_clients}")
            print(f"✅ Sent successfully: {sent_successfully}")
            print(f"❌ Failed: {failed}")
            
            if total_clients > 0:
                success_rate = (sent_successfully / total_clients) * 100
                print(f"📈 Success rate: {success_rate:.1f}%")
                
                if success_rate > 0:
                    print("✅ BULK EMAIL SENDING: SOME EMAILS SENT")
                    return True
                else:
                    print("❌ BULK EMAIL SENDING: ALL EMAILS FAILED")
                    return False
            else:
                print("⚠️  BULK EMAIL SENDING: NO CLIENTS TO SEND TO")
                return True
        else:
            print("❌ BULK EMAIL SENDING API CALL FAILED")
            return False

    def test_different_email_providers(self):
        """Test sending emails to different email providers"""
        print("\n🔍 TESTING DIFFERENT EMAIL PROVIDERS")
        print("=" * 60)
        
        # Create test clients with different email providers
        email_providers = [
            ("gmail_test", "testuser.gmail@gmail.com"),
            ("yahoo_test", "testuser.yahoo@yahoo.com"),
            ("outlook_test", "testuser.outlook@outlook.com"),
            ("corporate_test", "testuser@company.com")
        ]
        
        test_results = []
        
        for provider_name, test_email in email_providers:
            print(f"\n📧 Testing email provider: {provider_name} ({test_email})")
            
            # Create client with specific email
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            client_data = {
                "name": f"Email Provider Test - {provider_name}",
                "email": test_email,
                "phone": "(555) 123-4567",
                "membership_type": "Standard",
                "monthly_fee": 50.00,
                "start_date": "2025-01-25"
            }
            
            success, response = self.run_test(
                f"Create Client for {provider_name}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                client_id = response["id"]
                
                # Send payment reminder
                reminder_data = {
                    "client_id": client_id,
                    "template_name": "default",
                    "custom_subject": f"Email Provider Test - {provider_name}",
                    "custom_message": f"Testing email delivery to {test_email}",
                    "custom_amount": 50.00,
                    "custom_due_date": "February 15, 2025"
                }
                
                email_success, email_response = self.run_test(
                    f"Send Email to {provider_name}",
                    "POST",
                    "email/payment-reminder",
                    200,
                    reminder_data
                )
                
                if email_success:
                    email_sent = email_response.get('success', False)
                    test_results.append((provider_name, test_email, email_sent))
                    
                    if email_sent:
                        print(f"✅ {provider_name}: EMAIL SENT SUCCESSFULLY")
                    else:
                        print(f"❌ {provider_name}: EMAIL SENDING FAILED")
                else:
                    test_results.append((provider_name, test_email, False))
                    print(f"❌ {provider_name}: API CALL FAILED")
            else:
                test_results.append((provider_name, test_email, False))
                print(f"❌ {provider_name}: CLIENT CREATION FAILED")
        
        # Summary
        print(f"\n📊 EMAIL PROVIDER TEST SUMMARY:")
        successful_providers = 0
        for provider_name, test_email, success in test_results:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"   {provider_name} ({test_email}): {status}")
            if success:
                successful_providers += 1
        
        print(f"\n📈 Success rate: {successful_providers}/{len(test_results)} providers")
        
        return successful_providers > 0

    def test_email_template_variations(self):
        """Test all email template variations"""
        print("\n🔍 TESTING EMAIL TEMPLATE VARIATIONS")
        print("=" * 60)
        
        if not self.created_client_id:
            print("❌ No test client available - skipping template variation test")
            return False
        
        templates = ["default", "professional", "friendly"]
        template_results = []
        
        for template_name in templates:
            print(f"\n📧 Testing template: {template_name}")
            
            reminder_data = {
                "client_id": self.created_client_id,
                "template_name": template_name,
                "custom_subject": f"Template Test - {template_name.title()}",
                "custom_message": f"Testing {template_name} email template for delivery verification.",
                "custom_amount": 100.00,
                "custom_due_date": "February 20, 2025"
            }
            
            success, response = self.run_test(
                f"Email Template Test - {template_name}",
                "POST",
                "email/custom-reminder",
                200,
                reminder_data
            )
            
            if success:
                email_sent = response.get('success', False)
                template_results.append((template_name, email_sent))
                
                if email_sent:
                    print(f"✅ {template_name} template: EMAIL SENT SUCCESSFULLY")
                else:
                    print(f"❌ {template_name} template: EMAIL SENDING FAILED")
            else:
                template_results.append((template_name, False))
                print(f"❌ {template_name} template: API CALL FAILED")
            
            # Small delay between template tests
            time.sleep(2)
        
        # Summary
        print(f"\n📊 EMAIL TEMPLATE TEST SUMMARY:")
        successful_templates = 0
        for template_name, success in template_results:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"   {template_name}: {status}")
            if success:
                successful_templates += 1
        
        print(f"\n📈 Success rate: {successful_templates}/{len(templates)} templates")
        
        return successful_templates > 0

    def run_comprehensive_email_investigation(self):
        """Run comprehensive email delivery investigation"""
        print("\n🚨 STARTING COMPREHENSIVE EMAIL DELIVERY INVESTIGATION")
        print("=" * 80)
        
        # Test sequence
        tests = [
            ("Direct SMTP Connection", self.test_direct_smtp_connection),
            ("Direct Email Sending", self.test_send_direct_test_email),
            ("Backend Email Configuration", self.test_backend_email_configuration),
            ("Create Test Client", self.create_test_client),
            ("Payment Reminder Email", self.test_payment_reminder_email_delivery),
            ("Custom Reminder Email", self.test_custom_reminder_email_delivery),
            ("Payment Recording with Invoice", self.test_payment_recording_with_invoice_email),
            ("Bulk Email Sending", self.test_bulk_email_sending),
            ("Different Email Providers", self.test_different_email_providers),
            ("Email Template Variations", self.test_email_template_variations)
        ]
        
        results = []
        
        for test_name, test_function in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_function()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} CRASHED: {e}")
                results.append((test_name, False))
        
        # Final summary
        print(f"\n🚨 CRITICAL EMAIL DELIVERY INVESTIGATION SUMMARY")
        print("=" * 80)
        
        passed_tests = 0
        critical_failures = []
        
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status}: {test_name}")
            
            if success:
                passed_tests += 1
            else:
                critical_failures.append(test_name)
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Run: {len(results)}")
        print(f"   Tests Passed: {passed_tests}")
        print(f"   Tests Failed: {len(results) - passed_tests}")
        print(f"   Success Rate: {(passed_tests/len(results)*100):.1f}%")
        
        if critical_failures:
            print(f"\n🚨 CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"   ❌ {failure}")
        
        # Diagnosis
        print(f"\n🔍 DIAGNOSIS:")
        
        if "Direct SMTP Connection" in critical_failures:
            print("   🚨 CRITICAL: Gmail SMTP authentication is failing")
            print("   🔧 SOLUTION: Check Gmail app password and account settings")
        elif "Direct Email Sending" in critical_failures:
            print("   🚨 CRITICAL: Gmail SMTP connection works but email sending fails")
            print("   🔧 SOLUTION: Check Gmail sending limits and account restrictions")
        elif "Backend Email Configuration" in critical_failures:
            print("   🚨 CRITICAL: Backend email service configuration is broken")
            print("   🔧 SOLUTION: Check backend email service implementation")
        elif passed_tests == 0:
            print("   🚨 CRITICAL: Complete email system failure")
            print("   🔧 SOLUTION: Full email system investigation required")
        elif passed_tests < len(results) * 0.5:
            print("   ⚠️  WARNING: Partial email system failure")
            print("   🔧 SOLUTION: Investigate specific failing components")
        else:
            print("   ✅ GOOD: Most email functionality is working")
            print("   🔧 RECOMMENDATION: Address minor issues in failing tests")
        
        print(f"\n🚨 INVESTIGATION COMPLETE")
        print("=" * 80)
        
        return passed_tests, len(results), critical_failures

if __name__ == "__main__":
    tester = CriticalEmailDeliveryTester()
    passed, total, failures = tester.run_comprehensive_email_investigation()
    
    # Exit with appropriate code
    if passed == total:
        print("🎉 ALL EMAIL TESTS PASSED!")
        sys.exit(0)
    elif passed > 0:
        print("⚠️  SOME EMAIL TESTS FAILED!")
        sys.exit(1)
    else:
        print("🚨 ALL EMAIL TESTS FAILED!")
        sys.exit(2)