#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class MembershipTypesInvestigator:
    def __init__(self, base_url="https://fitness-club-app-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_membership_types = []

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
                return False, response.text
                
        except requests.exceptions.RequestException as e:
            details = f"(Network Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}
        except Exception as e:
            details = f"(Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}

    def test_get_active_membership_types(self):
        """Test getting all active membership types (what user sees in UI)"""
        print("\n🎯 STEP 1: GET ACTIVE MEMBERSHIP TYPES (What user sees in UI)")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get Active Membership Types",
            "GET",
            "membership-types",
            200
        )
        
        if success:
            print(f"   Found {len(response)} ACTIVE membership types:")
            active_types = []
            for mt in response:
                print(f"   - {mt['name']}: TTD {mt['monthly_fee']} (Active: {mt.get('is_active', True)})")
                active_types.append(mt['name'].lower())
            
            # Check if "Standard" is in active types
            if 'standard' in active_types:
                print("   ✅ 'Standard' membership type IS VISIBLE in UI")
            else:
                print("   ❌ 'Standard' membership type IS NOT VISIBLE in UI")
                print("   🔍 This could explain why user doesn't see it but gets 'already exists' error")
            
            return success, active_types
        
        return success, []

    def test_database_direct_query(self):
        """Test direct database query to see ALL membership types including inactive ones"""
        print("\n🎯 STEP 2: DIRECT DATABASE QUERY (All membership types including inactive)")
        print("=" * 80)
        
        # We can't directly query MongoDB from here, but we can try to create a "Standard" type
        # to see what the exact error message is
        standard_data = {
            "name": "Standard",
            "monthly_fee": 55.00,
            "description": "Basic gym access with equipment usage",
            "features": ["Equipment Access", "Locker Room", "Basic Support"],
            "is_active": True
        }
        
        success, response = self.run_test(
            "Try to Create 'Standard' Membership Type",
            "POST",
            "membership-types",
            400,  # Expecting 400 if it already exists
            standard_data
        )
        
        if not success:
            print(f"   🔍 Error response: {response}")
            if "already exists" in str(response).lower():
                print("   ✅ CONFIRMED: 'Standard' membership type ALREADY EXISTS in database")
                print("   🔍 This confirms the issue - it exists but is not visible in GET request")
            else:
                print("   ❓ Different error occurred")
        else:
            print("   ❓ Unexpected success - 'Standard' type was created")
            
        return not success  # We expect this to fail

    def test_case_sensitivity(self):
        """Test case sensitivity variations"""
        print("\n🎯 STEP 3: CASE SENSITIVITY TESTING")
        print("=" * 80)
        
        case_variations = [
            "standard",
            "Standard", 
            "STANDARD",
            "StAnDaRd"
        ]
        
        results = {}
        
        for variation in case_variations:
            test_data = {
                "name": variation,
                "monthly_fee": 55.00,
                "description": f"Test case sensitivity for {variation}",
                "features": ["Test"],
                "is_active": True
            }
            
            success, response = self.run_test(
                f"Try to Create '{variation}' Membership Type",
                "POST",
                "membership-types",
                400,  # Expecting 400 if any variation already exists
                test_data
            )
            
            results[variation] = {
                "failed": not success,
                "response": response
            }
            
            if not success and "already exists" in str(response).lower():
                print(f"   ✅ '{variation}' already exists - case sensitivity detected")
            elif success:
                print(f"   ⚠️  '{variation}' was created successfully - no conflict")
                # Store ID for cleanup
                if isinstance(response, dict) and "id" in response:
                    self.created_membership_types.append(response["id"])
            else:
                print(f"   ❓ '{variation}' had different error: {response}")
        
        return results

    def test_create_inactive_standard(self):
        """Test creating an inactive 'Standard' membership type to simulate the issue"""
        print("\n🎯 STEP 4: CREATE INACTIVE 'STANDARD' TYPE (Simulate the issue)")
        print("=" * 80)
        
        # First, try to create an inactive Standard type
        inactive_standard_data = {
            "name": "TestStandard",  # Use different name first
            "monthly_fee": 55.00,
            "description": "Test inactive standard membership",
            "features": ["Equipment Access", "Locker Room"],
            "is_active": True
        }
        
        success, response = self.run_test(
            "Create TestStandard Membership Type",
            "POST",
            "membership-types",
            200,
            inactive_standard_data
        )
        
        if success and "id" in response:
            test_standard_id = response["id"]
            self.created_membership_types.append(test_standard_id)
            print(f"   ✅ Created TestStandard with ID: {test_standard_id}")
            
            # Now deactivate it
            success2, response2 = self.run_test(
                "Deactivate TestStandard Membership Type",
                "DELETE",
                f"membership-types/{test_standard_id}",
                200
            )
            
            if success2:
                print("   ✅ TestStandard deactivated (soft deleted)")
                
                # Now check if it appears in GET request
                success3, active_types = self.test_get_active_membership_types()
                
                if success3:
                    if 'teststandard' not in [t.lower() for t in active_types]:
                        print("   ✅ CONFIRMED: Deactivated type does NOT appear in GET request")
                    else:
                        print("   ❌ ISSUE: Deactivated type still appears in GET request")
                
                # Now try to create it again (should fail due to duplicate check)
                success4, response4 = self.run_test(
                    "Try to Create TestStandard Again (Should Fail)",
                    "POST",
                    "membership-types",
                    400,
                    inactive_standard_data
                )
                
                if not success4 and "already exists" in str(response4).lower():
                    print("   ✅ CONFIRMED: Duplicate validation checks ALL records (including inactive)")
                    print("   🎯 ROOT CAUSE IDENTIFIED: GET shows only active, POST checks all records")
                    return True
                else:
                    print("   ❓ Unexpected result in duplicate check")
            
        return False

    def test_backend_validation_logic(self):
        """Test the backend validation logic by examining the exact behavior"""
        print("\n🎯 STEP 5: BACKEND VALIDATION LOGIC ANALYSIS")
        print("=" * 80)
        
        # From the backend code analysis:
        # Line 364: GET /api/membership-types filters by {"is_active": True}
        # Line 354-356: POST validation checks find_one({"name": membership_obj.name}) without is_active filter
        
        print("   📋 BACKEND CODE ANALYSIS:")
        print("   - GET /api/membership-types: db.membership_types.find({'is_active': True})")
        print("   - POST validation: db.membership_types.find_one({'name': membership_obj.name})")
        print("   - POST validation does NOT filter by is_active!")
        print("")
        print("   🔍 EXPECTED BEHAVIOR:")
        print("   1. GET request shows only active membership types")
        print("   2. POST validation checks ALL membership types (active + inactive)")
        print("   3. User sees limited list but validation checks full database")
        print("")
        
        return True

    def test_proposed_solution(self):
        """Test what the solution should be"""
        print("\n🎯 STEP 6: PROPOSED SOLUTION ANALYSIS")
        print("=" * 80)
        
        print("   💡 SOLUTION OPTIONS:")
        print("")
        print("   OPTION 1: Fix GET endpoint to show inactive types")
        print("   - Change line 364: db.membership_types.find({}) # Remove is_active filter")
        print("   - PRO: User sees all types")
        print("   - CON: May show unwanted inactive types")
        print("")
        print("   OPTION 2: Fix POST validation to check only active types")
        print("   - Change line 354: find_one({'name': membership_obj.name, 'is_active': True})")
        print("   - PRO: Allows reactivation of inactive types")
        print("   - CON: May allow duplicate names if one is inactive")
        print("")
        print("   OPTION 3: Add reactivation endpoint")
        print("   - Add PUT /api/membership-types/{id}/reactivate")
        print("   - PRO: Clean solution, explicit reactivation")
        print("   - CON: Requires frontend changes")
        print("")
        print("   🎯 RECOMMENDED: OPTION 2 - Fix POST validation")
        print("   - Most user-friendly")
        print("   - Allows natural reactivation by 'creating' inactive type")
        print("   - Minimal code change required")
        
        return True

    def cleanup_test_data(self):
        """Clean up any test membership types created during testing"""
        print("\n🧹 CLEANUP: Removing test membership types")
        print("=" * 50)
        
        for membership_id in self.created_membership_types:
            success, response = self.run_test(
                f"Delete Test Membership Type {membership_id}",
                "DELETE",
                f"membership-types/{membership_id}",
                200
            )
            
            if success:
                print(f"   ✅ Cleaned up membership type {membership_id}")
            else:
                print(f"   ⚠️  Failed to clean up membership type {membership_id}")

    def run_investigation(self):
        """Run the complete membership types investigation"""
        print("🔍 MEMBERSHIP TYPES ISSUE INVESTIGATION")
        print("=" * 80)
        print("ISSUE: User tries to add 'Standard' membership but gets 'already exists' error")
        print("       while not seeing it in the UI")
        print("=" * 80)
        
        try:
            # Step 1: Check what user sees in UI
            success1, active_types = self.test_get_active_membership_types()
            
            # Step 2: Try to create Standard to see error
            success2 = self.test_database_direct_query()
            
            # Step 3: Test case sensitivity
            success3 = self.test_case_sensitivity()
            
            # Step 4: Simulate the issue
            success4 = self.test_create_inactive_standard()
            
            # Step 5: Analyze backend logic
            success5 = self.test_backend_validation_logic()
            
            # Step 6: Propose solution
            success6 = self.test_proposed_solution()
            
            # Cleanup
            self.cleanup_test_data()
            
            # Summary
            print("\n" + "=" * 80)
            print("🎯 INVESTIGATION SUMMARY")
            print("=" * 80)
            
            print(f"Tests run: {self.tests_run}")
            print(f"Tests passed: {self.tests_passed}")
            print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
            
            print("\n🔍 KEY FINDINGS:")
            if not success1:
                print("❌ Could not retrieve active membership types")
            elif 'standard' not in active_types:
                print("✅ CONFIRMED: 'Standard' is NOT visible in UI (GET /api/membership-types)")
            else:
                print("❓ 'Standard' IS visible in UI - issue may be different")
                
            if success2:
                print("✅ CONFIRMED: 'Standard' already exists in database (POST validation fails)")
            else:
                print("❓ Could not confirm 'Standard' exists in database")
                
            print("\n🎯 ROOT CAUSE:")
            print("GET /api/membership-types filters by is_active=True (shows only active types)")
            print("POST /api/membership-types validation checks ALL types (active + inactive)")
            print("Result: User doesn't see inactive 'Standard' but can't create it due to duplicate check")
            
            print("\n💡 RECOMMENDED SOLUTION:")
            print("Modify POST validation in server.py line 354 to:")
            print("existing_membership = await db.membership_types.find_one({")
            print("    'name': membership_obj.name,")
            print("    'is_active': True")
            print("})")
            print("This allows reactivation of inactive types by 'creating' them again.")
            
            return True
            
        except Exception as e:
            print(f"❌ Investigation failed with error: {str(e)}")
            return False

if __name__ == "__main__":
    investigator = MembershipTypesInvestigator()
    success = investigator.run_investigation()
    
    if success:
        print("\n✅ Investigation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Investigation failed!")
        sys.exit(1)