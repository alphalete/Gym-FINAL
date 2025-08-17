#!/usr/bin/env python3
"""
Final CRUD Verification - Comprehensive Backend API Test
"""

import requests
import os
from datetime import date
import json

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fitness-tracker-pwa.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f'{BACKEND_URL}/api'

def test_crud_operations():
    print("🔍 COMPREHENSIVE CRUD VERIFICATION")
    print("=" * 50)
    
    # 1. GET initial count
    print("\n1. Testing GET /api/clients...")
    response = requests.get(f'{BACKEND_URL}/clients', timeout=15)
    if response.status_code == 200:
        initial_clients = response.json()
        initial_count = len(initial_clients)
        print(f"✅ GET /api/clients: {initial_count} clients retrieved")
    else:
        print(f"❌ GET /api/clients failed: HTTP {response.status_code}")
        return False
    
    # 2. POST create client
    print("\n2. Testing POST /api/clients...")
    test_client_data = {
        "name": "Backend Test User",
        "email": "backendtest@example.com",
        "phone": "+1868-555-TEST",
        "membership_type": "Standard",
        "monthly_fee": 55.0,
        "start_date": date.today().isoformat(),
        "payment_status": "due"
    }
    
    response = requests.post(f'{BACKEND_URL}/clients', json=test_client_data, timeout=15)
    if response.status_code in [200, 201]:
        created_client = response.json()
        client_id = created_client.get('id')
        print(f"✅ POST /api/clients: Created client {created_client.get('name')} (ID: {client_id})")
    else:
        print(f"❌ POST /api/clients failed: HTTP {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # 3. GET specific client
    print("\n3. Testing GET /api/clients/{id}...")
    response = requests.get(f'{BACKEND_URL}/clients/{client_id}', timeout=15)
    if response.status_code == 200:
        retrieved_client = response.json()
        print(f"✅ GET /api/clients/{{id}}: Retrieved {retrieved_client.get('name')}")
    else:
        print(f"❌ GET /api/clients/{{id}} failed: HTTP {response.status_code}")
        return False
    
    # 4. PUT update client
    print("\n4. Testing PUT /api/clients/{id}...")
    update_data = {
        "phone": "+1868-555-UPDATED",
        "monthly_fee": 65.0
    }
    
    response = requests.put(f'{BACKEND_URL}/clients/{client_id}', json=update_data, timeout=15)
    if response.status_code == 200:
        updated_client = response.json()
        print(f"✅ PUT /api/clients/{{id}}: Updated phone to {updated_client.get('phone')}")
    else:
        print(f"❌ PUT /api/clients/{{id}} failed: HTTP {response.status_code}")
        return False
    
    # 5. DELETE client
    print("\n5. Testing DELETE /api/clients/{id}...")
    response = requests.delete(f'{BACKEND_URL}/clients/{client_id}', timeout=15)
    if response.status_code == 200:
        delete_result = response.json()
        print(f"✅ DELETE /api/clients/{{id}}: Deleted {delete_result.get('client_name')}")
    else:
        print(f"❌ DELETE /api/clients/{{id}} failed: HTTP {response.status_code}")
        return False
    
    # 6. Verify deletion
    print("\n6. Verifying deletion...")
    
    # Check specific client returns 404
    response = requests.get(f'{BACKEND_URL}/clients/{client_id}', timeout=15)
    if response.status_code == 404:
        print(f"✅ Deleted client returns 404 as expected")
    else:
        print(f"❌ Deleted client still accessible: HTTP {response.status_code}")
        return False
    
    # Check client count returned to original
    response = requests.get(f'{BACKEND_URL}/clients', timeout=15)
    if response.status_code == 200:
        final_clients = response.json()
        final_count = len(final_clients)
        
        if final_count == initial_count:
            print(f"✅ Client count restored: {initial_count} → {final_count}")
        else:
            print(f"❌ Client count mismatch: {initial_count} → {final_count}")
            return False
            
        # Verify test client not in list
        test_client_exists = any(c.get('email') == 'backendtest@example.com' for c in final_clients)
        if not test_client_exists:
            print(f"✅ Test client not found in client list")
        else:
            print(f"❌ Test client still exists in client list")
            return False
    else:
        print(f"❌ Final client count check failed: HTTP {response.status_code}")
        return False
    
    return True

if __name__ == "__main__":
    print(f"🔧 Testing Backend URL: {BACKEND_URL}")
    
    if test_crud_operations():
        print("\n🎉 ALL CRUD OPERATIONS WORKING PERFECTLY!")
        print("✅ GET /api/clients - retrieves client list")
        print("✅ POST /api/clients - creates new clients")
        print("✅ GET /api/clients/{id} - retrieves specific clients")
        print("✅ PUT /api/clients/{id} - updates client data")
        print("✅ DELETE /api/clients/{id} - deletes clients")
        print("✅ Data integrity maintained throughout")
        print("\n🔍 CONCLUSION: Backend APIs are working correctly!")
        print("   The frontend add/delete issues are NOT backend problems.")
    else:
        print("\n❌ CRUD OPERATIONS HAVE ISSUES!")
        print("   Backend API problems detected.")