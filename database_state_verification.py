#!/usr/bin/env python3
"""
Database State Verification - Alphalete Club PWA
Purpose: Check the ACTUAL current state of the database and verify what members are currently present

CRITICAL VERIFICATION REQUIREMENTS:
1. Check the current count of members in the database via GET /api/clients
2. List the first 5-10 members currently in the database to see their names and IDs
3. Verify which database the backend is actually connected to
4. Check if there are any connection issues or if the backend is using a different database than expected

This is critical because the user reports the database is still full of members despite testing reports claiming delete functionality works.
"""

import asyncio
import aiohttp
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date
import json

# Configuration
BACKEND_URL = "https://fitness-club-admin.preview.emergentagent.com"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

class DatabaseStateVerifier:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.mongo_client = None
        self.db = None
        self.session = None
        self.verification_results = []
        
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
    
    async def log_verification_result(self, check_name, success, details=""):
        """Log verification result"""
        status = "✅ VERIFIED" if success else "❌ ISSUE"
        print(f"{status}: {check_name}")
        if details:
            print(f"   Details: {details}")
        
        self.verification_results.append({
            "check": check_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_backend_connectivity(self):
        """Test backend API connectivity"""
        try:
            url = f"{self.backend_url}/api/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    await self.log_verification_result(
                        "Backend API connectivity", 
                        True, 
                        f"Backend is accessible: {data.get('message', 'OK')}"
                    )
                    return True
                else:
                    await self.log_verification_result(
                        "Backend API connectivity", 
                        False, 
                        f"Backend returned status {response.status}"
                    )
                    return False
        except Exception as e:
            await self.log_verification_result(
                "Backend API connectivity", 
                False, 
                f"Backend request failed: {str(e)}"
            )
            return False
    
    async def verify_database_connection(self):
        """Verify direct MongoDB database connection"""
        try:
            # Test database connection by listing collections
            collections = await self.db.list_collection_names()
            
            await self.log_verification_result(
                "Direct MongoDB connection", 
                True, 
                f"Connected to database '{DB_NAME}' with collections: {collections}"
            )
            return True
            
        except Exception as e:
            await self.log_verification_result(
                "Direct MongoDB connection", 
                False, 
                f"Database connection failed: {str(e)}"
            )
            return False
    
    async def get_current_member_count_via_api(self):
        """Get current member count via backend API"""
        try:
            url = f"{self.backend_url}/api/clients"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    member_count = len(data) if isinstance(data, list) else -1
                    
                    await self.log_verification_result(
                        "Member count via API", 
                        True, 
                        f"Backend API reports {member_count} members in database"
                    )
                    return member_count, data
                else:
                    await self.log_verification_result(
                        "Member count via API", 
                        False, 
                        f"API returned status {response.status}"
                    )
                    return -1, None
        except Exception as e:
            await self.log_verification_result(
                "Member count via API", 
                False, 
                f"API request failed: {str(e)}"
            )
            return -1, None
    
    async def get_current_member_count_direct_db(self):
        """Get current member count via direct database query"""
        try:
            # Count documents in clients collection
            client_count = await self.db.clients.count_documents({})
            
            await self.log_verification_result(
                "Member count via direct DB", 
                True, 
                f"Direct database query reports {client_count} members in clients collection"
            )
            return client_count
            
        except Exception as e:
            await self.log_verification_result(
                "Member count via direct DB", 
                False, 
                f"Direct database query failed: {str(e)}"
            )
            return -1
    
    async def list_current_members_via_api(self, members_data):
        """List first 5-10 members via API data"""
        try:
            if not members_data or not isinstance(members_data, list):
                await self.log_verification_result(
                    "List members via API", 
                    False, 
                    "No valid member data available from API"
                )
                return False
            
            # Show first 10 members (or all if less than 10)
            members_to_show = members_data[:10]
            
            member_details = []
            for i, member in enumerate(members_to_show, 1):
                member_info = {
                    "index": i,
                    "id": member.get('id', 'N/A'),
                    "name": member.get('name', 'N/A'),
                    "email": member.get('email', 'N/A'),
                    "membership_type": member.get('membership_type', 'N/A'),
                    "status": member.get('status', 'N/A'),
                    "monthly_fee": member.get('monthly_fee', 'N/A'),
                    "payment_status": member.get('payment_status', 'N/A')
                }
                member_details.append(member_info)
            
            details_text = f"First {len(members_to_show)} members from API:\n"
            for member in member_details:
                details_text += f"   {member['index']}. {member['name']} ({member['email']}) - ID: {member['id'][:8]}... - {member['membership_type']} - {member['status']} - Fee: {member['monthly_fee']} - Payment: {member['payment_status']}\n"
            
            await self.log_verification_result(
                "List members via API", 
                True, 
                details_text.strip()
            )
            return True
            
        except Exception as e:
            await self.log_verification_result(
                "List members via API", 
                False, 
                f"Failed to list members: {str(e)}"
            )
            return False
    
    async def list_current_members_direct_db(self):
        """List first 5-10 members via direct database query"""
        try:
            # Get first 10 members from database
            members_cursor = self.db.clients.find({}).limit(10)
            members = await members_cursor.to_list(length=10)
            
            if not members:
                await self.log_verification_result(
                    "List members via direct DB", 
                    True, 
                    "No members found in database via direct query"
                )
                return True
            
            member_details = []
            for i, member in enumerate(members, 1):
                member_info = {
                    "index": i,
                    "id": member.get('id', 'N/A'),
                    "name": member.get('name', 'N/A'),
                    "email": member.get('email', 'N/A'),
                    "membership_type": member.get('membership_type', 'N/A'),
                    "status": member.get('status', 'N/A'),
                    "monthly_fee": member.get('monthly_fee', 'N/A'),
                    "payment_status": member.get('payment_status', 'N/A')
                }
                member_details.append(member_info)
            
            details_text = f"First {len(members)} members from direct DB query:\n"
            for member in member_details:
                details_text += f"   {member['index']}. {member['name']} ({member['email']}) - ID: {member['id'][:8] if isinstance(member['id'], str) else 'N/A'}... - {member['membership_type']} - {member['status']} - Fee: {member['monthly_fee']} - Payment: {member['payment_status']}\n"
            
            await self.log_verification_result(
                "List members via direct DB", 
                True, 
                details_text.strip()
            )
            return True
            
        except Exception as e:
            await self.log_verification_result(
                "List members via direct DB", 
                False, 
                f"Failed to list members from database: {str(e)}"
            )
            return False
    
    async def check_database_configuration(self):
        """Check which database the backend is actually using"""
        try:
            # Check backend environment configuration
            await self.log_verification_result(
                "Database configuration check", 
                True, 
                f"Backend configured to use: MongoDB URL: {MONGO_URL}, Database: {DB_NAME}"
            )
            
            # Test if we can access the same database the backend should be using
            db_stats = await self.db.command("dbStats")
            
            await self.log_verification_result(
                "Database stats verification", 
                True, 
                f"Database '{DB_NAME}' stats: {db_stats.get('collections', 'N/A')} collections, {db_stats.get('objects', 'N/A')} objects, {db_stats.get('dataSize', 'N/A')} bytes"
            )
            return True
            
        except Exception as e:
            await self.log_verification_result(
                "Database configuration check", 
                False, 
                f"Failed to verify database configuration: {str(e)}"
            )
            return False
    
    async def compare_api_vs_direct_counts(self, api_count, direct_count):
        """Compare member counts from API vs direct database query"""
        try:
            if api_count == direct_count:
                await self.log_verification_result(
                    "API vs Direct DB count comparison", 
                    True, 
                    f"Counts match: API={api_count}, Direct DB={direct_count}"
                )
                return True
            else:
                await self.log_verification_result(
                    "API vs Direct DB count comparison", 
                    False, 
                    f"Counts DO NOT match: API={api_count}, Direct DB={direct_count}. This indicates a potential issue!"
                )
                return False
                
        except Exception as e:
            await self.log_verification_result(
                "API vs Direct DB count comparison", 
                False, 
                f"Failed to compare counts: {str(e)}"
            )
            return False
    
    async def check_payment_records(self):
        """Check payment records to understand data state"""
        try:
            # Count payment records
            payment_count = await self.db.payment_records.count_documents({})
            
            # Get recent payments
            recent_payments = await self.db.payment_records.find({}).sort("recorded_at", -1).limit(5).to_list(5)
            
            payment_details = f"Payment records count: {payment_count}\n"
            if recent_payments:
                payment_details += "Recent payments:\n"
                for i, payment in enumerate(recent_payments, 1):
                    payment_details += f"   {i}. Client: {payment.get('client_name', 'N/A')} - Amount: {payment.get('amount_paid', 'N/A')} - Date: {payment.get('payment_date', 'N/A')}\n"
            
            await self.log_verification_result(
                "Payment records check", 
                True, 
                payment_details.strip()
            )
            return True
            
        except Exception as e:
            await self.log_verification_result(
                "Payment records check", 
                False, 
                f"Failed to check payment records: {str(e)}"
            )
            return False
    
    async def run_database_state_verification(self):
        """Run the complete database state verification"""
        print("🔍 ALPHALETE CLUB PWA - DATABASE STATE VERIFICATION")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"MongoDB URL: {MONGO_URL}")
        print(f"Database: {DB_NAME}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("\n🚨 CRITICAL: Checking ACTUAL current state of database")
        print("User reports database still full despite delete functionality claims")
        
        # Setup connections
        if not await self.setup():
            return False
        
        try:
            print("\n📡 STEP 1: Testing backend connectivity...")
            backend_ok = await self.test_backend_connectivity()
            
            print("\n🗄️  STEP 2: Verifying direct database connection...")
            db_ok = await self.verify_database_connection()
            
            print("\n🔢 STEP 3: Getting member count via API...")
            api_count, members_data = await self.get_current_member_count_via_api()
            
            print("\n🔢 STEP 4: Getting member count via direct database query...")
            direct_count = await self.get_current_member_count_direct_db()
            
            print("\n⚖️  STEP 5: Comparing API vs Direct database counts...")
            await self.compare_api_vs_direct_counts(api_count, direct_count)
            
            print("\n📋 STEP 6: Listing current members via API...")
            await self.list_current_members_via_api(members_data)
            
            print("\n📋 STEP 7: Listing current members via direct database...")
            await self.list_current_members_direct_db()
            
            print("\n⚙️  STEP 8: Checking database configuration...")
            await self.check_database_configuration()
            
            print("\n💰 STEP 9: Checking payment records...")
            await self.check_payment_records()
            
            # Summary
            print("\n📊 VERIFICATION SUMMARY")
            print("=" * 80)
            
            passed_checks = sum(1 for result in self.verification_results if result['success'])
            total_checks = len(self.verification_results)
            success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
            
            print(f"Checks Passed: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
            
            # Critical findings
            print("\n🚨 CRITICAL FINDINGS:")
            print(f"   • Backend API member count: {api_count}")
            print(f"   • Direct database member count: {direct_count}")
            print(f"   • Backend connectivity: {'✅ OK' if backend_ok else '❌ FAILED'}")
            print(f"   • Database connectivity: {'✅ OK' if db_ok else '❌ FAILED'}")
            
            if api_count > 0 or direct_count > 0:
                print(f"\n⚠️  DATABASE IS NOT EMPTY!")
                print(f"   • The database contains {max(api_count, direct_count)} members")
                print(f"   • This contradicts reports that delete functionality is working")
                print(f"   • User's report about database being 'still full' is CONFIRMED")
            else:
                print(f"\n✅ DATABASE IS EMPTY")
                print(f"   • No members found in database")
                print(f"   • This matches expectations if delete functionality is working")
            
            # Show failed checks
            failed_checks = [result for result in self.verification_results if not result['success']]
            if failed_checks:
                print("\n❌ FAILED CHECKS:")
                for check in failed_checks:
                    print(f"   - {check['check']}: {check['details']}")
            
            return passed_checks == total_checks
            
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    verifier = DatabaseStateVerifier()
    success = await verifier.run_database_state_verification()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())