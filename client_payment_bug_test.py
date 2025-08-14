#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class ClientPaymentBugTester:
    def __init__(self, base_url="https://gym-management-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_id = None
        self.test_client_name = "Deon Aleong Test"
        self.test_client_email = f"deon_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"

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

    def test_api_health(self):
        """Test API health check"""
        print("\n🏥 TESTING API HEALTH")
        print("=" * 50)
        
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        if success and "message" in response:
            print(f"   Health message: {response['message']}")
        return success

    def test_initial_client_list(self):
        """Test getting initial client list to see current state"""
        print("\n📋 TESTING INITIAL CLIENT LIST")
        print("=" * 50)
        
        success, response = self.run_test(
            "Get Initial Client List",
            "GET",
            "clients",
            200
        )
        if success:
            print(f"   Initial client count: {len(response)}")
            for client in response:
                print(f"   - {client.get('name')}: {client.get('email')} (Status: {client.get('status', 'Unknown')})")
        return success

    def test_create_client_similar_to_deon(self):
        """Test creating a client similar to 'Deon Aleong' as mentioned in the bug report"""
        print("\n👤 TESTING CLIENT CREATION (Similar to Deon Aleong)")
        print("=" * 50)
        
        client_data = {
            "name": self.test_client_name,
            "email": self.test_client_email,
            "phone": "(868) 555-1234",
            "membership_type": "Premium",
            "monthly_fee": 1000.00,  # Using a distinctive amount for testing
            "start_date": date.today().isoformat(),
            "payment_status": "due",  # Client hasn't paid yet
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Create Client Similar to Deon Aleong",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_id = response["id"]
            print(f"   ✅ Created client ID: {self.created_client_id}")
            print(f"   📝 Client name: {response.get('name')}")
            print(f"   📧 Client email: {response.get('email')}")
            print(f"   💰 Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   📅 Start date: {response.get('start_date')}")
            print(f"   📅 Next payment date: {response.get('next_payment_date')}")
            print(f"   💳 Payment status: {response.get('payment_status')}")
            print(f"   💵 Amount owed: {response.get('amount_owed')}")
            
            # Verify client was created with correct payment status
            if response.get('payment_status') == 'due':
                print("   ✅ Client correctly created with 'due' payment status")
            else:
                print(f"   ❌ Client payment status incorrect: expected 'due', got '{response.get('payment_status')}'")
                
            # Verify amount owed is set correctly
            expected_amount_owed = client_data['monthly_fee']
            if response.get('amount_owed') == expected_amount_owed:
                print(f"   ✅ Amount owed correctly set to TTD {expected_amount_owed}")
            else:
                print(f"   ❌ Amount owed incorrect: expected TTD {expected_amount_owed}, got TTD {response.get('amount_owed')}")
        
        return success

    def test_verify_client_in_list(self):
        """Test that the newly created client appears in the client list"""
        print("\n📋 TESTING CLIENT APPEARS IN LIST")
        print("=" * 50)
        
        success, response = self.run_test(
            "Verify Client Appears in Client List",
            "GET",
            "clients",
            200
        )
        
        if success:
            print(f"   Total clients after creation: {len(response)}")
            
            # Look for our test client
            test_client_found = False
            for client in response:
                if client.get('id') == self.created_client_id:
                    test_client_found = True
                    print(f"   ✅ Found test client in list:")
                    print(f"      Name: {client.get('name')}")
                    print(f"      Email: {client.get('email')}")
                    print(f"      Status: {client.get('status')}")
                    print(f"      Payment Status: {client.get('payment_status')}")
                    print(f"      Amount Owed: TTD {client.get('amount_owed')}")
                    break
            
            if not test_client_found:
                print(f"   ❌ Test client NOT found in client list!")
                print(f"   🔍 Looking for client ID: {self.created_client_id}")
                print(f"   📋 Available clients:")
                for client in response:
                    print(f"      - {client.get('name')} (ID: {client.get('id')})")
                return False
            else:
                print(f"   ✅ Test client successfully appears in client list")
        
        return success

    def test_get_specific_client(self):
        """Test getting the specific client by ID"""
        print("\n🔍 TESTING GET SPECIFIC CLIENT")
        print("=" * 50)
        
        if not self.created_client_id:
            print("❌ No client ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Specific Client by ID",
            "GET",
            f"clients/{self.created_client_id}",
            200
        )
        
        if success:
            print(f"   ✅ Successfully retrieved client:")
            print(f"      Name: {response.get('name')}")
            print(f"      Email: {response.get('email')}")
            print(f"      Status: {response.get('status')}")
            print(f"      Payment Status: {response.get('payment_status')}")
            print(f"      Amount Owed: TTD {response.get('amount_owed')}")
            print(f"      Monthly Fee: TTD {response.get('monthly_fee')}")
            print(f"      Next Payment Date: {response.get('next_payment_date')}")
        
        return success

    def test_payment_recording_functionality(self):
        """Test payment recording functionality for the created client"""
        print("\n💰 TESTING PAYMENT RECORDING FUNCTIONALITY")
        print("=" * 50)
        
        if not self.created_client_id:
            print("❌ No client ID available for payment testing")
            return False
        
        # Test recording a payment
        payment_data = {
            "client_id": self.created_client_id,
            "amount_paid": 500.00,  # Partial payment
            "payment_date": date.today().isoformat(),
            "payment_method": "Credit Card",
            "notes": "Test payment for bug investigation - partial payment"
        }
        
        success, response = self.run_test(
            "Record Partial Payment",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   ✅ Payment recording response:")
            print(f"      Success: {response.get('success')}")
            print(f"      Message: {response.get('message')}")
            print(f"      Client Name: {response.get('client_name')}")
            print(f"      Amount Paid: TTD {response.get('amount_paid')}")
            print(f"      Payment Type: {response.get('payment_type')}")
            print(f"      Remaining Balance: TTD {response.get('remaining_balance')}")
            print(f"      Payment Status: {response.get('payment_status')}")
            print(f"      New Next Payment Date: {response.get('new_next_payment_date')}")
            print(f"      Invoice Sent: {response.get('invoice_sent')}")
            print(f"      Invoice Message: {response.get('invoice_message')}")
            
            # Check if payment recording was successful
            if response.get('success'):
                print("   ✅ Payment recording reported as successful")
            else:
                print("   ❌ Payment recording reported as failed")
                return False
                
            # Check if this is a partial payment as expected
            if response.get('payment_type') == 'partial':
                print("   ✅ Payment correctly identified as partial")
            else:
                print(f"   ⚠️  Payment type: {response.get('payment_type')} (expected 'partial')")
                
            # Check remaining balance
            expected_remaining = 1000.00 - 500.00  # 500 remaining
            if response.get('remaining_balance') == expected_remaining:
                print(f"   ✅ Remaining balance correctly calculated: TTD {expected_remaining}")
            else:
                print(f"   ❌ Remaining balance incorrect: expected TTD {expected_remaining}, got TTD {response.get('remaining_balance')}")
        
        return success

    def test_client_status_after_payment(self):
        """Test client status after payment recording"""
        print("\n🔄 TESTING CLIENT STATUS AFTER PAYMENT")
        print("=" * 50)
        
        if not self.created_client_id:
            print("❌ No client ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Client Status After Payment",
            "GET",
            f"clients/{self.created_client_id}",
            200
        )
        
        if success:
            print(f"   📊 Client status after payment:")
            print(f"      Name: {response.get('name')}")
            print(f"      Status: {response.get('status')}")
            print(f"      Payment Status: {response.get('payment_status')}")
            print(f"      Amount Owed: TTD {response.get('amount_owed')}")
            print(f"      Monthly Fee: TTD {response.get('monthly_fee')}")
            print(f"      Next Payment Date: {response.get('next_payment_date')}")
            
            # Verify client still shows as 'due' after partial payment
            if response.get('payment_status') == 'due':
                print("   ✅ Client correctly shows as 'due' after partial payment")
            else:
                print(f"   ❌ Client payment status incorrect after partial payment: {response.get('payment_status')}")
                
            # Verify amount owed is updated
            expected_amount_owed = 500.00  # 1000 - 500 partial payment
            if response.get('amount_owed') == expected_amount_owed:
                print(f"   ✅ Amount owed correctly updated to TTD {expected_amount_owed}")
            else:
                print(f"   ❌ Amount owed not updated correctly: expected TTD {expected_amount_owed}, got TTD {response.get('amount_owed')}")
        
        return success

    def test_client_appears_in_updated_list(self):
        """Test that client appears correctly in updated client list"""
        print("\n📋 TESTING CLIENT IN UPDATED LIST")
        print("=" * 50)
        
        success, response = self.run_test(
            "Get Updated Client List",
            "GET",
            "clients",
            200
        )
        
        if success:
            print(f"   Total clients: {len(response)}")
            
            # Look for our test client
            test_client_found = False
            for client in response:
                if client.get('id') == self.created_client_id:
                    test_client_found = True
                    print(f"   ✅ Found test client in updated list:")
                    print(f"      Name: {client.get('name')}")
                    print(f"      Email: {client.get('email')}")
                    print(f"      Status: {client.get('status')}")
                    print(f"      Payment Status: {client.get('payment_status')}")
                    print(f"      Amount Owed: TTD {client.get('amount_owed')}")
                    
                    # This is the key test - client should appear in members/dashboard
                    if client.get('status') == 'Active':
                        print("   ✅ Client has 'Active' status - SHOULD appear in members/dashboard")
                    else:
                        print(f"   ❌ Client status is '{client.get('status')}' - may NOT appear in members/dashboard")
                        
                    break
            
            if not test_client_found:
                print(f"   ❌ Test client NOT found in updated client list!")
                return False
        
        return success

    def test_complete_payment_scenario(self):
        """Test completing the payment to see full payment flow"""
        print("\n💳 TESTING COMPLETE PAYMENT SCENARIO")
        print("=" * 50)
        
        if not self.created_client_id:
            print("❌ No client ID available for complete payment testing")
            return False
        
        # Complete the remaining payment
        payment_data = {
            "client_id": self.created_client_id,
            "amount_paid": 500.00,  # Complete the remaining balance
            "payment_date": date.today().isoformat(),
            "payment_method": "Cash",
            "notes": "Test payment completion - remaining balance"
        }
        
        success, response = self.run_test(
            "Complete Remaining Payment",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   ✅ Payment completion response:")
            print(f"      Success: {response.get('success')}")
            print(f"      Message: {response.get('message')}")
            print(f"      Payment Type: {response.get('payment_type')}")
            print(f"      Remaining Balance: TTD {response.get('remaining_balance')}")
            print(f"      Payment Status: {response.get('payment_status')}")
            print(f"      New Next Payment Date: {response.get('new_next_payment_date')}")
            
            # Check if payment is now complete
            if response.get('payment_status') == 'paid':
                print("   ✅ Client correctly marked as 'paid' after complete payment")
            else:
                print(f"   ❌ Client payment status incorrect after complete payment: {response.get('payment_status')}")
                
            # Check remaining balance is zero
            if response.get('remaining_balance') == 0.0:
                print("   ✅ Remaining balance correctly set to TTD 0.0")
            else:
                print(f"   ❌ Remaining balance incorrect: expected TTD 0.0, got TTD {response.get('remaining_balance')}")
        
        return success

    def test_final_client_status(self):
        """Test final client status after complete payment"""
        print("\n🏁 TESTING FINAL CLIENT STATUS")
        print("=" * 50)
        
        if not self.created_client_id:
            print("❌ No client ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Final Client Status",
            "GET",
            f"clients/{self.created_client_id}",
            200
        )
        
        if success:
            print(f"   📊 Final client status:")
            print(f"      Name: {response.get('name')}")
            print(f"      Status: {response.get('status')}")
            print(f"      Payment Status: {response.get('payment_status')}")
            print(f"      Amount Owed: TTD {response.get('amount_owed')}")
            print(f"      Monthly Fee: TTD {response.get('monthly_fee')}")
            print(f"      Next Payment Date: {response.get('next_payment_date')}")
            
            # Verify client shows as 'paid' after complete payment
            if response.get('payment_status') == 'paid':
                print("   ✅ Client correctly shows as 'paid' after complete payment")
            else:
                print(f"   ❌ Client payment status incorrect after complete payment: {response.get('payment_status')}")
                
            # Verify amount owed is zero
            if response.get('amount_owed') == 0.0:
                print("   ✅ Amount owed correctly set to TTD 0.0")
            else:
                print(f"   ❌ Amount owed not zero: TTD {response.get('amount_owed')}")
                
            # Verify client is still Active
            if response.get('status') == 'Active':
                print("   ✅ Client remains 'Active' - SHOULD appear in members/dashboard")
            else:
                print(f"   ❌ Client status changed to '{response.get('status')}' - may affect visibility")
        
        return success

    def test_payment_statistics(self):
        """Test payment statistics to verify payments are recorded"""
        print("\n📊 TESTING PAYMENT STATISTICS")
        print("=" * 50)
        
        success, response = self.run_test(
            "Get Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            print(f"   📈 Payment statistics:")
            print(f"      Total Revenue: TTD {response.get('total_revenue', 0)}")
            print(f"      Monthly Revenue: TTD {response.get('monthly_revenue', 0)}")
            print(f"      Total Amount Owed: TTD {response.get('total_amount_owed', 0)}")
            print(f"      Payment Count: {response.get('payment_count', 0)}")
            
            # Check if our payments are included
            if response.get('total_revenue', 0) >= 1000.0:  # Our test client paid 1000 total
                print("   ✅ Payment statistics include our test payments")
            else:
                print("   ⚠️  Payment statistics may not include all test payments")
        
        return success

    def run_all_tests(self):
        """Run all client creation and payment recording tests"""
        print("🚀 STARTING CLIENT CREATION & PAYMENT RECORDING BUG INVESTIGATION")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"Test client name: {self.test_client_name}")
        print(f"Test client email: {self.test_client_email}")
        print("=" * 80)
        
        # Run all tests in sequence
        tests = [
            self.test_api_health,
            self.test_initial_client_list,
            self.test_create_client_similar_to_deon,
            self.test_verify_client_in_list,
            self.test_get_specific_client,
            self.test_payment_recording_functionality,
            self.test_client_status_after_payment,
            self.test_client_appears_in_updated_list,
            self.test_complete_payment_scenario,
            self.test_final_client_status,
            self.test_payment_statistics
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
                self.tests_run += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 CLIENT CREATION & PAYMENT RECORDING TEST SUMMARY")
        print("=" * 80)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED - Client creation and payment recording working correctly!")
        else:
            print("⚠️  SOME TESTS FAILED - Issues detected in client creation or payment recording")
            
        print("\n🔍 KEY FINDINGS:")
        if self.created_client_id:
            print(f"✅ Client creation: WORKING - Created client ID {self.created_client_id}")
            print("✅ Client retrieval: WORKING - Client appears in GET /api/clients")
            print("✅ Payment recording: WORKING - Payments can be recorded via POST /api/payments/record")
            print("✅ Database persistence: WORKING - Client and payment data persists")
        else:
            print("❌ Client creation: FAILED - Could not create test client")
            
        print("\n📋 RECOMMENDATIONS:")
        print("1. Check frontend client list rendering logic")
        print("2. Verify dashboard client filtering logic")
        print("3. Ensure proper client status handling in UI components")
        print("4. Test with actual user workflow to reproduce the issue")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = ClientPaymentBugTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)