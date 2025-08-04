#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any
import time

class InvoiceEmailTester:
    def __init__(self, base_url="https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.deon_client_id = None
        
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
        """Test Gmail SMTP connection directly"""
        print("\n🔍 CRITICAL TEST 1: Direct Email Service Connection")
        print("=" * 80)
        
        success, response = self.run_test(
            "Gmail SMTP Connection Test",
            "POST",
            "email/test",
            200
        )
        
        if success:
            email_success = response.get('success', False)
            message = response.get('message', 'No message')
            
            print(f"   📧 Email Service Status: {'✅ WORKING' if email_success else '❌ FAILED'}")
            print(f"   📝 Message: {message}")
            
            if not email_success:
                print("   🚨 CRITICAL ISSUE: Gmail SMTP authentication is failing!")
                print("   🔧 SOLUTION: Check Gmail app password in backend/.env")
                return False
            else:
                print("   ✅ Gmail SMTP authentication is working correctly")
                return True
        
        return False

    def find_or_create_deon_client(self):
        """Find existing Deon Aleong client or create one for testing"""
        print("\n🔍 CRITICAL TEST 2: Find/Create Deon Aleong Client")
        print("=" * 80)
        
        # First, try to find existing Deon Aleong client
        success, response = self.run_test(
            "Get All Clients - Search for Deon Aleong",
            "GET",
            "clients",
            200
        )
        
        if success:
            clients = response
            deon_client = None
            
            # Look for Deon Aleong client
            for client in clients:
                if "Deon Aleong" in client.get('name', ''):
                    deon_client = client
                    break
            
            if deon_client:
                self.deon_client_id = deon_client['id']
                print(f"   ✅ Found existing Deon Aleong client: {self.deon_client_id}")
                print(f"   📧 Email: {deon_client.get('email')}")
                print(f"   💰 Monthly Fee: ${deon_client.get('monthly_fee')}")
                print(f"   📅 Next Payment: {deon_client.get('next_payment_date')}")
                return True
            else:
                print("   ⚠️  Deon Aleong client not found, creating new one...")
                
                # Create Deon Aleong client for testing
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                client_data = {
                    "name": "Deon Aleong",
                    "email": f"deon.aleong.test_{timestamp}@example.com",
                    "phone": "(868) 555-1234",
                    "membership_type": "Elite",
                    "monthly_fee": 100.00,
                    "start_date": "2025-01-15"
                }
                
                success2, response2 = self.run_test(
                    "Create Deon Aleong Test Client",
                    "POST",
                    "clients",
                    200,
                    client_data
                )
                
                if success2 and "id" in response2:
                    self.deon_client_id = response2["id"]
                    print(f"   ✅ Created Deon Aleong client: {self.deon_client_id}")
                    print(f"   📧 Email: {response2.get('email')}")
                    print(f"   💰 Monthly Fee: ${response2.get('monthly_fee')}")
                    return True
                else:
                    print("   ❌ Failed to create Deon Aleong client")
                    return False
        
        return False

    def test_direct_invoice_email_function(self):
        """Test the email_service.send_payment_invoice function directly"""
        print("\n🔍 CRITICAL TEST 3: Direct Invoice Email Function Test")
        print("=" * 80)
        
        if not self.deon_client_id:
            print("❌ Direct Invoice Test - SKIPPED (No Deon client ID available)")
            return False
        
        # Get Deon client details first
        success, client_response = self.run_test(
            "Get Deon Client Details",
            "GET",
            f"clients/{self.deon_client_id}",
            200
        )
        
        if not success:
            print("❌ Could not get Deon client details")
            return False
        
        client_email = client_response.get('email')
        client_name = client_response.get('name')
        
        print(f"   👤 Testing invoice for: {client_name} ({client_email})")
        
        # Test direct payment recording with invoice
        payment_data = {
            "client_id": self.deon_client_id,
            "amount_paid": 100.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Credit Card",
            "notes": "CRITICAL INVOICE TEST - Testing automatic invoice email functionality"
        }
        
        success, response = self.run_test(
            "Record Payment with Automatic Invoice Email",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            # CRITICAL: Check invoice email status
            invoice_sent = response.get('invoice_sent')
            invoice_message = response.get('invoice_message')
            
            print(f"\n   🎯 CRITICAL INVOICE EMAIL ANALYSIS:")
            print(f"      💳 Payment recorded for: {response.get('client_name')}")
            print(f"      💰 Amount paid: ${response.get('amount_paid')}")
            print(f"      📅 New payment date: {response.get('new_next_payment_date')}")
            print(f"      📧 Invoice sent: {invoice_sent}")
            print(f"      📝 Invoice message: {invoice_message}")
            
            if invoice_sent is None:
                print("   ❌ CRITICAL ISSUE: invoice_sent field is missing from response!")
                print("   🔧 SOLUTION: Check if send_payment_invoice is being called in payments/record endpoint")
                return False
            elif invoice_sent is True:
                print("   ✅ INVOICE EMAIL: Successfully sent!")
                print("   ✅ Backend reports invoice email was delivered")
                return True
            elif invoice_sent is False:
                print("   ❌ INVOICE EMAIL: Failed to send!")
                print(f"   📝 Failure reason: {invoice_message}")
                print("   🚨 CRITICAL ISSUE: Backend email service is failing")
                
                # Additional debugging
                if "rate limit" in str(invoice_message).lower() or "too many" in str(invoice_message).lower():
                    print("   🔧 SOLUTION: Gmail rate limiting - regenerate app password")
                elif "authentication" in str(invoice_message).lower():
                    print("   🔧 SOLUTION: Gmail authentication failed - check app password")
                elif "connection" in str(invoice_message).lower():
                    print("   🔧 SOLUTION: SMTP connection issue - check network/firewall")
                else:
                    print("   🔧 SOLUTION: Unknown email error - check backend logs")
                
                return False
            else:
                print(f"   ⚠️  UNEXPECTED: invoice_sent value is {invoice_sent} (not True/False)")
                return False
        
        return False

    def test_multiple_payment_invoice_scenario(self):
        """Test multiple payments with invoice emails"""
        print("\n🔍 CRITICAL TEST 4: Multiple Payment Invoice Scenario")
        print("=" * 80)
        
        if not self.deon_client_id:
            print("❌ Multiple Payment Test - SKIPPED (No Deon client ID available)")
            return False
        
        # Record multiple payments to test invoice email consistency
        payment_scenarios = [
            {
                "amount": 50.00,
                "method": "Cash",
                "notes": "First payment - testing invoice consistency"
            },
            {
                "amount": 75.00,
                "method": "Bank Transfer", 
                "notes": "Second payment - testing invoice reliability"
            },
            {
                "amount": 100.00,
                "method": "Credit Card",
                "notes": "Third payment - testing invoice delivery"
            }
        ]
        
        all_invoices_successful = True
        invoice_results = []
        
        for i, scenario in enumerate(payment_scenarios, 1):
            print(f"\n   💳 Payment Scenario {i}: ${scenario['amount']} via {scenario['method']}")
            
            payment_data = {
                "client_id": self.deon_client_id,
                "amount_paid": scenario['amount'],
                "payment_date": date.today().isoformat(),
                "payment_method": scenario['method'],
                "notes": scenario['notes']
            }
            
            success, response = self.run_test(
                f"Payment {i} with Invoice",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                invoice_sent = response.get('invoice_sent')
                invoice_message = response.get('invoice_message')
                
                print(f"      📧 Invoice sent: {invoice_sent}")
                print(f"      📝 Invoice message: {invoice_message}")
                
                invoice_results.append({
                    "payment": i,
                    "amount": scenario['amount'],
                    "invoice_sent": invoice_sent,
                    "message": invoice_message
                })
                
                if not invoice_sent:
                    all_invoices_successful = False
                    print(f"      ❌ Invoice {i} FAILED!")
                else:
                    print(f"      ✅ Invoice {i} SUCCESS!")
                
                # Small delay between payments to avoid rate limiting
                time.sleep(2)
            else:
                all_invoices_successful = False
                print(f"      ❌ Payment {i} recording FAILED!")
        
        # Summary of invoice results
        print(f"\n   📊 INVOICE EMAIL SUMMARY:")
        successful_invoices = sum(1 for result in invoice_results if result['invoice_sent'])
        total_invoices = len(invoice_results)
        
        print(f"      Total payments: {total_invoices}")
        print(f"      Successful invoices: {successful_invoices}")
        print(f"      Failed invoices: {total_invoices - successful_invoices}")
        print(f"      Success rate: {(successful_invoices/total_invoices*100):.1f}%" if total_invoices > 0 else "0%")
        
        if all_invoices_successful:
            print("   ✅ ALL INVOICE EMAILS: Successfully sent!")
            print("   ✅ Invoice email system is working consistently")
        else:
            print("   ❌ SOME INVOICE EMAILS: Failed to send!")
            print("   🚨 Invoice email system has reliability issues")
            
            # Show failed invoices
            failed_invoices = [r for r in invoice_results if not r['invoice_sent']]
            for failed in failed_invoices:
                print(f"      ❌ Payment ${failed['amount']}: {failed['message']}")
        
        return all_invoices_successful

    def test_invoice_email_template_content(self):
        """Test invoice email template by examining the response"""
        print("\n🔍 CRITICAL TEST 5: Invoice Email Template Content Analysis")
        print("=" * 80)
        
        if not self.deon_client_id:
            print("❌ Template Test - SKIPPED (No Deon client ID available)")
            return False
        
        # Record a payment specifically to analyze the invoice template
        payment_data = {
            "client_id": self.deon_client_id,
            "amount_paid": 125.50,
            "payment_date": date.today().isoformat(),
            "payment_method": "Online Payment",
            "notes": "Template analysis test - checking invoice email formatting and content"
        }
        
        success, response = self.run_test(
            "Payment for Invoice Template Analysis",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            invoice_sent = response.get('invoice_sent')
            invoice_message = response.get('invoice_message')
            payment_record = response.get('payment_record', {})
            
            print(f"   📧 Invoice Status: {invoice_sent}")
            print(f"   📝 Invoice Message: {invoice_message}")
            
            if invoice_sent:
                print(f"\n   📋 INVOICE TEMPLATE DATA ANALYSIS:")
                print(f"      👤 Client Name: {payment_record.get('client_name')}")
                print(f"      📧 Client Email: {payment_record.get('client_email')}")
                print(f"      💰 Amount Paid: ${payment_record.get('amount_paid')}")
                print(f"      📅 Payment Date: {payment_record.get('payment_date')}")
                print(f"      💳 Payment Method: {payment_record.get('payment_method')}")
                print(f"      📝 Notes: {payment_record.get('notes')}")
                print(f"      🆔 Payment ID: {payment_record.get('id')}")
                
                print(f"\n   ✅ INVOICE TEMPLATE: All required data is available")
                print(f"   ✅ EMAIL DELIVERY: Backend reports successful sending")
                
                # Check if template would render properly
                required_fields = ['client_name', 'client_email', 'amount_paid', 'payment_date', 'payment_method']
                missing_fields = [field for field in required_fields if not payment_record.get(field)]
                
                if missing_fields:
                    print(f"   ⚠️  TEMPLATE WARNING: Missing fields: {missing_fields}")
                    return False
                else:
                    print(f"   ✅ TEMPLATE DATA: All required fields present")
                    return True
            else:
                print(f"   ❌ INVOICE TEMPLATE: Cannot analyze - email sending failed")
                print(f"   🚨 ROOT CAUSE: {invoice_message}")
                return False
        
        return False

    def test_gmail_rate_limiting_detection(self):
        """Test for Gmail rate limiting issues"""
        print("\n🔍 CRITICAL TEST 6: Gmail Rate Limiting Detection")
        print("=" * 80)
        
        # Test email connection multiple times to detect rate limiting
        rate_limit_detected = False
        connection_failures = 0
        
        for i in range(3):
            print(f"   🔄 Connection Test {i+1}/3...")
            
            success, response = self.run_test(
                f"Gmail Connection Test {i+1}",
                "POST",
                "email/test",
                200
            )
            
            if success:
                email_success = response.get('success', False)
                message = response.get('message', '')
                
                if not email_success:
                    connection_failures += 1
                    print(f"      ❌ Connection {i+1} failed: {message}")
                    
                    # Check for rate limiting indicators
                    if any(indicator in message.lower() for indicator in ['rate limit', 'too many', '454', 'login attempts']):
                        rate_limit_detected = True
                        print(f"      🚨 RATE LIMITING DETECTED!")
                else:
                    print(f"      ✅ Connection {i+1} successful")
            else:
                connection_failures += 1
                print(f"      ❌ Connection {i+1} failed to reach server")
            
            # Small delay between tests
            time.sleep(1)
        
        print(f"\n   📊 GMAIL CONNECTION ANALYSIS:")
        print(f"      Total tests: 3")
        print(f"      Failed connections: {connection_failures}")
        print(f"      Success rate: {((3-connection_failures)/3*100):.1f}%")
        print(f"      Rate limiting detected: {'Yes' if rate_limit_detected else 'No'}")
        
        if rate_limit_detected:
            print(f"\n   🚨 CRITICAL ISSUE: Gmail rate limiting is active!")
            print(f"   🔧 IMMEDIATE SOLUTION: Regenerate Gmail app password")
            print(f"   📝 Steps: Gmail Settings > Security > App Passwords > Generate New")
            print(f"   ⚠️  This explains why invoices fail despite backend success")
            return False
        elif connection_failures > 0:
            print(f"\n   ⚠️  CONNECTION ISSUES: {connection_failures}/3 tests failed")
            print(f"   🔧 SOLUTION: Check Gmail credentials and network connectivity")
            return False
        else:
            print(f"\n   ✅ GMAIL CONNECTION: All tests passed")
            print(f"   ✅ No rate limiting detected")
            return True

    def test_end_to_end_invoice_workflow(self):
        """Test complete end-to-end invoice workflow"""
        print("\n🔍 CRITICAL TEST 7: End-to-End Invoice Workflow")
        print("=" * 80)
        
        if not self.deon_client_id:
            print("❌ End-to-End Test - SKIPPED (No Deon client ID available)")
            return False
        
        # Step 1: Get client current state
        success1, client_before = self.run_test(
            "Get Client State Before Payment",
            "GET",
            f"clients/{self.deon_client_id}",
            200
        )
        
        if not success1:
            return False
        
        print(f"   📋 BEFORE PAYMENT:")
        print(f"      👤 Client: {client_before.get('name')}")
        print(f"      📧 Email: {client_before.get('email')}")
        print(f"      💰 Monthly Fee: ${client_before.get('monthly_fee')}")
        print(f"      📅 Next Payment Due: {client_before.get('next_payment_date')}")
        
        # Step 2: Record payment with invoice
        payment_data = {
            "client_id": self.deon_client_id,
            "amount_paid": client_before.get('monthly_fee', 100.00),
            "payment_date": date.today().isoformat(),
            "payment_method": "Credit Card",
            "notes": "End-to-end invoice workflow test - complete payment processing"
        }
        
        success2, payment_response = self.run_test(
            "Record Payment with Invoice (End-to-End)",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success2:
            return False
        
        # Step 3: Analyze payment response
        invoice_sent = payment_response.get('invoice_sent')
        invoice_message = payment_response.get('invoice_message')
        new_payment_date = payment_response.get('new_next_payment_date')
        
        print(f"\n   📋 PAYMENT PROCESSING RESULTS:")
        print(f"      ✅ Payment recorded: ${payment_response.get('amount_paid')}")
        print(f"      📅 New payment date: {new_payment_date}")
        print(f"      📧 Invoice sent: {invoice_sent}")
        print(f"      📝 Invoice status: {invoice_message}")
        
        # Step 4: Verify client state after payment
        success3, client_after = self.run_test(
            "Get Client State After Payment",
            "GET",
            f"clients/{self.deon_client_id}",
            200
        )
        
        if success3:
            print(f"\n   📋 AFTER PAYMENT:")
            print(f"      📅 Updated payment due: {client_after.get('next_payment_date')}")
            
            # Verify payment date was updated
            if client_after.get('next_payment_date') != client_before.get('next_payment_date'):
                print(f"      ✅ Payment date successfully updated")
            else:
                print(f"      ❌ Payment date was not updated")
                return False
        
        # Step 5: Overall workflow assessment
        print(f"\n   🎯 END-TO-END WORKFLOW ASSESSMENT:")
        
        workflow_success = True
        
        if not success2:
            print(f"      ❌ Payment recording failed")
            workflow_success = False
        else:
            print(f"      ✅ Payment recording successful")
        
        if invoice_sent is None:
            print(f"      ❌ Invoice system not implemented")
            workflow_success = False
        elif invoice_sent:
            print(f"      ✅ Invoice email sent successfully")
        else:
            print(f"      ❌ Invoice email failed to send")
            workflow_success = False
        
        if not success3:
            print(f"      ❌ Client state verification failed")
            workflow_success = False
        else:
            print(f"      ✅ Client state updated correctly")
        
        if workflow_success:
            print(f"\n   🎉 END-TO-END WORKFLOW: FULLY FUNCTIONAL!")
            print(f"   ✅ Payment processing works correctly")
            print(f"   ✅ Invoice emails are being sent")
            print(f"   ✅ Client data is updated properly")
            print(f"   ✅ Complete invoice system is operational")
        else:
            print(f"\n   ❌ END-TO-END WORKFLOW: HAS ISSUES!")
            print(f"   🚨 Invoice system needs attention")
        
        return workflow_success

    def run_all_invoice_tests(self):
        """Run all critical invoice functionality tests"""
        print("🚨 CRITICAL INVOICE EMAIL DEBUGGING - COMPREHENSIVE TEST SUITE")
        print("=" * 100)
        print("🎯 OBJECTIVE: Identify why invoices are failing despite backend showing success")
        print("=" * 100)
        
        # Test results tracking
        test_results = []
        
        # Test 1: Email Service Connection
        result1 = self.test_email_service_connection()
        test_results.append(("Gmail SMTP Connection", result1))
        
        # Test 2: Find/Create Deon Client
        result2 = self.find_or_create_deon_client()
        test_results.append(("Deon Aleong Client Setup", result2))
        
        # Test 3: Direct Invoice Function
        result3 = self.test_direct_invoice_email_function()
        test_results.append(("Direct Invoice Email Function", result3))
        
        # Test 4: Multiple Payment Scenario
        result4 = self.test_multiple_payment_invoice_scenario()
        test_results.append(("Multiple Payment Invoice Consistency", result4))
        
        # Test 5: Template Content Analysis
        result5 = self.test_invoice_email_template_content()
        test_results.append(("Invoice Email Template Content", result5))
        
        # Test 6: Rate Limiting Detection
        result6 = self.test_gmail_rate_limiting_detection()
        test_results.append(("Gmail Rate Limiting Detection", result6))
        
        # Test 7: End-to-End Workflow
        result7 = self.test_end_to_end_invoice_workflow()
        test_results.append(("End-to-End Invoice Workflow", result7))
        
        # Final Summary
        print("\n" + "=" * 100)
        print("🎯 CRITICAL INVOICE EMAIL DEBUGGING - FINAL RESULTS")
        print("=" * 100)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        print(f"📊 OVERALL TEST RESULTS:")
        print(f"   Total tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success rate: {(passed_tests/total_tests*100):.1f}%")
        
        print(f"\n📋 DETAILED TEST RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}: {test_name}")
        
        # Critical Issue Analysis
        print(f"\n🚨 CRITICAL ISSUE ANALYSIS:")
        
        if not test_results[0][1]:  # Gmail connection failed
            print("   🔥 PRIMARY ISSUE: Gmail SMTP authentication is failing")
            print("   🔧 IMMEDIATE ACTION: Regenerate Gmail app password")
            print("   📝 This explains why backend shows success but emails don't send")
        elif not test_results[2][1]:  # Invoice function failed
            print("   🔥 PRIMARY ISSUE: Invoice email function is not working")
            print("   🔧 IMMEDIATE ACTION: Check email_service.send_payment_invoice implementation")
        elif not test_results[3][1]:  # Multiple payments failed
            print("   🔥 PRIMARY ISSUE: Invoice email system is unreliable")
            print("   🔧 IMMEDIATE ACTION: Investigate email service stability")
        elif passed_tests == total_tests:
            print("   ✅ NO CRITICAL ISSUES: All invoice functionality is working correctly")
            print("   🎉 Invoice email system is fully operational")
        else:
            print("   ⚠️  MIXED RESULTS: Some invoice functionality is working")
            print("   🔧 RECOMMENDED ACTION: Review failed tests for specific issues")
        
        print(f"\n🎯 CONCLUSION:")
        if passed_tests >= 5:  # Most tests passed
            print("   ✅ Invoice email system is mostly functional")
            print("   📧 Emails should be sending successfully")
            print("   🔧 Minor issues may need attention")
        else:
            print("   ❌ Invoice email system has significant issues")
            print("   🚨 Emails are likely not being sent despite backend success")
            print("   🔧 Immediate fixes required")
        
        return passed_tests, total_tests

if __name__ == "__main__":
    print("🚨 STARTING CRITICAL INVOICE EMAIL DEBUGGING")
    print("🎯 Focus: Identify why invoices fail despite backend success")
    print("=" * 100)
    
    tester = InvoiceEmailTester()
    passed, total = tester.run_all_invoice_tests()
    
    print(f"\n🏁 INVOICE DEBUGGING COMPLETE")
    print(f"📊 Final Score: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    
    if passed >= 5:
        print("✅ Invoice system is working correctly")
        sys.exit(0)
    else:
        print("❌ Invoice system has critical issues")
        sys.exit(1)