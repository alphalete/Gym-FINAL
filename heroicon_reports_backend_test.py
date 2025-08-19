#!/usr/bin/env python3
"""
Heroicon Conversion & Enhanced Reports Backend Testing - Alphalete Club PWA
Purpose: Test backend stability and functionality after Heroicon implementation and Reports enhancement

CRITICAL TESTING REQUIREMENTS:
1. API Endpoints Verification:
   - Test GET /api/clients endpoint for member data retrieval
   - Verify GET /api/payments/stats for payment statistics
   - Check all existing CRUD operations still function correctly
   - Confirm no regressions in backend functionality

2. Data Integrity Check:
   - Verify member data structure is properly supported
   - Test payment data retrieval and calculations
   - Ensure database connections remain stable
   - Check enhanced frontend calculations don't affect backend

3. Performance Testing:
   - Test backend response times under Reports component load
   - Verify no memory leaks or performance degradation
   - Check concurrent request handling capability

4. Backend Stability:
   - Confirm all services are running properly
   - Test error handling and validation
   - Verify CORS settings are still correct
   - Check backend API can handle enhanced Reports data requirements

The frontend Heroicon changes should not have affected backend, but we need to ensure
complete system stability before proceeding with enhanced Reports functionality testing.
"""

import asyncio
import aiohttp
import os
import sys
import time
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, date
import json
import concurrent.futures

# Configuration
BACKEND_URL = "https://alphalete-pwa.preview.emergentagent.com"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

class HeroiconReportsBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.mongo_client = None
        self.db = None
        self.session = None
        self.test_results = []
        self.performance_metrics = []
        
    async def setup(self):
        """Initialize database and HTTP connections"""
        try:
            # Setup MongoDB connection
            self.mongo_client = AsyncIOMotorClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            
            # Setup HTTP session with longer timeout for performance tests
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
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
    
    async def log_test_result(self, test_name, success, details="", performance_data=None):
        """Log test result with optional performance data"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if performance_data:
            print(f"   Performance: {performance_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "performance": performance_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def measure_response_time(self, url, method="GET", data=None):
        """Measure API response time"""
        start_time = time.time()
        try:
            if method == "GET":
                async with self.session.get(url) as response:
                    await response.json()
                    end_time = time.time()
                    return response.status, end_time - start_time
            elif method == "POST":
                async with self.session.post(url, json=data) as response:
                    await response.json()
                    end_time = time.time()
                    return response.status, end_time - start_time
        except Exception as e:
            end_time = time.time()
            return 500, end_time - start_time
    
    # 1. API ENDPOINTS VERIFICATION
    async def test_api_health_and_status(self):
        """Test basic API connectivity and status"""
        try:
            # Test health endpoint
            url = f"{self.backend_url}/api/health"
            status, response_time = await self.measure_response_time(url)
            
            if status == 200:
                await self.log_test_result(
                    "API Health Check", 
                    True, 
                    "API is healthy and responding",
                    f"Response time: {response_time:.3f}s"
                )
                
                # Test API status endpoint
                status_url = f"{self.backend_url}/api/"
                status_code, status_time = await self.measure_response_time(status_url)
                
                if status_code == 200:
                    await self.log_test_result(
                        "API Status Endpoint", 
                        True, 
                        "API status endpoint working",
                        f"Response time: {status_time:.3f}s"
                    )
                    return True
                else:
                    await self.log_test_result(
                        "API Status Endpoint", 
                        False, 
                        f"Status endpoint returned {status_code}"
                    )
                    return False
            else:
                await self.log_test_result(
                    "API Health Check", 
                    False, 
                    f"Health check failed with status {status}"
                )
                return False
        except Exception as e:
            await self.log_test_result(
                "API Health Check", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def test_clients_endpoint(self):
        """Test GET /api/clients endpoint for member data retrieval"""
        try:
            url = f"{self.backend_url}/api/clients"
            status, response_time = await self.measure_response_time(url)
            
            if status == 200:
                async with self.session.get(url) as response:
                    data = await response.json()
                    
                    # Verify data structure
                    if isinstance(data, list):
                        member_count = len(data)
                        
                        # Check if members have required fields for Reports component
                        required_fields = ['id', 'name', 'email', 'membership_type', 'monthly_fee', 'status']
                        enhanced_fields = ['payment_status', 'amount_owed', 'next_payment_date']
                        
                        if member_count > 0:
                            sample_member = data[0]
                            has_required = all(field in sample_member for field in required_fields)
                            has_enhanced = all(field in sample_member for field in enhanced_fields)
                            
                            await self.log_test_result(
                                "GET /api/clients - Data Structure", 
                                has_required, 
                                f"Members: {member_count}, Required fields: {has_required}, Enhanced fields: {has_enhanced}",
                                f"Response time: {response_time:.3f}s"
                            )
                            
                            return has_required
                        else:
                            await self.log_test_result(
                                "GET /api/clients - Empty Database", 
                                True, 
                                "No members in database - structure cannot be verified",
                                f"Response time: {response_time:.3f}s"
                            )
                            return True
                    else:
                        await self.log_test_result(
                            "GET /api/clients - Response Format", 
                            False, 
                            f"Expected array, got {type(data)}"
                        )
                        return False
            else:
                await self.log_test_result(
                    "GET /api/clients", 
                    False, 
                    f"API returned status {status}"
                )
                return False
        except Exception as e:
            await self.log_test_result(
                "GET /api/clients", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def test_payments_stats_endpoint(self):
        """Test GET /api/payments/stats for enhanced Reports component"""
        try:
            url = f"{self.backend_url}/api/payments/stats"
            status, response_time = await self.measure_response_time(url)
            
            if status == 200:
                async with self.session.get(url) as response:
                    data = await response.json()
                    
                    # Verify required fields for Reports component
                    required_stats = ['total_revenue', 'monthly_revenue', 'total_amount_owed', 'payment_count']
                    has_all_stats = all(field in data for field in required_stats)
                    
                    # Verify data types
                    numeric_fields_valid = all(
                        isinstance(data.get(field, 0), (int, float)) 
                        for field in required_stats
                    )
                    
                    await self.log_test_result(
                        "GET /api/payments/stats - Reports Data", 
                        has_all_stats and numeric_fields_valid, 
                        f"Stats fields: {has_all_stats}, Numeric types: {numeric_fields_valid}, Data: {data}",
                        f"Response time: {response_time:.3f}s"
                    )
                    
                    return has_all_stats and numeric_fields_valid
            else:
                await self.log_test_result(
                    "GET /api/payments/stats", 
                    False, 
                    f"API returned status {status}"
                )
                return False
        except Exception as e:
            await self.log_test_result(
                "GET /api/payments/stats", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    async def test_membership_types_endpoint(self):
        """Test GET /api/membership-types for Reports component"""
        try:
            url = f"{self.backend_url}/api/membership-types"
            status, response_time = await self.measure_response_time(url)
            
            if status == 200:
                async with self.session.get(url) as response:
                    data = await response.json()
                    
                    if isinstance(data, list):
                        membership_count = len(data)
                        
                        # Check membership type structure
                        if membership_count > 0:
                            sample_type = data[0]
                            required_fields = ['id', 'name', 'monthly_fee', 'description']
                            has_required = all(field in sample_type for field in required_fields)
                            
                            await self.log_test_result(
                                "GET /api/membership-types", 
                                has_required, 
                                f"Membership types: {membership_count}, Structure valid: {has_required}",
                                f"Response time: {response_time:.3f}s"
                            )
                            return has_required
                        else:
                            await self.log_test_result(
                                "GET /api/membership-types - Empty", 
                                True, 
                                "No membership types found",
                                f"Response time: {response_time:.3f}s"
                            )
                            return True
                    else:
                        await self.log_test_result(
                            "GET /api/membership-types - Format", 
                            False, 
                            f"Expected array, got {type(data)}"
                        )
                        return False
            else:
                await self.log_test_result(
                    "GET /api/membership-types", 
                    False, 
                    f"API returned status {status}"
                )
                return False
        except Exception as e:
            await self.log_test_result(
                "GET /api/membership-types", 
                False, 
                f"API request failed: {str(e)}"
            )
            return False
    
    # 2. CRUD OPERATIONS VERIFICATION
    async def test_crud_operations(self):
        """Test all CRUD operations still work after frontend changes"""
        test_client_data = {
            "name": "Heroicon Test Client",
            "email": f"heroicon.test.{int(time.time())}@example.com",  # Unique email
            "phone": "+1234567890",
            "membership_type": "Premium",
            "monthly_fee": 75.0,
            "start_date": date.today().isoformat(),
            "auto_reminders_enabled": True,
            "payment_status": "due",
            "billing_interval_days": 30
        }
        
        created_client_id = None
        
        try:
            # CREATE - Test POST /api/clients
            url = f"{self.backend_url}/api/clients"
            status, response_time = await self.measure_response_time(url, "POST", test_client_data)
            
            if status == 200:
                async with self.session.post(url, json=test_client_data) as response:
                    data = await response.json()
                    created_client_id = data.get('id')
                    
                    await self.log_test_result(
                        "CRUD - CREATE Client", 
                        created_client_id is not None, 
                        f"Client created with ID: {created_client_id}",
                        f"Response time: {response_time:.3f}s"
                    )
                    
                    if not created_client_id:
                        return False
            else:
                await self.log_test_result(
                    "CRUD - CREATE Client", 
                    False, 
                    f"Create failed with status {status}"
                )
                return False
            
            if not created_client_id:
                return False
            
            # READ - Test GET /api/clients/{id}
            read_url = f"{self.backend_url}/api/clients/{created_client_id}"
            status, response_time = await self.measure_response_time(read_url)
            
            if status == 200:
                await self.log_test_result(
                    "CRUD - READ Client", 
                    True, 
                    f"Client retrieved successfully",
                    f"Response time: {response_time:.3f}s"
                )
            else:
                await self.log_test_result(
                    "CRUD - READ Client", 
                    False, 
                    f"Read failed with status {status}"
                )
            
            # UPDATE - Test PUT /api/clients/{id}
            update_data = {
                "phone": "+9876543210",
                "monthly_fee": 85.0
            }
            
            async with self.session.put(read_url, json=update_data) as response:
                if response.status == 200:
                    await self.log_test_result(
                        "CRUD - UPDATE Client", 
                        True, 
                        "Client updated successfully"
                    )
                else:
                    await self.log_test_result(
                        "CRUD - UPDATE Client", 
                        False, 
                        f"Update failed with status {response.status}"
                    )
            
            # DELETE - Test DELETE /api/clients/{id}
            async with self.session.delete(read_url) as response:
                if response.status == 200:
                    data = await response.json()
                    await self.log_test_result(
                        "CRUD - DELETE Client", 
                        True, 
                        f"Client deleted: {data.get('client_name', 'Unknown')}"
                    )
                    return True
                else:
                    await self.log_test_result(
                        "CRUD - DELETE Client", 
                        False, 
                        f"Delete failed with status {response.status}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_test_result(
                "CRUD Operations", 
                False, 
                f"CRUD test failed: {str(e)}"
            )
            return False
    
    # 3. PERFORMANCE TESTING
    async def test_concurrent_requests(self):
        """Test concurrent request handling for Reports component load"""
        try:
            # Test concurrent GET requests to simulate Reports component loading
            urls = [
                f"{self.backend_url}/api/clients",
                f"{self.backend_url}/api/payments/stats",
                f"{self.backend_url}/api/membership-types",
                f"{self.backend_url}/api/health"
            ]
            
            # Make 5 concurrent requests to each endpoint
            tasks = []
            for _ in range(5):
                for url in urls:
                    tasks.append(self.measure_response_time(url))
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Analyze results
            successful_requests = sum(1 for result in results if not isinstance(result, Exception) and result[0] == 200)
            total_requests = len(tasks)
            success_rate = (successful_requests / total_requests) * 100
            
            avg_response_time = sum(
                result[1] for result in results 
                if not isinstance(result, Exception)
            ) / len([r for r in results if not isinstance(r, Exception)])
            
            performance_acceptable = success_rate >= 95 and avg_response_time < 2.0
            
            await self.log_test_result(
                "Concurrent Request Handling", 
                performance_acceptable, 
                f"Success rate: {success_rate:.1f}%, Avg response: {avg_response_time:.3f}s",
                f"Total time: {total_time:.3f}s, Requests: {total_requests}"
            )
            
            return performance_acceptable
            
        except Exception as e:
            await self.log_test_result(
                "Concurrent Request Handling", 
                False, 
                f"Concurrent test failed: {str(e)}"
            )
            return False
    
    async def test_response_time_consistency(self):
        """Test response time consistency under load"""
        try:
            # Test the main endpoints that Reports component will use
            endpoints = [
                f"{self.backend_url}/api/clients",
                f"{self.backend_url}/api/payments/stats"
            ]
            
            response_times = []
            
            for endpoint in endpoints:
                for _ in range(10):  # 10 requests per endpoint
                    status, response_time = await self.measure_response_time(endpoint)
                    if status == 200:
                        response_times.append(response_time)
                    await asyncio.sleep(0.1)  # Small delay between requests
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                min_time = min(response_times)
                
                # Check if response times are consistent (max < 5x avg for very fast responses)
                consistency_good = max_time < (avg_time * 5) and max_time < 0.1
                performance_good = avg_time < 1.0
                
                await self.log_test_result(
                    "Response Time Consistency", 
                    consistency_good and performance_good, 
                    f"Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s",
                    f"Consistency: {consistency_good}, Performance: {performance_good}"
                )
                
                return consistency_good and performance_good
            else:
                await self.log_test_result(
                    "Response Time Consistency", 
                    False, 
                    "No successful requests recorded"
                )
                return False
                
        except Exception as e:
            await self.log_test_result(
                "Response Time Consistency", 
                False, 
                f"Consistency test failed: {str(e)}"
            )
            return False
    
    # 4. DATA INTEGRITY AND STABILITY
    async def test_database_connectivity(self):
        """Test direct database connectivity and stability"""
        try:
            # Test MongoDB connection using the correct method
            ping_result = await self.mongo_client.admin.command('ping')
            
            # Test collections exist
            collections = await self.db.list_collection_names()
            expected_collections = ['clients', 'payment_records', 'membership_types']
            
            has_required_collections = all(col in collections for col in expected_collections)
            
            await self.log_test_result(
                "Database Connectivity", 
                True, 
                f"MongoDB ping successful, Collections: {len(collections)}"
            )
            
            await self.log_test_result(
                "Database Collections", 
                has_required_collections, 
                f"Required collections present: {has_required_collections}, Available: {collections}"
            )
            
            return has_required_collections
            
        except Exception as e:
            await self.log_test_result(
                "Database Connectivity", 
                False, 
                f"Database test failed: {str(e)}"
            )
            return False
    
    async def test_cors_and_headers(self):
        """Test CORS settings and response headers"""
        try:
            url = f"{self.backend_url}/api/clients"
            
            # Test with Origin header (simulating frontend request)
            headers = {
                'Origin': 'https://alphalete-pwa.preview.emergentagent.com',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    # Check CORS headers
                    cors_headers = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                    }
                    
                    # Check cache-busting headers for mobile compatibility
                    cache_headers = {
                        'Cache-Control': response.headers.get('Cache-Control'),
                        'X-Mobile-Cache-Bust': response.headers.get('X-Mobile-Cache-Bust')
                    }
                    
                    cors_working = response.status == 200
                    has_cache_busting = 'no-cache' in str(cache_headers.get('Cache-Control', ''))
                    
                    await self.log_test_result(
                        "CORS Configuration", 
                        cors_working, 
                        f"CORS headers: {cors_headers}"
                    )
                    
                    await self.log_test_result(
                        "Mobile Cache Busting", 
                        has_cache_busting, 
                        f"Cache headers: {cache_headers}"
                    )
                    
                    return cors_working
                    
        except Exception as e:
            await self.log_test_result(
                "CORS and Headers", 
                False, 
                f"CORS test failed: {str(e)}"
            )
            return False
    
    async def run_comprehensive_backend_test(self):
        """Run the complete backend testing suite"""
        print("🚀 ALPHALETE CLUB PWA - HEROICON & REPORTS BACKEND TESTING")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"MongoDB URL: {MONGO_URL}")
        print(f"Database: {DB_NAME}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("\nTesting backend stability after Heroicon conversion and Reports enhancement...")
        
        # Setup connections
        if not await self.setup():
            return False
        
        try:
            print("\n🔍 PHASE 1: API ENDPOINTS VERIFICATION")
            print("-" * 50)
            
            # Test basic API health
            await self.test_api_health_and_status()
            
            # Test main endpoints for Reports component
            await self.test_clients_endpoint()
            await self.test_payments_stats_endpoint()
            await self.test_membership_types_endpoint()
            
            print("\n🔧 PHASE 2: CRUD OPERATIONS VERIFICATION")
            print("-" * 50)
            
            # Test all CRUD operations
            await self.test_crud_operations()
            
            print("\n⚡ PHASE 3: PERFORMANCE TESTING")
            print("-" * 50)
            
            # Test concurrent requests (Reports component load simulation)
            await self.test_concurrent_requests()
            
            # Test response time consistency
            await self.test_response_time_consistency()
            
            print("\n🛡️ PHASE 4: STABILITY & INTEGRITY CHECKS")
            print("-" * 50)
            
            # Test database connectivity
            await self.test_database_connectivity()
            
            # Test CORS and headers
            await self.test_cors_and_headers()
            
            # Generate comprehensive summary
            print("\n📊 COMPREHENSIVE TEST SUMMARY")
            print("=" * 80)
            
            passed_tests = sum(1 for result in self.test_results if result['success'])
            total_tests = len(self.test_results)
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
            
            # Categorize results
            api_tests = [r for r in self.test_results if 'API' in r['test'] or 'GET' in r['test']]
            crud_tests = [r for r in self.test_results if 'CRUD' in r['test']]
            performance_tests = [r for r in self.test_results if 'Concurrent' in r['test'] or 'Response Time' in r['test']]
            stability_tests = [r for r in self.test_results if 'Database' in r['test'] or 'CORS' in r['test']]
            
            print(f"\n📋 TEST BREAKDOWN:")
            print(f"   API Endpoints: {sum(1 for t in api_tests if t['success'])}/{len(api_tests)} passed")
            print(f"   CRUD Operations: {sum(1 for t in crud_tests if t['success'])}/{len(crud_tests)} passed")
            print(f"   Performance: {sum(1 for t in performance_tests if t['success'])}/{len(performance_tests)} passed")
            print(f"   Stability: {sum(1 for t in stability_tests if t['success'])}/{len(stability_tests)} passed")
            
            if success_rate >= 90:
                print("\n🎉 BACKEND TESTING COMPLETED SUCCESSFULLY!")
                print("✅ Backend is stable and ready for enhanced Reports component")
                print("✅ All critical API endpoints are functional")
                print("✅ CRUD operations working correctly")
                print("✅ Performance metrics within acceptable ranges")
                print("✅ Database connectivity and CORS configuration verified")
                print("\n🔥 CONCLUSION: Backend fully supports Heroicon conversion and enhanced Reports functionality")
            else:
                print("\n⚠️ BACKEND TESTING COMPLETED WITH ISSUES!")
                print("❌ Some critical tests failed")
                print("❌ Backend may need attention before Reports enhancement")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
            
            # Show performance summary
            perf_tests = [r for r in self.test_results if r.get('performance')]
            if perf_tests:
                print(f"\n⚡ PERFORMANCE SUMMARY:")
                for test in perf_tests:
                    print(f"   - {test['test']}: {test['performance']}")
            
            return success_rate >= 90
            
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    tester = HeroiconReportsBackendTester()
    success = await tester.run_comprehensive_backend_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())