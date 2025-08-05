#!/usr/bin/env python3
"""
Detailed debugging test for amount_owed field issue
"""

import requests
import json
from datetime import date, datetime
import sys

# Get backend URL from environment
BACKEND_URL = "https://442a58e4-b64f-4824-924a-0c12436c79ea.preview.emergentagent.com/api"

def debug_amount_owed_issue():
    """Debug the amount_owed field issue in detail"""
    print("🔍 DEBUGGING AMOUNT OWED FIELD ISSUE")
    print("=" * 60)
    
    # Test 1: Create unpaid client and examine response in detail
    print("\n📋 TEST 1: Create unpaid client with payment_status='due'")
    unpaid_client_data = {
        "name": "Debug Unpaid Client",
        "email": "debug_unpaid@example.com",
        "phone": "+18685551111",
        "membership_type": "Standard",
        "monthly_fee": 55.0,
        "start_date": "2025-01-15",
        "payment_status": "due",
        "auto_reminders_enabled": True
    }
    
    print(f"Request data: {json.dumps(unpaid_client_data, indent=2)}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/clients", json=unpaid_client_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 201]:
            client_data = response.json()
            print(f"\n🔍 ANALYSIS:")
            print(f"  - payment_status: {client_data.get('payment_status')}")
            print(f"  - monthly_fee: {client_data.get('monthly_fee')}")
            print(f"  - amount_owed: {client_data.get('amount_owed')}")
            print(f"  - amount_owed type: {type(client_data.get('amount_owed'))}")
            
            if client_data.get('amount_owed') is None:
                print("  ❌ ISSUE: amount_owed is None instead of monthly_fee")
            elif client_data.get('amount_owed') == client_data.get('monthly_fee'):
                print("  ✅ CORRECT: amount_owed equals monthly_fee")
            else:
                print(f"  ❌ ISSUE: amount_owed ({client_data.get('amount_owed')}) != monthly_fee ({client_data.get('monthly_fee')})")
            
            unpaid_client_id = client_data['id']
        else:
            print(f"❌ Failed to create unpaid client")
            unpaid_client_id = None
            
    except Exception as e:
        print(f"❌ Exception creating unpaid client: {str(e)}")
        unpaid_client_id = None
    
    # Test 2: Create paid client and examine response
    print("\n📋 TEST 2: Create paid client with payment_status='paid'")
    paid_client_data = {
        "name": "Debug Paid Client",
        "email": "debug_paid@example.com", 
        "phone": "+18685552222",
        "membership_type": "Premium",
        "monthly_fee": 75.0,
        "start_date": "2025-01-15",
        "payment_status": "paid",
        "auto_reminders_enabled": True
    }
    
    print(f"Request data: {json.dumps(paid_client_data, indent=2)}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/clients", json=paid_client_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 201]:
            client_data = response.json()
            print(f"\n🔍 ANALYSIS:")
            print(f"  - payment_status: {client_data.get('payment_status')}")
            print(f"  - monthly_fee: {client_data.get('monthly_fee')}")
            print(f"  - amount_owed: {client_data.get('amount_owed')}")
            print(f"  - amount_owed type: {type(client_data.get('amount_owed'))}")
            
            if client_data.get('amount_owed') == 0.0:
                print("  ✅ CORRECT: amount_owed is 0.0 for paid client")
            else:
                print(f"  ❌ ISSUE: amount_owed should be 0.0 for paid client, got {client_data.get('amount_owed')}")
            
            paid_client_id = client_data['id']
        else:
            print(f"❌ Failed to create paid client")
            paid_client_id = None
            
    except Exception as e:
        print(f"❌ Exception creating paid client: {str(e)}")
        paid_client_id = None
    
    # Test 3: Test with explicit amount_owed in request
    print("\n📋 TEST 3: Create unpaid client with explicit amount_owed=None")
    explicit_client_data = {
        "name": "Debug Explicit Client",
        "email": "debug_explicit@example.com",
        "phone": "+18685553333",
        "membership_type": "Elite",
        "monthly_fee": 100.0,
        "start_date": "2025-01-15",
        "payment_status": "due",
        "amount_owed": None,  # Explicitly set to None
        "auto_reminders_enabled": True
    }
    
    print(f"Request data: {json.dumps(explicit_client_data, indent=2, default=str)}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/clients", json=explicit_client_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 201]:
            client_data = response.json()
            print(f"\n🔍 ANALYSIS:")
            print(f"  - payment_status: {client_data.get('payment_status')}")
            print(f"  - monthly_fee: {client_data.get('monthly_fee')}")
            print(f"  - amount_owed: {client_data.get('amount_owed')}")
            print(f"  - amount_owed type: {type(client_data.get('amount_owed'))}")
            
            explicit_client_id = client_data['id']
        else:
            print(f"❌ Failed to create explicit client")
            explicit_client_id = None
            
    except Exception as e:
        print(f"❌ Exception creating explicit client: {str(e)}")
        explicit_client_id = None
    
    # Cleanup
    print("\n🧹 CLEANUP: Deleting test clients")
    for client_id, client_name in [(unpaid_client_id, "unpaid"), (paid_client_id, "paid"), (explicit_client_id, "explicit")]:
        if client_id:
            try:
                response = requests.delete(f"{BACKEND_URL}/clients/{client_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted {client_name} test client")
                else:
                    print(f"⚠️ Failed to delete {client_name} test client: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Exception deleting {client_name} test client: {str(e)}")

def main():
    """Main debug execution"""
    print("🚀 DEBUGGING: Amount Owed Field Issue")
    print("Investigating why amount_owed is None instead of monthly_fee for unpaid clients")
    print("=" * 80)
    
    debug_amount_owed_issue()
    
    print("\n" + "=" * 60)
    print("🔍 CONCLUSION")
    print("=" * 60)
    print("The issue appears to be that the Pydantic model is overriding")
    print("the amount_owed value set in the business logic.")
    print("The fix may need to be applied differently.")

if __name__ == "__main__":
    main()