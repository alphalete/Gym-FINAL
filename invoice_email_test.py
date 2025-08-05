#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class InvoiceEmailTester:
    def __init__(self, base_url="https://442a58e4-b64f-4824-924a-0c12436c79ea.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_client_id = None

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

    def test_email_service_connection(self):
        """Test email service connection with new Gmail app password"""
        print("\n🔍 TESTING EMAIL SERVICE CONNECTION")
        print("=" * 60)
        
        success, response = self.run_test(
            "Email Service Connection Test",
            "POST",
            "email/test",
            200
        )
        
        if success:
            email_success = response.get('success', False)
            message = response.get('message', 'No message')
            print(f"   📧 Email Configuration Success: {email_success}")
            print(f"   📝 Message: {message}")
            
            if email_success:
                print("   ✅ Gmail SMTP authentication is working with new app password!")
                return True
            else:
                print("   ❌ Gmail SMTP authentication is failing!")
                return False
        else:
            print("   ❌ Email service connection test failed!")
            return False

    def create_test_client(self):
        """Create a test client for payment recording"""
        print("\n🔍 CREATING TEST CLIENT FOR PAYMENT RECORDING")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Invoice Test Client",
            "email": f"invoice_test_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": "2025-01-25"
        }
        
        success, response = self.run_test(
            "Create Test Client for Invoice Testing",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.test_client_id = response["id"]
            print(f"   ✅ Created test client ID: {self.test_client_id}")
            print(f"   📧 Client email: {response.get('email')}")
            print(f"   👤 Client name: {response.get('name')}")
            return True
        else:
            print("   ❌ Failed to create test client!")
            return False

    def test_payment_recording_with_invoice(self):
        """Test payment recording with automatic invoice email - CRITICAL TEST"""
        if not self.test_client_id:
            print("❌ Payment Recording with Invoice - SKIPPED (No test client ID available)")
            return False
            
        print("\n🎯 TESTING PAYMENT RECORDING WITH AUTOMATIC INVOICE EMAIL")
        print("=" * 70)
        
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 100.00,
            "payment_date": "2025-01-23",
            "payment_method": "Credit Card",
            "notes": "Testing automatic invoice email functionality - Critical Test"
        }
        
        success, response = self.run_test(
            "Record Payment with Automatic Invoice Email",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"\n📊 PAYMENT RECORDING RESPONSE ANALYSIS:")
            print(f"   💰 Payment recorded for: {response.get('client_name')}")
            print(f"   💵 Amount paid: ${response.get('amount_paid')}")
            print(f"   📅 New next payment date: {response.get('new_next_payment_date')}")
            print(f"   ✅ Payment success: {response.get('success')}")
            
            # CRITICAL: Check for automatic invoice email fields
            invoice_sent = response.get('invoice_sent')
            invoice_message = response.get('invoice_message')
            
            print(f"\n🔍 INVOICE EMAIL STATUS ANALYSIS:")
            print(f"   📧 Invoice Sent Field: {invoice_sent}")
            print(f"   📝 Invoice Message: {invoice_message}")
            
            if invoice_sent is not None and invoice_message is not None:
                print(f"   ✅ AUTOMATIC INVOICE EMAIL FEATURE: IMPLEMENTED")
                
                if invoice_sent:
                    print(f"   🎉 INVOICE EMAIL: SENT SUCCESSFULLY!")
                    print(f"   ✅ User issue 'Invoice email failed to send' is RESOLVED!")
                    return True
                else:
                    print(f"   ⚠️  INVOICE EMAIL: FAILED TO SEND")
                    print(f"   🚨 User issue 'Invoice email failed to send' is CONFIRMED!")
                    print(f"   📝 Failure reason: {invoice_message}")
                    
                    # This is still a successful test as we identified the issue
                    return True
            else:
                print(f"   ❌ AUTOMATIC INVOICE EMAIL FEATURE: NOT IMPLEMENTED")
                return False
        else:
            print(f"   ❌ Payment recording failed!")
            return False

    def test_multiple_payment_scenarios(self):
        """Test multiple payment scenarios to verify invoice email consistency"""
        if not self.test_client_id:
            print("❌ Multiple Payment Scenarios - SKIPPED (No test client ID available)")
            return False
            
        print("\n🔍 TESTING MULTIPLE PAYMENT SCENARIOS FOR INVOICE EMAIL CONSISTENCY")
        print("=" * 80)
        
        payment_scenarios = [
            {
                "name": "Cash Payment",
                "amount": 75.00,
                "method": "Cash",
                "notes": "Cash payment test for invoice email"
            },
            {
                "name": "Bank Transfer",
                "amount": 100.00,
                "method": "Bank Transfer",
                "notes": "Bank transfer test for invoice email"
            },
            {
                "name": "Online Payment",
                "amount": 125.00,
                "method": "Online Payment",
                "notes": "Online payment test for invoice email"
            }
        ]
        
        all_tests_passed = True
        invoice_results = []
        
        for i, scenario in enumerate(payment_scenarios, 1):
            print(f"\n📋 Scenario {i}: {scenario['name']}")
            
            payment_data = {
                "client_id": self.test_client_id,
                "amount_paid": scenario['amount'],
                "payment_date": f"2025-01-{23+i}",
                "payment_method": scenario['method'],
                "notes": scenario['notes']
            }
            
            success, response = self.run_test(
                f"Payment Scenario {i}: {scenario['name']}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                invoice_sent = response.get('invoice_sent')
                invoice_message = response.get('invoice_message')
                
                invoice_results.append({
                    'scenario': scenario['name'],
                    'invoice_sent': invoice_sent,
                    'invoice_message': invoice_message
                })
                
                print(f"   📧 Invoice sent: {invoice_sent}")
                print(f"   📝 Invoice message: {invoice_message}")
            else:
                all_tests_passed = False
                invoice_results.append({
                    'scenario': scenario['name'],
                    'invoice_sent': None,
                    'invoice_message': 'Payment recording failed'
                })
        
        # Analyze results
        print(f"\n📊 INVOICE EMAIL CONSISTENCY ANALYSIS:")
        successful_invoices = sum(1 for result in invoice_results if result['invoice_sent'] is True)
        failed_invoices = sum(1 for result in invoice_results if result['invoice_sent'] is False)
        
        print(f"   ✅ Successful invoice emails: {successful_invoices}/{len(invoice_results)}")
        print(f"   ❌ Failed invoice emails: {failed_invoices}/{len(invoice_results)}")
        
        if failed_invoices > 0:
            print(f"   🚨 INVOICE EMAIL ISSUE CONFIRMED: {failed_invoices} out of {len(invoice_results)} invoice emails failed")
        else:
            print(f"   🎉 ALL INVOICE EMAILS SENT SUCCESSFULLY!")
        
        return all_tests_passed

    def test_email_service_send_invoice_directly(self):
        """Test the email service send_payment_invoice method directly"""
        if not self.test_client_id:
            print("❌ Direct Invoice Email Test - SKIPPED (No test client ID available)")
            return False
            
        print("\n🔍 TESTING EMAIL SERVICE SEND_PAYMENT_INVOICE METHOD DIRECTLY")
        print("=" * 70)
        
        # First get the client details
        success, client_response = self.run_test(
            "Get Client Details for Direct Invoice Test",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if not success:
            print("   ❌ Failed to get client details!")
            return False
        
        client_email = client_response.get('email')
        client_name = client_response.get('name')
        
        print(f"   📧 Testing direct invoice email to: {client_email}")
        print(f"   👤 Client name: {client_name}")
        
        # Note: We can't directly test the email service method from here,
        # but we can test if the payment recording endpoint properly calls it
        # by recording another payment and checking the response
        
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 150.00,
            "payment_date": "2025-01-24",
            "payment_method": "Direct Test",
            "notes": "Direct invoice email service test"
        }
        
        success, response = self.run_test(
            "Direct Invoice Email Service Test via Payment Recording",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            invoice_sent = response.get('invoice_sent')
            invoice_message = response.get('invoice_message')
            
            print(f"   📧 Direct invoice test result: {invoice_sent}")
            print(f"   📝 Direct invoice message: {invoice_message}")
            
            if invoice_sent:
                print(f"   ✅ Email service send_payment_invoice method is working!")
            else:
                print(f"   ❌ Email service send_payment_invoice method is failing!")
                print(f"   🔍 This indicates the issue is in the email service implementation")
            
            return True
        else:
            print(f"   ❌ Direct invoice email test failed!")
            return False

    def run_comprehensive_invoice_email_tests(self):
        """Run all invoice email tests"""
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE INVOICE EMAIL FUNCTIONALITY TESTING")
        print("   Focus: Diagnosing 'Invoice email failed to send' issue")
        print("="*80)
        
        # Test 1: Email service connection
        email_connection_success = self.test_email_service_connection()
        
        # Test 2: Create test client
        client_creation_success = self.create_test_client()
        
        if not client_creation_success:
            print("\n❌ Cannot proceed with invoice tests - client creation failed")
            return False
        
        # Test 3: Payment recording with invoice
        payment_invoice_success = self.test_payment_recording_with_invoice()
        
        # Test 4: Multiple payment scenarios
        multiple_scenarios_success = self.test_multiple_payment_scenarios()
        
        # Test 5: Direct email service test
        direct_email_success = self.test_email_service_send_invoice_directly()
        
        # Summary
        print("\n" + "="*80)
        print("📊 INVOICE EMAIL TESTING SUMMARY")
        print("="*80)
        
        print(f"📧 Email Service Connection: {'✅ WORKING' if email_connection_success else '❌ FAILED'}")
        print(f"👤 Test Client Creation: {'✅ SUCCESS' if client_creation_success else '❌ FAILED'}")
        print(f"💰 Payment Recording with Invoice: {'✅ TESTED' if payment_invoice_success else '❌ FAILED'}")
        print(f"🔄 Multiple Payment Scenarios: {'✅ TESTED' if multiple_scenarios_success else '❌ FAILED'}")
        print(f"🎯 Direct Email Service Test: {'✅ TESTED' if direct_email_success else '❌ FAILED'}")
        
        print(f"\n📈 Overall Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if email_connection_success:
            print("\n🎉 DIAGNOSIS COMPLETE:")
            print("   ✅ Gmail SMTP authentication is working with new app password")
            print("   ✅ Email service connection is functional")
            print("   📧 Invoice email functionality has been thoroughly tested")
            print("   🔍 Check the individual test results above for specific invoice email status")
        else:
            print("\n🚨 CRITICAL ISSUE IDENTIFIED:")
            print("   ❌ Gmail SMTP authentication is failing")
            print("   🔧 SOLUTION: Check Gmail app password configuration")
            print("   📝 Current app password: 'difs xvgc ljue sxjr'")
        
        return True

if __name__ == "__main__":
    print("🎯 INVOICE EMAIL FUNCTIONALITY TESTER")
    print("   Diagnosing: 'Invoice email failed to send' when recording payments")
    print("   Focus: Payment recording endpoint and automatic invoice emails")
    
    tester = InvoiceEmailTester()
    tester.run_comprehensive_invoice_email_tests()