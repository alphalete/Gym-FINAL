#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class AddMemberFixTester:
    def __init__(self, base_url="https://alphalete-club.emergent.host"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_client_ids = []
        
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

    def test_backend_health_check(self):
        """Test backend API health check"""
        success, response = self.run_test(
            "Backend API Health Check",
            "GET",
            "",
            200
        )
        if success and "message" in response:
            print(f"   Health message: {response['message']}")
        return success

    def test_add_member_backend_availability(self):
        """Test backend availability for Add Member functionality"""
        success, response = self.run_test(
            "Backend Availability for Add Member",
            "GET",
            "health",
            200
        )
        if success:
            print(f"   Backend status: {response.get('status', 'Unknown')}")
            print(f"   Timestamp: {response.get('timestamp', 'Unknown')}")
        return success

    def test_create_member_standard_membership(self):
        """Test creating a new member with Standard membership (TTD 55)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Add Member Test User",
            "email": f"add_member_test_{timestamp}@example.com",
            "phone": "+1868-555-0123",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        success, response = self.run_test(
            "Create Member - Standard Membership (TTD 55)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            print(f"   Created member ID: {response['id']}")
            print(f"   Member name: {response.get('name')}")
            print(f"   Membership type: {response.get('membership_type')}")
            print(f"   Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   Payment status: {response.get('payment_status')}")
            print(f"   Amount owed: TTD {response.get('amount_owed')}")
            
            # Verify payment status logic for unpaid member
            if response.get('payment_status') == 'due' and response.get('amount_owed') == 55.00:
                print("   ✅ Payment status logic working correctly for unpaid member")
            else:
                print("   ❌ Payment status logic incorrect for unpaid member")
                return False
        
        return success

    def test_create_member_premium_membership(self):
        """Test creating a new member with Premium membership (TTD 75)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Premium Member Test",
            "email": f"premium_test_{timestamp}@example.com",
            "phone": "+1868-555-0124",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": date.today().isoformat(),
            "payment_status": "paid"
        }
        
        success, response = self.run_test(
            "Create Member - Premium Membership (TTD 75)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            print(f"   Created member ID: {response['id']}")
            print(f"   Member name: {response.get('name')}")
            print(f"   Membership type: {response.get('membership_type')}")
            print(f"   Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   Payment status: {response.get('payment_status')}")
            print(f"   Amount owed: TTD {response.get('amount_owed')}")
            
            # Verify payment status logic for paid member
            if response.get('payment_status') == 'paid' and response.get('amount_owed') == 0.0:
                print("   ✅ Payment status logic working correctly for paid member")
            else:
                print("   ❌ Payment status logic incorrect for paid member")
                return False
        
        return success

    def test_create_member_elite_membership(self):
        """Test creating a new member with Elite membership (TTD 100)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Elite Member Test",
            "email": f"elite_test_{timestamp}@example.com",
            "phone": "+1868-555-0125",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        success, response = self.run_test(
            "Create Member - Elite Membership (TTD 100)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            print(f"   Created member ID: {response['id']}")
            print(f"   Member name: {response.get('name')}")
            print(f"   Membership type: {response.get('membership_type')}")
            print(f"   Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   Payment status: {response.get('payment_status')}")
            print(f"   Amount owed: TTD {response.get('amount_owed')}")
        
        return success

    def test_create_member_vip_membership(self):
        """Test creating a new member with VIP membership (TTD 150)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "VIP Member Test",
            "email": f"vip_test_{timestamp}@example.com",
            "phone": "+1868-555-0126",
            "membership_type": "VIP",
            "monthly_fee": 150.00,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        success, response = self.run_test(
            "Create Member - VIP Membership (TTD 150)",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            print(f"   Created member ID: {response['id']}")
            print(f"   Member name: {response.get('name')}")
            print(f"   Membership type: {response.get('membership_type')}")
            print(f"   Monthly fee: TTD {response.get('monthly_fee')}")
            print(f"   Payment status: {response.get('payment_status')}")
            print(f"   Amount owed: TTD {response.get('amount_owed')}")
        
        return success

    def test_member_data_persistence(self):
        """Test that created members persist in the database"""
        success, response = self.run_test(
            "Verify Member Data Persistence",
            "GET",
            "clients",
            200
        )
        
        if success:
            print(f"   Total members in database: {len(response)}")
            
            # Check if our created members are in the list
            created_members_found = 0
            for client in response:
                if client.get('id') in self.created_client_ids:
                    created_members_found += 1
                    print(f"   Found created member: {client.get('name')} ({client.get('membership_type')})")
            
            if created_members_found == len(self.created_client_ids):
                print(f"   ✅ All {created_members_found} created members found in database")
            else:
                print(f"   ❌ Only {created_members_found}/{len(self.created_client_ids)} created members found")
                return False
        
        return success

    def test_member_retrieval_by_id(self):
        """Test retrieving individual members by ID"""
        if not self.created_client_ids:
            print("❌ Member Retrieval by ID - SKIPPED (No member IDs available)")
            return False
        
        all_success = True
        for i, client_id in enumerate(self.created_client_ids):
            success, response = self.run_test(
                f"Retrieve Member by ID #{i+1}",
                "GET",
                f"clients/{client_id}",
                200
            )
            
            if success:
                print(f"   Retrieved member: {response.get('name')}")
                print(f"   Email: {response.get('email')}")
                print(f"   Membership: {response.get('membership_type')} - TTD {response.get('monthly_fee')}")
                print(f"   Status: {response.get('status')}")
                print(f"   Payment status: {response.get('payment_status')}")
            else:
                all_success = False
        
        return all_success

    def test_duplicate_email_validation(self):
        """Test that duplicate email addresses are properly rejected"""
        if not self.created_client_ids:
            print("❌ Duplicate Email Validation - SKIPPED (No existing members)")
            return False
        
        # Get the first created member's email
        success, first_member = self.run_test(
            "Get First Member for Duplicate Test",
            "GET",
            f"clients/{self.created_client_ids[0]}",
            200
        )
        
        if not success:
            return False
        
        duplicate_email = first_member.get('email')
        
        # Try to create a new member with the same email
        duplicate_client_data = {
            "name": "Duplicate Email Test",
            "email": duplicate_email,
            "phone": "+1868-555-9999",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": date.today().isoformat()
        }
        
        success, response = self.run_test(
            "Create Member with Duplicate Email (Should Fail)",
            "POST",
            "clients",
            400,  # Expecting 400 Bad Request
            duplicate_client_data
        )
        
        if success:
            print(f"   ✅ Duplicate email properly rejected: {duplicate_email}")
        
        return success

    def test_invalid_email_validation(self):
        """Test that invalid email formats are properly rejected"""
        invalid_client_data = {
            "name": "Invalid Email Test",
            "email": "invalid-email-format",
            "phone": "+1868-555-8888",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": date.today().isoformat()
        }
        
        success, response = self.run_test(
            "Create Member with Invalid Email (Should Fail)",
            "POST",
            "clients",
            422,  # Expecting 422 Validation Error
            invalid_client_data
        )
        
        if success:
            print("   ✅ Invalid email format properly rejected")
        
        return success

    def test_payment_date_calculation(self):
        """Test that next payment dates are calculated correctly"""
        if not self.created_client_ids:
            print("❌ Payment Date Calculation - SKIPPED (No member IDs available)")
            return False
        
        # Test with a specific start date
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_date = "2025-01-15"
        expected_payment_date = "2025-02-14"  # 30 days later
        
        client_data = {
            "name": "Payment Date Test",
            "email": f"payment_date_test_{timestamp}@example.com",
            "phone": "+1868-555-7777",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": start_date
        }
        
        success, response = self.run_test(
            "Test Payment Date Calculation",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.created_client_ids.append(response["id"])
            actual_payment_date = str(response.get('next_payment_date'))
            
            print(f"   Start date: {start_date}")
            print(f"   Expected payment date: {expected_payment_date}")
            print(f"   Actual payment date: {actual_payment_date}")
            
            if actual_payment_date == expected_payment_date:
                print("   ✅ Payment date calculation is CORRECT!")
            else:
                print("   ❌ Payment date calculation is INCORRECT!")
                return False
        
        return success

    def test_backend_error_handling(self):
        """Test backend error handling scenarios"""
        print("\n--- Testing Backend Error Handling ---")
        
        # Test creating member with missing required fields
        incomplete_data = {
            "name": "Incomplete Member",
            # Missing email, membership_type, monthly_fee, start_date
        }
        
        success1, _ = self.run_test(
            "Create Member with Missing Fields (Should Fail)",
            "POST",
            "clients",
            422,  # Validation error
            incomplete_data
        )
        
        # Test retrieving non-existent member
        success2, _ = self.run_test(
            "Get Non-existent Member (Should Fail)",
            "GET",
            "clients/non-existent-id",
            404
        )
        
        # Test with invalid membership type
        invalid_membership_data = {
            "name": "Invalid Membership Test",
            "email": f"invalid_membership_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "phone": "+1868-555-6666",
            "membership_type": "NonExistentMembership",
            "monthly_fee": 55.00,
            "start_date": date.today().isoformat()
        }
        
        # This should still succeed as backend doesn't validate membership types strictly
        success3, _ = self.run_test(
            "Create Member with Invalid Membership Type",
            "POST",
            "clients",
            200,  # Should succeed but with warning
            invalid_membership_data
        )
        
        return success1 and success2 and success3

    def test_backend_performance(self):
        """Test backend performance for Add Member operations"""
        print("\n--- Testing Backend Performance ---")
        
        start_time = datetime.now()
        
        # Create multiple members quickly to test performance
        performance_test_count = 3
        successful_creates = 0
        
        for i in range(performance_test_count):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            client_data = {
                "name": f"Performance Test Member {i+1}",
                "email": f"perf_test_{i+1}_{timestamp}@example.com",
                "phone": f"+1868-555-{1000+i:04d}",
                "membership_type": "Standard",
                "monthly_fee": 55.00,
                "start_date": date.today().isoformat()
            }
            
            success, response = self.run_test(
                f"Performance Test - Create Member {i+1}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                self.created_client_ids.append(response["id"])
                successful_creates += 1
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print(f"\n📊 Performance Test Results:")
        print(f"   Total members created: {successful_creates}/{performance_test_count}")
        print(f"   Total time: {total_time:.2f} seconds")
        print(f"   Average time per member: {total_time/performance_test_count:.2f} seconds")
        
        if successful_creates == performance_test_count and total_time < 30:
            print("   ✅ Backend performance is ACCEPTABLE")
            return True
        else:
            print("   ❌ Backend performance is POOR")
            return False

    def test_data_consistency(self):
        """Test data consistency across multiple API calls"""
        if not self.created_client_ids:
            print("❌ Data Consistency Test - SKIPPED (No member IDs available)")
            return False
        
        # Get all clients multiple times and verify consistency
        all_consistent = True
        
        for attempt in range(3):
            success, response = self.run_test(
                f"Data Consistency Check #{attempt+1}",
                "GET",
                "clients",
                200
            )
            
            if success:
                current_count = len(response)
                if attempt == 0:
                    initial_count = current_count
                    print(f"   Initial member count: {initial_count}")
                else:
                    if current_count != initial_count:
                        print(f"   ❌ Data inconsistency detected: {current_count} vs {initial_count}")
                        all_consistent = False
                    else:
                        print(f"   ✅ Data consistent: {current_count} members")
            else:
                all_consistent = False
        
        return all_consistent

    def run_all_tests(self):
        """Run all Add Member functionality tests"""
        print("🎯 ALPHALETE CLUB PWA - ADD MEMBER FUNCTIONALITY BACKEND TESTING")
        print("=" * 80)
        print("Testing the backend API endpoints that support the Add Member functionality")
        print("Focus: Backend availability, member creation, data persistence, and error handling")
        print("=" * 80)
        
        # Core functionality tests
        tests = [
            self.test_backend_health_check,
            self.test_add_member_backend_availability,
            self.test_create_member_standard_membership,
            self.test_create_member_premium_membership,
            self.test_create_member_elite_membership,
            self.test_create_member_vip_membership,
            self.test_member_data_persistence,
            self.test_member_retrieval_by_id,
            self.test_duplicate_email_validation,
            self.test_invalid_email_validation,
            self.test_payment_date_calculation,
            self.test_backend_error_handling,
            self.test_backend_performance,
            self.test_data_consistency,
        ]
        
        print(f"\n🚀 Starting {len(tests)} backend tests...\n")
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
                self.tests_run += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 ADD MEMBER FUNCTIONALITY BACKEND TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.created_client_ids:
            print(f"\nCreated {len(self.created_client_ids)} test members during testing:")
            for i, client_id in enumerate(self.created_client_ids):
                print(f"  {i+1}. Member ID: {client_id}")
        
        print("\n🔍 KEY FINDINGS:")
        if self.tests_passed == self.tests_run:
            print("✅ ALL BACKEND TESTS PASSED!")
            print("✅ Add Member backend functionality is working correctly")
            print("✅ Backend API endpoints are available and responsive")
            print("✅ Member creation, validation, and persistence working properly")
            print("✅ Error handling is functioning as expected")
        else:
            print("❌ SOME BACKEND TESTS FAILED!")
            print("❌ Add Member backend functionality has issues")
            print("❌ Review failed tests above for specific problems")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = AddMemberFixTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)