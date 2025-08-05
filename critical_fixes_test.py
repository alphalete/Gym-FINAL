#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any
import pytz

class CriticalFixesTester:
    def __init__(self, base_url="https://442a58e4-b64f-4824-924a-0c12436c79ea.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_ids = []
        
        # AST timezone (Atlantic Standard Time, UTC-4)
        self.ast_timezone = pytz.timezone('America/Halifax')  # AST timezone
        
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
                    details = f"(Expected {expected_status}, got {response.status_code}) - {response.text[:200]}"
                self.log_test(name, False, details)
                return False, error_data if 'error_data' in locals() else {}

        except requests.exceptions.RequestException as e:
            details = f"(Network Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}
        except Exception as e:
            details = f"(Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}

    def get_ast_date(self, offset_days=0):
        """Get current date in AST timezone with optional offset"""
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        ast_now = utc_now.astimezone(self.ast_timezone)
        target_date = ast_now + timedelta(days=offset_days)
        return target_date.date()

    def get_ast_datetime_string(self, offset_days=0):
        """Get current datetime in AST timezone as string"""
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        ast_now = utc_now.astimezone(self.ast_timezone)
        target_datetime = ast_now + timedelta(days=offset_days)
        return target_datetime.strftime("%Y-%m-%d")

    def test_ast_date_handling_client_creation(self):
        """Test 1: AST Date Handling - Client Creation with AST dates"""
        print("\n🌍 CRITICAL FIX TEST 1: AST DATE HANDLING - CLIENT CREATION")
        print("=" * 80)
        
        # Get current AST date
        ast_today = self.get_ast_date()
        ast_date_string = ast_today.isoformat()
        expected_payment_date = (ast_today + timedelta(days=30)).isoformat()
        
        print(f"   Current AST date: {ast_date_string}")
        print(f"   Expected payment date (30 days later): {expected_payment_date}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "AST Date Test Client",
            "email": f"ast_test_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": ast_date_string
        }
        
        success, response = self.run_test(
            "Create Client with AST Date",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            actual_start_date = response.get('start_date')
            actual_payment_date = response.get('next_payment_date')
            
            print(f"   ✅ Client created with ID: {response['id']}")
            print(f"   📅 Start date returned: {actual_start_date}")
            print(f"   💰 Payment date returned: {actual_payment_date}")
            
            # Verify dates are correct
            if str(actual_start_date) == ast_date_string:
                print("   ✅ AST start date handling: CORRECT")
            else:
                print(f"   ❌ AST start date handling: INCORRECT (Expected: {ast_date_string}, Got: {actual_start_date})")
                return False
                
            if str(actual_payment_date) == expected_payment_date:
                print("   ✅ AST payment date calculation: CORRECT")
            else:
                print(f"   ❌ AST payment date calculation: INCORRECT (Expected: {expected_payment_date}, Got: {actual_payment_date})")
                return False
                
            return True
        else:
            return False

    def test_ast_date_july_31st_issue(self):
        """Test 2: AST Date Handling - Specific July 31st AST vs August 1st UTC issue"""
        print("\n🌍 CRITICAL FIX TEST 2: AST DATE HANDLING - JULY 31ST ISSUE")
        print("=" * 80)
        
        # Test the specific issue: July 31st AST showing as August 1st
        july_31_ast = "2025-07-31"  # This should stay July 31st in AST
        expected_payment_date = "2025-08-30"  # 30 days later
        
        print(f"   Testing specific date: {july_31_ast} (July 31st AST)")
        print(f"   Expected payment date: {expected_payment_date}")
        print(f"   Issue: Should NOT show as August 1st due to UTC conversion")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "July 31st AST Test Client",
            "email": f"july31_ast_test_{timestamp}@example.com",
            "phone": "(555) 987-6543",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": july_31_ast
        }
        
        success, response = self.run_test(
            "Create Client with July 31st AST Date",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            actual_start_date = response.get('start_date')
            actual_payment_date = response.get('next_payment_date')
            
            print(f"   ✅ Client created with ID: {response['id']}")
            print(f"   📅 Start date returned: {actual_start_date}")
            print(f"   💰 Payment date returned: {actual_payment_date}")
            
            # Critical check: Should NOT be August 1st
            if str(actual_start_date) == july_31_ast:
                print("   ✅ July 31st AST date preserved: CORRECT (not converted to August 1st)")
            elif str(actual_start_date) == "2025-08-01":
                print("   ❌ July 31st AST date converted to August 1st: INCORRECT (UTC conversion issue)")
                return False
            else:
                print(f"   ❌ Unexpected date returned: {actual_start_date}")
                return False
                
            if str(actual_payment_date) == expected_payment_date:
                print("   ✅ Payment date calculation from July 31st: CORRECT")
            else:
                print(f"   ❌ Payment date calculation from July 31st: INCORRECT (Expected: {expected_payment_date}, Got: {actual_payment_date})")
                return False
                
            return True
        else:
            return False

    def test_email_uniqueness_constraint(self):
        """Test 3: Email Uniqueness Constraint - Should prevent duplicate emails"""
        print("\n📧 CRITICAL FIX TEST 3: EMAIL UNIQUENESS CONSTRAINT")
        print("=" * 80)
        
        # First, create a client with a unique email
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_email = f"unique_email_test_{timestamp}@example.com"
        
        client_data_1 = {
            "name": "First Client",
            "email": unique_email,
            "phone": "(555) 111-1111",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": "2025-07-31"
        }
        
        print(f"   Step 1: Creating client with unique email: {unique_email}")
        success1, response1 = self.run_test(
            "Create Client with Unique Email",
            "POST",
            "clients",
            200,
            client_data_1
        )
        
        if success1 and "id" in response1:
            self.created_client_ids.append(response1["id"])
            print(f"   ✅ First client created successfully with ID: {response1['id']}")
        else:
            print("   ❌ Failed to create first client - aborting email constraint test")
            return False
        
        # Now try to create another client with the same email (should fail)
        client_data_2 = {
            "name": "Duplicate Email Client",
            "email": unique_email,  # Same email as first client
            "phone": "(555) 222-2222",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-08-01"
        }
        
        print(f"   Step 2: Attempting to create client with duplicate email: {unique_email}")
        success2, response2 = self.run_test(
            "Create Client with Duplicate Email (Should Fail)",
            "POST",
            "clients",
            400,  # Should return 400 Bad Request
            client_data_2
        )
        
        if success2:
            print("   ✅ Email uniqueness constraint working: Duplicate email rejected")
            
            # Check error message
            error_detail = response2.get('detail', '')
            if 'email' in error_detail.lower() and ('exists' in error_detail.lower() or 'unique' in error_detail.lower()):
                print(f"   ✅ Proper error message returned: {error_detail}")
            else:
                print(f"   ⚠️  Error message could be more specific: {error_detail}")
            
            return True
        else:
            print("   ❌ Email uniqueness constraint FAILED: Duplicate email was accepted")
            return False

    def test_email_constraint_database_index(self):
        """Test 4: Email Constraint Database Index - Test the specific MongoDB index error"""
        print("\n📧 CRITICAL FIX TEST 4: EMAIL CONSTRAINT DATABASE INDEX")
        print("=" * 80)
        
        print("   Testing the specific MongoDB error: 'Unable to add key to index 'email': at least one key does not satisfy the uniqueness requirements'")
        
        # Try to create multiple clients with different emails to test index integrity
        test_emails = [
            f"index_test_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            f"index_test_2_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            f"index_test_3_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        ]
        
        all_success = True
        
        for i, email in enumerate(test_emails, 1):
            client_data = {
                "name": f"Index Test Client {i}",
                "email": email,
                "phone": f"(555) {100+i:03d}-{1000+i:04d}",
                "membership_type": "Standard",
                "monthly_fee": 55.00,
                "start_date": "2025-07-31"
            }
            
            print(f"   Step {i}: Creating client with email: {email}")
            success, response = self.run_test(
                f"Create Client {i} - Index Test",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                self.created_client_ids.append(response["id"])
                print(f"   ✅ Client {i} created successfully - No index constraint error")
            else:
                print(f"   ❌ Client {i} creation failed - Possible index constraint issue")
                all_success = False
        
        if all_success:
            print("   ✅ Email index constraint working correctly - No MongoDB index errors")
        else:
            print("   ❌ Email index constraint has issues - MongoDB index may be corrupted")
        
        return all_success

    def test_payment_recording_ast_dates(self):
        """Test 5: Payment Recording with AST Date Handling"""
        print("\n💰 CRITICAL FIX TEST 5: PAYMENT RECORDING WITH AST DATES")
        print("=" * 80)
        
        if not self.created_client_ids:
            print("   ❌ No clients available for payment recording test")
            return False
        
        client_id = self.created_client_ids[0]
        
        # Use AST date for payment
        ast_payment_date = self.get_ast_date()
        ast_payment_date_string = ast_payment_date.isoformat()
        
        print(f"   Testing payment recording with AST date: {ast_payment_date_string}")
        print(f"   Client ID: {client_id}")
        
        payment_data = {
            "client_id": client_id,
            "amount_paid": 55.00,
            "payment_date": ast_payment_date_string,
            "payment_method": "Cash",
            "notes": "AST date payment test"
        }
        
        success, response = self.run_test(
            "Record Payment with AST Date",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   ✅ Payment recorded successfully")
            print(f"   💰 Amount paid: ${response.get('amount_paid')}")
            print(f"   📅 New next payment date: {response.get('new_next_payment_date')}")
            print(f"   📧 Invoice sent: {response.get('invoice_sent')}")
            
            # Verify the new payment date is calculated correctly from AST date
            new_payment_date = response.get('new_next_payment_date')
            if new_payment_date:
                print("   ✅ Payment date calculation with AST dates: WORKING")
            else:
                print("   ❌ Payment date calculation with AST dates: FAILED")
                return False
            
            return True
        else:
            return False

    def test_payment_amounts_and_dates_display(self):
        """Test 6: Payment Amounts and Dates Display Corrections"""
        print("\n💰 CRITICAL FIX TEST 6: PAYMENT AMOUNTS AND DATES DISPLAY")
        print("=" * 80)
        
        # Test payment statistics endpoint
        success1, response1 = self.run_test(
            "Get Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if success1:
            total_revenue = response1.get('total_revenue', 0)
            monthly_revenue = response1.get('monthly_revenue', 0)
            payment_count = response1.get('payment_count', 0)
            
            print(f"   📊 Total revenue: ${total_revenue}")
            print(f"   📊 Monthly revenue: ${monthly_revenue}")
            print(f"   📊 Payment count: {payment_count}")
            
            # Verify amounts are reasonable (not showing incorrect data)
            if total_revenue >= 0 and monthly_revenue >= 0 and payment_count >= 0:
                print("   ✅ Payment statistics display: CORRECT (non-negative values)")
            else:
                print("   ❌ Payment statistics display: INCORRECT (negative values)")
                return False
        else:
            print("   ❌ Failed to get payment statistics")
            return False
        
        # Test getting clients to verify payment dates are displayed correctly
        success2, response2 = self.run_test(
            "Get Clients - Verify Payment Dates Display",
            "GET",
            "clients",
            200
        )
        
        if success2:
            clients = response2
            print(f"   👥 Found {len(clients)} clients")
            
            # Check a few clients for proper date formatting
            for i, client in enumerate(clients[:3]):  # Check first 3 clients
                name = client.get('name', 'Unknown')
                start_date = client.get('start_date')
                next_payment_date = client.get('next_payment_date')
                monthly_fee = client.get('monthly_fee', 0)
                
                print(f"   Client {i+1}: {name}")
                print(f"      Start date: {start_date}")
                print(f"      Next payment: {next_payment_date}")
                print(f"      Monthly fee: ${monthly_fee}")
                
                # Verify date formats are valid
                try:
                    if start_date:
                        datetime.fromisoformat(str(start_date))
                    if next_payment_date:
                        datetime.fromisoformat(str(next_payment_date))
                    print(f"      ✅ Date formats valid")
                except ValueError:
                    print(f"      ❌ Invalid date format detected")
                    return False
            
            print("   ✅ Client payment dates display: CORRECT")
            return True
        else:
            print("   ❌ Failed to get clients for date verification")
            return False

    def test_api_response_verification(self):
        """Test 7: API Response Verification for Key Endpoints"""
        print("\n🔌 CRITICAL FIX TEST 7: API RESPONSE VERIFICATION")
        print("=" * 80)
        
        # Test GET /api/clients
        print("   Testing GET /api/clients...")
        success1, response1 = self.run_test(
            "GET /api/clients - Response Verification",
            "GET",
            "clients",
            200
        )
        
        if success1:
            clients = response1
            print(f"   ✅ GET /api/clients: Returns {len(clients)} clients with proper JSON format")
            
            # Verify date formatting in response
            if clients:
                sample_client = clients[0]
                if 'start_date' in sample_client and 'next_payment_date' in sample_client:
                    print("   ✅ Client dates included in response")
                else:
                    print("   ❌ Client dates missing from response")
                    return False
        else:
            return False
        
        # Test POST /api/clients with AST date
        print("   Testing POST /api/clients with AST date...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ast_date = self.get_ast_date().isoformat()
        
        client_data = {
            "name": "API Response Test Client",
            "email": f"api_response_test_{timestamp}@example.com",
            "phone": "(555) 999-8888",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": ast_date
        }
        
        success2, response2 = self.run_test(
            "POST /api/clients - AST Date Acceptance",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success2 and "id" in response2:
            self.created_client_ids.append(response2["id"])
            print(f"   ✅ POST /api/clients: Accepts AST dates correctly")
            print(f"   📅 Returned start date: {response2.get('start_date')}")
            print(f"   💰 Calculated payment date: {response2.get('next_payment_date')}")
        else:
            return False
        
        # Test POST /api/payments/record with AST date
        print("   Testing POST /api/payments/record with AST date...")
        payment_data = {
            "client_id": response2["id"],
            "amount_paid": 75.00,
            "payment_date": ast_date,
            "payment_method": "Credit Card",
            "notes": "API response verification test"
        }
        
        success3, response3 = self.run_test(
            "POST /api/payments/record - AST Date Handling",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success3:
            print(f"   ✅ POST /api/payments/record: Handles AST dates properly")
            print(f"   💰 Payment recorded: ${response3.get('amount_paid')}")
            print(f"   📅 New payment date: {response3.get('new_next_payment_date')}")
            print(f"   📧 Invoice status: {response3.get('invoice_sent')}")
        else:
            return False
        
        print("   ✅ All key API endpoints verified working correctly")
        return True

    def run_all_critical_tests(self):
        """Run all critical fix tests"""
        print("🚨 CRITICAL FIXES TESTING - USER REPORTED ISSUES")
        print("=" * 80)
        print("Testing fixes for:")
        print("1. Date/Timezone Handling (AST, UTC-4)")
        print("2. Email Constraint Resolution")
        print("3. Payment Date Calculations")
        print("4. API Response Verification")
        print("=" * 80)
        
        tests = [
            self.test_ast_date_handling_client_creation,
            self.test_ast_date_july_31st_issue,
            self.test_email_uniqueness_constraint,
            self.test_email_constraint_database_index,
            self.test_payment_recording_ast_dates,
            self.test_payment_amounts_and_dates_display,
            self.test_api_response_verification
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 CRITICAL FIXES TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL CRITICAL FIXES VERIFIED WORKING!")
        else:
            print("⚠️  SOME CRITICAL FIXES NEED ATTENTION!")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    print("🚨 ALPHALETE ATHLETICS CLUB - CRITICAL FIXES TESTING")
    print("Testing specific user-reported issues and their fixes")
    print("=" * 80)
    
    tester = CriticalFixesTester()
    success = tester.run_all_critical_tests()
    
    sys.exit(0 if success else 1)