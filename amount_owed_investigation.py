#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class AmountOwedInvestigator:
    """
    Investigate the amount_owed field behavior to understand why it's 0.0 instead of monthly_fee
    """
    
    def __init__(self, base_url="https://442a58e4-b64f-4824-924a-0c12436c79ea.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Dict[Any, Any] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    print(f"   ✅ SUCCESS (Status: {response.status_code})")
                    print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
                    return True, response_data
                except:
                    print(f"   ✅ SUCCESS (Status: {response.status_code}, No JSON response)")
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    print(f"   ❌ FAILED (Expected {expected_status}, got {response.status_code}) - {error_data}")
                except:
                    print(f"   ❌ FAILED (Expected {expected_status}, got {response.status_code}) - {response.text[:100]}")
                return False, {}

        except requests.exceptions.RequestException as e:
            print(f"   ❌ NETWORK ERROR: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return False, {}

    def test_amount_owed_scenarios(self):
        """Test different scenarios for amount_owed field"""
        print("\n" + "="*80)
        print("🎯 AMOUNT_OWED FIELD INVESTIGATION")
        print("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Scenario 1: Create client with payment_status='due' and NO amount_owed specified
        print("\n📋 SCENARIO 1: payment_status='due', NO amount_owed specified")
        client_data_1 = {
            "name": "Test Client 1",
            "email": f"test1_{timestamp}@example.com",
            "phone": "+18685551111",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-15",
            "payment_status": "due",
            "auto_reminders_enabled": True
        }
        
        success1, response1 = self.run_test(
            "Create Client - Due Status, No Amount Owed",
            "POST",
            "clients",
            200,
            client_data_1
        )
        
        if success1:
            print(f"   📊 RESULT: amount_owed = ${response1.get('amount_owed')}, monthly_fee = ${response1.get('monthly_fee')}")
        
        # Scenario 2: Create client with payment_status='due' and amount_owed=0.0 explicitly
        print("\n📋 SCENARIO 2: payment_status='due', amount_owed=0.0 explicitly")
        client_data_2 = {
            "name": "Test Client 2",
            "email": f"test2_{timestamp}@example.com",
            "phone": "+18685552222",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-15",
            "payment_status": "due",
            "amount_owed": 0.0,  # Explicitly set to 0
            "auto_reminders_enabled": True
        }
        
        success2, response2 = self.run_test(
            "Create Client - Due Status, Amount Owed = 0.0",
            "POST",
            "clients",
            200,
            client_data_2
        )
        
        if success2:
            print(f"   📊 RESULT: amount_owed = ${response2.get('amount_owed')}, monthly_fee = ${response2.get('monthly_fee')}")
        
        # Scenario 3: Create client with payment_status='due' and amount_owed=monthly_fee explicitly
        print("\n📋 SCENARIO 3: payment_status='due', amount_owed=monthly_fee explicitly")
        client_data_3 = {
            "name": "Test Client 3",
            "email": f"test3_{timestamp}@example.com",
            "phone": "+18685553333",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-15",
            "payment_status": "due",
            "amount_owed": 50.00,  # Explicitly set to monthly fee
            "auto_reminders_enabled": True
        }
        
        success3, response3 = self.run_test(
            "Create Client - Due Status, Amount Owed = Monthly Fee",
            "POST",
            "clients",
            200,
            client_data_3
        )
        
        if success3:
            print(f"   📊 RESULT: amount_owed = ${response3.get('amount_owed')}, monthly_fee = ${response3.get('monthly_fee')}")
        
        # Scenario 4: Create client with payment_status='paid'
        print("\n📋 SCENARIO 4: payment_status='paid'")
        client_data_4 = {
            "name": "Test Client 4",
            "email": f"test4_{timestamp}@example.com",
            "phone": "+18685554444",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-15",
            "payment_status": "paid",
            "auto_reminders_enabled": True
        }
        
        success4, response4 = self.run_test(
            "Create Client - Paid Status",
            "POST",
            "clients",
            200,
            client_data_4
        )
        
        if success4:
            print(f"   📊 RESULT: amount_owed = ${response4.get('amount_owed')}, monthly_fee = ${response4.get('monthly_fee')}")
        
        # Scenario 5: Create client with NO payment_status (should default to 'due')
        print("\n📋 SCENARIO 5: NO payment_status specified (should default to 'due')")
        client_data_5 = {
            "name": "Test Client 5",
            "email": f"test5_{timestamp}@example.com",
            "phone": "+18685555555",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-15",
            "auto_reminders_enabled": True
        }
        
        success5, response5 = self.run_test(
            "Create Client - No Payment Status",
            "POST",
            "clients",
            200,
            client_data_5
        )
        
        if success5:
            print(f"   📊 RESULT: payment_status = '{response5.get('payment_status')}', amount_owed = ${response5.get('amount_owed')}, monthly_fee = ${response5.get('monthly_fee')}")
        
        # Analysis
        print("\n" + "="*80)
        print("🔍 ANALYSIS OF AMOUNT_OWED BEHAVIOR")
        print("="*80)
        
        print("\n📊 SUMMARY OF RESULTS:")
        if success1:
            print(f"   Scenario 1 (due, no amount_owed): amount_owed = ${response1.get('amount_owed')}")
        if success2:
            print(f"   Scenario 2 (due, amount_owed=0.0): amount_owed = ${response2.get('amount_owed')}")
        if success3:
            print(f"   Scenario 3 (due, amount_owed=50.0): amount_owed = ${response3.get('amount_owed')}")
        if success4:
            print(f"   Scenario 4 (paid): amount_owed = ${response4.get('amount_owed')}")
        if success5:
            print(f"   Scenario 5 (no status): payment_status = '{response5.get('payment_status')}', amount_owed = ${response5.get('amount_owed')}")
        
        print("\n🔍 BACKEND CODE ANALYSIS:")
        print("   Looking at server.py lines 309-316:")
        print("   payment_status = client_dict.get('payment_status', 'due')")
        print("   if payment_status == 'paid':")
        print("       client_dict['amount_owed'] = 0.0")
        print("   else:")
        print("       client_dict['amount_owed'] = client_dict.get('amount_owed', client_dict['monthly_fee'])")
        
        print("\n💡 EXPECTED BEHAVIOR:")
        print("   - If payment_status='paid': amount_owed should be 0.0")
        print("   - If payment_status='due' and amount_owed not specified: amount_owed should be monthly_fee")
        print("   - If payment_status='due' and amount_owed specified: amount_owed should be the specified value")
        
        print("\n🎯 CONCLUSION:")
        if success1 and response1.get('amount_owed') == 0.0:
            print("   ⚠️  POTENTIAL ISSUE: When payment_status='due' and amount_owed not specified,")
            print("       amount_owed is 0.0 instead of monthly_fee")
            print("   🔍 ROOT CAUSE: The client_dict.get('amount_owed', client_dict['monthly_fee']) logic")
            print("       may not be working as expected. This could be because:")
            print("       1. amount_owed=0.0 is being passed explicitly in the request")
            print("       2. The Pydantic model is setting a default value of 0.0")
            print("       3. The logic is being overridden somewhere else")
        else:
            print("   ✅ BEHAVIOR APPEARS CORRECT: amount_owed is being set properly")

if __name__ == "__main__":
    print("🎯 AMOUNT_OWED FIELD INVESTIGATION")
    print("Investigating why amount_owed is 0.0 instead of monthly_fee for unpaid clients")
    print("="*80)
    
    investigator = AmountOwedInvestigator()
    investigator.test_amount_owed_scenarios()