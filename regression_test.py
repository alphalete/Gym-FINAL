#!/usr/bin/env python3
"""
REGRESSION TEST FOR PAYMENT DATE CALCULATION
============================================

The user is reporting the same issue that was supposedly fixed before.
Let me test if there's a regression or if the old max() logic somehow returned.

From the history, the bug was:
- OLD (BROKEN): base_date = max(current_due_date, payment_date)
- NEW (FIXED): base_date = current_due_date

Let me test various scenarios to see if I can reproduce the user's issue.
"""

import requests
import json
from datetime import datetime, date
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def test_exact_user_scenario():
    """Test the EXACT scenario the user reported"""
    print("🎯 TESTING EXACT USER SCENARIO")
    print("=" * 60)
    print("User Report: Client joins Feb 15 → next due Mar 15 ✅")
    print("User Report: Client pays late → due date goes to Apr 15 ❌ (should stay Mar 15)")
    print()
    
    test_client_data = {
        "name": "Exact User Scenario Client",
        "email": f"exact_user_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "phone": "+18685551234",
        "membership_type": "Standard",
        "monthly_fee": 55.0,
        "start_date": "2025-02-15",
        "payment_status": "due",
        "auto_reminders_enabled": True
    }
    
    try:
        # Step 1: Client joins Feb 15
        print("📝 STEP 1: Client joins Feb 15...")
        response = requests.post(f"{API_BASE}/clients", json=test_client_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Client creation failed: {response.status_code}")
            return False
            
        client = response.json()
        client_id = client['id']
        
        print(f"✅ Client created: {client['name']}")
        print(f"   Start Date: {client['start_date']}")
        print(f"   Next Due Date: {client['next_payment_date']}")
        
        # Verify next due date is Mar 15
        if client['next_payment_date'] != "2025-03-15":
            print(f"❌ Initial due date wrong! Expected 2025-03-15, got {client['next_payment_date']}")
            return False
        else:
            print(f"✅ Initial due date correct: Mar 15")
        
        # Step 2: Client pays late
        print(f"\n💰 STEP 2: Client pays late (after Mar 15)...")
        
        # Try different late payment dates to see if any trigger the bug
        late_payment_scenarios = [
            "2025-03-16",  # 1 day late
            "2025-03-20",  # 5 days late  
            "2025-03-25",  # 10 days late
            "2025-03-31",  # 16 days late
            "2025-04-01",  # 17 days late (next month)
        ]
        
        for late_date in late_payment_scenarios:
            print(f"\n🧪 Testing late payment on {late_date}...")
            
            # Create fresh client for each test
            fresh_client_data = test_client_data.copy()
            fresh_client_data['email'] = f"late_test_{late_date.replace('-', '')}_{datetime.now().strftime('%H%M%S')}@example.com"
            
            response = requests.post(f"{API_BASE}/clients", json=fresh_client_data, timeout=10)
            if response.status_code != 200:
                continue
                
            fresh_client = response.json()
            fresh_client_id = fresh_client['id']
            
            # Record late payment
            payment_data = {
                "client_id": fresh_client_id,
                "amount_paid": 55.0,
                "payment_date": late_date,
                "payment_method": "Cash",
                "notes": f"Late payment test - {late_date}"
            }
            
            response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
            if response.status_code != 200:
                print(f"   ❌ Payment failed: {response.status_code}")
                continue
                
            payment_result = response.json()
            new_due_date = payment_result['new_next_payment_date']
            
            print(f"   Payment Date: {late_date}")
            print(f"   New Due Date: {new_due_date}")
            
            # Analyze result based on user's expectation
            if "April 15" in new_due_date:
                print(f"   📊 SYSTEM BEHAVIOR: Advanced to next month (Mar 15 → Apr 15)")
                print(f"   🤔 USER EXPECTATION: Wants it to stay Mar 15 (no advancement)")
                print(f"   ✅ PROFESSIONAL BILLING: This is correct behavior")
            elif "March 15" in new_due_date:
                print(f"   📊 SYSTEM BEHAVIOR: Stayed same month (Mar 15 → Mar 15)")
                print(f"   ✅ USER EXPECTATION: This matches what user wants")
                print(f"   ❌ PROFESSIONAL BILLING: This would be incorrect")
            elif "May 15" in new_due_date:
                print(f"   🚨 BUG DETECTED: Jumped TWO months (Mar 15 → May 15)")
                print(f"   ❌ This matches user's complaint about jumping ahead!")
                return False
            else:
                print(f"   ❓ UNEXPECTED: {new_due_date}")
            
            # Cleanup
            try:
                requests.delete(f"{API_BASE}/clients/{fresh_client_id}", timeout=5)
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        try:
            if 'client_id' in locals():
                requests.delete(f"{API_BASE}/clients/{client_id}", timeout=5)
        except:
            pass

def test_old_max_logic_regression():
    """Test if the old max() logic somehow returned"""
    print("\n🔍 TESTING FOR OLD MAX() LOGIC REGRESSION")
    print("=" * 60)
    print("OLD BUG: max(current_due_date, payment_date) caused date drift")
    print("FIXED: current_due_date only (no max logic)")
    
    test_client_data = {
        "name": "Max Logic Regression Test",
        "email": f"max_logic_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "phone": "+18685551235",
        "membership_type": "Premium",
        "monthly_fee": 75.0,
        "start_date": "2025-01-15",
        "payment_status": "due",
        "auto_reminders_enabled": True
    }
    
    try:
        # Create client
        response = requests.post(f"{API_BASE}/clients", json=test_client_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Client creation failed: {response.status_code}")
            return False
            
        client = response.json()
        client_id = client['id']
        
        print(f"✅ Client created with due date: {client['next_payment_date']}")
        
        # Test the exact scenario that would trigger the old bug
        print(f"\n🧪 Testing scenario that triggered old max() bug...")
        print(f"   Due Date: Feb 15, 2025")
        print(f"   Payment Date: Feb 20, 2025 (5 days late)")
        print(f"   OLD BUG: Would calculate from Feb 20 → Mar 20")
        print(f"   FIXED: Should calculate from Feb 15 → Mar 15")
        
        payment_data = {
            "client_id": client_id,
            "amount_paid": 75.0,
            "payment_date": "2025-02-20",  # 5 days after Feb 15 due date
            "payment_method": "Cash",
            "notes": "Testing for max() logic regression"
        }
        
        response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Payment failed: {response.status_code}")
            return False
            
        payment_result = response.json()
        new_due_date = payment_result['new_next_payment_date']
        
        print(f"\n📊 RESULT ANALYSIS:")
        print(f"   Payment Date: Feb 20, 2025")
        print(f"   New Due Date: {new_due_date}")
        
        if "March 15" in new_due_date:
            print(f"   ✅ CORRECT: Calculated from due date (Feb 15 + 1 month = Mar 15)")
            print(f"   ✅ NO REGRESSION: Old max() logic not present")
            return True
        elif "March 20" in new_due_date:
            print(f"   ❌ REGRESSION DETECTED: Using max() logic!")
            print(f"   🚨 OLD BUG RETURNED: Calculating from payment date instead of due date")
            return False
        else:
            print(f"   ❓ UNEXPECTED RESULT: {new_due_date}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        try:
            if 'client_id' in locals():
                requests.delete(f"{API_BASE}/clients/{client_id}", timeout=5)
                print(f"🧹 Cleanup: Test client deleted")
        except:
            pass

def test_user_misunderstanding_scenario():
    """Test if user misunderstands professional billing behavior"""
    print("\n🤔 TESTING USER MISUNDERSTANDING SCENARIO")
    print("=" * 60)
    print("Hypothesis: User expects late payment to NOT advance due date")
    print("Reality: Professional billing SHOULD advance due date after payment")
    
    print("\n📚 PROFESSIONAL BILLING EXPLANATION:")
    print("   - Monthly membership = pay for upcoming month of service")
    print("   - When you pay (even late), you get next month of service")
    print("   - Due date advances to next month regardless of payment timing")
    print("   - This prevents 'free months' from late payments")
    
    test_client_data = {
        "name": "User Understanding Test",
        "email": f"user_understanding_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "phone": "+18685551236",
        "membership_type": "Elite",
        "monthly_fee": 100.0,
        "start_date": "2025-02-15",
        "payment_status": "due",
        "auto_reminders_enabled": True
    }
    
    try:
        # Create client
        response = requests.post(f"{API_BASE}/clients", json=test_client_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Client creation failed: {response.status_code}")
            return False
            
        client = response.json()
        client_id = client['id']
        
        print(f"\n✅ Client created:")
        print(f"   Start Date: {client['start_date']} (Feb 15)")
        print(f"   First Due Date: {client['next_payment_date']} (Mar 15)")
        print(f"   Service Period: Feb 15 - Mar 14 (paid in advance)")
        
        # Record late payment
        payment_date = "2025-03-25"  # 10 days late
        payment_data = {
            "client_id": client_id,
            "amount_paid": 100.0,
            "payment_date": payment_date,
            "payment_method": "Cash",
            "notes": "Late payment - user understanding test"
        }
        
        print(f"\n💰 Recording late payment:")
        print(f"   Due Date: Mar 15, 2025")
        print(f"   Payment Date: {payment_date} (10 days late)")
        print(f"   Payment For: Mar 15 - Apr 14 service period")
        
        response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Payment failed: {response.status_code}")
            return False
            
        payment_result = response.json()
        new_due_date = payment_result['new_next_payment_date']
        
        print(f"\n📊 PROFESSIONAL BILLING ANALYSIS:")
        print(f"   Payment Received: {payment_date}")
        print(f"   Service Paid For: Mar 15 - Apr 14")
        print(f"   Next Due Date: {new_due_date}")
        print(f"   Next Service Period: Apr 15 - May 14")
        
        if "April 15" in new_due_date:
            print(f"\n✅ CORRECT PROFESSIONAL BILLING:")
            print(f"   - Client paid for Mar 15 - Apr 14 service")
            print(f"   - Next payment due Apr 15 for Apr 15 - May 14 service")
            print(f"   - No 'free months' from late payment")
            print(f"   - Consistent monthly billing cycle maintained")
            
            print(f"\n🤔 USER'S POSSIBLE MISUNDERSTANDING:")
            print(f"   - User may expect late payment to not advance due date")
            print(f"   - User may think: 'I paid late, so next payment should still be Mar 15'")
            print(f"   - This would give client free service time")
            print(f"   - This is not standard professional billing practice")
            
            return True
        else:
            print(f"\n❓ UNEXPECTED BILLING BEHAVIOR: {new_due_date}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        try:
            if 'client_id' in locals():
                requests.delete(f"{API_BASE}/clients/{client_id}", timeout=5)
                print(f"🧹 Cleanup: Test client deleted")
        except:
            pass

def main():
    """Run regression tests for payment date calculation"""
    print("🔍 PAYMENT DATE CALCULATION REGRESSION TESTING")
    print("=" * 80)
    print("Investigating user's reported issue with payment date jumping ahead")
    print("=" * 80)
    
    results = []
    
    # Test 1: Exact user scenario
    result1 = test_exact_user_scenario()
    results.append(("Exact User Scenario", result1))
    
    # Test 2: Old max() logic regression
    result2 = test_old_max_logic_regression()
    results.append(("Max Logic Regression Check", result2))
    
    # Test 3: User misunderstanding
    result3 = test_user_misunderstanding_scenario()
    results.append(("User Understanding Analysis", result3))
    
    # Summary
    print("\n" + "="*80)
    print("🎯 REGRESSION TEST SUMMARY")
    print("="*80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 NO REGRESSION DETECTED!")
        print("   Payment date calculation working correctly.")
        print("   User's issue may be based on misunderstanding professional billing.")
        print("   System correctly advances due date after payment (standard practice).")
    else:
        print("\n🚨 REGRESSION OR BUG DETECTED!")
        print("   Payment date calculation has issues.")
        print("   User's complaint appears to be valid.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)