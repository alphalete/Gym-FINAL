#!/usr/bin/env python3
"""
Create Default Membership Plans and Test Members - Alphalete Club PWA
Purpose: Create default membership plans and test members for Edit Member functionality testing

CRITICAL REQUIREMENTS FROM REVIEW REQUEST:
1. Create 3-4 basic membership plans:
   - Basic Plan: name="Basic", price=55.0, cycleDays=30
   - Premium Plan: name="Premium", price=75.0, cycleDays=30  
   - Elite Plan: name="Elite", price=100.0, cycleDays=30

2. Create 1-2 test members:
   - Test Member 1: name="John Smith", email="john.smith@test.com", phone="+1234567890", 
     membership_type="Basic", monthly_fee=55.0, status="Active"

This will provide the necessary data to test the comprehensive Edit Member functionality.
"""

import asyncio
import aiohttp
import os
import sys
from datetime import datetime, date
import json

# Configuration
BACKEND_URL = "https://821b78cf-1060-44c5-a0dd-f265722428d2.preview.emergentagent.com"

class DefaultDataCreator:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        self.test_results = []
        self.created_plans = []
        self.created_members = []
        
    async def setup(self):
        """Initialize HTTP connections"""
        try:
            # Setup HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'Content-Type': 'application/json'}
            )
            
            print("✅ HTTP connection established")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {str(e)}")
            return False
    
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
    
    async def test_api_health(self):
        """Test basic API connectivity"""
        try:
            url = f"{self.backend_url}/api/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    await self.log_test_result(
                        "API health check", 
                        True, 
                        f"API is healthy: {data.get('message', 'OK')}"
                    )
                    return True
                else:
                    await self.log_test_result(
                        "API health check", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "API health check", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def create_membership_plan(self, plan_data):
        """Create a single membership plan"""
        try:
            url = f"{self.backend_url}/api/membership-types"
            async with self.session.post(url, json=plan_data) as response:
                if response.status == 200:
                    data = await response.json()
                    plan_id = data.get('id')
                    self.created_plans.append({
                        'id': plan_id,
                        'name': plan_data['name'],
                        'monthly_fee': plan_data['monthly_fee']
                    })
                    
                    await self.log_test_result(
                        f"Create {plan_data['name']} plan", 
                        True, 
                        f"Successfully created plan with ID: {plan_id}, Fee: TTD {plan_data['monthly_fee']}"
                    )
                    return True
                elif response.status == 400:
                    response_text = await response.text()
                    if "already exists" in response_text:
                        # Plan already exists, this is OK
                        await self.log_test_result(
                            f"Create {plan_data['name']} plan", 
                            True, 
                            f"Plan already exists (skipped): {plan_data['name']} - TTD {plan_data['monthly_fee']}"
                        )
                        return True
                    else:
                        await self.log_test_result(
                            f"Create {plan_data['name']} plan", 
                            False, 
                            f"API returned status {response.status}: {response_text}"
                        )
                        return False
                else:
                    response_text = await response.text()
                    await self.log_test_result(
                        f"Create {plan_data['name']} plan", 
                        False, 
                        f"API returned status {response.status}: {response_text}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                f"Create {plan_data['name']} plan", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def create_default_membership_plans(self):
        """Create the default membership plans as specified in review request"""
        plans = [
            {
                "name": "Basic",
                "monthly_fee": 55.0,
                "description": "Basic gym access with equipment usage",
                "features": ["Equipment Access", "Locker Room", "Basic Support"],
                "is_active": True
            },
            {
                "name": "Premium", 
                "monthly_fee": 75.0,
                "description": "Gym access plus group fitness classes",
                "features": ["All Basic Features", "Group Classes", "Extended Hours", "Guest Passes"],
                "is_active": True
            },
            {
                "name": "Elite",
                "monthly_fee": 100.0,
                "description": "Premium features plus personal training sessions",
                "features": ["All Premium Features", "Personal Training Sessions", "Nutrition Consultation", "Priority Booking"],
                "is_active": True
            }
        ]
        
        success_count = 0
        for plan in plans:
            if await self.create_membership_plan(plan):
                success_count += 1
        
        return success_count == len(plans)
    
    async def verify_membership_plans(self):
        """Verify that membership plans were created successfully"""
        try:
            url = f"{self.backend_url}/api/membership-types"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list):
                        plan_names = [plan.get('name') for plan in data]
                        expected_plans = ['Basic', 'Premium', 'Elite']
                        
                        plans_found = all(plan in plan_names for plan in expected_plans)
                        
                        await self.log_test_result(
                            "Verify membership plans", 
                            plans_found, 
                            f"Found {len(data)} plans: {plan_names}. Expected: {expected_plans}"
                        )
                        return plans_found
                    else:
                        await self.log_test_result(
                            "Verify membership plans", 
                            False, 
                            f"API returned non-array response: {data}"
                        )
                        return False
                else:
                    await self.log_test_result(
                        "Verify membership plans", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Verify membership plans", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def create_test_member(self, member_data):
        """Create a single test member"""
        try:
            url = f"{self.backend_url}/api/clients"
            async with self.session.post(url, json=member_data) as response:
                if response.status == 200:
                    data = await response.json()
                    member_id = data.get('id')
                    self.created_members.append({
                        'id': member_id,
                        'name': member_data['name'],
                        'email': member_data['email'],
                        'membership_type': member_data['membership_type']
                    })
                    
                    await self.log_test_result(
                        f"Create member {member_data['name']}", 
                        True, 
                        f"Successfully created member with ID: {member_id}"
                    )
                    return True
                else:
                    response_text = await response.text()
                    await self.log_test_result(
                        f"Create member {member_data['name']}", 
                        False, 
                        f"API returned status {response.status}: {response_text}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                f"Create member {member_data['name']}", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def create_test_members(self):
        """Create test members as specified in review request"""
        members = [
            {
                "name": "John Smith",
                "email": "john.smith@test.com",
                "phone": "+1234567890",
                "membership_type": "Basic",
                "monthly_fee": 55.0,
                "start_date": date.today().isoformat(),
                "status": "Active",
                "auto_reminders_enabled": True,
                "payment_status": "due",
                "billing_interval_days": 30
            }
        ]
        
        success_count = 0
        for member in members:
            if await self.create_test_member(member):
                success_count += 1
        
        return success_count == len(members)
    
    async def verify_test_members(self):
        """Verify that test members were created successfully"""
        try:
            url = f"{self.backend_url}/api/clients"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list):
                        member_names = [member.get('name') for member in data]
                        expected_members = ['John Smith']
                        
                        members_found = all(member in member_names for member in expected_members)
                        
                        await self.log_test_result(
                            "Verify test members", 
                            members_found, 
                            f"Found {len(data)} members: {member_names}. Expected: {expected_members}"
                        )
                        return members_found
                    else:
                        await self.log_test_result(
                            "Verify test members", 
                            False, 
                            f"API returned non-array response: {data}"
                        )
                        return False
                else:
                    await self.log_test_result(
                        "Verify test members", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Verify test members", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def run_default_data_creation(self):
        """Run the complete default data creation process"""
        print("🚀 ALPHALETE CLUB PWA - CREATE DEFAULT MEMBERSHIP PLANS AND TEST MEMBERS")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("\nCREATING DATA AS SPECIFIED IN REVIEW REQUEST:")
        print("📋 Membership Plans: Basic (TTD 55), Premium (TTD 75), Elite (TTD 100)")
        print("👤 Test Members: John Smith (Basic membership)")
        
        # Setup connections
        if not await self.setup():
            return False
        
        try:
            # Test API connectivity first
            if not await self.test_api_health():
                print("❌ API is not accessible, aborting data creation")
                return False
            
            print("\n📊 STEP 1: Creating membership plans...")
            # Create membership plans
            if not await self.create_default_membership_plans():
                print("❌ Failed to create all membership plans")
                return False
            
            print("\n✅ STEP 2: Verifying membership plans...")
            # Verify plans were created
            if not await self.verify_membership_plans():
                print("❌ Failed to verify membership plans")
                return False
            
            print("\n👤 STEP 3: Creating test members...")
            # Create test members
            if not await self.create_test_members():
                print("❌ Failed to create test members")
                return False
            
            print("\n✅ STEP 4: Verifying test members...")
            # Verify members were created
            if not await self.verify_test_members():
                print("❌ Failed to verify test members")
                return False
            
            # Summary
            print("\n📋 CREATION SUMMARY")
            print("=" * 80)
            
            passed_tests = sum(1 for result in self.test_results if result['success'])
            total_tests = len(self.test_results)
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
            
            if passed_tests == total_tests:
                print("🎉 DEFAULT DATA CREATION COMPLETED SUCCESSFULLY!")
                print("✅ All membership plans created successfully")
                print("✅ All test members created successfully")
                print("✅ Edit Member functionality can now be tested")
            else:
                print("❌ DEFAULT DATA CREATION FAILED!")
                print("❌ Some operations failed during the process")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ FAILED OPERATIONS:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
            
            # Show created data for reference
            if self.created_plans:
                print(f"\n📋 CREATED MEMBERSHIP PLANS:")
                for plan in self.created_plans:
                    print(f"   - {plan['name']}: TTD {plan['monthly_fee']} (ID: {plan['id']})")
            
            if self.created_members:
                print(f"\n👤 CREATED TEST MEMBERS:")
                for member in self.created_members:
                    print(f"   - {member['name']} ({member['email']}) - {member['membership_type']} (ID: {member['id']})")
            
            return passed_tests == total_tests
            
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    creator = DefaultDataCreator()
    success = await creator.run_default_data_creation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())