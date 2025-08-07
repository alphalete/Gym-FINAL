#!/usr/bin/env python3
"""
Debug script to check if there's data in the backend when agent is running
and create seed data for offline usage
"""

import requests
import json
from datetime import datetime, date

def check_backend_status():
    """Check if backend is accessible and has data"""
    try:
        backend_url = "https://7ef3f37b-7d23-49f0-a1a7-5437683b78af.preview.emergentagent.com"
        
        print(f"🔍 Checking backend at: {backend_url}")
        
        # Test basic connectivity
        response = requests.get(f"{backend_url}/api/clients", timeout=10)
        
        if response.status_code == 200:
            clients = response.json()
            print(f"✅ Backend is UP - Found {len(clients)} clients")
            
            for client in clients:
                print(f"  - {client.get('name', 'Unknown')} ({client.get('email', 'No email')})")
            
            return True, clients
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"❌ Backend is DOWN or unreachable: {e}")
        return False, []

def create_offline_seed_data():
    """Create some seed data that can be used when offline"""
    
    seed_clients = [
        {
            "id": "offline-seed-1",
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "+1868-555-0101",
            "membership_type": "Standard",
            "monthly_fee": 300.0,
            "start_date": "2025-01-15",
            "next_payment_date": "2025-02-15",
            "status": "Active",
            "payment_status": "due",
            "amount_owed": 300.0,
            "billing_interval_days": 30,
            "notes": "Seed data for offline testing",
            "auto_reminders_enabled": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "offline-seed-2", 
            "name": "Sarah Johnson",
            "email": "sarah@example.com",
            "phone": "+1868-555-0102",
            "membership_type": "Premium",
            "monthly_fee": 500.0,
            "start_date": "2025-01-10",
            "next_payment_date": "2025-02-10",
            "status": "Active",
            "payment_status": "paid",
            "amount_owed": 0.0,
            "billing_interval_days": 30,
            "notes": "Seed data for offline testing - Premium member",
            "auto_reminders_enabled": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    return seed_clients

def main():
    """Main debug function"""
    print("🔍 DEBUGGING OFFLINE PWA DATA ISSUE")
    print("=" * 50)
    
    # Check if backend is available
    backend_up, existing_clients = check_backend_status()
    
    if backend_up:
        print(f"\n✅ GOOD NEWS: Backend has {len(existing_clients)} clients")
        print("💡 The issue might be:")
        print("  1. Frontend not caching data properly")
        print("  2. IndexedDB not storing data") 
        print("  3. App not falling back to local storage correctly")
        
        print("\n📋 EXISTING CLIENTS:")
        for i, client in enumerate(existing_clients, 1):
            print(f"{i}. {client.get('name')} - {client.get('email')}")
            
    else:
        print(f"\n❌ PROBLEM IDENTIFIED: Backend is down/unreachable")
        print("💡 This explains why no clients show when agent sleeps")
        
        seed_data = create_offline_seed_data()
        print(f"\n📦 CREATED SEED DATA: {len(seed_data)} sample clients")
        print("To fix this, we need to ensure the PWA:")
        print("  1. Stores data locally when backend is available")
        print("  2. Shows cached data when backend is unavailable")
        print("  3. Has some default/seed data for first-time users")
        
        print(f"\n💾 SEED DATA PREVIEW:")
        for client in seed_data:
            print(f"  - {client['name']} ({client['email']}) - {client['membership_type']}")
    
    print(f"\n🎯 NEXT STEPS:")
    print("  1. Enhance local storage initialization")
    print("  2. Add seed data for offline-first experience") 
    print("  3. Improve error handling when backend unavailable")
    print("  4. Test offline functionality thoroughly")

if __name__ == "__main__":
    main()