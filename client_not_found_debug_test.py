#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class ClientNotFoundDebugger:
    def __init__(self, base_url="https://bc0d3d40-9578-4667-9bfb-b44c2f8459c5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.deon_aleong_client = None

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
                print(f"   ERROR RESPONSE: {response.text}")
                return False, {}

        except requests.exceptions.RequestException as e:
            details = f"(Network Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}
        except Exception as e:
            details = f"(Error: {str(e)})"
            self.log_test(name, False, details)
            return False, {}

    def test_get_all_clients(self):
        """Test 1: GET /api/clients to see all current clients"""
        print("\n" + "="*80)
        print("🔍 TEST 1: CLIENT RETRIEVAL - GET /api/clients")
        print("="*80)
        
        success, response = self.run_test(
            "Get All Clients",
            "GET",
            "clients",
            200
        )
        
        if success:
            clients = response if isinstance(response, list) else []
            print(f"\n📊 FOUND {len(clients)} TOTAL CLIENTS:")
            
            # Look for "Deon Aleong" specifically
            deon_clients = []
            for client in clients:
                client_name = client.get('name', '').lower()
                if 'deon' in client_name and 'aleong' in client_name:
                    deon_clients.append(client)
                    print(f"\n🎯 FOUND DEON ALEONG CLIENT:")
                    print(f"   ID: {client.get('id')}")
                    print(f"   Name: {client.get('name')}")
                    print(f"   Email: {client.get('email')}")
                    print(f"   Membership: {client.get('membership_type')}")
                    print(f"   Monthly Fee: TTD {client.get('monthly_fee')}")
                    print(f"   Status: {client.get('status')}")
                    print(f"   ID Type: {type(client.get('id'))}")
                    print(f"   ID Length: {len(str(client.get('id')))}")
                    
            if deon_clients:
                self.deon_aleong_client = deon_clients[0]  # Use first match
                print(f"\n✅ DEON ALEONG CLIENT FOUND - ID: {self.deon_aleong_client.get('id')}")
            else:
                print(f"\n❌ DEON ALEONG CLIENT NOT FOUND!")
                print(f"   Searching for clients with 'deon' and 'aleong' in name...")
                
                # Show all client names for debugging
                print(f"\n📋 ALL CLIENT NAMES:")
                for i, client in enumerate(clients[:20], 1):  # Show first 20
                    print(f"   {i}. {client.get('name')} (ID: {client.get('id')})")
                
                if len(clients) > 20:
                    print(f"   ... and {len(clients) - 20} more clients")
        
        return success

    def test_search_for_similar_clients(self):
        """Test 2: Search for clients with similar names to Deon Aleong"""
        print("\n" + "="*80)
        print("🔍 TEST 2: SEARCH FOR SIMILAR CLIENT NAMES")
        print("="*80)
        
        success, response = self.run_test(
            "Search for Similar Client Names",
            "GET",
            "clients",
            200
        )
        
        if success:
            clients = response if isinstance(response, list) else []
            
            # Search patterns
            search_patterns = ['deon', 'aleong', 'standard', 'ttd 1000', '1000']
            
            print(f"\n🔍 SEARCHING FOR PATTERNS: {search_patterns}")
            
            for pattern in search_patterns:
                matching_clients = []
                for client in clients:
                    client_name = client.get('name', '').lower()
                    client_membership = client.get('membership_type', '').lower()
                    client_fee = str(client.get('monthly_fee', '')).lower()
                    
                    if (pattern in client_name or 
                        pattern in client_membership or 
                        pattern in client_fee):
                        matching_clients.append(client)
                
                if matching_clients:
                    print(f"\n📋 CLIENTS MATCHING '{pattern.upper()}':")
                    for client in matching_clients[:5]:  # Show first 5 matches
                        print(f"   - {client.get('name')} (ID: {client.get('id')})")
                        print(f"     Membership: {client.get('membership_type')} - TTD {client.get('monthly_fee')}")
                        print(f"     Status: {client.get('status')}")
                        
                        # Check if this could be our target client
                        if (client.get('membership_type', '').lower() == 'standard' and 
                            client.get('monthly_fee') == 1000):
                            print(f"   🎯 POTENTIAL MATCH: This could be 'Deon Aleong - TTD 1000 (Standard)'")
                            if not self.deon_aleong_client:
                                self.deon_aleong_client = client
                else:
                    print(f"\n❌ NO CLIENTS FOUND MATCHING '{pattern.upper()}'")
        
        return success

    def test_client_id_formats(self):
        """Test 3: Debug Client ID Issues - Check ID formats"""
        print("\n" + "="*80)
        print("🔍 TEST 3: CLIENT ID FORMAT ANALYSIS")
        print("="*80)
        
        success, response = self.run_test(
            "Analyze Client ID Formats",
            "GET",
            "clients",
            200
        )
        
        if success:
            clients = response if isinstance(response, list) else []
            
            if clients:
                print(f"\n📊 CLIENT ID FORMAT ANALYSIS:")
                
                # Analyze ID formats
                id_types = {}
                id_lengths = {}
                sample_ids = []
                
                for client in clients[:10]:  # Analyze first 10 clients
                    client_id = client.get('id')
                    if client_id:
                        id_type = type(client_id).__name__
                        id_length = len(str(client_id))
                        
                        id_types[id_type] = id_types.get(id_type, 0) + 1
                        id_lengths[id_length] = id_lengths.get(id_length, 0) + 1
                        
                        if len(sample_ids) < 5:
                            sample_ids.append({
                                'name': client.get('name'),
                                'id': client_id,
                                'type': id_type,
                                'length': id_length
                            })
                
                print(f"   ID Types: {id_types}")
                print(f"   ID Lengths: {id_lengths}")
                print(f"\n   Sample IDs:")
                for sample in sample_ids:
                    print(f"   - {sample['name']}: {sample['id']} (Type: {sample['type']}, Length: {sample['length']})")
                
                # Check for UUID format
                import re
                uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                
                uuid_count = 0
                non_uuid_count = 0
                
                for client in clients:
                    client_id = str(client.get('id', ''))
                    if uuid_pattern.match(client_id):
                        uuid_count += 1
                    else:
                        non_uuid_count += 1
                
                print(f"\n   UUID Format Analysis:")
                print(f"   - Valid UUIDs: {uuid_count}")
                print(f"   - Non-UUID IDs: {non_uuid_count}")
                
                if non_uuid_count > 0:
                    print(f"   ⚠️  WARNING: Some client IDs are not in UUID format!")
                else:
                    print(f"   ✅ All client IDs are in proper UUID format")
        
        return success

    def test_specific_client_retrieval(self):
        """Test 4: Test retrieving the specific client if found"""
        print("\n" + "="*80)
        print("🔍 TEST 4: SPECIFIC CLIENT RETRIEVAL")
        print("="*80)
        
        if not self.deon_aleong_client:
            print("❌ SKIPPED: No Deon Aleong client found to test")
            return False
        
        client_id = self.deon_aleong_client.get('id')
        print(f"🎯 Testing retrieval of client ID: {client_id}")
        
        success, response = self.run_test(
            f"Get Specific Client - {self.deon_aleong_client.get('name')}",
            "GET",
            f"clients/{client_id}",
            200
        )
        
        if success:
            print(f"\n✅ CLIENT RETRIEVAL SUCCESSFUL:")
            print(f"   Name: {response.get('name')}")
            print(f"   Email: {response.get('email')}")
            print(f"   ID: {response.get('id')}")
            print(f"   Membership: {response.get('membership_type')}")
            print(f"   Monthly Fee: TTD {response.get('monthly_fee')}")
            print(f"   Status: {response.get('status')}")
        
        return success

    def test_payment_recording_with_found_client(self):
        """Test 5: Test payment recording with the found client"""
        print("\n" + "="*80)
        print("🔍 TEST 5: PAYMENT RECORDING WITH FOUND CLIENT")
        print("="*80)
        
        if not self.deon_aleong_client:
            print("❌ SKIPPED: No Deon Aleong client found to test payment recording")
            return False
        
        client_id = self.deon_aleong_client.get('id')
        client_name = self.deon_aleong_client.get('name')
        
        print(f"🎯 Testing payment recording for:")
        print(f"   Client ID: {client_id}")
        print(f"   Client Name: {client_name}")
        print(f"   ID Type: {type(client_id)}")
        
        # Test payment recording
        payment_data = {
            "client_id": client_id,
            "amount_paid": 1000.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Cash",
            "notes": "Debug test payment for Deon Aleong client not found issue"
        }
        
        success, response = self.run_test(
            f"Record Payment for {client_name}",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"\n✅ PAYMENT RECORDING SUCCESSFUL:")
            print(f"   Client Name: {response.get('client_name')}")
            print(f"   Amount Paid: TTD {response.get('amount_paid')}")
            print(f"   Success: {response.get('success')}")
            print(f"   Invoice Sent: {response.get('invoice_sent')}")
            print(f"   Invoice Message: {response.get('invoice_message')}")
            print(f"   New Next Payment Date: {response.get('new_next_payment_date')}")
        else:
            print(f"\n❌ PAYMENT RECORDING FAILED!")
            print(f"   This confirms the 'Client not found' error!")
        
        return success

    def test_payment_recording_with_different_id_formats(self):
        """Test 6: Test payment recording with different ID formats"""
        print("\n" + "="*80)
        print("🔍 TEST 6: PAYMENT RECORDING WITH DIFFERENT ID FORMATS")
        print("="*80)
        
        if not self.deon_aleong_client:
            print("❌ SKIPPED: No client found to test different ID formats")
            return False
        
        client_id = self.deon_aleong_client.get('id')
        original_id = str(client_id)
        
        # Test different ID formats
        id_variations = [
            ("Original ID", original_id),
            ("String ID", str(client_id)),
            ("Uppercase ID", str(client_id).upper()),
            ("Lowercase ID", str(client_id).lower()),
        ]
        
        # Add integer conversion if possible
        try:
            int_id = int(client_id)
            id_variations.append(("Integer ID", int_id))
        except:
            pass
        
        results = []
        
        for variation_name, test_id in id_variations:
            print(f"\n🧪 Testing {variation_name}: {test_id} (Type: {type(test_id)})")
            
            payment_data = {
                "client_id": test_id,
                "amount_paid": 100.00,
                "payment_date": date.today().isoformat(),
                "payment_method": "Test",
                "notes": f"Testing {variation_name} format"
            }
            
            success, response = self.run_test(
                f"Payment with {variation_name}",
                "POST",
                "payments/record",
                200,
                payment_data
            )
            
            results.append({
                'variation': variation_name,
                'id': test_id,
                'success': success,
                'response': response
            })
        
        # Analyze results
        print(f"\n📊 ID FORMAT TEST RESULTS:")
        successful_formats = []
        failed_formats = []
        
        for result in results:
            if result['success']:
                successful_formats.append(result['variation'])
                print(f"   ✅ {result['variation']}: SUCCESS")
            else:
                failed_formats.append(result['variation'])
                print(f"   ❌ {result['variation']}: FAILED")
        
        if successful_formats:
            print(f"\n✅ WORKING ID FORMATS: {successful_formats}")
        if failed_formats:
            print(f"\n❌ FAILING ID FORMATS: {failed_formats}")
        
        return len(successful_formats) > 0

    def test_email_service_during_payment(self):
        """Test 7: Test email service functionality during payment recording"""
        print("\n" + "="*80)
        print("🔍 TEST 7: EMAIL SERVICE FUNCTIONALITY DURING PAYMENT")
        print("="*80)
        
        # First test email configuration
        success1, response1 = self.run_test(
            "Test Email Configuration",
            "POST",
            "email/test",
            200
        )
        
        if success1:
            print(f"\n📧 EMAIL CONFIGURATION TEST:")
            print(f"   Success: {response1.get('success')}")
            print(f"   Message: {response1.get('message')}")
            
            if not response1.get('success'):
                print(f"   ⚠️  EMAIL SERVICE NOT WORKING - This explains invoice email failures!")
        
        # Test email templates
        success2, response2 = self.run_test(
            "Get Email Templates",
            "GET",
            "email/templates",
            200
        )
        
        if success2:
            templates = response2.get('templates', {})
            print(f"\n📧 AVAILABLE EMAIL TEMPLATES: {list(templates.keys())}")
        
        return success1 and success2

    def test_backend_logs_simulation(self):
        """Test 8: Simulate backend error scenarios"""
        print("\n" + "="*80)
        print("🔍 TEST 8: BACKEND ERROR SCENARIOS SIMULATION")
        print("="*80)
        
        # Test with completely invalid client ID
        invalid_ids = [
            "invalid-client-id",
            "12345",
            "",
            None,
            "00000000-0000-0000-0000-000000000000"
        ]
        
        for invalid_id in invalid_ids:
            if invalid_id is None:
                continue
                
            print(f"\n🧪 Testing with invalid ID: {invalid_id}")
            
            payment_data = {
                "client_id": invalid_id,
                "amount_paid": 1000.00,
                "payment_date": date.today().isoformat(),
                "payment_method": "Cash",
                "notes": "Testing invalid client ID"
            }
            
            success, response = self.run_test(
                f"Payment with Invalid ID: {invalid_id}",
                "POST",
                "payments/record",
                404,  # Expecting 404 Client not found
                payment_data
            )
            
            if not success:
                print(f"   ⚠️  Expected 404 but got different error - this might indicate the issue!")
        
        return True

    def run_all_tests(self):
        """Run all debugging tests"""
        print("\n" + "="*100)
        print("🚨 CLIENT NOT FOUND ERROR DEBUGGING - COMPREHENSIVE ANALYSIS")
        print("="*100)
        print("🎯 TARGET: Debug 'Client not found' error for 'Deon Aleong - TTD 1000 (Standard)'")
        print("📧 FOCUS: Payment recording and email invoice functionality")
        print("="*100)
        
        # Run all tests
        tests = [
            self.test_get_all_clients,
            self.test_search_for_similar_clients,
            self.test_client_id_formats,
            self.test_specific_client_retrieval,
            self.test_payment_recording_with_found_client,
            self.test_payment_recording_with_different_id_formats,
            self.test_email_service_during_payment,
            self.test_backend_logs_simulation
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        # Final summary
        print("\n" + "="*100)
        print("📊 DEBUGGING SUMMARY")
        print("="*100)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.deon_aleong_client:
            print(f"\n✅ DEON ALEONG CLIENT FOUND:")
            print(f"   ID: {self.deon_aleong_client.get('id')}")
            print(f"   Name: {self.deon_aleong_client.get('name')}")
            print(f"   Membership: {self.deon_aleong_client.get('membership_type')}")
            print(f"   Fee: TTD {self.deon_aleong_client.get('monthly_fee')}")
        else:
            print(f"\n❌ DEON ALEONG CLIENT NOT FOUND!")
            print(f"   This is likely the root cause of the 'Client not found' error")
        
        print("\n🔧 RECOMMENDATIONS:")
        if not self.deon_aleong_client:
            print("   1. Check if client name is spelled differently in database")
            print("   2. Verify client hasn't been deleted or deactivated")
            print("   3. Check if client exists with different membership type or fee")
        else:
            print("   1. Client exists - issue may be in frontend client ID passing")
            print("   2. Check frontend payment form client selection logic")
            print("   3. Verify client ID format consistency between frontend and backend")
        
        print("   4. Check email service configuration for invoice sending issues")
        print("   5. Review backend logs during actual payment attempts")
        
        return self.tests_passed, self.tests_run

if __name__ == "__main__":
    debugger = ClientNotFoundDebugger()
    passed, total = debugger.run_all_tests()
    
    if passed == total:
        print(f"\n🎉 ALL DEBUGGING TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  SOME DEBUGGING TESTS FAILED - ISSUES IDENTIFIED!")
        sys.exit(1)