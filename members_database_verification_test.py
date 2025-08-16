#!/usr/bin/env python3
"""
Members Database Verification Test
Specific test to verify if there are existing members in the MongoDB database
and if the backend API endpoints for getting members are working correctly.

This addresses the user's question: "No members yet" display - is this correct?

VERIFICATION POINTS:
1. Check if existing members/clients exist in MongoDB database
2. Test GET /api/clients endpoint functionality
3. Verify sample data presence
4. Test data loading and sync between backend and frontend
5. Determine if "No members yet" display is accurate
"""

import requests
import json
import sys
import os
from datetime import datetime, date
from typing import Dict, List, Any

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fitness-club-app-2.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Backend URL: {BACKEND_URL}")
print(f"🕐 Members Database Verification Started: {datetime.now().isoformat()}")
print("=" * 80)

class MembersDatabaseVerifier:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def make_request(self, method, endpoint, data=None, timeout=10):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            headers = {'Content-Type': 'application/json'}
            if method == "GET":
                response = requests.get(url, timeout=timeout, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=timeout, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None

    def test_backend_connectivity(self):
        """Test 1: Backend Connectivity - verify backend is accessible"""
        print("\n🔍 TEST 1: Backend Connectivity Check")
        print("-" * 50)
        
        # Test main API status
        response = self.make_request("GET", "/")
        if not response:
            self.log_test("Backend API Connectivity", False, "Backend not accessible")
            return False
            
        if response.status_code == 200:
            api_data = response.json()
            self.log_test("Backend API Connectivity", True, 
                        f"Status: {api_data.get('status')}, Version: {api_data.get('version')}")
            return True
        else:
            self.log_test("Backend API Connectivity", False, f"HTTP {response.status_code}")
            return False

    def test_members_endpoint_functionality(self):
        """Test 2: Members Endpoint - test GET /api/clients functionality"""
        print("\n🔍 TEST 2: Members Endpoint Functionality")
        print("-" * 50)
        
        # Test GET /api/clients
        response = self.make_request("GET", "/clients")
        if not response:
            self.log_test("GET /api/clients Endpoint", False, "Request failed")
            return False, None
            
        if response.status_code == 200:
            try:
                clients = response.json()
                self.log_test("GET /api/clients Endpoint", True, 
                            f"Endpoint working, returned {len(clients)} clients")
                
                # Check response format
                if isinstance(clients, list):
                    self.log_test("Response Format", True, "Proper JSON array format")
                    return True, clients
                else:
                    self.log_test("Response Format", False, f"Expected array, got {type(clients)}")
                    return False, None
                    
            except json.JSONDecodeError:
                self.log_test("GET /api/clients Endpoint", False, "Invalid JSON response")
                return False, None
        else:
            self.log_test("GET /api/clients Endpoint", False, f"HTTP {response.status_code}")
            return False, None

    def analyze_existing_members_data(self, clients):
        """Test 3: Analyze existing members data in database"""
        print("\n🔍 TEST 3: Existing Members Data Analysis")
        print("-" * 50)
        
        if not clients:
            self.log_test("Members Database Status", True, 
                        "Database is empty - 'No members yet' display is CORRECT")
            return True, "empty"
            
        total_members = len(clients)
        self.log_test("Total Members in Database", True, f"Found {total_members} members")
        
        # Analyze member data structure
        if total_members > 0:
            sample_member = clients[0]
            required_fields = ['id', 'name', 'email', 'membership_type', 'status']
            
            has_required_fields = all(field in sample_member for field in required_fields)
            self.log_test("Member Data Structure", has_required_fields,
                        f"Required fields present: {has_required_fields}")
            
            # Analyze member statuses
            active_members = [c for c in clients if c.get('status') == 'Active']
            inactive_members = [c for c in clients if c.get('status') != 'Active']
            
            self.log_test("Active Members Count", True, f"{len(active_members)} active members")
            self.log_test("Inactive Members Count", True, f"{len(inactive_members)} inactive members")
            
            # Analyze payment statuses
            paid_members = [c for c in clients if c.get('payment_status') == 'paid']
            due_members = [c for c in clients if c.get('payment_status') == 'due']
            overdue_members = [c for c in clients if c.get('payment_status') == 'overdue']
            
            self.log_test("Payment Status Distribution", True,
                        f"Paid: {len(paid_members)}, Due: {len(due_members)}, Overdue: {len(overdue_members)}")
            
            # Show sample member data (first 3 members)
            print("\n📋 SAMPLE MEMBER DATA:")
            for i, member in enumerate(clients[:3]):
                print(f"   Member {i+1}: {member.get('name', 'Unknown')} ({member.get('email', 'No email')})")
                print(f"      Status: {member.get('status', 'Unknown')}, Payment: {member.get('payment_status', 'Unknown')}")
                print(f"      Membership: {member.get('membership_type', 'Unknown')}, Fee: TTD {member.get('monthly_fee', 0)}")
            
            if total_members > 3:
                print(f"   ... and {total_members - 3} more members")
                
            return True, "populated"
        else:
            return True, "empty"

    def test_payment_statistics(self):
        """Test 4: Payment Statistics - check if there's payment data"""
        print("\n🔍 TEST 4: Payment Statistics Analysis")
        print("-" * 50)
        
        response = self.make_request("GET", "/payments/stats")
        if not response:
            self.log_test("Payment Statistics Endpoint", False, "Request failed")
            return False
            
        if response.status_code == 200:
            try:
                stats = response.json()
                total_revenue = stats.get('total_revenue', 0)
                payment_count = stats.get('payment_count', 0)
                total_amount_owed = stats.get('total_amount_owed', 0)
                
                self.log_test("Payment Statistics Endpoint", True, "Endpoint working")
                self.log_test("Total Revenue", True, f"TTD {total_revenue}")
                self.log_test("Payment Count", True, f"{payment_count} payments recorded")
                self.log_test("Total Amount Owed", True, f"TTD {total_amount_owed}")
                
                # Determine if there's financial activity
                has_financial_activity = total_revenue > 0 or payment_count > 0 or total_amount_owed > 0
                self.log_test("Financial Activity Present", has_financial_activity,
                            f"Financial data exists: {has_financial_activity}")
                
                return True
                
            except json.JSONDecodeError:
                self.log_test("Payment Statistics Endpoint", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Payment Statistics Endpoint", False, f"HTTP {response.status_code}")
            return False

    def test_membership_types_availability(self):
        """Test 5: Membership Types - check if membership plans exist"""
        print("\n🔍 TEST 5: Membership Types Availability")
        print("-" * 50)
        
        response = self.make_request("GET", "/membership-types")
        if not response:
            self.log_test("Membership Types Endpoint", False, "Request failed")
            return False
            
        if response.status_code == 200:
            try:
                membership_types = response.json()
                type_count = len(membership_types)
                
                self.log_test("Membership Types Endpoint", True, "Endpoint working")
                self.log_test("Available Membership Types", True, f"{type_count} types available")
                
                if type_count > 0:
                    print("\n📋 AVAILABLE MEMBERSHIP TYPES:")
                    for membership_type in membership_types:
                        name = membership_type.get('name', 'Unknown')
                        fee = membership_type.get('monthly_fee', 0)
                        print(f"   - {name}: TTD {fee}/month")
                
                return True
                
            except json.JSONDecodeError:
                self.log_test("Membership Types Endpoint", False, "Invalid JSON response")
                return False
        else:
            self.log_test("Membership Types Endpoint", False, f"HTTP {response.status_code}")
            return False

    def test_cache_busting_headers(self):
        """Test 6: Cache Busting - verify mobile cache-busting headers"""
        print("\n🔍 TEST 6: Mobile Cache-Busting Headers")
        print("-" * 50)
        
        response = self.make_request("GET", "/clients")
        if not response:
            self.log_test("Cache-Busting Headers Test", False, "Request failed")
            return False
            
        # Check for cache-busting headers
        cache_control = response.headers.get('Cache-Control', '')
        mobile_cache_bust = response.headers.get('X-Mobile-Cache-Bust', '')
        pragma = response.headers.get('Pragma', '')
        
        has_cache_control = 'no-cache' in cache_control.lower()
        has_mobile_header = bool(mobile_cache_bust)
        has_pragma = 'no-cache' in pragma.lower()
        
        self.log_test("Cache-Control Header", has_cache_control, f"Cache-Control: {cache_control}")
        self.log_test("Mobile Cache-Bust Header", has_mobile_header, f"X-Mobile-Cache-Bust: {mobile_cache_bust}")
        self.log_test("Pragma Header", has_pragma, f"Pragma: {pragma}")
        
        cache_busting_working = has_cache_control or has_mobile_header
        self.log_test("Cache-Busting Mechanism", cache_busting_working,
                    "Mobile cache-busting headers present")
        
        return True

    def run_verification(self):
        """Run complete members database verification"""
        print("🚀 STARTING MEMBERS DATABASE VERIFICATION")
        print("🎯 Focus: Verify existing members data and API functionality")
        print("❓ Question: Is 'No members yet' display correct?")
        print("=" * 80)
        
        # Test sequence
        verification_successful = True
        
        # Test 1: Backend connectivity
        if not self.test_backend_connectivity():
            verification_successful = False
            
        # Test 2: Members endpoint functionality
        endpoint_working, clients_data = self.test_members_endpoint_functionality()
        if not endpoint_working:
            verification_successful = False
            
        # Test 3: Analyze existing data
        if endpoint_working:
            data_analysis_success, database_status = self.analyze_existing_members_data(clients_data)
            if not data_analysis_success:
                verification_successful = False
        else:
            database_status = "unknown"
            
        # Test 4: Payment statistics
        self.test_payment_statistics()
        
        # Test 5: Membership types
        self.test_membership_types_availability()
        
        # Test 6: Cache busting
        self.test_cache_busting_headers()
        
        # Summary and conclusion
        print("\n" + "=" * 80)
        print("📊 MEMBERS DATABASE VERIFICATION SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        # Key findings
        print("\n🎯 KEY FINDINGS:")
        print("-" * 50)
        
        if database_status == "empty":
            print("✅ CONCLUSION: 'No members yet' display is CORRECT")
            print("   📝 The MongoDB database contains no member/client records")
            print("   📝 Backend API endpoints are working properly")
            print("   📝 This is likely a new installation or all members have been removed")
            
        elif database_status == "populated":
            print("❌ CONCLUSION: 'No members yet' display is INCORRECT")
            print("   📝 The MongoDB database contains member/client records")
            print("   📝 Backend API endpoints are working properly")
            print("   📝 There may be a frontend-backend sync issue")
            print("   📝 Frontend may not be properly loading data from backend")
            
        else:
            print("⚠️  CONCLUSION: Unable to determine database status")
            print("   📝 Backend connectivity issues prevent verification")
            print("   📝 API endpoints may not be functioning properly")
            
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 50)
        
        if database_status == "empty":
            print("   1. 'No members yet' display is working correctly")
            print("   2. Consider adding sample data if this is a demo environment")
            print("   3. Test member creation functionality to verify it works")
            
        elif database_status == "populated":
            print("   1. Check frontend data loading logic")
            print("   2. Verify frontend is calling correct API endpoints")
            print("   3. Check browser console for JavaScript errors")
            print("   4. Verify frontend environment variables (REACT_APP_BACKEND_URL)")
            print("   5. Test frontend-backend connectivity from browser")
            
        else:
            print("   1. Fix backend connectivity issues first")
            print("   2. Check backend server status")
            print("   3. Verify API endpoint URLs")
            print("   4. Check network connectivity")
            
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
                    
        print(f"\n🏁 Verification completed at: {datetime.now().isoformat()}")
        
        return verification_successful and success_rate >= 80.0

def main():
    """Main verification execution"""
    try:
        verifier = MembersDatabaseVerifier(BACKEND_URL)
        success = verifier.run_verification()
        
        if success:
            print("\n🎉 MEMBERS DATABASE VERIFICATION: COMPLETE!")
            print("✅ Backend API endpoints are functional")
            print("✅ Database status has been determined")
            print("✅ 'No members yet' display accuracy verified")
            sys.exit(0)
        else:
            print("\n🚨 MEMBERS DATABASE VERIFICATION: ISSUES DETECTED!")
            print("❌ Some issues were found during verification")
            print("❌ Check the detailed results above for specific problems")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()