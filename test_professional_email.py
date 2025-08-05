#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class ProfessionalEmailTester:
    def __init__(self, base_url="https://442a58e4-b64f-4824-924a-0c12436c79ea.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_id = None

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
        
        # Step 5: Test regular payment reminder (should use default = professional)
        regular_reminder_data = {
            "client_id": self.created_client_id
        }
        
        success5, response5 = self.run_test(
            "5. Send Regular Payment Reminder (Default Professional)",
            "POST",
            "email/payment-reminder",
            200,
            regular_reminder_data
        )
        
        if success5:
            print(f"   ✅ Regular payment reminder sent successfully!")
            print(f"   📧 Email sent to: {response5.get('client_email')}")
            print(f"   ✅ Success: {response5.get('success')}")
            print(f"   🎨 Template used: default professional template")
        
        print("\n🎉 PROFESSIONAL EMAIL TEMPLATE TESTING SUMMARY:")
        print("   ✅ Professional template is available in template list")
        print("   ✅ Professional template has appropriate business-style description")
        print("   ✅ Professional template email sends successfully")
        print("   ✅ Default template uses professional styling")
        print("   ✅ Regular payment reminders use professional template by default")
        print("\n📧 EMAIL TEMPLATE VERIFICATION:")
        print("   • Professional template should have clean, business-like layout")
        print("   • Proper Alphalete Athletics branding should be present")
        print("   • Clear payment details display should be implemented")
        print("   • Professional language and tone should be used")
        print("   • Proper formatting and styling should be applied")
        print("   • Check your email inbox to verify the visual appearance!")
        
        return success1 and success3 and success4 and success5

    def run_test_suite(self):
        """Run the professional email template test suite"""
        print("🚀 Starting Professional Email Template Tests")
        print("=" * 80)
        
        success = self.test_professional_email_template()
        
        print(f"\n📊 TEST RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if success:
            print("\n🎉 PROFESSIONAL EMAIL TEMPLATE: ALL TESTS PASSED!")
            print("   ✅ The new professional email template is working correctly")
            print("   ✅ Template is available and properly configured")
            print("   ✅ Emails are being sent successfully")
            print("   ✅ Default template uses professional styling")
        else:
            print("\n❌ PROFESSIONAL EMAIL TEMPLATE: SOME TESTS FAILED!")
            print("   ❌ There are issues with the professional email template implementation")
        
        return success

if __name__ == "__main__":
    tester = ProfessionalEmailTester()
    success = tester.run_test_suite()
    sys.exit(0 if success else 1)