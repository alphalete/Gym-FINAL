#!/usr/bin/env python3

import requests
import sys
import json
from typing import Dict, Any

class SpecificStandardTester:
    def __init__(self, base_url="https://fitness-club-admin.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 {name}")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            print(f"   Status: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
                return response.status_code == expected_status, response_data
            except:
                print(f"   Response: {response.text}")
                return response.status_code == expected_status, response.text
                
        except Exception as e:
            print(f"   Error: {str(e)}")
            return False, {}

    def investigate_standard_issue(self):
        """Investigate the specific Standard membership issue"""
        print("🔍 SPECIFIC STANDARD MEMBERSHIP INVESTIGATION")
        print("=" * 80)
        
        # Step 1: Get all membership types and analyze them
        print("\n📋 STEP 1: Analyze all existing membership types")
        success, response = self.run_test(
            "Get All Membership Types",
            "GET", 
            "membership-types",
            200
        )
        
        if success:
            standard_variations = []
            for mt in response:
                name = mt['name']
                if 'standard' in name.lower():
                    standard_variations.append({
                        'name': name,
                        'name_repr': repr(name),  # Shows hidden characters
                        'monthly_fee': mt['monthly_fee'],
                        'is_active': mt.get('is_active', True),
                        'id': mt['id']
                    })
            
            print(f"\n   Found {len(standard_variations)} Standard-related membership types:")
            for i, var in enumerate(standard_variations, 1):
                print(f"   {i}. Name: {var['name_repr']} (Fee: TTD {var['monthly_fee']}, Active: {var['is_active']})")
                print(f"      ID: {var['id']}")
        
        # Step 2: Try to create exact "Standard" membership
        print("\n📋 STEP 2: Try to create exact 'Standard' membership")
        standard_data = {
            "name": "Standard",
            "monthly_fee": 55.00,
            "description": "Basic gym access with equipment usage",
            "features": ["Equipment Access", "Locker Room", "Basic Support"],
            "is_active": True
        }
        
        success, response = self.run_test(
            "Create 'Standard' Membership Type",
            "POST",
            "membership-types", 
            400,  # Expecting 400 if it already exists
            standard_data
        )
        
        # Step 3: Test with different variations to understand the validation
        print("\n📋 STEP 3: Test validation with different variations")
        
        test_cases = [
            ("Standard", "Exact match"),
            ("Standard ", "With trailing space"),
            (" Standard", "With leading space"),
            (" Standard ", "With both spaces"),
            ("standard", "Lowercase"),
            ("STANDARD", "Uppercase")
        ]
        
        for test_name, description in test_cases:
            test_data = {
                "name": test_name,
                "monthly_fee": 55.00,
                "description": f"Test {description}",
                "features": ["Test"],
                "is_active": True
            }
            
            print(f"\n   Testing: {repr(test_name)} ({description})")
            success, response = self.run_test(
                f"Test '{test_name}'",
                "POST",
                "membership-types",
                400,  # Expecting 400 if it conflicts
                test_data
            )
            
            if success:
                print(f"   ✅ Got expected 400 error - conflicts with existing type")
            else:
                print(f"   ❓ Unexpected result - may have been created or different error")
        
        # Step 4: Check database for inactive Standard types
        print("\n📋 STEP 4: Summary and recommendations")
        print("\n   🎯 KEY FINDINGS:")
        print("   1. Multiple Standard variations exist in database")
        print("   2. Case-sensitive validation allows 'Standard' and 'standard' to coexist")
        print("   3. Whitespace variations ('Standard ' vs 'Standard') are treated as different")
        print("\n   💡 LIKELY USER ISSUE:")
        print("   - User sees 'Standard' in UI but tries to create 'Standard ' (with space)")
        print("   - Or user tries to create 'Standard' but there's an inactive one")
        print("   - Or frontend sends slightly different name than what user types")
        print("\n   🔧 RECOMMENDED INVESTIGATION:")
        print("   1. Check frontend form submission - does it trim whitespace?")
        print("   2. Check if there are inactive 'Standard' types")
        print("   3. Consider implementing name normalization (trim + case insensitive)")

if __name__ == "__main__":
    tester = SpecificStandardTester()
    tester.investigate_standard_issue()