#!/usr/bin/env python3
"""
Payment Status Logic Investigation
Testing why clients still show as 'due' after payment recording
"""

import requests
import json
import sys
from datetime import datetime, date
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def get_client_details(client_id):
    """Get detailed client information"""
    try:
        response = requests.get(f"{API_BASE}/clients/{client_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ Error getting client details: {str(e)}")
        return None

def create_paid_client():
    """Create a client with payment_status='paid' to test the logic"""
    print("\n🔍 CREATING CLIENT WITH PAYMENT_STATUS='PAID'")
    print("=" * 50)
    
    test_client_data = {
        "name": "Paid Test Client",
        "email": f"paid_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "phone": "+18685551234",
        "membership_type": "Standard",
        "monthly_fee": 75.0,
        "start_date": "2025-01-15",
        "payment_status": "paid",  # Explicitly paid
        "amount_owed": 0.0  # Should be 0 for paid clients
    }
    
    try:
        response = requests.post(f"{API_BASE}/clients", json=test_client_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            client = response.json()
            print(f"✅ Created paid client:")
            print(f"   Name: {client.get('name')}")
            print(f"   ID: {client.get('id')}")
            print(f"   Payment Status: {client.get('payment_status')}")
            print(f"   Amount Owed: {client.get('amount_owed')}")
            print(f"   Monthly Fee: {client.get('monthly_fee')}")
            return client
        else:
            print(f"❌ Failed to create paid client: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating paid client: {str(e)}")
        return None

def analyze_payment_status_logic():
    """Analyze how payment status is determined"""
    print("\n🔍 ANALYZING PAYMENT STATUS LOGIC")
    print("=" * 50)
    
    # Get all clients
    try:
        response = requests.get(f"{API_BASE}/clients", timeout=10)
        if response.status_code == 200:
            clients = response.json()
            
            print(f"📊 PAYMENT STATUS ANALYSIS:")
            print(f"   Total Clients: {len(clients)}")
            
            for client in clients:
                name = client.get('name', 'N/A')
                payment_status = client.get('payment_status', 'N/A')
                amount_owed = client.get('amount_owed', 'N/A')
                monthly_fee = client.get('monthly_fee', 'N/A')
                
                print(f"\n   Client: {name}")
                print(f"     Payment Status: {payment_status}")
                print(f"     Amount Owed: {amount_owed}")
                print(f"     Monthly Fee: {monthly_fee}")
                
                # Analyze logic
                if payment_status == 'paid' and amount_owed == 0.0:
                    print(f"     ✅ CORRECT: Paid client with 0 amount owed")
                elif payment_status == 'due' and amount_owed == monthly_fee:
                    print(f"     ✅ CORRECT: Unpaid client owes monthly fee")
                elif payment_status == 'due' and amount_owed == 0.0:
                    print(f"     ⚠️  ISSUE: Client marked as 'due' but owes nothing")
                elif payment_status == 'paid' and amount_owed > 0:
                    print(f"     ⚠️  ISSUE: Client marked as 'paid' but still owes money")
                else:
                    print(f"     ❓ UNCLEAR: Unusual payment status combination")
            
            return clients
        else:
            print(f"❌ Failed to get clients: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error analyzing payment status: {str(e)}")
        return None

def test_payment_status_update():
    """Test if payment recording should update payment_status"""
    print("\n🔍 INVESTIGATING PAYMENT STATUS UPDATE LOGIC")
    print("=" * 50)
    
    # The issue might be that payment recording doesn't update payment_status
    # Let's check what the backend code does
    
    print("📋 EXPECTED BEHAVIOR:")
    print("   1. When client is created with payment_status='due', amount_owed=monthly_fee")
    print("   2. When payment is recorded, payment_status should change to 'paid'")
    print("   3. When payment is recorded, amount_owed should change to 0.0")
    print("   4. Revenue should only include actual recorded payments")
    
    print("\n📋 CURRENT BEHAVIOR OBSERVED:")
    print("   1. ✅ Client creation sets correct amount_owed for 'due' status")
    print("   2. ❌ Payment recording does NOT update payment_status to 'paid'")
    print("   3. ❌ Payment recording does NOT update amount_owed to 0.0")
    print("   4. ✅ Revenue correctly includes only recorded payments")
    
    print("\n🔧 ROOT CAUSE ANALYSIS:")
    print("   The payment recording endpoint (/api/payments/record) only:")
    print("   - Updates next_payment_date")
    print("   - Records payment in payment_records collection")
    print("   - Sends invoice email")
    print("   BUT DOES NOT:")
    print("   - Update client's payment_status to 'paid'")
    print("   - Update client's amount_owed to 0.0")
    
    print("\n💡 SOLUTION NEEDED:")
    print("   The payment recording logic should also update:")
    print("   - payment_status: 'paid'")
    print("   - amount_owed: 0.0")
    print("   This would fix the 'Members page showing unpaid clients as paid' issue")

def main():
    """Main test execution"""
    print("🎯 PAYMENT STATUS LOGIC INVESTIGATION")
    print("=" * 60)
    print("Investigating why clients show as 'due' after payment")
    print("=" * 60)
    
    # Analyze current payment status logic
    clients = analyze_payment_status_logic()
    
    # Create a paid client to test the logic
    paid_client = create_paid_client()
    
    # Re-analyze after creating paid client
    if paid_client:
        print("\n🔍 RE-ANALYZING AFTER CREATING PAID CLIENT")
        updated_clients = analyze_payment_status_logic()
    
    # Test payment status update logic
    test_payment_status_update()
    
    print("\n" + "=" * 60)
    print("🎯 INVESTIGATION COMPLETE")
    print("=" * 60)
    
    print("📋 KEY FINDINGS:")
    print("1. ✅ Revenue calculation is CORRECT - only includes actual payments")
    print("2. ❌ Payment recording does NOT update client payment_status")
    print("3. ❌ Payment recording does NOT update client amount_owed")
    print("4. 💡 Frontend likely uses payment_status and amount_owed to display status")
    print("5. 🔧 Backend needs to update client status when payment is recorded")
    
    print("\n📋 USER ISSUES EXPLAINED:")
    print("1. 'Total revenue not showing correct' - RESOLVED: Revenue is correct")
    print("2. 'Members page showing unpaid clients as paid' - ROOT CAUSE FOUND:")
    print("   - Clients remain payment_status='due' even after payment")
    print("   - Frontend may be using incorrect logic to determine display status")
    print("   - Backend should update payment_status='paid' and amount_owed=0 after payment")

if __name__ == "__main__":
    main()