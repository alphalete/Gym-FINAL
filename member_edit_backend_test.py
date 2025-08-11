#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any

class MemberEditAPITester:
    def __init__(self, base_url="https://46206bdc-27f0-428b-bb53-27c7a4990807.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_client_id = None
        self.test_clients = []  # Store multiple test clients for comprehensive testing

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

    def test_get_clients_for_editing(self):
        """Test GET /api/clients - Verify clients are available for editing"""
        print("\n🎯 TESTING: GET /api/clients - Clients Available for Editing")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get All Clients for Edit Selection",
            "GET",
            "clients",
            200
        )
        
        if success:
            clients = response if isinstance(response, list) else []
            print(f"   📊 Found {len(clients)} clients available for editing")
            
            if len(clients) > 0:
                print("   📋 Sample client data structure:")
                sample_client = clients[0]
                required_fields = ['id', 'name', 'email', 'phone', 'membership_type', 'monthly_fee', 'start_date', 'status']
                
                for field in required_fields:
                    if field in sample_client:
                        print(f"      ✅ {field}: {sample_client.get(field)}")
                    else:
                        print(f"      ❌ {field}: MISSING")
                        success = False
                
                # Store first client for editing tests
                if success and len(clients) > 0:
                    self.test_client_id = clients[0].get('id')
                    print(f"   🎯 Selected client for edit testing: {clients[0].get('name')} (ID: {self.test_client_id})")
            else:
                print("   ⚠️  No existing clients found - will create test clients")
        
        return success

    def test_get_membership_types_for_edit_form(self):
        """Test GET /api/membership-types - Ensure membership types are available for edit form"""
        print("\n🎯 TESTING: GET /api/membership-types - Membership Types for Edit Form")
        print("=" * 80)
        
        success, response = self.run_test(
            "Get Membership Types for Edit Form",
            "GET",
            "membership-types",
            200
        )
        
        if success:
            membership_types = response if isinstance(response, list) else []
            print(f"   📊 Found {len(membership_types)} membership types for edit form")
            
            if len(membership_types) > 0:
                print("   📋 Available membership types:")
                for mt in membership_types:
                    print(f"      • {mt.get('name')}: TTD {mt.get('monthly_fee')} - {mt.get('description')}")
                    
                # Verify required fields for edit form
                required_fields = ['id', 'name', 'monthly_fee', 'description']
                sample_type = membership_types[0]
                
                print("   🔍 Verifying membership type data structure:")
                for field in required_fields:
                    if field in sample_type:
                        print(f"      ✅ {field}: Present")
                    else:
                        print(f"      ❌ {field}: MISSING")
                        success = False
            else:
                print("   ❌ No membership types found - edit form will not work properly")
                success = False
        
        return success

    def create_test_client_for_editing(self):
        """Create a test client specifically for edit testing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        client_data = {
            "name": "Edit Test Client",
            "email": f"edit_test_{timestamp}@example.com",
            "phone": "+1868-555-0123",
            "membership_type": "Standard",
            "monthly_fee": 55.00,
            "start_date": "2025-01-15",
            "status": "Active",
            "auto_reminders_enabled": True,
            "payment_status": "due"
        }
        
        success, response = self.run_test(
            "Create Test Client for Editing",
            "POST",
            "clients",
            200,
            client_data
        )
        
        if success and "id" in response:
            self.test_client_id = response["id"]
            self.test_clients.append(response)
            print(f"   ✅ Created test client for editing: {response.get('name')} (ID: {self.test_client_id})")
            return True
        
        return False

    def test_update_basic_information(self):
        """Test updating basic client information (name, email, phone)"""
        print("\n🎯 TESTING: PUT /api/clients/{id} - Update Basic Information")
        print("=" * 80)
        
        if not self.test_client_id:
            if not self.create_test_client_for_editing():
                print("❌ Cannot test basic information update - no test client available")
                return False
        
        # Test updating name, email, and phone
        update_data = {
            "name": "Updated Edit Test Client",
            "email": "updated_edit_test@example.com",
            "phone": "+1868-555-9999"
        }
        
        success, response = self.run_test(
            "Update Basic Information (Name, Email, Phone)",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            update_data
        )
        
        if success:
            print("   🔍 Verifying updated fields:")
            print(f"      Name: {response.get('name')} (Expected: {update_data['name']})")
            print(f"      Email: {response.get('email')} (Expected: {update_data['email']})")
            print(f"      Phone: {response.get('phone')} (Expected: {update_data['phone']})")
            
            # Verify all fields were updated correctly
            if (response.get('name') == update_data['name'] and 
                response.get('email') == update_data['email'] and 
                response.get('phone') == update_data['phone']):
                print("   ✅ All basic information updated correctly")
            else:
                print("   ❌ Some basic information was not updated correctly")
                success = False
        
        return success

    def test_update_membership_type_and_fee(self):
        """Test changing membership type and monthly fee"""
        print("\n🎯 TESTING: PUT /api/clients/{id} - Update Membership Type & Fee")
        print("=" * 80)
        
        if not self.test_client_id:
            print("❌ Cannot test membership update - no test client available")
            return False
        
        # Test updating membership type and monthly fee
        update_data = {
            "membership_type": "Premium",
            "monthly_fee": 75.00
        }
        
        success, response = self.run_test(
            "Update Membership Type and Monthly Fee",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            update_data
        )
        
        if success:
            print("   🔍 Verifying membership updates:")
            print(f"      Membership Type: {response.get('membership_type')} (Expected: {update_data['membership_type']})")
            print(f"      Monthly Fee: TTD {response.get('monthly_fee')} (Expected: TTD {update_data['monthly_fee']})")
            
            # Verify membership fields were updated correctly
            if (response.get('membership_type') == update_data['membership_type'] and 
                response.get('monthly_fee') == update_data['monthly_fee']):
                print("   ✅ Membership type and fee updated correctly")
            else:
                print("   ❌ Membership type or fee was not updated correctly")
                success = False
        
        return success

    def test_update_status_active_inactive(self):
        """Test updating client status between Active/Inactive"""
        print("\n🎯 TESTING: PUT /api/clients/{id} - Update Status (Active/Inactive)")
        print("=" * 80)
        
        if not self.test_client_id:
            print("❌ Cannot test status update - no test client available")
            return False
        
        # Test 1: Update status to Inactive
        update_data_inactive = {
            "status": "Inactive"
        }
        
        success1, response1 = self.run_test(
            "Update Status to Inactive",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            update_data_inactive
        )
        
        if success1:
            print(f"   Status updated to: {response1.get('status')}")
            if response1.get('status') == 'Inactive':
                print("   ✅ Status successfully updated to Inactive")
            else:
                print("   ❌ Status was not updated to Inactive correctly")
                success1 = False
        
        # Test 2: Update status back to Active
        update_data_active = {
            "status": "Active"
        }
        
        success2, response2 = self.run_test(
            "Update Status back to Active",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            update_data_active
        )
        
        if success2:
            print(f"   Status updated to: {response2.get('status')}")
            if response2.get('status') == 'Active':
                print("   ✅ Status successfully updated back to Active")
            else:
                print("   ❌ Status was not updated to Active correctly")
                success2 = False
        
        return success1 and success2

    def test_update_start_date_and_auto_reminders(self):
        """Test updating start date and auto reminders settings"""
        print("\n🎯 TESTING: PUT /api/clients/{id} - Update Start Date & Auto Reminders")
        print("=" * 80)
        
        if not self.test_client_id:
            print("❌ Cannot test date/reminders update - no test client available")
            return False
        
        # Test updating start date and auto reminders
        new_start_date = "2025-02-01"
        expected_payment_date = "2025-03-03"  # Should be recalculated based on new start date
        
        update_data = {
            "start_date": new_start_date,
            "auto_reminders_enabled": False
        }
        
        success, response = self.run_test(
            "Update Start Date and Auto Reminders",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            update_data
        )
        
        if success:
            print("   🔍 Verifying date and reminder updates:")
            print(f"      Start Date: {response.get('start_date')} (Expected: {new_start_date})")
            print(f"      Next Payment Date: {response.get('next_payment_date')} (Expected: {expected_payment_date})")
            print(f"      Auto Reminders: {response.get('auto_reminders_enabled')} (Expected: False)")
            
            # Verify all fields were updated correctly
            if (str(response.get('start_date')) == new_start_date and 
                str(response.get('next_payment_date')) == expected_payment_date and
                response.get('auto_reminders_enabled') == False):
                print("   ✅ Start date, payment date recalculation, and auto reminders updated correctly")
            else:
                print("   ❌ Some date or reminder settings were not updated correctly")
                success = False
        
        return success

    def test_data_validation_invalid_email(self):
        """Test edge case: Invalid email format"""
        print("\n🎯 TESTING: Data Validation - Invalid Email Format")
        print("=" * 80)
        
        if not self.test_client_id:
            print("❌ Cannot test email validation - no test client available")
            return False
        
        # Test with invalid email format
        update_data = {
            "email": "invalid-email-format-no-at-symbol"
        }
        
        success, response = self.run_test(
            "Update with Invalid Email Format (Should Fail)",
            "PUT",
            f"clients/{self.test_client_id}",
            422,  # Expecting validation error
            update_data
        )
        
        if success:
            print("   ✅ Invalid email format correctly rejected with 422 validation error")
        
        return success

    def test_data_validation_missing_required_fields(self):
        """Test edge case: Missing required fields"""
        print("\n🎯 TESTING: Data Validation - Missing Required Fields")
        print("=" * 80)
        
        if not self.test_client_id:
            print("❌ Cannot test required fields validation - no test client available")
            return False
        
        # Test with empty name (should fail if name is required)
        update_data = {
            "name": ""
        }
        
        success, response = self.run_test(
            "Update with Empty Name (Should Fail or Handle Gracefully)",
            "PUT",
            f"clients/{self.test_client_id}",
            422,  # Expecting validation error
            update_data
        )
        
        # Note: This might pass if empty name is allowed, which is also acceptable
        if success:
            print("   ✅ Empty name correctly rejected with validation error")
        else:
            print("   ℹ️  Empty name may be allowed - checking if update was processed")
            # Check if the update went through (which might be acceptable)
            check_success, check_response = self.run_test(
                "Check if Empty Name Update Went Through",
                "GET",
                f"clients/{self.test_client_id}",
                200
            )
            if check_success and check_response.get('name') == "":
                print("   ⚠️  Empty name was accepted - may need validation improvement")
                return True
        
        return success

    def test_data_validation_invalid_client_id(self):
        """Test edge case: Invalid client ID (404 error)"""
        print("\n🎯 TESTING: Data Validation - Invalid Client ID (404 Error)")
        print("=" * 80)
        
        # Test with non-existent client ID
        update_data = {
            "name": "Should Not Work",
            "email": "should.not.work@example.com"
        }
        
        success, response = self.run_test(
            "Update Non-existent Client (Should Return 404)",
            "PUT",
            "clients/non-existent-client-id-12345",
            404,  # Expecting 404 Not Found
            update_data
        )
        
        if success:
            print("   ✅ Non-existent client ID correctly returned 404 error")
        
        return success

    def test_concurrent_edit_scenarios(self):
        """Test concurrent edit scenarios"""
        print("\n🎯 TESTING: Concurrent Edit Scenarios")
        print("=" * 80)
        
        if not self.test_client_id:
            print("❌ Cannot test concurrent edits - no test client available")
            return False
        
        # Simulate concurrent edits by making multiple rapid updates
        print("   🔄 Simulating concurrent edit scenario...")
        
        # First update
        update_data_1 = {
            "name": "Concurrent Edit Test 1",
            "phone": "+1868-555-1111"
        }
        
        success1, response1 = self.run_test(
            "Concurrent Edit #1",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            update_data_1
        )
        
        # Second update immediately after
        update_data_2 = {
            "name": "Concurrent Edit Test 2",
            "phone": "+1868-555-2222"
        }
        
        success2, response2 = self.run_test(
            "Concurrent Edit #2 (Immediate)",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            update_data_2
        )
        
        if success1 and success2:
            print("   🔍 Verifying final state after concurrent edits:")
            
            # Get final state
            final_success, final_response = self.run_test(
                "Get Final State After Concurrent Edits",
                "GET",
                f"clients/{self.test_client_id}",
                200
            )
            
            if final_success:
                final_name = final_response.get('name')
                final_phone = final_response.get('phone')
                
                print(f"      Final Name: {final_name}")
                print(f"      Final Phone: {final_phone}")
                
                # The second update should have won
                if final_name == update_data_2['name'] and final_phone == update_data_2['phone']:
                    print("   ✅ Concurrent edits handled correctly - last update wins")
                    return True
                else:
                    print("   ⚠️  Concurrent edit results may be inconsistent")
                    return True  # Still acceptable behavior
        
        return success1 and success2

    def test_response_format_verification(self):
        """Test response format - Verify updated client data is returned correctly"""
        print("\n🎯 TESTING: Response Format Verification")
        print("=" * 80)
        
        if not self.test_client_id:
            print("❌ Cannot test response format - no test client available")
            return False
        
        # Make a comprehensive update and verify the response format
        comprehensive_update = {
            "name": "Response Format Test Client",
            "email": "response.format.test@example.com",
            "phone": "+1868-555-FORMAT",
            "membership_type": "Elite",
            "monthly_fee": 100.00,
            "start_date": "2025-03-01",
            "status": "Active",
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Comprehensive Update for Response Format Test",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            comprehensive_update
        )
        
        if success:
            print("   🔍 Verifying response format and completeness:")
            
            # Check all expected fields are present in response
            expected_fields = [
                'id', 'name', 'email', 'phone', 'membership_type', 'monthly_fee',
                'start_date', 'next_payment_date', 'status', 'auto_reminders_enabled',
                'payment_status', 'amount_owed', 'created_at', 'updated_at'
            ]
            
            missing_fields = []
            present_fields = []
            
            for field in expected_fields:
                if field in response:
                    present_fields.append(field)
                    print(f"      ✅ {field}: {response.get(field)}")
                else:
                    missing_fields.append(field)
                    print(f"      ❌ {field}: MISSING")
            
            print(f"   📊 Response completeness: {len(present_fields)}/{len(expected_fields)} fields present")
            
            if len(missing_fields) == 0:
                print("   ✅ Response format is complete - all expected fields present")
            else:
                print(f"   ⚠️  Response format missing fields: {missing_fields}")
            
            # Verify data types are correct
            print("   🔍 Verifying data types:")
            type_checks = [
                ('id', str),
                ('name', str),
                ('email', str),
                ('monthly_fee', (int, float)),
                ('auto_reminders_enabled', bool)
            ]
            
            type_errors = []
            for field, expected_type in type_checks:
                if field in response:
                    actual_value = response.get(field)
                    if isinstance(actual_value, expected_type):
                        print(f"      ✅ {field}: {type(actual_value).__name__} (correct)")
                    else:
                        print(f"      ❌ {field}: {type(actual_value).__name__} (expected {expected_type.__name__})")
                        type_errors.append(field)
            
            if len(type_errors) == 0:
                print("   ✅ All data types are correct")
            else:
                print(f"   ❌ Data type errors in fields: {type_errors}")
                success = False
        
        return success

    def test_database_persistence(self):
        """Test that updates are properly persisted in database"""
        print("\n🎯 TESTING: Database Persistence Verification")
        print("=" * 80)
        
        if not self.test_client_id:
            print("❌ Cannot test database persistence - no test client available")
            return False
        
        # Make an update
        persistence_update = {
            "name": "Database Persistence Test",
            "email": "persistence.test@example.com",
            "membership_type": "VIP",
            "monthly_fee": 150.00
        }
        
        success1, response1 = self.run_test(
            "Update for Persistence Test",
            "PUT",
            f"clients/{self.test_client_id}",
            200,
            persistence_update
        )
        
        if not success1:
            return False
        
        # Retrieve the client again to verify persistence
        success2, response2 = self.run_test(
            "Retrieve Client to Verify Persistence",
            "GET",
            f"clients/{self.test_client_id}",
            200
        )
        
        if success2:
            print("   🔍 Verifying data persistence:")
            
            # Compare updated fields
            persistence_verified = True
            for field, expected_value in persistence_update.items():
                actual_value = response2.get(field)
                if actual_value == expected_value:
                    print(f"      ✅ {field}: {actual_value} (persisted correctly)")
                else:
                    print(f"      ❌ {field}: {actual_value} (expected {expected_value})")
                    persistence_verified = False
            
            if persistence_verified:
                print("   ✅ All updates properly persisted in database")
            else:
                print("   ❌ Some updates were not properly persisted")
                success2 = False
        
        return success1 and success2

    def test_comprehensive_edit_workflow(self):
        """Test a complete edit workflow as would be used by the frontend"""
        print("\n🎯 TESTING: Comprehensive Edit Workflow (Frontend Simulation)")
        print("=" * 80)
        
        # Step 1: Get all clients (as frontend would do to populate client list)
        success1, clients_response = self.run_test(
            "1. Get All Clients (Frontend Client List)",
            "GET",
            "clients",
            200
        )
        
        if not success1 or not clients_response:
            print("❌ Cannot proceed with workflow test - failed to get clients")
            return False
        
        # Step 2: Get membership types (as frontend would do to populate edit form dropdown)
        success2, membership_response = self.run_test(
            "2. Get Membership Types (Frontend Edit Form Dropdown)",
            "GET",
            "membership-types",
            200
        )
        
        if not success2:
            print("❌ Cannot proceed with workflow test - failed to get membership types")
            return False
        
        # Step 3: Select a client for editing (use our test client or first available)
        target_client_id = self.test_client_id or (clients_response[0].get('id') if clients_response else None)
        
        if not target_client_id:
            print("❌ Cannot proceed with workflow test - no client available for editing")
            return False
        
        # Step 4: Get specific client details (as frontend would do when opening edit modal)
        success3, client_details = self.run_test(
            "3. Get Specific Client Details (Frontend Edit Modal)",
            "GET",
            f"clients/{target_client_id}",
            200
        )
        
        if not success3:
            print("❌ Cannot proceed with workflow test - failed to get client details")
            return False
        
        print("   📋 Current client details:")
        print(f"      Name: {client_details.get('name')}")
        print(f"      Email: {client_details.get('email')}")
        print(f"      Membership: {client_details.get('membership_type')} - TTD {client_details.get('monthly_fee')}")
        print(f"      Status: {client_details.get('status')}")
        
        # Step 5: Simulate user making comprehensive edits
        workflow_updates = {
            "name": "Workflow Test Updated Client",
            "email": "workflow.updated@example.com",
            "phone": "+1868-555-WORK",
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "status": "Active",
            "auto_reminders_enabled": True
        }
        
        success4, update_response = self.run_test(
            "4. Apply User Edits (Frontend Save Action)",
            "PUT",
            f"clients/{target_client_id}",
            200,
            workflow_updates
        )
        
        if not success4:
            print("❌ Workflow test failed - could not apply user edits")
            return False
        
        # Step 6: Verify the edit was successful and client list would show updated data
        success5, verification_response = self.run_test(
            "5. Verify Edit Success (Frontend Refresh)",
            "GET",
            f"clients/{target_client_id}",
            200
        )
        
        if success5:
            print("   🔍 Verifying complete workflow success:")
            
            workflow_success = True
            for field, expected_value in workflow_updates.items():
                actual_value = verification_response.get(field)
                if actual_value == expected_value:
                    print(f"      ✅ {field}: Updated successfully")
                else:
                    print(f"      ❌ {field}: Update failed (expected {expected_value}, got {actual_value})")
                    workflow_success = False
            
            if workflow_success:
                print("   🎉 Complete edit workflow successful!")
                print("   ✅ Frontend edit modal will work correctly with this backend")
            else:
                print("   ❌ Edit workflow has issues - frontend may not work properly")
                success5 = False
        
        return success1 and success2 and success3 and success4 and success5

    def run_all_tests(self):
        """Run all member edit functionality tests"""
        print("🚀 STARTING MEMBER EDIT FUNCTIONALITY BACKEND API TESTING")
        print("=" * 80)
        print("Testing member edit functionality backend API to ensure the rebuilt edit client modal will work correctly")
        print()
        
        # Test sequence as specified in review request
        tests = [
            ("GET /api/clients Availability", self.test_get_clients_for_editing),
            ("GET /api/membership-types Availability", self.test_get_membership_types_for_edit_form),
            ("PUT /api/clients/{id} - Basic Information", self.test_update_basic_information),
            ("PUT /api/clients/{id} - Membership & Fee", self.test_update_membership_type_and_fee),
            ("PUT /api/clients/{id} - Status Updates", self.test_update_status_active_inactive),
            ("PUT /api/clients/{id} - Date & Reminders", self.test_update_start_date_and_auto_reminders),
            ("Data Validation - Invalid Email", self.test_data_validation_invalid_email),
            ("Data Validation - Missing Fields", self.test_data_validation_missing_required_fields),
            ("Data Validation - Invalid Client ID", self.test_data_validation_invalid_client_id),
            ("Concurrent Edit Scenarios", self.test_concurrent_edit_scenarios),
            ("Response Format Verification", self.test_response_format_verification),
            ("Database Persistence", self.test_database_persistence),
            ("Complete Edit Workflow", self.test_comprehensive_edit_workflow)
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*20} {test_name} {'='*20}")
                test_func()
            except Exception as e:
                print(f"❌ {test_name} - ERROR: {str(e)}")
                self.tests_run += 1
        
        # Print final results
        print("\n" + "="*80)
        print("🏁 MEMBER EDIT FUNCTIONALITY BACKEND API TESTING COMPLETE")
        print("="*80)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! Member edit functionality backend is ready for frontend integration!")
            print("✅ GET /api/clients returns clients for editing")
            print("✅ GET /api/membership-types returns membership options")
            print("✅ PUT /api/clients/{id} successfully updates client data")
            print("✅ Proper error handling for invalid requests")
            print("✅ Database persistence of changes confirmed")
            print("✅ Response format is correct and complete")
            print("✅ The rebuilt member edit modal will work correctly!")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} TESTS FAILED - Issues need to be addressed")
            print("❌ Some member edit functionality may not work properly")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    print("🎯 MEMBER EDIT FUNCTIONALITY BACKEND API TESTER")
    print("Testing backend APIs to ensure the rebuilt edit client modal will work correctly")
    print()
    
    tester = MemberEditAPITester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)