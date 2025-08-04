#!/usr/bin/env python3
"""
PAYMENT DATE CALCULATION JUMP TEST
==================================

Testing the specific user-reported issue:
1. Client joins Feb 15 → next due date is Mar 15 ✅ (correct)
2. Client pays late → due date goes to Apr 15 ❌ (wrong, should stay Mar 15)

This test focuses on the exact scenario where late payments cause 
the due date to jump ahead by a full extra month instead of maintaining 
the normal cycle.
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

def test_payment_date_jump_scenario():
    """Test the exact scenario reported by the user"""
    print("🎯 TESTING PAYMENT DATE JUMP SCENARIO")
    print("=" * 60)
    
    # Test data
    test_client_data = {
        "name": "Payment Jump Test Client",
        "email": f"payment_jump_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "phone": "+18685551234",
        "membership_type": "Standard",
        "monthly_fee": 55.0,
        "start_date": "2025-02-15",
        "payment_status": "due",
        "auto_reminders_enabled": True
    }
    
    try:
        # STEP 1: Create client with start_date "2025-02-15" and payment_status="due"
        print("\n📝 STEP 1: Creating client with start_date 2025-02-15...")
        response = requests.post(f"{API_BASE}/clients", json=test_client_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Client creation failed: {response.status_code} - {response.text}")
            return False
            
        client = response.json()
        client_id = client['id']
        print(f"✅ Client created successfully: {client['name']}")
        print(f"   Start Date: {client['start_date']}")
        print(f"   Next Payment Date: {client['next_payment_date']}")
        
        # STEP 2: Verify next_payment_date is correctly set to "2025-03-15"
        print("\n🔍 STEP 2: Verifying initial next_payment_date...")
        expected_next_date = "2025-03-15"
        actual_next_date = client['next_payment_date']
        
        if actual_next_date == expected_next_date:
            print(f"✅ Initial payment date correct: {actual_next_date}")
        else:
            print(f"❌ Initial payment date WRONG: Expected {expected_next_date}, got {actual_next_date}")
            return False
        
        # STEP 3: Record a late payment (after March 15th)
        print("\n💰 STEP 3: Recording late payment (after March 15th)...")
        late_payment_date = "2025-03-20"  # 5 days late
        payment_data = {
            "client_id": client_id,
            "amount_paid": 55.0,
            "payment_date": late_payment_date,
            "payment_method": "Cash",
            "notes": "Late payment test"
        }
        
        response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Payment recording failed: {response.status_code} - {response.text}")
            return False
            
        payment_result = response.json()
        print(f"✅ Payment recorded successfully")
        print(f"   Payment Date: {late_payment_date}")
        print(f"   New Next Payment Date: {payment_result['new_next_payment_date']}")
        
        # STEP 4: Check if the new next_payment_date incorrectly jumps to "2025-04-15"
        print("\n🚨 STEP 4: Checking for incorrect date jump...")
        
        # Get updated client data
        response = requests.get(f"{API_BASE}/clients/{client_id}", timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to get updated client: {response.status_code}")
            return False
            
        updated_client = response.json()
        new_next_payment_date = updated_client['next_payment_date']
        
        print(f"   Updated Next Payment Date: {new_next_payment_date}")
        
        # The correct behavior: should be 2025-04-15 (one month from March 15th)
        # The bug would be: jumping to 2025-05-15 or some other incorrect date
        expected_correct_date = "2025-04-15"
        
        if new_next_payment_date == expected_correct_date:
            print(f"✅ Payment date calculation CORRECT: {new_next_payment_date}")
            print("   Late payment did NOT cause incorrect date jump")
            return True
        else:
            print(f"❌ Payment date calculation WRONG!")
            print(f"   Expected: {expected_correct_date}")
            print(f"   Actual: {new_next_payment_date}")
            print("   🚨 CONFIRMED: Late payment caused incorrect date jump!")
            
            # Analyze the jump
            if new_next_payment_date == "2025-05-15":
                print("   📊 Analysis: Date jumped TWO months ahead (Mar 15 → May 15)")
            elif new_next_payment_date == "2025-04-20":
                print("   📊 Analysis: Date calculated from payment date instead of due date")
            else:
                print(f"   📊 Analysis: Unexpected date calculation result")
            
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False
    finally:
        # Cleanup: Delete test client if it was created
        try:
            if 'client_id' in locals():
                requests.delete(f"{API_BASE}/clients/{client_id}", timeout=5)
                print(f"🧹 Cleanup: Test client deleted")
        except:
            pass

def test_multiple_consecutive_payments():
    """Test multiple consecutive payments to see if date drift accumulates"""
    print("\n🔄 TESTING MULTIPLE CONSECUTIVE PAYMENTS")
    print("=" * 60)
    
    test_client_data = {
        "name": "Multiple Payments Test Client",
        "email": f"multi_payments_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
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
        print(f"✅ Client created: {client['name']}")
        print(f"   Initial Next Payment Date: {client['next_payment_date']}")
        
        # Expected payment cycle: Jan 15 → Feb 15 → Mar 15 → Apr 15 → May 15
        expected_dates = ["2025-02-15", "2025-03-15", "2025-04-15", "2025-05-15", "2025-06-15"]
        payment_dates = ["2025-02-18", "2025-03-22", "2025-04-10", "2025-05-20", "2025-06-14"]  # Various late/early payments
        
        for i, (payment_date, expected_next) in enumerate(zip(payment_dates, expected_dates[1:]), 1):
            print(f"\n💰 Payment {i}: Recording payment on {payment_date}")
            
            payment_data = {
                "client_id": client_id,
                "amount_paid": 75.0,
                "payment_date": payment_date,
                "payment_method": "Cash",
                "notes": f"Payment {i} test"
            }
            
            response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
            if response.status_code != 200:
                print(f"❌ Payment {i} failed: {response.status_code}")
                continue
                
            # Get updated client
            response = requests.get(f"{API_BASE}/clients/{client_id}", timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to get updated client after payment {i}")
                continue
                
            updated_client = response.json()
            actual_next = updated_client['next_payment_date']
            
            print(f"   Expected Next: {expected_next}")
            print(f"   Actual Next: {actual_next}")
            
            if actual_next == expected_next:
                print(f"   ✅ Payment {i} date calculation CORRECT")
            else:
                print(f"   ❌ Payment {i} date calculation WRONG!")
                print(f"   🚨 Date drift detected at payment {i}")
                return False
        
        print("\n✅ All consecutive payments maintained correct monthly cycle")
        return True
        
    except Exception as e:
        print(f"❌ Error in consecutive payments test: {str(e)}")
        return False
    finally:
        # Cleanup
        try:
            if 'client_id' in locals():
                requests.delete(f"{API_BASE}/clients/{client_id}", timeout=5)
                print(f"🧹 Cleanup: Test client deleted")
        except:
            pass

def test_edge_case_scenarios():
    """Test edge cases that might cause date calculation issues"""
    print("\n🎯 TESTING EDGE CASE SCENARIOS")
    print("=" * 60)
    
    edge_cases = [
        {
            "name": "Month End Client",
            "start_date": "2025-01-31",
            "expected_next": "2025-02-28",  # Jan 31 → Feb 28 (no Feb 31)
            "payment_date": "2025-03-05",   # Late payment
            "expected_after_payment": "2025-03-28"  # Should be Mar 28, not Apr 5
        },
        {
            "name": "February Client",
            "start_date": "2025-02-28",
            "expected_next": "2025-03-28",  # Feb 28 → Mar 28
            "payment_date": "2025-04-02",   # Late payment
            "expected_after_payment": "2025-04-28"  # Should be Apr 28, not May 2
        },
        {
            "name": "Year Boundary Client",
            "start_date": "2024-12-15",
            "expected_next": "2025-01-15",  # Dec 15 → Jan 15 (year boundary)
            "payment_date": "2025-01-20",   # Late payment
            "expected_after_payment": "2025-02-15"  # Should be Feb 15, not Feb 20
        }
    ]
    
    all_passed = True
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\n🧪 Edge Case {i}: {case['name']}")
        
        test_client_data = {
            "name": f"Edge Case {i} Client",
            "email": f"edge_case_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "phone": f"+1868555123{i}",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": case['start_date'],
            "payment_status": "due",
            "auto_reminders_enabled": True
        }
        
        try:
            # Create client
            response = requests.post(f"{API_BASE}/clients", json=test_client_data, timeout=10)
            if response.status_code != 200:
                print(f"❌ Client creation failed: {response.status_code}")
                all_passed = False
                continue
                
            client = response.json()
            client_id = client['id']
            
            # Check initial next payment date
            actual_initial = client['next_payment_date']
            expected_initial = case['expected_next']
            
            print(f"   Start Date: {case['start_date']}")
            print(f"   Expected Initial Next: {expected_initial}")
            print(f"   Actual Initial Next: {actual_initial}")
            
            if actual_initial != expected_initial:
                print(f"   ❌ Initial date calculation WRONG!")
                all_passed = False
                continue
            else:
                print(f"   ✅ Initial date calculation correct")
            
            # Record late payment
            payment_data = {
                "client_id": client_id,
                "amount_paid": 55.0,
                "payment_date": case['payment_date'],
                "payment_method": "Cash",
                "notes": f"Edge case {i} payment"
            }
            
            response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
            if response.status_code != 200:
                print(f"   ❌ Payment recording failed: {response.status_code}")
                all_passed = False
                continue
            
            # Check next payment date after payment
            response = requests.get(f"{API_BASE}/clients/{client_id}", timeout=10)
            if response.status_code != 200:
                print(f"   ❌ Failed to get updated client")
                all_passed = False
                continue
                
            updated_client = response.json()
            actual_after_payment = updated_client['next_payment_date']
            expected_after_payment = case['expected_after_payment']
            
            print(f"   Payment Date: {case['payment_date']}")
            print(f"   Expected After Payment: {expected_after_payment}")
            print(f"   Actual After Payment: {actual_after_payment}")
            
            if actual_after_payment != expected_after_payment:
                print(f"   ❌ Post-payment date calculation WRONG!")
                print(f"   🚨 Edge case {i} FAILED - Date jump detected!")
                all_passed = False
            else:
                print(f"   ✅ Post-payment date calculation correct")
                
        except Exception as e:
            print(f"   ❌ Error in edge case {i}: {str(e)}")
            all_passed = False
        finally:
            # Cleanup
            try:
                if 'client_id' in locals():
                    requests.delete(f"{API_BASE}/clients/{client_id}", timeout=5)
            except:
                pass
    
    return all_passed

def main():
    """Run all payment date jump tests"""
    print("🚨 PAYMENT DATE CALCULATION JUMP TESTING")
    print("=" * 80)
    print("Testing user-reported issue: Late payments cause due date to jump ahead by full month")
    print("=" * 80)
    
    results = []
    
    # Test 1: Main scenario
    print("\n" + "="*80)
    result1 = test_payment_date_jump_scenario()
    results.append(("Main Scenario Test", result1))
    
    # Test 2: Multiple consecutive payments
    print("\n" + "="*80)
    result2 = test_multiple_consecutive_payments()
    results.append(("Consecutive Payments Test", result2))
    
    # Test 3: Edge cases
    print("\n" + "="*80)
    result3 = test_edge_case_scenarios()
    results.append(("Edge Cases Test", result3))
    
    # Summary
    print("\n" + "="*80)
    print("🎯 PAYMENT DATE JUMP TEST SUMMARY")
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
        print("🎉 ALL TESTS PASSED - Payment date calculation working correctly!")
        print("   No date jump issues detected.")
    else:
        print("🚨 CRITICAL ISSUES DETECTED!")
        print("   Payment date calculation has bugs causing date jumps.")
        print("   User's reported issue is CONFIRMED.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)