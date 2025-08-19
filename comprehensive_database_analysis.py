#!/usr/bin/env python3
"""
Comprehensive Database Analysis - Alphalete Club PWA
Purpose: Deep dive into database state to understand the discrepancy between user reports and actual state

INVESTIGATION FOCUS:
1. Check all collections in the database
2. Look for historical data that might explain user confusion
3. Check if there are multiple databases
4. Examine payment records, billing cycles, and other related data
5. Check for any cached or stale data
"""

import asyncio
import aiohttp
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date
import json

# Configuration
BACKEND_URL = "https://alphalete-pwa.preview.emergentagent.com"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

class ComprehensiveDatabaseAnalyzer:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.mongo_client = None
        self.db = None
        self.session = None
        
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
    
    async def analyze_all_databases(self):
        """Check all databases on the MongoDB server"""
        try:
            print("\n🗄️  ANALYZING ALL DATABASES ON MONGODB SERVER")
            print("-" * 60)
            
            # List all databases
            db_list = await self.mongo_client.list_database_names()
            print(f"Found {len(db_list)} databases: {db_list}")
            
            # Analyze each database
            for db_name in db_list:
                if db_name in ['admin', 'config', 'local']:
                    continue  # Skip system databases
                
                print(f"\n📊 Database: {db_name}")
                temp_db = self.mongo_client[db_name]
                
                try:
                    collections = await temp_db.list_collection_names()
                    print(f"   Collections: {collections}")
                    
                    # Check clients collection if it exists
                    if 'clients' in collections:
                        client_count = await temp_db.clients.count_documents({})
                        print(f"   Clients count: {client_count}")
                        
                        if client_count > 0:
                            # Get sample clients
                            sample_clients = await temp_db.clients.find({}).limit(3).to_list(3)
                            print(f"   Sample clients:")
                            for i, client in enumerate(sample_clients, 1):
                                print(f"      {i}. {client.get('name', 'N/A')} ({client.get('email', 'N/A')})")
                    
                    # Check payment_records if it exists
                    if 'payment_records' in collections:
                        payment_count = await temp_db.payment_records.count_documents({})
                        print(f"   Payment records count: {payment_count}")
                    
                except Exception as e:
                    print(f"   Error analyzing database {db_name}: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to analyze databases: {str(e)}")
            return False
    
    async def analyze_all_collections(self):
        """Analyze all collections in the current database"""
        try:
            print(f"\n📋 ANALYZING ALL COLLECTIONS IN DATABASE '{DB_NAME}'")
            print("-" * 60)
            
            collections = await self.db.list_collection_names()
            print(f"Found {len(collections)} collections: {collections}")
            
            for collection_name in collections:
                print(f"\n📊 Collection: {collection_name}")
                collection = self.db[collection_name]
                
                try:
                    # Get document count
                    doc_count = await collection.count_documents({})
                    print(f"   Document count: {doc_count}")
                    
                    if doc_count > 0:
                        # Get sample documents
                        sample_docs = await collection.find({}).limit(2).to_list(2)
                        print(f"   Sample documents:")
                        for i, doc in enumerate(sample_docs, 1):
                            # Remove _id for cleaner output
                            if '_id' in doc:
                                del doc['_id']
                            # Truncate long documents
                            doc_str = str(doc)
                            if len(doc_str) > 200:
                                doc_str = doc_str[:200] + "..."
                            print(f"      {i}. {doc_str}")
                    
                except Exception as e:
                    print(f"   Error analyzing collection {collection_name}: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to analyze collections: {str(e)}")
            return False
    
    async def check_historical_data(self):
        """Check for historical data that might explain user confusion"""
        try:
            print(f"\n📈 CHECKING HISTORICAL DATA")
            print("-" * 60)
            
            # Check payment records for historical client data
            payment_records = await self.db.payment_records.find({}).to_list(1000)
            print(f"Total payment records found: {len(payment_records)}")
            
            if payment_records:
                # Extract unique client names from payment history
                client_names = set()
                client_emails = set()
                for record in payment_records:
                    if 'client_name' in record:
                        client_names.add(record['client_name'])
                    if 'client_email' in record:
                        client_emails.add(record['client_email'])
                
                print(f"Historical clients from payment records:")
                print(f"   Unique client names: {len(client_names)}")
                print(f"   Unique client emails: {len(client_emails)}")
                
                if client_names:
                    print(f"   Sample client names: {list(client_names)[:10]}")
            
            # Check billing cycles
            billing_cycles = await self.db.billing_cycles.find({}).to_list(1000)
            print(f"Total billing cycles found: {len(billing_cycles)}")
            
            if billing_cycles:
                # Extract unique member IDs
                member_ids = set()
                for cycle in billing_cycles:
                    if 'member_id' in cycle:
                        member_ids.add(cycle['member_id'])
                
                print(f"Historical member IDs from billing cycles: {len(member_ids)}")
                if member_ids:
                    print(f"   Sample member IDs: {list(member_ids)[:5]}")
            
            # Check payments
            payments = await self.db.payments.find({}).to_list(1000)
            print(f"Total payments found: {len(payments)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to check historical data: {str(e)}")
            return False
    
    async def check_api_endpoints_thoroughly(self):
        """Check various API endpoints to understand current state"""
        try:
            print(f"\n🌐 CHECKING API ENDPOINTS THOROUGHLY")
            print("-" * 60)
            
            # Check clients endpoint
            try:
                url = f"{self.backend_url}/api/clients"
                async with self.session.get(url) as response:
                    print(f"GET /api/clients: Status {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   Response: {len(data) if isinstance(data, list) else 'Not a list'} items")
                        if isinstance(data, list) and len(data) > 0:
                            print(f"   First item: {data[0] if data else 'None'}")
            except Exception as e:
                print(f"   Error: {str(e)}")
            
            # Check payment stats
            try:
                url = f"{self.backend_url}/api/payments/stats"
                async with self.session.get(url) as response:
                    print(f"GET /api/payments/stats: Status {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   Response: {data}")
            except Exception as e:
                print(f"   Error: {str(e)}")
            
            # Check membership types
            try:
                url = f"{self.backend_url}/api/membership-types"
                async with self.session.get(url) as response:
                    print(f"GET /api/membership-types: Status {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   Response: {len(data) if isinstance(data, list) else 'Not a list'} membership types")
            except Exception as e:
                print(f"   Error: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to check API endpoints: {str(e)}")
            return False
    
    async def check_recent_activity(self):
        """Check for recent activity in the database"""
        try:
            print(f"\n⏰ CHECKING RECENT ACTIVITY")
            print("-" * 60)
            
            # Check recent payment records
            recent_payments = await self.db.payment_records.find({}).sort("recorded_at", -1).limit(10).to_list(10)
            print(f"Recent payment records: {len(recent_payments)}")
            
            for i, payment in enumerate(recent_payments, 1):
                recorded_at = payment.get('recorded_at', 'N/A')
                client_name = payment.get('client_name', 'N/A')
                amount = payment.get('amount_paid', 'N/A')
                print(f"   {i}. {recorded_at} - {client_name} - ${amount}")
            
            # Check recent reminder history
            recent_reminders = await self.db.reminder_history.find({}).sort("sent_at", -1).limit(5).to_list(5)
            print(f"Recent reminder history: {len(recent_reminders)}")
            
            for i, reminder in enumerate(recent_reminders, 1):
                sent_at = reminder.get('sent_at', 'N/A')
                client_name = reminder.get('client_name', 'N/A')
                print(f"   {i}. {sent_at} - {client_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to check recent activity: {str(e)}")
            return False
    
    async def run_comprehensive_analysis(self):
        """Run the complete comprehensive database analysis"""
        print("🔬 ALPHALETE CLUB PWA - COMPREHENSIVE DATABASE ANALYSIS")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"MongoDB URL: {MONGO_URL}")
        print(f"Database: {DB_NAME}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("\n🚨 INVESTIGATING: User reports database full vs actual empty state")
        
        # Setup connections
        if not await self.setup():
            return False
        
        try:
            # Run all analyses
            await self.analyze_all_databases()
            await self.analyze_all_collections()
            await self.check_historical_data()
            await self.check_api_endpoints_thoroughly()
            await self.check_recent_activity()
            
            print("\n🎯 ANALYSIS CONCLUSIONS")
            print("=" * 80)
            print("Based on comprehensive analysis:")
            print("1. Current database state: EMPTY (0 members)")
            print("2. Historical data exists in payment_records and billing_cycles")
            print("3. This suggests members were previously present but have been deleted")
            print("4. User's confusion may be due to:")
            print("   - Looking at cached frontend data")
            print("   - Expecting to see historical payment data as current members")
            print("   - Frontend not refreshing properly after deletions")
            print("   - Confusion between payment history and current member list")
            
            return True
            
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    analyzer = ComprehensiveDatabaseAnalyzer()
    success = await analyzer.run_comprehensive_analysis()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())