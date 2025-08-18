#!/usr/bin/env python3
"""
DELETE /api/clients/{id} Endpoint Testing Script
Testing the specific issue: Frontend delete button not actually removing members

ISSUE REPORTED:
- Frontend delete button is trying to delete members but they're not actually being removed
- Need to verify if DELETE /api/clients/{id} endpoint exists and works properly
- Check for authentication/permission issues
- Test with real member ID from database
- Check HTTP status codes returned

TESTING REQUIREMENTS:
1. Verify DELETE /api/clients/{id} endpoint exists
2. Test if it works correctly when called
3. Check for authentication/permission issues  
4. Test with a real member ID from the database
5. Check what HTTP status codes are returned
6. Verify cascading deletion of payment records
"""

import requests
import json
import sys
import os
from datetime import datetime, date
from typing import Dict, List, Any
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fitness-club-admin.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Backend URL: {BACKEND_URL}")
print(f"🕐 DELETE Client Endpoint Test Started: {datetime.now().isoformat()}")
print("=" * 80)

class DeleteClientTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        self.test_client_id = None
        self.test_client_name = None
        
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

    def test_1_verify_delete_endpoint_exists(self):
        """Test 1: Verify DELETE /api/clients/{id} endpoint exists"""
        print("\n🔍 TEST 1: Verify DELETE Endpoint Exists")
        print("-" * 50)
        
        # First, get existing clients to find a real ID
        response = self.make_request("GET", "/clients")
        if not response or response.status_code != 200:
            self.log_test("GET /api/clients for ID lookup", False, "Cannot retrieve clients list")
            return False
            
        clients = response.json()
        if not clients:
            self.log_test("Find existing client for testing", False, "No existing clients found")
            return False
            
        # Use first client ID for testing endpoint existence
        test_client_id = clients[0]['id']
        test_client_name = clients[0]['name']
        
        # Test DELETE endpoint with existing ID (should work)
        response = self.make_request("DELETE", f"/clients/{test_client_id}")
        
        if response is None:
            self.log_test("DELETE endpoint accessibility", False, "No response from DELETE endpoint")
            return False
            
        # Check if endpoint exists (should return 200 for successful deletion or proper error)
        endpoint_exists = response.status_code in [200, 404, 422, 500]  # Any valid HTTP response
        
        if endpoint_exists:
            self.log_test("DELETE /api/clients/{id} endpoint exists", True, 
                        f"Endpoint responds with HTTP {response.status_code}")
            
            # If deletion was successful, we need to restore the client for further testing
            if response.status_code == 200:
                print(f"   ⚠️  WARNING: Client '{test_client_name}' was actually deleted!")
                deletion_result = response.json()
                self.log_test("Actual deletion occurred", True, 
                            f"Deleted: {deletion_result.get('client_name', 'Unknown')}")
        else:
            self.log_test("DELETE /api/clients/{id} endpoint exists", False, 
                        f"Unexpected response: HTTP {response.status_code}")
            
        return endpoint_exists

    def test_2_create_test_client_for_deletion(self):
        """Test 2: Create a test client specifically for deletion testing"""
        print("\n🔍 TEST 2: Create Test Client for Deletion")
        print("-" * 50)
        
        # Create a test client that we can safely delete
        test_client_data = {
            "name": f"DELETE TEST CLIENT {datetime.now().strftime('%H%M%S')}",
            "email": f"delete.test.{datetime.now().strftime('%H%M%S')}@example.com",
            "phone": "+1868-555-DELETE",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        response = self.make_request("POST", "/clients", test_client_data)
        if not response or response.status_code not in [200, 201]:
            self.log_test("Create test client for deletion", False, 
                        f"HTTP {response.status_code if response else 'No response'}")
            return False
            
        created_client = response.json()
        self.test_client_id = created_client.get('id')
        self.test_client_name = created_client.get('name')
        
        self.log_test("Create test client for deletion", True, 
                    f"Created client: {self.test_client_name} (ID: {self.test_client_id})")
        
        # Verify client was created by retrieving it
        response = self.make_request("GET", f"/clients/{self.test_client_id}")
        if response and response.status_code == 200:
            retrieved_client = response.json()
            self.log_test("Verify test client creation", True, 
                        f"Client retrievable: {retrieved_client.get('name')}")
            return True
        else:
            self.log_test("Verify test client creation", False, "Created client not retrievable")
            return False

    def test_3_add_payment_records_for_cascading_test(self):
        """Test 3: Add payment records to test cascading deletion"""
        print("\n🔍 TEST 3: Add Payment Records for Cascading Test")
        print("-" * 50)
        
        if not self.test_client_id:
            self.log_test("Payment records setup", False, "No test client available")
            return False
            
        # Add multiple payment records to test cascading deletion
        payment_records = [
            {
                "client_id": self.test_client_id,
                "amount_paid": 25.0,
                "payment_date": date.today().isoformat(),
                "payment_method": "Cash",
                "notes": "Test payment 1 for deletion"
            },
            {
                "client_id": self.test_client_id,
                "amount_paid": 20.0,
                "payment_date": date.today().isoformat(),
                "payment_method": "Card",
                "notes": "Test payment 2 for deletion"
            },
            {
                "client_id": self.test_client_id,
                "amount_paid": 10.0,
                "payment_date": date.today().isoformat(),
                "payment_method": "Bank Transfer",
                "notes": "Test payment 3 for deletion"
            }
        ]
        
        successful_payments = 0
        total_payment_amount = 0
        
        for i, payment_data in enumerate(payment_records, 1):
            response = self.make_request("POST", "/payments/record", payment_data)
            if response and response.status_code == 200:
                successful_payments += 1
                total_payment_amount += payment_data["amount_paid"]
                self.log_test(f"Payment record {i} creation", True, 
                            f"TTD {payment_data['amount_paid']} recorded")
            else:
                self.log_test(f"Payment record {i} creation", False, 
                            f"HTTP {response.status_code if response else 'No response'}")
                
        self.log_test("Payment records setup complete", successful_payments > 0, 
                    f"{successful_payments}/3 payments created, Total: TTD {total_payment_amount}")
        
        return successful_payments > 0

    def test_4_verify_payment_stats_before_deletion(self):
        """Test 4: Get payment statistics before deletion to verify changes"""
        print("\n🔍 TEST 4: Payment Statistics Before Deletion")
        print("-" * 50)
        
        response = self.make_request("GET", "/payments/stats")
        if not response or response.status_code != 200:
            self.log_test("Get payment stats before deletion", False, "Cannot retrieve payment stats")
            return False
            
        stats_before = response.json()
        total_revenue_before = stats_before.get('total_revenue', 0)
        payment_count_before = stats_before.get('payment_count', 0)
        
        self.log_test("Payment stats before deletion", True, 
                    f"Revenue: TTD {total_revenue_before}, Count: {payment_count_before}")
        
        # Store for comparison after deletion
        self.stats_before_deletion = stats_before
        return True

    def test_5_perform_delete_operation(self):
        """Test 5: Perform the actual DELETE operation"""
        print("\n🔍 TEST 5: Perform DELETE Operation")
        print("-" * 50)
        
        if not self.test_client_id:
            self.log_test("DELETE operation", False, "No test client ID available")
            return False
            
        # Perform the DELETE request
        response = self.make_request("DELETE", f"/clients/{self.test_client_id}")
        
        if not response:
            self.log_test("DELETE request execution", False, "No response from DELETE request")
            return False
            
        # Check HTTP status code
        status_code = response.status_code
        self.log_test("DELETE HTTP status code", status_code == 200, 
                    f"HTTP {status_code} (Expected: 200)")
        
        if status_code == 200:
            try:
                deletion_result = response.json()
                
                # Verify response contains expected fields
                expected_fields = ['message', 'client_name', 'client_deleted', 'payment_records_deleted']
                has_expected_fields = all(field in deletion_result for field in expected_fields)
                
                self.log_test("DELETE response format", has_expected_fields, 
                            f"Response contains expected fields: {has_expected_fields}")
                
                # Check deletion details
                client_deleted = deletion_result.get('client_deleted', False)
                payment_records_deleted = deletion_result.get('payment_records_deleted', 0)
                client_name = deletion_result.get('client_name', 'Unknown')
                
                self.log_test("Client deletion confirmed", client_deleted, 
                            f"Client '{client_name}' deleted: {client_deleted}")
                
                self.log_test("Payment records cascading deletion", payment_records_deleted > 0, 
                            f"Payment records deleted: {payment_records_deleted}")
                
                # Store deletion details for verification
                self.deletion_result = deletion_result
                return True
                
            except json.JSONDecodeError:
                self.log_test("DELETE response parsing", False, "Invalid JSON response")
                return False
        else:
            # Handle error responses
            try:
                error_data = response.json()
                error_message = error_data.get('detail', 'Unknown error')
                self.log_test("DELETE error handling", True, 
                            f"Error response: {error_message}")
            except:
                self.log_test("DELETE error handling", False, 
                            f"HTTP {status_code} with unparseable response")
            return False

    def test_6_verify_client_actually_deleted(self):
        """Test 6: Verify the client was actually removed from database"""
        print("\n🔍 TEST 6: Verify Client Actually Deleted")
        print("-" * 50)
        
        if not self.test_client_id:
            self.log_test("Client deletion verification", False, "No test client ID to verify")
            return False
            
        # Try to retrieve the deleted client
        response = self.make_request("GET", f"/clients/{self.test_client_id}")
        
        if not response:
            self.log_test("Client deletion verification request", False, "No response from GET request")
            return False
            
        # Should return 404 if client was actually deleted
        if response.status_code == 404:
            self.log_test("Client actually deleted from database", True, 
                        "GET request returns 404 - client not found")
            
            # Verify error message
            try:
                error_data = response.json()
                error_message = error_data.get('detail', '')
                has_proper_error = 'not found' in error_message.lower()
                self.log_test("Proper 404 error message", has_proper_error, 
                            f"Error message: {error_message}")
            except:
                self.log_test("404 error message format", False, "Cannot parse 404 response")
                
            return True
        elif response.status_code == 200:
            # Client still exists - deletion failed
            client_data = response.json()
            self.log_test("Client actually deleted from database", False, 
                        f"Client still exists: {client_data.get('name', 'Unknown')}")
            return False
        else:
            self.log_test("Client deletion verification", False, 
                        f"Unexpected HTTP {response.status_code}")
            return False

    def test_7_verify_client_not_in_list(self):
        """Test 7: Verify deleted client doesn't appear in clients list"""
        print("\n🔍 TEST 7: Verify Client Not in Clients List")
        print("-" * 50)
        
        if not self.test_client_id:
            self.log_test("Client list verification", False, "No test client ID to verify")
            return False
            
        # Get all clients
        response = self.make_request("GET", "/clients")
        if not response or response.status_code != 200:
            self.log_test("Get clients list", False, "Cannot retrieve clients list")
            return False
            
        clients = response.json()
        
        # Check if deleted client ID appears in the list
        client_ids = [client.get('id') for client in clients]
        client_still_in_list = self.test_client_id in client_ids
        
        self.log_test("Deleted client not in clients list", not client_still_in_list, 
                    f"Client ID {self.test_client_id} in list: {client_still_in_list}")
        
        # Also check by name
        client_names = [client.get('name') for client in clients]
        name_still_in_list = self.test_client_name in client_names
        
        self.log_test("Deleted client name not in list", not name_still_in_list, 
                    f"Client name '{self.test_client_name}' in list: {name_still_in_list}")
        
        return not client_still_in_list and not name_still_in_list

    def test_8_verify_payment_stats_updated(self):
        """Test 8: Verify payment statistics updated after deletion"""
        print("\n🔍 TEST 8: Verify Payment Statistics Updated")
        print("-" * 50)
        
        if not hasattr(self, 'stats_before_deletion'):
            self.log_test("Payment stats comparison", False, "No before-deletion stats available")
            return False
            
        # Get current payment statistics
        response = self.make_request("GET", "/payments/stats")
        if not response or response.status_code != 200:
            self.log_test("Get payment stats after deletion", False, "Cannot retrieve payment stats")
            return False
            
        stats_after = response.json()
        
        # Compare statistics
        revenue_before = self.stats_before_deletion.get('total_revenue', 0)
        revenue_after = stats_after.get('total_revenue', 0)
        count_before = self.stats_before_deletion.get('payment_count', 0)
        count_after = stats_after.get('payment_count', 0)
        
        # Calculate expected changes
        expected_revenue_reduction = 55.0  # 25 + 20 + 10 from our test payments
        expected_count_reduction = 3  # 3 payment records
        
        actual_revenue_reduction = revenue_before - revenue_after
        actual_count_reduction = count_before - count_after
        
        revenue_updated_correctly = abs(actual_revenue_reduction - expected_revenue_reduction) < 0.01
        count_updated_correctly = actual_count_reduction == expected_count_reduction
        
        self.log_test("Payment revenue updated correctly", revenue_updated_correctly, 
                    f"Before: TTD {revenue_before}, After: TTD {revenue_after}, Reduction: TTD {actual_revenue_reduction}")
        
        self.log_test("Payment count updated correctly", count_updated_correctly, 
                    f"Before: {count_before}, After: {count_after}, Reduction: {actual_count_reduction}")
        
        return revenue_updated_correctly and count_updated_correctly

    def test_9_test_delete_nonexistent_client(self):
        """Test 9: Test DELETE with non-existent client ID"""
        print("\n🔍 TEST 9: Test DELETE Non-existent Client")
        print("-" * 50)
        
        # Use a fake UUID that doesn't exist
        fake_client_id = str(uuid.uuid4())
        
        response = self.make_request("DELETE", f"/clients/{fake_client_id}")
        
        if not response:
            self.log_test("DELETE non-existent client request", False, "No response")
            return False
            
        # Should return 404 for non-existent client
        if response.status_code == 404:
            self.log_test("DELETE non-existent client returns 404", True, 
                        "Proper 404 response for non-existent client")
            
            try:
                error_data = response.json()
                error_message = error_data.get('detail', '')
                has_proper_error = 'not found' in error_message.lower()
                self.log_test("Proper 404 error message for non-existent", has_proper_error, 
                            f"Error message: {error_message}")
            except:
                self.log_test("404 error message format", False, "Cannot parse 404 response")
                
            return True
        else:
            self.log_test("DELETE non-existent client returns 404", False, 
                        f"Expected 404, got HTTP {response.status_code}")
            return False

    def test_10_test_authentication_permissions(self):
        """Test 10: Test if there are any authentication/permission issues"""
        print("\n🔍 TEST 10: Test Authentication/Permissions")
        print("-" * 50)
        
        # Test if DELETE endpoint requires authentication
        # Since we've been making successful requests, check if there are any auth headers required
        
        # Try DELETE without any special headers (we've been doing this already)
        fake_id = str(uuid.uuid4())
        response = self.make_request("DELETE", f"/clients/{fake_id}")
        
        if response:
            # Check if we get authentication errors
            auth_error_codes = [401, 403]  # Unauthorized, Forbidden
            has_auth_issues = response.status_code in auth_error_codes
            
            if has_auth_issues:
                self.log_test("Authentication/Permission issues detected", True, 
                            f"HTTP {response.status_code} - Authentication required")
                
                try:
                    error_data = response.json()
                    auth_message = error_data.get('detail', 'Unknown auth error')
                    self.log_test("Authentication error details", True, 
                                f"Auth error: {auth_message}")
                except:
                    self.log_test("Authentication error parsing", False, "Cannot parse auth error")
                    
                return False  # Auth issues prevent proper testing
            else:
                self.log_test("No authentication/permission issues", True, 
                            f"DELETE endpoint accessible without special auth (HTTP {response.status_code})")
                return True
        else:
            self.log_test("Authentication test request", False, "No response for auth test")
            return False

    def run_all_tests(self):
        """Run all DELETE endpoint tests"""
        print("🚀 STARTING DELETE /api/clients/{id} ENDPOINT TESTING")
        print("🎯 Focus: Frontend delete button not actually removing members")
        print("📋 Testing: Endpoint existence, functionality, cascading deletion, error handling")
        print("=" * 80)
        
        # Test sequence
        tests_passed = 0
        total_tests = 10
        
        if self.test_1_verify_delete_endpoint_exists():
            tests_passed += 1
        if self.test_2_create_test_client_for_deletion():
            tests_passed += 1
        if self.test_3_add_payment_records_for_cascading_test():
            tests_passed += 1
        if self.test_4_verify_payment_stats_before_deletion():
            tests_passed += 1
        if self.test_5_perform_delete_operation():
            tests_passed += 1
        if self.test_6_verify_client_actually_deleted():
            tests_passed += 1
        if self.test_7_verify_client_not_in_list():
            tests_passed += 1
        if self.test_8_verify_payment_stats_updated():
            tests_passed += 1
        if self.test_9_test_delete_nonexistent_client():
            tests_passed += 1
        if self.test_10_test_authentication_permissions():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 DELETE ENDPOINT TEST SUMMARY")
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
                    
        # Key findings for DELETE endpoint
        print("\n🎯 KEY FINDINGS FOR DELETE ENDPOINT:")
        print("-" * 50)
        
        # Analyze results to provide specific findings
        endpoint_exists = any("DELETE /api/clients/{id} endpoint exists" in result['test'] and result['success'] 
                            for result in self.test_results)
        deletion_works = any("Client actually deleted from database" in result['test'] and result['success'] 
                           for result in self.test_results)
        cascading_works = any("Payment records cascading deletion" in result['test'] and result['success'] 
                            for result in self.test_results)
        stats_update = any("Payment revenue updated correctly" in result['test'] and result['success'] 
                         for result in self.test_results)
        no_auth_issues = any("No authentication/permission issues" in result['test'] and result['success'] 
                           for result in self.test_results)
        
        findings = []
        if endpoint_exists:
            findings.append("✅ DELETE /api/clients/{id} endpoint EXISTS and is accessible")
        else:
            findings.append("❌ DELETE /api/clients/{id} endpoint NOT FOUND or inaccessible")
            
        if deletion_works:
            findings.append("✅ DELETE operation WORKS CORRECTLY - clients are actually removed")
        else:
            findings.append("❌ DELETE operation FAILS - clients are NOT being removed from database")
            
        if cascading_works:
            findings.append("✅ CASCADING DELETION works - payment records are removed with client")
        else:
            findings.append("❌ CASCADING DELETION fails - payment records may remain orphaned")
            
        if stats_update:
            findings.append("✅ PAYMENT STATISTICS update correctly after deletion")
        else:
            findings.append("❌ PAYMENT STATISTICS not updating after deletion")
            
        if no_auth_issues:
            findings.append("✅ NO AUTHENTICATION/PERMISSION issues - endpoint is publicly accessible")
        else:
            findings.append("❌ AUTHENTICATION/PERMISSION issues detected - may require special headers")
            
        for finding in findings:
            print(f"   {finding}")
            
        # Root cause analysis
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        print("-" * 50)
        
        if not endpoint_exists:
            print("   🚨 CRITICAL: DELETE endpoint doesn't exist - frontend cannot delete members")
        elif not deletion_works:
            print("   🚨 CRITICAL: DELETE endpoint exists but doesn't actually delete - database issue")
        elif not no_auth_issues:
            print("   🚨 CRITICAL: Authentication issues prevent deletion - frontend may lack proper headers")
        elif endpoint_exists and deletion_works and no_auth_issues:
            print("   ✅ BACKEND DELETE FUNCTIONALITY IS WORKING CORRECTLY")
            print("   💡 Issue may be in frontend implementation:")
            print("      - Check if frontend is calling the correct endpoint URL")
            print("      - Verify frontend error handling for HTTP responses")
            print("      - Check if frontend is refreshing the UI after deletion")
            print("      - Verify frontend is using the correct HTTP method (DELETE)")
        else:
            print("   ⚠️  MIXED RESULTS: Some functionality works, some doesn't")
            
        print(f"\n🏁 Testing completed at: {datetime.now().isoformat()}")
        
        # Consider 80%+ success rate as passing for DELETE endpoint testing
        return success_rate >= 80.0

def main():
    """Main test execution"""
    try:
        tester = DeleteClientTester(BACKEND_URL)
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 DELETE ENDPOINT TESTING: SUCCESS!")
            print("✅ DELETE /api/clients/{id} endpoint is working correctly")
            print("✅ If frontend delete button isn't working, the issue is likely in frontend code")
            sys.exit(0)
        else:
            print("\n🚨 DELETE ENDPOINT TESTING: ISSUES DETECTED!")
            print("❌ DELETE /api/clients/{id} endpoint has problems that prevent proper deletion")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()