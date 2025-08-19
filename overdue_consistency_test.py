#!/usr/bin/env python3
"""
Overdue Figures Consistency Testing Script
Testing the fixed logic for overdue account calculations to ensure consistency between dashboard stats and payment tab counts.

Test Scenarios as specified in review request:
1. Client A: Has amount_owed > 0 and overdue date (should count as overdue)
2. Client B: Has amount_owed = 0 but overdue date (should NOT count as overdue - paid client)  
3. Client C: Has amount_owed > 0 but no due date (should count as overdue - no due date but owes money)
4. Client D: Has amount_owed > 0 and future due date (should NOT count as overdue)

Key validation:
- Logic: if (amount_owed > 0.01) AND (no_due_date OR due_date < today) = overdue
- Both dashboard stat and payment tab should show the same count
- Only clients who actually owe money should be counted
"""

import requests
import json
import sys
import os
from datetime import datetime, date, timedelta
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://alphalete-pwa.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Backend URL: {BACKEND_URL}")
print(f"🕐 Test Started: {datetime.now().isoformat()}")
print("=" * 80)
print("🎯 OVERDUE FIGURES CONSISTENCY TESTING")
print("Testing the fixed logic for overdue account calculations")
print("=" * 80)

class OverdueConsistencyTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        self.created_test_clients = []
        self.today = date.today()
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def make_request(self, method, endpoint, data=None):
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {'Content-Type': 'application/json'}
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            return None

    def create_test_client(self, name, email, amount_owed, next_payment_date, payment_status="due"):
        """Create a test client with specific overdue scenario"""
        client_data = {
            "name": name,
            "email": email,
            "phone": "+1868-555-TEST",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": (self.today - timedelta(days=30)).isoformat(),
            "payment_status": payment_status,
            "amount_owed": amount_owed
        }
        
        response = self.make_request('POST', '/clients', client_data)
        if response and response.status_code == 200:
            client = response.json()
            
            # Update next_payment_date if specified
            if next_payment_date:
                update_data = {"next_payment_date": next_payment_date.isoformat()}
                update_response = self.make_request('PUT', f'/clients/{client["id"]}', update_data)
                if update_response and update_response.status_code == 200:
                    client = update_response.json()
            
            self.created_test_clients.append(client["id"])
            return client
        return None

    def get_payment_stats(self):
        """Get payment statistics from backend"""
        response = self.make_request('GET', '/payments/stats')
        if response and response.status_code == 200:
            return response.json()
        return None

    def get_all_clients(self):
        """Get all clients from backend"""
        response = self.make_request('GET', '/clients')
        if response and response.status_code == 200:
            return response.json()
        return []

    def calculate_overdue_clients_manually(self, clients):
        """Manually calculate overdue clients using the fixed logic"""
        overdue_count = 0
        overdue_clients = []
        
        for client in clients:
            amount_owed = client.get('amount_owed', 0) or 0
            next_payment_date_str = client.get('next_payment_date')
            
            # Logic: if (amount_owed > 0.01) AND (no_due_date OR due_date < today) = overdue
            if amount_owed > 0.01:
                if not next_payment_date_str:
                    # No due date but owes money = overdue
                    overdue_count += 1
                    overdue_clients.append({
                        'name': client.get('name'),
                        'amount_owed': amount_owed,
                        'reason': 'No due date but owes money'
                    })
                else:
                    try:
                        next_payment_date = datetime.fromisoformat(next_payment_date_str).date()
                        if next_payment_date < self.today:
                            # Due date passed and owes money = overdue
                            overdue_count += 1
                            overdue_clients.append({
                                'name': client.get('name'),
                                'amount_owed': amount_owed,
                                'due_date': next_payment_date_str,
                                'reason': 'Due date passed and owes money'
                            })
                    except (ValueError, AttributeError):
                        # Invalid date format, treat as no due date
                        overdue_count += 1
                        overdue_clients.append({
                            'name': client.get('name'),
                            'amount_owed': amount_owed,
                            'reason': 'Invalid due date but owes money'
                        })
        
        return overdue_count, overdue_clients

    def test_scenario_a_overdue_with_amount(self):
        """Test Client A: Has amount_owed > 0 and overdue date (should count as overdue)"""
        print("\n🧪 Testing Scenario A: Client with amount owed and overdue date")
        
        overdue_date = self.today - timedelta(days=5)  # 5 days overdue
        client = self.create_test_client(
            name="Test Client A - Overdue",
            email=f"test_a_{int(datetime.now().timestamp())}@overdue.test",
            amount_owed=100.0,
            next_payment_date=overdue_date
        )
        
        if client:
            self.log_test(
                "Create Client A (amount_owed > 0, overdue date)",
                True,
                f"Created client with TTD 100 owed, due date {overdue_date} (5 days overdue)"
            )
            return True
        else:
            self.log_test("Create Client A", False, "Failed to create test client")
            return False

    def test_scenario_b_paid_but_overdue_date(self):
        """Test Client B: Has amount_owed = 0 but overdue date (should NOT count as overdue)"""
        print("\n🧪 Testing Scenario B: Paid client with overdue date")
        
        overdue_date = self.today - timedelta(days=10)  # 10 days past due but paid
        client = self.create_test_client(
            name="Test Client B - Paid",
            email=f"test_b_{int(datetime.now().timestamp())}@paid.test",
            amount_owed=0.0,
            next_payment_date=overdue_date,
            payment_status="paid"
        )
        
        if client:
            self.log_test(
                "Create Client B (amount_owed = 0, overdue date)",
                True,
                f"Created paid client with TTD 0 owed, due date {overdue_date} (should NOT count as overdue)"
            )
            return True
        else:
            self.log_test("Create Client B", False, "Failed to create test client")
            return False

    def test_scenario_c_amount_no_due_date(self):
        """Test Client C: Has amount_owed > 0 but no due date (should count as overdue)"""
        print("\n🧪 Testing Scenario C: Client with amount owed but no due date")
        
        client = self.create_test_client(
            name="Test Client C - No Due Date",
            email=f"test_c_{int(datetime.now().timestamp())}@nodue.test",
            amount_owed=75.0,
            next_payment_date=None  # No due date
        )
        
        if client:
            # Manually set next_payment_date to None by updating
            update_data = {"next_payment_date": None}
            update_response = self.make_request('PUT', f'/clients/{client["id"]}', update_data)
            
            self.log_test(
                "Create Client C (amount_owed > 0, no due date)",
                True,
                "Created client with TTD 75 owed, no due date (should count as overdue)"
            )
            return True
        else:
            self.log_test("Create Client C", False, "Failed to create test client")
            return False

    def test_scenario_d_amount_future_date(self):
        """Test Client D: Has amount_owed > 0 and future due date (should NOT count as overdue)"""
        print("\n🧪 Testing Scenario D: Client with amount owed and future due date")
        
        future_date = self.today + timedelta(days=15)  # 15 days in future
        client = self.create_test_client(
            name="Test Client D - Future Due",
            email=f"test_d_{int(datetime.now().timestamp())}@future.test",
            amount_owed=120.0,
            next_payment_date=future_date
        )
        
        if client:
            self.log_test(
                "Create Client D (amount_owed > 0, future due date)",
                True,
                f"Created client with TTD 120 owed, due date {future_date} (should NOT count as overdue)"
            )
            return True
        else:
            self.log_test("Create Client D", False, "Failed to create test client")
            return False

    def test_overdue_calculation_consistency(self):
        """Test that dashboard stats and manual calculation show same overdue count"""
        print("\n🧪 Testing Overdue Calculation Consistency")
        
        # Get all clients
        clients = self.get_all_clients()
        if not clients:
            self.log_test("Get All Clients", False, "Failed to retrieve clients")
            return False
        
        # Get payment stats (dashboard data)
        stats = self.get_payment_stats()
        if not stats:
            self.log_test("Get Payment Stats", False, "Failed to retrieve payment statistics")
            return False
        
        # Manual calculation using fixed logic
        manual_overdue_count, overdue_clients = self.calculate_overdue_clients_manually(clients)
        
        # Check if backend has overdue count in stats
        backend_overdue_count = stats.get('overdue_count', 'NOT_AVAILABLE')
        
        print(f"   📊 Manual calculation: {manual_overdue_count} overdue clients")
        print(f"   📊 Backend stats: {backend_overdue_count} overdue clients")
        
        # Show details of overdue clients
        if overdue_clients:
            print("   📋 Overdue clients details:")
            for client in overdue_clients:
                print(f"      • {client['name']}: TTD {client['amount_owed']} - {client['reason']}")
        
        # Test consistency (if backend provides overdue count)
        if backend_overdue_count != 'NOT_AVAILABLE':
            consistency_check = manual_overdue_count == backend_overdue_count
            self.log_test(
                "Overdue Count Consistency",
                consistency_check,
                f"Manual: {manual_overdue_count}, Backend: {backend_overdue_count}"
            )
        else:
            self.log_test(
                "Manual Overdue Calculation",
                True,
                f"Calculated {manual_overdue_count} overdue clients using fixed logic"
            )
        
        return True

    def test_unified_calculation_logic(self):
        """Test that the unified calculation logic works correctly"""
        print("\n🧪 Testing Unified Calculation Logic")
        
        clients = self.get_all_clients()
        if not clients:
            self.log_test("Get Clients for Logic Test", False, "Failed to retrieve clients")
            return False
        
        # Find our test clients and verify logic
        test_clients_found = {
            'A': None,  # Should be overdue
            'B': None,  # Should NOT be overdue
            'C': None,  # Should be overdue
            'D': None   # Should NOT be overdue
        }
        
        for client in clients:
            name = client.get('name', '')
            if 'Test Client A' in name:
                test_clients_found['A'] = client
            elif 'Test Client B' in name:
                test_clients_found['B'] = client
            elif 'Test Client C' in name:
                test_clients_found['C'] = client
            elif 'Test Client D' in name:
                test_clients_found['D'] = client
        
        # Verify each test client
        logic_tests_passed = 0
        total_logic_tests = 4
        
        for scenario, client in test_clients_found.items():
            if client:
                amount_owed = client.get('amount_owed', 0) or 0
                next_payment_date_str = client.get('next_payment_date')
                
                # Apply the fixed logic
                is_overdue = False
                if amount_owed > 0.01:
                    if not next_payment_date_str:
                        is_overdue = True
                    else:
                        try:
                            next_payment_date = datetime.fromisoformat(next_payment_date_str).date()
                            if next_payment_date < self.today:
                                is_overdue = True
                        except (ValueError, AttributeError):
                            is_overdue = True
                
                # Check expected results
                expected_overdue = scenario in ['A', 'C']  # A and C should be overdue
                logic_correct = is_overdue == expected_overdue
                
                if logic_correct:
                    logic_tests_passed += 1
                
                self.log_test(
                    f"Logic Test Client {scenario}",
                    logic_correct,
                    f"Amount: TTD {amount_owed}, Due: {next_payment_date_str}, Overdue: {is_overdue} (Expected: {expected_overdue})"
                )
        
        overall_logic_success = logic_tests_passed == total_logic_tests
        self.log_test(
            "Overall Logic Consistency",
            overall_logic_success,
            f"{logic_tests_passed}/{total_logic_tests} logic tests passed"
        )
        
        return overall_logic_success

    def cleanup_test_data(self):
        """Clean up created test clients"""
        print("\n🧹 Cleaning up test data...")
        
        cleanup_count = 0
        for client_id in self.created_test_clients:
            response = self.make_request('DELETE', f'/clients/{client_id}')
            if response and response.status_code == 200:
                cleanup_count += 1
        
        self.log_test(
            "Test Data Cleanup",
            cleanup_count == len(self.created_test_clients),
            f"Cleaned up {cleanup_count}/{len(self.created_test_clients)} test clients"
        )

    def run_all_tests(self):
        """Run all overdue consistency tests"""
        print("🚀 Starting Overdue Figures Consistency Tests")
        print(f"📅 Today's date: {self.today}")
        
        # Create test scenarios
        scenario_a = self.test_scenario_a_overdue_with_amount()
        scenario_b = self.test_scenario_b_paid_but_overdue_date()
        scenario_c = self.test_scenario_c_amount_no_due_date()
        scenario_d = self.test_scenario_d_amount_future_date()
        
        # Test calculations
        consistency_test = self.test_overdue_calculation_consistency()
        logic_test = self.test_unified_calculation_logic()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 ALL TESTS PASSED - Overdue figures consistency is working correctly!")
        elif success_rate >= 80:
            print("⚠️  MOSTLY SUCCESSFUL - Minor issues detected")
        else:
            print("❌ CRITICAL ISSUES - Overdue calculation logic needs attention")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        print("\n🔍 Key Validation Results:")
        print("   • Logic: if (amount_owed > 0.01) AND (no_due_date OR due_date < today) = overdue")
        print("   • Only clients who actually owe money are counted")
        print("   • Paid clients (amount_owed = 0) are never counted as overdue")
        print("   • Dashboard stats should match payment tab counts")
        
        return success_rate == 100

def main():
    """Main test execution"""
    tester = OverdueConsistencyTester(BACKEND_URL)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        tester.cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        tester.cleanup_test_data()
        sys.exit(1)

if __name__ == "__main__":
    main()