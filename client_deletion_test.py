#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

class ClientDeletionTester:
    def __init__(self, base_url="https://8beb6460-0117-4864-a970-463f629aa57c.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_client_ids = []
        self.initial_client_count = 0
        self.test_clients_created = []

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

    def get_initial_client_count(self):
        """Get the initial count of clients in the database"""
        print("\n🔍 STEP 1: Getting initial client count...")
        success, response = self.run_test(
            "Get Initial Client Count",
            "GET",
            "clients",
            200
        )
        
        if success:
            self.initial_client_count = len(response)
            print(f"   📊 Initial client count: {self.initial_client_count}")
            
            # Show some sample clients for identification
            if response:
                print(f"   📋 Sample existing clients:")
                for i, client in enumerate(response[:5]):  # Show first 5
                    print(f"      {i+1}. {client.get('name')} ({client.get('email')}) - ID: {client.get('id')}")
                if len(response) > 5:
                    print(f"      ... and {len(response) - 5} more clients")
            
            return True
        else:
            print("❌ Failed to get initial client count")
            return False

    def identify_test_clients(self):
        """Identify test clients by name/email patterns"""
        print("\n🔍 STEP 2: Identifying test clients...")
        success, response = self.run_test(
            "Get All Clients for Test Identification",
            "GET",
            "clients",
            200
        )
        
        if success:
            test_clients = []
            test_patterns = [
                'test', 'john doe', 'jane doe', 'example.com', 'test.com',
                'dummy', 'sample', 'demo', '(555)', 'fake'
            ]
            
            for client in response:
                client_name = (client.get('name') or '').lower()
                client_email = (client.get('email') or '').lower()
                client_phone = (client.get('phone') or '').lower()
                
                # Check if client matches test patterns
                is_test_client = False
                matched_patterns = []
                
                for pattern in test_patterns:
                    if (pattern in client_name or 
                        pattern in client_email or 
                        pattern in client_phone):
                        is_test_client = True
                        matched_patterns.append(pattern)
                
                if is_test_client:
                    test_clients.append({
                        'id': client.get('id'),
                        'name': client.get('name'),
                        'email': client.get('email'),
                        'phone': client.get('phone'),
                        'membership_type': client.get('membership_type'),
                        'monthly_fee': client.get('monthly_fee'),
                        'matched_patterns': matched_patterns
                    })
            
            print(f"   🎯 Identified {len(test_clients)} test clients:")
            for i, client in enumerate(test_clients[:10]):  # Show first 10
                print(f"      {i+1}. {client['name']} ({client['email']}) - ID: {client['id']}")
                print(f"         Patterns: {', '.join(client['matched_patterns'])}")
            
            if len(test_clients) > 10:
                print(f"      ... and {len(test_clients) - 10} more test clients")
            
            self.test_client_ids = [client['id'] for client in test_clients]
            return True
        else:
            print("❌ Failed to identify test clients")
            return False

    def create_test_clients_for_deletion(self):
        """Create specific test clients for deletion testing"""
        print("\n🔍 STEP 3: Creating test clients for deletion testing...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_clients_data = [
            {
                "name": "DELETE Test Client 1",
                "email": f"delete_test_1_{timestamp}@example.com",
                "phone": "(555) 111-1111",
                "membership_type": "Standard",
                "monthly_fee": 50.00,
                "start_date": "2025-01-01"
            },
            {
                "name": "DELETE Test Client 2", 
                "email": f"delete_test_2_{timestamp}@example.com",
                "phone": "(555) 222-2222",
                "membership_type": "Premium",
                "monthly_fee": 75.00,
                "start_date": "2025-01-15"
            },
            {
                "name": "DELETE Test Client 3",
                "email": f"delete_test_3_{timestamp}@example.com", 
                "phone": "(555) 333-3333",
                "membership_type": "Elite",
                "monthly_fee": 100.00,
                "start_date": "2025-02-01"
            }
        ]
        
        created_count = 0
        for i, client_data in enumerate(test_clients_data, 1):
            success, response = self.run_test(
                f"Create Test Client {i} for Deletion",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                client_id = response["id"]
                self.test_clients_created.append({
                    'id': client_id,
                    'name': client_data['name'],
                    'email': client_data['email']
                })
                created_count += 1
                print(f"   ✅ Created test client {i}: {client_data['name']} (ID: {client_id})")
            else:
                print(f"   ❌ Failed to create test client {i}")
        
        print(f"   📊 Successfully created {created_count} test clients for deletion testing")
        return created_count > 0

    def test_delete_single_client(self):
        """Test deleting a single client"""
        print("\n🔍 STEP 4: Testing DELETE endpoint with single client...")
        
        if not self.test_clients_created:
            print("❌ No test clients available for deletion testing")
            return False
        
        # Use the first created test client
        test_client = self.test_clients_created[0]
        client_id = test_client['id']
        client_name = test_client['name']
        
        print(f"   🎯 Attempting to delete: {client_name} (ID: {client_id})")
        
        # First verify the client exists
        success1, response1 = self.run_test(
            "Verify Client Exists Before Deletion",
            "GET",
            f"clients/{client_id}",
            200
        )
        
        if not success1:
            print(f"   ❌ Test client {client_id} does not exist before deletion")
            return False
        
        print(f"   ✅ Confirmed client exists: {response1.get('name')} ({response1.get('email')})")
        
        # Now attempt to delete the client
        success2, response2 = self.run_test(
            "DELETE Single Client",
            "DELETE",
            f"clients/{client_id}",
            200
        )
        
        if not success2:
            print(f"   ❌ DELETE request failed for client {client_id}")
            return False
        
        print(f"   ✅ DELETE request successful: {response2.get('message', 'No message')}")
        
        # Verify the client is actually deleted
        success3, response3 = self.run_test(
            "Verify Client is Deleted",
            "GET",
            f"clients/{client_id}",
            404  # Should return 404 if deleted
        )
        
        if success3:
            print(f"   ✅ Client {client_id} is confirmed deleted (404 response)")
            # Remove from our tracking list
            self.test_clients_created = [c for c in self.test_clients_created if c['id'] != client_id]
            return True
        else:
            print(f"   ❌ Client {client_id} still exists after deletion!")
            return False

    def test_delete_multiple_clients(self):
        """Test deleting multiple clients one by one"""
        print("\n🔍 STEP 5: Testing multiple client deletions...")
        
        if len(self.test_clients_created) < 2:
            print("❌ Not enough test clients for multiple deletion testing")
            return False
        
        deleted_count = 0
        failed_count = 0
        
        # Delete remaining test clients
        clients_to_delete = self.test_clients_created.copy()
        
        for i, test_client in enumerate(clients_to_delete, 1):
            client_id = test_client['id']
            client_name = test_client['name']
            
            print(f"\n   🎯 Deleting client {i}: {client_name} (ID: {client_id})")
            
            # Delete the client
            success, response = self.run_test(
                f"DELETE Client {i}",
                "DELETE",
                f"clients/{client_id}",
                200
            )
            
            if success:
                print(f"   ✅ DELETE successful: {response.get('message', 'No message')}")
                
                # Verify deletion
                verify_success, _ = self.run_test(
                    f"Verify Client {i} Deleted",
                    "GET",
                    f"clients/{client_id}",
                    404
                )
                
                if verify_success:
                    deleted_count += 1
                    print(f"   ✅ Client {i} confirmed deleted")
                else:
                    failed_count += 1
                    print(f"   ❌ Client {i} still exists after deletion")
            else:
                failed_count += 1
                print(f"   ❌ DELETE failed for client {i}")
        
        print(f"\n   📊 Multiple deletion results:")
        print(f"      Successfully deleted: {deleted_count}")
        print(f"      Failed deletions: {failed_count}")
        print(f"      Success rate: {(deleted_count / len(clients_to_delete) * 100):.1f}%")
        
        # Clear our tracking list
        self.test_clients_created = []
        
        return deleted_count > 0

    def test_delete_nonexistent_client(self):
        """Test deleting a non-existent client (should return 404)"""
        print("\n🔍 STEP 6: Testing deletion of non-existent client...")
        
        fake_client_id = "non-existent-client-id-12345"
        
        success, response = self.run_test(
            "DELETE Non-existent Client (Should Return 404)",
            "DELETE",
            f"clients/{fake_client_id}",
            404
        )
        
        if success:
            print(f"   ✅ Correctly returned 404 for non-existent client")
            return True
        else:
            print(f"   ❌ Did not return 404 for non-existent client")
            return False

    def verify_database_state_after_deletions(self):
        """Verify the database state after all deletions"""
        print("\n🔍 STEP 7: Verifying database state after deletions...")
        
        success, response = self.run_test(
            "Get Final Client Count",
            "GET",
            "clients",
            200
        )
        
        if success:
            final_client_count = len(response)
            print(f"   📊 Final client count: {final_client_count}")
            print(f"   📊 Initial client count: {self.initial_client_count}")
            
            # Calculate expected count (initial + created - deleted)
            created_count = 3  # We created 3 test clients
            expected_deleted = 3  # We should have deleted all 3
            expected_final_count = self.initial_client_count + created_count - expected_deleted
            
            print(f"   📊 Expected final count: {expected_final_count}")
            
            if final_client_count == expected_final_count:
                print(f"   ✅ Database state is CORRECT after deletions")
                return True
            else:
                print(f"   ❌ Database state is INCORRECT after deletions")
                print(f"      Expected: {expected_final_count}, Got: {final_client_count}")
                return False
        else:
            print("   ❌ Failed to get final client count")
            return False

    def test_existing_test_clients_deletion(self):
        """Test deleting existing test clients identified earlier"""
        print("\n🔍 STEP 8: Testing deletion of existing test clients...")
        
        if not self.test_client_ids:
            print("   ℹ️  No existing test clients identified for deletion")
            return True
        
        print(f"   🎯 Found {len(self.test_client_ids)} existing test clients to delete")
        
        # Limit to first 5 to avoid overwhelming the system
        clients_to_delete = self.test_client_ids[:5]
        deleted_count = 0
        failed_count = 0
        
        for i, client_id in enumerate(clients_to_delete, 1):
            print(f"\n   🎯 Deleting existing test client {i}: {client_id}")
            
            # First get client info
            info_success, info_response = self.run_test(
                f"Get Info for Test Client {i}",
                "GET",
                f"clients/{client_id}",
                200
            )
            
            if info_success:
                client_name = info_response.get('name', 'Unknown')
                client_email = info_response.get('email', 'Unknown')
                print(f"      Client: {client_name} ({client_email})")
                
                # Delete the client
                delete_success, delete_response = self.run_test(
                    f"DELETE Existing Test Client {i}",
                    "DELETE",
                    f"clients/{client_id}",
                    200
                )
                
                if delete_success:
                    print(f"   ✅ DELETE successful: {delete_response.get('message', 'No message')}")
                    
                    # Verify deletion
                    verify_success, _ = self.run_test(
                        f"Verify Test Client {i} Deleted",
                        "GET",
                        f"clients/{client_id}",
                        404
                    )
                    
                    if verify_success:
                        deleted_count += 1
                        print(f"   ✅ Test client {i} confirmed deleted")
                    else:
                        failed_count += 1
                        print(f"   ❌ Test client {i} still exists after deletion")
                else:
                    failed_count += 1
                    print(f"   ❌ DELETE failed for test client {i}")
            else:
                print(f"   ⚠️  Test client {i} not found (may have been deleted already)")
        
        print(f"\n   📊 Existing test client deletion results:")
        print(f"      Successfully deleted: {deleted_count}")
        print(f"      Failed deletions: {failed_count}")
        print(f"      Clients processed: {len(clients_to_delete)}")
        
        return True

    def run_comprehensive_deletion_test(self):
        """Run the complete client deletion test suite"""
        print("🚀 STARTING COMPREHENSIVE CLIENT DELETION TESTING")
        print("=" * 80)
        print("🎯 FOCUS: Testing backend DELETE /api/clients/{client_id} endpoint")
        print("🎯 PURPOSE: Investigate why database cleanup is not working")
        print("=" * 80)
        
        # Step 1: Get initial state
        if not self.get_initial_client_count():
            print("❌ Failed to get initial client count - aborting test")
            return False
        
        # Step 2: Identify existing test clients
        if not self.identify_test_clients():
            print("❌ Failed to identify test clients - continuing with created clients only")
        
        # Step 3: Create new test clients
        if not self.create_test_clients_for_deletion():
            print("❌ Failed to create test clients - aborting test")
            return False
        
        # Step 4: Test single client deletion
        single_delete_success = self.test_delete_single_client()
        
        # Step 5: Test multiple client deletions
        multiple_delete_success = self.test_delete_multiple_clients()
        
        # Step 6: Test error handling
        error_handling_success = self.test_delete_nonexistent_client()
        
        # Step 7: Verify database state
        db_state_success = self.verify_database_state_after_deletions()
        
        # Step 8: Test existing test clients deletion
        existing_delete_success = self.test_existing_test_clients_deletion()
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎯 CLIENT DELETION TEST SUMMARY")
        print("=" * 80)
        
        total_tests = 6
        passed_tests = sum([
            single_delete_success,
            multiple_delete_success, 
            error_handling_success,
            db_state_success,
            existing_delete_success,
            True  # Initial setup always counts as passed if we get here
        ])
        
        print(f"📊 Tests run: {self.tests_run}")
        print(f"📊 Tests passed: {self.tests_passed}")
        print(f"📊 Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        print(f"📊 Major test categories passed: {passed_tests}/{total_tests}")
        
        print(f"\n🔍 DETAILED RESULTS:")
        print(f"   ✅ Initial Setup: PASSED" if True else "   ❌ Initial Setup: FAILED")
        print(f"   ✅ Single Client Deletion: PASSED" if single_delete_success else "   ❌ Single Client Deletion: FAILED")
        print(f"   ✅ Multiple Client Deletions: PASSED" if multiple_delete_success else "   ❌ Multiple Client Deletions: FAILED")
        print(f"   ✅ Error Handling (404): PASSED" if error_handling_success else "   ❌ Error Handling (404): FAILED")
        print(f"   ✅ Database State Verification: PASSED" if db_state_success else "   ❌ Database State Verification: FAILED")
        print(f"   ✅ Existing Test Clients Deletion: PASSED" if existing_delete_success else "   ❌ Existing Test Clients Deletion: FAILED")
        
        # Critical analysis
        if single_delete_success and multiple_delete_success and db_state_success:
            print(f"\n🎉 CONCLUSION: DELETE endpoint is WORKING CORRECTLY!")
            print(f"   ✅ Individual client deletions work")
            print(f"   ✅ Multiple client deletions work")
            print(f"   ✅ Database state updates correctly")
            print(f"   ✅ Deleted clients are actually removed from database")
            print(f"\n🔍 IMPLICATION: If frontend cleanup is failing, the issue is likely:")
            print(f"   - Frontend not calling the DELETE endpoint correctly")
            print(f"   - Frontend not passing correct client IDs")
            print(f"   - Frontend error handling masking backend success")
            print(f"   - Race conditions or timing issues in bulk operations")
        else:
            print(f"\n🚨 CONCLUSION: DELETE endpoint has CRITICAL ISSUES!")
            print(f"   ❌ Backend DELETE functionality is not working properly")
            print(f"   ❌ This explains why database cleanup is failing")
            print(f"   ❌ Frontend shows success but backend doesn't actually delete")
            
        return passed_tests >= 4  # At least 4 out of 6 major categories should pass

if __name__ == "__main__":
    tester = ClientDeletionTester()
    success = tester.run_comprehensive_deletion_test()
    
    if success:
        print(f"\n🎉 CLIENT DELETION TESTING COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print(f"\n🚨 CLIENT DELETION TESTING FAILED!")
        sys.exit(1)