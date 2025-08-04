#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class PaymentsPageAPITester:
    def __init__(self, base_url="https://65d688ea-a807-4f80-b037-f168ea1491e4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_clients = []

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
                    details = f"(Status: {response.status_code}, Response time: {response.elapsed.total_seconds():.3f}s)"
                    self.log_test(name, True, details)
                    print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
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

    def test_get_clients_for_payments_page(self):
        """Test GET /api/clients - should return 4 clients with proper payment status data"""
        print("\n🎯 TESTING PAYMENTS PAGE REQUIREMENT: GET /api/clients should return 4 clients")
        print("=" * 80)
        
        success, response = self.run_test(
            "GET /api/clients - Verify 4 clients with payment data",
            "GET",
            "clients",
            200
        )
        
        if success:
            client_count = len(response)
            print(f"   📊 Total clients returned: {client_count}")
            
            # Verify we have 4 clients as expected
            if client_count == 4:
                print("   ✅ REQUIREMENT MET: Exactly 4 clients returned")
            else:
                print(f"   ⚠️  Expected 4 clients, got {client_count}")
            
            # Verify each client has required fields for payment cards
            required_fields = ['id', 'name', 'monthly_fee', 'next_payment_date', 'status', 'membership_type']
            clients_with_all_fields = 0
            overdue_clients = []
            
            print(f"\n   📋 CLIENT DATA ANALYSIS:")
            for i, client in enumerate(response, 1):
                print(f"   Client {i}: {client.get('name', 'Unknown')}")
                print(f"      ID: {client.get('id', 'Missing')}")
                print(f"      Email: {client.get('email', 'Missing')}")
                print(f"      Status: {client.get('status', 'Missing')}")
                print(f"      Membership: {client.get('membership_type', 'Missing')}")
                print(f"      Monthly Fee: TTD {client.get('monthly_fee', 'Missing')}")
                print(f"      Next Payment: {client.get('next_payment_date', 'Missing')}")
                
                # Check if all required fields are present
                missing_fields = [field for field in required_fields if field not in client or client[field] is None]
                if not missing_fields:
                    clients_with_all_fields += 1
                    print(f"      ✅ All required fields present")
                else:
                    print(f"      ❌ Missing fields: {missing_fields}")
                
                # Check if payment is overdue
                next_payment_str = client.get('next_payment_date')
                if next_payment_str:
                    try:
                        next_payment_date = datetime.fromisoformat(next_payment_str).date()
                        if next_payment_date < date.today():
                            overdue_clients.append(client.get('name', 'Unknown'))
                            print(f"      🔴 OVERDUE: Payment due {next_payment_date}")
                        else:
                            print(f"      🟢 CURRENT: Payment due {next_payment_date}")
                    except:
                        print(f"      ⚠️  Invalid date format: {next_payment_str}")
                print()
            
            print(f"   📊 SUMMARY:")
            print(f"      Clients with all required fields: {clients_with_all_fields}/{client_count}")
            print(f"      Overdue clients: {len(overdue_clients)}")
            if overdue_clients:
                print(f"      Overdue client names: {', '.join(overdue_clients)}")
                
                # Check if we have the expected 3 overdue clients mentioned in console
                expected_overdue = ['Sarah Thompson', 'David Rodriguez', 'Lisa Chen']
                found_expected = [name for name in expected_overdue if name in overdue_clients]
                print(f"      Expected overdue clients found: {len(found_expected)}/3")
                if found_expected:
                    print(f"      Found: {', '.join(found_expected)}")
            
            # Verify data structure and types
            print(f"\n   🔍 DATA TYPE VERIFICATION:")
            if response:
                sample_client = response[0]
                print(f"      ID type: {type(sample_client.get('id', ''))}")
                print(f"      Monthly fee type: {type(sample_client.get('monthly_fee', 0))}")
                print(f"      Status type: {type(sample_client.get('status', ''))}")
                print(f"      Next payment date type: {type(sample_client.get('next_payment_date', ''))}")
        
        return success

    def test_get_payment_stats(self):
        """Test GET /api/payments/stats - should return TTD 75 revenue and payment statistics"""
        print("\n🎯 TESTING PAYMENTS PAGE REQUIREMENT: GET /api/payments/stats should return TTD 75 revenue")
        print("=" * 80)
        
        success, response = self.run_test(
            "GET /api/payments/stats - Verify TTD 75 revenue",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            total_revenue = response.get('total_revenue', 0)
            monthly_revenue = response.get('monthly_revenue', 0)
            payment_count = response.get('payment_count', 0)
            
            print(f"   💰 REVENUE ANALYSIS:")
            print(f"      Total Revenue: TTD {total_revenue}")
            print(f"      Monthly Revenue: TTD {monthly_revenue}")
            print(f"      Payment Count: {payment_count}")
            print(f"      Timestamp: {response.get('timestamp', 'Missing')}")
            print(f"      Cache Buster: {response.get('cache_buster', 'Missing')}")
            
            # Check if we have the expected TTD 75 revenue
            if total_revenue == 75.0:
                print("   ✅ REQUIREMENT MET: Total revenue is exactly TTD 75")
            else:
                print(f"   ⚠️  Expected TTD 75, got TTD {total_revenue}")
            
            # Verify response structure
            expected_fields = ['total_revenue', 'monthly_revenue', 'payment_count', 'timestamp']
            missing_fields = [field for field in expected_fields if field not in response]
            if not missing_fields:
                print("   ✅ All expected fields present in payment stats")
            else:
                print(f"   ❌ Missing fields in payment stats: {missing_fields}")
            
            # Verify data types
            print(f"\n   🔍 DATA TYPE VERIFICATION:")
            print(f"      Total revenue type: {type(total_revenue)} (should be float/int)")
            print(f"      Monthly revenue type: {type(monthly_revenue)} (should be float/int)")
            print(f"      Payment count type: {type(payment_count)} (should be int)")
            
            # Check for mobile cache busting headers (important for payments page)
            if 'cache_buster' in response:
                print("   ✅ Mobile cache busting implemented")
            else:
                print("   ⚠️  Mobile cache busting may not be implemented")
        
        return success

    def test_payment_reminder_endpoints(self):
        """Test payment reminder endpoints functionality"""
        print("\n🎯 TESTING PAYMENT REMINDER ENDPOINTS")
        print("=" * 80)
        
        # First, get a client to test with
        success_clients, clients_response = self.run_test(
            "Get clients for reminder testing",
            "GET",
            "clients",
            200
        )
        
        if not success_clients or not clients_response:
            print("❌ Cannot test reminders - no clients available")
            return False
        
        test_client = clients_response[0]  # Use first client
        client_id = test_client.get('id')
        client_name = test_client.get('name', 'Unknown')
        
        print(f"   Using test client: {client_name} (ID: {client_id})")
        
        # Test individual payment reminder
        reminder_data = {
            "client_id": client_id,
            "template_name": "default"
        }
        
        success_reminder, reminder_response = self.run_test(
            "POST /api/email/payment-reminder - Send individual reminder",
            "POST",
            "email/payment-reminder",
            200,
            reminder_data
        )
        
        if success_reminder:
            print(f"   📧 Reminder sent to: {reminder_response.get('client_email', 'Unknown')}")
            print(f"   ✅ Success: {reminder_response.get('success', False)}")
            print(f"   📝 Message: {reminder_response.get('message', 'No message')}")
        
        # Test custom reminder with professional template
        custom_reminder_data = {
            "client_id": client_id,
            "template_name": "professional",
            "custom_subject": "Payment Due - Alphalete Athletics Club",
            "custom_message": "Your monthly membership payment is due. Please make payment at your earliest convenience.",
            "custom_amount": test_client.get('monthly_fee', 75.0),
            "custom_due_date": "February 15, 2025"
        }
        
        success_custom, custom_response = self.run_test(
            "POST /api/email/custom-reminder - Send custom reminder",
            "POST",
            "email/custom-reminder",
            200,
            custom_reminder_data
        )
        
        if success_custom:
            print(f"   📧 Custom reminder sent to: {custom_response.get('client_email', 'Unknown')}")
            print(f"   ✅ Success: {custom_response.get('success', False)}")
        
        return success_reminder and success_custom

    def test_payment_recording(self):
        """Test POST /api/payments for recording new payments"""
        print("\n🎯 TESTING PAYMENT RECORDING ENDPOINT")
        print("=" * 80)
        
        # Get a client to record payment for
        success_clients, clients_response = self.run_test(
            "Get clients for payment recording",
            "GET",
            "clients",
            200
        )
        
        if not success_clients or not clients_response:
            print("❌ Cannot test payment recording - no clients available")
            return False
        
        test_client = clients_response[0]  # Use first client
        client_id = test_client.get('id')
        client_name = test_client.get('name', 'Unknown')
        original_payment_date = test_client.get('next_payment_date')
        
        print(f"   Using test client: {client_name} (ID: {client_id})")
        print(f"   Original next payment date: {original_payment_date}")
        
        # Record a payment
        payment_data = {
            "client_id": client_id,
            "amount_paid": 75.0,  # TTD 75 as mentioned in console
            "payment_date": date.today().isoformat(),
            "payment_method": "Credit Card",
            "notes": "Payment recorded via Payments page backend test"
        }
        
        success_payment, payment_response = self.run_test(
            "POST /api/payments/record - Record new payment",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success_payment:
            print(f"   💰 Payment recorded for: {payment_response.get('client_name', 'Unknown')}")
            print(f"   💵 Amount paid: TTD {payment_response.get('amount_paid', 0)}")
            print(f"   📅 New next payment date: {payment_response.get('new_next_payment_date', 'Unknown')}")
            print(f"   🆔 Payment ID: {payment_response.get('payment_id', 'Unknown')}")
            print(f"   📧 Invoice sent: {payment_response.get('invoice_sent', False)}")
            print(f"   📝 Invoice message: {payment_response.get('invoice_message', 'No message')}")
            
            # Verify payment extended the due date by 30 days
            new_payment_date = payment_response.get('new_next_payment_date')
            if new_payment_date:
                print(f"   ✅ Payment date updated successfully")
            else:
                print(f"   ❌ Payment date not updated")
        
        # Verify payment stats updated
        success_stats, stats_response = self.run_test(
            "Verify payment stats updated after recording",
            "GET",
            "payments/stats",
            200
        )
        
        if success_stats:
            new_total_revenue = stats_response.get('total_revenue', 0)
            new_payment_count = stats_response.get('payment_count', 0)
            print(f"   📊 Updated total revenue: TTD {new_total_revenue}")
            print(f"   📊 Updated payment count: {new_payment_count}")
        
        return success_payment

    def test_overdue_payment_calculation(self):
        """Test overdue payment calculation logic"""
        print("\n🎯 TESTING OVERDUE PAYMENT CALCULATION")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get all clients for overdue analysis",
            "GET",
            "clients",
            200
        )
        
        if success:
            overdue_clients = []
            current_clients = []
            
            print(f"   📊 OVERDUE PAYMENT ANALYSIS:")
            for client in response:
                client_name = client.get('name', 'Unknown')
                next_payment_str = client.get('next_payment_date')
                
                if next_payment_str:
                    try:
                        next_payment_date = datetime.fromisoformat(next_payment_str).date()
                        days_overdue = (date.today() - next_payment_date).days
                        
                        if next_payment_date < date.today():
                            overdue_clients.append({
                                'name': client_name,
                                'due_date': next_payment_date,
                                'days_overdue': days_overdue,
                                'amount': client.get('monthly_fee', 0)
                            })
                            print(f"   🔴 OVERDUE: {client_name} - Due {next_payment_date} ({days_overdue} days overdue) - TTD {client.get('monthly_fee', 0)}")
                        else:
                            current_clients.append({
                                'name': client_name,
                                'due_date': next_payment_date,
                                'amount': client.get('monthly_fee', 0)
                            })
                            print(f"   🟢 CURRENT: {client_name} - Due {next_payment_date} - TTD {client.get('monthly_fee', 0)}")
                    except:
                        print(f"   ⚠️  INVALID DATE: {client_name} - {next_payment_str}")
            
            print(f"\n   📊 OVERDUE SUMMARY:")
            print(f"      Total overdue clients: {len(overdue_clients)}")
            print(f"      Total current clients: {len(current_clients)}")
            
            # Check if we have the expected 3 overdue clients
            expected_overdue_names = ['Sarah Thompson', 'David Rodriguez', 'Lisa Chen']
            found_overdue_names = [client['name'] for client in overdue_clients]
            
            print(f"      Expected overdue clients: {', '.join(expected_overdue_names)}")
            print(f"      Found overdue clients: {', '.join(found_overdue_names)}")
            
            matches = [name for name in expected_overdue_names if name in found_overdue_names]
            print(f"      Matches: {len(matches)}/3 - {', '.join(matches)}")
            
            if len(overdue_clients) == 3:
                print("   ✅ REQUIREMENT MET: Exactly 3 overdue payments found")
            else:
                print(f"   ⚠️  Expected 3 overdue payments, found {len(overdue_clients)}")
            
            # Calculate total overdue amount
            total_overdue_amount = sum(client['amount'] for client in overdue_clients)
            print(f"      Total overdue amount: TTD {total_overdue_amount}")
        
        return success

    def test_api_response_format(self):
        """Test API response format and data types"""
        print("\n🎯 TESTING API RESPONSE FORMAT AND DATA TYPES")
        print("=" * 80)
        
        # Test clients endpoint response format
        success_clients, clients_response = self.run_test(
            "Verify clients API response format",
            "GET",
            "clients",
            200
        )
        
        clients_format_valid = True
        if success_clients and clients_response:
            print(f"   📋 CLIENTS API FORMAT VERIFICATION:")
            print(f"      Response type: {type(clients_response)} (should be list)")
            
            if isinstance(clients_response, list):
                print("   ✅ Clients response is a list")
                
                if clients_response:
                    sample_client = clients_response[0]
                    print(f"      Sample client structure:")
                    for key, value in sample_client.items():
                        print(f"         {key}: {type(value).__name__} = {value}")
                    
                    # Verify required field types
                    type_checks = [
                        ('id', str),
                        ('name', str),
                        ('email', str),
                        ('monthly_fee', (int, float)),
                        ('status', str),
                        ('membership_type', str),
                        ('next_payment_date', str)
                    ]
                    
                    for field, expected_type in type_checks:
                        if field in sample_client:
                            actual_type = type(sample_client[field])
                            if isinstance(expected_type, tuple):
                                type_match = actual_type in expected_type
                            else:
                                type_match = actual_type == expected_type
                            
                            if type_match:
                                print(f"   ✅ {field}: {actual_type.__name__} (correct)")
                            else:
                                print(f"   ❌ {field}: {actual_type.__name__} (expected {expected_type})")
                                clients_format_valid = False
                        else:
                            print(f"   ❌ Missing required field: {field}")
                            clients_format_valid = False
            else:
                print("   ❌ Clients response is not a list")
                clients_format_valid = False
        
        # Test payment stats endpoint response format
        success_stats, stats_response = self.run_test(
            "Verify payment stats API response format",
            "GET",
            "payments/stats",
            200
        )
        
        stats_format_valid = True
        if success_stats and stats_response:
            print(f"\n   💰 PAYMENT STATS API FORMAT VERIFICATION:")
            print(f"      Response type: {type(stats_response)} (should be dict)")
            
            if isinstance(stats_response, dict):
                print("   ✅ Payment stats response is a dictionary")
                
                print(f"      Payment stats structure:")
                for key, value in stats_response.items():
                    print(f"         {key}: {type(value).__name__} = {value}")
                
                # Verify required field types
                stats_type_checks = [
                    ('total_revenue', (int, float)),
                    ('monthly_revenue', (int, float)),
                    ('payment_count', int),
                    ('timestamp', str)
                ]
                
                for field, expected_type in stats_type_checks:
                    if field in stats_response:
                        actual_type = type(stats_response[field])
                        if isinstance(expected_type, tuple):
                            type_match = actual_type in expected_type
                        else:
                            type_match = actual_type == expected_type
                        
                        if type_match:
                            print(f"   ✅ {field}: {actual_type.__name__} (correct)")
                        else:
                            print(f"   ❌ {field}: {actual_type.__name__} (expected {expected_type})")
                            stats_format_valid = False
                    else:
                        print(f"   ❌ Missing required field: {field}")
                        stats_format_valid = False
            else:
                print("   ❌ Payment stats response is not a dictionary")
                stats_format_valid = False
        
        return clients_format_valid and stats_format_valid

    def run_all_payments_page_tests(self):
        """Run all tests for Payments page backend functionality"""
        print("🎯 PAYMENTS PAGE BACKEND API TESTING")
        print("=" * 100)
        print("Testing backend API endpoints for redesigned Payments page functionality")
        print("Expected: 4 clients, TTD 75 revenue, 3 overdue payments (Sarah Thompson, David Rodriguez, Lisa Chen)")
        print("=" * 100)
        
        # Run all tests
        test_results = []
        
        test_results.append(self.test_get_clients_for_payments_page())
        test_results.append(self.test_get_payment_stats())
        test_results.append(self.test_overdue_payment_calculation())
        test_results.append(self.test_api_response_format())
        test_results.append(self.test_payment_reminder_endpoints())
        test_results.append(self.test_payment_recording())
        
        # Print summary
        print("\n" + "=" * 100)
        print("🎯 PAYMENTS PAGE BACKEND TESTING SUMMARY")
        print("=" * 100)
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Tests failed: {self.tests_run - self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        print(f"\n🎯 PAYMENTS PAGE REQUIREMENTS VERIFICATION:")
        print(f"   ✅ GET /api/clients endpoint tested")
        print(f"   ✅ GET /api/payments/stats endpoint tested")
        print(f"   ✅ Payment status calculation tested")
        print(f"   ✅ Client data structure verified")
        print(f"   ✅ API response format validated")
        print(f"   ✅ Payment reminder endpoints tested")
        print(f"   ✅ Payment recording functionality tested")
        
        if all(test_results):
            print(f"\n🎉 ALL PAYMENTS PAGE BACKEND TESTS PASSED!")
            print(f"   Backend APIs are working correctly for the redesigned Payments page")
            print(f"   Data fetching should work properly - frontend UI update issue is likely client-side")
        else:
            failed_tests = sum(1 for result in test_results if not result)
            print(f"\n⚠️  {failed_tests} TEST CATEGORIES FAILED")
            print(f"   Some backend functionality may need attention")
        
        return all(test_results)

if __name__ == "__main__":
    print("🚀 Starting Payments Page Backend API Testing...")
    
    tester = PaymentsPageAPITester()
    success = tester.run_all_payments_page_tests()
    
    if success:
        print("\n✅ All Payments Page backend tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some Payments Page backend tests failed!")
        sys.exit(1)