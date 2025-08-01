#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class MobileCacheUrgentTester:
    def __init__(self, base_url="https://8beb6460-0117-4864-a970-463f629aa57c.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

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

    def test_payment_stats_current_state(self):
        """URGENT: Test GET /api/payments/stats - What is the current total_revenue?"""
        print("\n🎯 URGENT TEST 1: GET /api/payments/stats - Current Total Revenue")
        print("=" * 80)
        
        success, response = self.run_test(
            "GET Payment Stats - Current Total Revenue",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            total_revenue = response.get('total_revenue', 0)
            payment_count = response.get('payment_count', 0)
            monthly_revenue = response.get('monthly_revenue', 0)
            
            print(f"\n📊 CURRENT PAYMENT STATISTICS:")
            print(f"   💰 Total Revenue: {total_revenue}")
            print(f"   📅 Monthly Revenue: {monthly_revenue}")
            print(f"   🧾 Payment Count: {payment_count}")
            print(f"   🕐 Timestamp: {response.get('timestamp', 'N/A')}")
            
            # Check if this matches user's expectation
            if total_revenue == 0:
                print(f"   ⚠️  WARNING: Total revenue is 0 - User expected 100!")
                print(f"   🔍 This matches user's mobile device showing 0 revenue")
            elif total_revenue == 100:
                print(f"   ✅ Total revenue is 100 - Matches user's expectation!")
            else:
                print(f"   ❓ Total revenue is {total_revenue} - Different from user's expectation of 100")
        
        return success

    def test_clients_current_state(self):
        """URGENT: Test GET /api/clients - How many clients are there and what's their status?"""
        print("\n🎯 URGENT TEST 2: GET /api/clients - Current Client Count and Status")
        print("=" * 80)
        
        success, response = self.run_test(
            "GET Clients - Current Count and Status",
            "GET",
            "clients",
            200
        )
        
        if success:
            total_clients = len(response)
            active_clients = len([c for c in response if c.get('status') == 'Active'])
            inactive_clients = len([c for c in response if c.get('status') == 'Inactive'])
            
            print(f"\n👥 CURRENT CLIENT STATISTICS:")
            print(f"   📊 Total Clients: {total_clients}")
            print(f"   ✅ Active Clients: {active_clients}")
            print(f"   ❌ Inactive Clients: {inactive_clients}")
            
            # Check if this matches user's expectation
            if active_clients == 0:
                print(f"   ⚠️  WARNING: Active clients is 0 - User expected 1 active client!")
                print(f"   🔍 This matches user's mobile device showing 0 members")
            elif active_clients == 1:
                print(f"   ✅ Active clients is 1 - Matches user's expectation!")
            else:
                print(f"   ❓ Active clients is {active_clients} - Different from user's expectation of 1")
            
            # Show client details
            if total_clients > 0:
                print(f"\n📋 CLIENT DETAILS:")
                for i, client in enumerate(response[:5], 1):  # Show first 5 clients
                    print(f"   {i}. {client.get('name', 'Unknown')} ({client.get('email', 'No email')})")
                    print(f"      Status: {client.get('status', 'Unknown')}")
                    print(f"      Membership: {client.get('membership_type', 'Unknown')} - ${client.get('monthly_fee', 0)}")
                    print(f"      Next Payment: {client.get('next_payment_date', 'Unknown')}")
                
                if total_clients > 5:
                    print(f"   ... and {total_clients - 5} more clients")
            else:
                print(f"   📭 No clients found in database")
        
        return success

    def test_database_state_investigation(self):
        """URGENT: Investigate if database has been cleared or changed"""
        print("\n🎯 URGENT TEST 3: Database State Investigation")
        print("=" * 80)
        
        # Test multiple endpoints to understand database state
        endpoints_to_test = [
            ("membership-types", "Membership Types"),
            ("reminders/stats", "Reminder Statistics"),
            ("", "API Health Check")
        ]
        
        all_success = True
        
        for endpoint, description in endpoints_to_test:
            success, response = self.run_test(
                f"Check {description}",
                "GET",
                endpoint,
                200
            )
            
            if success:
                if endpoint == "membership-types":
                    membership_count = len(response) if isinstance(response, list) else 0
                    print(f"   📋 Membership Types Available: {membership_count}")
                    
                elif endpoint == "reminders/stats":
                    total_sent = response.get('total_reminders_sent', 0)
                    scheduler_active = response.get('scheduler_active', False)
                    print(f"   📧 Total Reminders Sent: {total_sent}")
                    print(f"   ⚙️  Scheduler Active: {scheduler_active}")
                    
                elif endpoint == "":
                    api_status = response.get('status', 'unknown')
                    api_version = response.get('version', 'unknown')
                    print(f"   🔧 API Status: {api_status}")
                    print(f"   📦 API Version: {api_version}")
            else:
                all_success = False
        
        return all_success

    def test_api_errors_investigation(self):
        """URGENT: Check for any API errors or issues"""
        print("\n🎯 URGENT TEST 4: API Errors and Issues Investigation")
        print("=" * 80)
        
        # Test various endpoints for errors
        error_tests = [
            ("clients/non-existent-id", "GET", 404, "Non-existent Client"),
            ("payments/stats", "GET", 200, "Payment Stats Reliability"),
            ("clients", "GET", 200, "Clients List Reliability"),
        ]
        
        all_success = True
        
        for endpoint, method, expected_status, description in error_tests:
            success, response = self.run_test(
                f"Error Test - {description}",
                method,
                endpoint,
                expected_status
            )
            
            if not success:
                all_success = False
                print(f"   ⚠️  API Error detected in {description}")
        
        return all_success

    def test_create_test_client_and_payment(self):
        """Create a test client and payment to verify real-time data updates"""
        print("\n🎯 URGENT TEST 5: Create Test Client and Payment - Real-time Data Verification")
        print("=" * 80)
        
        # Step 1: Create a test client
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Mobile Cache Test Client",
            "email": f"mobile_cache_test_{timestamp}@example.com",
            "phone": "(555) 999-0000",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-08-01"
        }
        
        success1, client_response = self.run_test(
            "Create Test Client for Mobile Cache Verification",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1:
            print("❌ Failed to create test client - aborting real-time test")
            return False
        
        test_client_id = client_response.get('id')
        print(f"   ✅ Created test client ID: {test_client_id}")
        
        # Step 2: Record a payment for this client
        payment_data = {
            "client_id": test_client_id,
            "amount_paid": 50.00,
            "payment_date": "2025-08-01",
            "payment_method": "Cash",
            "notes": "Mobile cache test payment"
        }
        
        success2, payment_response = self.run_test(
            "Record Test Payment for Mobile Cache Verification",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success2:
            print(f"   ✅ Payment recorded successfully")
            print(f"   💰 Amount: ${payment_response.get('amount_paid', 0)}")
            print(f"   📧 Invoice sent: {payment_response.get('invoice_sent', False)}")
        
        # Step 3: Check updated payment stats
        success3, stats_response = self.run_test(
            "Check Updated Payment Stats After Test Payment",
            "GET",
            "payments/stats",
            200
        )
        
        if success3:
            new_total_revenue = stats_response.get('total_revenue', 0)
            new_payment_count = stats_response.get('payment_count', 0)
            
            print(f"\n📊 UPDATED PAYMENT STATISTICS AFTER TEST:")
            print(f"   💰 New Total Revenue: {new_total_revenue}")
            print(f"   🧾 New Payment Count: {new_payment_count}")
            
            if new_total_revenue > 0:
                print(f"   ✅ Revenue updated successfully - Real-time data working!")
            else:
                print(f"   ⚠️  Revenue still 0 - Possible data persistence issue")
        
        # Step 4: Check updated client count
        success4, clients_response = self.run_test(
            "Check Updated Client Count After Test Client",
            "GET",
            "clients",
            200
        )
        
        if success4:
            new_total_clients = len(clients_response)
            new_active_clients = len([c for c in clients_response if c.get('status') == 'Active'])
            
            print(f"\n👥 UPDATED CLIENT STATISTICS AFTER TEST:")
            print(f"   📊 New Total Clients: {new_total_clients}")
            print(f"   ✅ New Active Clients: {new_active_clients}")
            
            if new_active_clients > 0:
                print(f"   ✅ Client count updated successfully - Real-time data working!")
            else:
                print(f"   ⚠️  Active clients still 0 - Possible data persistence issue")
        
        return success1 and success2 and success3 and success4

    def run_urgent_mobile_cache_tests(self):
        """Run all urgent mobile cache tests as requested in review"""
        print("🚨 URGENT MOBILE CACHE ISSUE INVESTIGATION")
        print("=" * 80)
        print("User's mobile device shows:")
        print("- Total Revenue: 0 (previously was 100)")
        print("- Active Members: 0 (user says they have 1 active client)")
        print("- Sync Status: syncing")
        print("=" * 80)
        
        # Run all urgent tests
        test1_success = self.test_payment_stats_current_state()
        test2_success = self.test_clients_current_state()
        test3_success = self.test_database_state_investigation()
        test4_success = self.test_api_errors_investigation()
        test5_success = self.test_create_test_client_and_payment()
        
        # Summary
        print(f"\n🎯 URGENT MOBILE CACHE INVESTIGATION SUMMARY")
        print("=" * 80)
        print(f"📊 TOTAL TESTS RUN: {self.tests_run}")
        print(f"✅ TESTS PASSED: {self.tests_passed}")
        print(f"❌ TESTS FAILED: {self.tests_run - self.tests_passed}")
        print(f"📈 SUCCESS RATE: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        all_tests_passed = test1_success and test2_success and test3_success and test4_success and test5_success
        
        if all_tests_passed:
            print(f"🎉 ALL URGENT TESTS PASSED!")
        else:
            print(f"⚠️  SOME URGENT TESTS FAILED - INVESTIGATION NEEDED")
        
        print("=" * 80)
        return all_tests_passed

if __name__ == "__main__":
    print("🚨 URGENT: MOBILE CACHE ISSUE BACKEND VERIFICATION")
    print("Testing backend data state for mobile cache discrepancy...")
    print()
    
    tester = MobileCacheUrgentTester()
    success = tester.run_urgent_mobile_cache_tests()
    
    if success:
        print("\n✅ URGENT INVESTIGATION COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\n❌ URGENT INVESTIGATION FOUND ISSUES")
        sys.exit(1)