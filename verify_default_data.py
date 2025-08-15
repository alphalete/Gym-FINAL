#!/usr/bin/env python3
"""
Verify Default Data Creation - Alphalete Club PWA
Purpose: Verify that membership plans and test members were created successfully
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://gogym4u-app.preview.emergentagent.com"

class DataVerifier:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = None
        
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
    
    async def verify_membership_plans(self):
        """Verify membership plans exist"""
        try:
            url = f"{self.backend_url}/api/membership-types"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"📋 MEMBERSHIP PLANS VERIFICATION:")
                    print(f"   Total plans found: {len(data)}")
                    
                    # Look for our required plans
                    required_plans = {'Basic': 55.0, 'Premium': 75.0, 'Elite': 100.0}
                    found_plans = {}
                    
                    for plan in data:
                        name = plan.get('name')
                        fee = plan.get('monthly_fee')
                        if name in required_plans:
                            found_plans[name] = fee
                            print(f"   ✅ {name}: TTD {fee} (ID: {plan.get('id')})")
                    
                    # Check if all required plans exist
                    missing_plans = set(required_plans.keys()) - set(found_plans.keys())
                    if missing_plans:
                        print(f"   ❌ Missing plans: {missing_plans}")
                        return False
                    
                    # Check if fees match
                    for name, expected_fee in required_plans.items():
                        actual_fee = found_plans.get(name)
                        if actual_fee != expected_fee:
                            print(f"   ❌ {name} fee mismatch: expected TTD {expected_fee}, got TTD {actual_fee}")
                            return False
                    
                    print("   ✅ All required membership plans verified successfully!")
                    return True
                else:
                    print(f"   ❌ API returned status {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ API request failed: {str(e)}")
            return False
    
    async def verify_test_members(self):
        """Verify test members exist"""
        try:
            url = f"{self.backend_url}/api/clients"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"\n👤 TEST MEMBERS VERIFICATION:")
                    print(f"   Total members found: {len(data)}")
                    
                    # Look for John Smith
                    john_smith = None
                    for member in data:
                        if member.get('name') == 'John Smith' and member.get('email') == 'john.smith@test.com':
                            john_smith = member
                            break
                    
                    if john_smith:
                        print(f"   ✅ John Smith found:")
                        print(f"      - ID: {john_smith.get('id')}")
                        print(f"      - Email: {john_smith.get('email')}")
                        print(f"      - Phone: {john_smith.get('phone')}")
                        print(f"      - Membership: {john_smith.get('membership_type')}")
                        print(f"      - Monthly Fee: TTD {john_smith.get('monthly_fee')}")
                        print(f"      - Status: {john_smith.get('status')}")
                        
                        # Verify details match requirements
                        expected = {
                            'name': 'John Smith',
                            'email': 'john.smith@test.com',
                            'phone': '+1234567890',
                            'membership_type': 'Basic',
                            'monthly_fee': 55.0,
                            'status': 'Active'
                        }
                        
                        all_match = True
                        for key, expected_value in expected.items():
                            actual_value = john_smith.get(key)
                            if actual_value != expected_value:
                                print(f"      ❌ {key} mismatch: expected {expected_value}, got {actual_value}")
                                all_match = False
                        
                        if all_match:
                            print("   ✅ John Smith details verified successfully!")
                            return True
                        else:
                            print("   ❌ John Smith details don't match requirements")
                            return False
                    else:
                        print("   ❌ John Smith not found")
                        return False
                else:
                    print(f"   ❌ API returned status {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ API request failed: {str(e)}")
            return False
    
    async def test_edit_member_readiness(self):
        """Test if Edit Member functionality can now be tested"""
        print(f"\n🔧 EDIT MEMBER FUNCTIONALITY READINESS:")
        
        # Check if we have both plans and members
        plans_ok = await self.verify_membership_plans()
        members_ok = await self.verify_test_members()
        
        if plans_ok and members_ok:
            print("   ✅ Edit Member functionality is ready for testing!")
            print("   ✅ Membership plans available for dropdown selection")
            print("   ✅ Test member available for editing")
            print("   ✅ All requirements from review request satisfied")
            return True
        else:
            print("   ❌ Edit Member functionality is NOT ready for testing")
            return False
    
    async def run_verification(self):
        """Run the complete verification process"""
        print("🔍 ALPHALETE CLUB PWA - VERIFY DEFAULT DATA CREATION")
        print("=" * 70)
        print(f"Backend URL: {self.backend_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        await self.setup()
        
        try:
            success = await self.test_edit_member_readiness()
            
            print(f"\n📋 VERIFICATION SUMMARY")
            print("=" * 70)
            
            if success:
                print("🎉 VERIFICATION COMPLETED SUCCESSFULLY!")
                print("✅ All default data created as specified in review request")
                print("✅ Edit Member functionality can now be tested")
                print("✅ Testing agent can proceed with Edit Member testing")
            else:
                print("❌ VERIFICATION FAILED!")
                print("❌ Some required data is missing or incorrect")
            
            return success
            
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    verifier = DataVerifier()
    success = await verifier.run_verification()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nVerification {'PASSED' if result else 'FAILED'}")