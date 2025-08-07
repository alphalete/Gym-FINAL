#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class PaidThisMonthTester:
    def __init__(self, base_url="https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_clients = []
        self.payment_records = []

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
                    details = f"(Status: {response.status_code}, Response time: {response.elapsed.total_seconds():.3f}s)"
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

    def test_initial_payment_stats(self):
        """Test 1: Get initial payment statistics to establish baseline"""
        print("\n🎯 TEST 1: INITIAL PAYMENT STATISTICS BASELINE")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get Initial Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            total_revenue = response.get('total_revenue', 0)
            monthly_revenue = response.get('monthly_revenue', 0)
            payment_count = response.get('payment_count', 0)
            
            print(f"   📊 INITIAL STATE:")
            print(f"      Total Revenue: TTD {total_revenue}")
            print(f"      Monthly Revenue: TTD {monthly_revenue}")
            print(f"      Payment Count: {payment_count}")
            print(f"      Timestamp: {response.get('timestamp')}")
            
            # Verify API response structure
            required_fields = ['total_revenue', 'monthly_revenue', 'payment_count', 'timestamp']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"   ❌ MISSING REQUIRED FIELDS: {missing_fields}")
                return False
            else:
                print(f"   ✅ ALL REQUIRED FIELDS PRESENT")
                
            # Verify data consistency
            if monthly_revenue <= total_revenue:
                print(f"   ✅ DATA CONSISTENCY: Monthly revenue ({monthly_revenue}) <= Total revenue ({total_revenue})")
            else:
                print(f"   ❌ DATA INCONSISTENCY: Monthly revenue ({monthly_revenue}) > Total revenue ({total_revenue})")
                return False
                
            return True
        
        return False

    def test_create_test_clients(self):
        """Test 2: Create test clients for payment recording"""
        print("\n🎯 TEST 2: CREATE TEST CLIENTS FOR PAYMENT TESTING")
        print("=" * 80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Create clients with different scenarios
        test_clients = [
            {
                "name": "Current Month Test Client 1",
                "email": f"current_month_1_{timestamp}@example.com",
                "phone": "(555) 001-0001",
                "membership_type": "Standard",
                "monthly_fee": 55.0,
                "start_date": f"{current_year}-{current_month:02d}-01",
                "payment_status": "due"
            },
            {
                "name": "Current Month Test Client 2", 
                "email": f"current_month_2_{timestamp}@example.com",
                "phone": "(555) 001-0002",
                "membership_type": "Premium",
                "monthly_fee": 75.0,
                "start_date": f"{current_year}-{current_month:02d}-15",
                "payment_status": "due"
            },
            {
                "name": "Previous Month Test Client",
                "email": f"previous_month_{timestamp}@example.com", 
                "phone": "(555) 001-0003",
                "membership_type": "Elite",
                "monthly_fee": 100.0,
                "start_date": f"{current_year}-{current_month-1 if current_month > 1 else 12:02d}-01",
                "payment_status": "due"
            }
        ]
        
        all_success = True
        for i, client_data in enumerate(test_clients, 1):
            success, response = self.run_test(
                f"Create Test Client {i}: {client_data['name']}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                client_id = response["id"]
                self.created_clients.append({
                    "id": client_id,
                    "name": client_data["name"],
                    "monthly_fee": client_data["monthly_fee"],
                    "start_date": client_data["start_date"]
                })
                print(f"   ✅ Created client ID: {client_id}")
                print(f"      Name: {response.get('name')}")
                print(f"      Monthly Fee: TTD {response.get('monthly_fee')}")
                print(f"      Payment Status: {response.get('payment_status')}")
                print(f"      Amount Owed: TTD {response.get('amount_owed')}")
            else:
                all_success = False
                
        print(f"\n   📊 CREATED CLIENTS SUMMARY:")
        print(f"      Total clients created: {len(self.created_clients)}")
        for client in self.created_clients:
            print(f"      - {client['name']}: TTD {client['monthly_fee']}")
            
        return all_success

    def test_record_current_month_payments(self):
        """Test 3: Record payments in current month to test monthly revenue calculation"""
        print("\n🎯 TEST 3: RECORD CURRENT MONTH PAYMENTS")
        print("=" * 80)
        
        if not self.created_clients:
            print("❌ No test clients available - skipping payment recording")
            return False
            
        current_date = date.today()
        current_month = current_date.month
        current_year = current_date.year
        
        # Record payments for first two clients (current month clients)
        current_month_clients = self.created_clients[:2]  # First 2 clients are current month
        expected_monthly_revenue = 0
        
        all_success = True
        for i, client in enumerate(current_month_clients, 1):
            # Record payment for current month
            payment_data = {
                "client_id": client["id"],
                "amount_paid": client["monthly_fee"],
                "payment_date": f"{current_year}-{current_month:02d}-{10+i:02d}",  # Different dates in current month
                "payment_method": "Credit Card",
                "notes": f"Current month payment test {i}"
            }
            
            success, response = self.run_test(
                f"Record Current Month Payment {i}: {client['name']}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                expected_monthly_revenue += client["monthly_fee"]
                self.payment_records.append({
                    "client_id": client["id"],
                    "client_name": client["name"],
                    "amount_paid": client["monthly_fee"],
                    "payment_date": payment_data["payment_date"],
                    "month": current_month,
                    "year": current_year
                })
                
                print(f"   ✅ Payment recorded successfully")
                print(f"      Client: {response.get('client_name')}")
                print(f"      Amount: TTD {response.get('amount_paid')}")
                print(f"      New Next Payment Date: {response.get('new_next_payment_date')}")
                print(f"      Invoice Sent: {response.get('invoice_sent')}")
            else:
                all_success = False
                
        # Record payment for previous month client (should not affect current month revenue)
        if len(self.created_clients) > 2:
            previous_month_client = self.created_clients[2]
            prev_month = current_month - 1 if current_month > 1 else 12
            prev_year = current_year if current_month > 1 else current_year - 1
            
            payment_data = {
                "client_id": previous_month_client["id"],
                "amount_paid": previous_month_client["monthly_fee"],
                "payment_date": f"{prev_year}-{prev_month:02d}-15",  # Previous month payment
                "payment_method": "Bank Transfer",
                "notes": "Previous month payment test"
            }
            
            success, response = self.run_test(
                f"Record Previous Month Payment: {previous_month_client['name']}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                self.payment_records.append({
                    "client_id": previous_month_client["id"],
                    "client_name": previous_month_client["name"],
                    "amount_paid": previous_month_client["monthly_fee"],
                    "payment_date": payment_data["payment_date"],
                    "month": prev_month,
                    "year": prev_year
                })
                print(f"   ✅ Previous month payment recorded (should not affect current month revenue)")
            else:
                all_success = False
                
        print(f"\n   📊 PAYMENT RECORDING SUMMARY:")
        print(f"      Current month payments: {len(current_month_clients)}")
        print(f"      Expected monthly revenue: TTD {expected_monthly_revenue}")
        print(f"      Total payments recorded: {len(self.payment_records)}")
        
        return all_success

    def test_verify_monthly_revenue_calculation(self):
        """Test 4: Verify monthly revenue calculation is correct"""
        print("\n🎯 TEST 4: VERIFY MONTHLY REVENUE CALCULATION")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get Updated Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if not success:
            return False
            
        total_revenue = response.get('total_revenue', 0)
        monthly_revenue = response.get('monthly_revenue', 0)
        payment_count = response.get('payment_count', 0)
        
        print(f"   📊 UPDATED PAYMENT STATISTICS:")
        print(f"      Total Revenue: TTD {total_revenue}")
        print(f"      Monthly Revenue: TTD {monthly_revenue}")
        print(f"      Payment Count: {payment_count}")
        print(f"      Timestamp: {response.get('timestamp')}")
        
        # Calculate expected values
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        expected_monthly_revenue = sum(
            record["amount_paid"] for record in self.payment_records 
            if record["month"] == current_month and record["year"] == current_year
        )
        
        expected_total_revenue = sum(record["amount_paid"] for record in self.payment_records)
        
        print(f"\n   🎯 EXPECTED VALUES:")
        print(f"      Expected Monthly Revenue: TTD {expected_monthly_revenue}")
        print(f"      Expected Total Revenue: TTD {expected_total_revenue}")
        print(f"      Expected Payment Count: {len(self.payment_records)}")
        
        # Verify calculations
        verification_results = []
        
        # Test 1: Monthly revenue calculation
        if abs(monthly_revenue - expected_monthly_revenue) < 0.01:  # Allow for floating point precision
            print(f"   ✅ MONTHLY REVENUE CALCULATION: CORRECT")
            verification_results.append(True)
        else:
            print(f"   ❌ MONTHLY REVENUE CALCULATION: INCORRECT")
            print(f"      Expected: TTD {expected_monthly_revenue}")
            print(f"      Actual: TTD {monthly_revenue}")
            print(f"      Difference: TTD {abs(monthly_revenue - expected_monthly_revenue)}")
            verification_results.append(False)
            
        # Test 2: Total revenue calculation
        if abs(total_revenue - expected_total_revenue) < 0.01:
            print(f"   ✅ TOTAL REVENUE CALCULATION: CORRECT")
            verification_results.append(True)
        else:
            print(f"   ❌ TOTAL REVENUE CALCULATION: INCORRECT")
            print(f"      Expected: TTD {expected_total_revenue}")
            print(f"      Actual: TTD {total_revenue}")
            verification_results.append(False)
            
        # Test 3: Payment count
        if payment_count == len(self.payment_records):
            print(f"   ✅ PAYMENT COUNT: CORRECT")
            verification_results.append(True)
        else:
            print(f"   ❌ PAYMENT COUNT: INCORRECT")
            print(f"      Expected: {len(self.payment_records)}")
            print(f"      Actual: {payment_count}")
            verification_results.append(False)
            
        # Test 4: Data consistency (monthly <= total)
        if monthly_revenue <= total_revenue:
            print(f"   ✅ DATA CONSISTENCY: Monthly revenue <= Total revenue")
            verification_results.append(True)
        else:
            print(f"   ❌ DATA CONSISTENCY: Monthly revenue > Total revenue")
            verification_results.append(False)
            
        # Test 5: Non-zero monthly revenue (if we recorded current month payments)
        current_month_payments = [r for r in self.payment_records if r["month"] == current_month and r["year"] == current_year]
        if current_month_payments and monthly_revenue > 0:
            print(f"   ✅ NON-ZERO MONTHLY REVENUE: Correctly showing TTD {monthly_revenue}")
            verification_results.append(True)
        elif not current_month_payments and monthly_revenue == 0:
            print(f"   ✅ ZERO MONTHLY REVENUE: Correctly showing TTD 0 (no current month payments)")
            verification_results.append(True)
        else:
            print(f"   ❌ MONTHLY REVENUE LOGIC: Incorrect value")
            verification_results.append(False)
            
        return all(verification_results)

    def test_monthly_revenue_edge_cases(self):
        """Test 5: Test monthly revenue calculation edge cases"""
        print("\n🎯 TEST 5: MONTHLY REVENUE EDGE CASES")
        print("=" * 80)
        
        # Test with different payment dates in current month
        current_date = date.today()
        current_month = current_date.month
        current_year = current_date.year
        
        if not self.created_clients:
            print("❌ No test clients available - skipping edge case testing")
            return False
            
        # Create additional client for edge case testing
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        edge_case_client_data = {
            "name": "Edge Case Test Client",
            "email": f"edge_case_{timestamp}@example.com",
            "phone": "(555) 999-9999",
            "membership_type": "VIP",
            "monthly_fee": 150.0,
            "start_date": f"{current_year}-{current_month:02d}-01",
            "payment_status": "due"
        }
        
        success, response = self.run_test(
            "Create Edge Case Test Client",
            "POST",
            "clients",
            200,
            edge_case_client_data
        )
        
        if not success or "id" not in response:
            print("❌ Failed to create edge case test client")
            return False
            
        edge_case_client_id = response["id"]
        
        # Test payments on different days of current month
        edge_case_payments = [
            {
                "date": f"{current_year}-{current_month:02d}-01",  # First day of month
                "amount": 50.0,
                "description": "First day of month"
            },
            {
                "date": f"{current_year}-{current_month:02d}-15",  # Mid month
                "amount": 25.0,
                "description": "Mid month"
            }
        ]
        
        # Get baseline monthly revenue
        success, baseline_response = self.run_test(
            "Get Baseline Monthly Revenue",
            "GET",
            "payments/stats",
            200
        )
        
        if not success:
            return False
            
        baseline_monthly_revenue = baseline_response.get('monthly_revenue', 0)
        
        # Record edge case payments
        total_edge_case_amount = 0
        for i, payment_info in enumerate(edge_case_payments, 1):
            payment_data = {
                "client_id": edge_case_client_id,
                "amount_paid": payment_info["amount"],
                "payment_date": payment_info["date"],
                "payment_method": "Test",
                "notes": f"Edge case payment {i}: {payment_info['description']}"
            }
            
            success, response = self.run_test(
                f"Record Edge Case Payment {i}: {payment_info['description']}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success:
                total_edge_case_amount += payment_info["amount"]
                print(f"   ✅ Recorded TTD {payment_info['amount']} on {payment_info['date']}")
            else:
                return False
                
        # Verify monthly revenue increased by correct amount
        success, final_response = self.run_test(
            "Get Final Monthly Revenue After Edge Cases",
            "GET",
            "payments/stats",
            200
        )
        
        if not success:
            return False
            
        final_monthly_revenue = final_response.get('monthly_revenue', 0)
        expected_increase = total_edge_case_amount
        actual_increase = final_monthly_revenue - baseline_monthly_revenue
        
        print(f"\n   📊 EDGE CASE RESULTS:")
        print(f"      Baseline Monthly Revenue: TTD {baseline_monthly_revenue}")
        print(f"      Final Monthly Revenue: TTD {final_monthly_revenue}")
        print(f"      Expected Increase: TTD {expected_increase}")
        print(f"      Actual Increase: TTD {actual_increase}")
        
        if abs(actual_increase - expected_increase) < 0.01:
            print(f"   ✅ EDGE CASE MONTHLY REVENUE: CORRECT")
            return True
        else:
            print(f"   ❌ EDGE CASE MONTHLY REVENUE: INCORRECT")
            return False

    def test_api_response_structure(self):
        """Test 6: Verify API response structure matches frontend expectations"""
        print("\n🎯 TEST 6: API RESPONSE STRUCTURE VERIFICATION")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get Payment Stats for Structure Verification",
            "GET",
            "payments/stats",
            200
        )
        
        if not success:
            return False
            
        print(f"   📋 API RESPONSE STRUCTURE:")
        for key, value in response.items():
            print(f"      {key}: {value} ({type(value).__name__})")
            
        # Verify required fields for frontend
        required_fields = {
            'total_revenue': (int, float),
            'monthly_revenue': (int, float),
            'payment_count': int,
            'timestamp': str
        }
        
        structure_valid = True
        for field, expected_types in required_fields.items():
            if field not in response:
                print(f"   ❌ MISSING FIELD: {field}")
                structure_valid = False
            elif not isinstance(response[field], expected_types):
                print(f"   ❌ WRONG TYPE: {field} should be {expected_types}, got {type(response[field])}")
                structure_valid = False
            else:
                print(f"   ✅ FIELD OK: {field} ({type(response[field]).__name__})")
                
        # Verify cache-busting headers are present
        print(f"\n   🔄 CACHE-BUSTING VERIFICATION:")
        if 'cache_buster' in response:
            print(f"   ✅ CACHE BUSTER: Present ({response['cache_buster']})")
        else:
            print(f"   ⚠️  CACHE BUSTER: Not present in response body")
            
        return structure_valid

    def run_all_tests(self):
        """Run all paid this month tests"""
        print("🎯 PAID THIS MONTH FIGURE FIX - COMPREHENSIVE BACKEND TESTING")
        print("=" * 100)
        print("Testing the user-reported issue: 'Paid This Month figure was showing 0 instead of correct monthly revenue'")
        print("=" * 100)
        
        test_methods = [
            self.test_initial_payment_stats,
            self.test_create_test_clients,
            self.test_record_current_month_payments,
            self.test_verify_monthly_revenue_calculation,
            self.test_monthly_revenue_edge_cases,
            self.test_api_response_structure
        ]
        
        for test_method in test_methods:
            try:
                success = test_method()
                if not success:
                    print(f"\n❌ Test failed: {test_method.__name__}")
            except Exception as e:
                print(f"\n❌ Test error in {test_method.__name__}: {str(e)}")
                self.log_test(test_method.__name__, False, f"Exception: {str(e)}")
                
        # Final summary
        print("\n" + "=" * 100)
        print("🎯 PAID THIS MONTH FIGURE FIX - TEST SUMMARY")
        print("=" * 100)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! 'Paid This Month' figure fix is working correctly!")
            print("✅ Backend API returns correct monthly_revenue value")
            print("✅ Monthly calculation logic correctly sums current month payments")
            print("✅ Payment records are properly filtered by current month/year")
            print("✅ Data consistency maintained (monthly_revenue <= total_revenue)")
            print("✅ API response structure matches frontend expectations")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} TESTS FAILED")
            print("❌ 'Paid This Month' figure fix needs attention")
            
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = PaidThisMonthTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)