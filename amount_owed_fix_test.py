#!/usr/bin/env python3
"""
Backend Testing Script for Amount Owed Field Default Fix - With Unique Emails
Testing the fix where amount_owed field default was changed from 0.0 to None
"""

import requests
import json
from datetime import date, datetime
import sys
import os
import uuid

# Get backend URL from environment
BACKEND_URL = "https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com/api"

def test_amount_owed_field_fix():
    """Test the amount_owed field default fix with unique emails"""
    print("🎯 TESTING AMOUNT OWED FIELD DEFAULT FIX")
    print("=" * 60)
    
    test_results = []
    unique_id = str(uuid.uuid4())[:8]  # Short unique identifier
    
    # Test 1: Create unpaid client (payment_status="due")
    print("\n📋 TEST 1: Create unpaid client with payment_status='due'")
    unpaid_client_data = {
        "name": "Test Unpaid Client",
        "email": f"unpaid_test_{unique_id}@example.com",
        "phone": "+18685551111",
        "membership_type": "Standard",
        "monthly_fee": 55.0,
        "start_date": "2025-01-15",
        "payment_status": "due",
        "auto_reminders_enabled": True
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/clients", json=unpaid_client_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            client_data = response.json()
            print(f"✅ Client created successfully")
            print(f"Client ID: {client_data['id']}")
            print(f"Name: {client_data['name']}")
            print(f"Payment Status: {client_data['payment_status']}")
            print(f"Monthly Fee: {client_data['monthly_fee']}")
            print(f"Amount Owed: {client_data['amount_owed']}")
            
            # Verify amount_owed equals monthly_fee for unpaid client
            if client_data['amount_owed'] == client_data['monthly_fee']:
                print(f"✅ CORRECT: amount_owed ({client_data['amount_owed']}) equals monthly_fee ({client_data['monthly_fee']})")
                test_results.append(("Unpaid client amount_owed", True, f"amount_owed={client_data['amount_owed']}, monthly_fee={client_data['monthly_fee']}"))
            else:
                print(f"❌ ERROR: amount_owed ({client_data['amount_owed']}) should equal monthly_fee ({client_data['monthly_fee']})")
                test_results.append(("Unpaid client amount_owed", False, f"amount_owed={client_data['amount_owed']}, expected={client_data['monthly_fee']}"))
            
            unpaid_client_id = client_data['id']
        else:
            print(f"❌ Failed to create unpaid client: {response.text}")
            test_results.append(("Unpaid client creation", False, f"Status: {response.status_code}"))
            unpaid_client_id = None
            
    except Exception as e:
        print(f"❌ Exception creating unpaid client: {str(e)}")
        test_results.append(("Unpaid client creation", False, f"Exception: {str(e)}"))
        unpaid_client_id = None
    
    # Test 2: Create paid client (payment_status="paid")
    print("\n📋 TEST 2: Create paid client with payment_status='paid'")
    paid_client_data = {
        "name": "Test Paid Client",
        "email": f"paid_test_{unique_id}@example.com", 
        "phone": "+18685552222",
        "membership_type": "Premium",
        "monthly_fee": 75.0,
        "start_date": "2025-01-15",
        "payment_status": "paid",
        "auto_reminders_enabled": True
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/clients", json=paid_client_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            client_data = response.json()
            print(f"✅ Client created successfully")
            print(f"Client ID: {client_data['id']}")
            print(f"Name: {client_data['name']}")
            print(f"Payment Status: {client_data['payment_status']}")
            print(f"Monthly Fee: {client_data['monthly_fee']}")
            print(f"Amount Owed: {client_data['amount_owed']}")
            
            # Verify amount_owed equals 0.0 for paid client
            if client_data['amount_owed'] == 0.0:
                print(f"✅ CORRECT: amount_owed ({client_data['amount_owed']}) equals 0.0 for paid client")
                test_results.append(("Paid client amount_owed", True, f"amount_owed={client_data['amount_owed']}"))
            else:
                print(f"❌ ERROR: amount_owed ({client_data['amount_owed']}) should equal 0.0 for paid client")
                test_results.append(("Paid client amount_owed", False, f"amount_owed={client_data['amount_owed']}, expected=0.0"))
            
            paid_client_id = client_data['id']
        else:
            print(f"❌ Failed to create paid client: {response.text}")
            test_results.append(("Paid client creation", False, f"Status: {response.status_code}"))
            paid_client_id = None
            
    except Exception as e:
        print(f"❌ Exception creating paid client: {str(e)}")
        test_results.append(("Paid client creation", False, f"Exception: {str(e)}"))
        paid_client_id = None
    
    # Test 3: Test default behavior (no payment_status specified)
    print("\n📋 TEST 3: Create client without specifying payment_status (should default to 'due')")
    default_client_data = {
        "name": "Test Default Client",
        "email": f"default_test_{unique_id}@example.com",
        "phone": "+18685553333",
        "membership_type": "Elite",
        "monthly_fee": 100.0,
        "start_date": "2025-01-15",
        "auto_reminders_enabled": True
        # Note: payment_status not specified, should default to 'due'
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/clients", json=default_client_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            client_data = response.json()
            print(f"✅ Client created successfully")
            print(f"Client ID: {client_data['id']}")
            print(f"Name: {client_data['name']}")
            print(f"Payment Status: {client_data['payment_status']}")
            print(f"Monthly Fee: {client_data['monthly_fee']}")
            print(f"Amount Owed: {client_data['amount_owed']}")
            
            # Verify payment_status defaults to 'due' and amount_owed equals monthly_fee
            if client_data['payment_status'] == 'due' and client_data['amount_owed'] == client_data['monthly_fee']:
                print(f"✅ CORRECT: Default payment_status='due' and amount_owed ({client_data['amount_owed']}) equals monthly_fee ({client_data['monthly_fee']})")
                test_results.append(("Default client behavior", True, f"payment_status={client_data['payment_status']}, amount_owed={client_data['amount_owed']}"))
            else:
                print(f"❌ ERROR: Expected payment_status='due' and amount_owed=monthly_fee, got payment_status='{client_data['payment_status']}', amount_owed={client_data['amount_owed']}")
                test_results.append(("Default client behavior", False, f"payment_status={client_data['payment_status']}, amount_owed={client_data['amount_owed']}"))
            
            default_client_id = client_data['id']
        else:
            print(f"❌ Failed to create default client: {response.text}")
            test_results.append(("Default client creation", False, f"Status: {response.status_code}"))
            default_client_id = None
            
    except Exception as e:
        print(f"❌ Exception creating default client: {str(e)}")
        test_results.append(("Default client creation", False, f"Exception: {str(e)}"))
        default_client_id = None
    
    # Test 4: Test with explicit amount_owed value (should be preserved)
    print("\n📋 TEST 4: Create client with explicit amount_owed value")
    explicit_client_data = {
        "name": "Test Explicit Client",
        "email": f"explicit_test_{unique_id}@example.com",
        "phone": "+18685554444",
        "membership_type": "VIP",
        "monthly_fee": 150.0,
        "start_date": "2025-01-15",
        "payment_status": "due",
        "amount_owed": 200.0,  # Explicit custom amount
        "auto_reminders_enabled": True
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/clients", json=explicit_client_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            client_data = response.json()
            print(f"✅ Client created successfully")
            print(f"Client ID: {client_data['id']}")
            print(f"Name: {client_data['name']}")
            print(f"Payment Status: {client_data['payment_status']}")
            print(f"Monthly Fee: {client_data['monthly_fee']}")
            print(f"Amount Owed: {client_data['amount_owed']}")
            
            # Verify explicit amount_owed is preserved
            if client_data['amount_owed'] == 200.0:
                print(f"✅ CORRECT: Explicit amount_owed ({client_data['amount_owed']}) is preserved")
                test_results.append(("Explicit amount_owed preservation", True, f"amount_owed={client_data['amount_owed']}"))
            else:
                print(f"❌ ERROR: Explicit amount_owed should be 200.0, got {client_data['amount_owed']}")
                test_results.append(("Explicit amount_owed preservation", False, f"amount_owed={client_data['amount_owed']}, expected=200.0"))
            
            explicit_client_id = client_data['id']
        else:
            print(f"❌ Failed to create explicit client: {response.text}")
            test_results.append(("Explicit client creation", False, f"Status: {response.status_code}"))
            explicit_client_id = None
            
    except Exception as e:
        print(f"❌ Exception creating explicit client: {str(e)}")
        test_results.append(("Explicit client creation", False, f"Exception: {str(e)}"))
        explicit_client_id = None
    
    # Cleanup: Delete test clients
    print("\n🧹 CLEANUP: Deleting test clients")
    for client_id, client_name in [(unpaid_client_id, "unpaid"), (paid_client_id, "paid"), (default_client_id, "default"), (explicit_client_id, "explicit")]:
        if client_id:
            try:
                response = requests.delete(f"{BACKEND_URL}/clients/{client_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted {client_name} test client")
                else:
                    print(f"⚠️ Failed to delete {client_name} test client: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Exception deleting {client_name} test client: {str(e)}")
    
    return test_results

def main():
    """Main test execution"""
    print("🚀 BACKEND TESTING: Amount Owed Field Default Fix")
    print("Testing the fix where amount_owed field default was changed from 0.0 to None")
    print("This should allow proper logic to set amount_owed = monthly_fee for unpaid clients")
    print("=" * 80)
    
    # Test the amount_owed field fix
    test_results = test_amount_owed_field_fix()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed, details in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            print(f"    Details: {details}")
        if passed:
            passed_tests += 1
    
    print(f"\n📈 RESULTS: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests*100):.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! The amount_owed field default fix is working correctly.")
        return True
    else:
        print("⚠️ SOME TESTS FAILED! The amount_owed field default fix needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)