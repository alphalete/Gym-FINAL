#!/usr/bin/env python3
"""
Payment Date Calculation Investigation Test
==========================================

This test investigates the reported issue with next payment date calculation.
User reports: "Next payment date calculation is wrong"

Suspected Issue: System uses 30-day increments instead of proper monthly calculations
Expected: January 15th → February 15th → March 15th → April 15th
Current: January 15th → February 14th → March 16th (30-day drift)
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

class PaymentDateCalculationTester:
    def __init__(self):
        self.test_results = []
        self.test_client_id = None
        
    def log_result(self, test_name: str, success: bool, details: str, expected: str = "", actual: str = ""):
        """Log test result with details"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if expected and actual:
            print(f"   Expected: {expected}")
            print(f"   Actual:   {actual}")
        print(f"   Details: {details}")
        print()

    def create_test_client_january_15th(self) -> bool:
        """Create a test client with start date January 15th, 2025"""
        try:
            client_data = {
                "name": "Payment Date Test Client",
                "email": "payment_date_test@example.com",
                "phone": "+18685551234",
                "membership_type": "Standard",
                "monthly_fee": 55.0,
                "start_date": "2025-01-15",  # January 15th as suggested
                "auto_reminders_enabled": True,
                "payment_status": "due"
            }
            
            response = requests.post(f"{API_BASE}/clients", json=client_data, timeout=10)
            
            if response.status_code == 201:
                client = response.json()
                self.test_client_id = client['id']
                
                # Check the initial next_payment_date calculation
                expected_date = "2025-01-15"  # Should be same as start date since payment_status is 'due'
                actual_date = client['next_payment_date']
                
                self.log_result(
                    "Create test client with January 15th start date",
                    True,
                    f"Client created successfully with ID: {self.test_client_id}",
                    expected_date,
                    actual_date
                )
                
                return True
            else:
                self.log_result(
                    "Create test client with January 15th start date",
                    False,
                    f"Failed to create client. Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Create test client with January 15th start date",
                False,
                f"Exception occurred: {str(e)}"
            )
            return False

    def record_payment_and_check_date(self, payment_number: int, payment_date: str, expected_next_date: str) -> bool:
        """Record a payment and check the calculated next payment date"""
        try:
            payment_data = {
                "client_id": self.test_client_id,
                "amount_paid": 55.0,
                "payment_date": payment_date,
                "payment_method": "Cash",
                "notes": f"Payment #{payment_number} - Date calculation test"
            }
            
            response = requests.post(f"{API_BASE}/payments/record", json=payment_data, timeout=10)
            
            if response.status_code == 200:
                payment_result = response.json()
                actual_next_date = payment_result.get('new_next_payment_date', 'Not provided')
                
                # Convert to comparable format
                try:
                    # Parse the actual date and convert to expected format
                    actual_date_obj = datetime.strptime(actual_next_date, "%B %d, %Y").date()
                    expected_date_obj = datetime.strptime(expected_next_date, "%B %d, %Y").date()
                    
                    success = actual_date_obj == expected_date_obj
                    
                    self.log_result(
                        f"Payment #{payment_number} - Next date calculation",
                        success,
                        f"Payment recorded on {payment_date}",
                        expected_next_date,
                        actual_next_date
                    )
                    
                    return success
                    
                except ValueError as ve:
                    self.log_result(
                        f"Payment #{payment_number} - Next date calculation",
                        False,
                        f"Date parsing error: {str(ve)}. Raw response: {actual_next_date}"
                    )
                    return False
                    
            else:
                self.log_result(
                    f"Payment #{payment_number} - Next date calculation",
                    False,
                    f"Failed to record payment. Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                f"Payment #{payment_number} - Next date calculation",
                False,
                f"Exception occurred: {str(e)}"
            )
            return False

    def demonstrate_30_day_vs_monthly_calculation(self):
        """Demonstrate the difference between 30-day and proper monthly calculations"""
        print("=" * 80)
        print("PAYMENT DATE CALCULATION ANALYSIS")
        print("=" * 80)
        
        start_date = date(2025, 1, 15)  # January 15th, 2025
        
        print(f"Starting Date: {start_date.strftime('%B %d, %Y')} (January 15th)")
        print()
        
        print("EXPECTED BEHAVIOR (Proper Monthly Calculation):")
        print("January 15th → February 15th → March 15th → April 15th → May 15th")
        
        # Calculate proper monthly dates
        proper_dates = []
        current_date = start_date
        for i in range(5):
            proper_dates.append(current_date.strftime('%B %d, %Y'))
            # Add one month properly
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                try:
                    current_date = current_date.replace(month=current_date.month + 1)
                except ValueError:
                    # Handle cases like January 31st → February 28th
                    if current_date.month == 1:  # January to February
                        current_date = current_date.replace(month=2, day=min(current_date.day, 28))
                    else:
                        # Handle other month transitions
                        next_month = current_date.month + 1
                        if next_month > 12:
                            next_month = 1
                            current_date = current_date.replace(year=current_date.year + 1)
                        
                        # Get the last day of the next month
                        if next_month in [1, 3, 5, 7, 8, 10, 12]:
                            max_day = 31
                        elif next_month in [4, 6, 9, 11]:
                            max_day = 30
                        else:  # February
                            max_day = 29 if current_date.year % 4 == 0 else 28
                        
                        current_date = current_date.replace(month=next_month, day=min(current_date.day, max_day))
        
        for i, proper_date in enumerate(proper_dates):
            print(f"  Payment {i+1}: {proper_date}")
        
        print()
        print("CURRENT BEHAVIOR (30-Day Increments):")
        
        # Calculate 30-day increments (current system)
        current_date = start_date
        day_increments = []
        for i in range(5):
            day_increments.append(current_date.strftime('%B %d, %Y'))
            current_date = current_date + timedelta(days=30)
        
        for i, day_date in enumerate(day_increments):
            print(f"  Payment {i+1}: {day_date}")
        
        print()
        print("DRIFT ANALYSIS:")
        for i in range(5):
            proper = datetime.strptime(proper_dates[i], '%B %d, %Y').date()
            current = datetime.strptime(day_increments[i], '%B %d, %Y').date()
            drift = (current - proper).days
            
            if drift == 0:
                print(f"  Payment {i+1}: No drift")
            else:
                print(f"  Payment {i+1}: {abs(drift)} day{'s' if abs(drift) != 1 else ''} {'early' if drift < 0 else 'late'}")
        
        print()

    def run_comprehensive_test(self):
        """Run comprehensive payment date calculation test"""
        print("🎯 PAYMENT DATE CALCULATION INVESTIGATION")
        print("=" * 60)
        print()
        
        # First, demonstrate the theoretical difference
        self.demonstrate_30_day_vs_monthly_calculation()
        
        print("LIVE API TESTING:")
        print("=" * 40)
        
        # Create test client
        if not self.create_test_client_january_15th():
            print("❌ Cannot proceed with testing - client creation failed")
            return
        
        # Test multiple payment recordings to show drift
        test_scenarios = [
            {
                "payment_number": 1,
                "payment_date": "2025-01-15",
                "expected_next_date": "February 15, 2025"  # Should be February 15th
            },
            {
                "payment_number": 2,
                "payment_date": "2025-02-14",  # System will likely calculate Feb 14th
                "expected_next_date": "March 15, 2025"   # Should be March 15th
            },
            {
                "payment_number": 3,
                "payment_date": "2025-03-16",  # System will likely calculate Mar 16th
                "expected_next_date": "April 15, 2025"   # Should be April 15th
            }
        ]
        
        success_count = 0
        for scenario in test_scenarios:
            if self.record_payment_and_check_date(
                scenario["payment_number"],
                scenario["payment_date"],
                scenario["expected_next_date"]
            ):
                success_count += 1
        
        # Get final client state
        self.check_final_client_state()
        
        # Cleanup
        self.cleanup_test_client()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len([r for r in self.test_results if 'Next date calculation' in r['test']])
        passed_tests = len([r for r in self.test_results if 'Next date calculation' in r['test'] and r['success']])
        
        print(f"Payment Date Calculation Tests: {passed_tests}/{total_tests} passed")
        
        if passed_tests < total_tests:
            print()
            print("🚨 CRITICAL ISSUE CONFIRMED:")
            print("The system is using 30-day increments instead of proper monthly calculations.")
            print("This causes date drift over time:")
            print("- January 15th → February 14th (1 day early)")
            print("- February 14th → March 16th (1 day late)")
            print("- March 16th → April 15th (back on track by coincidence)")
            print()
            print("RECOMMENDATION:")
            print("Replace the calculate_next_payment_date function to use proper monthly arithmetic")
            print("instead of adding 30 days.")
        else:
            print("✅ Payment date calculations are working correctly!")

    def check_final_client_state(self):
        """Check the final state of the test client"""
        try:
            response = requests.get(f"{API_BASE}/clients/{self.test_client_id}", timeout=10)
            
            if response.status_code == 200:
                client = response.json()
                self.log_result(
                    "Final client state check",
                    True,
                    f"Client next payment date: {client.get('next_payment_date', 'Not found')}"
                )
            else:
                self.log_result(
                    "Final client state check",
                    False,
                    f"Failed to get client. Status: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "Final client state check",
                False,
                f"Exception occurred: {str(e)}"
            )

    def cleanup_test_client(self):
        """Clean up the test client"""
        if self.test_client_id:
            try:
                response = requests.delete(f"{API_BASE}/clients/{self.test_client_id}", timeout=10)
                
                if response.status_code == 200:
                    self.log_result(
                        "Cleanup test client",
                        True,
                        "Test client deleted successfully"
                    )
                else:
                    self.log_result(
                        "Cleanup test client",
                        False,
                        f"Failed to delete client. Status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_result(
                    "Cleanup test client",
                    False,
                    f"Exception occurred: {str(e)}"
                )

def main():
    """Main test execution"""
    tester = PaymentDateCalculationTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()