#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class EmailDiagnosticTester:
    def __init__(self, base_url="https://413cf26f-b3f7-4bfe-b0d4-96a01530ff67.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_id = None
        self.email_errors = []

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

    def test_email_service_configuration(self):
        """Test 1: Email Service Configuration - Test SMTP connection and Gmail credentials"""
        print("\n" + "="*80)
        print("🔧 TEST 1: EMAIL SERVICE CONFIGURATION")
        print("="*80)
        
        success, response = self.run_test(
            "Email Service Configuration Test",
            "POST",
            "email/test",
            200
        )
        
        if success:
            email_success = response.get('success', False)
            message = response.get('message', 'No message')
            
            print(f"\n📊 EMAIL CONFIGURATION RESULTS:")
            print(f"   SMTP Connection: {'✅ SUCCESS' if email_success else '❌ FAILED'}")
            print(f"   Message: {message}")
            
            if not email_success:
                print(f"\n🚨 EMAIL CONFIGURATION ISSUE DETECTED:")
                print(f"   - Gmail SMTP connection failed")
                print(f"   - Check Gmail app password: kmgy qduv iioa wgda")
                print(f"   - Check Gmail email: alphaleteclub@gmail.com")
                print(f"   - Verify SMTP settings: smtp.gmail.com:587")
                self.email_errors.append("Gmail SMTP configuration failed")
        else:
            print(f"\n🚨 EMAIL TEST ENDPOINT FAILED:")
            print(f"   - Cannot reach /api/email/test endpoint")
            self.email_errors.append("Email test endpoint unreachable")
        
        return success

    def test_email_templates_system(self):
        """Test 2: Email Template System - Verify templates are available"""
        print("\n" + "="*80)
        print("📧 TEST 2: EMAIL TEMPLATE SYSTEM")
        print("="*80)
        
        success, response = self.run_test(
            "Get Email Templates",
            "GET",
            "email/templates",
            200
        )
        
        if success:
            templates = response.get('templates', {})
            print(f"\n📊 EMAIL TEMPLATE RESULTS:")
            print(f"   Available Templates: {len(templates)}")
            
            expected_templates = ['default', 'professional', 'friendly']
            for template_name in expected_templates:
                if template_name in templates:
                    template_info = templates[template_name]
                    print(f"   ✅ {template_name.upper()}: {template_info.get('name')} - {template_info.get('description')}")
                else:
                    print(f"   ❌ {template_name.upper()}: Missing")
                    self.email_errors.append(f"Missing {template_name} template")
            
            # Check professional template specifically
            if 'professional' in templates:
                prof_desc = templates['professional'].get('description', '').lower()
                professional_keywords = ['professional', 'business', 'clean', 'formal']
                found_keywords = [kw for kw in professional_keywords if kw in prof_desc]
                if found_keywords:
                    print(f"   ✅ Professional template has business keywords: {found_keywords}")
                else:
                    print(f"   ⚠️  Professional template may lack business terminology")
        else:
            print(f"\n🚨 EMAIL TEMPLATES ENDPOINT FAILED:")
            self.email_errors.append("Email templates endpoint failed")
        
        return success

    def create_test_client(self):
        """Create a test client for email testing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Email Test Client",
            "email": f"email_test_{timestamp}@example.com",
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
            print(f"   ✅ Created test client ID: {self.created_client_id}")
            print(f"   📧 Test email: {response.get('email')}")
            return True
        else:
            print("   ❌ Failed to create test client for email testing")
            self.email_errors.append("Cannot create test client for email testing")
            return False

    def test_manual_payment_reminder_sending(self):
        """Test 3: Manual Payment Reminder Sending - Test POST /api/email/payment-reminder"""
        print("\n" + "="*80)
        print("📤 TEST 3: MANUAL PAYMENT REMINDER SENDING")
        print("="*80)
        
        if not self.created_client_id:
            if not self.create_test_client():
                return False
        
        # Test basic payment reminder
        reminder_data = {
            "client_id": self.created_client_id
        }
        
        success, response = self.run_test(
            "Send Basic Payment Reminder",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success:
            email_sent = response.get('success', False)
            client_email = response.get('client_email', 'Unknown')
            message = response.get('message', 'No message')
            
            print(f"\n📊 PAYMENT REMINDER RESULTS:")
            print(f"   Email Sent: {'✅ SUCCESS' if email_sent else '❌ FAILED'}")
            print(f"   Target Email: {client_email}")
            print(f"   Response Message: {message}")
            
            if not email_sent:
                print(f"\n🚨 PAYMENT REMINDER SENDING FAILED:")
                print(f"   - Email service unable to send payment reminder")
                print(f"   - This is the core issue reported by user")
                self.email_errors.append(f"Payment reminder failed to send: {message}")
            else:
                print(f"\n✅ PAYMENT REMINDER SENDING SUCCESSFUL")
        else:
            print(f"\n🚨 PAYMENT REMINDER ENDPOINT FAILED:")
            self.email_errors.append("Payment reminder endpoint failed")
        
        return success and response.get('success', False) if success else False

    def test_custom_email_sending(self):
        """Test 4: Custom Email Sending - Test POST /api/email/custom-reminder"""
        print("\n" + "="*80)
        print("📧 TEST 4: CUSTOM EMAIL SENDING")
        print("="*80)
        
        if not self.created_client_id:
            if not self.create_test_client():
                return False
        
        # Test custom email with professional template
        custom_email_data = {
            "client_id": self.created_client_id,
            "template_name": "professional",
            "custom_subject": "Email Diagnosis Test - Professional Template",
            "custom_message": "This is a diagnostic test to identify email sending issues in the member management system.",
            "custom_amount": 125.00,
            "custom_due_date": "February 15, 2025"
        }
        
        success, response = self.run_test(
            "Send Custom Email (Professional Template)",
            "POST",
            "email/custom-reminder",
            200,
            custom_email_data
        )
        
        if success:
            email_sent = response.get('success', False)
            client_email = response.get('client_email', 'Unknown')
            message = response.get('message', 'No message')
            
            print(f"\n📊 CUSTOM EMAIL RESULTS:")
            print(f"   Email Sent: {'✅ SUCCESS' if email_sent else '❌ FAILED'}")
            print(f"   Target Email: {client_email}")
            print(f"   Template Used: professional")
            print(f"   Response Message: {message}")
            
            if not email_sent:
                print(f"\n🚨 CUSTOM EMAIL SENDING FAILED:")
                print(f"   - Custom email functionality not working")
                print(f"   - Email Center feature affected")
                self.email_errors.append(f"Custom email failed to send: {message}")
            else:
                print(f"\n✅ CUSTOM EMAIL SENDING SUCCESSFUL")
        else:
            print(f"\n🚨 CUSTOM EMAIL ENDPOINT FAILED:")
            self.email_errors.append("Custom email endpoint failed")
        
        return success and response.get('success', False) if success else False

    def test_bulk_email_sending(self):
        """Test 5: Bulk Email Sending - Test bulk reminder functionality"""
        print("\n" + "="*80)
        print("📬 TEST 5: BULK EMAIL SENDING")
        print("="*80)
        
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
            results = response.get('results', [])
            
            print(f"\n📊 BULK EMAIL RESULTS:")
            print(f"   Total Clients: {total_clients}")
            print(f"   Sent Successfully: {sent_successfully}")
            print(f"   Failed: {failed}")
            print(f"   Success Rate: {(sent_successfully / total_clients * 100):.1f}%" if total_clients > 0 else "N/A")
            
            # Analyze failures
            if failed > 0:
                print(f"\n🚨 BULK EMAIL FAILURES DETECTED:")
                failure_count = 0
                for result in results:
                    if not result.get('success', True) and failure_count < 5:  # Show first 5 failures
                        print(f"   ❌ {result.get('client_name', 'Unknown')} ({result.get('client_email', 'Unknown')})")
                        if 'error' in result:
                            print(f"      Error: {result['error']}")
                        failure_count += 1
                
                self.email_errors.append(f"Bulk email failures: {failed}/{total_clients} failed")
            else:
                print(f"\n✅ ALL BULK EMAILS SENT SUCCESSFULLY")
        else:
            print(f"\n🚨 BULK EMAIL ENDPOINT FAILED:")
            self.email_errors.append("Bulk email endpoint failed")
        
        return success

    def test_automatic_reminder_system(self):
        """Test 6: Automatic Reminder System - Test scheduler and automatic sending"""
        print("\n" + "="*80)
        print("⏰ TEST 6: AUTOMATIC REMINDER SYSTEM")
        print("="*80)
        
        # Test reminder stats
        success1, stats_response = self.run_test(
            "Get Reminder Statistics",
            "GET",
            "reminders/stats",
            200
        )
        
        if success1:
            total_sent = stats_response.get('total_reminders_sent', 0)
            total_failed = stats_response.get('total_failed_reminders', 0)
            success_rate = stats_response.get('success_rate', 0)
            scheduler_active = stats_response.get('scheduler_active', False)
            
            print(f"\n📊 AUTOMATIC REMINDER STATS:")
            print(f"   Total Reminders Sent: {total_sent}")
            print(f"   Total Failed: {total_failed}")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Scheduler Active: {'✅ YES' if scheduler_active else '❌ NO'}")
            
            if not scheduler_active:
                print(f"\n🚨 SCHEDULER NOT ACTIVE:")
                print(f"   - Automatic reminder scheduler is not running")
                print(f"   - Automatic reminders will not be sent")
                self.email_errors.append("Automatic reminder scheduler not active")
            
            if total_failed > 0:
                print(f"\n⚠️  AUTOMATIC REMINDER FAILURES DETECTED:")
                print(f"   - {total_failed} automatic reminders have failed")
                print(f"   - Success rate: {success_rate:.1f}%")
                self.email_errors.append(f"Automatic reminder failures: {total_failed} failed")
        
        # Test manual reminder run
        success2, run_response = self.run_test(
            "Manual Reminder Test Run",
            "POST",
            "reminders/test-run",
            200
        )
        
        if success2:
            run_success = run_response.get('success', False)
            run_message = run_response.get('message', 'No message')
            
            print(f"\n📊 MANUAL REMINDER RUN:")
            print(f"   Test Run Success: {'✅ YES' if run_success else '❌ NO'}")
            print(f"   Message: {run_message}")
            
            if not run_success:
                print(f"\n🚨 MANUAL REMINDER RUN FAILED:")
                self.email_errors.append(f"Manual reminder run failed: {run_message}")
        
        return success1 and success2

    def diagnose_gmail_specific_issues(self):
        """Test 7: Gmail-Specific Issue Diagnosis"""
        print("\n" + "="*80)
        print("📮 TEST 7: GMAIL-SPECIFIC ISSUE DIAGNOSIS")
        print("="*80)
        
        print(f"\n🔍 GMAIL CONFIGURATION ANALYSIS:")
        print(f"   Gmail Email: alphaleteclub@gmail.com")
        print(f"   Gmail App Password: kmgy qduv iioa wgda")
        print(f"   SMTP Server: smtp.gmail.com")
        print(f"   SMTP Port: 587")
        
        # Common Gmail issues
        print(f"\n🔍 COMMON GMAIL ISSUES TO CHECK:")
        print(f"   1. ❓ App Password Validity:")
        print(f"      - App password may have expired")
        print(f"      - Need to regenerate app password in Gmail settings")
        print(f"   2. ❓ Gmail Account Security:")
        print(f"      - 2-factor authentication must be enabled")
        print(f"      - Less secure app access must be disabled (use app passwords)")
        print(f"   3. ❓ Gmail Rate Limiting:")
        print(f"      - Gmail may be rate limiting due to high volume")
        print(f"      - Daily sending limits may be reached")
        print(f"   4. ❓ SMTP Connection Issues:")
        print(f"      - Network connectivity to smtp.gmail.com:587")
        print(f"      - TLS/SSL handshake problems")
        
        # Test email configuration again with detailed analysis
        success, response = self.run_test(
            "Detailed Gmail Configuration Test",
            "POST",
            "email/test",
            200
        )
        
        if success:
            email_success = response.get('success', False)
            if not email_success:
                print(f"\n🚨 GMAIL CONFIGURATION DIAGNOSIS:")
                print(f"   ❌ Gmail SMTP authentication failed")
                print(f"   🔧 RECOMMENDED ACTIONS:")
                print(f"      1. Verify Gmail app password is correct and not expired")
                print(f"      2. Check if 2FA is enabled on Gmail account")
                print(f"      3. Regenerate app password in Gmail settings")
                print(f"      4. Test SMTP connection manually")
                self.email_errors.append("Gmail SMTP authentication failed - check app password")
            else:
                print(f"\n✅ GMAIL CONFIGURATION IS WORKING")
                print(f"   - SMTP connection successful")
                print(f"   - Authentication working")
                print(f"   - Issue may be in email sending logic or rate limiting")
        
        return success

    def run_comprehensive_email_diagnosis(self):
        """Run all email diagnostic tests"""
        print("\n" + "🔥"*80)
        print("🚨 COMPREHENSIVE EMAIL DIAGNOSIS - MEMBER MANAGEMENT SYSTEM")
        print("🔥"*80)
        print(f"Target: {self.base_url}")
        print(f"Focus: Diagnosing 'email reminder failed to send' issue")
        
        # Run all diagnostic tests
        test_results = []
        
        test_results.append(self.test_email_service_configuration())
        test_results.append(self.test_email_templates_system())
        test_results.append(self.test_manual_payment_reminder_sending())
        test_results.append(self.test_custom_email_sending())
        test_results.append(self.test_bulk_email_sending())
        test_results.append(self.test_automatic_reminder_system())
        test_results.append(self.diagnose_gmail_specific_issues())
        
        # Final diagnosis summary
        print("\n" + "🎯"*80)
        print("📋 FINAL EMAIL DIAGNOSIS SUMMARY")
        print("🎯"*80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n📊 TEST RESULTS:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if self.email_errors:
            print(f"\n🚨 IDENTIFIED EMAIL ISSUES:")
            for i, error in enumerate(self.email_errors, 1):
                print(f"   {i}. {error}")
        else:
            print(f"\n✅ NO CRITICAL EMAIL ISSUES DETECTED")
        
        # Specific recommendations
        print(f"\n🔧 RECOMMENDATIONS FOR USER:")
        if any("Gmail SMTP" in error for error in self.email_errors):
            print(f"   1. 🔑 REGENERATE GMAIL APP PASSWORD:")
            print(f"      - Go to Gmail Settings > Security > App Passwords")
            print(f"      - Generate new app password for 'Mail' application")
            print(f"      - Update backend/.env with new password")
        
        if any("failed to send" in error for error in self.email_errors):
            print(f"   2. 📧 EMAIL SENDING ISSUES:")
            print(f"      - Check Gmail daily sending limits")
            print(f"      - Verify Gmail account is not suspended")
            print(f"      - Test with different email provider if needed")
        
        if any("scheduler" in error for error in self.email_errors):
            print(f"   3. ⏰ SCHEDULER ISSUES:")
            print(f"      - Restart backend service to reinitialize scheduler")
            print(f"      - Check backend logs for scheduler errors")
        
        print(f"\n🎯 ROOT CAUSE ANALYSIS:")
        if not self.email_errors:
            print(f"   ✅ Email system appears to be working correctly")
            print(f"   ✅ Issue may be intermittent or resolved")
        elif any("Gmail" in error for error in self.email_errors):
            print(f"   🎯 PRIMARY ISSUE: Gmail SMTP Configuration")
            print(f"   🔧 SOLUTION: Update Gmail app password")
        elif any("endpoint failed" in error for error in self.email_errors):
            print(f"   🎯 PRIMARY ISSUE: Backend API Problems")
            print(f"   🔧 SOLUTION: Check backend service status")
        else:
            print(f"   🎯 PRIMARY ISSUE: Email Service Logic")
            print(f"   🔧 SOLUTION: Review email service implementation")
        
        return passed_tests, total_tests, self.email_errors

if __name__ == "__main__":
    print("🚀 Starting Email Diagnostic Testing...")
    
    tester = EmailDiagnosticTester()
    passed, total, errors = tester.run_comprehensive_email_diagnosis()
    
    print(f"\n🏁 Email Diagnosis Complete!")
    print(f"📊 Final Score: {passed}/{total} tests passed")
    
    if errors:
        print(f"🚨 {len(errors)} issues identified and documented")
        sys.exit(1)
    else:
        print(f"✅ No critical email issues detected")
        sys.exit(0)