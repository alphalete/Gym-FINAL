#!/usr/bin/env python3
"""
IMMEDIATE PAYMENT ON JOIN DATE TEST
===================================

Testing the specific scenario where a client joins and pays immediately on the same day.

SCENARIO:
1. Client joins Jan 15 → due date is Feb 15 ✅
2. Client makes January payment on Jan 15 (same day they join) → due date should STILL be Feb 15 ✅

EXPECTED BEHAVIOR:
- Join Jan 15 → Due Feb 15
- Pay Jan 15 (for January service) → Still due Feb 15 (for February service)
- The immediate payment covers the current month, not the next month
"""

import requests
import json
from datetime import datetime, date
import sys
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_immediate_payment_scenario():
    """Test the exact scenario: join Jan 15, pay Jan 15, should still be due Feb 15"""
    
    print("🎯 TESTING IMMEDIATE PAYMENT ON JOIN DATE SCENARIO")
    print("=" * 60)
    
    # Step 1: Create client with start_date "2025-01-15" and payment_status="due"
    print("\n📝 Step 1: Creating client with start_date 2025-01-15...")
    
    client_data = {
        "name": "Immediate Payment Test Client",
        "email": "immediate_test_client@example.com",
        "phone": "+18685551234",
        "membership_type": "Standard",
        "monthly_fee": 55.0,
        "start_date": "2025-01-15",
        "payment_status": "due",
        "auto_reminders_enabled": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/clients", json=client_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ FAILED to create client: {response.status_code} - {response.text}")
            return False
        
        client = response.json()
        client_id = client['id']
        print(f"✅ Client created successfully: {client['name']}")
        print(f"   Start Date: {client['start_date']}")
        print(f"   Next Payment Date: {client['next_payment_date']}")
        
        # Step 2: Verify next_payment_date is correctly set to "2025-02-15"
        print(f"\n🔍 Step 2: Verifying initial next_payment_date...")
        expected_due_date = "2025-02-15"
        actual_due_date = client['next_payment_date']
        
        if actual_due_date == expected_due_date:
            print(f"✅ CORRECT: Next payment date is {actual_due_date} (expected {expected_due_date})")
        else:
            print(f"❌ INCORRECT: Next payment date is {actual_due_date} (expected {expected_due_date})")
            return False
        
        # Step 3: Record a payment with payment_date "2025-01-15" (same day they joined)
        print(f"\n💰 Step 3: Recording payment on join date (2025-01-15)...")
        
        payment_data = {
            "client_id": client_id,
            "amount_paid": 55.0,
            "payment_date": "2025-01-15",  # Same day as join date
            "payment_method": "Cash",
            "notes": "Immediate payment on join date - testing scenario"
        }
        
        payment_response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
        if payment_response.status_code != 200:
            print(f"❌ FAILED to record payment: {payment_response.status_code} - {payment_response.text}")
            return False
        
        payment_result = payment_response.json()
        print(f"✅ Payment recorded successfully")
        print(f"   Amount Paid: TTD {payment_result['amount_paid']}")
        print(f"   New Next Payment Date: {payment_result['new_next_payment_date']}")
        
        # Step 4: Check if the next_payment_date incorrectly advances to "2025-03-15" (wrong) instead of staying "2025-02-15" (correct)
        print(f"\n🎯 Step 4: CRITICAL TEST - Checking if due date advanced incorrectly...")
        
        # Get updated client data
        client_response = requests.get(f"{API_BASE}/clients/{client_id}", timeout=10)
        if client_response.status_code != 200:
            print(f"❌ FAILED to get updated client: {client_response.status_code}")
            return False
        
        updated_client = client_response.json()
        final_due_date = updated_client['next_payment_date']
        
        print(f"\n📊 SCENARIO ANALYSIS:")
        print(f"   Join Date: 2025-01-15")
        print(f"   Initial Due Date: {actual_due_date}")
        print(f"   Payment Date: 2025-01-15 (same day as join)")
        print(f"   Final Due Date: {final_due_date}")
        
        # EXPECTED BEHAVIOR: Due date should STILL be Feb 15 (or advance to Mar 15)
        # The question is: does immediate payment cover current month or next month?
        
        if final_due_date == "2025-02-15":
            print(f"\n✅ SCENARIO 1 RESULT: Due date stayed at Feb 15")
            print(f"   This means: Immediate payment covered January service")
            print(f"   Client still owes for February service (due Feb 15)")
            print(f"   ✅ This matches the user's expected behavior!")
            return True
            
        elif final_due_date == "2025-03-15":
            print(f"\n❌ SCENARIO 2 RESULT: Due date advanced to Mar 15")
            print(f"   This means: Immediate payment covered February service")
            print(f"   Client doesn't owe anything until March 15")
            print(f"   ❌ This does NOT match the user's expected behavior!")
            print(f"\n🚨 ISSUE IDENTIFIED: Payment logic advances due date even for immediate payments")
            print(f"   The system treats immediate payment as covering the NEXT month instead of current month")
            return False
            
        else:
            print(f"\n❓ UNEXPECTED RESULT: Due date is {final_due_date}")
            print(f"   This is neither Feb 15 nor Mar 15 - unexpected behavior")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False
    finally:
        # Cleanup: Delete test client
        try:
            if 'client_id' in locals():
                requests.delete(f"{API_BASE}/clients/{client_id}", timeout=5)
                print(f"\n🧹 Cleanup: Test client deleted")
        except:
            pass

def main():
    """Run the immediate payment test"""
    print("🎯 IMMEDIATE PAYMENT ON JOIN DATE TEST")
    print("Testing user's clarified scenario about immediate payments")
    print(f"Backend URL: {API_BASE}")
    
    success = test_immediate_payment_scenario()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ TEST PASSED: Immediate payment behavior is correct")
        print("   Payment on join date covers current month, still due next month")
    else:
        print("❌ TEST FAILED: Immediate payment behavior is incorrect")
        print("   Payment on join date incorrectly advances due date")
    
    print(f"{'='*60}")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)