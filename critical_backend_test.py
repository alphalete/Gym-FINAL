#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class CriticalFunctionalityTester:
    def __init__(self, base_url="https://a2eb3b6a-2c20-4e9f-b52b-bd4f318d28fc.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_membership_types = []
        self.created_client_id = None

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

    def test_membership_type_crud_complete(self):
        """Test complete CRUD cycle for membership types"""
        print("\n🎯 CRITICAL TEST: MEMBERSHIP TYPE CRUD OPERATIONS")
        print("=" * 80)
        
        # 1. GET - List all membership types (should work)
        success1, response1 = self.run_test(
            "1. GET /api/membership-types (List All)",
            "GET",
            "membership-types",
            200
        )
        
        if success1:
            print(f"   Found {len(response1)} existing membership types")
            for mt in response1:
                print(f"   - {mt['name']}: TTD {mt['monthly_fee']} ({mt['description']})")
        
        # 2. POST - Create new membership type
        new_membership_data = {
            "name": "Test Membership Type",
            "monthly_fee": 85.00,
            "description": "Test membership for CRUD testing",
            "features": ["Equipment Access", "Test Feature", "CRUD Testing"],
            "is_active": True
        }
        
        success2, response2 = self.run_test(
            "2. POST /api/membership-types (Create New)",
            "POST",
            "membership-types",
            200,
            new_membership_data
        )
        
        membership_id = None
        if success2 and "id" in response2:
            membership_id = response2["id"]
            self.created_membership_types.append(membership_id)
            print(f"   Created membership type ID: {membership_id}")
            print(f"   Name: {response2['name']}")
            print(f"   Fee: TTD {response2['monthly_fee']}")
            
            # Verify currency is numeric (not string with $ symbol)
            monthly_fee = response2.get('monthly_fee')
            if isinstance(monthly_fee, (int, float)):
                print(f"   ✅ Currency field is numeric: {monthly_fee} (ready for TTD display)")
            else:
                print(f"   ❌ Currency field is not numeric: {monthly_fee} (type: {type(monthly_fee)})")
        
        if not membership_id:
            print("❌ Cannot continue CRUD test - membership type creation failed")
            return False
        
        # 3. GET - Retrieve specific membership type
        success3, response3 = self.run_test(
            "3. GET /api/membership-types/{id} (Get Specific)",
            "GET",
            f"membership-types/{membership_id}",
            200
        )
        
        if success3:
            print(f"   Retrieved: {response3.get('name')} - TTD {response3.get('monthly_fee')}")
        
        # 4. PUT - Update membership type
        update_data = {
            "monthly_fee": 95.00,
            "description": "Updated test membership with new price",
            "features": ["Equipment Access", "Updated Feature", "CRUD Testing", "New Feature"]
        }
        
        success4, response4 = self.run_test(
            "4. PUT /api/membership-types/{id} (Update Existing)",
            "PUT",
            f"membership-types/{membership_id}",
            200,
            update_data
        )
        
        if success4:
            print(f"   Updated fee: TTD {response4.get('monthly_fee')}")
            print(f"   Updated description: {response4.get('description')}")
            
            # Verify currency is still numeric after update
            monthly_fee = response4.get('monthly_fee')
            if isinstance(monthly_fee, (int, float)):
                print(f"   ✅ Currency field remains numeric after update: {monthly_fee}")
            else:
                print(f"   ❌ Currency field corrupted after update: {monthly_fee}")
        
        # 5. DELETE - Soft delete membership type (CRITICAL - User reported this doesn't work)
        success5, response5 = self.run_test(
            "5. DELETE /api/membership-types/{id} (Soft Delete - CRITICAL)",
            "DELETE",
            f"membership-types/{membership_id}",
            200
        )
        
        if success5:
            print(f"   Deletion message: {response5.get('message')}")
            print("   ✅ CRITICAL: Membership type deletion endpoint is working!")
        else:
            print("   ❌ CRITICAL: Membership type deletion endpoint is NOT working!")
            print("   This explains why user can't delete membership types!")
        
        # 6. Verify soft delete - membership should not appear in active list
        success6, response6 = self.run_test(
            "6. Verify Soft Delete - Check Active List",
            "GET",
            "membership-types",
            200
        )
        
        if success6:
            deleted_found = False
            for mt in response6:
                if mt.get('id') == membership_id:
                    deleted_found = True
                    break
            
            if not deleted_found:
                print("   ✅ Soft delete working - deleted membership not in active list")
            else:
                print("   ❌ Soft delete NOT working - deleted membership still in active list")
                return False
        
        # 7. Try to retrieve deleted membership directly (should still exist but inactive)
        success7, response7 = self.run_test(
            "7. Try to Get Deleted Membership Directly",
            "GET",
            f"membership-types/{membership_id}",
            200  # Should still exist but be inactive
        )
        
        if success7:
            is_active = response7.get('is_active')
            if is_active is False:
                print("   ✅ Soft delete confirmed - membership exists but is_active=False")
            else:
                print(f"   ❌ Soft delete issue - is_active={is_active} (should be False)")
        
        return success1 and success2 and success3 and success4 and success5 and success6

    def test_client_status_updates(self):
        """Test client status updates (ACTIVATE/DEACTIVATE functionality)"""
        print("\n🎯 CRITICAL TEST: CLIENT STATUS UPDATES")
        print("=" * 80)
        
        # Create a test client first
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Status Test Client",
            "email": f"status_test_{timestamp}@example.com",
            "phone": "(555) 123-4567",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-25",
            "status": "Active"
        }
        
        success1, response1 = self.run_test(
            "1. Create Test Client for Status Updates",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if not success1 or "id" not in response1:
            print("❌ Cannot test client status updates - client creation failed")
            return False
        
        client_id = response1["id"]
        self.created_client_id = client_id
        print(f"   Created test client ID: {client_id}")
        print(f"   Initial status: {response1.get('status')}")
        
        # Test DEACTIVATE (Active -> Inactive)
        deactivate_data = {
            "status": "Inactive"
        }
        
        success2, response2 = self.run_test(
            "2. DEACTIVATE Client (Active -> Inactive)",
            "PUT",
            f"clients/{client_id}",
            200,
            deactivate_data
        )
        
        if success2:
            new_status = response2.get('status')
            print(f"   Status after deactivation: {new_status}")
            if new_status == "Inactive":
                print("   ✅ DEACTIVATE functionality working correctly")
            else:
                print(f"   ❌ DEACTIVATE failed - status is {new_status}, expected Inactive")
                return False
        else:
            print("   ❌ DEACTIVATE functionality NOT working")
            return False
        
        # Test ACTIVATE (Inactive -> Active)
        activate_data = {
            "status": "Active"
        }
        
        success3, response3 = self.run_test(
            "3. ACTIVATE Client (Inactive -> Active)",
            "PUT",
            f"clients/{client_id}",
            200,
            activate_data
        )
        
        if success3:
            new_status = response3.get('status')
            print(f"   Status after activation: {new_status}")
            if new_status == "Active":
                print("   ✅ ACTIVATE functionality working correctly")
            else:
                print(f"   ❌ ACTIVATE failed - status is {new_status}, expected Active")
                return False
        else:
            print("   ❌ ACTIVATE functionality NOT working")
            return False
        
        # Verify status persists when getting client
        success4, response4 = self.run_test(
            "4. Verify Status Persistence",
            "GET",
            f"clients/{client_id}",
            200
        )
        
        if success4:
            persisted_status = response4.get('status')
            print(f"   Persisted status: {persisted_status}")
            if persisted_status == "Active":
                print("   ✅ Status updates persist correctly")
            else:
                print(f"   ❌ Status persistence failed - got {persisted_status}")
                return False
        
        return success1 and success2 and success3 and success4

    def test_currency_display_backend(self):
        """Test that backend returns proper numeric values for TTD currency display"""
        print("\n🎯 CRITICAL TEST: CURRENCY DISPLAY (Backend Numeric Values)")
        print("=" * 80)
        
        # Test membership types return numeric values
        success1, response1 = self.run_test(
            "1. Check Membership Types Currency Fields",
            "GET",
            "membership-types",
            200
        )
        
        currency_issues = []
        if success1:
            for mt in response1:
                monthly_fee = mt.get('monthly_fee')
                if not isinstance(monthly_fee, (int, float)):
                    currency_issues.append(f"Membership '{mt.get('name')}': {monthly_fee} (type: {type(monthly_fee)})")
                else:
                    print(f"   ✅ {mt.get('name')}: {monthly_fee} (numeric - ready for TTD display)")
        
        # Test clients return numeric values
        success2, response2 = self.run_test(
            "2. Check Clients Currency Fields",
            "GET",
            "clients",
            200
        )
        
        if success2:
            for client in response2:
                monthly_fee = client.get('monthly_fee')
                if not isinstance(monthly_fee, (int, float)):
                    currency_issues.append(f"Client '{client.get('name')}': {monthly_fee} (type: {type(monthly_fee)})")
                else:
                    print(f"   ✅ {client.get('name')}: {monthly_fee} (numeric - ready for TTD display)")
        
        # Create a new client to test currency handling
        if self.created_client_id:
            success3, response3 = self.run_test(
                "3. Check Specific Client Currency Field",
                "GET",
                f"clients/{self.created_client_id}",
                200
            )
            
            if success3:
                monthly_fee = response3.get('monthly_fee')
                if isinstance(monthly_fee, (int, float)):
                    print(f"   ✅ Test client monthly_fee: {monthly_fee} (numeric)")
                else:
                    currency_issues.append(f"Test client: {monthly_fee} (type: {type(monthly_fee)})")
        
        if currency_issues:
            print("\n   ❌ CURRENCY ISSUES FOUND:")
            for issue in currency_issues:
                print(f"      - {issue}")
            print("   Backend is not returning proper numeric values for TTD display!")
            return False
        else:
            print("\n   ✅ ALL CURRENCY FIELDS ARE NUMERIC")
            print("   Backend is properly returning numeric values for TTD currency display")
            return True

    def test_add_member_form_data_refresh(self):
        """Test that membership types are available for Add Member form"""
        print("\n🎯 CRITICAL TEST: ADD MEMBER FORM DATA REFRESH")
        print("=" * 80)
        
        # This tests the backend endpoint that the Add Member form uses
        success1, response1 = self.run_test(
            "1. GET Membership Types for Add Member Form",
            "GET",
            "membership-types",
            200
        )
        
        if not success1:
            print("   ❌ Add Member form cannot get membership types!")
            return False
        
        membership_types = response1
        print(f"   Available membership types for Add Member form: {len(membership_types)}")
        
        if len(membership_types) == 0:
            print("   ❌ No membership types available for Add Member form!")
            return False
        
        # Display available types
        for mt in membership_types:
            print(f"   - {mt['name']}: TTD {mt['monthly_fee']} (Active: {mt.get('is_active', True)})")
        
        # Verify all returned types are active
        inactive_types = [mt for mt in membership_types if not mt.get('is_active', True)]
        if inactive_types:
            print(f"   ❌ Found {len(inactive_types)} inactive types in active list!")
            for mt in inactive_types:
                print(f"      - {mt['name']} (is_active: {mt.get('is_active')})")
            return False
        
        print("   ✅ All membership types are active and available for Add Member form")
        
        # Test creating a client with one of the available membership types
        if membership_types:
            test_membership = membership_types[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            client_data = {
                "name": "Add Member Form Test",
                "email": f"add_member_test_{timestamp}@example.com",
                "phone": "(555) 123-4567",
                "membership_type": test_membership['name'],
                "monthly_fee": test_membership['monthly_fee'],
                "start_date": "2025-01-25"
            }
            
            success2, response2 = self.run_test(
                "2. Create Client Using Available Membership Type",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success2:
                print(f"   ✅ Successfully created client with membership: {test_membership['name']}")
                print("   Add Member form should work with available membership types")
                return True
            else:
                print("   ❌ Failed to create client with available membership type")
                return False
        
        return success1

    def test_dashboard_data_endpoints(self):
        """Test endpoints that provide dashboard statistics"""
        print("\n🎯 CRITICAL TEST: DASHBOARD DATA ENDPOINTS")
        print("=" * 80)
        
        # Test clients endpoint (provides client count and revenue data)
        success1, response1 = self.run_test(
            "1. GET Clients for Dashboard Stats",
            "GET",
            "clients",
            200
        )
        
        dashboard_stats = {
            "total_clients": 0,
            "active_clients": 0,
            "inactive_clients": 0,
            "total_monthly_revenue": 0,
            "active_monthly_revenue": 0
        }
        
        if success1:
            clients = response1
            dashboard_stats["total_clients"] = len(clients)
            
            for client in clients:
                status = client.get('status', 'Active')
                monthly_fee = client.get('monthly_fee', 0)
                
                if status == 'Active':
                    dashboard_stats["active_clients"] += 1
                    dashboard_stats["active_monthly_revenue"] += monthly_fee
                else:
                    dashboard_stats["inactive_clients"] += 1
                
                dashboard_stats["total_monthly_revenue"] += monthly_fee
            
            print(f"   📊 DASHBOARD STATISTICS:")
            print(f"      Total Clients: {dashboard_stats['total_clients']}")
            print(f"      Active Clients: {dashboard_stats['active_clients']}")
            print(f"      Inactive Clients: {dashboard_stats['inactive_clients']}")
            print(f"      Total Monthly Revenue: TTD {dashboard_stats['total_monthly_revenue']:.2f}")
            print(f"      Active Monthly Revenue: TTD {dashboard_stats['active_monthly_revenue']:.2f}")
            
            # Check if dashboard would show zeros (the user's complaint)
            if dashboard_stats["total_clients"] == 0:
                print("   ⚠️  Dashboard would show 0 clients (no data)")
            elif dashboard_stats["active_monthly_revenue"] == 0:
                print("   ⚠️  Dashboard would show TTD 0 revenue (no active clients or fees)")
            else:
                print("   ✅ Dashboard should show proper non-zero statistics")
        
        # Test membership types endpoint (provides membership type count)
        success2, response2 = self.run_test(
            "2. GET Membership Types for Dashboard Stats",
            "GET",
            "membership-types",
            200
        )
        
        if success2:
            membership_types = response2
            dashboard_stats["total_membership_types"] = len(membership_types)
            print(f"      Total Membership Types: {dashboard_stats['total_membership_types']}")
            
            if dashboard_stats["total_membership_types"] == 0:
                print("   ⚠️  Dashboard would show 0 membership types")
            else:
                print("   ✅ Dashboard should show proper membership type count")
        
        # Summary
        has_data = (dashboard_stats["total_clients"] > 0 and 
                   dashboard_stats["active_monthly_revenue"] > 0 and 
                   dashboard_stats["total_membership_types"] > 0)
        
        if has_data:
            print("\n   ✅ DASHBOARD DATA: Backend provides proper non-zero statistics")
            print("   If dashboard shows zeros, it's likely a frontend display issue")
            return True
        else:
            print("\n   ⚠️  DASHBOARD DATA: Backend has limited data, may show zeros")
            print("   Dashboard zeros might be due to lack of data, not backend issues")
            return success1 and success2

    def run_critical_tests(self):
        """Run all critical functionality tests"""
        print("🚀 STARTING CRITICAL FUNCTIONAL ISSUES TESTING")
        print("=" * 80)
        print("Testing the specific issues reported by the user:")
        print("1. Membership Type Deletion")
        print("2. Membership Type CRUD Operations") 
        print("3. Currency Display (Backend Numeric Values)")
        print("4. Client Status Updates (ACTIVATE/DEACTIVATE)")
        print("5. Dashboard Data Endpoints")
        print("6. Add Member Form Data Refresh")
        print("=" * 80)
        
        # Run all critical tests
        test_results = []
        
        test_results.append(("Membership Type CRUD Complete", self.test_membership_type_crud_complete()))
        test_results.append(("Client Status Updates", self.test_client_status_updates()))
        test_results.append(("Currency Display Backend", self.test_currency_display_backend()))
        test_results.append(("Add Member Form Data Refresh", self.test_add_member_form_data_refresh()))
        test_results.append(("Dashboard Data Endpoints", self.test_dashboard_data_endpoints()))
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 CRITICAL FUNCTIONAL ISSUES TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = 0
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall Results: {passed_tests}/{len(test_results)} critical tests passed")
        print(f"Success Rate: {(passed_tests/len(test_results)*100):.1f}%")
        
        if passed_tests == len(test_results):
            print("\n🎉 ALL CRITICAL FUNCTIONALITY TESTS PASSED!")
            print("Backend APIs are working correctly for the reported issues.")
        else:
            print(f"\n⚠️  {len(test_results) - passed_tests} CRITICAL ISSUES FOUND!")
            print("These backend issues need to be addressed.")
        
        return passed_tests == len(test_results)

if __name__ == "__main__":
    print("🔧 CRITICAL BACKEND FUNCTIONALITY TESTER")
    print("Testing specific issues reported by the user")
    print("=" * 80)
    
    tester = CriticalFunctionalityTester()
    success = tester.run_critical_tests()
    
    if success:
        print("\n✅ All critical backend functionality is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Critical backend issues found that need attention!")
        sys.exit(1)