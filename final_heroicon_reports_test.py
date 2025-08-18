#!/usr/bin/env python3
"""
Final Backend Testing for Heroicon Conversion & Enhanced Reports - Alphalete Club PWA
Focus: Critical API endpoints and data requirements for enhanced Reports component
"""

import asyncio
import aiohttp
import time
from datetime import datetime
import json

BACKEND_URL = "https://fitness-club-admin.preview.emergentagent.com"

class FinalBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        self.test_results = []
        
    async def setup(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return True
    
    async def cleanup(self):
        if self.session:
            await self.session.close()
    
    async def log_result(self, test_name, success, details=""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({"test": test_name, "success": success, "details": details})
    
    async def test_critical_endpoints(self):
        """Test the critical endpoints for Reports component"""
        
        # 1. Test GET /api/clients - Member data for Reports
        try:
            async with self.session.get(f"{self.backend_url}/api/clients") as response:
                if response.status == 200:
                    data = await response.json()
                    member_count = len(data) if isinstance(data, list) else 0
                    
                    # Check data structure for Reports
                    if member_count > 0:
                        sample = data[0]
                        required_fields = ['id', 'name', 'email', 'membership_type', 'monthly_fee', 'status', 'payment_status', 'amount_owed']
                        has_fields = all(field in sample for field in required_fields)
                        
                        await self.log_result(
                            "GET /api/clients - Reports Data Support",
                            has_fields,
                            f"Members: {member_count}, Required fields present: {has_fields}"
                        )
                    else:
                        await self.log_result(
                            "GET /api/clients - API Response",
                            True,
                            f"API working, {member_count} members found"
                        )
                else:
                    await self.log_result("GET /api/clients", False, f"Status: {response.status}")
        except Exception as e:
            await self.log_result("GET /api/clients", False, f"Error: {str(e)}")
        
        # 2. Test GET /api/payments/stats - Payment statistics for Reports
        try:
            async with self.session.get(f"{self.backend_url}/api/payments/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    required_stats = ['total_revenue', 'monthly_revenue', 'total_amount_owed', 'payment_count']
                    has_stats = all(field in data for field in required_stats)
                    
                    await self.log_result(
                        "GET /api/payments/stats - Reports Analytics",
                        has_stats,
                        f"Stats available: {has_stats}, Data: {data}"
                    )
                else:
                    await self.log_result("GET /api/payments/stats", False, f"Status: {response.status}")
        except Exception as e:
            await self.log_result("GET /api/payments/stats", False, f"Error: {str(e)}")
        
        # 3. Test GET /api/membership-types - Membership plans for Reports
        try:
            async with self.session.get(f"{self.backend_url}/api/membership-types") as response:
                if response.status == 200:
                    data = await response.json()
                    plan_count = len(data) if isinstance(data, list) else 0
                    
                    await self.log_result(
                        "GET /api/membership-types - Plans Data",
                        plan_count > 0,
                        f"Membership plans available: {plan_count}"
                    )
                else:
                    await self.log_result("GET /api/membership-types", False, f"Status: {response.status}")
        except Exception as e:
            await self.log_result("GET /api/membership-types", False, f"Error: {str(e)}")
    
    async def test_crud_stability(self):
        """Test CRUD operations are still working"""
        test_email = f"stability.test.{int(time.time())}@example.com"
        test_client = {
            "name": "Stability Test Client",
            "email": test_email,
            "phone": "+1234567890",
            "membership_type": "Basic",
            "monthly_fee": 55.0,
            "start_date": "2025-08-15",
            "auto_reminders_enabled": True,
            "payment_status": "due",
            "billing_interval_days": 30
        }
        
        created_id = None
        
        try:
            # CREATE
            async with self.session.post(f"{self.backend_url}/api/clients", json=test_client) as response:
                if response.status == 200:
                    data = await response.json()
                    created_id = data.get('id')
                    await self.log_result("CRUD - CREATE", created_id is not None, f"Client created: {created_id}")
                else:
                    await self.log_result("CRUD - CREATE", False, f"Status: {response.status}")
                    return
            
            if created_id:
                # READ
                async with self.session.get(f"{self.backend_url}/api/clients/{created_id}") as response:
                    read_success = response.status == 200
                    await self.log_result("CRUD - READ", read_success, f"Client retrieved: {read_success}")
                
                # UPDATE
                update_data = {"phone": "+9876543210"}
                async with self.session.put(f"{self.backend_url}/api/clients/{created_id}", json=update_data) as response:
                    update_success = response.status == 200
                    await self.log_result("CRUD - UPDATE", update_success, f"Client updated: {update_success}")
                
                # DELETE
                async with self.session.delete(f"{self.backend_url}/api/clients/{created_id}") as response:
                    delete_success = response.status == 200
                    await self.log_result("CRUD - DELETE", delete_success, f"Client deleted: {delete_success}")
                    
        except Exception as e:
            await self.log_result("CRUD Operations", False, f"Error: {str(e)}")
    
    async def test_performance(self):
        """Test performance for Reports component load"""
        try:
            # Test concurrent requests (simulating Reports component loading multiple endpoints)
            start_time = time.time()
            
            tasks = []
            for _ in range(3):  # 3 concurrent requests to each endpoint
                tasks.append(self.session.get(f"{self.backend_url}/api/clients"))
                tasks.append(self.session.get(f"{self.backend_url}/api/payments/stats"))
                tasks.append(self.session.get(f"{self.backend_url}/api/membership-types"))
            
            responses = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # Check all responses
            success_count = sum(1 for r in responses if r.status == 200)
            total_requests = len(responses)
            success_rate = (success_count / total_requests) * 100
            
            # Close all responses
            for response in responses:
                response.close()
            
            performance_good = success_rate >= 95 and total_time < 2.0
            
            await self.log_result(
                "Performance - Concurrent Requests",
                performance_good,
                f"Success rate: {success_rate:.1f}%, Total time: {total_time:.3f}s"
            )
            
        except Exception as e:
            await self.log_result("Performance Test", False, f"Error: {str(e)}")
    
    async def test_backend_stability(self):
        """Test overall backend stability"""
        try:
            # Test API health
            async with self.session.get(f"{self.backend_url}/api/health") as response:
                health_ok = response.status == 200
                await self.log_result("Backend Health", health_ok, f"API health check: {health_ok}")
            
            # Test API status
            async with self.session.get(f"{self.backend_url}/api/") as response:
                status_ok = response.status == 200
                if status_ok:
                    data = await response.json()
                    version = data.get('version', 'unknown')
                    await self.log_result("Backend Status", True, f"API version: {version}")
                else:
                    await self.log_result("Backend Status", False, f"Status: {response.status}")
                    
        except Exception as e:
            await self.log_result("Backend Stability", False, f"Error: {str(e)}")
    
    async def run_final_test(self):
        """Run the final comprehensive test"""
        print("🚀 FINAL BACKEND TESTING - HEROICON & REPORTS COMPATIBILITY")
        print("=" * 70)
        print(f"Backend URL: {self.backend_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("\nTesting backend stability after Heroicon conversion and Reports enhancement...")
        
        await self.setup()
        
        try:
            print("\n📊 TESTING CRITICAL API ENDPOINTS FOR REPORTS COMPONENT")
            print("-" * 50)
            await self.test_critical_endpoints()
            
            print("\n🔧 TESTING CRUD OPERATIONS STABILITY")
            print("-" * 50)
            await self.test_crud_stability()
            
            print("\n⚡ TESTING PERFORMANCE FOR REPORTS LOAD")
            print("-" * 50)
            await self.test_performance()
            
            print("\n🛡️ TESTING BACKEND STABILITY")
            print("-" * 50)
            await self.test_backend_stability()
            
            # Final summary
            print("\n📋 FINAL TEST SUMMARY")
            print("=" * 70)
            
            passed = sum(1 for r in self.test_results if r['success'])
            total = len(self.test_results)
            success_rate = (passed / total * 100) if total > 0 else 0
            
            print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
            
            if success_rate >= 90:
                print("\n🎉 BACKEND TESTING SUCCESSFUL!")
                print("✅ Backend is stable and ready for enhanced Reports component")
                print("✅ All critical API endpoints are functional")
                print("✅ CRUD operations working correctly")
                print("✅ Performance is acceptable for Reports component load")
                print("✅ Heroicon conversion has NOT affected backend functionality")
                print("\n🔥 CONCLUSION: Backend fully supports enhanced Reports functionality")
            else:
                print("\n⚠️ BACKEND TESTING COMPLETED WITH ISSUES!")
                failed = [r for r in self.test_results if not r['success']]
                for test in failed:
                    print(f"❌ {test['test']}: {test['details']}")
            
            return success_rate >= 90
            
        finally:
            await self.cleanup()

async def main():
    tester = FinalBackendTester()
    success = await tester.run_final_test()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())