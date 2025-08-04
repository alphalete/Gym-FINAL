#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

class DeonAleongDebugTester:
    """
    CRITICAL DEBUGGING - FRONTEND vs BACKEND DISCREPANCY
    
    Debug the discrepancy between backend testing (showing 100% invoice success) 
    and actual frontend user experience (showing invoice failures).
    
    Focus: Test the actual payment recording API with real Deon Aleong client data.
    """
    
    def __init__(self, base_url="https://276b2f1f-9d6e-4215-a382-5da8671edad7.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.deon_clients = []  # Store all Deon Aleong clients found
        self.primary_deon_client = None  # The main Deon client to test with

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

    def find_deon_aleong_clients(self):
        """
        STEP 1: Get Current Deon Aleong Client(s)
        - GET /api/clients to find the exact Deon Aleong client the user is interacting with
        - Get the client ID and email address
        - Verify the client exists and has correct data
        """
        print("\n" + "="*80)
        print("🎯 STEP 1: FINDING DEON ALEONG CLIENT(S)")
        print("="*80)
        
        success, response = self.run_test(
            "Get All Clients to Find Deon Aleong",
            "GET",
            "clients",
            200
        )
        
        if not success:
            print("❌ CRITICAL: Cannot retrieve clients list")
            return False
            
        clients = response if isinstance(response, list) else []
        print(f"\n📊 TOTAL CLIENTS FOUND: {len(clients)}")
        
        # Search for Deon Aleong clients (case-insensitive)
        deon_variations = ['deon aleong', 'deon', 'aleong']
        
        for client in clients:
            client_name = client.get('name', '').lower()
            client_email = client.get('email', '').lower()
            
            # Check if this is a Deon Aleong client
            is_deon = any(variation in client_name for variation in deon_variations)
            is_deon_email = 'deon' in client_email or 'aleong' in client_email
            
            if is_deon or is_deon_email:
                self.deon_clients.append(client)
                print(f"\n🎯 FOUND DEON ALEONG CLIENT:")
                print(f"   ID: {client.get('id')}")
                print(f"   Name: {client.get('name')}")
                print(f"   Email: {client.get('email')}")
                print(f"   Phone: {client.get('phone')}")
                print(f"   Membership: {client.get('membership_type')}")
                print(f"   Monthly Fee: ${client.get('monthly_fee')}")
                print(f"   Status: {client.get('status')}")
                print(f"   Start Date: {client.get('start_date')}")
                print(f"   Next Payment Date: {client.get('next_payment_date')}")
                print(f"   Auto Reminders: {client.get('auto_reminders_enabled')}")
        
        if not self.deon_clients:
            print("\n⚠️  NO DEON ALEONG CLIENTS FOUND!")
            print("   Creating a test Deon Aleong client for debugging...")
            return self.create_test_deon_client()
        
        # Set primary client (first one found)
        self.primary_deon_client = self.deon_clients[0]
        
        print(f"\n✅ FOUND {len(self.deon_clients)} DEON ALEONG CLIENT(S)")
        if len(self.deon_clients) > 1:
            print("⚠️  MULTIPLE DEON CLIENTS DETECTED - This could cause ID confusion!")
            for i, client in enumerate(self.deon_clients):
                print(f"   Client {i+1}: {client.get('name')} ({client.get('id')})")
        
        print(f"\n🎯 PRIMARY DEON CLIENT FOR TESTING:")
        print(f"   ID: {self.primary_deon_client.get('id')}")
        print(f"   Name: {self.primary_deon_client.get('name')}")
        print(f"   Email: {self.primary_deon_client.get('email')}")
        
        return True

    def create_test_deon_client(self):
        """Create a test Deon Aleong client if none exists"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Deon Aleong",
            "email": f"deon.aleong.test.{timestamp}@example.com",
            "phone": "(868) 555-1234",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": "2025-01-15",
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Create Test Deon Aleong Client",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.deon_clients.append(response)
            self.primary_deon_client = response
            print(f"✅ Created test Deon Aleong client: {response.get('id')}")
            return True
        
        return False

    def test_actual_payment_recording(self):
        """
        STEP 2: Test Actual Payment Recording
        - Use POST /api/payments/record with the EXACT Deon Aleong client ID from step 1
        - Monitor the actual `invoice_sent` field in the response
        - Check the exact `invoice_message` returned
        """
        print("\n" + "="*80)
        print("🎯 STEP 2: TESTING ACTUAL PAYMENT RECORDING WITH DEON ALEONG")
        print("="*80)
        
        if not self.primary_deon_client:
            print("❌ CRITICAL: No Deon Aleong client available for testing")
            return False
        
        client_id = self.primary_deon_client.get('id')
        client_name = self.primary_deon_client.get('name')
        client_email = self.primary_deon_client.get('email')
        
        print(f"\n🎯 TESTING WITH EXACT DEON ALEONG CLIENT:")
        print(f"   Client ID: {client_id}")
        print(f"   Client Name: {client_name}")
        print(f"   Client Email: {client_email}")
        
        # Test multiple payment scenarios to check consistency
        payment_scenarios = [
            {
                "name": "Cash Payment Test",
                "amount": 50.00,
                "method": "Cash",
                "notes": "Debug test - Cash payment for Deon Aleong"
            },
            {
                "name": "Bank Transfer Test", 
                "amount": 75.00,
                "method": "Bank Transfer",
                "notes": "Debug test - Bank transfer for Deon Aleong"
            },
            {
                "name": "Credit Card Test",
                "amount": 100.00,
                "method": "Credit Card", 
                "notes": "Debug test - Credit card payment for Deon Aleong"
            }
        ]
        
        all_payments_successful = True
        invoice_results = []
        
        for i, scenario in enumerate(payment_scenarios, 1):
            print(f"\n💳 PAYMENT SCENARIO {i}: {scenario['name']}")
            
            payment_data = {
                "client_id": client_id,
                "amount_paid": scenario['amount'],
                "payment_date": date.today().isoformat(),
                "payment_method": scenario['method'],
                "notes": scenario['notes']
            }
            
            success, response = self.run_test(
                f"Record Payment - {scenario['name']}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                # CRITICAL: Check invoice email status
                invoice_sent = response.get('invoice_sent')
                invoice_message = response.get('invoice_message')
                
                print(f"\n🔍 INVOICE EMAIL STATUS FOR {scenario['name']}:")
                print(f"   Invoice Sent: {invoice_sent}")
                print(f"   Invoice Message: {invoice_message}")
                print(f"   Payment Success: {response.get('success')}")
                print(f"   Client Name: {response.get('client_name')}")
                print(f"   Amount Paid: ${response.get('amount_paid')}")
                print(f"   New Payment Date: {response.get('new_next_payment_date')}")
                
                invoice_results.append({
                    'scenario': scenario['name'],
                    'invoice_sent': invoice_sent,
                    'invoice_message': invoice_message,
                    'success': response.get('success')
                })
                
                if invoice_sent is False:
                    print(f"⚠️  INVOICE EMAIL FAILED for {scenario['name']}")
                    all_payments_successful = False
                elif invoice_sent is True:
                    print(f"✅ INVOICE EMAIL SENT for {scenario['name']}")
                else:
                    print(f"❓ INVOICE STATUS UNCLEAR for {scenario['name']}")
                    all_payments_successful = False
            else:
                print(f"❌ PAYMENT RECORDING FAILED for {scenario['name']}")
                all_payments_successful = False
        
        # Summary of invoice results
        print(f"\n📊 INVOICE EMAIL SUMMARY:")
        successful_invoices = sum(1 for result in invoice_results if result['invoice_sent'] is True)
        failed_invoices = sum(1 for result in invoice_results if result['invoice_sent'] is False)
        unclear_invoices = len(invoice_results) - successful_invoices - failed_invoices
        
        print(f"   Total Payments: {len(invoice_results)}")
        print(f"   Successful Invoices: {successful_invoices}")
        print(f"   Failed Invoices: {failed_invoices}")
        print(f"   Unclear Status: {unclear_invoices}")
        
        if failed_invoices > 0:
            print(f"\n🚨 CRITICAL FINDING: {failed_invoices} invoice emails failed!")
            print("   This matches the user's report of invoice failures.")
        elif successful_invoices == len(invoice_results):
            print(f"\n✅ ALL INVOICES SENT SUCCESSFULLY")
            print("   This contradicts the user's report - need further investigation.")
        
        return all_payments_successful

    def test_client_status_update(self):
        """
        STEP 3: Test Client Status Update
        - Test PUT /api/clients/{client_id} to update Deon Aleong's status
        - Check if the "Client not found" error occurs in backend
        - Verify the client ID exists and is accessible
        """
        print("\n" + "="*80)
        print("🎯 STEP 3: TESTING CLIENT STATUS UPDATE FOR DEON ALEONG")
        print("="*80)
        
        if not self.primary_deon_client:
            print("❌ CRITICAL: No Deon Aleong client available for testing")
            return False
        
        client_id = self.primary_deon_client.get('id')
        current_status = self.primary_deon_client.get('status', 'Active')
        
        print(f"\n🎯 TESTING CLIENT STATUS UPDATE:")
        print(f"   Client ID: {client_id}")
        print(f"   Current Status: {current_status}")
        
        # Test status changes
        status_tests = [
            {
                "name": "Deactivate Client",
                "new_status": "Inactive",
                "description": "Change status from Active to Inactive"
            },
            {
                "name": "Reactivate Client", 
                "new_status": "Active",
                "description": "Change status from Inactive to Active"
            }
        ]
        
        all_status_updates_successful = True
        
        for test in status_tests:
            print(f"\n🔄 {test['name']}: {test['description']}")
            
            update_data = {
                "status": test['new_status']
            }
            
            success, response = self.run_test(
                test['name'],
                "PUT",
                f"clients/{client_id}",
                200,
                update_data
            )
            
            if success:
                updated_status = response.get('status')
                print(f"   ✅ Status updated to: {updated_status}")
                print(f"   Client ID: {response.get('id')}")
                print(f"   Client Name: {response.get('name')}")
                
                if updated_status == test['new_status']:
                    print(f"   ✅ Status change successful!")
                else:
                    print(f"   ❌ Status change failed! Expected: {test['new_status']}, Got: {updated_status}")
                    all_status_updates_successful = False
            else:
                print(f"   ❌ Status update failed - possible 'Client not found' error")
                all_status_updates_successful = False
        
        # Verify client still exists after updates
        success, response = self.run_test(
            "Verify Client Exists After Status Updates",
            "GET",
            f"clients/{client_id}",
            200
        )
        
        if success:
            print(f"\n✅ CLIENT VERIFICATION AFTER STATUS UPDATES:")
            print(f"   Client ID: {response.get('id')}")
            print(f"   Name: {response.get('name')}")
            print(f"   Email: {response.get('email')}")
            print(f"   Final Status: {response.get('status')}")
        else:
            print(f"\n❌ CLIENT NOT FOUND AFTER STATUS UPDATES!")
            print("   This indicates a critical backend issue with client persistence.")
            all_status_updates_successful = False
        
        return all_status_updates_successful

    def test_email_service_during_payment(self):
        """
        STEP 4: Debug Email Service During Payment
        - Monitor email service logs during payment recording
        - Check if Gmail SMTP errors occur during actual user flow
        - Verify if there's a timing or connection issue
        """
        print("\n" + "="*80)
        print("🎯 STEP 4: DEBUGGING EMAIL SERVICE DURING PAYMENT")
        print("="*80)
        
        # First, test email configuration
        success, response = self.run_test(
            "Test Email Configuration",
            "POST",
            "email/test",
            200
        )
        
        if success:
            email_working = response.get('success', False)
            email_message = response.get('message', 'No message')
            
            print(f"\n📧 EMAIL CONFIGURATION STATUS:")
            print(f"   Email Working: {email_working}")
            print(f"   Message: {email_message}")
            
            if not email_working:
                print("🚨 CRITICAL: Email configuration is failing!")
                print("   This explains why invoice emails are failing.")
                return False
        else:
            print("❌ Cannot test email configuration")
            return False
        
        if not self.primary_deon_client:
            print("❌ CRITICAL: No Deon Aleong client available for email testing")
            return False
        
        client_id = self.primary_deon_client.get('id')
        
        # Test direct email sending to Deon Aleong
        print(f"\n📧 TESTING DIRECT EMAIL TO DEON ALEONG:")
        
        email_test_data = {
            "client_id": client_id,
            "template_name": "default",
            "custom_subject": "Debug Test - Direct Email to Deon Aleong",
            "custom_message": "This is a debug test to verify email delivery to Deon Aleong specifically.",
            "custom_amount": 100.00,
            "custom_due_date": "February 15, 2025"
        }
        
        success, response = self.run_test(
            "Send Direct Email to Deon Aleong",
            "POST",
            "email/payment-reminder",
            200,
            email_test_data
        )
        
        if success:
            email_sent = response.get('success', False)
            email_message = response.get('message', 'No message')
            client_email = response.get('client_email', 'Unknown')
            
            print(f"\n📧 DIRECT EMAIL RESULT:")
            print(f"   Email Sent: {email_sent}")
            print(f"   Message: {email_message}")
            print(f"   Target Email: {client_email}")
            
            if not email_sent:
                print("🚨 CRITICAL: Direct email to Deon Aleong failed!")
                print("   This confirms the email service issue.")
                return False
            else:
                print("✅ Direct email to Deon Aleong successful!")
        else:
            print("❌ Direct email test failed")
            return False
        
        # Now test payment with invoice email
        print(f"\n💳 TESTING PAYMENT WITH INVOICE EMAIL:")
        
        payment_data = {
            "client_id": client_id,
            "amount_paid": 125.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Debug Test",
            "notes": "Debug test - Payment with invoice email for Deon Aleong"
        }
        
        success, response = self.run_test(
            "Payment with Invoice Email - Deon Aleong",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            invoice_sent = response.get('invoice_sent')
            invoice_message = response.get('invoice_message')
            
            print(f"\n📧 PAYMENT INVOICE EMAIL RESULT:")
            print(f"   Invoice Sent: {invoice_sent}")
            print(f"   Invoice Message: {invoice_message}")
            
            if invoice_sent is False:
                print("🚨 CRITICAL: Invoice email failed during payment!")
                print("   This confirms the user's experience.")
                
                # Check if it's a timing issue by retrying
                print("\n🔄 RETRYING INVOICE EMAIL (Timing Test)...")
                
                retry_success, retry_response = self.run_test(
                    "Retry Payment with Invoice - Timing Test",
                    "POST",
                    "payments/record",
                    200,
                    {**payment_data, "amount_paid": 130.00, "notes": "Retry test for timing issue"}
                )
                
                if retry_success:
                    retry_invoice_sent = retry_response.get('invoice_sent')
                    print(f"   Retry Invoice Sent: {retry_invoice_sent}")
                    
                    if retry_invoice_sent is True:
                        print("⚠️  TIMING ISSUE DETECTED: Email works on retry!")
                    else:
                        print("🚨 PERSISTENT EMAIL FAILURE: Not a timing issue.")
                
                return False
            else:
                print("✅ Invoice email sent successfully during payment!")
        else:
            print("❌ Payment with invoice test failed")
            return False
        
        return True

    def test_multiple_deon_clients_confusion(self):
        """
        STEP 5: Test Multiple Deon Aleong Clients
        - Check if there are multiple "Deon Aleong" clients causing ID confusion
        - Test payment recording with different Deon Aleong client instances
        - Verify client ID consistency
        """
        print("\n" + "="*80)
        print("🎯 STEP 5: TESTING MULTIPLE DEON CLIENTS CONFUSION")
        print("="*80)
        
        if len(self.deon_clients) <= 1:
            print("✅ NO MULTIPLE DEON CLIENTS DETECTED")
            print("   Only one Deon Aleong client found - no ID confusion possible.")
            return True
        
        print(f"⚠️  MULTIPLE DEON CLIENTS DETECTED: {len(self.deon_clients)}")
        print("   This could cause ID confusion in the frontend!")
        
        # Test each Deon client individually
        for i, client in enumerate(self.deon_clients):
            print(f"\n🎯 TESTING DEON CLIENT #{i+1}:")
            print(f"   ID: {client.get('id')}")
            print(f"   Name: {client.get('name')}")
            print(f"   Email: {client.get('email')}")
            
            # Test payment recording with this specific client
            payment_data = {
                "client_id": client.get('id'),
                "amount_paid": 50.00 + (i * 10),  # Different amounts to distinguish
                "payment_date": date.today().isoformat(),
                "payment_method": "Multiple Client Test",
                "notes": f"Testing client #{i+1} - {client.get('name')}"
            }
            
            success, response = self.run_test(
                f"Payment Test - Deon Client #{i+1}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                returned_client_name = response.get('client_name')
                invoice_sent = response.get('invoice_sent')
                
                print(f"   Payment Success: {response.get('success')}")
                print(f"   Returned Client Name: {returned_client_name}")
                print(f"   Invoice Sent: {invoice_sent}")
                
                # Check if the returned client name matches the expected client
                if returned_client_name != client.get('name'):
                    print(f"🚨 CLIENT ID CONFUSION DETECTED!")
                    print(f"   Expected: {client.get('name')}")
                    print(f"   Got: {returned_client_name}")
                    return False
            else:
                print(f"❌ Payment failed for Deon Client #{i+1}")
                return False
        
        print(f"\n📊 MULTIPLE DEON CLIENTS SUMMARY:")
        print(f"   Total Deon Clients: {len(self.deon_clients)}")
        print(f"   All clients tested successfully")
        print(f"   No ID confusion detected in backend")
        print(f"   ⚠️  Frontend may still have confusion - check client selection logic")
        
        return True

    def run_comprehensive_debug(self):
        """Run the complete debugging suite"""
        print("🚨 CRITICAL DEBUGGING - FRONTEND vs BACKEND DISCREPANCY")
        print("="*80)
        print("Debugging invoice email failures reported by user vs backend success")
        print("Focus: Real Deon Aleong client testing")
        print("="*80)
        
        # Step 1: Find Deon Aleong clients
        if not self.find_deon_aleong_clients():
            print("❌ CRITICAL: Cannot find or create Deon Aleong client")
            return False
        
        # Step 2: Test actual payment recording
        payment_success = self.test_actual_payment_recording()
        
        # Step 3: Test client status updates
        status_success = self.test_client_status_update()
        
        # Step 4: Debug email service during payment
        email_success = self.test_email_service_during_payment()
        
        # Step 5: Test multiple client confusion
        confusion_success = self.test_multiple_deon_clients_confusion()
        
        # Final summary
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE DEBUG SUMMARY")
        print("="*80)
        
        print(f"📊 TESTS RUN: {self.tests_run}")
        print(f"✅ TESTS PASSED: {self.tests_passed}")
        print(f"❌ TESTS FAILED: {self.tests_run - self.tests_passed}")
        print(f"📈 SUCCESS RATE: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        print(f"\n🔍 DEBUG RESULTS:")
        print(f"   Step 1 - Find Deon Clients: {'✅ PASSED' if len(self.deon_clients) > 0 else '❌ FAILED'}")
        print(f"   Step 2 - Payment Recording: {'✅ PASSED' if payment_success else '❌ FAILED'}")
        print(f"   Step 3 - Client Status Update: {'✅ PASSED' if status_success else '❌ FAILED'}")
        print(f"   Step 4 - Email Service Debug: {'✅ PASSED' if email_success else '❌ FAILED'}")
        print(f"   Step 5 - Multiple Client Test: {'✅ PASSED' if confusion_success else '❌ FAILED'}")
        
        if self.primary_deon_client:
            print(f"\n🎯 PRIMARY DEON CLIENT TESTED:")
            print(f"   ID: {self.primary_deon_client.get('id')}")
            print(f"   Name: {self.primary_deon_client.get('name')}")
            print(f"   Email: {self.primary_deon_client.get('email')}")
        
        # Root cause analysis
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        if not email_success:
            print("🚨 CRITICAL FINDING: Email service is failing during payment recording")
            print("   This explains the discrepancy between backend 'success' and actual email delivery")
            print("   Backend returns success=true but emails are not being sent")
        elif not payment_success:
            print("🚨 CRITICAL FINDING: Payment recording is failing for Deon Aleong client")
            print("   This indicates a client-specific issue or data corruption")
        elif len(self.deon_clients) > 1:
            print("⚠️  POTENTIAL ISSUE: Multiple Deon Aleong clients detected")
            print("   Frontend may be using wrong client ID causing confusion")
        else:
            print("✅ NO CRITICAL ISSUES DETECTED in backend")
            print("   The issue may be in frontend implementation or user interaction flow")
        
        overall_success = payment_success and status_success and email_success and confusion_success
        
        if overall_success:
            print(f"\n🎉 DEBUGGING COMPLETE: All systems working correctly")
        else:
            print(f"\n🚨 DEBUGGING COMPLETE: Critical issues identified")
        
        return overall_success

def main():
    """Main execution function"""
    print("🚨 DEON ALEONG DEBUG TEST - INVOICE EMAIL FAILURE INVESTIGATION")
    print("="*80)
    
    tester = DeonAleongDebugTester()
    
    try:
        success = tester.run_comprehensive_debug()
        
        if success:
            print(f"\n✅ ALL DEBUG TESTS PASSED")
            sys.exit(0)
        else:
            print(f"\n❌ CRITICAL ISSUES DETECTED")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Debug testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Debug testing failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()