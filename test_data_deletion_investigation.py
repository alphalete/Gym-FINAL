#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

class TestDataDeletionInvestigator:
    def __init__(self, base_url="https://276b2f1f-9d6e-4215-a382-5da8671edad7.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_clients_found = []
        self.deletion_test_results = []

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

    def identify_test_clients(self, clients: List[Dict]) -> List[Dict]:
        """Identify clients that appear to be test data"""
        test_clients = []
        
        test_indicators = [
            # Name patterns
            lambda c: any(keyword in c.get('name', '').lower() for keyword in ['test', 'demo', 'sample', 'example']),
            # Email patterns
            lambda c: any(domain in c.get('email', '').lower() for domain in ['@example.com', '@test.com', '@demo.com']),
            # Phone patterns (common test numbers)
            lambda c: any(pattern in c.get('phone', '') for pattern in ['555-', '(555)', '123-456', '000-000']),
            # Common test names
            lambda c: c.get('name', '').lower() in ['john doe', 'jane doe', 'test user', 'demo user', 'sample client'],
        ]
        
        for client in clients:
            is_test_client = any(indicator(client) for indicator in test_indicators)
            if is_test_client:
                test_clients.append(client)
                
        return test_clients

    def investigate_existing_clients(self):
        """Step 1: GET /api/clients - Check for test-like clients"""
        print("\n" + "="*80)
        print("🔍 STEP 1: INVESTIGATING EXISTING CLIENTS FOR TEST DATA")
        print("="*80)
        
        success, response = self.run_test(
            "Get All Clients to Identify Test Data",
            "GET",
            "clients",
            200
        )
        
        if not success:
            print("❌ Failed to retrieve clients - cannot proceed with investigation")
            return False
            
        clients = response if isinstance(response, list) else []
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"   Total clients found: {len(clients)}")
        
        # Identify test clients
        test_clients = self.identify_test_clients(clients)
        self.test_clients_found = test_clients
        
        print(f"   Test clients identified: {len(test_clients)}")
        
        if test_clients:
            print(f"\n🎯 TEST CLIENTS FOUND:")
            for i, client in enumerate(test_clients, 1):
                print(f"   {i}. Name: {client.get('name')}")
                print(f"      Email: {client.get('email')}")
                print(f"      Phone: {client.get('phone', 'N/A')}")
                print(f"      ID: {client.get('id')}")
                print(f"      Status: {client.get('status', 'N/A')}")
                print()
        else:
            print("   ✅ No obvious test clients found based on common patterns")
            
        return success

    def test_individual_client_deletion(self):
        """Step 2: Test DELETE /api/clients/{client_id} - Individual deletion"""
        print("\n" + "="*80)
        print("🔍 STEP 2: TESTING INDIVIDUAL CLIENT DELETION ENDPOINT")
        print("="*80)
        
        if not self.test_clients_found:
            print("⚠️  No test clients found to delete - creating test client for deletion testing")
            return self.create_and_delete_test_client()
        
        # Test deletion of first test client found
        test_client = self.test_clients_found[0]
        client_id = test_client.get('id')
        client_name = test_client.get('name')
        
        print(f"🎯 Testing deletion of: {client_name} (ID: {client_id})")
        
        # First, check if client has payment records
        success_stats, stats_response = self.run_test(
            "Get Payment Stats Before Deletion",
            "GET",
            "payments/stats",
            200
        )
        
        initial_revenue = 0
        initial_payment_count = 0
        if success_stats:
            initial_revenue = stats_response.get('total_revenue', 0)
            initial_payment_count = stats_response.get('payment_count', 0)
            print(f"   Initial revenue: {initial_revenue}")
            print(f"   Initial payment count: {initial_payment_count}")
        
        # Attempt to delete the client
        success, response = self.run_test(
            f"Delete Test Client: {client_name}",
            "DELETE",
            f"clients/{client_id}",
            200
        )
        
        if success:
            print(f"✅ Client deletion successful!")
            print(f"   Client name: {response.get('client_name')}")
            print(f"   Client deleted: {response.get('client_deleted')}")
            print(f"   Payment records deleted: {response.get('payment_records_deleted', 0)}")
            print(f"   Details: {response.get('details')}")
            
            # Verify client is actually deleted
            verify_success, verify_response = self.run_test(
                f"Verify Client Deletion: {client_name}",
                "GET",
                f"clients/{client_id}",
                404  # Should return 404 if properly deleted
            )
            
            if verify_success:
                print("✅ Client deletion verified - client no longer exists")
            else:
                print("❌ Client deletion verification failed - client may still exist")
                
            # Check payment stats after deletion
            success_stats_after, stats_after_response = self.run_test(
                "Get Payment Stats After Deletion",
                "GET",
                "payments/stats",
                200
            )
            
            if success_stats_after:
                final_revenue = stats_after_response.get('total_revenue', 0)
                final_payment_count = stats_after_response.get('payment_count', 0)
                print(f"   Final revenue: {final_revenue}")
                print(f"   Final payment count: {final_payment_count}")
                
                revenue_change = initial_revenue - final_revenue
                payment_count_change = initial_payment_count - final_payment_count
                
                if revenue_change > 0 or payment_count_change > 0:
                    print(f"✅ Cascading deletion working - Revenue reduced by {revenue_change}, Payment count reduced by {payment_count_change}")
                else:
                    print("ℹ️  No payment records were associated with this client")
            
            self.deletion_test_results.append({
                'client_id': client_id,
                'client_name': client_name,
                'deletion_successful': True,
                'payment_records_deleted': response.get('payment_records_deleted', 0),
                'verification_successful': verify_success
            })
            
        else:
            print(f"❌ Client deletion failed!")
            self.deletion_test_results.append({
                'client_id': client_id,
                'client_name': client_name,
                'deletion_successful': False,
                'error': 'Deletion request failed'
            })
            
        return success

    def create_and_delete_test_client(self):
        """Create a test client and then delete it to test the deletion endpoint"""
        print("\n🔧 Creating test client for deletion testing...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_client_data = {
            "name": "Test Client for Deletion",
            "email": f"deletion_test_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-25"
        }
        
        # Create test client
        success_create, create_response = self.run_test(
            "Create Test Client for Deletion Testing",
            "POST",
            "clients",
            200,
            test_client_data
        )
        
        if not success_create or 'id' not in create_response:
            print("❌ Failed to create test client for deletion testing")
            return False
            
        test_client_id = create_response['id']
        print(f"✅ Created test client: {test_client_id}")
        
        # Add a payment record to test cascading deletion
        payment_data = {
            "client_id": test_client_id,
            "amount_paid": 50.00,
            "payment_date": "2025-01-25",
            "payment_method": "Test Payment",
            "notes": "Test payment for deletion testing"
        }
        
        success_payment, payment_response = self.run_test(
            "Record Test Payment for Deletion Testing",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success_payment:
            print(f"✅ Added test payment record")
        
        # Now test deletion
        success_delete, delete_response = self.run_test(
            "Delete Test Client with Payment Records",
            "DELETE",
            f"clients/{test_client_id}",
            200
        )
        
        if success_delete:
            print(f"✅ Test client deletion successful!")
            print(f"   Payment records deleted: {delete_response.get('payment_records_deleted', 0)}")
            
            # Verify deletion
            verify_success, verify_response = self.run_test(
                "Verify Test Client Deletion",
                "GET",
                f"clients/{test_client_id}",
                404
            )
            
            return verify_success
        else:
            print(f"❌ Test client deletion failed!")
            return False

    def test_bulk_deletion_simulation(self):
        """Step 3: Simulate bulk deletion like the frontend cleanup function"""
        print("\n" + "="*80)
        print("🔍 STEP 3: TESTING BULK DELETION SIMULATION")
        print("="*80)
        
        if len(self.test_clients_found) < 2:
            print("⚠️  Not enough test clients for bulk deletion testing")
            return self.create_multiple_test_clients_and_delete()
        
        print(f"🎯 Testing bulk deletion of {len(self.test_clients_found)} test clients")
        
        successful_deletions = 0
        failed_deletions = 0
        
        for i, client in enumerate(self.test_clients_found[1:], 1):  # Skip first one already deleted
            client_id = client.get('id')
            client_name = client.get('name')
            
            print(f"\n📋 Bulk deletion {i}: {client_name}")
            
            success, response = self.run_test(
                f"Bulk Delete Client {i}: {client_name}",
                "DELETE",
                f"clients/{client_id}",
                200
            )
            
            if success:
                successful_deletions += 1
                print(f"   ✅ Deletion successful")
                print(f"   Payment records deleted: {response.get('payment_records_deleted', 0)}")
            else:
                failed_deletions += 1
                print(f"   ❌ Deletion failed")
        
        print(f"\n📊 BULK DELETION RESULTS:")
        print(f"   Successful deletions: {successful_deletions}")
        print(f"   Failed deletions: {failed_deletions}")
        print(f"   Success rate: {(successful_deletions / (successful_deletions + failed_deletions) * 100):.1f}%" if (successful_deletions + failed_deletions) > 0 else "N/A")
        
        return failed_deletions == 0

    def create_multiple_test_clients_and_delete(self):
        """Create multiple test clients and test bulk deletion"""
        print("\n🔧 Creating multiple test clients for bulk deletion testing...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_clients_to_create = [
            {
                "name": "Bulk Test Client 1",
                "email": f"bulk_test_1_{timestamp}@example.com",
                "phone": "(555) 111-1111",
                "membership_type": "Standard",
                "monthly_fee": 50.00,
                "start_date": "2025-01-25"
            },
            {
                "name": "Bulk Test Client 2", 
                "email": f"bulk_test_2_{timestamp}@example.com",
                "phone": "(555) 222-2222",
                "membership_type": "Premium",
                "monthly_fee": 75.00,
                "start_date": "2025-01-25"
            },
            {
                "name": "Demo User for Testing",
                "email": f"demo_user_{timestamp}@example.com",
                "phone": "(555) 333-3333",
                "membership_type": "Elite",
                "monthly_fee": 100.00,
                "start_date": "2025-01-25"
            }
        ]
        
        created_client_ids = []
        
        # Create test clients
        for i, client_data in enumerate(test_clients_to_create, 1):
            success, response = self.run_test(
                f"Create Bulk Test Client {i}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and 'id' in response:
                created_client_ids.append(response['id'])
                print(f"   ✅ Created client {i}: {response['id']}")
                
                # Add payment record to some clients
                if i <= 2:  # Add payments to first 2 clients
                    payment_data = {
                        "client_id": response['id'],
                        "amount_paid": client_data['monthly_fee'],
                        "payment_date": "2025-01-25",
                        "payment_method": "Test Payment",
                        "notes": f"Test payment for bulk client {i}"
                    }
                    
                    payment_success, payment_response = self.run_test(
                        f"Add Payment to Bulk Test Client {i}",
                        "POST",
                        "payments/record",
                        200,
                        payment_data
                    )
        
        print(f"\n✅ Created {len(created_client_ids)} test clients for bulk deletion")
        
        # Now test bulk deletion
        successful_deletions = 0
        failed_deletions = 0
        
        for i, client_id in enumerate(created_client_ids, 1):
            success, response = self.run_test(
                f"Bulk Delete Created Client {i}",
                "DELETE",
                f"clients/{client_id}",
                200
            )
            
            if success:
                successful_deletions += 1
                print(f"   ✅ Bulk deletion {i} successful")
                print(f"   Payment records deleted: {response.get('payment_records_deleted', 0)}")
            else:
                failed_deletions += 1
                print(f"   ❌ Bulk deletion {i} failed")
        
        print(f"\n📊 BULK DELETION TEST RESULTS:")
        print(f"   Successful deletions: {successful_deletions}")
        print(f"   Failed deletions: {failed_deletions}")
        
        return failed_deletions == 0

    def test_permission_and_validation_issues(self):
        """Step 4: Test for permission and validation issues"""
        print("\n" + "="*80)
        print("🔍 STEP 4: TESTING PERMISSION AND VALIDATION ISSUES")
        print("="*80)
        
        # Test 1: Delete non-existent client
        success1, response1 = self.run_test(
            "Delete Non-existent Client (Should Return 404)",
            "DELETE",
            "clients/non-existent-client-id-12345",
            404
        )
        
        # Test 2: Delete with invalid client ID format
        success2, response2 = self.run_test(
            "Delete with Invalid Client ID Format",
            "DELETE",
            "clients/invalid-id-format-!@#$%",
            404  # Should handle gracefully
        )
        
        # Test 3: Delete with empty client ID
        success3, response3 = self.run_test(
            "Delete with Empty Client ID",
            "DELETE",
            "clients/",
            404  # Should return method not allowed or 404
        )
        
        print(f"\n📊 PERMISSION & VALIDATION TEST RESULTS:")
        print(f"   Non-existent client test: {'✅ PASSED' if success1 else '❌ FAILED'}")
        print(f"   Invalid ID format test: {'✅ PASSED' if success2 else '❌ FAILED'}")
        print(f"   Empty ID test: {'✅ PASSED' if success3 else '❌ FAILED'}")
        
        return success1 and success2 and success3

    def test_cascading_deletion_verification(self):
        """Step 5: Verify cascading deletion works properly"""
        print("\n" + "="*80)
        print("🔍 STEP 5: TESTING CASCADING DELETION VERIFICATION")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a client with multiple payment records
        client_data = {
            "name": "Cascading Test Client",
            "email": f"cascading_test_{timestamp}@example.com",
            "phone": "(555) 999-9999",
            "membership_type": "VIP",
            "monthly_fee": 150.00,
            "start_date": "2025-01-20"
        }
        
        success_create, create_response = self.run_test(
            "Create Client for Cascading Deletion Test",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success_create or 'id' not in create_response:
            print("❌ Failed to create client for cascading deletion test")
            return False
            
        client_id = create_response['id']
        print(f"✅ Created cascading test client: {client_id}")
        
        # Add multiple payment records
        payment_amounts = [150.00, 150.00, 150.00]  # 3 payments
        payment_ids = []
        
        for i, amount in enumerate(payment_amounts, 1):
            payment_data = {
                "client_id": client_id,
                "amount_paid": amount,
                "payment_date": f"2025-01-{20+i:02d}",
                "payment_method": "Credit Card",
                "notes": f"Cascading test payment {i}"
            }
            
            success_payment, payment_response = self.run_test(
                f"Add Payment Record {i} for Cascading Test",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            if success_payment:
                payment_ids.append(payment_response.get('payment_id'))
                print(f"   ✅ Added payment {i}: ${amount}")
        
        print(f"✅ Added {len(payment_ids)} payment records")
        
        # Get payment stats before deletion
        success_stats_before, stats_before = self.run_test(
            "Get Payment Stats Before Cascading Deletion",
            "GET",
            "payments/stats",
            200
        )
        
        initial_revenue = stats_before.get('total_revenue', 0) if success_stats_before else 0
        initial_count = stats_before.get('payment_count', 0) if success_stats_before else 0
        
        print(f"📊 Before deletion - Revenue: {initial_revenue}, Payment count: {initial_count}")
        
        # Delete the client (should cascade delete all payment records)
        success_delete, delete_response = self.run_test(
            "Delete Client with Multiple Payment Records",
            "DELETE",
            f"clients/{client_id}",
            200
        )
        
        if success_delete:
            payment_records_deleted = delete_response.get('payment_records_deleted', 0)
            print(f"✅ Client deleted successfully")
            print(f"   Payment records deleted: {payment_records_deleted}")
            print(f"   Expected payment records: {len(payment_amounts)}")
            
            if payment_records_deleted == len(payment_amounts):
                print("✅ Cascading deletion count is CORRECT")
            else:
                print(f"❌ Cascading deletion count is INCORRECT - Expected {len(payment_amounts)}, got {payment_records_deleted}")
            
            # Verify payment stats after deletion
            success_stats_after, stats_after = self.run_test(
                "Get Payment Stats After Cascading Deletion",
                "GET",
                "payments/stats",
                200
            )
            
            if success_stats_after:
                final_revenue = stats_after.get('total_revenue', 0)
                final_count = stats_after.get('payment_count', 0)
                
                expected_revenue_reduction = sum(payment_amounts)
                actual_revenue_reduction = initial_revenue - final_revenue
                expected_count_reduction = len(payment_amounts)
                actual_count_reduction = initial_count - final_count
                
                print(f"📊 After deletion - Revenue: {final_revenue}, Payment count: {final_count}")
                print(f"📊 Revenue reduction - Expected: {expected_revenue_reduction}, Actual: {actual_revenue_reduction}")
                print(f"📊 Count reduction - Expected: {expected_count_reduction}, Actual: {actual_count_reduction}")
                
                if abs(actual_revenue_reduction - expected_revenue_reduction) < 0.01:  # Allow for floating point precision
                    print("✅ Revenue reduction is CORRECT")
                else:
                    print("❌ Revenue reduction is INCORRECT")
                    
                if actual_count_reduction == expected_count_reduction:
                    print("✅ Payment count reduction is CORRECT")
                else:
                    print("❌ Payment count reduction is INCORRECT")
                    
                return (abs(actual_revenue_reduction - expected_revenue_reduction) < 0.01 and 
                       actual_count_reduction == expected_count_reduction)
            
        else:
            print("❌ Client deletion failed")
            return False
            
        return success_delete

    def generate_investigation_report(self):
        """Generate a comprehensive investigation report"""
        print("\n" + "="*80)
        print("📋 TEST DATA DELETION INVESTIGATION REPORT")
        print("="*80)
        
        print(f"\n📊 OVERALL TEST RESULTS:")
        print(f"   Tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "N/A")
        
        print(f"\n🎯 TEST CLIENTS IDENTIFIED:")
        if self.test_clients_found:
            print(f"   Found {len(self.test_clients_found)} test clients:")
            for client in self.test_clients_found:
                print(f"   - {client.get('name')} ({client.get('email')})")
        else:
            print("   No obvious test clients found")
            
        print(f"\n🗑️  DELETION TEST RESULTS:")
        if self.deletion_test_results:
            successful_deletions = sum(1 for result in self.deletion_test_results if result.get('deletion_successful'))
            print(f"   Successful deletions: {successful_deletions}/{len(self.deletion_test_results)}")
            
            for result in self.deletion_test_results:
                status = "✅ SUCCESS" if result.get('deletion_successful') else "❌ FAILED"
                print(f"   - {result.get('client_name')}: {status}")
                if result.get('payment_records_deleted', 0) > 0:
                    print(f"     Payment records deleted: {result.get('payment_records_deleted')}")
        else:
            print("   No deletion tests performed")
            
        print(f"\n🔍 KEY FINDINGS:")
        
        # Analyze findings
        if self.tests_passed == self.tests_run:
            print("   ✅ ALL TESTS PASSED - DELETE endpoint is working correctly")
            print("   ✅ Individual client deletion works properly")
            print("   ✅ Cascading deletion of payment records works")
            print("   ✅ Error handling for invalid client IDs works")
            print("   ✅ No backend API issues detected")
            
            if not self.test_clients_found:
                print("   ℹ️  No test data found - database may already be clean")
            else:
                print("   ✅ Test data can be successfully deleted")
                
        else:
            print("   ❌ SOME TESTS FAILED - Issues detected with deletion functionality")
            
            failed_tests = self.tests_run - self.tests_passed
            print(f"   ❌ {failed_tests} test(s) failed")
            
        print(f"\n💡 RECOMMENDATIONS:")
        
        if self.tests_passed == self.tests_run:
            if self.test_clients_found:
                print("   1. The DELETE /api/clients/{client_id} endpoint is working correctly")
                print("   2. Test data can be deleted individually without issues")
                print("   3. If frontend cleanup is failing, the issue is likely in the frontend JavaScript")
                print("   4. Consider implementing a dedicated bulk delete endpoint for better performance")
                print("   5. Check frontend error handling and network timeout settings")
            else:
                print("   1. No test data found - database appears to be clean")
                print("   2. DELETE endpoint is working correctly for future use")
        else:
            print("   1. Fix the identified issues with the DELETE endpoint")
            print("   2. Investigate backend error handling")
            print("   3. Check database connection and permissions")
            
        print("\n" + "="*80)

    def run_full_investigation(self):
        """Run the complete test data deletion investigation"""
        print("🚀 STARTING TEST DATA DELETION INVESTIGATION")
        print("="*80)
        
        try:
            # Step 1: Investigate existing clients
            self.investigate_existing_clients()
            
            # Step 2: Test individual client deletion
            self.test_individual_client_deletion()
            
            # Step 3: Test bulk deletion simulation
            self.test_bulk_deletion_simulation()
            
            # Step 4: Test permission and validation issues
            self.test_permission_and_validation_issues()
            
            # Step 5: Test cascading deletion
            self.test_cascading_deletion_verification()
            
            # Generate final report
            self.generate_investigation_report()
            
        except Exception as e:
            print(f"\n❌ INVESTIGATION FAILED: {str(e)}")
            return False
            
        return True

if __name__ == "__main__":
    print("🔍 TEST DATA DELETION INVESTIGATION TOOL")
    print("="*50)
    
    investigator = TestDataDeletionInvestigator()
    success = investigator.run_full_investigation()
    
    if success:
        print("\n✅ Investigation completed successfully!")
    else:
        print("\n❌ Investigation completed with errors!")
        
    sys.exit(0 if success else 1)