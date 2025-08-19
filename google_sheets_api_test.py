#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime, date
import time
import uuid

# Google Sheets API Configuration from review request
SHEETS_API_URL = "https://script.google.com/macros/s/AKfycbzPGvbUq2e-NQwLuVXCc26bM-6pt9iLgsmBWor2gTxi7noC8x7LyztuRU3E8hdH20ON/exec"
API_KEY = "test12345"

def test_google_sheets_api():
    """
    Test Google Sheets API integration for Alphalete Club PWA as requested in review.
    
    Testing Focus (as per review request):
    1. Test direct Google Apps Script Web App connectivity with proper authentication
    2. Test member creation with required fields (name, email, phone, membershipType)
    3. Test member retrieval (list all members)
    4. Test member update operations
    5. Test member deletion
    6. Test payment creation linked to members
    7. Test payment retrieval
    
    Key validation points:
    - Authentication with api_key parameter
    - Proper JSON response format with success/error structure
    - CRUD operations working correctly
    - Error handling for invalid data
    - Cross-origin requests handling
    """
    
    print("🧪 ALPHALETE CLUB PWA - GOOGLE SHEETS API TESTING")
    print("=" * 80)
    print(f"Google Sheets API URL: {SHEETS_API_URL}")
    print(f"API Key: {API_KEY}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    total_tests = 0
    passed_tests = 0
    
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
    
    # ========== SECTION 1: BASIC CONNECTIVITY AND AUTHENTICATION ==========
    
    def test_api_connectivity():
        """Test basic Google Apps Script Web App connectivity"""
        try:
            # Test basic GET request with authentication
            params = {
                'entity': 'members',
                'operation': 'read_all',
                'api_key': API_KEY
            }
            
            response = requests.get(SHEETS_API_URL, params=params, timeout=15)
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response Data: {data}")
                    
                    # Check for proper JSON response format
                    if isinstance(data, dict):
                        if 'success' in data or 'error' in data or 'data' in data:
                            print(f"   ✅ Google Sheets API connectivity working")
                            return True
                        else:
                            print(f"   ❌ Response missing expected structure (success/error/data)")
                            return False
                    else:
                        print(f"   ❌ Response is not a JSON object")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Invalid JSON response: {str(e)}")
                    print(f"   Raw response: {response.text[:500]}")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_authentication():
        """Test API key authentication"""
        try:
            # Test with valid API key
            params = {
                'entity': 'members',
                'operation': 'read_all',
                'api_key': API_KEY
            }
            
            response = requests.get(SHEETS_API_URL, params=params, timeout=15)
            print(f"   Valid API Key - Status Code: {response.status_code}")
            
            if response.status_code == 200:
                valid_auth = True
            else:
                valid_auth = False
            
            # Test with invalid API key
            params_invalid = {
                'entity': 'members',
                'operation': 'read_all',
                'api_key': 'invalid_key_12345'
            }
            
            response_invalid = requests.get(SHEETS_API_URL, params=params_invalid, timeout=15)
            print(f"   Invalid API Key - Status Code: {response_invalid.status_code}")
            
            if valid_auth:
                print(f"   ✅ Authentication working with valid API key")
                return True
            else:
                print(f"   ❌ Authentication failed even with valid API key")
                return False
                
        except Exception as e:
            print(f"   ❌ Authentication test failed: {str(e)}")
            return False
    
    # ========== SECTION 2: MEMBER CRUD OPERATIONS ==========
    
    def test_member_retrieval():
        """Test member retrieval (list all members)"""
        try:
            params = {
                'entity': 'members',
                'operation': 'read_all',
                'api_key': API_KEY
            }
            
            response = requests.get(SHEETS_API_URL, params=params, timeout=15)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response: {data}")
                    
                    # Check response structure
                    if isinstance(data, dict):
                        if 'success' in data and data['success']:
                            members = data.get('data', [])
                            print(f"   ✅ Member retrieval working - Found {len(members)} members")
                            return True
                        elif 'error' in data:
                            print(f"   ❌ API returned error: {data['error']}")
                            return False
                        else:
                            print(f"   ❌ Unexpected response structure")
                            return False
                    else:
                        print(f"   ❌ Response is not a JSON object")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Member retrieval test failed: {str(e)}")
            return False
    
    def test_member_creation():
        """Test member creation with required fields"""
        try:
            # Create test member data
            test_member = {
                "operation": "create",
                "entity": "members",
                "api_key": API_KEY,
                "data": {
                    "name": "Google Sheets Test User",
                    "email": "gstest@example.com",
                    "phone": "+1234567890",
                    "membershipType": "Standard"
                }
            }
            
            response = requests.post(
                SHEETS_API_URL,
                json=test_member,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response: {data}")
                    
                    if isinstance(data, dict):
                        if 'success' in data and data['success']:
                            print(f"   ✅ Member creation working")
                            return True
                        elif 'error' in data:
                            print(f"   ❌ API returned error: {data['error']}")
                            return False
                        else:
                            print(f"   ❌ Unexpected response structure")
                            return False
                    else:
                        print(f"   ❌ Response is not a JSON object")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Member creation test failed: {str(e)}")
            return False
    
    def test_member_update():
        """Test member update operations"""
        try:
            # First, try to get existing members to update
            params = {
                'entity': 'members',
                'operation': 'read_all',
                'api_key': API_KEY
            }
            
            response = requests.get(SHEETS_API_URL, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'success' in data and data['success'] and data.get('data'):
                    # Use first member for update test
                    member_to_update = data['data'][0]
                    member_id = member_to_update.get('id') or member_to_update.get('email')
                    
                    # Update member data
                    update_data = {
                        "operation": "update",
                        "entity": "members",
                        "api_key": API_KEY,
                        "data": {
                            "id": member_id,
                            "phone": "+9876543210",
                            "membershipType": "Premium"
                        }
                    }
                    
                    update_response = requests.post(
                        SHEETS_API_URL,
                        json=update_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=15
                    )
                    
                    print(f"   Update Status Code: {update_response.status_code}")
                    
                    if update_response.status_code == 200:
                        update_result = update_response.json()
                        print(f"   Update Response: {update_result}")
                        
                        if 'success' in update_result and update_result['success']:
                            print(f"   ✅ Member update working")
                            return True
                        else:
                            print(f"   ❌ Member update failed: {update_result.get('error', 'Unknown error')}")
                            return False
                    else:
                        print(f"   ❌ Update HTTP Error: {update_response.status_code}")
                        return False
                else:
                    print(f"   ❌ No members found to update")
                    return False
            else:
                print(f"   ❌ Could not retrieve members for update test")
                return False
                
        except Exception as e:
            print(f"   ❌ Member update test failed: {str(e)}")
            return False
    
    def test_member_deletion():
        """Test member deletion"""
        try:
            # First create a member to delete
            test_member = {
                "operation": "create",
                "entity": "members",
                "api_key": API_KEY,
                "data": {
                    "name": "Delete Test User",
                    "email": "deletetest@example.com",
                    "phone": "+1111111111",
                    "membershipType": "Standard"
                }
            }
            
            create_response = requests.post(
                SHEETS_API_URL,
                json=test_member,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if create_response.status_code == 200:
                create_data = create_response.json()
                if 'success' in create_data and create_data['success']:
                    # Now delete the member
                    delete_data = {
                        "operation": "delete",
                        "entity": "members",
                        "api_key": API_KEY,
                        "data": {
                            "email": "deletetest@example.com"
                        }
                    }
                    
                    delete_response = requests.post(
                        SHEETS_API_URL,
                        json=delete_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=15
                    )
                    
                    print(f"   Delete Status Code: {delete_response.status_code}")
                    
                    if delete_response.status_code == 200:
                        delete_result = delete_response.json()
                        print(f"   Delete Response: {delete_result}")
                        
                        if 'success' in delete_result and delete_result['success']:
                            print(f"   ✅ Member deletion working")
                            return True
                        else:
                            print(f"   ❌ Member deletion failed: {delete_result.get('error', 'Unknown error')}")
                            return False
                    else:
                        print(f"   ❌ Delete HTTP Error: {delete_response.status_code}")
                        return False
                else:
                    print(f"   ❌ Could not create member for deletion test")
                    return False
            else:
                print(f"   ❌ Could not create member for deletion test")
                return False
                
        except Exception as e:
            print(f"   ❌ Member deletion test failed: {str(e)}")
            return False
    
    # ========== SECTION 3: PAYMENT OPERATIONS ==========
    
    def test_payment_creation():
        """Test payment creation linked to members"""
        try:
            # Create payment data
            test_payment = {
                "operation": "create",
                "entity": "payments",
                "api_key": API_KEY,
                "data": {
                    "memberEmail": "gstest@example.com",
                    "amount": 50.00,
                    "paymentDate": datetime.now().strftime("%Y-%m-%d"),
                    "paymentMethod": "Cash",
                    "notes": "Google Sheets API Test Payment"
                }
            }
            
            response = requests.post(
                SHEETS_API_URL,
                json=test_payment,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response: {data}")
                    
                    if isinstance(data, dict):
                        if 'success' in data and data['success']:
                            print(f"   ✅ Payment creation working")
                            return True
                        elif 'error' in data:
                            print(f"   ❌ API returned error: {data['error']}")
                            return False
                        else:
                            print(f"   ❌ Unexpected response structure")
                            return False
                    else:
                        print(f"   ❌ Response is not a JSON object")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Payment creation test failed: {str(e)}")
            return False
    
    def test_payment_retrieval():
        """Test payment retrieval"""
        try:
            params = {
                'entity': 'payments',
                'operation': 'read_all',
                'api_key': API_KEY
            }
            
            response = requests.get(SHEETS_API_URL, params=params, timeout=15)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response: {data}")
                    
                    # Check response structure
                    if isinstance(data, dict):
                        if 'success' in data and data['success']:
                            payments = data.get('data', [])
                            print(f"   ✅ Payment retrieval working - Found {len(payments)} payments")
                            return True
                        elif 'error' in data:
                            print(f"   ❌ API returned error: {data['error']}")
                            return False
                        else:
                            print(f"   ❌ Unexpected response structure")
                            return False
                    else:
                        print(f"   ❌ Response is not a JSON object")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Invalid JSON response: {str(e)}")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Payment retrieval test failed: {str(e)}")
            return False
    
    # ========== RUN ALL TESTS ==========
    
    print("🚀 STARTING GOOGLE SHEETS API TESTS")
    print("=" * 50)
    
    # Section 1: Basic Connectivity and Authentication
    print("\n📡 SECTION 1: CONNECTIVITY AND AUTHENTICATION")
    print("-" * 50)
    run_test("Google Apps Script Web App Connectivity", test_api_connectivity)
    run_test("API Key Authentication", test_authentication)
    
    # Section 2: Member CRUD Operations
    print("\n👥 SECTION 2: MEMBER CRUD OPERATIONS")
    print("-" * 50)
    run_test("Member Retrieval (List All)", test_member_retrieval)
    run_test("Member Creation", test_member_creation)
    run_test("Member Update", test_member_update)
    run_test("Member Deletion", test_member_deletion)
    
    # Section 3: Payment Operations
    print("\n💰 SECTION 3: PAYMENT OPERATIONS")
    print("-" * 50)
    run_test("Payment Creation", test_payment_creation)
    run_test("Payment Retrieval", test_payment_retrieval)
    
    # ========== FINAL RESULTS ==========
    
    print("\n" + "=" * 80)
    print("🏁 GOOGLE SHEETS API TEST RESULTS")
    print("=" * 80)
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 SUMMARY:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print()
    
    print("📋 DETAILED RESULTS:")
    for result in test_results:
        print(f"   {result}")
    
    print()
    print(f"🕒 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_rate >= 80:
        print("🎉 GOOGLE SHEETS API INTEGRATION: WORKING WELL")
        return True
    elif success_rate >= 50:
        print("⚠️  GOOGLE SHEETS API INTEGRATION: PARTIALLY WORKING")
        return False
    else:
        print("🚨 GOOGLE SHEETS API INTEGRATION: MAJOR ISSUES DETECTED")
        return False

if __name__ == "__main__":
    try:
        success = test_google_sheets_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)