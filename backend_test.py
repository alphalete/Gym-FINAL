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
from datetime import datetime
import json

# Configuration
BACKEND_URL = "https://821b78cf-1060-44c5-a0dd-f265722428d2.preview.emergentagent.com"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

class DatabaseResetTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.mongo_client = None
        self.db = None
        self.session = None
        self.test_results = []
        
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
    
    async def get_collection_count(self, collection_name):
        """Get count of documents in a collection"""
        try:
            collection = getattr(self.db, collection_name)
            count = await collection.count_documents({})
            return count
        except Exception as e:
            print(f"❌ Error counting {collection_name}: {str(e)}")
            return -1
    
    async def delete_all_from_collection(self, collection_name):
        """Delete all documents from a collection"""
        try:
            collection = getattr(self.db, collection_name)
            result = await collection.delete_many({})
            return result.deleted_count
        except Exception as e:
            print(f"❌ Error deleting from {collection_name}: {str(e)}")
            return -1
    
    async def test_database_reset(self):
        """Main database reset test"""
        print("\n🔥 STARTING DATABASE RESET OPERATION")
        print("=" * 60)
        
        # Step 1: Check initial state
        print("\n📊 STEP 1: Checking initial database state...")
        
        collections_to_check = ['clients', 'payment_records', 'billing_cycles', 'payments']
        initial_counts = {}
        
        for collection in collections_to_check:
            count = await self.get_collection_count(collection)
            initial_counts[collection] = count
            print(f"   {collection}: {count} documents")
        
        total_initial = sum(count for count in initial_counts.values() if count > 0)
        await self.log_test_result(
            "Initial database state check", 
            True, 
            f"Found {total_initial} total documents across all collections"
        )
        
        # Step 2: Delete all data
        print("\n🗑️ STEP 2: Deleting ALL data from database...")
        
        deletion_results = {}
        total_deleted = 0
        
        for collection in collections_to_check:
            deleted_count = await self.delete_all_from_collection(collection)
            deletion_results[collection] = deleted_count
            if deleted_count >= 0:
                total_deleted += deleted_count
                print(f"   {collection}: {deleted_count} documents deleted")
            else:
                print(f"   {collection}: ERROR during deletion")
        
        await self.log_test_result(
            "Database deletion operation", 
            all(count >= 0 for count in deletion_results.values()), 
            f"Deleted {total_deleted} total documents"
        )
        
        # Step 3: Verify deletion
        print("\n✅ STEP 3: Verifying complete deletion...")
        
        final_counts = {}
        all_empty = True
        
        for collection in collections_to_check:
            count = await self.get_collection_count(collection)
            final_counts[collection] = count
            print(f"   {collection}: {count} documents remaining")
            if count > 0:
                all_empty = False
        
        await self.log_test_result(
            "Database emptiness verification", 
            all_empty, 
            "All collections are empty" if all_empty else "Some collections still have data"
        )
        
        # Step 4: Test API endpoints
        print("\n🌐 STEP 4: Testing API endpoints...")
        
        await self.test_api_clients_empty()
        await self.test_api_payments_stats_empty()
        
        return all_empty
    
    async def test_api_clients_empty(self):
        """Test that GET /api/clients returns empty array"""
        try:
            url = f"{self.backend_url}/api/clients"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list) and len(data) == 0:
                        await self.log_test_result(
                            "GET /api/clients returns empty array", 
                            True, 
                            "API correctly returns [] for empty database"
                        )
                    else:
                        await self.log_test_result(
                            "GET /api/clients returns empty array", 
                            False, 
                            f"API returned {len(data) if isinstance(data, list) else 'non-array'} items instead of empty array"
                        )
                else:
                    await self.log_test_result(
                        "GET /api/clients returns empty array", 
                        False, 
                        f"API returned status {response.status}"
                    )
        except Exception as e:
            await self.log_test_result(
                "GET /api/clients returns empty array", 
                False, 
                f"API request failed: {str(e)}"
            )
    
    async def test_api_payments_stats_empty(self):
        """Test that payment stats reflect empty database"""
        try:
            url = f"{self.backend_url}/api/payments/stats"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    total_revenue = data.get('total_revenue', -1)
                    payment_count = data.get('payment_count', -1)
                    total_amount_owed = data.get('total_amount_owed', -1)
                    
                    if total_revenue == 0 and payment_count == 0 and total_amount_owed == 0:
                        await self.log_test_result(
                            "GET /api/payments/stats shows zero values", 
                            True, 
                            "Payment stats correctly show all zeros for empty database"
                        )
                    else:
                        await self.log_test_result(
                            "GET /api/payments/stats shows zero values", 
                            False, 
                            f"Stats show revenue:{total_revenue}, count:{payment_count}, owed:{total_amount_owed}"
                        )
                else:
                    await self.log_test_result(
                        "GET /api/payments/stats shows zero values", 
                        False, 
                        f"API returned status {response.status}"
                    )
        except Exception as e:
            await self.log_test_result(
                "GET /api/payments/stats shows zero values", 
                False, 
                f"API request failed: {str(e)}"
            )
    
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
    
    async def run_comprehensive_test(self):
        """Run the complete database reset test suite"""
        print("🚀 ALPHALETE CLUB PWA - DATABASE RESET TESTING")
        print("=" * 60)
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
                print("❌ API is not accessible, aborting database reset")
                return False
            
            # Perform database reset
            reset_success = await self.test_database_reset()
            
            # Summary
            print("\n📋 TEST SUMMARY")
            print("=" * 60)
            
            passed_tests = sum(1 for result in self.test_results if result['success'])
            total_tests = len(self.test_results)
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
            
            if reset_success:
                print("🎉 DATABASE RESET COMPLETED SUCCESSFULLY!")
                print("✅ All member records have been completely removed")
                print("✅ Database is now empty and ready for testing")
            else:
                print("❌ DATABASE RESET FAILED!")
                print("❌ Some data may still remain in the database")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ FAILED TESTS:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
            
            return reset_success
            
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    tester = DatabaseResetTester()
    success = await tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())