#!/usr/bin/env python3
"""
Revenue Calculation and Payment Status Investigation Test
Testing user-reported issues:
1. "Total revenue not showing correct"
2. "Members page showing unpaid clients as paid"
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

def test_payment_stats_endpoint():
    """Test the /api/payments/stats endpoint to check revenue calculation"""
    print("\n🔍 TESTING PAYMENT STATS ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/payments/stats", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Payment Stats Response:")
            print(f"   Total Revenue: TTD {data.get('total_revenue', 'N/A')}")
            print(f"   Monthly Revenue: TTD {data.get('monthly_revenue', 'N/A')}")
            print(f"   Payment Count: {data.get('payment_count', 'N/A')}")
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            return data
        else:
            print(f"❌ Failed to get payment stats: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing payment stats: {str(e)}")
        return None

def test_clients_endpoint():
    """Test the /api/clients endpoint to check payment status data"""
    print("\n🔍 TESTING CLIENTS ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/clients", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            clients = response.json()
            print(f"✅ Found {len(clients)} clients")
            
            # Analyze payment status data
            paid_clients = []
            unpaid_clients = []
            
            for client in clients:
                client_id = client.get('id', 'N/A')
                name = client.get('name', 'N/A')
                payment_status = client.get('payment_status', 'N/A')
                amount_owed = client.get('amount_owed', 'N/A')
                monthly_fee = client.get('monthly_fee', 'N/A')
                
                print(f"\n   Client: {name}")
                print(f"   ID: {client_id}")
                print(f"   Payment Status: {payment_status}")
                print(f"   Amount Owed: {amount_owed}")
                print(f"   Monthly Fee: {monthly_fee}")
                
                if payment_status == 'paid':
                    paid_clients.append({
                        'name': name,
                        'id': client_id,
                        'amount_owed': amount_owed,
                        'monthly_fee': monthly_fee
                    })
                elif payment_status == 'due':
                    unpaid_clients.append({
                        'name': name,
                        'id': client_id,
                        'amount_owed': amount_owed,
                        'monthly_fee': monthly_fee
                    })
            
            print(f"\n📊 PAYMENT STATUS SUMMARY:")
            print(f"   Paid Clients: {len(paid_clients)}")
            print(f"   Unpaid Clients: {len(unpaid_clients)}")
            
            return {
                'total_clients': len(clients),
                'paid_clients': paid_clients,
                'unpaid_clients': unpaid_clients,
                'all_clients': clients
            }
            
        else:
            print(f"❌ Failed to get clients: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing clients endpoint: {str(e)}")
        return None

def create_test_unpaid_client():
    """Create a test unpaid client to verify payment status logic"""
    print("\n🔍 CREATING TEST UNPAID CLIENT")
    print("=" * 50)
    
    test_client_data = {
        "name": "Revenue Test Client",
        "email": f"revenue_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "phone": "+18685551234",
        "membership_type": "Standard",
        "monthly_fee": 55.0,
        "start_date": "2025-01-15",
        "payment_status": "due",  # Explicitly unpaid
        "amount_owed": None  # Should default to monthly_fee
    }
    
    try:
        response = requests.post(f"{API_BASE}/clients", json=test_client_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            client = response.json()
            print(f"✅ Created test client:")
            print(f"   Name: {client.get('name')}")
            print(f"   ID: {client.get('id')}")
            print(f"   Payment Status: {client.get('payment_status')}")
            print(f"   Amount Owed: {client.get('amount_owed')}")
            print(f"   Monthly Fee: {client.get('monthly_fee')}")
            return client
        else:
            print(f"❌ Failed to create test client: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test client: {str(e)}")
        return None

def analyze_revenue_vs_unpaid_clients(payment_stats, clients_data):
    """Analyze if revenue calculation includes unpaid clients incorrectly"""
    print("\n🔍 ANALYZING REVENUE VS UNPAID CLIENTS")
    print("=" * 50)
    
    if not payment_stats or not clients_data:
        print("❌ Missing data for analysis")
        return
    
    total_revenue = payment_stats.get('total_revenue', 0)
    payment_count = payment_stats.get('payment_count', 0)
    unpaid_clients = clients_data.get('unpaid_clients', [])
    
    print(f"📊 REVENUE ANALYSIS:")
    print(f"   Total Revenue from API: TTD {total_revenue}")
    print(f"   Payment Count: {payment_count}")
    print(f"   Number of Unpaid Clients: {len(unpaid_clients)}")
    
    # Calculate potential revenue if unpaid clients were included
    potential_unpaid_revenue = sum(client.get('monthly_fee', 0) for client in unpaid_clients)
    print(f"   Potential Revenue from Unpaid Clients: TTD {potential_unpaid_revenue}")
    
    # Check if unpaid clients have correct amount_owed
    print(f"\n🔍 UNPAID CLIENT ANALYSIS:")
    for client in unpaid_clients:
        name = client.get('name', 'N/A')
        amount_owed = client.get('amount_owed', 'N/A')
        monthly_fee = client.get('monthly_fee', 'N/A')
        
        print(f"   {name}:")
        print(f"     Amount Owed: {amount_owed}")
        print(f"     Monthly Fee: {monthly_fee}")
        
        if amount_owed != monthly_fee:
            print(f"     ⚠️  ISSUE: Amount owed ({amount_owed}) != Monthly fee ({monthly_fee})")
        else:
            print(f"     ✅ Correct: Amount owed matches monthly fee")

def test_individual_client_endpoint(client_id):
    """Test individual client endpoint to verify payment status"""
    print(f"\n🔍 TESTING INDIVIDUAL CLIENT ENDPOINT: {client_id}")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/clients/{client_id}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            client = response.json()
            print(f"✅ Client Details:")
            print(f"   Name: {client.get('name')}")
            print(f"   Payment Status: {client.get('payment_status')}")
            print(f"   Amount Owed: {client.get('amount_owed')}")
            print(f"   Monthly Fee: {client.get('monthly_fee')}")
            return client
        else:
            print(f"❌ Failed to get client: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing individual client: {str(e)}")
        return None

def main():
    """Main test execution"""
    print("🎯 REVENUE CALCULATION AND PAYMENT STATUS INVESTIGATION")
    print("=" * 60)
    print("Testing user-reported issues:")
    print("1. 'Total revenue not showing correct'")
    print("2. 'Members page showing unpaid clients as paid'")
    print("=" * 60)
    
    # Test 1: Check payment stats endpoint
    payment_stats = test_payment_stats_endpoint()
    
    # Test 2: Check clients endpoint
    clients_data = test_clients_endpoint()
    
    # Test 3: Create a test unpaid client
    test_client = create_test_unpaid_client()
    
    # Test 4: Re-check clients after creating test client
    if test_client:
        print("\n🔍 RE-CHECKING CLIENTS AFTER TEST CLIENT CREATION")
        updated_clients_data = test_clients_endpoint()
        
        # Test individual client endpoint
        test_individual_client_endpoint(test_client.get('id'))
    
    # Test 5: Analyze revenue calculation logic
    analyze_revenue_vs_unpaid_clients(payment_stats, clients_data)
    
    # Test 6: Re-check payment stats to see if test client affected revenue
    print("\n🔍 RE-CHECKING PAYMENT STATS AFTER TEST CLIENT")
    updated_payment_stats = test_payment_stats_endpoint()
    
    if payment_stats and updated_payment_stats:
        old_revenue = payment_stats.get('total_revenue', 0)
        new_revenue = updated_payment_stats.get('total_revenue', 0)
        
        print(f"\n📊 REVENUE CHANGE ANALYSIS:")
        print(f"   Revenue Before Test Client: TTD {old_revenue}")
        print(f"   Revenue After Test Client: TTD {new_revenue}")
        print(f"   Revenue Change: TTD {new_revenue - old_revenue}")
        
        if new_revenue != old_revenue:
            print(f"   ⚠️  WARNING: Revenue changed after adding unpaid client!")
            print(f"   This suggests revenue calculation may include unpaid clients")
        else:
            print(f"   ✅ GOOD: Revenue unchanged after adding unpaid client")
    
    print("\n" + "=" * 60)
    print("🎯 INVESTIGATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()