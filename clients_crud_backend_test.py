#!/usr/bin/env python3
"""
Clients CRUD Backend API Testing Script
Testing backend API functionality for members/clients CRUD operations

SPECIFIC TEST REQUIREMENTS:
1. Test GET /api/clients - should return list of all clients
2. Test POST /api/clients - create a new test client with name "Backend Test User", email "backendtest@example.com" 
3. Test PUT /api/clients/{id} - update the test client
4. Test DELETE /api/clients/{id} - delete the test client
5. Verify that after DELETE, the client no longer exists

Current client count should be 24. After creating and then deleting a test client, it should return to 24.
"""

import requests
import json
import sys
import os
from datetime import datetime, date
from typing import Dict, List, Any
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fitness-tracker-pwa.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Backend URL: {BACKEND_URL}")
print(f"🕐 Test Started: {datetime.now().isoformat()}")
print("=" * 80)

class ClientsCRUDTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        self.test_client_id = None
        self.initial_client_count = 0
        
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

    def test_1_get_clients_initial(self):
        """Test 1: GET /api/clients - should return list of all clients"""
        print("\n🔍 TEST 1: GET /api/clients - Initial Client Count")
        print("-" * 50)
        
        response = self.make_request("GET", "/clients")
        if not response:
            self.log_test("GET /api/clients", False, "Request failed")
            return False
            
        if response.status_code == 200:
            clients = response.json()
            self.initial_client_count = len(clients)
            self.log_test("GET /api/clients", True, f"Retrieved {self.initial_client_count} clients")
            
            # Verify response format
            if clients and isinstance(clients, list):
                client = clients[0]
                required_fields = ['id', 'name', 'email', 'membership_type', 'monthly_fee', 'status']
                has_required_fields = all(field in client for field in required_fields)
                self.log_test("Client Response Format", has_required_fields, 
                            f"Required fields present: {has_required_fields}")
                
                # Check if initial count matches expected (24)
                expected_count = 24
                count_matches = self.initial_client_count == expected_count
                self.log_test("Initial Client Count Check", count_matches,
                            f"Expected: {expected_count}, Actual: {self.initial_client_count}")
            else:
                self.log_test("Client Response Format", True, "No clients to verify format")
                
            return True
        else:
            self.log_test("GET /api/clients", False, f"HTTP {response.status_code}: {response.text}")
            return False

    def test_2_post_create_client(self):
        """Test 2: POST /api/clients - create a new test client with specific data"""
        print("\n🔍 TEST 2: POST /api/clients - Create Test Client")
        print("-" * 50)
        
        # Create test client with exact specifications from review request
        test_client_data = {
            "name": "Backend Test User",
            "email": "backendtest@example.com",
            "phone": "+1868-555-TEST",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        response = self.make_request("POST", "/clients", test_client_data)
        if not response:
            self.log_test("POST /api/clients", False, "Request failed")
            return False
            
        if response.status_code in [200, 201]:
            created_client = response.json()
            self.test_client_id = created_client.get('id')
            
            # Verify created client data
            name_correct = created_client.get('name') == "Backend Test User"
            email_correct = created_client.get('email') == "backendtest@example.com"
            
            self.log_test("POST /api/clients", True, 
                        f"Created client: {created_client.get('name')} (ID: {self.test_client_id})")
            self.log_test("Client Data Verification", name_correct and email_correct,
                        f"Name: {created_client.get('name')}, Email: {created_client.get('email')}")
            
            # Verify client count increased by 1
            response = self.make_request("GET", "/clients")
            if response and response.status_code == 200:
                current_clients = response.json()
                current_count = len(current_clients)
                count_increased = current_count == (self.initial_client_count + 1)
                
                self.log_test("Client Count After Creation", count_increased,
                            f"Initial: {self.initial_client_count}, Current: {current_count}")
            
            return True
        else:
            self.log_test("POST /api/clients", False, 
                        f"HTTP {response.status_code}: {response.text}")
            return False

    def test_3_get_specific_client(self):
        """Test 3: GET /api/clients/{id} - retrieve the created test client"""
        print("\n🔍 TEST 3: GET /api/clients/{id} - Retrieve Specific Client")
        print("-" * 50)
        
        if not self.test_client_id:
            self.log_test("GET /api/clients/{id}", False, "No test client ID available")
            return False
            
        response = self.make_request("GET", f"/clients/{self.test_client_id}")
        if not response:
            self.log_test("GET /api/clients/{id}", False, "Request failed")
            return False
            
        if response.status_code == 200:
            retrieved_client = response.json()
            
            # Verify it's the correct client
            name_correct = retrieved_client.get('name') == "Backend Test User"
            email_correct = retrieved_client.get('email') == "backendtest@example.com"
            id_correct = retrieved_client.get('id') == self.test_client_id
            
            self.log_test("GET /api/clients/{id}", True,
                        f"Retrieved client: {retrieved_client.get('name')}")
            self.log_test("Retrieved Client Data Verification", name_correct and email_correct and id_correct,
                        f"All data matches created client")
            
            return True
        else:
            self.log_test("GET /api/clients/{id}", False,
                        f"HTTP {response.status_code}: {response.text}")
            return False

    def test_4_put_update_client(self):
        """Test 4: PUT /api/clients/{id} - update the test client"""
        print("\n🔍 TEST 4: PUT /api/clients/{id} - Update Test Client")
        print("-" * 50)
        
        if not self.test_client_id:
            self.log_test("PUT /api/clients/{id}", False, "No test client ID available")
            return False
            
        # Update client data
        update_data = {
            "phone": "+1868-555-UPDATED",
            "monthly_fee": 65.0,
            "membership_type": "Premium"
        }
        
        response = self.make_request("PUT", f"/clients/{self.test_client_id}", update_data)
        if not response:
            self.log_test("PUT /api/clients/{id}", False, "Request failed")
            return False
            
        if response.status_code == 200:
            updated_client = response.json()
            
            # Verify updates were applied
            phone_updated = updated_client.get('phone') == "+1868-555-UPDATED"
            fee_updated = updated_client.get('monthly_fee') == 65.0
            membership_updated = updated_client.get('membership_type') == "Premium"
            
            # Verify original data is preserved
            name_preserved = updated_client.get('name') == "Backend Test User"
            email_preserved = updated_client.get('email') == "backendtest@example.com"
            
            self.log_test("PUT /api/clients/{id}", True,
                        f"Updated client: {updated_client.get('name')}")
            self.log_test("Update Data Verification", phone_updated and fee_updated and membership_updated,
                        f"Phone: {updated_client.get('phone')}, Fee: {updated_client.get('monthly_fee')}, Type: {updated_client.get('membership_type')}")
            self.log_test("Original Data Preservation", name_preserved and email_preserved,
                        f"Name and email preserved correctly")
            
            return True
        else:
            self.log_test("PUT /api/clients/{id}", False,
                        f"HTTP {response.status_code}: {response.text}")
            return False

    def test_5_delete_client(self):
        """Test 5: DELETE /api/clients/{id} - delete the test client"""
        print("\n🔍 TEST 5: DELETE /api/clients/{id} - Delete Test Client")
        print("-" * 50)
        
        if not self.test_client_id:
            self.log_test("DELETE /api/clients/{id}", False, "No test client ID available")
            return False
            
        response = self.make_request("DELETE", f"/clients/{self.test_client_id}")
        if not response:
            self.log_test("DELETE /api/clients/{id}", False, "Request failed")
            return False
            
        if response.status_code == 200:
            delete_result = response.json()
            
            # Verify deletion response
            client_deleted = delete_result.get('client_deleted', False)
            client_name = delete_result.get('client_name', '')
            
            self.log_test("DELETE /api/clients/{id}", True,
                        f"Deleted client: {client_name}")
            self.log_test("Deletion Response Verification", client_deleted,
                        f"Client deletion confirmed: {client_deleted}")
            
            return True
        else:
            self.log_test("DELETE /api/clients/{id}", False,
                        f"HTTP {response.status_code}: {response.text}")
            return False

    def test_6_verify_client_deleted(self):
        """Test 6: Verify that after DELETE, the client no longer exists"""
        print("\n🔍 TEST 6: Verify Client Deletion - Client Should Not Exist")
        print("-" * 50)
        
        if not self.test_client_id:
            self.log_test("Client Deletion Verification", False, "No test client ID available")
            return False
            
        # Try to retrieve the deleted client
        response = self.make_request("GET", f"/clients/{self.test_client_id}")
        
        if response and response.status_code == 404:
            self.log_test("Client Not Found After Deletion", True,
                        f"Client {self.test_client_id} correctly returns 404")
        elif response and response.status_code == 200:
            self.log_test("Client Not Found After Deletion", False,
                        f"Client {self.test_client_id} still exists after deletion")
            return False
        else:
            self.log_test("Client Not Found After Deletion", False,
                        f"Unexpected response: HTTP {response.status_code if response else 'No response'}")
            return False
            
        # Verify client count returned to original
        response = self.make_request("GET", "/clients")
        if response and response.status_code == 200:
            final_clients = response.json()
            final_count = len(final_clients)
            count_restored = final_count == self.initial_client_count
            
            self.log_test("Client Count After Deletion", count_restored,
                        f"Initial: {self.initial_client_count}, Final: {final_count}")
            
            # Verify the deleted client is not in the list
            deleted_client_in_list = any(client.get('id') == self.test_client_id for client in final_clients)
            self.log_test("Deleted Client Not In List", not deleted_client_in_list,
                        f"Deleted client not found in clients list")
            
            return count_restored and not deleted_client_in_list
        else:
            self.log_test("Final Client Count Check", False, "Could not retrieve final client list")
            return False

    def run_all_tests(self):
        """Run all CRUD tests in sequence"""
        print("🚀 STARTING CLIENTS CRUD BACKEND API TESTING")
        print("🎯 Focus: Backend API functionality for members/clients CRUD operations")
        print("📋 Testing: GET, POST, PUT, DELETE operations with data verification")
        print("=" * 80)
        
        # Test sequence - must run in order
        tests_passed = 0
        total_tests = 6
        
        if self.test_1_get_clients_initial():
            tests_passed += 1
        else:
            print("❌ Initial GET test failed - aborting remaining tests")
            return False
            
        if self.test_2_post_create_client():
            tests_passed += 1
        else:
            print("❌ POST create test failed - aborting remaining tests")
            return False
            
        if self.test_3_get_specific_client():
            tests_passed += 1
            
        if self.test_4_put_update_client():
            tests_passed += 1
            
        if self.test_5_delete_client():
            tests_passed += 1
            
        if self.test_6_verify_client_deleted():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 CLIENTS CRUD BACKEND API TEST SUMMARY")
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
                    
        # Key findings
        print("\n🎯 KEY FINDINGS FOR CLIENTS CRUD API:")
        print("-" * 50)
        
        findings = []
        if tests_passed >= 1:
            findings.append("✅ GET /api/clients: Successfully retrieves client list")
        if tests_passed >= 2:
            findings.append("✅ POST /api/clients: Successfully creates new clients")
        if tests_passed >= 3:
            findings.append("✅ GET /api/clients/{id}: Successfully retrieves specific clients")
        if tests_passed >= 4:
            findings.append("✅ PUT /api/clients/{id}: Successfully updates client data")
        if tests_passed >= 5:
            findings.append("✅ DELETE /api/clients/{id}: Successfully deletes clients")
        if tests_passed >= 6:
            findings.append("✅ Deletion Verification: Clients properly removed from system")
            
        for finding in findings:
            print(f"   {finding}")
            
        # Specific test results
        print("\n🔄 CRUD OPERATION VERIFICATION:")
        print("-" * 50)
        if self.initial_client_count > 0:
            print(f"   ✅ Initial client count: {self.initial_client_count}")
        if self.test_client_id:
            print(f"   ✅ Test client created with ID: {self.test_client_id}")
            print(f"   ✅ Test client data: Backend Test User <backendtest@example.com>")
        
        print(f"\n🏁 Testing completed at: {datetime.now().isoformat()}")
        
        # Consider 100% success rate as passing for CRUD operations
        return success_rate >= 100.0

def main():
    """Main test execution"""
    try:
        tester = ClientsCRUDTester(BACKEND_URL)
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 CLIENTS CRUD BACKEND API TESTING: COMPLETE SUCCESS!")
            print("✅ All CRUD operations working correctly:")
            print("   - GET /api/clients: Retrieves client list successfully")
            print("   - POST /api/clients: Creates clients with correct data")
            print("   - PUT /api/clients/{id}: Updates client information properly")
            print("   - DELETE /api/clients/{id}: Removes clients completely")
            print("   - Data integrity maintained throughout all operations")
            print("✅ Backend APIs are working correctly - frontend issues are not backend-related")
            sys.exit(0)
        else:
            print("\n🚨 CLIENTS CRUD BACKEND API TESTING: ISSUES DETECTED!")
            print("❌ Some CRUD operations are not working correctly")
            print("❌ Backend API issues may be causing frontend problems")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()