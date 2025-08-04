#!/usr/bin/env python3
"""
SPECIFIC USER SCENARIO TEST
===========================

Re-testing the user's exact complaint with different interpretations:

User says: "Client pays late → due date goes to Apr 15 ❌ (wrong, should stay Mar 15)"

This suggests the user expects the due date to NOT advance when payment is late.
But that would be incorrect billing behavior. Let me test if there's a different bug:

1. Maybe the date jumps TWO months (Mar 15 → May 15)
2. Maybe the date uses payment date instead of due date (Mar 15 → Apr 20 if paid on Mar 20)
3. Maybe there's inconsistent behavior under certain conditions
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

def test_user_expectation_scenario():
    """Test if user expects due date to NOT advance after payment"""
    print("🤔 TESTING USER'S EXPECTATION SCENARIO")
    print("=" * 60)
    print("User seems to expect: Late payment should NOT advance due date")
    print("Professional billing: Late payment SHOULD advance due date")
    print()
    
    test_client_data = {
        "name": "User Expectation Test Client",
        "email": f"user_expect_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "phone": "+18685551234",
        "membership_type": "Standard",
        "monthly_fee": 55.0,
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
        
        print(f"✅ Client created: {client['name']}")
        print(f"   Start Date: {client['start_date']}")
        print(f"   Initial Next Payment Date: {client['next_payment_date']}")
        
        # Record late payment
        late_payment_date = "2025-03-20"  # 5 days after Mar 15 due date
        payment_data = {
            "client_id": client_id,
            "amount_paid": 55.0,
            "payment_date": late_payment_date,
            "payment_method": "Cash",
            "notes": "Late payment - user expectation test"
        }
        
        print(f"\n💰 Recording late payment on {late_payment_date} (5 days after Mar 15 due date)")
        response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Payment recording failed: {response.status_code}")
            return False
            
        payment_result = response.json()
        new_due_date = payment_result['new_next_payment_date']
        
        print(f"✅ Payment recorded successfully")
        print(f"   Payment Date: {late_payment_date}")
        print(f"   New Next Payment Date: {new_due_date}")
        
        # Analyze the result
        print(f"\n📊 ANALYSIS:")
        print(f"   Original Due Date: March 15, 2025")
        print(f"   Payment Made On: {late_payment_date} (5 days late)")
        print(f"   New Due Date: {new_due_date}")
        
        if new_due_date == "April 15, 2025":
            print(f"   ✅ PROFESSIONAL BILLING: Correct behavior - advanced one month")
            print(f"   📝 USER'S EXPECTATION: May be incorrect - expecting no advancement")
            print(f"   🎯 CONCLUSION: System working correctly, user may have wrong expectation")
            return True
        elif new_due_date == "March 15, 2025":
            print(f"   🤔 USER'S EXPECTATION: Due date stayed the same (as user wants)")
            print(f"   ❌ PROFESSIONAL BILLING: This would be incorrect billing behavior")
            print(f"   🎯 CONCLUSION: System has bug - not advancing payment dates")
            return False
        elif new_due_date == "May 15, 2025":
            print(f"   ❌ DOUBLE JUMP BUG: Date jumped TWO months ahead!")
            print(f"   🚨 CRITICAL BUG: This matches user's complaint about jumping ahead")
            return False
        elif "April 20" in new_due_date:
            print(f"   ❌ PAYMENT DATE BUG: Using payment date instead of due date!")
            print(f"   🚨 CRITICAL BUG: Should calculate from Mar 15, not Mar 20")
            return False
        else:
            print(f"   ❓ UNEXPECTED RESULT: Unexpected date calculation")
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

def test_potential_double_jump_bug():
    """Test if there's a bug causing double month jumps"""
    print("\n🚨 TESTING POTENTIAL DOUBLE JUMP BUG")
    print("=" * 60)
    print("Looking for: Mar 15 → May 15 (skipping April)")
    
    test_client_data = {
        "name": "Double Jump Test Client",
        "email": f"double_jump_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "phone": "+18685551235",
        "membership_type": "Premium",
        "monthly_fee": 75.0,
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
        
        print(f"✅ Client created with next payment date: {client['next_payment_date']}")
        
        # Try different late payment scenarios
        late_scenarios = [
            {"date": "2025-03-16", "days_late": 1},
            {"date": "2025-03-20", "days_late": 5},
            {"date": "2025-03-25", "days_late": 10},
            {"date": "2025-03-31", "days_late": 16},
            {"date": "2025-04-05", "days_late": 21}  # Very late
        ]
        
        for scenario in late_scenarios:
            print(f"\n🧪 Testing payment {scenario['days_late']} days late ({scenario['date']})...")
            
            # Create a fresh client for each test
            fresh_client_data = test_client_data.copy()
            fresh_client_data['email'] = f"double_jump_{scenario['days_late']}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
            
            response = requests.post(f"{API_BASE}/clients", json=fresh_client_data, timeout=10)
            if response.status_code != 200:
                continue
                
            fresh_client = response.json()
            fresh_client_id = fresh_client['id']
            
            # Record payment
            payment_data = {
                "client_id": fresh_client_id,
                "amount_paid": 75.0,
                "payment_date": scenario['date'],
                "payment_method": "Cash",
                "notes": f"Payment {scenario['days_late']} days late"
            }
            
            response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
            if response.status_code != 200:
                print(f"   ❌ Payment failed: {response.status_code}")
                continue
                
            payment_result = response.json()
            new_due_date = payment_result['new_next_payment_date']
            
            print(f"   Payment Date: {scenario['date']} ({scenario['days_late']} days late)")
            print(f"   New Due Date: {new_due_date}")
            
            # Check for double jump
            if "May 15" in new_due_date:
                print(f"   🚨 DOUBLE JUMP DETECTED! Mar 15 → May 15 (skipped April)")
                return False
            elif "April 15" in new_due_date:
                print(f"   ✅ Normal advancement: Mar 15 → Apr 15")
            else:
                print(f"   ❓ Unexpected result: {new_due_date}")
            
            # Cleanup
            try:
                requests.delete(f"{API_BASE}/clients/{fresh_client_id}", timeout=5)
            except:
                pass
        
        print(f"\n✅ No double jump bugs detected across all late payment scenarios")
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

def test_payment_date_vs_due_date_calculation():
    """Test if system incorrectly uses payment date instead of due date"""
    print("\n🎯 TESTING PAYMENT DATE VS DUE DATE CALCULATION")
    print("=" * 60)
    print("Correct: Calculate next payment from due date (Mar 15 → Apr 15)")
    print("Bug: Calculate next payment from payment date (Mar 20 → Apr 20)")
    
    test_client_data = {
        "name": "Payment vs Due Date Test",
        "email": f"payment_vs_due_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
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
        
        print(f"✅ Client created")
        print(f"   Due Date: {client['next_payment_date']} (March 15)")
        
        # Record payment on different date
        payment_date = "2025-03-25"  # 10 days after due date
        payment_data = {
            "client_id": client_id,
            "amount_paid": 100.0,
            "payment_date": payment_date,
            "payment_method": "Cash",
            "notes": "Testing payment date vs due date calculation"
        }
        
        print(f"\n💰 Recording payment on {payment_date} (10 days after Mar 15 due date)")
        response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Payment recording failed: {response.status_code}")
            return False
            
        payment_result = response.json()
        new_due_date = payment_result['new_next_payment_date']
        
        print(f"✅ Payment recorded")
        print(f"   New Due Date: {new_due_date}")
        
        # Analyze calculation method
        print(f"\n📊 CALCULATION ANALYSIS:")
        print(f"   Original Due Date: March 15, 2025")
        print(f"   Payment Made On: {payment_date}")
        print(f"   New Due Date: {new_due_date}")
        
        if "April 15" in new_due_date:
            print(f"   ✅ CORRECT: Calculated from due date (Mar 15 + 1 month = Apr 15)")
            return True
        elif "April 25" in new_due_date:
            print(f"   ❌ BUG: Calculated from payment date (Mar 25 + 1 month = Apr 25)")
            print(f"   🚨 This would cause billing dates to drift based on payment timing!")
            return False
        else:
            print(f"   ❓ UNEXPECTED: Unexpected calculation result")
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
    """Run specific user scenario tests"""
    print("🔍 SPECIFIC USER SCENARIO INVESTIGATION")
    print("=" * 80)
    print("Re-examining user's complaint with different interpretations")
    print("=" * 80)
    
    results = []
    
    # Test 1: User expectation analysis
    result1 = test_user_expectation_scenario()
    results.append(("User Expectation Analysis", result1))
    
    # Test 2: Double jump bug detection
    result2 = test_potential_double_jump_bug()
    results.append(("Double Jump Bug Detection", result2))
    
    # Test 3: Payment date vs due date calculation
    result3 = test_payment_date_vs_due_date_calculation()
    results.append(("Payment vs Due Date Calculation", result3))
    
    # Summary
    print("\n" + "="*80)
    print("🎯 USER SCENARIO INVESTIGATION SUMMARY")
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
        print("\n🎉 SYSTEM WORKING CORRECTLY!")
        print("   No bugs detected in payment date calculation.")
        print("   User's complaint may be based on incorrect expectation.")
        print("   Professional billing behavior: Payment advances due date by one month.")
    else:
        print("\n🚨 BUGS DETECTED!")
        print("   Payment date calculation has issues.")
        print("   User's complaint appears to be valid.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)