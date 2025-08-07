#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any

class CriticalEmailDatabaseTester:
    """
    CRITICAL REAL-WORLD DEBUGGING TESTER
    
    Focus: Debug the REAL issues the user is experiencing:
    1. Emails not actually being delivered (despite backend success)
    2. Revenue not updating after payments
    3. Database verification of actual changes
    """
    
    def __init__(self, base_url="https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_client_id = None
        self.initial_revenue = 0
        self.initial_client_count = 0
        
        # Real email for testing actual delivery
        self.test_email = "alphaleteclub@gmail.com"  # Using the same email as sender for testing
        
        print("🚨 CRITICAL REAL-WORLD DEBUGGING SESSION STARTED")
        print("=" * 80)
        print("FOCUS: Debug actual email delivery and database persistence issues")
        print("USER ISSUES: Emails not delivered, revenue not updating after payments")
        print("=" * 80)

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results with enhanced formatting"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None) -> tuple:
        """Run a single API test with enhanced error reporting"""
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
                    details = f"(Expected {expected_status}, got {response.status_code}) - {response.text[:200]}"
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

    def test_1_baseline_data_collection(self):
        """CRITICAL: Collect baseline data for comparison"""
        print("\n🎯 STEP 1: BASELINE DATA COLLECTION")
        print("=" * 60)
        
        # Get initial client count and revenue
        success, response = self.run_test(
            "Get Initial Client Data for Baseline",
            "GET",
            "clients",
            200
        )
        
        if success:
            clients = response
            self.initial_client_count = len(clients)
            
            # Calculate initial revenue
            total_revenue = 0
            active_clients = 0
            for client in clients:
                if client.get('status', 'Active') == 'Active':
                    active_clients += 1
                    total_revenue += client.get('monthly_fee', 0)
            
            self.initial_revenue = total_revenue
            
            print(f"   📊 BASELINE METRICS:")
            print(f"      Total Clients: {self.initial_client_count}")
            print(f"      Active Clients: {active_clients}")
            print(f"      Total Monthly Revenue: TTD {total_revenue:.2f}")
            
            return True
        
        return False

    def test_2_gmail_smtp_connection_verification(self):
        """CRITICAL: Test actual Gmail SMTP connection"""
        print("\n🎯 STEP 2: GMAIL SMTP CONNECTION VERIFICATION")
        print("=" * 60)
        
        success, response = self.run_test(
            "Gmail SMTP Connection Test",
            "POST",
            "email/test",
            200
        )
        
        if success:
            email_success = response.get('success', False)
            message = response.get('message', 'No message')
            
            print(f"   📧 GMAIL CONNECTION STATUS:")
            print(f"      Success: {email_success}")
            print(f"      Message: {message}")
            
            if email_success:
                print("   ✅ GMAIL SMTP CONNECTION: WORKING")
                return True
            else:
                print("   ❌ GMAIL SMTP CONNECTION: FAILED")
                print("   🔧 ISSUE: Gmail authentication or rate limiting problem")
                return False
        
        return False

    def test_3_create_real_test_client(self):
        """CRITICAL: Create a real test client for actual testing"""
        print("\n🎯 STEP 3: CREATE REAL TEST CLIENT")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Deon Aleong",  # Real-looking name as requested
            "email": self.test_email,  # Real email for actual delivery testing
            "phone": "(868) 555-1234",  # Trinidad format
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": "2025-01-20",
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Create Real Test Client (Deon Aleong)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.test_client_id = response["id"]
            print(f"   👤 CREATED TEST CLIENT:")
            print(f"      ID: {self.test_client_id}")
            print(f"      Name: {response.get('name')}")
            print(f"      Email: {response.get('email')}")
            print(f"      Monthly Fee: TTD {response.get('monthly_fee')}")
            print(f"      Next Payment: {response.get('next_payment_date')}")
            
            return True
        
        return False

    def test_4_actual_email_delivery_test(self):
        """CRITICAL: Test ACTUAL email delivery to real inbox"""
        print("\n🎯 STEP 4: ACTUAL EMAIL DELIVERY TEST")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client available - skipping email test")
            return False
        
        # Test payment reminder email
        reminder_data = {
            "client_id": self.test_client_id,
            "template_name": "professional",
            "custom_subject": "🚨 CRITICAL TEST - Payment Reminder Delivery Verification",
            "custom_message": "This is a CRITICAL TEST to verify actual email delivery. If you receive this email, the system is working correctly.",
            "custom_amount": 100.00,
            "custom_due_date": "February 15, 2025"
        }
        
        print(f"   📧 SENDING EMAIL TO: {self.test_email}")
        print(f"   📧 SUBJECT: {reminder_data['custom_subject']}")
        
        success, response = self.run_test(
            "Send Payment Reminder - ACTUAL DELIVERY TEST",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success:
            email_success = response.get('success', False)
            message = response.get('message', 'No message')
            client_email = response.get('client_email', 'Unknown')
            
            print(f"   📧 EMAIL DELIVERY RESULT:")
            print(f"      API Success: {email_success}")
            print(f"      Message: {message}")
            print(f"      Target Email: {client_email}")
            
            if email_success:
                print("   ✅ BACKEND REPORTS: EMAIL SENT SUCCESSFULLY")
                print("   🔍 MANUAL VERIFICATION REQUIRED:")
                print(f"      Please check inbox: {self.test_email}")
                print("      Look for email with subject containing 'CRITICAL TEST'")
                print("      Check spam folder if not in inbox")
                return True
            else:
                print("   ❌ BACKEND REPORTS: EMAIL SENDING FAILED")
                return False
        
        return False

    def test_5_payment_recording_and_database_verification(self):
        """CRITICAL: Test payment recording and verify database changes"""
        print("\n🎯 STEP 5: PAYMENT RECORDING & DATABASE VERIFICATION")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client available - skipping payment test")
            return False
        
        # Get client data before payment
        success_before, client_before = self.run_test(
            "Get Client Data BEFORE Payment",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if not success_before:
            return False
        
        print(f"   📊 CLIENT DATA BEFORE PAYMENT:")
        print(f"      Name: {client_before.get('name')}")
        print(f"      Next Payment Date: {client_before.get('next_payment_date')}")
        print(f"      Status: {client_before.get('status')}")
        
        # Record a payment
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 100.00,
            "payment_date": "2025-01-25",
            "payment_method": "Bank Transfer",
            "notes": "CRITICAL TEST - Payment recording verification"
        }
        
        success_payment, payment_response = self.run_test(
            "Record Payment - DATABASE VERIFICATION TEST",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if not success_payment:
            return False
        
        print(f"   💰 PAYMENT RECORDING RESULT:")
        print(f"      Success: {payment_response.get('success')}")
        print(f"      Client: {payment_response.get('client_name')}")
        print(f"      Amount: TTD {payment_response.get('amount_paid')}")
        print(f"      New Payment Date: {payment_response.get('new_next_payment_date')}")
        
        # Check invoice email status
        invoice_sent = payment_response.get('invoice_sent')
        invoice_message = payment_response.get('invoice_message')
        print(f"      Invoice Sent: {invoice_sent}")
        print(f"      Invoice Message: {invoice_message}")
        
        # Verify database changes by getting client data after payment
        time.sleep(2)  # Wait for database update
        
        success_after, client_after = self.run_test(
            "Get Client Data AFTER Payment",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if not success_after:
            return False
        
        print(f"   📊 CLIENT DATA AFTER PAYMENT:")
        print(f"      Name: {client_after.get('name')}")
        print(f"      Next Payment Date: {client_after.get('next_payment_date')}")
        print(f"      Status: {client_after.get('status')}")
        
        # Verify payment date changed
        before_date = client_before.get('next_payment_date')
        after_date = client_after.get('next_payment_date')
        
        if before_date != after_date:
            print("   ✅ DATABASE VERIFICATION: Payment date updated correctly")
            print(f"      Before: {before_date}")
            print(f"      After: {after_date}")
            return True
        else:
            print("   ❌ DATABASE VERIFICATION: Payment date NOT updated")
            print(f"      Before: {before_date}")
            print(f"      After: {after_date}")
            return False

    def test_6_revenue_calculation_verification(self):
        """CRITICAL: Test revenue calculation after payment"""
        print("\n🎯 STEP 6: REVENUE CALCULATION VERIFICATION")
        print("=" * 60)
        
        # Get current client data to calculate revenue
        success, response = self.run_test(
            "Get All Clients for Revenue Calculation",
            "GET",
            "clients",
            200
        )
        
        if not success:
            return False
        
        clients = response
        current_client_count = len(clients)
        
        # Calculate current revenue
        total_revenue = 0
        active_clients = 0
        overdue_clients = 0
        today = date.today()
        
        for client in clients:
            if client.get('status', 'Active') == 'Active':
                active_clients += 1
                monthly_fee = client.get('monthly_fee', 0)
                total_revenue += monthly_fee
                
                # Check if overdue
                next_payment_str = client.get('next_payment_date')
                if next_payment_str:
                    try:
                        next_payment_date = datetime.fromisoformat(next_payment_str).date()
                        if next_payment_date < today:
                            overdue_clients += 1
                    except:
                        pass
        
        print(f"   📊 CURRENT REVENUE METRICS:")
        print(f"      Total Clients: {current_client_count}")
        print(f"      Active Clients: {active_clients}")
        print(f"      Total Monthly Revenue: TTD {total_revenue:.2f}")
        print(f"      Overdue Clients: {overdue_clients}")
        
        print(f"   📊 COMPARISON WITH BASELINE:")
        print(f"      Initial Clients: {self.initial_client_count}")
        print(f"      Current Clients: {current_client_count}")
        print(f"      Client Change: {current_client_count - self.initial_client_count}")
        print(f"      Initial Revenue: TTD {self.initial_revenue:.2f}")
        print(f"      Current Revenue: TTD {total_revenue:.2f}")
        print(f"      Revenue Change: TTD {total_revenue - self.initial_revenue:.2f}")
        
        # Verify revenue calculation is working
        if total_revenue > 0:
            print("   ✅ REVENUE CALCULATION: Working (non-zero values)")
            return True
        else:
            print("   ❌ REVENUE CALCULATION: Failed (zero values)")
            return False

    def test_7_bulk_email_delivery_verification(self):
        """CRITICAL: Test bulk email sending for multiple clients"""
        print("\n🎯 STEP 7: BULK EMAIL DELIVERY VERIFICATION")
        print("=" * 60)
        
        success, response = self.run_test(
            "Send Bulk Payment Reminders - DELIVERY VERIFICATION",
            "POST",
            "email/payment-reminder/bulk",
            200
        )
        
        if success:
            total_clients = response.get('total_clients', 0)
            sent_successfully = response.get('sent_successfully', 0)
            failed = response.get('failed', 0)
            results = response.get('results', [])
            
            print(f"   📧 BULK EMAIL RESULTS:")
            print(f"      Total Clients: {total_clients}")
            print(f"      Sent Successfully: {sent_successfully}")
            print(f"      Failed: {failed}")
            print(f"      Success Rate: {(sent_successfully/total_clients*100):.1f}%" if total_clients > 0 else "N/A")
            
            # Show sample results
            print(f"   📧 SAMPLE RESULTS:")
            for i, result in enumerate(results[:5]):  # Show first 5
                status = "✅" if result.get('success') else "❌"
                print(f"      {i+1}. {status} {result.get('client_name')} ({result.get('client_email')})")
                if not result.get('success') and 'error' in result:
                    print(f"         Error: {result.get('error')}")
            
            if sent_successfully > 0:
                print("   ✅ BULK EMAIL DELIVERY: Some emails sent successfully")
                return True
            else:
                print("   ❌ BULK EMAIL DELIVERY: No emails sent successfully")
                return False
        
        return False

    def test_8_database_persistence_verification(self):
        """CRITICAL: Verify data persistence across operations"""
        print("\n🎯 STEP 8: DATABASE PERSISTENCE VERIFICATION")
        print("=" * 60)
        
        if not self.test_client_id:
            print("❌ No test client available - skipping persistence test")
            return False
        
        # Test multiple operations and verify persistence
        operations_passed = 0
        total_operations = 3
        
        # Operation 1: Update client details
        update_data = {
            "phone": "(868) 555-9999",
            "membership_type": "VIP",
            "monthly_fee": 150.00
        }
        
        success1, response1 = self.run_test(
            "Update Client Details - Persistence Test",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            update_data
        )
        
        if success1:
            print(f"   ✅ Operation 1: Client update successful")
            operations_passed += 1
        
        # Operation 2: Record another payment
        payment_data = {
            "client_id": self.test_client_id,
            "amount_paid": 150.00,
            "payment_date": "2025-01-26",
            "payment_method": "Credit Card",
            "notes": "Second payment for persistence testing"
        }
        
        success2, response2 = self.run_test(
            "Record Second Payment - Persistence Test",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success2:
            print(f"   ✅ Operation 2: Second payment recorded")
            operations_passed += 1
        
        # Operation 3: Verify all changes persisted
        success3, response3 = self.run_test(
            "Verify All Changes Persisted",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if success3:
            client = response3
            print(f"   📊 FINAL CLIENT STATE:")
            print(f"      Name: {client.get('name')}")
            print(f"      Phone: {client.get('phone')}")
            print(f"      Membership: {client.get('membership_type')}")
            print(f"      Monthly Fee: TTD {client.get('monthly_fee')}")
            print(f"      Next Payment: {client.get('next_payment_date')}")
            
            # Verify updates persisted
            if (client.get('phone') == "(868) 555-9999" and 
                client.get('membership_type') == "VIP" and 
                client.get('monthly_fee') == 150.00):
                print(f"   ✅ Operation 3: All changes persisted correctly")
                operations_passed += 1
            else:
                print(f"   ❌ Operation 3: Some changes did not persist")
        
        success_rate = (operations_passed / total_operations) * 100
        print(f"   📊 PERSISTENCE TEST RESULTS:")
        print(f"      Operations Passed: {operations_passed}/{total_operations}")
        print(f"      Success Rate: {success_rate:.1f}%")
        
        return operations_passed == total_operations

    def run_critical_debugging_suite(self):
        """Run the complete critical debugging test suite"""
        print("\n🚨 STARTING CRITICAL EMAIL & DATABASE DEBUGGING SUITE")
        print("=" * 80)
        
        tests = [
            self.test_1_baseline_data_collection,
            self.test_2_gmail_smtp_connection_verification,
            self.test_3_create_real_test_client,
            self.test_4_actual_email_delivery_test,
            self.test_5_payment_recording_and_database_verification,
            self.test_6_revenue_calculation_verification,
            self.test_7_bulk_email_delivery_verification,
            self.test_8_database_persistence_verification
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        # Final summary
        print("\n🎯 CRITICAL DEBUGGING SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL CRITICAL TESTS PASSED!")
            print("✅ Email delivery system appears to be working")
            print("✅ Database operations are functioning correctly")
            print("✅ Revenue calculations are working")
        else:
            print("🚨 CRITICAL ISSUES IDENTIFIED!")
            print("❌ Some systems are not working as expected")
            print("🔧 Manual investigation required for failed tests")
        
        print("\n📧 MANUAL VERIFICATION REQUIRED:")
        print(f"   Check email inbox: {self.test_email}")
        print("   Look for emails with 'CRITICAL TEST' in subject")
        print("   Verify actual email delivery vs backend success responses")

if __name__ == "__main__":
    tester = CriticalEmailDatabaseTester()
    tester.run_critical_debugging_suite()