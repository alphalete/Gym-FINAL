#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class CriticalEmailDebugTester:
    def __init__(self, base_url="https://a2eb3b6a-2c20-4e9f-b52b-bd4f318d28fc.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.deon_client_id = None
        self.deon_client_data = None

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

    def test_1_verify_deon_client_email_fix(self):
        """CRITICAL TEST 1: Verify Deon Aleong client data and email address fix"""
        print("\n" + "="*80)
        print("🎯 CRITICAL TEST 1: VERIFY DEON ALEONG CLIENT EMAIL ADDRESS FIX")
        print("="*80)
        
        # Get all clients to find Deon Aleong
        success, response = self.run_test(
            "Get All Clients - Find Deon Aleong",
            "GET",
            "clients",
            200
        )
        
        if not success:
            print("❌ CRITICAL FAILURE: Cannot retrieve clients list")
            return False
        
        # Search for Deon Aleong clients
        deon_clients = []
        for client in response:
            if "deon" in client.get('name', '').lower() and "aleong" in client.get('name', '').lower():
                deon_clients.append(client)
        
        print(f"\n🔍 DEON ALEONG CLIENT ANALYSIS:")
        print(f"   Found {len(deon_clients)} Deon Aleong client(s)")
        
        if len(deon_clients) == 0:
            print("❌ CRITICAL ISSUE: No Deon Aleong client found in database")
            return False
        elif len(deon_clients) > 1:
            print("⚠️  WARNING: Multiple Deon Aleong clients found - potential duplicates")
            for i, client in enumerate(deon_clients, 1):
                print(f"   Client {i}: {client.get('name')} - {client.get('email')} (ID: {client.get('id')})")
        
        # Use the first Deon client found
        self.deon_client_data = deon_clients[0]
        self.deon_client_id = self.deon_client_data.get('id')
        
        print(f"\n📧 DEON CLIENT EMAIL VERIFICATION:")
        print(f"   Client ID: {self.deon_client_id}")
        print(f"   Client Name: {self.deon_client_data.get('name')}")
        print(f"   Client Email: {self.deon_client_data.get('email')}")
        print(f"   Membership Type: {self.deon_client_data.get('membership_type')}")
        print(f"   Monthly Fee: ${self.deon_client_data.get('monthly_fee')}")
        
        # Verify email address is correct
        expected_email = "deonaleong@gmail.com"
        actual_email = self.deon_client_data.get('email')
        
        if actual_email == expected_email:
            print(f"   ✅ EMAIL ADDRESS CORRECT: {actual_email}")
            return True
        else:
            print(f"   ❌ EMAIL ADDRESS INCORRECT!")
            print(f"      Expected: {expected_email}")
            print(f"      Actual: {actual_email}")
            print(f"   🔧 EMAIL FIX NEEDED: Update client email to deonaleong@gmail.com")
            return False

    def test_2_gmail_smtp_connection(self):
        """CRITICAL TEST 2: Test Gmail SMTP connection directly"""
        print("\n" + "="*80)
        print("🎯 CRITICAL TEST 2: GMAIL SMTP CONNECTION TEST")
        print("="*80)
        
        success, response = self.run_test(
            "Gmail SMTP Connection Test",
            "POST",
            "email/test",
            200
        )
        
        if success:
            email_success = response.get('success', False)
            email_message = response.get('message', 'No message')
            
            print(f"\n📧 GMAIL SMTP STATUS:")
            print(f"   Connection Success: {email_success}")
            print(f"   Connection Message: {email_message}")
            
            if email_success:
                print("   ✅ GMAIL SMTP: WORKING CORRECTLY")
                return True
            else:
                print("   ❌ GMAIL SMTP: CONNECTION FAILED")
                print("   🔧 ISSUE: Gmail app password may be expired or rate limited")
                return False
        else:
            print("   ❌ GMAIL SMTP: API ENDPOINT FAILED")
            return False

    def test_3_payment_reminder_email_success(self):
        """CRITICAL TEST 3: Test payment reminder email (should show success)"""
        print("\n" + "="*80)
        print("🎯 CRITICAL TEST 3: PAYMENT REMINDER EMAIL TEST (EXPECTED SUCCESS)")
        print("="*80)
        
        if not self.deon_client_id:
            print("❌ SKIPPED: No Deon client ID available")
            return False
        
        reminder_data = {
            "client_id": self.deon_client_id,
            "template_name": "default"
        }
        
        print(f"📧 SENDING PAYMENT REMINDER TO: {self.deon_client_data.get('email')}")
        print(f"   Client: {self.deon_client_data.get('name')}")
        print(f"   Amount: ${self.deon_client_data.get('monthly_fee')}")
        
        success, response = self.run_test(
            "Send Payment Reminder to Deon Aleong",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success:
            email_success = response.get('success', False)
            email_message = response.get('message', 'No message')
            client_email = response.get('client_email', 'Unknown')
            
            print(f"\n📧 PAYMENT REMINDER RESULT:")
            print(f"   Email Success: {email_success}")
            print(f"   Email Message: {email_message}")
            print(f"   Client Email: {client_email}")
            
            if email_success:
                print("   ✅ PAYMENT REMINDER: SUCCESS (AS EXPECTED)")
                return True
            else:
                print("   ❌ PAYMENT REMINDER: FAILED (UNEXPECTED)")
                return False
        else:
            print("   ❌ PAYMENT REMINDER: API CALL FAILED")
            return False

    def test_4_payment_recording_invoice_failure(self):
        """CRITICAL TEST 4: Test payment recording with invoice email (expected to show failure)"""
        print("\n" + "="*80)
        print("🎯 CRITICAL TEST 4: PAYMENT RECORDING WITH INVOICE EMAIL (EXPECTED FAILURE)")
        print("="*80)
        
        if not self.deon_client_id:
            print("❌ SKIPPED: No Deon client ID available")
            return False
        
        payment_data = {
            "client_id": self.deon_client_id,
            "amount_paid": 100.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Credit Card",
            "notes": "CRITICAL EMAIL DEBUG TEST - Payment Recording with Invoice"
        }
        
        print(f"💳 RECORDING PAYMENT FOR: {self.deon_client_data.get('email')}")
        print(f"   Client: {self.deon_client_data.get('name')}")
        print(f"   Amount: ${payment_data['amount_paid']}")
        print(f"   Method: {payment_data['payment_method']}")
        
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
            
            print(f"\n💳 PAYMENT RECORDING RESULT:")
            print(f"   Payment Success: {payment_success}")
            print(f"   Invoice Sent: {invoice_sent}")
            print(f"   Invoice Message: {invoice_message}")
            print(f"   Client Name: {client_name}")
            
            if payment_success and invoice_sent is False:
                print("   ⚠️  PAYMENT RECORDING: SUCCESS BUT INVOICE FAILED (ISSUE REPRODUCED)")
                print("   🎯 ROOT CAUSE IDENTIFIED: Payment recording succeeds but invoice email fails")
                return True  # This confirms the issue exists
            elif payment_success and invoice_sent is True:
                print("   ✅ PAYMENT RECORDING: SUCCESS AND INVOICE SENT (ISSUE RESOLVED)")
                return True
            else:
                print("   ❌ PAYMENT RECORDING: FAILED COMPLETELY")
                return False
        else:
            print("   ❌ PAYMENT RECORDING: API CALL FAILED")
            return False

    def test_5_compare_email_mechanisms(self):
        """CRITICAL TEST 5: Compare send_payment_reminder vs send_payment_invoice mechanisms"""
        print("\n" + "="*80)
        print("🎯 CRITICAL TEST 5: COMPARE EMAIL MECHANISMS")
        print("="*80)
        
        print("🔍 ANALYZING EMAIL SENDING MECHANISMS:")
        print("   1. Payment Reminder: Uses send_payment_reminder() function")
        print("   2. Invoice Email: Uses send_payment_invoice() function")
        print("   3. Both use same Gmail SMTP configuration")
        print("   4. Both use same EmailService class")
        
        # Test both mechanisms with same client
        if not self.deon_client_id:
            print("❌ SKIPPED: No Deon client ID available")
            return False
        
        # Test 1: Payment Reminder
        reminder_data = {
            "client_id": self.deon_client_id,
            "template_name": "default"
        }
        
        print(f"\n📧 MECHANISM TEST 1: Payment Reminder")
        success1, response1 = self.run_test(
            "Payment Reminder Mechanism Test",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        reminder_success = False
        if success1:
            reminder_success = response1.get('success', False)
            print(f"   Payment Reminder Success: {reminder_success}")
        
        # Test 2: Record Payment (triggers invoice)
        payment_data = {
            "client_id": self.deon_client_id,
            "amount_paid": 50.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Cash",
            "notes": "Email mechanism comparison test"
        }
        
        print(f"\n💳 MECHANISM TEST 2: Payment Recording (Invoice)")
        success2, response2 = self.run_test(
            "Payment Recording Invoice Mechanism Test",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        invoice_success = False
        if success2:
            invoice_success = response2.get('invoice_sent', False)
            print(f"   Invoice Email Success: {invoice_success}")
        
        # Compare results
        print(f"\n🔍 MECHANISM COMPARISON RESULTS:")
        print(f"   Payment Reminder Success: {reminder_success}")
        print(f"   Invoice Email Success: {invoice_success}")
        
        if reminder_success and not invoice_success:
            print("   ❌ DISCREPANCY CONFIRMED: Reminder succeeds, Invoice fails")
            print("   🎯 ISSUE: Different email mechanisms have different success rates")
            return False
        elif reminder_success and invoice_success:
            print("   ✅ BOTH MECHANISMS WORKING: No discrepancy found")
            return True
        elif not reminder_success and not invoice_success:
            print("   ❌ BOTH MECHANISMS FAILING: General email issue")
            return False
        else:
            print("   ⚠️  UNEXPECTED PATTERN: Invoice succeeds, Reminder fails")
            return False

    def test_6_real_email_monitoring(self):
        """CRITICAL TEST 6: Monitor real email delivery to deonaleong@gmail.com"""
        print("\n" + "="*80)
        print("🎯 CRITICAL TEST 6: REAL EMAIL DELIVERY MONITORING")
        print("="*80)
        
        if not self.deon_client_id:
            print("❌ SKIPPED: No Deon client ID available")
            return False
        
        target_email = "deonaleong@gmail.com"
        print(f"📧 MONITORING EMAIL DELIVERY TO: {target_email}")
        
        # Test 1: Send payment reminder with monitoring
        reminder_data = {
            "client_id": self.deon_client_id,
            "template_name": "professional",
            "custom_subject": "CRITICAL EMAIL DELIVERY TEST - Payment Reminder",
            "custom_message": "This is a critical test to verify email delivery to your Gmail account. If you receive this, payment reminders are working correctly."
        }
        
        print(f"\n📧 SENDING MONITORED PAYMENT REMINDER:")
        success1, response1 = self.run_test(
            "Monitored Payment Reminder to deonaleong@gmail.com",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success1:
            print(f"   API Response Success: {response1.get('success', False)}")
            print(f"   API Response Message: {response1.get('message', 'No message')}")
            print(f"   Target Email: {response1.get('client_email', 'Unknown')}")
        
        # Test 2: Record payment with invoice monitoring
        payment_data = {
            "client_id": self.deon_client_id,
            "amount_paid": 75.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Bank Transfer",
            "notes": "CRITICAL EMAIL DELIVERY TEST - Invoice Email"
        }
        
        print(f"\n💳 RECORDING PAYMENT WITH MONITORED INVOICE:")
        success2, response2 = self.run_test(
            "Monitored Payment Recording with Invoice",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success2:
            print(f"   Payment Success: {response2.get('success', False)}")
            print(f"   Invoice Sent: {response2.get('invoice_sent', False)}")
            print(f"   Invoice Message: {response2.get('invoice_message', 'No message')}")
        
        # Summary
        print(f"\n📊 EMAIL DELIVERY MONITORING SUMMARY:")
        if success1 and success2:
            reminder_api_success = response1.get('success', False)
            invoice_api_success = response2.get('invoice_sent', False)
            
            print(f"   Payment Reminder API Success: {reminder_api_success}")
            print(f"   Invoice Email API Success: {invoice_api_success}")
            
            if reminder_api_success and invoice_api_success:
                print("   ✅ BOTH EMAIL TYPES: API reports success")
                print("   📧 CHECK GMAIL: Both emails should be delivered to deonaleong@gmail.com")
                return True
            elif reminder_api_success and not invoice_api_success:
                print("   ⚠️  DISCREPANCY: Reminder API success, Invoice API failure")
                print("   📧 CHECK GMAIL: Only payment reminder should be received")
                return False
            else:
                print("   ❌ EMAIL DELIVERY ISSUES: Check Gmail SMTP configuration")
                return False
        else:
            print("   ❌ API CALL FAILURES: Cannot monitor email delivery")
            return False

    def test_7_backend_logic_differences(self):
        """CRITICAL TEST 7: Analyze backend logic differences between email types"""
        print("\n" + "="*80)
        print("🎯 CRITICAL TEST 7: BACKEND LOGIC ANALYSIS")
        print("="*80)
        
        print("🔍 ANALYZING BACKEND EMAIL LOGIC DIFFERENCES:")
        print("\n📧 PAYMENT REMINDER ENDPOINT (/api/email/payment-reminder):")
        print("   - Uses CustomEmailRequest model")
        print("   - Calls email_service.send_payment_reminder()")
        print("   - Template: Uses get_email_template() with customization")
        print("   - SMTP: Direct SMTP connection with login")
        
        print("\n💳 PAYMENT RECORDING ENDPOINT (/api/payments/record):")
        print("   - Uses PaymentRecordRequest model")
        print("   - Calls email_service.send_payment_invoice()")
        print("   - Template: Uses fixed invoice HTML template")
        print("   - SMTP: Same SMTP connection with login")
        
        print("\n🔍 KEY DIFFERENCES IDENTIFIED:")
        print("   1. Different email templates (reminder vs invoice)")
        print("   2. Different template rendering logic")
        print("   3. Different error handling paths")
        print("   4. Same SMTP authentication and connection")
        
        # Test template differences
        success, response = self.run_test(
            "Get Email Templates for Analysis",
            "GET",
            "email/templates",
            200
        )
        
        if success:
            templates = response.get('templates', {})
            print(f"\n📋 AVAILABLE TEMPLATES: {list(templates.keys())}")
            print("   Payment Reminder: Uses customizable templates (default, professional, friendly)")
            print("   Invoice Email: Uses fixed invoice template (not customizable)")
            
            print("\n🎯 POTENTIAL ISSUE IDENTIFIED:")
            print("   - Payment reminders use flexible template system")
            print("   - Invoice emails use fixed template with different HTML structure")
            print("   - Template rendering differences may cause SMTP issues")
            
            return True
        else:
            print("   ❌ Cannot analyze templates - API call failed")
            return False

    def run_critical_email_debug_tests(self):
        """Run all critical email debugging tests"""
        print("\n" + "="*100)
        print("🚨 CRITICAL EMAIL DEBUG TESTING - PAYMENT REMINDER SUCCESS vs INVOICE FAILURE")
        print("="*100)
        print("🎯 OBJECTIVE: Debug discrepancy between payment reminder 'success' vs invoice 'failure'")
        print("📧 TARGET: deonaleong@gmail.com")
        print("🔍 FOCUS: Real persistent issues user is experiencing")
        print("="*100)
        
        # Run all critical tests
        test_results = []
        
        test_results.append(self.test_1_verify_deon_client_email_fix())
        test_results.append(self.test_2_gmail_smtp_connection())
        test_results.append(self.test_3_payment_reminder_email_success())
        test_results.append(self.test_4_payment_recording_invoice_failure())
        test_results.append(self.test_5_compare_email_mechanisms())
        test_results.append(self.test_6_real_email_monitoring())
        test_results.append(self.test_7_backend_logic_differences())
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print("\n" + "="*100)
        print("🎯 CRITICAL EMAIL DEBUG TEST SUMMARY")
        print("="*100)
        print(f"📊 TESTS PASSED: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"📧 DEON CLIENT ID: {self.deon_client_id}")
        print(f"📧 DEON CLIENT EMAIL: {self.deon_client_data.get('email') if self.deon_client_data else 'Not found'}")
        
        if passed_tests == total_tests:
            print("✅ ALL TESTS PASSED: Email system appears to be working correctly")
            print("📧 RECOMMENDATION: Check Gmail inbox for deonaleong@gmail.com")
        elif passed_tests >= total_tests * 0.7:
            print("⚠️  PARTIAL SUCCESS: Some email functionality working")
            print("🔧 RECOMMENDATION: Review failed tests for specific issues")
        else:
            print("❌ CRITICAL ISSUES IDENTIFIED: Email system has significant problems")
            print("🚨 RECOMMENDATION: Immediate investigation required")
        
        print("\n🎯 SPECIFIC FINDINGS:")
        if self.deon_client_data:
            if self.deon_client_data.get('email') == 'deonaleong@gmail.com':
                print("   ✅ Deon client email address is correct")
            else:
                print("   ❌ Deon client email address needs correction")
        
        print("="*100)
        
        return passed_tests, total_tests

if __name__ == "__main__":
    print("🚨 CRITICAL EMAIL DEBUG TESTING STARTED")
    print("🎯 Debugging payment reminder SUCCESS vs invoice FAILURE discrepancy")
    
    tester = CriticalEmailDebugTester()
    passed, total = tester.run_critical_email_debug_tests()
    
    print(f"\n🎯 FINAL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ EMAIL SYSTEM: FULLY OPERATIONAL")
        sys.exit(0)
    else:
        print("❌ EMAIL SYSTEM: ISSUES IDENTIFIED")
        sys.exit(1)