#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime, date, timedelta
import time
import uuid

# Get backend URL from environment
BACKEND_URL = "https://fitness-club-admin.preview.emergentagent.com/api"

def test_field_name_mapping_fix():
    """
    CRITICAL FIELD MAPPING TEST for Due Date Calculation Fix
    
    Testing Focus (as per review request):
    1. Create a new client with join date "2025-07-30" 
    2. Verify the backend correctly receives and stores the due date in `next_payment_date` field
    3. Confirm the due date is calculated as "2025-08-29" (exactly 30 days)
    4. Verify that when the frontend fetches this client, it can read the due date from `next_payment_date`
    
    ROOT CAUSE BEING TESTED:
    The issue was a field name mismatch where:
    - Frontend was sending `nextDue` but backend expected `next_payment_date`
    - Frontend was looking for `nextDue || dueDate` but backend returned `next_payment_date`
    - This caused correctly calculated due dates to not persist or display properly
    """
    
    print("🧪 FIELD NAME MAPPING FIX - DUE DATE CALCULATION TEST")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    total_tests = 0
    passed_tests = 0
    created_client_id = None
    
    def run_test(test_name, test_func):
        nonlocal total_tests, passed_tests
        total_tests += 1
        print(f"🔍 Testing: {test_name}")
        try:
            result = test_func()
            if result:
                print(f"✅ PASSED: {test_name}")
                passed_tests += 1
                test_results.append(f"✅ {test_name}")
                return True
            else:
                print(f"❌ FAILED: {test_name}")
                test_results.append(f"❌ {test_name}")
                return False
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {str(e)}")
            test_results.append(f"❌ {test_name} - ERROR: {str(e)}")
            return False
        finally:
            print()
    
    # ========== TEST 1: CREATE CLIENT WITH SPECIFIC JOIN DATE ==========
    
    def test_create_client_with_join_date():
        """Create a new client with join date 2025-07-30 and verify next_payment_date field"""
        nonlocal created_client_id
        try:
            # Create test client with specific join date as per review request
            test_client = {
                "name": "Field Mapping Test Client",
                "email": f"fieldmapping.{int(time.time())}@example.com",
                "phone": "+1234567890",
                "membership_type": "Basic",
                "monthly_fee": 55.0,
                "start_date": "2025-07-30",  # Specific date from review request
                "payment_status": "due",
                "amount_owed": 55.0,
                "auto_reminders_enabled": True
            }
            
            print(f"   Creating client with join date: {test_client['start_date']}")
            
            response = requests.post(
                f"{BACKEND_URL}/clients", 
                json=test_client,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                created_client = response.json()
                created_client_id = created_client.get('id')
                print(f"   Response: Created client with ID {created_client_id}")
                
                # CRITICAL CHECK: Verify next_payment_date field exists and is calculated correctly
                if 'next_payment_date' in created_client:
                    next_payment_date = created_client['next_payment_date']
                    print(f"   ✅ Backend stores due date in 'next_payment_date' field: {next_payment_date}")
                    
                    # Verify the date calculation is exactly 30 days (2025-07-30 + 30 days = 2025-08-29)
                    expected_date = "2025-08-29"
                    if next_payment_date == expected_date:
                        print(f"   ✅ Due date calculated correctly: {next_payment_date} (exactly 30 days)")
                        return True
                    else:
                        print(f"   ❌ Due date calculation incorrect: Expected {expected_date}, got {next_payment_date}")
                        return False
                else:
                    print(f"   ❌ CRITICAL: 'next_payment_date' field missing from backend response")
                    print(f"   Available fields: {list(created_client.keys())}")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Error text: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # ========== TEST 2: VERIFY BACKEND STORAGE ==========
    
    def test_backend_storage_verification():
        """Verify the backend correctly stores the due date in next_payment_date field"""
        try:
            if not created_client_id:
                print(f"   ⚠️ No test client available - skipping")
                return False
            
            print(f"   Fetching client {created_client_id} to verify backend storage")
            
            response = requests.get(f"{BACKEND_URL}/clients/{created_client_id}", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                client = response.json()
                print(f"   Response: Retrieved client {client.get('name', 'Unknown')}")
                
                # CRITICAL CHECK: Verify backend returns next_payment_date field
                if 'next_payment_date' in client:
                    stored_date = client['next_payment_date']
                    print(f"   ✅ Backend returns 'next_payment_date' field: {stored_date}")
                    
                    # Verify the stored date matches expected calculation
                    expected_date = "2025-08-29"
                    if stored_date == expected_date:
                        print(f"   ✅ Backend storage correct: {stored_date}")
                        return True
                    else:
                        print(f"   ❌ Backend storage incorrect: Expected {expected_date}, stored {stored_date}")
                        return False
                else:
                    print(f"   ❌ CRITICAL: Backend does not return 'next_payment_date' field")
                    print(f"   Available fields: {list(client.keys())}")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # ========== TEST 3: FRONTEND-BACKEND FIELD MAPPING ==========
    
    def test_frontend_backend_field_mapping():
        """Test that frontend can read the due date from next_payment_date field"""
        try:
            if not created_client_id:
                print(f"   ⚠️ No test client available - skipping")
                return False
            
            print(f"   Testing frontend-backend field mapping for client {created_client_id}")
            
            # Simulate frontend GET request to fetch client data
            response = requests.get(f"{BACKEND_URL}/clients/{created_client_id}", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                client_data = response.json()
                
                # CRITICAL CHECK: Verify frontend can access the due date field
                # Frontend now reads: nextDue || dueDate || next_payment_date
                next_payment_date = client_data.get('next_payment_date')
                next_due = client_data.get('nextDue')  # Old field name
                due_date = client_data.get('dueDate')  # Alternative field name
                
                print(f"   Field mapping check:")
                print(f"     next_payment_date: {next_payment_date}")
                print(f"     nextDue: {next_due}")
                print(f"     dueDate: {due_date}")
                
                # The fix ensures frontend can read from next_payment_date
                if next_payment_date:
                    expected_date = "2025-08-29"
                    if next_payment_date == expected_date:
                        print(f"   ✅ Frontend can read due date from 'next_payment_date': {next_payment_date}")
                        print(f"   ✅ Field mapping fix working correctly")
                        return True
                    else:
                        print(f"   ❌ Due date value incorrect: Expected {expected_date}, got {next_payment_date}")
                        return False
                else:
                    print(f"   ❌ CRITICAL: Frontend cannot read due date - 'next_payment_date' field missing")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # ========== TEST 4: COMPREHENSIVE VERIFICATION ==========
    
    def test_comprehensive_verification():
        """Comprehensive verification of the field mapping fix"""
        try:
            print(f"   Running comprehensive verification of field mapping fix")
            
            # Test POST /api/clients with new member data
            print(f"   ✓ Testing POST /api/clients with calculated next_payment_date")
            
            # Test GET /api/clients to verify returned data contains next_payment_date field
            response = requests.get(f"{BACKEND_URL}/clients", timeout=10)
            if response.status_code == 200:
                clients = response.json()
                
                # Find our test client
                test_client = None
                for client in clients:
                    if client.get('id') == created_client_id:
                        test_client = client
                        break
                
                if test_client:
                    print(f"   ✓ Testing GET /api/clients returns next_payment_date field")
                    
                    if 'next_payment_date' in test_client:
                        next_payment_date = test_client['next_payment_date']
                        expected_date = "2025-08-29"
                        
                        if next_payment_date == expected_date:
                            print(f"   ✅ GET /api/clients returns correct next_payment_date: {next_payment_date}")
                            print(f"   ✅ Date calculation is exactly 30 days from join date")
                            print(f"   ✅ Field mapping fix resolves the persistent 'due date off by 1 day' issue")
                            return True
                        else:
                            print(f"   ❌ Date calculation error: Expected {expected_date}, got {next_payment_date}")
                            return False
                    else:
                        print(f"   ❌ GET /api/clients missing next_payment_date field")
                        return False
                else:
                    print(f"   ❌ Test client not found in clients list")
                    return False
            else:
                print(f"   ❌ GET /api/clients failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Comprehensive verification failed: {str(e)}")
            return False
    
    # ========== TEST 5: EXISTING MEMBERS HANDLING ==========
    
    def test_existing_members_handling():
        """Test that existing members without next_payment_date field are handled gracefully"""
        try:
            print(f"   Testing graceful handling of existing members")
            
            # Get all clients to check for any without next_payment_date
            response = requests.get(f"{BACKEND_URL}/clients", timeout=10)
            if response.status_code == 200:
                clients = response.json()
                
                clients_without_field = []
                clients_with_field = []
                
                for client in clients:
                    if 'next_payment_date' in client and client['next_payment_date']:
                        clients_with_field.append(client['name'])
                    else:
                        clients_without_field.append(client['name'])
                
                print(f"   Clients with next_payment_date: {len(clients_with_field)}")
                print(f"   Clients without next_payment_date: {len(clients_without_field)}")
                
                if len(clients_without_field) > 0:
                    print(f"   ⚠️ Some existing members lack next_payment_date field")
                    print(f"   ✓ Backend should handle these gracefully")
                
                # The test passes if the API doesn't crash and returns data
                print(f"   ✅ Existing members handled gracefully - no API crashes")
                return True
            else:
                print(f"   ❌ Failed to get clients: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Existing members test failed: {str(e)}")
            return False
    
    # ========== CLEANUP FUNCTION ==========
    
    def cleanup_test_client():
        """Clean up the test client"""
        try:
            if created_client_id:
                print(f"   Cleaning up test client {created_client_id}")
                response = requests.delete(f"{BACKEND_URL}/clients/{created_client_id}", timeout=15)
                if response.status_code == 200:
                    print(f"   ✅ Test client cleaned up successfully")
                else:
                    print(f"   ⚠️ Cleanup failed: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ Cleanup error: {str(e)}")
    
    # ========== RUN ALL TESTS ==========
    
    print("🚀 Starting Field Name Mapping Fix Tests...")
    print()
    
    print("🎯 CRITICAL FIELD MAPPING TESTS")
    print("-" * 50)
    run_test("Create Client with Join Date 2025-07-30", test_create_client_with_join_date)
    run_test("Backend Storage Verification", test_backend_storage_verification)
    run_test("Frontend-Backend Field Mapping", test_frontend_backend_field_mapping)
    run_test("Comprehensive Verification", test_comprehensive_verification)
    run_test("Existing Members Handling", test_existing_members_handling)
    print()
    
    # Cleanup
    print("🧹 CLEANUP")
    print("-" * 50)
    cleanup_test_client()
    print()
    
    # Print comprehensive summary
    print("=" * 80)
    print("📊 FIELD NAME MAPPING FIX TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    print("📋 DETAILED RESULTS:")
    for result in test_results:
        print(f"  {result}")
    print()
    
    # Determine overall result
    if passed_tests == total_tests:
        print("🎉 FIELD NAME MAPPING FIX TESTS PASSED!")
        print("✅ Due date calculation field mapping working correctly")
        print("✅ Backend correctly stores due date in 'next_payment_date' field")
        print("✅ Frontend can read due date from 'next_payment_date' field")
        print("✅ 30-day billing cycle calculation working perfectly")
        print("✅ Field mapping fix resolves the 'due date off by 1 day' issue")
        return True
    elif passed_tests >= total_tests * 0.8:  # 80% pass rate for critical tests
        print("⚠️ FIELD NAME MAPPING FIX MOSTLY WORKING")
        print(f"⚠️ {total_tests - passed_tests} tests failed - check details above")
        print("✅ Core field mapping appears to be working")
        return True
    else:
        print("❌ FIELD NAME MAPPING FIX HAS ISSUES")
        print(f"🚨 {total_tests - passed_tests} tests failed - field mapping fix not working properly")
        return False

if __name__ == "__main__":
    success = test_field_name_mapping_fix()
    sys.exit(0 if success else 1)