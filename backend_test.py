#!/usr/bin/env python3
"""
Backend Testing Script for Membership Types "Standard already exists but not visible" Issue Fix
Testing the implementation of:
1. Backend name normalization (trim + title case)
2. Case-insensitive duplicate checking for active membership types only
3. Frontend validation with local case-insensitive duplicate checking

Test Scenarios:
1. Get current membership types - See what's currently displayed
2. Try to create "Standard" - Should work now if no active "Standard" exists
3. Try to create "standard" (lowercase) - Should be normalized to "Standard" and either succeed or properly indicate duplicate
4. Try to create " Standard " (with spaces) - Should be normalized to "Standard"
5. Test case variations - Try "STANDARD", "StAnDaRd" etc to verify normalization
6. Verify error messages - Ensure clear, helpful error messages when duplicates exist
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://46206bdc-27f0-428b-bb53-27c7a4990807.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Backend URL: {BACKEND_URL}")
print(f"🕐 Test Started: {datetime.now().isoformat()}")
print("=" * 80)

class MembershipTypesTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        self.created_test_types = []
        
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
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
            
    def test_get_current_membership_types(self):
        """Test 1: Get current membership types - See what's currently displayed"""
        print("\n🔍 TEST 1: Get Current Membership Types")
        print("-" * 50)
        
        response = self.make_request("GET", "/membership-types")
        if not response:
            self.log_test("Get membership types", False, "Request failed")
            return []
            
        if response.status_code == 200:
            types = response.json()
            print(f"📊 Found {len(types)} active membership types:")
            for i, membership_type in enumerate(types, 1):
                name = membership_type.get('name', 'Unknown')
                fee = membership_type.get('monthly_fee', 0)
                print(f"   {i}. '{name}' - TTD {fee}/month")
                
            # Check for Standard variations
            standard_variations = [t for t in types if 'standard' in t.get('name', '').lower()]
            if standard_variations:
                print(f"🔍 Found {len(standard_variations)} Standard variations:")
                for var in standard_variations:
                    print(f"   - '{var.get('name')}' (TTD {var.get('monthly_fee')})")
            else:
                print("🔍 No Standard variations found")
                
            self.log_test("Get membership types", True, f"Retrieved {len(types)} types successfully")
            return types
        else:
            self.log_test("Get membership types", False, f"HTTP {response.status_code}: {response.text}")
            return []
            
    def test_create_standard_exact(self):
        """Test 2: Try to create "Standard" - Should work now if no active "Standard" exists"""
        print("\n🔍 TEST 2: Create 'Standard' (Exact Case)")
        print("-" * 50)
        
        test_data = {
            "name": "Standard",
            "monthly_fee": 55.0,
            "description": "Basic gym access with equipment usage",
            "features": ["Equipment Access", "Locker Room", "Basic Support"]
        }
        
        response = self.make_request("POST", "/membership-types", test_data)
        if not response:
            self.log_test("Create 'Standard'", False, "Request failed")
            return
            
        if response.status_code == 201:
            created_type = response.json()
            self.created_test_types.append(created_type.get('id'))
            self.log_test("Create 'Standard'", True, f"Created successfully with ID: {created_type.get('id')}")
            print(f"   📝 Name: '{created_type.get('name')}'")
            print(f"   📝 Fee: TTD {created_type.get('monthly_fee')}")
        elif response.status_code == 400:
            error_msg = response.json().get('detail', 'Unknown error')
            self.log_test("Create 'Standard'", True, f"Correctly rejected as duplicate: {error_msg}")
        else:
            self.log_test("Create 'Standard'", False, f"HTTP {response.status_code}: {response.text}")
            
    def test_create_standard_lowercase(self):
        """Test 3: Try to create "standard" (lowercase) - Should be normalized to "Standard" """
        print("\n🔍 TEST 3: Create 'standard' (Lowercase - Should Normalize)")
        print("-" * 50)
        
        test_data = {
            "name": "standard",
            "monthly_fee": 60.0,
            "description": "Basic gym access (lowercase test)",
            "features": ["Equipment Access"]
        }
        
        response = self.make_request("POST", "/membership-types", test_data)
        if not response:
            self.log_test("Create 'standard' (lowercase)", False, "Request failed")
            return
            
        if response.status_code == 201:
            created_type = response.json()
            normalized_name = created_type.get('name')
            if normalized_name == "Standard":
                self.created_test_types.append(created_type.get('id'))
                self.log_test("Create 'standard' (lowercase)", True, f"Correctly normalized to 'Standard'")
                print(f"   📝 Input: 'standard' → Output: '{normalized_name}'")
            else:
                self.log_test("Create 'standard' (lowercase)", False, f"Not normalized correctly: '{normalized_name}'")
        elif response.status_code == 400:
            error_msg = response.json().get('detail', 'Unknown error')
            if "Standard" in error_msg:
                self.log_test("Create 'standard' (lowercase)", True, f"Correctly detected duplicate after normalization: {error_msg}")
            else:
                self.log_test("Create 'standard' (lowercase)", False, f"Unexpected error message: {error_msg}")
        else:
            self.log_test("Create 'standard' (lowercase)", False, f"HTTP {response.status_code}: {response.text}")
            
    def test_create_standard_with_spaces(self):
        """Test 4: Try to create " Standard " (with spaces) - Should be normalized to "Standard" """
        print("\n🔍 TEST 4: Create ' Standard ' (With Spaces - Should Normalize)")
        print("-" * 50)
        
        test_data = {
            "name": " Standard ",
            "monthly_fee": 65.0,
            "description": "Basic gym access (spaces test)",
            "features": ["Equipment Access"]
        }
        
        response = self.make_request("POST", "/membership-types", test_data)
        if not response:
            self.log_test("Create ' Standard ' (with spaces)", False, "Request failed")
            return
            
        if response.status_code == 201:
            created_type = response.json()
            normalized_name = created_type.get('name')
            if normalized_name == "Standard":
                self.created_test_types.append(created_type.get('id'))
                self.log_test("Create ' Standard ' (with spaces)", True, f"Correctly normalized and trimmed to 'Standard'")
                print(f"   📝 Input: ' Standard ' → Output: '{normalized_name}'")
            else:
                self.log_test("Create ' Standard ' (with spaces)", False, f"Not normalized correctly: '{normalized_name}'")
        elif response.status_code == 400:
            error_msg = response.json().get('detail', 'Unknown error')
            if "Standard" in error_msg:
                self.log_test("Create ' Standard ' (with spaces)", True, f"Correctly detected duplicate after normalization: {error_msg}")
            else:
                self.log_test("Create ' Standard ' (with spaces)", False, f"Unexpected error message: {error_msg}")
        else:
            self.log_test("Create ' Standard ' (with spaces)", False, f"HTTP {response.status_code}: {response.text}")
            
    def test_case_variations(self):
        """Test 5: Test case variations - Try "STANDARD", "StAnDaRd" etc to verify normalization"""
        print("\n🔍 TEST 5: Test Case Variations")
        print("-" * 50)
        
        variations = [
            ("STANDARD", "All uppercase"),
            ("StAnDaRd", "Mixed case"),
            ("sTaNdArD", "Alternating case"),
            ("standard", "All lowercase again")
        ]
        
        for variation, description in variations:
            print(f"\n   Testing: '{variation}' ({description})")
            
            test_data = {
                "name": variation,
                "monthly_fee": 70.0,
                "description": f"Test variation: {description}",
                "features": ["Test Feature"]
            }
            
            response = self.make_request("POST", "/membership-types", test_data)
            if not response:
                self.log_test(f"Create '{variation}'", False, "Request failed")
                continue
                
            if response.status_code == 201:
                created_type = response.json()
                normalized_name = created_type.get('name')
                if normalized_name == "Standard":
                    self.created_test_types.append(created_type.get('id'))
                    self.log_test(f"Create '{variation}'", True, f"Correctly normalized to 'Standard'")
                    print(f"      📝 Input: '{variation}' → Output: '{normalized_name}'")
                else:
                    self.log_test(f"Create '{variation}'", False, f"Not normalized correctly: '{normalized_name}'")
            elif response.status_code == 400:
                error_msg = response.json().get('detail', 'Unknown error')
                if "Standard" in error_msg:
                    self.log_test(f"Create '{variation}'", True, f"Correctly detected duplicate: {error_msg}")
                else:
                    self.log_test(f"Create '{variation}'", False, f"Unexpected error: {error_msg}")
            else:
                self.log_test(f"Create '{variation}'", False, f"HTTP {response.status_code}: {response.text}")
                
    def test_unique_membership_type(self):
        """Test 6: Create a unique membership type to verify system is working"""
        print("\n🔍 TEST 6: Create Unique Membership Type")
        print("-" * 50)
        
        unique_name = f"TestType{datetime.now().strftime('%H%M%S')}"
        test_data = {
            "name": unique_name,
            "monthly_fee": 99.0,
            "description": "Test membership type for verification",
            "features": ["Test Feature 1", "Test Feature 2"]
        }
        
        response = self.make_request("POST", "/membership-types", test_data)
        if not response:
            self.log_test(f"Create unique type '{unique_name}'", False, "Request failed")
            return
            
        if response.status_code == 201:
            created_type = response.json()
            self.created_test_types.append(created_type.get('id'))
            self.log_test(f"Create unique type '{unique_name}'", True, "Successfully created unique membership type")
            print(f"   📝 Name: '{created_type.get('name')}'")
            print(f"   📝 Fee: TTD {created_type.get('monthly_fee')}")
        else:
            self.log_test(f"Create unique type '{unique_name}'", False, f"HTTP {response.status_code}: {response.text}")
            
    def test_error_messages(self):
        """Test 7: Verify error messages are clear and helpful"""
        print("\n🔍 TEST 7: Verify Error Messages")
        print("-" * 50)
        
        # Try to create a duplicate of an existing type
        test_data = {
            "name": "Standard",  # This should exist by now
            "monthly_fee": 50.0,
            "description": "Duplicate test",
            "features": []
        }
        
        response = self.make_request("POST", "/membership-types", test_data)
        if not response:
            self.log_test("Error message verification", False, "Request failed")
            return
            
        if response.status_code == 400:
            error_response = response.json()
            error_msg = error_response.get('detail', '')
            
            # Check if error message is clear and mentions the normalized name
            if "Standard" in error_msg and "already exists" in error_msg:
                self.log_test("Error message verification", True, f"Clear error message: {error_msg}")
            else:
                self.log_test("Error message verification", False, f"Unclear error message: {error_msg}")
        else:
            self.log_test("Error message verification", False, f"Expected 400 error, got {response.status_code}")
            
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n🧹 CLEANUP: Removing Test Data")
        print("-" * 50)
        
        cleanup_count = 0
        for type_id in self.created_test_types:
            response = self.make_request("DELETE", f"/membership-types/{type_id}")
            if response and response.status_code == 200:
                cleanup_count += 1
                print(f"   ✅ Deleted membership type: {type_id}")
            else:
                print(f"   ❌ Failed to delete membership type: {type_id}")
                
        print(f"🧹 Cleaned up {cleanup_count}/{len(self.created_test_types)} test membership types")
        
    def run_all_tests(self):
        """Run all membership types tests"""
        print("🚀 STARTING MEMBERSHIP TYPES 'STANDARD ALREADY EXISTS' FIX TESTING")
        print("=" * 80)
        
        # Test sequence
        current_types = self.test_get_current_membership_types()
        self.test_create_standard_exact()
        self.test_create_standard_lowercase()
        self.test_create_standard_with_spaces()
        self.test_case_variations()
        self.test_unique_membership_type()
        self.test_error_messages()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
                    
        # Key expectations verification
        print("\n🎯 KEY EXPECTATIONS VERIFICATION:")
        print("-" * 50)
        
        expectations = [
            "Name normalization should work (trim + title case)",
            "Only active membership types should be checked for duplicates", 
            "Case-insensitive matching should prevent 'Standard' vs 'standard' conflicts",
            "Clear error messages should indicate which normalized name already exists"
        ]
        
        for expectation in expectations:
            print(f"📋 {expectation}")
            
        # Cleanup
        if self.created_test_types:
            self.cleanup_test_data()
            
        print(f"\n🏁 Testing completed at: {datetime.now().isoformat()}")
        
        return success_rate >= 80  # Consider 80%+ success rate as passing

def main():
    """Main test execution"""
    try:
        tester = MembershipTypesTester(BACKEND_URL)
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 MEMBERSHIP TYPES FIX TESTING: OVERALL SUCCESS!")
            sys.exit(0)
        else:
            print("\n🚨 MEMBERSHIP TYPES FIX TESTING: ISSUES DETECTED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()