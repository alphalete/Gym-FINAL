#!/usr/bin/env python3
"""
Comprehensive Payment Date Calculation Edge Cases Test
=====================================================

This test demonstrates various edge cases where 30-day increments fail
compared to proper monthly calculations.
"""

import requests
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def demonstrate_edge_cases():
    """Demonstrate various edge cases where 30-day calculation fails"""
    print("🔍 PAYMENT DATE CALCULATION EDGE CASES ANALYSIS")
    print("=" * 70)
    print()
    
    edge_cases = [
        {
            "name": "January 31st (Month-end)",
            "start_date": date(2025, 1, 31),
            "description": "Starting at month end - should go to Feb 28th, not March 2nd"
        },
        {
            "name": "February 28th (Non-leap year)",
            "start_date": date(2025, 2, 28),
            "description": "February end in non-leap year"
        },
        {
            "name": "March 31st (31-day month)",
            "start_date": date(2025, 3, 31),
            "description": "31-day month to 30-day month transition"
        },
        {
            "name": "April 30th (30-day month)",
            "start_date": date(2025, 4, 30),
            "description": "30-day month to 31-day month transition"
        },
        {
            "name": "December 31st (Year boundary)",
            "start_date": date(2024, 12, 31),
            "description": "Year boundary crossing"
        }
    ]
    
    for case in edge_cases:
        print(f"CASE: {case['name']}")
        print(f"Description: {case['description']}")
        print(f"Start Date: {case['start_date'].strftime('%B %d, %Y')}")
        print()
        
        # Calculate 5 payments using both methods
        current_date = case['start_date']
        
        print("30-Day Increments (Current System):")
        for i in range(5):
            print(f"  Payment {i+1}: {current_date.strftime('%B %d, %Y')}")
            current_date = current_date + timedelta(days=30)
        
        print()
        print("Proper Monthly Calculation (Expected):")
        current_date = case['start_date']
        for i in range(5):
            print(f"  Payment {i+1}: {current_date.strftime('%B %d, %Y')}")
            # Add one month properly
            if current_date.month == 12:
                next_year = current_date.year + 1
                next_month = 1
            else:
                next_year = current_date.year
                next_month = current_date.month + 1
            
            # Handle day overflow (e.g., Jan 31 → Feb 28)
            try:
                current_date = current_date.replace(year=next_year, month=next_month)
            except ValueError:
                # Day doesn't exist in next month (e.g., Jan 31 → Feb 31)
                # Use the last day of the next month
                if next_month == 2:  # February
                    if next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0):
                        last_day = 29  # Leap year
                    else:
                        last_day = 28  # Non-leap year
                elif next_month in [4, 6, 9, 11]:
                    last_day = 30
                else:
                    last_day = 31
                
                current_date = current_date.replace(year=next_year, month=next_month, day=min(current_date.day, last_day))
        
        print()
        print("-" * 50)
        print()

def test_backend_calculation_function():
    """Test the actual backend calculation function behavior"""
    print("🧪 BACKEND CALCULATION FUNCTION TESTING")
    print("=" * 50)
    print()
    
    test_cases = [
        ("2025-01-15", "Should be February 15th"),
        ("2025-01-31", "Should be February 28th (month-end adjustment)"),
        ("2025-02-28", "Should be March 28th"),
        ("2025-03-31", "Should be April 30th (month-end adjustment)"),
        ("2025-12-31", "Should be January 31st (year boundary)")
    ]
    
    for start_date_str, expected_behavior in test_cases:
        try:
            # Create a temporary client to test the calculation
            client_data = {
                "name": f"Edge Case Test {start_date_str}",
                "email": f"edge_test_{start_date_str.replace('-', '_')}_{datetime.now().strftime('%H%M%S')}@example.com",
                "phone": "+18685551234",
                "membership_type": "Standard",
                "monthly_fee": 55.0,
                "start_date": start_date_str,
                "auto_reminders_enabled": True,
                "payment_status": "paid"  # This will trigger next_payment_date calculation
            }
            
            response = requests.post(f"{API_BASE}/clients", json=client_data, timeout=10)
            
            if response.status_code == 200:
                client = response.json()
                actual_next_date = client['next_payment_date']
                
                # Calculate what it should be with proper monthly arithmetic
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                expected_30_day = (start_date + timedelta(days=30)).strftime('%Y-%m-%d')
                
                print(f"Start Date: {start_date_str}")
                print(f"Expected Behavior: {expected_behavior}")
                print(f"Actual Result: {actual_next_date}")
                print(f"30-Day Calculation: {expected_30_day}")
                
                if actual_next_date == expected_30_day:
                    print("✅ Confirms 30-day calculation is being used")
                else:
                    print("❓ Unexpected result")
                
                # Clean up
                requests.delete(f"{API_BASE}/clients/{client['id']}", timeout=10)
                
            else:
                print(f"❌ Failed to create test client: {response.status_code}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error testing {start_date_str}: {str(e)}")
            print()

def main():
    """Main test execution"""
    demonstrate_edge_cases()
    test_backend_calculation_function()
    
    print("📋 SUMMARY OF FINDINGS")
    print("=" * 30)
    print()
    print("🚨 CONFIRMED ISSUE: The system uses 30-day increments instead of proper monthly calculations")
    print()
    print("📍 ROOT CAUSE: Line 133-134 in backend/server.py:")
    print("   def calculate_next_payment_date(start_date: date) -> date:")
    print("       return start_date + timedelta(days=30)")
    print()
    print("🔧 RECOMMENDED FIX: Replace with proper monthly arithmetic:")
    print("   def calculate_next_payment_date(start_date: date) -> date:")
    print("       if start_date.month == 12:")
    print("           next_year = start_date.year + 1")
    print("           next_month = 1")
    print("       else:")
    print("           next_year = start_date.year")
    print("           next_month = start_date.month + 1")
    print("       ")
    print("       try:")
    print("           return start_date.replace(year=next_year, month=next_month)")
    print("       except ValueError:")
    print("           # Handle month-end cases (e.g., Jan 31 → Feb 28)")
    print("           # Use last day of next month")
    print("           ...")
    print()
    print("💡 IMPACT: This affects all payment date calculations throughout the system")
    print("   - Client creation with payment_status='paid'")
    print("   - Payment recording (/api/payments/record)")
    print("   - Client updates when start_date changes")

if __name__ == "__main__":
    main()