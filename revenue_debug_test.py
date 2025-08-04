#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

class RevenueCalculationDebugger:
    def __init__(self, base_url="https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.all_clients = []
        self.active_clients = []
        self.inactive_clients = []
        self.total_revenue = 0.0
        self.active_revenue = 0.0

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

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
                    details = f"(Status: {response.status_code})"
                    self.log_test(name, True, details)
                    return True, response_data
                except:
                    details = f"(Status: {response.status_code}, No JSON response)"
                    self.log_test(name, True, details)
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    details = f"(Expected {expected_status}, got {response.status_code}) - {error_data}"
                except:
                    details = f"(Expected {expected_status}, got {response.status_code}) - {response.text[:100]}"
                self.log_test(name, False, details)
                return False, {}

        except requests.exceptions.RequestException as e:
            details = f"(Network Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}
        except Exception as e:
            details = f"(Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}

    def get_all_clients(self):
        """Get all clients from the database"""
        print("\n" + "="*80)
        print("🎯 CRITICAL REVENUE CALCULATION DEBUGGING")
        print("="*80)
        print("📊 STEP 1: GET ALL CURRENT CLIENTS")
        
        success, response = self.run_test(
            "Get All Clients",
            "GET",
            "clients",
            200
        )
        
        if success:
            self.all_clients = response
            print(f"\n📈 TOTAL CLIENTS FOUND: {len(self.all_clients)}")
            
            # Separate active and inactive clients
            self.active_clients = [client for client in self.all_clients if client.get('status', 'Active') == 'Active']
            self.inactive_clients = [client for client in self.all_clients if client.get('status', 'Active') != 'Active']
            
            print(f"✅ ACTIVE CLIENTS: {len(self.active_clients)}")
            print(f"⏸️  INACTIVE CLIENTS: {len(self.inactive_clients)}")
            
            return True
        else:
            print("❌ FAILED TO GET CLIENTS - CANNOT PROCEED WITH REVENUE DEBUGGING")
            return False

    def analyze_client_fees(self):
        """Analyze each client's monthly fee and calculate totals"""
        print("\n📊 STEP 2: ANALYZE INDIVIDUAL CLIENT FEES")
        print("-" * 60)
        
        if not self.all_clients:
            print("❌ NO CLIENTS DATA AVAILABLE")
            return False
        
        # Calculate revenue from all clients
        total_all_clients = 0.0
        total_active_clients = 0.0
        
        print("\n🔍 ALL CLIENTS BREAKDOWN:")
        print(f"{'Name':<25} {'Email':<30} {'Fee':<10} {'Status':<10}")
        print("-" * 75)
        
        for i, client in enumerate(self.all_clients, 1):
            name = client.get('name', 'Unknown')[:24]
            email = client.get('email', 'Unknown')[:29]
            monthly_fee = client.get('monthly_fee', 0.0)
            status = client.get('status', 'Active')
            
            print(f"{name:<25} {email:<30} TTD {monthly_fee:<7.2f} {status:<10}")
            
            total_all_clients += monthly_fee
            if status == 'Active':
                total_active_clients += monthly_fee
        
        print("-" * 75)
        print(f"{'TOTAL (ALL CLIENTS)':<55} TTD {total_all_clients:<7.2f}")
        print(f"{'TOTAL (ACTIVE ONLY)':<55} TTD {total_active_clients:<7.2f}")
        
        self.total_revenue = total_all_clients
        self.active_revenue = total_active_clients
        
        print(f"\n💰 REVENUE CALCULATION RESULTS:")
        print(f"   📊 Total Revenue (All Clients): TTD {self.total_revenue:.2f}")
        print(f"   ✅ Active Revenue (Active Only): TTD {self.active_revenue:.2f}")
        
        return True

    def identify_specific_clients(self):
        """Identify the specific clients mentioned in the review request"""
        print("\n📊 STEP 3: IDENTIFY SPECIFIC CLIENTS FROM SCREENSHOT")
        print("-" * 60)
        
        expected_clients = {
            'Tata': 150.0,
            'Deon': 1000.0,
            'Test': 100.0,
            'John': 100.0
        }
        
        found_clients = {}
        total_expected = sum(expected_clients.values())
        
        print(f"\n🔍 SEARCHING FOR EXPECTED CLIENTS:")
        print(f"Expected: Tata (TTD 150) + Deon (TTD 1000) + Test (TTD 100) + John (TTD 100) = TTD {total_expected}")
        
        for client in self.all_clients:
            name = client.get('name', '').lower()
            monthly_fee = client.get('monthly_fee', 0.0)
            status = client.get('status', 'Active')
            
            # Check for matches with expected clients
            for expected_name, expected_fee in expected_clients.items():
                if expected_name.lower() in name:
                    found_clients[expected_name] = {
                        'actual_name': client.get('name'),
                        'actual_fee': monthly_fee,
                        'expected_fee': expected_fee,
                        'status': status,
                        'email': client.get('email', 'Unknown')
                    }
                    print(f"   ✅ Found {expected_name}: {client.get('name')} - TTD {monthly_fee} ({status})")
                    break
        
        # Check for missing clients
        missing_clients = []
        for expected_name in expected_clients:
            if expected_name not in found_clients:
                missing_clients.append(expected_name)
                print(f"   ❌ Missing {expected_name}: Expected TTD {expected_clients[expected_name]}")
        
        # Calculate actual total from found clients
        actual_total_found = sum(client_data['actual_fee'] for client_data in found_clients.values())
        
        print(f"\n📊 SPECIFIC CLIENTS ANALYSIS:")
        print(f"   Expected Total: TTD {total_expected}")
        print(f"   Found Clients Total: TTD {actual_total_found}")
        print(f"   Missing Clients: {missing_clients}")
        
        if actual_total_found != total_expected:
            print(f"   ⚠️  DISCREPANCY: TTD {abs(actual_total_found - total_expected):.2f}")
        
        return found_clients, missing_clients

    def check_dashboard_calculation_source(self):
        """Check if there's a separate dashboard endpoint that calculates revenue"""
        print("\n📊 STEP 4: CHECK DASHBOARD CALCULATION SOURCE")
        print("-" * 60)
        
        # The backend doesn't seem to have a separate dashboard endpoint
        # Revenue is likely calculated on the frontend from the clients data
        print("🔍 ANALYZING REVENUE CALCULATION LOGIC:")
        print("   Backend provides: GET /api/clients")
        print("   Frontend calculates: Sum of monthly_fee for active clients")
        
        print(f"\n💡 EXPECTED DASHBOARD CALCULATION:")
        print(f"   Should show: TTD {self.active_revenue:.2f} (sum of active clients)")
        print(f"   User reports: TTD 2,125.00")
        print(f"   Discrepancy: TTD {abs(2125.00 - self.active_revenue):.2f}")
        
        if abs(2125.00 - self.active_revenue) > 0.01:
            print(f"   🚨 REVENUE CALCULATION ISSUE CONFIRMED!")
            return False
        else:
            print(f"   ✅ Revenue calculation appears correct")
            return True

    def test_payment_impact_on_revenue(self):
        """Test if payment recording affects revenue calculations"""
        print("\n📊 STEP 5: TEST PAYMENT IMPACT ON REVENUE")
        print("-" * 60)
        
        if not self.all_clients:
            print("❌ NO CLIENTS AVAILABLE FOR PAYMENT TEST")
            return False
        
        # Find an active client to test payment recording
        test_client = None
        for client in self.active_clients:
            if client.get('monthly_fee', 0) > 0:
                test_client = client
                break
        
        if not test_client:
            print("❌ NO SUITABLE CLIENT FOUND FOR PAYMENT TEST")
            return False
        
        print(f"🔍 TESTING PAYMENT IMPACT WITH CLIENT: {test_client.get('name')}")
        print(f"   Client ID: {test_client.get('id')}")
        print(f"   Current Monthly Fee: TTD {test_client.get('monthly_fee', 0):.2f}")
        
        # Record a payment
        payment_data = {
            "client_id": test_client.get('id'),
            "amount_paid": 50.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Cash",
            "notes": "Revenue debugging test payment"
        }
        
        success, response = self.run_test(
            "Record Test Payment",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   ✅ Payment recorded successfully")
            print(f"   Amount paid: TTD {response.get('amount_paid', 0):.2f}")
            print(f"   New next payment date: {response.get('new_next_payment_date')}")
            
            # Get clients again to check if monthly_fee changed
            success2, clients_after_payment = self.run_test(
                "Get Clients After Payment",
                "GET",
                "clients",
                200
            )
            
            if success2:
                # Find the same client and check if monthly_fee changed
                updated_client = None
                for client in clients_after_payment:
                    if client.get('id') == test_client.get('id'):
                        updated_client = client
                        break
                
                if updated_client:
                    original_fee = test_client.get('monthly_fee', 0)
                    updated_fee = updated_client.get('monthly_fee', 0)
                    
                    print(f"   Original monthly fee: TTD {original_fee:.2f}")
                    print(f"   Updated monthly fee: TTD {updated_fee:.2f}")
                    
                    if abs(original_fee - updated_fee) > 0.01:
                        print(f"   🚨 PAYMENT RECORDING CHANGED MONTHLY FEE!")
                        print(f"   This could be causing revenue inflation!")
                        return False
                    else:
                        print(f"   ✅ Monthly fee unchanged - payment recording OK")
                        return True
        
        return False

    def find_revenue_discrepancy_source(self):
        """Try to identify the exact source of the TTD 2,125.00 vs TTD 1,350 discrepancy"""
        print("\n📊 STEP 6: FIND REVENUE DISCREPANCY SOURCE")
        print("-" * 60)
        
        reported_dashboard_amount = 2125.00
        expected_amount = 1350.00
        discrepancy = reported_dashboard_amount - expected_amount
        
        print(f"🔍 REVENUE DISCREPANCY ANALYSIS:")
        print(f"   Dashboard shows: TTD {reported_dashboard_amount:.2f}")
        print(f"   Expected (Tata+Deon+Test+John): TTD {expected_amount:.2f}")
        print(f"   Discrepancy: TTD {discrepancy:.2f}")
        print(f"   Actual calculated from all active clients: TTD {self.active_revenue:.2f}")
        
        # Check if there are clients with fees that could explain the discrepancy
        print(f"\n🔍 LOOKING FOR CLIENTS THAT COULD EXPLAIN TTD {discrepancy:.2f} DISCREPANCY:")
        
        potential_sources = []
        for client in self.active_clients:
            fee = client.get('monthly_fee', 0)
            if fee > 0:
                # Check if this client's fee could be part of the discrepancy
                if abs(fee - discrepancy) < 100:  # Within 100 TTD
                    potential_sources.append({
                        'name': client.get('name'),
                        'fee': fee,
                        'email': client.get('email'),
                        'status': client.get('status')
                    })
        
        if potential_sources:
            print(f"   🎯 POTENTIAL SOURCES OF DISCREPANCY:")
            for source in potential_sources:
                print(f"   - {source['name']}: TTD {source['fee']:.2f} ({source['status']})")
        else:
            print(f"   ❌ NO SINGLE CLIENT FEE MATCHES THE DISCREPANCY")
        
        # Check if there are duplicate clients
        print(f"\n🔍 CHECKING FOR DUPLICATE CLIENTS:")
        client_emails = {}
        client_names = {}
        
        for client in self.all_clients:
            email = client.get('email', '').lower()
            name = client.get('name', '').lower()
            
            if email in client_emails:
                client_emails[email].append(client)
            else:
                client_emails[email] = [client]
            
            if name in client_names:
                client_names[name].append(client)
            else:
                client_names[name] = [client]
        
        # Find duplicates
        duplicate_emails = {email: clients for email, clients in client_emails.items() if len(clients) > 1}
        duplicate_names = {name: clients for name, clients in client_names.items() if len(clients) > 1}
        
        if duplicate_emails:
            print(f"   🚨 DUPLICATE EMAILS FOUND:")
            for email, clients in duplicate_emails.items():
                total_fee = sum(c.get('monthly_fee', 0) for c in clients)
                print(f"   - {email}: {len(clients)} clients, Total fee: TTD {total_fee:.2f}")
                for client in clients:
                    print(f"     * {client.get('name')}: TTD {client.get('monthly_fee', 0):.2f} ({client.get('status')})")
        
        if duplicate_names:
            print(f"   🚨 DUPLICATE NAMES FOUND:")
            for name, clients in duplicate_names.items():
                total_fee = sum(c.get('monthly_fee', 0) for c in clients)
                print(f"   - {name}: {len(clients)} clients, Total fee: TTD {total_fee:.2f}")
                for client in clients:
                    print(f"     * {client.get('email')}: TTD {client.get('monthly_fee', 0):.2f} ({client.get('status')})")
        
        return len(duplicate_emails) == 0 and len(duplicate_names) == 0

    def run_comprehensive_revenue_debug(self):
        """Run the complete revenue debugging process"""
        print("\n🚨 CRITICAL REVENUE CALCULATION DEBUGGING STARTED")
        print("="*80)
        print("Issue: Dashboard shows TTD 2,125.00 but individual client fees add up to TTD 1,350")
        print("Expected: Tata (150) + Deon (1000) + Test (100) + John (100) = 1,350")
        print("="*80)
        
        # Step 1: Get all clients
        if not self.get_all_clients():
            return False
        
        # Step 2: Analyze client fees
        if not self.analyze_client_fees():
            return False
        
        # Step 3: Identify specific clients
        found_clients, missing_clients = self.identify_specific_clients()
        
        # Step 4: Check dashboard calculation source
        dashboard_ok = self.check_dashboard_calculation_source()
        
        # Step 5: Test payment impact
        payment_ok = self.test_payment_impact_on_revenue()
        
        # Step 6: Find discrepancy source
        no_duplicates = self.find_revenue_discrepancy_source()
        
        # Final summary
        print("\n" + "="*80)
        print("🎯 REVENUE DEBUGGING SUMMARY")
        print("="*80)
        
        print(f"📊 ACTUAL DATA FOUND:")
        print(f"   Total Clients: {len(self.all_clients)}")
        print(f"   Active Clients: {len(self.active_clients)}")
        print(f"   Inactive Clients: {len(self.inactive_clients)}")
        print(f"   Total Revenue (All): TTD {self.total_revenue:.2f}")
        print(f"   Active Revenue (Active Only): TTD {self.active_revenue:.2f}")
        
        print(f"\n🎯 ISSUE ANALYSIS:")
        print(f"   Dashboard Shows: TTD 2,125.00")
        print(f"   Expected (Screenshot): TTD 1,350.00")
        print(f"   Actual Calculated: TTD {self.active_revenue:.2f}")
        print(f"   Discrepancy: TTD {abs(2125.00 - self.active_revenue):.2f}")
        
        if abs(2125.00 - self.active_revenue) < 0.01:
            print(f"   ✅ DASHBOARD CALCULATION MATCHES BACKEND DATA")
            print(f"   🔍 Issue may be in frontend display or user expectation")
        elif abs(1350.00 - self.active_revenue) < 0.01:
            print(f"   ✅ BACKEND DATA MATCHES EXPECTED AMOUNT")
            print(f"   🚨 Dashboard calculation error in frontend")
        else:
            print(f"   🚨 BACKEND DATA DOESN'T MATCH EITHER AMOUNT")
            print(f"   🔍 Data integrity issue or calculation error")
        
        print(f"\n🔧 RECOMMENDATIONS:")
        if missing_clients:
            print(f"   1. Missing expected clients: {missing_clients}")
            print(f"   2. Check if clients were deleted or renamed")
        
        if not dashboard_ok:
            print(f"   3. Review frontend revenue calculation logic")
            print(f"   4. Check if dashboard is using cached data")
        
        if not payment_ok:
            print(f"   5. Payment recording may be affecting monthly fees")
            print(f"   6. Review payment recording logic")
        
        if not no_duplicates:
            print(f"   7. Duplicate clients found - may cause double counting")
            print(f"   8. Clean up duplicate client records")
        
        print(f"\n📈 SUCCESS RATE: {self.tests_passed}/{self.tests_run} tests passed")
        
        return True

def main():
    """Main function to run revenue debugging"""
    debugger = RevenueCalculationDebugger()
    
    try:
        success = debugger.run_comprehensive_revenue_debug()
        
        if success:
            print(f"\n✅ REVENUE DEBUGGING COMPLETED SUCCESSFULLY")
            print(f"📊 Check the analysis above for the source of the revenue calculation issue")
        else:
            print(f"\n❌ REVENUE DEBUGGING FAILED")
            print(f"🔧 Check network connection and API availability")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Revenue debugging interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Revenue debugging failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())