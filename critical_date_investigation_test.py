#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class CriticalDateInvestigationTester:
    def __init__(self, base_url="https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_ids = []

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

    def test_critical_date_calculation_bug(self):
        """CRITICAL TEST: Investigate the backwards date calculation bug"""
        print("\n🚨 CRITICAL DATE CALCULATION BUG INVESTIGATION")
        print("=" * 80)
        print("USER REPORT: 'If I add a client today Aug 5 and the client does not pay, the due date shows Aug 4'")
        print("EXPECTED: Due date should be FORWARD (one month ahead), not backwards!")
        print("=" * 80)
        
        # Get today's date
        today = date.today()
        print(f"📅 Today's date: {today}")
        
        # Create a client with today's date and payment_status="due" (unpaid)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Critical Date Test Client",
            "email": f"critical_date_test_{timestamp}@example.com",
            "phone": "+18685551234",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": today.isoformat(),
            "payment_status": "due"  # This is the key - unpaid client
        }
        
        print(f"🔍 Creating client with:")
        print(f"   Start Date: {today}")
        print(f"   Payment Status: due (unpaid)")
        print(f"   Expected Next Payment Date: {today + timedelta(days=30)} (approximately one month ahead)")
        
        success, response = self.run_test(
            "Create Client with Today's Date (Unpaid)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            client_id = response["id"]
            self.created_client_ids.append(client_id)
            
            start_date = response.get('start_date')
            next_payment_date = response.get('next_payment_date')
            payment_status = response.get('payment_status')
            amount_owed = response.get('amount_owed')
            
            print(f"\n📊 CRITICAL ANALYSIS:")
            print(f"   Client ID: {client_id}")
            print(f"   Start Date: {start_date}")
            print(f"   Next Payment Date: {next_payment_date}")
            print(f"   Payment Status: {payment_status}")
            print(f"   Amount Owed: {amount_owed}")
            
            # Parse dates for comparison
            try:
                start_date_obj = datetime.fromisoformat(start_date).date()
                next_payment_date_obj = datetime.fromisoformat(next_payment_date).date()
                
                print(f"\n🔍 DATE CALCULATION ANALYSIS:")
                print(f"   Start Date (parsed): {start_date_obj}")
                print(f"   Next Payment Date (parsed): {next_payment_date_obj}")
                
                # Check if next payment date is before start date (backwards!)
                if next_payment_date_obj < start_date_obj:
                    print(f"   🚨 CRITICAL BUG CONFIRMED: Next payment date is BEFORE start date!")
                    print(f"   🚨 This matches user's report: due date shows BACKWARDS!")
                    print(f"   🚨 Days difference: {(start_date_obj - next_payment_date_obj).days} days backwards")
                    return False
                elif next_payment_date_obj == start_date_obj:
                    print(f"   ⚠️  ISSUE: Next payment date is SAME as start date!")
                    print(f"   ⚠️  Expected: Should be approximately one month ahead")
                    return False
                else:
                    days_ahead = (next_payment_date_obj - start_date_obj).days
                    print(f"   ✅ Next payment date is AHEAD of start date by {days_ahead} days")
                    
                    # Check if it's reasonable (should be around 28-31 days ahead)
                    if days_ahead < 25 or days_ahead > 35:
                        print(f"   ⚠️  WARNING: Days ahead ({days_ahead}) seems unusual for monthly billing")
                        print(f"   ⚠️  Expected: Around 28-31 days for monthly billing")
                    else:
                        print(f"   ✅ Days ahead ({days_ahead}) is reasonable for monthly billing")
                        
            except Exception as e:
                print(f"   ❌ Error parsing dates: {e}")
                return False
                
            # Check payment status and amount owed
            if payment_status == "due" and amount_owed and amount_owed > 0:
                print(f"   ✅ Payment status and amount owed are correct for unpaid client")
            else:
                print(f"   ⚠️  Payment status or amount owed may be incorrect")
                print(f"   Expected: payment_status='due', amount_owed > 0")
                print(f"   Actual: payment_status='{payment_status}', amount_owed={amount_owed}")
                
            return True
        else:
            print(f"   ❌ Failed to create test client")
            return False

    def test_data_display_issues(self):
        """CRITICAL TEST: Investigate 'No data showing on home page' and 'Total revenue not showing'"""
        print("\n🚨 DATA DISPLAY ISSUES INVESTIGATION")
        print("=" * 80)
        print("USER REPORTS:")
        print("1. 'No data is showing on home page'")
        print("2. 'Total revenue not showing'")
        print("=" * 80)
        
        # Test 1: Check if GET /api/clients returns data
        print(f"\n🔍 TEST 1: Check if client data is available")
        success1, clients_response = self.run_test(
            "Get All Clients (Check for Data)",
            "GET",
            "clients",
            200
        )
        
        if success1:
            clients = clients_response if isinstance(clients_response, list) else []
            print(f"   📊 Client Data Analysis:")
            print(f"   Total Clients Found: {len(clients)}")
            
            if len(clients) == 0:
                print(f"   🚨 CRITICAL ISSUE: NO CLIENTS FOUND!")
                print(f"   🚨 This explains 'No data showing on home page'")
            else:
                print(f"   ✅ Clients found - data should be available")
                for i, client in enumerate(clients[:3]):  # Show first 3 clients
                    print(f"   Client {i+1}: {client.get('name')} - {client.get('email')} - Status: {client.get('status')}")
        else:
            print(f"   ❌ Failed to get clients data")
            
        # Test 2: Check if GET /api/payments/stats returns revenue data
        print(f"\n🔍 TEST 2: Check if revenue data is available")
        success2, stats_response = self.run_test(
            "Get Payment Statistics (Check Revenue)",
            "GET",
            "payments/stats",
            200
        )
        
        if success2:
            total_revenue = stats_response.get('total_revenue', 0)
            payment_count = stats_response.get('payment_count', 0)
            monthly_revenue = stats_response.get('monthly_revenue', 0)
            
            print(f"   📊 Revenue Data Analysis:")
            print(f"   Total Revenue: {total_revenue}")
            print(f"   Payment Count: {payment_count}")
            print(f"   Monthly Revenue: {monthly_revenue}")
            
            if total_revenue == 0 and payment_count == 0:
                print(f"   🚨 CRITICAL ISSUE: NO REVENUE DATA FOUND!")
                print(f"   🚨 This explains 'Total revenue not showing'")
                print(f"   🚨 Possible causes:")
                print(f"      - No payments have been recorded")
                print(f"      - Payment recording system is broken")
                print(f"      - Database connection issues")
            else:
                print(f"   ✅ Revenue data found - should be displaying")
        else:
            print(f"   ❌ Failed to get payment statistics")
            
        return success1 and success2

    def test_database_connectivity(self):
        """Test basic database connectivity and data integrity"""
        print("\n🔍 DATABASE CONNECTIVITY TEST")
        print("=" * 50)
        
        # Test API health
        success1, health_response = self.run_test(
            "API Health Check",
            "GET",
            "health",
            200
        )
        
        if success1:
            print(f"   ✅ API is responding")
            print(f"   Status: {health_response.get('status')}")
            print(f"   Message: {health_response.get('message')}")
        
        # Test membership types (should be seeded)
        success2, membership_response = self.run_test(
            "Get Membership Types",
            "GET",
            "membership-types",
            200
        )
        
        if success2:
            memberships = membership_response if isinstance(membership_response, list) else []
            print(f"   📊 Membership Types: {len(memberships)} found")
            if len(memberships) == 0:
                print(f"   ⚠️  No membership types found - may need seeding")
            else:
                for membership in memberships:
                    print(f"   - {membership.get('name')}: ${membership.get('monthly_fee')}")
        
        return success1 and success2

    def test_calculate_next_payment_date_function(self):
        """Test the calculate_next_payment_date function with various scenarios"""
        print("\n🔍 CALCULATE_NEXT_PAYMENT_DATE FUNCTION TEST")
        print("=" * 60)
        
        # Test various start dates to see if calculation is working correctly
        test_cases = [
            {
                "name": "Today's Date",
                "start_date": date.today().isoformat(),
                "description": "Current date test"
            },
            {
                "name": "January 15th",
                "start_date": "2025-01-15",
                "description": "Mid-month test"
            },
            {
                "name": "January 31st",
                "start_date": "2025-01-31",
                "description": "Month-end test"
            },
            {
                "name": "February 28th",
                "start_date": "2025-02-28",
                "description": "February end test"
            }
        ]
        
        all_passed = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, test_case in enumerate(test_cases):
            print(f"\n📅 Test Case: {test_case['name']}")
            print(f"   Start Date: {test_case['start_date']}")
            print(f"   Description: {test_case['description']}")
            
            client_data = {
                "name": f"Date Calc Test {i+1}",
                "email": f"date_calc_test_{i+1}_{timestamp}@example.com",
                "phone": f"(555) {200+i:03d}-{2000+i:04d}",
                "membership_type": "Standard",
                "monthly_fee": 55.0,
                "start_date": test_case['start_date'],
                "payment_status": "due"
            }
            
            success, response = self.run_test(
                f"Create Client - {test_case['name']}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                self.created_client_ids.append(response["id"])
                
                start_date = response.get('start_date')
                next_payment_date = response.get('next_payment_date')
                
                print(f"   Result:")
                print(f"   Start Date: {start_date}")
                print(f"   Next Payment Date: {next_payment_date}")
                
                # Analyze the calculation
                try:
                    start_obj = datetime.fromisoformat(start_date).date()
                    next_obj = datetime.fromisoformat(next_payment_date).date()
                    days_diff = (next_obj - start_obj).days
                    
                    print(f"   Days Difference: {days_diff}")
                    
                    if days_diff < 0:
                        print(f"   🚨 CRITICAL: Next payment date is BEFORE start date!")
                        all_passed = False
                    elif days_diff == 0:
                        print(f"   🚨 CRITICAL: Next payment date is SAME as start date!")
                        all_passed = False
                    elif days_diff < 25 or days_diff > 35:
                        print(f"   ⚠️  WARNING: Unusual days difference for monthly billing")
                    else:
                        print(f"   ✅ Reasonable monthly calculation")
                        
                except Exception as e:
                    print(f"   ❌ Error analyzing dates: {e}")
                    all_passed = False
            else:
                print(f"   ❌ Failed to create client for test case")
                all_passed = False
                
        return all_passed

    def test_timezone_issues(self):
        """Test for potential timezone-related date calculation issues"""
        print("\n🔍 TIMEZONE ISSUES INVESTIGATION")
        print("=" * 50)
        
        # Get current time information
        now_utc = datetime.utcnow()
        now_local = datetime.now()
        
        print(f"   Current UTC Time: {now_utc}")
        print(f"   Current Local Time: {now_local}")
        print(f"   Time Difference: {(now_local - now_utc).total_seconds() / 3600} hours")
        
        # Create a client and check if dates are affected by timezone
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        today = date.today()
        
        client_data = {
            "name": "Timezone Test Client",
            "email": f"timezone_test_{timestamp}@example.com",
            "phone": "+18685559999",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": today.isoformat(),
            "payment_status": "due"
        }
        
        success, response = self.run_test(
            "Create Client for Timezone Test",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            
            start_date = response.get('start_date')
            next_payment_date = response.get('next_payment_date')
            created_at = response.get('created_at')
            
            print(f"   📊 Timezone Analysis:")
            print(f"   Input Start Date: {today}")
            print(f"   Returned Start Date: {start_date}")
            print(f"   Next Payment Date: {next_payment_date}")
            print(f"   Created At: {created_at}")
            
            # Check if start date matches input
            if str(start_date) == today.isoformat():
                print(f"   ✅ Start date matches input - no timezone drift")
            else:
                print(f"   ⚠️  Start date doesn't match input - possible timezone issue")
                
            return True
        else:
            return False

    def cleanup_test_data(self):
        """Clean up test clients created during testing"""
        print(f"\n🧹 CLEANING UP TEST DATA")
        print(f"   Clients to delete: {len(self.created_client_ids)}")
        
        for client_id in self.created_client_ids:
            success, response = self.run_test(
                f"Delete Test Client {client_id[:8]}...",
                "DELETE",
                f"clients/{client_id}",
                200
            )
            
            if success:
                print(f"   ✅ Deleted client {client_id[:8]}...")
            else:
                print(f"   ❌ Failed to delete client {client_id[:8]}...")

    def run_all_critical_tests(self):
        """Run all critical investigation tests"""
        print("🚨 CRITICAL ISSUES INVESTIGATION - USER REPORTED PROBLEMS")
        print("=" * 80)
        print("INVESTIGATING:")
        print("1. Date calculation bug (backwards dates)")
        print("2. No data showing on home page")
        print("3. Total revenue not showing")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        test_results.append(("Database Connectivity", self.test_database_connectivity()))
        test_results.append(("Data Display Issues", self.test_data_display_issues()))
        test_results.append(("Critical Date Calculation Bug", self.test_critical_date_calculation_bug()))
        test_results.append(("Calculate Next Payment Date Function", self.test_calculate_next_payment_date_function()))
        test_results.append(("Timezone Issues", self.test_timezone_issues()))
        
        # Clean up test data
        self.cleanup_test_data()
        
        # Summary
        print(f"\n🎯 CRITICAL INVESTIGATION SUMMARY")
        print("=" * 50)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        print(f"\n📊 TEST RESULTS:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        # Critical findings
        failed_tests = [name for name, result in test_results if not result]
        if failed_tests:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for test_name in failed_tests:
                print(f"   ❌ {test_name}")
        else:
            print(f"\n✅ ALL CRITICAL TESTS PASSED")
            
        return len(failed_tests) == 0

if __name__ == "__main__":
    tester = CriticalDateInvestigationTester()
    success = tester.run_all_critical_tests()
    sys.exit(0 if success else 1)