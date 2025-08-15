#!/usr/bin/env python3
"""
Add Test Member for Delete Functionality Testing - Alphalete Club PWA
Purpose: Add ONE test member to empty database for testing delete functionality

CRITICAL TESTING REQUIREMENTS:
- Add ONE test member with specific details:
  * name: "Test Delete Member"
  * email: "delete.test@example.com"
  * phone: "+1234567890"
  * membership_type: "Basic"
  * monthly_fee: 55.0
  * status: "Active"
- Verify the member was created successfully
- Confirm GET /api/clients returns exactly 1 member
- Get the member ID for testing
- This single member will be used to test delete functionality from frontend

This test member addition is essential for proper testing of the delete member functionality.
"""

import asyncio
import aiohttp
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date
import json

# Configuration
BACKEND_URL = "https://fitness-tracker-app.preview.emergentagent.com"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

class TestMemberAdder:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.mongo_client = None
        self.db = None
        self.session = None
        self.test_results = []
        self.test_member_id = None
        
    async def setup(self):
        """Initialize database and HTTP connections"""
        try:
            # Setup MongoDB connection
            self.mongo_client = AsyncIOMotorClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            
            # Setup HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'Content-Type': 'application/json'}
            )
            
            print("✅ Database and HTTP connections established")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up connections"""
        if self.session:
            await self.session.close()
        if self.mongo_client:
            self.mongo_client.close()
    
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
    
    async def check_database_empty(self):
        """Check if database is empty before adding test member"""
        try:
            url = f"{self.backend_url}/api/clients"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    member_count = len(data) if isinstance(data, list) else -1
                    
                    await self.log_test_result(
                        "Database empty check", 
                        member_count == 0, 
                        f"Found {member_count} existing members in database"
                    )
                    return member_count == 0
                else:
                    await self.log_test_result(
                        "Database empty check", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Database empty check", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def add_test_member(self):
        """Add the specific test member for delete functionality testing"""
        test_member_data = {
            "name": "Test Delete Member",
            "email": "delete.test@example.com",
            "phone": "+1234567890",
            "membership_type": "Basic",
            "monthly_fee": 55.0,
            "start_date": date.today().isoformat(),
            "status": "Active",
            "auto_reminders_enabled": True,
            "payment_status": "due",
            "billing_interval_days": 30
        }
        
        try:
            url = f"{self.backend_url}/api/clients"
            async with self.session.post(url, json=test_member_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_member_id = data.get('id')
                    
                    await self.log_test_result(
                        "Add test member", 
                        True, 
                        f"Successfully created test member with ID: {self.test_member_id}"
                    )
                    return True
                else:
                    response_text = await response.text()
                    await self.log_test_result(
                        "Add test member", 
                        False, 
                        f"API returned status {response.status}: {response_text}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Add test member", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def verify_member_created(self):
        """Verify the test member was created successfully"""
        try:
            url = f"{self.backend_url}/api/clients"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list) and len(data) == 1:
                        member = data[0]
                        
                        # Verify member details
                        expected_details = {
                            "name": "Test Delete Member",
                            "email": "delete.test@example.com",
                            "phone": "+1234567890",
                            "membership_type": "Basic",
                            "monthly_fee": 55.0,
                            "status": "Active"
                        }
                        
                        details_match = all(
                            member.get(key) == value 
                            for key, value in expected_details.items()
                        )
                        
                        if details_match:
                            await self.log_test_result(
                                "Verify member details", 
                                True, 
                                f"All member details match expected values. Member ID: {member.get('id')}"
                            )
                            self.test_member_id = member.get('id')
                            return True
                        else:
                            await self.log_test_result(
                                "Verify member details", 
                                False, 
                                f"Member details don't match. Expected: {expected_details}, Got: {member}"
                            )
                            return False
                    else:
                        await self.log_test_result(
                            "Verify member count", 
                            False, 
                            f"Expected exactly 1 member, found {len(data) if isinstance(data, list) else 'non-array'}"
                        )
                        return False
                else:
                    await self.log_test_result(
                        "Verify member created", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_test_result(
                "Verify member created", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def get_member_by_id(self):
        """Get the specific member by ID to confirm it exists"""
        if not self.test_member_id:
            await self.log_test_result(
                "Get member by ID", 
                False, 
                "No test member ID available"
            )
            return False
        
        try:
            url = f"{self.backend_url}/api/clients/{self.test_member_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    await self.log_test_result(
                        "Get member by ID", 
                        True, 
                        f"Successfully retrieved member: {data.get('name')} ({data.get('email')})"
                    )
                    return True
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
    
    async def run_test_member_addition(self):
        """Run the complete test member addition process"""
        print("🚀 ALPHALETE CLUB PWA - ADD TEST MEMBER FOR DELETE TESTING")
        print("=" * 70)
        print(f"Backend URL: {self.backend_url}")
        print(f"MongoDB URL: {MONGO_URL}")
        print(f"Database: {DB_NAME}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Setup connections
        if not await self.setup():
            return False
        
        try:
            # Test API connectivity first
            if not await self.test_api_health():
                print("❌ API is not accessible, aborting test member addition")
                return False
            
            print("\n📊 STEP 1: Checking database state...")
            # Check if database is empty
            if not await self.check_database_empty():
                print("⚠️  Database is not empty, but proceeding with test member addition")
            
            print("\n➕ STEP 2: Adding test member...")
            # Add the test member
            if not await self.add_test_member():
                print("❌ Failed to add test member")
                return False
            
            print("\n✅ STEP 3: Verifying member creation...")
            # Verify member was created correctly
            if not await self.verify_member_created():
                print("❌ Failed to verify member creation")
                return False
            
            print("\n🔍 STEP 4: Testing member retrieval by ID...")
            # Test getting member by ID
            if not await self.get_member_by_id():
                print("❌ Failed to retrieve member by ID")
                return False
            
            # Summary
            print("\n📋 TEST SUMMARY")
            print("=" * 70)
            
            passed_tests = sum(1 for result in self.test_results if result['success'])
            total_tests = len(self.test_results)
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
            
            if passed_tests == total_tests:
                print("🎉 TEST MEMBER ADDITION COMPLETED SUCCESSFULLY!")
                print("✅ Test member 'Test Delete Member' has been added to database")
                print(f"✅ Member ID: {self.test_member_id}")
                print("✅ Database now contains exactly 1 member for delete testing")
                print("✅ Ready for frontend delete functionality testing")
            else:
                print("❌ TEST MEMBER ADDITION FAILED!")
                print("❌ Some tests failed during the process")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ FAILED TESTS:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
            
            # Show member details for reference
            if self.test_member_id:
                print(f"\n📝 TEST MEMBER DETAILS:")
                print(f"   Name: Test Delete Member")
                print(f"   Email: delete.test@example.com")
                print(f"   Phone: +1234567890")
                print(f"   Membership: Basic")
                print(f"   Monthly Fee: TTD 55.0")
                print(f"   Status: Active")
                print(f"   Member ID: {self.test_member_id}")
            
            return passed_tests == total_tests
            
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    tester = TestMemberAdder()
    success = await tester.run_test_member_addition()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())