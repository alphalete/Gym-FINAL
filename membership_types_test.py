#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any

class MembershipTypesAPITester:
    def __init__(self, base_url="https://alphalete-pwa.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_membership_type_ids = []
        
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
                    details = f"(Expected {expected_status}, got {response.status_code}) - {response.text[:200]}"
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

    def test_api_health_check(self):
        """Test API health check"""
        print("\n🏥 TESTING API HEALTH CHECK")
        print("=" * 60)
        
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "health",
            200
        )
        if success and "message" in response:
            print(f"   Health message: {response['message']}")
        return success

    def test_get_membership_types_initial(self):
        """Test getting all membership types initially"""
        print("\n📋 TESTING INITIAL MEMBERSHIP TYPES RETRIEVAL")
        print("=" * 60)
        
        success, response = self.run_test(
            "Get All Membership Types (Initial)",
            "GET",
            "membership-types",
            200
        )
        if success:
            print(f"   Found {len(response)} membership types initially:")
            for mt in response:
                print(f"   - {mt['name']}: TTD {mt['monthly_fee']} ({mt['description']})")
                print(f"     Features: {', '.join(mt.get('features', []))}")
                print(f"     Active: {mt.get('is_active', True)}")
        return success, response

    def test_create_test_premium_membership(self):
        """Test creating the specific membership type from review request"""
        print("\n🆕 TESTING MEMBERSHIP TYPE CREATION - TEST PREMIUM")
        print("=" * 60)
        
        # Use the exact sample data from the review request
        test_premium_data = {
            "name": "Test Premium",
            "monthly_fee": 99.99,
            "description": "Test premium membership",
            "features": ["Premium Equipment Access", "Personal Training Sessions", "Nutrition Consultation", "Priority Booking"],
            "is_active": True
        }
        
        success, response = self.run_test(
            "Create Test Premium Membership Type",
            "POST",
            "membership-types",
            200,
            test_premium_data
        )
        
        if success and "id" in response:
            self.created_membership_type_ids.append(response["id"])
            print(f"   ✅ Created membership type ID: {response['id']}")
            print(f"   Name: {response['name']}")
            print(f"   Fee: TTD {response['monthly_fee']}")
            print(f"   Description: {response['description']}")
            print(f"   Features: {', '.join(response.get('features', []))}")
            print(f"   Active: {response.get('is_active', True)}")
            
            # Verify all fields match what was sent
            if (response['name'] == test_premium_data['name'] and
                response['monthly_fee'] == test_premium_data['monthly_fee'] and
                response['description'] == test_premium_data['description'] and
                response['is_active'] == test_premium_data['is_active']):
                print("   ✅ All fields saved correctly!")
            else:
                print("   ❌ Some fields were not saved correctly!")
                return False
        
        return success

    def test_verify_membership_type_saved(self):
        """Test that the created membership type is actually saved and retrievable"""
        print("\n🔍 TESTING MEMBERSHIP TYPE PERSISTENCE")
        print("=" * 60)
        
        if not self.created_membership_type_ids:
            print("❌ No membership type ID available for verification")
            return False
            
        membership_id = self.created_membership_type_ids[0]
        
        # Test individual retrieval
        success1, response1 = self.run_test(
            "Get Specific Test Premium Membership Type",
            "GET",
            f"membership-types/{membership_id}",
            200
        )
        
        if success1:
            print(f"   ✅ Retrieved: {response1.get('name')} - TTD {response1.get('monthly_fee')}")
            print(f"   Description: {response1.get('description')}")
            print(f"   Features: {', '.join(response1.get('features', []))}")
        
        # Test that it appears in the list
        success2, response2 = self.run_test(
            "Verify Test Premium in Membership Types List",
            "GET",
            "membership-types",
            200
        )
        
        if success2:
            found_test_premium = False
            for mt in response2:
                if mt.get('id') == membership_id:
                    found_test_premium = True
                    print(f"   ✅ Found Test Premium in list: {mt['name']} - TTD {mt['monthly_fee']}")
                    break
            
            if not found_test_premium:
                print("   ❌ Test Premium not found in membership types list!")
                return False
        
        return success1 and success2

    def test_update_membership_type(self):
        """Test updating the created membership type"""
        print("\n✏️ TESTING MEMBERSHIP TYPE UPDATE")
        print("=" * 60)
        
        if not self.created_membership_type_ids:
            print("❌ No membership type ID available for update")
            return False
            
        membership_id = self.created_membership_type_ids[0]
        
        # Update the membership type
        update_data = {
            "monthly_fee": 109.99,
            "description": "Updated test premium membership with enhanced features",
            "features": ["Premium Equipment Access", "Personal Training Sessions", "Nutrition Consultation", "Priority Booking", "VIP Lounge Access"]
        }
        
        success, response = self.run_test(
            "Update Test Premium Membership Type",
            "PUT",
            f"membership-types/{membership_id}",
            200,
            update_data
        )
        
        if success:
            print(f"   ✅ Updated fee: TTD {response.get('monthly_fee')}")
            print(f"   ✅ Updated description: {response.get('description')}")
            print(f"   ✅ Updated features: {', '.join(response.get('features', []))}")
            
            # Verify the updates were saved
            if (response.get('monthly_fee') == update_data['monthly_fee'] and
                response.get('description') == update_data['description']):
                print("   ✅ Updates saved correctly!")
            else:
                print("   ❌ Updates were not saved correctly!")
                return False
        
        return success

    def test_verify_update_persistence(self):
        """Test that the updates are actually persisted"""
        print("\n🔄 TESTING UPDATE PERSISTENCE")
        print("=" * 60)
        
        if not self.created_membership_type_ids:
            print("❌ No membership type ID available for verification")
            return False
            
        membership_id = self.created_membership_type_ids[0]
        
        success, response = self.run_test(
            "Verify Updates Persisted",
            "GET",
            f"membership-types/{membership_id}",
            200
        )
        
        if success:
            print(f"   ✅ Verified fee: TTD {response.get('monthly_fee')}")
            print(f"   ✅ Verified description: {response.get('description')}")
            print(f"   ✅ Verified features count: {len(response.get('features', []))}")
            
            # Check if the updated values are correct
            if response.get('monthly_fee') == 109.99:
                print("   ✅ Fee update persisted correctly!")
            else:
                print(f"   ❌ Fee update not persisted! Expected 109.99, got {response.get('monthly_fee')}")
                return False
        
        return success

    def test_create_additional_membership_types(self):
        """Test creating additional membership types to verify system can handle multiple"""
        print("\n🔢 TESTING MULTIPLE MEMBERSHIP TYPE CREATION")
        print("=" * 60)
        
        additional_types = [
            {
                "name": "Test Basic",
                "monthly_fee": 49.99,
                "description": "Basic test membership",
                "features": ["Equipment Access", "Locker Room"],
                "is_active": True
            },
            {
                "name": "Test Elite",
                "monthly_fee": 149.99,
                "description": "Elite test membership",
                "features": ["All Premium Features", "Personal Trainer", "Massage Therapy"],
                "is_active": True
            }
        ]
        
        all_success = True
        
        for i, membership_data in enumerate(additional_types, 1):
            success, response = self.run_test(
                f"Create Additional Membership Type {i} - {membership_data['name']}",
                "POST",
                "membership-types",
                200,
                membership_data
            )
            
            if success and "id" in response:
                self.created_membership_type_ids.append(response["id"])
                print(f"   ✅ Created {response['name']}: TTD {response['monthly_fee']}")
            else:
                all_success = False
        
        return all_success

    def test_duplicate_name_prevention(self):
        """Test that duplicate membership type names are prevented"""
        print("\n🚫 TESTING DUPLICATE NAME PREVENTION")
        print("=" * 60)
        
        # Try to create a membership type with the same name as "Test Premium"
        duplicate_data = {
            "name": "Test Premium",  # Same name as previously created
            "monthly_fee": 79.99,
            "description": "Duplicate test premium membership",
            "features": ["Basic Features"],
            "is_active": True
        }
        
        success, response = self.run_test(
            "Create Duplicate Membership Type (Should Fail)",
            "POST",
            "membership-types",
            400,  # Should return 400 Bad Request
            duplicate_data
        )
        
        return success

    def test_validation_errors(self):
        """Test various validation scenarios"""
        print("\n⚠️ TESTING VALIDATION ERRORS")
        print("=" * 60)
        
        # Test missing required fields
        invalid_data = {
            "description": "Missing name and monthly_fee",
            "features": ["Some features"],
            "is_active": True
        }
        
        success1, response1 = self.run_test(
            "Create Membership Type with Missing Required Fields",
            "POST",
            "membership-types",
            422,  # Should return 422 Validation Error
            invalid_data
        )
        
        # Test invalid monthly_fee (negative)
        invalid_fee_data = {
            "name": "Invalid Fee Test",
            "monthly_fee": -10.00,
            "description": "Negative fee test",
            "features": ["Some features"],
            "is_active": True
        }
        
        success2, response2 = self.run_test(
            "Create Membership Type with Invalid Fee",
            "POST",
            "membership-types",
            422,  # Should return 422 Validation Error
            invalid_fee_data
        )
        
        return success1 and success2

    def test_get_all_membership_types_final(self):
        """Test getting all membership types after all creations"""
        print("\n📊 TESTING FINAL MEMBERSHIP TYPES LIST")
        print("=" * 60)
        
        success, response = self.run_test(
            "Get All Membership Types (Final)",
            "GET",
            "membership-types",
            200
        )
        
        if success:
            print(f"   ✅ Total membership types: {len(response)}")
            print("   📋 Complete list:")
            for i, mt in enumerate(response, 1):
                print(f"   {i}. {mt['name']}: TTD {mt['monthly_fee']}")
                print(f"      Description: {mt['description']}")
                print(f"      Features: {', '.join(mt.get('features', []))}")
                print(f"      Active: {mt.get('is_active', True)}")
                print(f"      ID: {mt.get('id', 'N/A')}")
                print()
            
            # Verify our created membership types are in the list
            created_names = ["Test Premium", "Test Basic", "Test Elite"]
            found_count = 0
            for mt in response:
                if mt['name'] in created_names:
                    found_count += 1
            
            print(f"   ✅ Found {found_count} of our created membership types in the list")
            if found_count == len(created_names):
                print("   ✅ All created membership types are properly saved and retrievable!")
            else:
                print("   ❌ Some created membership types are missing from the list!")
                return False
        
        return success

    def test_database_persistence_verification(self):
        """Test that data persists across multiple API calls"""
        print("\n💾 TESTING DATABASE PERSISTENCE")
        print("=" * 60)
        
        if not self.created_membership_type_ids:
            print("❌ No membership type IDs available for persistence testing")
            return False
        
        all_success = True
        
        # Test each created membership type individually
        for i, membership_id in enumerate(self.created_membership_type_ids, 1):
            success, response = self.run_test(
                f"Verify Persistence - Membership Type {i}",
                "GET",
                f"membership-types/{membership_id}",
                200
            )
            
            if success:
                print(f"   ✅ Membership Type {i} persisted: {response.get('name')} - TTD {response.get('monthly_fee')}")
            else:
                all_success = False
                print(f"   ❌ Membership Type {i} not found in database!")
        
        return all_success

    def run_comprehensive_membership_types_test(self):
        """Run all membership types tests"""
        print("\n" + "="*80)
        print("🎯 MEMBERSHIP TYPES FUNCTIONALITY COMPREHENSIVE TESTING")
        print("   Testing membership plans saving issue reported by user")
        print("="*80)
        
        # Test sequence
        tests = [
            self.test_api_health_check,
            self.test_get_membership_types_initial,
            self.test_create_test_premium_membership,
            self.test_verify_membership_type_saved,
            self.test_update_membership_type,
            self.test_verify_update_persistence,
            self.test_create_additional_membership_types,
            self.test_duplicate_name_prevention,
            self.test_validation_errors,
            self.test_get_all_membership_types_final,
            self.test_database_persistence_verification
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
                self.tests_run += 1
        
        # Print summary
        print("\n" + "="*80)
        print("📊 MEMBERSHIP TYPES TESTING SUMMARY")
        print("="*80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! Membership types functionality is working correctly.")
            print("✅ Membership plans ARE saving when created")
            print("✅ GET /api/membership-types endpoint is working")
            print("✅ POST /api/membership-types endpoint can create new membership types")
            print("✅ PUT /api/membership-types/{id} endpoint can update existing membership types")
            print("✅ Data is being properly saved to the database")
        else:
            print(f"\n❌ {self.tests_run - self.tests_passed} TESTS FAILED!")
            print("❌ There are issues with membership types functionality")
            
        print(f"\nCreated membership type IDs: {self.created_membership_type_ids}")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    print("🚀 Starting Membership Types API Testing...")
    print("🎯 Focus: Testing membership plans saving issue")
    
    tester = MembershipTypesAPITester()
    success = tester.run_comprehensive_membership_types_test()
    
    if success:
        print("\n✅ CONCLUSION: Membership types functionality is working correctly!")
        print("   The user's issue may be frontend-related or resolved.")
        sys.exit(0)
    else:
        print("\n❌ CONCLUSION: Issues found with membership types functionality!")
        print("   Backend API has problems that need to be addressed.")
        sys.exit(1)