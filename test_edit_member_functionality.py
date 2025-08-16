#!/usr/bin/env python3
"""
Test Edit Member Functionality - Alphalete Club PWA
Purpose: Test the Edit Member functionality now that membership plans and test members exist
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date

# Configuration
BACKEND_URL = "https://gym-billing-system.preview.emergentagent.com"

class EditMemberTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        self.test_results = []
        self.john_smith_id = None
        
    async def setup(self):
        """Initialize HTTP connections"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return True
    
    async def cleanup(self):
        """Clean up connections"""
        if self.session:
            await self.session.close()
    
    async def log_test_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def find_john_smith(self):
        """Find John Smith member for testing"""
        try:
            url = f"{self.backend_url}/api/clients"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for member in data:
                        if member.get('name') == 'John Smith' and member.get('email') == 'john.smith@test.com':
                            self.john_smith_id = member.get('id')
                            await self.log_test_result(
                                "Find John Smith member", 
                                True, 
                                f"Found John Smith with ID: {self.john_smith_id}"
                            )
                            return True
                    
                    await self.log_test_result(
                        "Find John Smith member", 
                        False, 
                        "John Smith not found in member list"
                    )
                    return False
                else:
                    await self.log_test_result(
                        "Find John Smith member", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Find John Smith member", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def test_get_member_by_id(self):
        """Test retrieving member by ID (required for Edit Member pre-population)"""
        if not self.john_smith_id:
            await self.log_test_result(
                "Get member by ID", 
                False, 
                "No member ID available"
            )
            return False
        
        try:
            url = f"{self.backend_url}/api/clients/{self.john_smith_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify all required fields for Edit Member form
                    required_fields = ['id', 'name', 'email', 'phone', 'membership_type', 'monthly_fee', 'status']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        await self.log_test_result(
                            "Get member by ID", 
                            True, 
                            f"Successfully retrieved member with all required fields: {required_fields}"
                        )
                        return data
                    else:
                        await self.log_test_result(
                            "Get member by ID", 
                            False, 
                            f"Missing required fields: {missing_fields}"
                        )
                        return False
                else:
                    await self.log_test_result(
                        "Get member by ID", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Get member by ID", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def test_update_member(self, original_data):
        """Test updating member information (core Edit Member functionality)"""
        if not self.john_smith_id or not original_data:
            await self.log_test_result(
                "Update member information", 
                False, 
                "No member ID or original data available"
            )
            return False
        
        # Test updating to Premium membership
        update_data = {
            "name": "John Smith Updated",
            "phone": "+1234567891",  # Changed phone
            "membership_type": "Premium",  # Changed from Basic to Premium
            "monthly_fee": 75.0  # Updated fee to match Premium
        }
        
        try:
            url = f"{self.backend_url}/api/clients/{self.john_smith_id}"
            async with self.session.put(url, json=update_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify updates were applied
                    updates_applied = all(
                        data.get(key) == value 
                        for key, value in update_data.items()
                    )
                    
                    if updates_applied:
                        await self.log_test_result(
                            "Update member information", 
                            True, 
                            f"Successfully updated member: {update_data}"
                        )
                        return data
                    else:
                        await self.log_test_result(
                            "Update member information", 
                            False, 
                            f"Updates not applied correctly. Expected: {update_data}, Got: {data}"
                        )
                        return False
                else:
                    response_text = await response.text()
                    await self.log_test_result(
                        "Update member information", 
                        False, 
                        f"API returned status {response.status}: {response_text}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Update member information", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def test_membership_plan_integration(self):
        """Test that membership plans are available for Edit Member dropdown"""
        try:
            url = f"{self.backend_url}/api/membership-types"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for required plans
                    required_plans = ['Basic', 'Premium', 'Elite']
                    available_plans = [plan.get('name') for plan in data]
                    
                    plans_available = all(plan in available_plans for plan in required_plans)
                    
                    if plans_available:
                        await self.log_test_result(
                            "Membership plan integration", 
                            True, 
                            f"All required plans available for dropdown: {required_plans}"
                        )
                        return True
                    else:
                        missing_plans = [plan for plan in required_plans if plan not in available_plans]
                        await self.log_test_result(
                            "Membership plan integration", 
                            False, 
                            f"Missing required plans: {missing_plans}"
                        )
                        return False
                else:
                    await self.log_test_result(
                        "Membership plan integration", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Membership plan integration", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def test_restore_original_data(self, original_data):
        """Restore John Smith to original state for future testing"""
        if not self.john_smith_id or not original_data:
            await self.log_test_result(
                "Restore original member data", 
                False, 
                "No member ID or original data available"
            )
            return False
        
        # Restore original data
        restore_data = {
            "name": original_data.get('name'),
            "phone": original_data.get('phone'),
            "membership_type": original_data.get('membership_type'),
            "monthly_fee": original_data.get('monthly_fee')
        }
        
        try:
            url = f"{self.backend_url}/api/clients/{self.john_smith_id}"
            async with self.session.put(url, json=restore_data) as response:
                if response.status == 200:
                    await self.log_test_result(
                        "Restore original member data", 
                        True, 
                        f"Successfully restored John Smith to original state"
                    )
                    return True
                else:
                    await self.log_test_result(
                        "Restore original member data", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Restore original member data", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def run_edit_member_tests(self):
        """Run the complete Edit Member functionality tests"""
        print("🔧 ALPHALETE CLUB PWA - EDIT MEMBER FUNCTIONALITY TESTING")
        print("=" * 70)
        print(f"Backend URL: {self.backend_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("\nTesting Edit Member functionality with created membership plans and test member")
        
        await self.setup()
        
        try:
            # Step 1: Find John Smith member
            if not await self.find_john_smith():
                print("❌ Cannot proceed without test member")
                return False
            
            # Step 2: Test membership plan integration
            if not await self.test_membership_plan_integration():
                print("❌ Membership plans not available for Edit Member")
                return False
            
            # Step 3: Test getting member by ID (for form pre-population)
            original_data = await self.test_get_member_by_id()
            if not original_data:
                print("❌ Cannot retrieve member data for editing")
                return False
            
            # Step 4: Test updating member information
            updated_data = await self.test_update_member(original_data)
            if not updated_data:
                print("❌ Member update functionality failed")
                return False
            
            # Step 5: Restore original data for future testing
            await self.test_restore_original_data(original_data)
            
            # Summary
            print("\n📋 EDIT MEMBER TESTING SUMMARY")
            print("=" * 70)
            
            passed_tests = sum(1 for result in self.test_results if result['success'])
            total_tests = len(self.test_results)
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
            
            if passed_tests == total_tests:
                print("🎉 EDIT MEMBER FUNCTIONALITY TESTING COMPLETED SUCCESSFULLY!")
                print("✅ Member retrieval by ID working (form pre-population)")
                print("✅ Membership plans available for dropdown selection")
                print("✅ Member update functionality working")
                print("✅ All backend APIs support Edit Member functionality")
                print("✅ Edit Member functionality is ready for frontend testing")
            else:
                print("❌ EDIT MEMBER FUNCTIONALITY TESTING FAILED!")
                print("❌ Some backend APIs are not working correctly")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ FAILED TESTS:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
            
            return passed_tests == total_tests
            
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    tester = EditMemberTester()
    success = await tester.run_edit_member_tests()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nEdit Member Testing {'PASSED' if result else 'FAILED'}")