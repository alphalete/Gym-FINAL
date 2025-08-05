#!/usr/bin/env python3
"""
Payment Recording and Revenue Update Test
Testing if payment recording properly updates revenue calculations
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

def record_payment_for_client(client_id, amount, payment_date="2025-01-20"):
    """Record a payment for a specific client"""
    print(f"\n🔍 RECORDING PAYMENT FOR CLIENT: {client_id}")
    print("=" * 50)
    
    payment_data = {
        "client_id": client_id,
        "amount_paid": amount,
        "payment_date": payment_date,
        "payment_method": "Cash",
        "notes": "Test payment for revenue investigation"
    }
    
    try:
        response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Payment recorded successfully:")
            print(f"   Client: {result.get('client_name')}")
            print(f"   Amount: TTD {result.get('amount_paid')}")
            print(f"   Payment ID: {result.get('payment_id')}")
            print(f"   New Next Payment Date: {result.get('new_next_payment_date')}")
            print(f"   Invoice Sent: {result.get('invoice_sent')}")
            return result
        else:
            print(f"❌ Failed to record payment: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error recording payment: {str(e)}")
        return None

def get_payment_stats():
    """Get current payment statistics"""
    try:
        response = requests.get(f"{API_BASE}/payments/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ Error getting payment stats: {str(e)}")
        return None

def get_clients():
    """Get all clients"""
    try:
        response = requests.get(f"{API_BASE}/clients", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ Error getting clients: {str(e)}")
        return None

def main():
    """Main test execution"""
    print("🎯 PAYMENT RECORDING AND REVENUE UPDATE TEST")
    print("=" * 60)
    
    # Get initial state
    print("\n📊 INITIAL STATE:")
    initial_stats = get_payment_stats()
    initial_clients = get_clients()
    
    if initial_stats:
        print(f"   Initial Revenue: TTD {initial_stats.get('total_revenue', 0)}")
        print(f"   Initial Payment Count: {initial_stats.get('payment_count', 0)}")
    
    if initial_clients:
        unpaid_clients = [c for c in initial_clients if c.get('payment_status') == 'due']
        print(f"   Unpaid Clients: {len(unpaid_clients)}")
        
        # Record payment for first unpaid client
        if unpaid_clients:
            test_client = unpaid_clients[0]
            client_id = test_client.get('id')
            client_name = test_client.get('name')
            monthly_fee = test_client.get('monthly_fee', 0)
            
            print(f"\n🎯 TESTING WITH CLIENT: {client_name}")
            print(f"   Client ID: {client_id}")
            print(f"   Monthly Fee: TTD {monthly_fee}")
            
            # Record payment
            payment_result = record_payment_for_client(client_id, monthly_fee)
            
            if payment_result:
                # Check updated stats
                print("\n📊 AFTER PAYMENT:")
                updated_stats = get_payment_stats()
                updated_clients = get_clients()
                
                if updated_stats:
                    print(f"   Updated Revenue: TTD {updated_stats.get('total_revenue', 0)}")
                    print(f"   Updated Payment Count: {updated_stats.get('payment_count', 0)}")
                    
                    # Compare with initial
                    if initial_stats:
                        revenue_change = updated_stats.get('total_revenue', 0) - initial_stats.get('total_revenue', 0)
                        count_change = updated_stats.get('payment_count', 0) - initial_stats.get('payment_count', 0)
                        
                        print(f"\n📈 CHANGES:")
                        print(f"   Revenue Change: TTD {revenue_change}")
                        print(f"   Payment Count Change: {count_change}")
                        
                        if revenue_change == monthly_fee and count_change == 1:
                            print(f"   ✅ CORRECT: Revenue increased by payment amount")
                        else:
                            print(f"   ⚠️  ISSUE: Revenue change doesn't match payment amount")
                
                # Check client status update
                if updated_clients:
                    updated_client = next((c for c in updated_clients if c.get('id') == client_id), None)
                    if updated_client:
                        print(f"\n👤 CLIENT STATUS AFTER PAYMENT:")
                        print(f"   Payment Status: {updated_client.get('payment_status')}")
                        print(f"   Amount Owed: {updated_client.get('amount_owed')}")
                        print(f"   Next Payment Date: {updated_client.get('next_payment_date')}")
        else:
            print("   No unpaid clients found to test with")
    
    # Test with another unpaid client if available
    current_clients = get_clients()
    if current_clients:
        remaining_unpaid = [c for c in current_clients if c.get('payment_status') == 'due']
        if remaining_unpaid:
            print(f"\n🎯 TESTING WITH SECOND CLIENT")
            second_client = remaining_unpaid[0]
            client_id = second_client.get('id')
            client_name = second_client.get('name')
            monthly_fee = second_client.get('monthly_fee', 0)
            
            print(f"   Client: {client_name}")
            print(f"   Monthly Fee: TTD {monthly_fee}")
            
            # Get stats before second payment
            before_second_stats = get_payment_stats()
            
            # Record second payment
            second_payment = record_payment_for_client(client_id, monthly_fee)
            
            if second_payment:
                # Check final stats
                final_stats = get_payment_stats()
                if before_second_stats and final_stats:
                    revenue_change = final_stats.get('total_revenue', 0) - before_second_stats.get('total_revenue', 0)
                    print(f"\n📈 SECOND PAYMENT IMPACT:")
                    print(f"   Revenue Change: TTD {revenue_change}")
                    print(f"   Expected Change: TTD {monthly_fee}")
                    
                    if revenue_change == monthly_fee:
                        print(f"   ✅ CORRECT: Second payment properly updated revenue")
                    else:
                        print(f"   ⚠️  ISSUE: Second payment revenue change incorrect")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 PAYMENT RECORDING TEST COMPLETE")
    
    final_stats = get_payment_stats()
    final_clients = get_clients()
    
    if final_stats:
        print(f"📊 FINAL STATE:")
        print(f"   Total Revenue: TTD {final_stats.get('total_revenue', 0)}")
        print(f"   Payment Count: {final_stats.get('payment_count', 0)}")
    
    if final_clients:
        paid_count = len([c for c in final_clients if c.get('payment_status') == 'paid'])
        unpaid_count = len([c for c in final_clients if c.get('payment_status') == 'due'])
        print(f"   Paid Clients: {paid_count}")
        print(f"   Unpaid Clients: {unpaid_count}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()