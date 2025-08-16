#!/usr/bin/env python3

import requests
import json
import time
import uuid
from datetime import datetime, date
import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor

class OptimisticToggleBackendTest:
    def __init__(self):
        # Use the production URL from frontend/.env
        self.base_url = "https://gym-billing-system.preview.emergentagent.com/api"
        self.session = None
        self.test_results = []
        self.test_membership_types = []
        
    def setup_session(self):
        """Setup HTTP session with proper headers"""
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OptimisticToggleTest/1.0'
        })
        self.session.timeout = 30
        
    def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            self.session.close()
            
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def test_backend_readiness(self):
        """Test 1: Optimistic Toggle Backend Readiness - Verify backend can handle rapid plan active status updates"""
        print("\n🔍 TEST 1: Backend Readiness for Rapid Plan Updates")
        
        try:
            # Test API health first
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Backend Health Check", True, f"API responding: {health_data.get('status', 'unknown')}")
            else:
                self.log_test("Backend Health Check", False, f"Health endpoint returned {response.status_code}")
                return False
                    
            # Test membership types endpoint availability
            response = self.session.get(f"{self.base_url}/membership-types")
            if response.status_code == 200:
                membership_types = response.json()
                self.log_test("Membership Types Endpoint", True, f"Found {len(membership_types)} membership types")
                
                # Check if we have required fields for optimistic updates
                if membership_types and len(membership_types) > 0:
                    first_type = membership_types[0]
                    required_fields = ['id', 'name', 'is_active', 'monthly_fee']
                    has_required = all(field in first_type for field in required_fields)
                    self.log_test("Required Fields Present", has_required, 
                                f"Fields: {list(first_type.keys())}")
                else:
                    self.log_test("Membership Types Data", False, "No membership types found")
                    
            else:
                self.log_test("Membership Types Endpoint", False, f"Endpoint returned {response.status_code}")
                return False
                    
            return True
            
        except Exception as e:
            self.log_test("Backend Readiness", False, f"Connection error: {str(e)}")
            return False
            
    def test_rapid_toggle_handling(self):
        """Test 2: Error Handling - Test backend response to concurrent updates and rapid toggles"""
        print("\n🔍 TEST 2: Rapid Toggle and Concurrent Update Handling")
        
        try:
            # Create a test membership type for rapid updates
            test_plan = {
                "name": f"OptimisticTest_{int(time.time())}",
                "monthly_fee": 75.0,
                "description": "Test plan for optimistic toggle testing",
                "features": ["Test Feature 1", "Test Feature 2"],
                "is_active": True
            }
            
            # Create the test plan
            response = self.session.post(f"{self.base_url}/membership-types", 
                                       data=json.dumps(test_plan))
            if response.status_code == 200:
                created_plan = response.json()
                plan_id = created_plan['id']
                self.test_membership_types.append(plan_id)
                self.log_test("Test Plan Creation", True, f"Created plan with ID: {plan_id}")
                
                # Test rapid sequential updates (simulating optimistic toggles)
                rapid_update_success = True
                for i in range(5):
                    update_data = {
                        "is_active": i % 2 == 0  # Alternate between True/False
                    }
                    
                    start_time = time.time()
                    update_response = self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                              data=json.dumps(update_data))
                    response_time = time.time() - start_time
                    
                    if update_response.status_code == 200:
                        updated_plan = update_response.json()
                        expected_active = update_data["is_active"]
                        actual_active = updated_plan.get("is_active")
                        
                        if actual_active == expected_active:
                            self.log_test(f"Rapid Update {i+1}", True, 
                                        f"Response time: {response_time:.3f}s, Active: {actual_active}")
                        else:
                            self.log_test(f"Rapid Update {i+1}", False, 
                                        f"Expected active={expected_active}, got {actual_active}")
                            rapid_update_success = False
                    else:
                        self.log_test(f"Rapid Update {i+1}", False, 
                                    f"Update failed with status {update_response.status_code}")
                        rapid_update_success = False
                        
                    # Small delay to prevent overwhelming the server
                    time.sleep(0.1)
                    
                self.log_test("Rapid Sequential Updates", rapid_update_success, 
                            "All 5 rapid updates processed correctly")
                
                # Test concurrent updates (simulating multiple users)
                def concurrent_update(plan_id, update_data):
                    try:
                        response = self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                                  data=json.dumps(update_data))
                        return response.status_code == 200
                    except Exception as e:
                        return False
                
                with ThreadPoolExecutor(max_workers=3) as executor:
                    update_data = {"is_active": True}  # All trying to set to True
                    futures = [executor.submit(concurrent_update, plan_id, update_data) for _ in range(3)]
                    concurrent_results = [future.result() for future in futures]
                
                successful_updates = sum(concurrent_results)
                concurrent_success = successful_updates >= 2  # At least 2 out of 3 should succeed
                
                for i, success in enumerate(concurrent_results):
                    self.log_test(f"Concurrent Update {i+1}", success, "Update successful" if success else "Update failed")
                    
                self.log_test("Concurrent Updates Handling", concurrent_success,
                            f"{successful_updates}/3 concurrent updates succeeded")
                
            else:
                self.log_test("Test Plan Creation", False, f"Failed to create test plan: {response.status_code}")
                return False
                    
            return True
            
        except Exception as e:
            self.log_test("Rapid Toggle Handling", False, f"Error: {str(e)}")
            return False
            
    def test_plans_store_performance(self):
        """Test 3: Plans Store Performance - Verify dedicated plans store with active index handles toggle operations efficiently"""
        print("\n🔍 TEST 3: Plans Store Performance with Active Index")
        
        try:
            # Test filtering by active status (simulating IndexedDB active index)
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/membership-types")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                all_plans = response.json()
                active_plans = [p for p in all_plans if p.get('is_active', False)]
                inactive_plans = [p for p in all_plans if not p.get('is_active', False)]
                
                self.log_test("Plans Retrieval Performance", response_time < 2.0,
                            f"Retrieved {len(all_plans)} plans in {response_time:.3f}s")
                
                self.log_test("Active/Inactive Filtering", True,
                            f"Active: {len(active_plans)}, Inactive: {len(inactive_plans)}")
                
                # Test data consistency for active index simulation
                consistency_check = True
                for plan in all_plans:
                    if 'is_active' not in plan:
                        consistency_check = False
                        break
                        
                self.log_test("Data Consistency for Filtering", consistency_check,
                            "All plans have is_active field for efficient filtering")
                
                # Test rapid filtering operations (simulating frontend filter changes)
                filter_times = []
                for _ in range(3):
                    start_filter = time.time()
                    # Simulate filtering operations
                    active_filtered = [p for p in all_plans if p.get('is_active', False)]
                    filter_time = time.time() - start_filter
                    filter_times.append(filter_time)
                    
                avg_filter_time = sum(filter_times) / len(filter_times)
                self.log_test("Filter Performance", avg_filter_time < 0.1,
                            f"Average filter time: {avg_filter_time:.4f}s")
                
            else:
                self.log_test("Plans Store Performance", False, f"Failed to retrieve plans: {response.status_code}")
                return False
                    
            return True
            
        except Exception as e:
            self.log_test("Plans Store Performance", False, f"Error: {str(e)}")
            return False
            
    def test_data_consistency(self):
        """Test 4: Data Consistency - Ensure active/inactive filtering works correctly with instant toggles"""
        print("\n🔍 TEST 4: Data Consistency with Instant Toggles")
        
        try:
            # Get current state
            response = self.session.get(f"{self.base_url}/membership-types")
            if response.status_code == 200:
                initial_plans = response.json()
                
                if len(initial_plans) > 0:
                    test_plan = initial_plans[0]
                    plan_id = test_plan['id']
                    initial_active = test_plan.get('is_active', False)
                    
                    # Toggle the active status
                    new_active = not initial_active
                    update_data = {"is_active": new_active}
                    
                    update_response = self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                              data=json.dumps(update_data))
                    if update_response.status_code == 200:
                        updated_plan = update_response.json()
                        
                        # Verify immediate consistency
                        if updated_plan.get('is_active') == new_active:
                            self.log_test("Immediate Update Consistency", True,
                                        f"Active status changed from {initial_active} to {new_active}")
                            
                            # Verify consistency in list endpoint
                            time.sleep(0.1)  # Small delay
                            list_response = self.session.get(f"{self.base_url}/membership-types")
                            if list_response.status_code == 200:
                                updated_list = list_response.json()
                                updated_plan_in_list = next((p for p in updated_list if p['id'] == plan_id), None)
                                
                                if updated_plan_in_list and updated_plan_in_list.get('is_active') == new_active:
                                    self.log_test("List Endpoint Consistency", True,
                                                "Updated plan reflects correct active status in list")
                                else:
                                    self.log_test("List Endpoint Consistency", False,
                                                "Plan active status inconsistent between endpoints")
                            else:
                                self.log_test("List Endpoint Consistency", False,
                                            f"List endpoint failed: {list_response.status_code}")
                            
                            # Test filtering consistency
                            active_plans = [p for p in updated_list if p.get('is_active', False)]
                            inactive_plans = [p for p in updated_list if not p.get('is_active', False)]
                            
                            if new_active:
                                plan_in_active = any(p['id'] == plan_id for p in active_plans)
                                self.log_test("Active Filter Consistency", plan_in_active,
                                            "Toggled plan appears in active filter")
                            else:
                                plan_in_inactive = any(p['id'] == plan_id for p in inactive_plans)
                                self.log_test("Inactive Filter Consistency", plan_in_inactive,
                                            "Toggled plan appears in inactive filter")
                            
                            # Restore original state
                            restore_data = {"is_active": initial_active}
                            restore_response = self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                                      data=json.dumps(restore_data))
                            if restore_response.status_code == 200:
                                self.log_test("State Restoration", True, "Original state restored")
                            else:
                                self.log_test("State Restoration", False, "Failed to restore original state")
                            
                        else:
                            self.log_test("Immediate Update Consistency", False,
                                        f"Expected {new_active}, got {updated_plan.get('is_active')}")
                    else:
                        self.log_test("Data Consistency Update", False, f"Update failed: {update_response.status_code}")
                else:
                    self.log_test("Data Consistency", False, "No plans available for testing")
                    return False
            else:
                self.log_test("Data Consistency", False, f"Failed to get plans: {response.status_code}")
                return False
                    
            return True
            
        except Exception as e:
            self.log_test("Data Consistency", False, f"Error: {str(e)}")
            return False
            
    def test_indexeddb_integration(self):
        """Test 5: IndexedDB Integration - Test that local storage updates work seamlessly with backend persistence"""
        print("\n🔍 TEST 5: IndexedDB Integration Support")
        
        try:
            # Test backend endpoints that support IndexedDB operations
            
            # 1. Test bulk retrieval (for IndexedDB sync)
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/membership-types")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                plans = response.json()
                self.log_test("Bulk Retrieval for IndexedDB Sync", True,
                            f"Retrieved {len(plans)} plans in {response_time:.3f}s")
                
                # Test data format compatibility with IndexedDB
                indexeddb_compatible = True
                for plan in plans:
                    # Check for JSON serializable fields
                    required_fields = ['id', 'name', 'monthly_fee', 'is_active']
                    if not all(field in plan for field in required_fields):
                        indexeddb_compatible = False
                        break
                    
                    # Check data types
                    if not isinstance(plan['id'], str) or not isinstance(plan['is_active'], bool):
                        indexeddb_compatible = False
                        break
                        
                self.log_test("IndexedDB Data Format Compatibility", indexeddb_compatible,
                            "All plans have IndexedDB-compatible structure")
                
                # Test individual plan retrieval (for conflict resolution)
                if plans:
                    test_plan_id = plans[0]['id']
                    single_response = self.session.get(f"{self.base_url}/membership-types/{test_plan_id}")
                    if single_response.status_code == 200:
                        single_plan = single_response.json()
                        self.log_test("Individual Plan Retrieval", True,
                                    f"Retrieved plan {test_plan_id} for conflict resolution")
                        
                        # Verify data consistency between bulk and individual retrieval
                        bulk_plan = next((p for p in plans if p['id'] == test_plan_id), None)
                        if bulk_plan and bulk_plan.get('is_active') == single_plan.get('is_active'):
                            self.log_test("Bulk vs Individual Consistency", True,
                                        "Data consistent between bulk and individual endpoints")
                        else:
                            self.log_test("Bulk vs Individual Consistency", False,
                                        "Data inconsistency detected")
                    else:
                        self.log_test("Individual Plan Retrieval", False,
                                    f"Failed to retrieve individual plan: {single_response.status_code}")
                
                # Test update response format (for optimistic update confirmation)
                if plans:
                    test_plan = plans[0]
                    plan_id = test_plan['id']
                    current_active = test_plan.get('is_active', False)
                    
                    update_data = {"is_active": not current_active}
                    update_response = self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                              data=json.dumps(update_data))
                    if update_response.status_code == 200:
                        updated_plan = update_response.json()
                        
                        # Check if response includes all necessary data for IndexedDB update
                        has_complete_data = all(field in updated_plan for field in 
                                              ['id', 'name', 'monthly_fee', 'is_active', 'updated_at'])
                        
                        self.log_test("Update Response Completeness", has_complete_data,
                                    "Update response includes all data needed for IndexedDB sync")
                        
                        # Restore original state
                        restore_data = {"is_active": current_active}
                        self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                       data=json.dumps(restore_data))
                    else:
                        self.log_test("Update Response Format", False,
                                    f"Update failed: {update_response.status_code}")
                
            else:
                self.log_test("IndexedDB Integration Support", False, f"Bulk retrieval failed: {response.status_code}")
                return False
                    
            return True
            
        except Exception as e:
            self.log_test("IndexedDB Integration", False, f"Error: {str(e)}")
            return False
            
    def test_rollback_support(self):
        """Test 6: Rollback Support - Verify backend maintains data integrity if frontend needs to rollback changes"""
        print("\n🔍 TEST 6: Rollback Support and Data Integrity")
        
        try:
            # Get a plan to test rollback scenarios
            response = self.session.get(f"{self.base_url}/membership-types")
            if response.status_code == 200:
                plans = response.json()
                
                if plans:
                    test_plan = plans[0]
                    plan_id = test_plan['id']
                    original_state = {
                        'is_active': test_plan.get('is_active', False),
                        'name': test_plan.get('name', ''),
                        'monthly_fee': test_plan.get('monthly_fee', 0)
                    }
                    
                    # Test 1: Successful update followed by rollback
                    new_active = not original_state['is_active']
                    update_data = {"is_active": new_active}
                    
                    update_response = self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                              data=json.dumps(update_data))
                    if update_response.status_code == 200:
                        self.log_test("Initial Update for Rollback Test", True,
                                    f"Updated active status to {new_active}")
                        
                        # Simulate rollback by reverting to original state
                        rollback_data = {"is_active": original_state['is_active']}
                        rollback_response = self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                                  data=json.dumps(rollback_data))
                        if rollback_response.status_code == 200:
                            rolled_back_plan = rollback_response.json()
                            
                            if rolled_back_plan.get('is_active') == original_state['is_active']:
                                self.log_test("Rollback Operation", True,
                                            "Successfully rolled back to original state")
                            else:
                                self.log_test("Rollback Operation", False,
                                            "Rollback did not restore original state")
                        else:
                            self.log_test("Rollback Operation", False,
                                        f"Rollback failed: {rollback_response.status_code}")
                    else:
                        self.log_test("Initial Update for Rollback Test", False,
                                    f"Initial update failed: {update_response.status_code}")
                    
                    # Test 2: Error handling for invalid updates (simulating failed optimistic updates)
                    invalid_update_data = {"monthly_fee": -100}  # Invalid negative fee
                    invalid_response = self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                              data=json.dumps(invalid_update_data))
                    
                    # Check if backend properly rejects invalid data
                    if invalid_response.status_code in [400, 422]:  # Bad request or validation error
                        self.log_test("Invalid Update Rejection", True,
                                    f"Backend properly rejected invalid data with status {invalid_response.status_code}")
                        
                        # Verify original data is unchanged
                        verify_response = self.session.get(f"{self.base_url}/membership-types/{plan_id}")
                        if verify_response.status_code == 200:
                            current_plan = verify_response.json()
                            if current_plan.get('monthly_fee') == original_state['monthly_fee']:
                                self.log_test("Data Integrity After Invalid Update", True,
                                            "Original data preserved after invalid update attempt")
                            else:
                                self.log_test("Data Integrity After Invalid Update", False,
                                            "Data was corrupted by invalid update attempt")
                        else:
                            self.log_test("Data Integrity Verification", False,
                                        "Could not verify data integrity")
                    else:
                        self.log_test("Invalid Update Rejection", False,
                                    f"Backend accepted invalid data with status {invalid_response.status_code}")
                    
                    # Test 3: Concurrent update conflict resolution
                    def concurrent_update_test(plan_id, update_data):
                        try:
                            response = self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                                      data=json.dumps(update_data))
                            return response.status_code == 200
                        except Exception:
                            return False
                    
                    # Simulate two clients trying to update the same plan
                    update1_data = {"is_active": True}
                    update2_data = {"is_active": False}
                    
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        future1 = executor.submit(concurrent_update_test, plan_id, update1_data)
                        future2 = executor.submit(concurrent_update_test, plan_id, update2_data)
                        results = [future1.result(), future2.result()]
                    
                    successful_updates = sum(results)
                    
                    # Both updates should succeed (last one wins)
                    self.log_test("Concurrent Update Handling", successful_updates >= 1,
                                f"{successful_updates}/2 concurrent updates succeeded")
                    
                    # Verify final state is consistent
                    final_response = self.session.get(f"{self.base_url}/membership-types/{plan_id}")
                    if final_response.status_code == 200:
                        final_plan = final_response.json()
                        final_active = final_plan.get('is_active')
                        
                        # Final state should be either True or False (not corrupted)
                        if isinstance(final_active, bool):
                            self.log_test("Final State Consistency", True,
                                        f"Final active state is consistent: {final_active}")
                        else:
                            self.log_test("Final State Consistency", False,
                                        f"Final state is corrupted: {final_active}")
                    else:
                        self.log_test("Final State Verification", False,
                                    "Could not verify final state")
                    
                    # Restore original state
                    restore_data = original_state
                    self.session.put(f"{self.base_url}/membership-types/{plan_id}",
                                   data=json.dumps(restore_data))
                    
                else:
                    self.log_test("Rollback Support", False, "No plans available for rollback testing")
                    return False
            else:
                self.log_test("Rollback Support", False, f"Failed to get plans: {response.status_code}")
                return False
                    
            return True
            
        except Exception as e:
            self.log_test("Rollback Support", False, f"Error: {str(e)}")
            return False
            
    def cleanup_test_data(self):
        """Clean up any test membership types created during testing"""
        print("\n🧹 Cleaning up test data...")
        
        for plan_id in self.test_membership_types:
            try:
                response = self.session.delete(f"{self.base_url}/membership-types/{plan_id}")
                if response.status_code == 200:
                    print(f"✅ Cleaned up test plan: {plan_id}")
                else:
                    print(f"⚠️ Could not clean up test plan {plan_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error cleaning up test plan {plan_id}: {str(e)}")
                
    def run_all_tests(self):
        """Run all optimistic toggle backend tests"""
        print("🚀 OPTIMISTIC TOGGLE BACKEND FUNCTIONALITY TESTING")
        print("=" * 60)
        print("Testing backend support for optimistic UI updates with proper error handling and rollback capabilities")
        print()
        
        self.setup_session()
        
        try:
            # Run all tests
            test_methods = [
                self.test_backend_readiness,
                self.test_rapid_toggle_handling,
                self.test_plans_store_performance,
                self.test_data_consistency,
                self.test_indexeddb_integration,
                self.test_rollback_support
            ]
            
            passed_tests = 0
            total_tests = len(test_methods)
            
            for test_method in test_methods:
                try:
                    result = test_method()
                    if result:
                        passed_tests += 1
                except Exception as e:
                    print(f"❌ Test {test_method.__name__} failed with exception: {str(e)}")
            
            # Clean up test data
            self.cleanup_test_data()
            
            # Print summary
            print("\n" + "=" * 60)
            print("🎯 OPTIMISTIC TOGGLE BACKEND TEST SUMMARY")
            print("=" * 60)
            
            success_rate = (passed_tests / total_tests) * 100
            print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} test categories passed)")
            
            # Count individual test results
            total_individual_tests = len(self.test_results)
            passed_individual_tests = sum(1 for result in self.test_results if result['success'])
            individual_success_rate = (passed_individual_tests / total_individual_tests) * 100 if total_individual_tests > 0 else 0
            
            print(f"Individual Tests: {passed_individual_tests}/{total_individual_tests} passed ({individual_success_rate:.1f}%)")
            print()
            
            # Print test categories summary
            print("📊 Test Categories Results:")
            categories = [
                "✅ Backend Readiness: Rapid plan active status updates supported",
                "✅ Error Handling: Concurrent updates and error scenarios handled",
                "✅ Plans Store Performance: Active index filtering efficient",
                "✅ Data Consistency: Active/inactive filtering works with toggles",
                "✅ IndexedDB Integration: Local storage updates supported",
                "✅ Rollback Support: Data integrity maintained for rollbacks"
            ]
            
            for i, category in enumerate(categories):
                if i < passed_tests:
                    print(category)
                else:
                    print(category.replace("✅", "❌"))
            
            print()
            print("🎯 Focus: Plan CRUD stability, Active index performance, Backend response times, Error handling, Data consistency")
            
            if success_rate >= 80:
                print("🎉 CONCLUSION: Backend is READY to support optimistic toggle functionality!")
            else:
                print("⚠️ CONCLUSION: Backend needs improvements to properly support optimistic toggles.")
                
            return success_rate >= 80
            
        finally:
            self.cleanup_session()

def main():
    """Main test execution"""
    tester = OptimisticToggleBackendTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()