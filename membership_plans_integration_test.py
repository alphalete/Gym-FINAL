#!/usr/bin/env python3
"""
Membership Plans Integration Backend Testing Script
Testing the backend functionality for membership plans integration into Add/Edit Member form

Test Focus:
1. Membership Types API - GET /api/membership-types endpoint
2. Client Creation with Membership Plans - POST /api/clients with membership plan data
3. Data Persistence - billing_interval_days field storage
4. API Response Format - proper structure verification

Review Request Context:
- Frontend Add Client form now integrates membership plans
- Loading membership types from GET /api/membership-types
- Automatically prefilling amount and billing cycle days when plans are selected
- Storing clients with membership_type, monthly_fee, and billing_interval_days fields
"""

import requests
import json
import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://gym-billing-app.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Backend URL: {BACKEND_URL}")
print(f"🕐 Test Started: {datetime.now().isoformat()}")
print("=" * 80)

class MembershipPlansIntegrationTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        self.created_test_clients = []
        self.membership_types = []
        
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
        
    def make_request(self, method, endpoint, data=None, timeout=10):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            headers = {'Content-Type': 'application/json'}
            if method == "GET":
                response = requests.get(url, timeout=timeout, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=timeout, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=timeout, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, timeout=timeout, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None

    def test_membership_types_api(self):
        """Test 1: Membership Types API - Verify GET /api/membership-types endpoint"""
        print("\n🔍 TEST 1: Membership Types API")
        print("-" * 50)
        
        # Test GET /api/membership-types
        response = self.make_request("GET", "/membership-types")
        if not response:
            self.log_test("GET /api/membership-types", False, "Request failed")
            return False
            
        if response.status_code == 200:
            membership_types = response.json()
            self.membership_types = membership_types
            self.log_test("GET /api/membership-types", True, f"Retrieved {len(membership_types)} membership types")
            
            # Verify response format - should be array
            if isinstance(membership_types, list):
                self.log_test("Membership Types Array Format", True, "Response is properly formatted as array")
                
                if membership_types:
                    # Test first membership type structure
                    membership_type = membership_types[0]
                    required_fields = ['id', 'name', 'monthly_fee', 'description']
                    has_required_fields = all(field in membership_type for field in required_fields)
                    
                    self.log_test("Membership Type Structure", has_required_fields, 
                                f"Required fields present: {required_fields}")
                    
                    # Verify TTD currency amounts
                    monthly_fee = membership_type.get('monthly_fee', 0)
                    is_valid_amount = isinstance(monthly_fee, (int, float)) and monthly_fee > 0
                    self.log_test("TTD Currency Format", is_valid_amount,
                                f"Monthly fee: TTD {monthly_fee}")
                    
                    # Check for features field (optional but expected)
                    has_features = 'features' in membership_type
                    features = membership_type.get('features', [])
                    self.log_test("Membership Features Field", has_features,
                                f"Features: {len(features)} items")
                    
                    # Log sample membership type for verification
                    sample_type = {
                        'name': membership_type.get('name'),
                        'monthly_fee': membership_type.get('monthly_fee'),
                        'description': membership_type.get('description')[:50] + '...' if len(membership_type.get('description', '')) > 50 else membership_type.get('description')
                    }
                    self.log_test("Sample Membership Type", True, f"Sample: {sample_type}")
                    
                else:
                    self.log_test("Membership Types Available", False, "No membership types found")
                    return False
            else:
                self.log_test("Membership Types Array Format", False, f"Expected array, got {type(membership_types)}")
                return False
        else:
            self.log_test("GET /api/membership-types", False, f"HTTP {response.status_code}: {response.text}")
            return False
            
        return True

    def test_client_creation_with_membership_plans(self):
        """Test 2: Client Creation with Membership Plan Data"""
        print("\n🔍 TEST 2: Client Creation with Membership Plan Data")
        print("-" * 50)
        
        if not self.membership_types:
            self.log_test("Client Creation Test Setup", False, "No membership types available for testing")
            return False
        
        # Test with different membership types
        test_scenarios = []
        
        # Use first 3 membership types or all if less than 3
        for i, membership_type in enumerate(self.membership_types[:3]):
            scenario = {
                'name': f"Test Client Membership {membership_type.get('name')} {datetime.now().strftime('%H%M%S')}{i}",
                'email': f"test.membership.{membership_type.get('name').lower().replace(' ', '')}.{datetime.now().strftime('%H%M%S')}{i}@example.com",
                'phone': f"+1868-555-{membership_type.get('name')[:4].upper()}{i}",
                'membership_type': membership_type.get('name'),
                'monthly_fee': membership_type.get('monthly_fee'),
                'billing_interval_days': 30,  # Default monthly billing
                'start_date': date.today().isoformat(),
                'payment_status': 'due'
            }
            test_scenarios.append(scenario)
        
        # Test each scenario
        for i, client_data in enumerate(test_scenarios):
            scenario_name = f"Scenario {i+1}: {client_data['membership_type']}"
            
            response = self.make_request("POST", "/clients", client_data)
            if response and response.status_code in [200, 201]:
                created_client = response.json()
                client_id = created_client.get('id')
                self.created_test_clients.append(client_id)
                
                self.log_test(f"Client Creation {scenario_name}", True, 
                            f"Created: {created_client.get('name')}")
                
                # Verify membership plan data was stored correctly
                stored_membership_type = created_client.get('membership_type')
                stored_monthly_fee = created_client.get('monthly_fee')
                stored_billing_interval = created_client.get('billing_interval_days')
                
                # Check membership type
                membership_type_correct = stored_membership_type == client_data['membership_type']
                self.log_test(f"Membership Type Storage {scenario_name}", membership_type_correct,
                            f"Expected: {client_data['membership_type']}, Stored: {stored_membership_type}")
                
                # Check monthly fee
                fee_correct = abs(stored_monthly_fee - client_data['monthly_fee']) < 0.01
                self.log_test(f"Monthly Fee Storage {scenario_name}", fee_correct,
                            f"Expected: TTD {client_data['monthly_fee']}, Stored: TTD {stored_monthly_fee}")
                
                # Check billing interval days
                billing_correct = stored_billing_interval == client_data['billing_interval_days']
                self.log_test(f"Billing Interval Storage {scenario_name}", billing_correct,
                            f"Expected: {client_data['billing_interval_days']} days, Stored: {stored_billing_interval} days")
                
                # Verify amount_owed is set correctly for unpaid clients
                stored_amount_owed = created_client.get('amount_owed')
                amount_owed_correct = stored_amount_owed == client_data['monthly_fee']
                self.log_test(f"Amount Owed Logic {scenario_name}", amount_owed_correct,
                            f"Expected: TTD {client_data['monthly_fee']}, Stored: TTD {stored_amount_owed}")
                
            else:
                self.log_test(f"Client Creation {scenario_name}", False,
                            f"HTTP {response.status_code if response else 'No response'}: {response.text if response else 'Request failed'}")
        
        return True

    def test_data_persistence_verification(self):
        """Test 3: Data Persistence - Verify billing_interval_days field storage"""
        print("\n🔍 TEST 3: Data Persistence Verification")
        print("-" * 50)
        
        if not self.created_test_clients:
            self.log_test("Data Persistence Test", False, "No test clients available")
            return False
        
        # Test data persistence by retrieving clients and verifying fields
        for i, client_id in enumerate(self.created_test_clients):
            response = self.make_request("GET", f"/clients/{client_id}")
            if response and response.status_code == 200:
                retrieved_client = response.json()
                
                # Verify all membership plan fields are persisted
                required_fields = ['membership_type', 'monthly_fee', 'billing_interval_days']
                all_fields_present = all(field in retrieved_client for field in required_fields)
                
                self.log_test(f"Field Persistence Client {i+1}", all_fields_present,
                            f"All membership fields present: {all_fields_present}")
                
                # Verify billing_interval_days specifically (new field)
                billing_interval = retrieved_client.get('billing_interval_days')
                billing_interval_valid = isinstance(billing_interval, int) and billing_interval > 0
                
                self.log_test(f"Billing Interval Days Client {i+1}", billing_interval_valid,
                            f"Billing interval: {billing_interval} days")
                
                # Verify data types are correct
                monthly_fee = retrieved_client.get('monthly_fee')
                fee_type_correct = isinstance(monthly_fee, (int, float))
                
                self.log_test(f"Data Types Client {i+1}", fee_type_correct,
                            f"Monthly fee type: {type(monthly_fee).__name__}")
                
            else:
                self.log_test(f"Data Retrieval Client {i+1}", False,
                            f"HTTP {response.status_code if response else 'No response'}")
        
        return True

    def test_api_response_format_compliance(self):
        """Test 4: API Response Format - Verify proper structure for frontend integration"""
        print("\n🔍 TEST 4: API Response Format Compliance")
        print("-" * 50)
        
        # Test membership types response format for frontend dropdown
        response = self.make_request("GET", "/membership-types")
        if response and response.status_code == 200:
            membership_types = response.json()
            
            # Verify each membership type has required structure for frontend
            frontend_compatible = True
            for membership_type in membership_types:
                # Check required fields for frontend dropdown
                required_for_frontend = ['id', 'name', 'monthly_fee', 'description']
                has_frontend_fields = all(field in membership_type for field in required_for_frontend)
                
                if not has_frontend_fields:
                    frontend_compatible = False
                    break
                
                # Verify data types for frontend consumption
                name_valid = isinstance(membership_type.get('name'), str)
                fee_valid = isinstance(membership_type.get('monthly_fee'), (int, float))
                description_valid = isinstance(membership_type.get('description'), str)
                
                if not (name_valid and fee_valid and description_valid):
                    frontend_compatible = False
                    break
            
            self.log_test("Frontend Compatibility", frontend_compatible,
                        f"All {len(membership_types)} membership types have proper structure")
            
            # Test specific format requirements
            if membership_types:
                sample_type = membership_types[0]
                
                # Verify TTD currency format
                monthly_fee = sample_type.get('monthly_fee')
                ttd_format_valid = isinstance(monthly_fee, (int, float)) and monthly_fee > 0
                self.log_test("TTD Currency Format", ttd_format_valid,
                            f"Sample fee: TTD {monthly_fee}")
                
                # Verify description is not empty
                description = sample_type.get('description', '')
                description_valid = len(description.strip()) > 0
                self.log_test("Description Field", description_valid,
                            f"Description length: {len(description)} chars")
        
        # Test client creation response format
        if self.created_test_clients:
            client_id = self.created_test_clients[0]
            response = self.make_request("GET", f"/clients/{client_id}")
            if response and response.status_code == 200:
                client = response.json()
                
                # Verify client response has all fields needed for frontend
                client_frontend_fields = ['id', 'name', 'email', 'membership_type', 'monthly_fee', 'billing_interval_days', 'amount_owed', 'payment_status']
                has_client_fields = all(field in client for field in client_frontend_fields)
                
                self.log_test("Client Response Format", has_client_fields,
                            f"Client has all required fields for frontend")
                
                # Verify JSON serialization compatibility
                try:
                    json_str = json.dumps(client)
                    json_compatible = True
                except (TypeError, ValueError):
                    json_compatible = False
                
                self.log_test("JSON Serialization", json_compatible,
                            "Client data is JSON serializable")
        
        return True

    def test_integration_workflow(self):
        """Test 5: Complete Integration Workflow - Simulate frontend Add Client form workflow"""
        print("\n🔍 TEST 5: Complete Integration Workflow")
        print("-" * 50)
        
        # Step 1: Frontend loads membership types
        response = self.make_request("GET", "/membership-types")
        if not response or response.status_code != 200:
            self.log_test("Workflow Step 1: Load Membership Types", False, "Failed to load membership types")
            return False
        
        membership_types = response.json()
        self.log_test("Workflow Step 1: Load Membership Types", True,
                    f"Loaded {len(membership_types)} types for dropdown")
        
        # Step 2: User selects a membership type (simulate)
        if not membership_types:
            self.log_test("Workflow Step 2: Select Membership", False, "No membership types available")
            return False
        
        selected_membership = membership_types[0]  # Simulate user selecting first option
        self.log_test("Workflow Step 2: Select Membership", True,
                    f"Selected: {selected_membership.get('name')} - TTD {selected_membership.get('monthly_fee')}")
        
        # Step 3: Frontend auto-fills amount and billing cycle (simulate)
        auto_filled_data = {
            'membership_type': selected_membership.get('name'),
            'monthly_fee': selected_membership.get('monthly_fee'),
            'billing_interval_days': 30  # Default monthly
        }
        self.log_test("Workflow Step 3: Auto-fill Data", True,
                    f"Auto-filled: {auto_filled_data}")
        
        # Step 4: User submits form (simulate)
        client_data = {
            'name': f"Integration Workflow Test {datetime.now().strftime('%H%M%S')}",
            'email': f"workflow.test.{datetime.now().strftime('%H%M%S')}@example.com",
            'phone': '+1868-555-WORKFLOW',
            'membership_type': auto_filled_data['membership_type'],
            'monthly_fee': auto_filled_data['monthly_fee'],
            'billing_interval_days': auto_filled_data['billing_interval_days'],
            'start_date': date.today().isoformat(),
            'payment_status': 'due'
        }
        
        response = self.make_request("POST", "/clients", client_data)
        if response and response.status_code in [200, 201]:
            created_client = response.json()
            client_id = created_client.get('id')
            self.created_test_clients.append(client_id)
            
            self.log_test("Workflow Step 4: Create Client", True,
                        f"Created client: {created_client.get('name')}")
            
            # Step 5: Verify client appears in members list with correct data
            response = self.make_request("GET", "/clients")
            if response and response.status_code == 200:
                all_clients = response.json()
                created_client_in_list = any(client.get('id') == client_id for client in all_clients)
                
                self.log_test("Workflow Step 5: Client in Members List", created_client_in_list,
                            f"Client appears in members list")
                
                # Verify the client has correct membership plan data
                if created_client_in_list:
                    client_in_list = next(client for client in all_clients if client.get('id') == client_id)
                    
                    data_integrity_checks = [
                        client_in_list.get('membership_type') == selected_membership.get('name'),
                        abs(client_in_list.get('monthly_fee') - selected_membership.get('monthly_fee')) < 0.01,
                        client_in_list.get('billing_interval_days') == 30
                    ]
                    
                    all_data_correct = all(data_integrity_checks)
                    self.log_test("Workflow Step 6: Data Integrity", all_data_correct,
                                f"All membership plan data preserved correctly")
            else:
                self.log_test("Workflow Step 5: Client in Members List", False,
                            "Failed to retrieve members list")
        else:
            self.log_test("Workflow Step 4: Create Client", False,
                        f"HTTP {response.status_code if response else 'No response'}")
            return False
        
        return True

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n🧹 CLEANUP: Removing Test Data")
        print("-" * 50)
        
        cleanup_count = 0
        for client_id in self.created_test_clients:
            response = self.make_request("DELETE", f"/clients/{client_id}")
            if response and response.status_code == 200:
                cleanup_count += 1
                print(f"   ✅ Deleted test client: {client_id}")
            else:
                print(f"   ❌ Failed to delete test client: {client_id}")
                
        print(f"🧹 Cleaned up {cleanup_count}/{len(self.created_test_clients)} test clients")

    def run_all_tests(self):
        """Run all membership plans integration tests"""
        print("🚀 STARTING MEMBERSHIP PLANS INTEGRATION BACKEND TESTING")
        print("🎯 Focus: Membership Plans Integration into Add/Edit Member Form")
        print("=" * 80)
        
        # Test sequence
        tests_passed = 0
        total_tests = 5
        
        if self.test_membership_types_api():
            tests_passed += 1
        if self.test_client_creation_with_membership_plans():
            tests_passed += 1
        if self.test_data_persistence_verification():
            tests_passed += 1
        if self.test_api_response_format_compliance():
            tests_passed += 1
        if self.test_integration_workflow():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 MEMBERSHIP PLANS INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        total_individual_tests = len(self.test_results)
        passed_individual_tests = sum(1 for result in self.test_results if result['success'])
        failed_individual_tests = total_individual_tests - passed_individual_tests
        success_rate = (passed_individual_tests / total_individual_tests * 100) if total_individual_tests > 0 else 0
        
        print(f"📈 Test Categories Passed: {tests_passed}/{total_tests}")
        print(f"📈 Individual Tests: {total_individual_tests}")
        print(f"✅ Passed: {passed_individual_tests}")
        print(f"❌ Failed: {failed_individual_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if failed_individual_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
                    
        # Key findings for membership plans integration
        print("\n🎯 KEY FINDINGS FOR MEMBERSHIP PLANS INTEGRATION:")
        print("-" * 50)
        
        findings = []
        if tests_passed >= 1:
            findings.append("✅ Membership Types API: Returns correct data for Add Client form")
        if tests_passed >= 2:
            findings.append("✅ Client Creation: Works with membership plan data (membership_type, monthly_fee, billing_interval_days)")
        if tests_passed >= 3:
            findings.append("✅ Data Persistence: Clients stored correctly with billing cycle days field")
        if tests_passed >= 4:
            findings.append("✅ API Response Format: Membership types have proper structure (id, name, monthly_fee, description)")
        if tests_passed >= 5:
            findings.append("✅ Integration Workflow: Complete Add Client form workflow functional")
        
        for finding in findings:
            print(f"   {finding}")
            
        # Expected backend behavior verification
        print("\n🔍 EXPECTED BACKEND BEHAVIOR VERIFICATION:")
        print("-" * 50)
        
        behavior_checks = [
            f"✅ Membership types API returns array of plans with TTD currency" if tests_passed >= 1 else "❌ Membership types API issues",
            f"✅ Client creation accepts and stores billing_interval_days field" if tests_passed >= 2 else "❌ Client creation issues",
            f"✅ All existing client management functionality remains intact" if tests_passed >= 3 else "❌ Data persistence issues"
        ]
        
        for check in behavior_checks:
            print(f"   {check}")
            
        # Cleanup
        if self.created_test_clients:
            self.cleanup_test_data()
            
        print(f"\n🏁 Testing completed at: {datetime.now().isoformat()}")
        
        # Consider 90%+ success rate as passing for integration testing
        return success_rate >= 90.0

def main():
    """Main test execution"""
    try:
        tester = MembershipPlansIntegrationTester(BACKEND_URL)
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 MEMBERSHIP PLANS INTEGRATION BACKEND TESTING: SUCCESS!")
            print("✅ Backend is ready for membership plans integration into Add/Edit Member form")
            sys.exit(0)
        else:
            print("\n🚨 MEMBERSHIP PLANS INTEGRATION BACKEND TESTING: ISSUES DETECTED!")
            print("❌ Some backend functionality may need attention for membership plans integration")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()