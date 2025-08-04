#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta

class MultiplePaymentTester:
    def __init__(self, base_url="https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: dict = None) -> tuple:
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
                    print(f"   ✅ {name} - PASSED (Status: {response.status_code})")
                    print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
                    return True, response_data
                except:
                    print(f"   ✅ {name} - PASSED (Status: {response.status_code}, No JSON response)")
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    print(f"   ❌ {name} - FAILED (Expected {expected_status}, got {response.status_code}) - {error_data}")
                except:
                    print(f"   ❌ {name} - FAILED (Expected {expected_status}, got {response.status_code}) - {response.text[:100]}")
                return False, {}

        except requests.exceptions.RequestException as e:
            print(f"   ❌ {name} - FAILED (Network Error: {str(e)})")
            return False, {}
        except Exception as e:
            print(f"   ❌ {name} - FAILED (Error: {str(e)})")
            return False, {}

    def test_multiple_payment_logic_issue(self):
        """CRITICAL TEST: Demonstrate the multiple payment logic issue identified by the user"""
        print("\n🚨 CRITICAL TEST: MULTIPLE PAYMENT LOGIC ISSUE DEMONSTRATION")
        print("=" * 80)
        print("🎯 OBJECTIVE: Test multiple payment scenarios to demonstrate the issue")
        print("📋 SCENARIO: Client makes multiple payments on the same day")
        print("❌ PROBLEM: Current logic uses payment_date + 30 days (doesn't accumulate)")
        print("✅ EXPECTED: Should extend from current due date or accumulate properly")
        print("=" * 80)
        
        # Step 1: Find or create "Deon Aleong" client
        print("\n📋 STEP 1: Get Current Client Data")
        success1, clients_response = self.run_test(
            "Get All Clients to Find Deon Aleong",
            "GET",
            "clients",
            200
        )
        
        deon_client = None
        if success1:
            clients = clients_response if isinstance(clients_response, list) else []
            for client in clients:
                if client.get('name') == 'Deon Aleong':
                    deon_client = client
                    break
        
        # If Deon Aleong doesn't exist, create him
        if not deon_client:
            print("   ⚠️  Deon Aleong not found, creating client...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            deon_data = {
                "name": "Deon Aleong",
                "email": f"deon_aleong_{timestamp}@example.com",
                "phone": "(555) 123-4567",
                "membership_type": "Elite",
                "monthly_fee": 100.00,
                "start_date": "2025-01-15"  # Due date would be 2025-02-14
            }
            
            success_create, create_response = self.run_test(
                "Create Deon Aleong Client",
                "POST",
                "clients",
                200,
                deon_data
            )
            
            if success_create and "id" in create_response:
                deon_client = create_response
                print(f"   ✅ Created Deon Aleong client ID: {deon_client['id']}")
            else:
                print("   ❌ Failed to create Deon Aleong client - aborting test")
                return False
        else:
            print(f"   ✅ Found Deon Aleong client ID: {deon_client['id']}")
        
        # Document starting scenario
        print(f"\n📊 STARTING SCENARIO:")
        print(f"   Client Name: {deon_client.get('name')}")
        print(f"   Client ID: {deon_client.get('id')}")
        print(f"   Current Next Payment Date: {deon_client.get('next_payment_date')}")
        print(f"   Monthly Fee: ${deon_client.get('monthly_fee')}")
        print(f"   Membership Type: {deon_client.get('membership_type')}")
        
        original_due_date = deon_client.get('next_payment_date')
        client_id = deon_client.get('id')
        
        # Step 2: Record First Payment
        print(f"\n📋 STEP 2: Record First Payment")
        today = date.today().isoformat()
        
        first_payment_data = {
            "client_id": client_id,
            "amount_paid": 100.00,
            "payment_date": today,
            "payment_method": "Credit Card",
            "notes": "First payment - testing multiple payment logic"
        }
        
        success2, first_payment_response = self.run_test(
            "Record First Payment (Today)",
            "POST",
            "payments/record",
            200,
            first_payment_data
        )
        
        if not success2:
            print("   ❌ Failed to record first payment - aborting test")
            return False
        
        first_new_due_date = first_payment_response.get('new_next_payment_date')
        print(f"   ✅ First payment recorded successfully")
        print(f"   💰 Amount paid: ${first_payment_response.get('amount_paid')}")
        print(f"   📅 Payment date: {today}")
        print(f"   📅 New next payment date: {first_new_due_date}")
        
        # Step 3: Record Second Payment Immediately (Same Day)
        print(f"\n📋 STEP 3: Record Second Payment Immediately (Same Day)")
        
        second_payment_data = {
            "client_id": client_id,
            "amount_paid": 100.00,
            "payment_date": today,  # Same day as first payment
            "payment_method": "Cash",
            "notes": "Second payment - same day as first payment"
        }
        
        success3, second_payment_response = self.run_test(
            "Record Second Payment (Same Day)",
            "POST",
            "payments/record",
            200,
            second_payment_data
        )
        
        if not success3:
            print("   ❌ Failed to record second payment - aborting test")
            return False
        
        second_new_due_date = second_payment_response.get('new_next_payment_date')
        print(f"   ✅ Second payment recorded successfully")
        print(f"   💰 Amount paid: ${second_payment_response.get('amount_paid')}")
        print(f"   📅 Payment date: {today}")
        print(f"   📅 New next payment date: {second_new_due_date}")
        
        # Step 4: Analyze the Multiple Payment Logic Issue
        print(f"\n📋 STEP 4: Analyze Multiple Payment Logic Issue")
        print("=" * 60)
        
        # Helper function to parse date strings in various formats
        def parse_date_string(date_str):
            """Parse date string in various formats"""
            if not isinstance(date_str, str):
                return date_str
            try:
                # Try ISO format first
                return datetime.fromisoformat(date_str).date()
            except ValueError:
                try:
                    # Try "Month DD, YYYY" format
                    return datetime.strptime(date_str, "%B %d, %Y").date()
                except ValueError:
                    try:
                        # Try "YYYY-MM-DD" format
                        return datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        print(f"   ⚠️  Could not parse date: {date_str}")
                        return None
        
        # Calculate expected dates for different logic options
        payment_date = datetime.fromisoformat(today).date()
        
        # Option A: Extend from current due date (correct logic)
        if original_due_date:
            original_due = parse_date_string(original_due_date)
            if original_due:
                option_a_after_first = original_due + timedelta(days=30)
                option_a_after_second = option_a_after_first + timedelta(days=30)
            else:
                option_a_after_first = payment_date + timedelta(days=30)
                option_a_after_second = option_a_after_first + timedelta(days=30)
        else:
            option_a_after_first = payment_date + timedelta(days=30)
            option_a_after_second = option_a_after_first + timedelta(days=30)
        
        # Option B: Payment date + 30 days (current flawed logic)
        option_b_after_first = payment_date + timedelta(days=30)
        option_b_after_second = payment_date + timedelta(days=30)  # Same as first!
        
        print(f"📊 PAYMENT LOGIC ANALYSIS:")
        print(f"   Original Due Date: {original_due_date}")
        print(f"   Payment Date (Both): {today}")
        print(f"   ")
        print(f"   🔍 OPTION A (Correct - Extend from due date):")
        print(f"      After 1st payment: {option_a_after_first}")
        print(f"      After 2nd payment: {option_a_after_second}")
        print(f"   ")
        print(f"   🔍 OPTION B (Current - Payment date + 30):")
        print(f"      After 1st payment: {option_b_after_first}")
        print(f"      After 2nd payment: {option_b_after_second}")
        print(f"   ")
        print(f"   📋 ACTUAL RESULTS:")
        print(f"      After 1st payment: {first_new_due_date}")
        print(f"      After 2nd payment: {second_new_due_date}")
        
        # Determine which logic is being used
        first_actual = parse_date_string(first_new_due_date)
        second_actual = parse_date_string(second_new_due_date)
        
        print(f"\n🎯 ISSUE DEMONSTRATION:")
        
        # Check if the current logic is flawed
        if first_actual == second_actual:
            print(f"   ❌ CRITICAL ISSUE CONFIRMED!")
            print(f"   ❌ Both payments result in the same due date: {second_new_due_date}")
            print(f"   ❌ This means the second payment didn't extend the membership period")
            print(f"   ❌ Current logic: payment_date + 30 days (doesn't accumulate)")
            print(f"   ")
            print(f"   💡 PROBLEM EXPLANATION:")
            print(f"      - Client pays twice on {today}")
            print(f"      - Both payments set due date to {today} + 30 days = {second_new_due_date}")
            print(f"      - Second payment doesn't extend membership beyond first payment")
            print(f"      - Client loses value from multiple payments")
            
            issue_confirmed = True
        else:
            print(f"   ✅ Multiple payments extend membership period correctly")
            print(f"   ✅ First payment due date: {first_new_due_date}")
            print(f"   ✅ Second payment due date: {second_new_due_date}")
            issue_confirmed = False
        
        # Step 5: Proposed Logic Options
        print(f"\n📋 STEP 5: Proposed Logic Options")
        print("=" * 60)
        
        print(f"🔧 OPTION A: Extend from current due date")
        print(f"   Logic: new_due_date = max(current_due_date, payment_date) + 30 days")
        print(f"   Benefit: Multiple payments accumulate properly")
        print(f"   Example: If due 2025-02-15, payment on 2025-01-10 → new due 2025-03-17")
        print(f"   ")
        print(f"🔧 OPTION B: Payment date + 30 days (CURRENT - FLAWED)")
        print(f"   Logic: new_due_date = payment_date + 30 days")
        print(f"   Problem: Multiple payments on same day don't accumulate")
        print(f"   Example: Two payments on 2025-01-10 → both set due to 2025-02-09")
        print(f"   ")
        print(f"🔧 OPTION C: Pro-rated logic (Complex)")
        print(f"   Logic: Calculate based on remaining days and payment amount")
        print(f"   Benefit: More precise for partial payments")
        print(f"   Complexity: Requires more complex calculation logic")
        
        # Step 6: Test with different payment dates
        print(f"\n📋 STEP 6: Test Different Payment Date Scenarios")
        
        # Create another test client for different scenarios
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_client_data = {
            "name": "Multiple Payment Test Client",
            "email": f"multi_payment_test_{timestamp}@example.com",
            "phone": "(555) 999-8888",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-01-15"  # Due date: 2025-02-14
        }
        
        success_test, test_client_response = self.run_test(
            "Create Test Client for Different Scenarios",
            "POST",
            "clients",
            200,
            test_client_data
        )
        
        if success_test and "id" in test_client_response:
            test_client_id = test_client_response["id"]
            original_test_due = test_client_response.get('next_payment_date')
            
            print(f"   ✅ Created test client - Due date: {original_test_due}")
            
            # Scenario: Payment before due date
            early_payment_date = "2025-01-10"  # 5 days before due
            early_payment_data = {
                "client_id": test_client_id,
                "amount_paid": 50.00,
                "payment_date": early_payment_date,
                "payment_method": "Bank Transfer",
                "notes": "Early payment test"
            }
            
            success_early, early_response = self.run_test(
                "Record Early Payment (Before Due Date)",
                "POST",
                "payments/record",
                200,
                early_payment_data
            )
            
            if success_early:
                early_new_due = early_response.get('new_next_payment_date')
                print(f"   📅 Early payment on: {early_payment_date}")
                print(f"   📅 Original due date: {original_test_due}")
                print(f"   📅 New due date: {early_new_due}")
                
                # Analyze the logic
                early_payment_dt = datetime.fromisoformat(early_payment_date).date()
                expected_option_a = parse_date_string(original_test_due) + timedelta(days=30) if parse_date_string(original_test_due) else None
                expected_option_b = early_payment_dt + timedelta(days=30)
                actual_due = parse_date_string(early_new_due)
                
                print(f"   🔍 Expected (Option A - extend from due): {expected_option_a}")
                print(f"   🔍 Expected (Option B - payment + 30): {expected_option_b}")
                print(f"   🔍 Actual result: {actual_due}")
                
                if actual_due and expected_option_b and actual_due == expected_option_b:
                    print(f"   ❌ Using Option B logic (payment_date + 30)")
                    if expected_option_a:
                        print(f"   ❌ Client loses {(expected_option_a - expected_option_b).days} days of membership")
                elif actual_due and expected_option_a and actual_due == expected_option_a:
                    print(f"   ✅ Using Option A logic (extend from due date)")
                else:
                    print(f"   ❓ Using unknown logic")
        
        # Final Summary
        print(f"\n🎯 MULTIPLE PAYMENT LOGIC TEST SUMMARY")
        print("=" * 80)
        
        if issue_confirmed:
            print(f"❌ CRITICAL ISSUE CONFIRMED: Multiple Payment Logic Problem")
            print(f"   • Current logic: payment_date + 30 days")
            print(f"   • Problem: Multiple payments on same day don't accumulate")
            print(f"   • Impact: Clients lose membership time with multiple payments")
            print(f"   • Solution needed: Implement Option A (extend from due date)")
            print(f"   ")
            print(f"🔧 RECOMMENDED FIX:")
            print(f"   Change line 483 in server.py from:")
            print(f"   new_next_payment_date = payment_request.payment_date + timedelta(days=30)")
            print(f"   To:")
            print(f"   current_due = client_obj.next_payment_date")
            print(f"   new_next_payment_date = max(current_due, payment_request.payment_date) + timedelta(days=30)")
        else:
            print(f"✅ Multiple payment logic appears to be working correctly")
            print(f"   • Multiple payments extend membership period properly")
            print(f"   • No accumulation issues detected")
        
        return not issue_confirmed  # Return True if no issue, False if issue confirmed

def main():
    """Main function to run the multiple payment logic test"""
    print("🏋️‍♂️ ALPHALETE ATHLETICS CLUB - MULTIPLE PAYMENT LOGIC TESTING")
    print("Testing multiple payment scenarios to demonstrate the issue")
    print()
    
    tester = MultiplePaymentTester()
    
    # Run the multiple payment logic test
    result = tester.test_multiple_payment_logic_issue()
    
    if result:
        print("\n✅ Multiple payment logic test completed - no issues detected")
        return 0
    else:
        print("\n❌ Multiple payment logic test completed - CRITICAL ISSUE CONFIRMED")
        return 1

if __name__ == "__main__":
    sys.exit(main())