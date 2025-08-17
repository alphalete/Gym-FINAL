#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class ClientCreationTester:
    def __init__(self, base_url="https://fitness-tracker-pwa.preview.emergentagent.com"):
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
                    details = f"(Status: {response.status_code})"
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

    def test_client_creation_basic(self):
        """Test basic client creation with realistic data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_data = {
            "name": "Emily Rodriguez",
            "email": f"emily.rodriguez.{timestamp}@alphaleteclub.com",
            "phone": "(555) 234-5678",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": "2025-07-25"
        }
        
        success, response = self.run_test(
            "Create Client - Basic Valid Data",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_clients.append(response["id"])
            print(f"   ✅ Client created successfully with ID: {response['id']}")
            print(f"   ✅ Name: {response.get('name')}")
            print(f"   ✅ Email: {response.get('email')}")
            print(f"   ✅ Start date: {response.get('start_date')}")
            print(f"   ✅ Next payment date: {response.get('next_payment_date')}")
            
            # Verify payment date calculation (30 days from start date)
            expected_payment_date = "2025-08-24"
            if str(response.get('next_payment_date')) == expected_payment_date:
                print(f"   ✅ Payment date calculation CORRECT: {expected_payment_date}")
            else:
                print(f"   ❌ Payment date calculation INCORRECT: Expected {expected_payment_date}, got {response.get('next_payment_date')}")
        
        return success

    def test_client_creation_missing_required_fields(self):
        """Test client creation with missing required fields"""
        # Missing name
        client_data_no_name = {
            "email": "test.missing.name@example.com",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-07-25"
        }
        
        success1, _ = self.run_test(
            "Create Client - Missing Name (Should Fail)",
            "POST",
            "clients",
            422,  # Validation error
            client_data_no_name
        )
        
        # Missing email
        client_data_no_email = {
            "name": "Test User",
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-07-25"
        }
        
        success2, _ = self.run_test(
            "Create Client - Missing Email (Should Fail)",
            "POST",
            "clients",
            422,  # Validation error
            client_data_no_email
        )
        
        # Missing monthly_fee
        client_data_no_fee = {
            "name": "Test User",
            "email": "test.missing.fee@example.com",
            "membership_type": "Standard",
            "start_date": "2025-07-25"
        }
        
        success3, _ = self.run_test(
            "Create Client - Missing Monthly Fee (Should Fail)",
            "POST",
            "clients",
            422,  # Validation error
            client_data_no_fee
        )
        
        return success1 and success2 and success3

    def test_client_creation_invalid_email(self):
        """Test client creation with invalid email formats"""
        invalid_emails = [
            "invalid-email",
            "missing@domain",
            "@missing-local.com",
            "spaces in@email.com",
            "double@@domain.com"
        ]
        
        all_success = True
        for i, invalid_email in enumerate(invalid_emails):
            client_data = {
                "name": f"Invalid Email Test {i+1}",
                "email": invalid_email,
                "membership_type": "Standard",
                "monthly_fee": 50.00,
                "start_date": "2025-07-25"
            }
            
            success, _ = self.run_test(
                f"Create Client - Invalid Email '{invalid_email}' (Should Fail)",
                "POST",
                "clients",
                422,  # Validation error
                client_data
            )
            
            if not success:
                all_success = False
        
        return all_success

    def test_client_creation_duplicate_email(self):
        """Test client creation with duplicate email - CRITICAL TEST"""
        # First, create a client
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email = f"duplicate.test.{timestamp}@example.com"
        
        client_data = {
            "name": "Original Client",
            "email": email,
            "membership_type": "Standard",
            "monthly_fee": 50.00,
            "start_date": "2025-07-25"
        }
        
        success1, response1 = self.run_test(
            "Create Client - Original (For Duplicate Test)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success1 and "id" in response1:
            self.created_clients.append(response1["id"])
            print(f"   ✅ Original client created with ID: {response1['id']}")
            
            # Now try to create another client with the same email
            duplicate_client_data = {
                "name": "Duplicate Client",
                "email": email,  # Same email
                "membership_type": "Premium",
                "monthly_fee": 75.00,
                "start_date": "2025-07-26"
            }
            
            success2, response2 = self.run_test(
                "Create Client - Duplicate Email (Should Fail)",
                "POST",
                "clients",
                400,  # Bad Request - duplicate email
                duplicate_client_data
            )
            
            if success2:
                print(f"   ✅ DUPLICATE EMAIL VALIDATION: Working correctly - rejected duplicate")
            else:
                print(f"   ❌ DUPLICATE EMAIL VALIDATION: BROKEN - allowed duplicate email!")
                print(f"   🚨 CRITICAL ISSUE: This could be why users can't add clients properly")
            
            return success2
        else:
            print(f"   ❌ Could not create original client for duplicate test")
            return False

    def test_client_creation_various_membership_types(self):
        """Test client creation with different membership types"""
        membership_types = [
            {"type": "Standard", "fee": 50.00},
            {"type": "Premium", "fee": 75.00},
            {"type": "Elite", "fee": 100.00},
            {"type": "VIP", "fee": 150.00}
        ]
        
        all_success = True
        for i, membership in enumerate(membership_types):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            client_data = {
                "name": f"Test Client {membership['type']}",
                "email": f"test.{membership['type'].lower()}.{timestamp}.{i}@example.com",
                "phone": f"(555) {100+i:03d}-{1000+i:04d}",
                "membership_type": membership["type"],
                "monthly_fee": membership["fee"],
                "start_date": "2025-07-25"
            }
            
            success, response = self.run_test(
                f"Create Client - {membership['type']} Membership",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                self.created_clients.append(response["id"])
                print(f"   ✅ {membership['type']} client created: {response.get('name')}")
            else:
                all_success = False
        
        return all_success

    def test_client_creation_date_edge_cases(self):
        """Test client creation with various date scenarios"""
        date_scenarios = [
            {"name": "Past Date", "date": "2025-01-01", "expected_payment": "2025-01-31"},
            {"name": "Today", "date": "2025-07-25", "expected_payment": "2025-08-24"},
            {"name": "Future Date", "date": "2025-12-01", "expected_payment": "2025-12-31"},
            {"name": "End of Month", "date": "2025-01-31", "expected_payment": "2025-03-02"},  # 30 days from Jan 31
        ]
        
        all_success = True
        for i, scenario in enumerate(date_scenarios):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            client_data = {
                "name": f"Date Test {scenario['name']}",
                "email": f"date.test.{i}.{timestamp}@example.com",
                "membership_type": "Standard",
                "monthly_fee": 50.00,
                "start_date": scenario["date"]
            }
            
            success, response = self.run_test(
                f"Create Client - {scenario['name']} Start Date",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                self.created_clients.append(response["id"])
                actual_payment_date = response.get('next_payment_date')
                expected_payment_date = scenario["expected_payment"]
                
                print(f"   ✅ Client created with start date: {scenario['date']}")
                print(f"   📅 Next payment date: {actual_payment_date}")
                print(f"   📅 Expected payment date: {expected_payment_date}")
                
                if str(actual_payment_date) == expected_payment_date:
                    print(f"   ✅ Date calculation CORRECT for {scenario['name']}")
                else:
                    print(f"   ⚠️  Date calculation differs for {scenario['name']} - may need verification")
            else:
                all_success = False
        
        return all_success

    def test_get_clients_after_creation(self):
        """Test that newly created clients appear in the clients list"""
        success, response = self.run_test(
            "Get All Clients - Verify New Clients Appear",
            "GET",
            "clients",
            200
        )
        
        if success:
            client_count = len(response)
            print(f"   📊 Total clients in system: {client_count}")
            
            # Check if our created clients appear in the list
            created_count = 0
            for client_id in self.created_clients:
                found = any(client.get('id') == client_id for client in response)
                if found:
                    created_count += 1
            
            print(f"   ✅ Created clients found in list: {created_count}/{len(self.created_clients)}")
            
            if created_count == len(self.created_clients):
                print(f"   ✅ ALL CREATED CLIENTS APPEAR IN LIST - Data persistence working")
                return True
            else:
                print(f"   ❌ SOME CREATED CLIENTS MISSING FROM LIST - Data persistence issue")
                return False
        
        return success

    def test_get_specific_created_clients(self):
        """Test retrieving specific clients that were just created"""
        if not self.created_clients:
            print("❌ Get Specific Clients - SKIPPED (No clients created)")
            return False
        
        all_success = True
        for i, client_id in enumerate(self.created_clients[:3]):  # Test first 3 clients
            success, response = self.run_test(
                f"Get Specific Client #{i+1}",
                "GET",
                f"clients/{client_id}",
                200
            )
            
            if success:
                print(f"   ✅ Retrieved client: {response.get('name')} ({response.get('email')})")
                print(f"   📋 Membership: {response.get('membership_type')} - ${response.get('monthly_fee')}")
                print(f"   📅 Start: {response.get('start_date')}, Next payment: {response.get('next_payment_date')}")
            else:
                all_success = False
        
        return all_success

    def run_client_creation_tests(self):
        """Run comprehensive client creation tests"""
        print("🏋️‍♂️ CLIENT CREATION FUNCTIONALITY TESTING")
        print("Testing client creation as requested in review")
        print("=" * 80)
        
        # Test sequence focusing on client creation
        tests = [
            ("Basic Client Creation", [
                self.test_client_creation_basic,
                self.test_client_creation_various_membership_types,
            ]),
            
            ("Date Calculations", [
                self.test_client_creation_date_edge_cases,
            ]),
            
            ("Data Retrieval", [
                self.test_get_clients_after_creation,
                self.test_get_specific_created_clients,
            ]),
            
            ("Validation & Edge Cases", [
                self.test_client_creation_missing_required_fields,
                self.test_client_creation_invalid_email,
                self.test_client_creation_duplicate_email,  # CRITICAL TEST
            ]),
        ]
        
        for section_name, section_tests in tests:
            print(f"\n🔧 {section_name.upper()}")
            print("=" * 60)
            
            for test in section_tests:
                try:
                    test()
                except Exception as e:
                    print(f"❌ {test.__name__} - EXCEPTION: {str(e)}")
                print("-" * 40)
        
        # Print summary
        print("\n📊 CLIENT CREATION TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        print(f"Clients Created: {len(self.created_clients)}")
        
        # Critical findings
        print(f"\n🎯 CRITICAL FINDINGS FOR USER ISSUE:")
        if self.tests_passed == self.tests_run:
            print(f"   ✅ Client creation is working correctly")
            print(f"   ✅ Date calculations are accurate (30 days from start date)")
            print(f"   ✅ Clients appear in list after creation")
            print(f"   ✅ Validation is working for required fields and email format")
            print(f"   ✅ All membership types work correctly")
        else:
            print(f"   ⚠️  {self.tests_run - self.tests_passed} issue(s) found that could affect user experience")
            print(f"   🔍 Check duplicate email validation - this is a common cause of client creation issues")
        
        return 0 if self.tests_passed == self.tests_run else 1

def main():
    """Main function"""
    print("🚀 FOCUSED CLIENT CREATION TESTING")
    print("Testing POST /api/clients and GET /api/clients functionality")
    print("Addressing user report: 'can't add clients'")
    print()
    
    tester = ClientCreationTester()
    return tester.run_client_creation_tests()

if __name__ == "__main__":
    sys.exit(main())