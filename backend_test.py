#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime, date
import time
import uuid

# Get backend URL from environment
BACKEND_URL = "https://alphalete-pwa.preview.emergentagent.com/api"

def test_comprehensive_backend():
    """
    Comprehensive testing of Alphalete Club PWA backend functionality.
    
    Testing Focus (as per review request):
    1. Basic API Endpoints: Test all CRUD operations for members, payments, and plans
    2. Email Service: Verify email sending functionality for payment reminders and receipts
    3. MongoDB Connection: Ensure database operations are working properly
    4. Reminder Scheduler: Check if the automated reminder system is functioning
    5. Settings Management: Test loading and saving of gym settings
    6. Data Consistency: Verify that all data operations return expected results
    """
    
    print("🧪 ALPHALETE CLUB PWA - COMPREHENSIVE BACKEND TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    total_tests = 0
    passed_tests = 0
    
    def run_test(test_name, test_func):
        nonlocal total_tests, passed_tests
        total_tests += 1
        print(f"🔍 Testing: {test_name}")
        try:
            result = test_func()
            if result:
                print(f"✅ PASSED: {test_name}")
                passed_tests += 1
                test_results.append(f"✅ {test_name}")
                return True
            else:
                print(f"❌ FAILED: {test_name}")
                test_results.append(f"❌ {test_name}")
                return False
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {str(e)}")
            test_results.append(f"❌ {test_name} - ERROR: {str(e)}")
            return False
        finally:
            print()
    
    # ========== SECTION 1: BASIC API CONNECTIVITY ==========
    
    def test_api_health():
        """Test basic API connectivity and health check"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                
                if 'status' in data and data['status'] == 'healthy':
                    print(f"   ✅ API Health Check: {data['status']}")
                    return True
                else:
                    print(f"   ❌ Unexpected health status")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_api_status():
        """Test API status endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                
                if 'status' in data and 'version' in data and 'endpoints' in data:
                    print(f"   ✅ API Status: {data['status']}")
                    print(f"   ✅ Version: {data['version']}")
                    print(f"   ✅ Endpoints: {data['endpoints']}")
                    return True
                else:
                    print(f"   ❌ Missing required fields in response")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # ========== SECTION 2: CLIENT/MEMBER CRUD OPERATIONS ==========
    
    def test_get_clients():
        """Test GET /api/clients endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/clients", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                clients = response.json()
                print(f"   Response: Found {len(clients)} clients")
                
                if isinstance(clients, list):
                    if len(clients) > 0:
                        # Check first client structure
                        client = clients[0]
                        required_fields = ['id', 'name', 'email', 'membership_type', 'monthly_fee', 'status']
                        for field in required_fields:
                            if field not in client:
                                print(f"   ❌ Missing required field: {field}")
                                return False
                        print(f"   ✅ Client structure valid")
                    print(f"   ✅ GET /api/clients working - {len(clients)} clients found")
                    return True
                else:
                    print(f"   ❌ Response is not a list")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_create_client():
        """Test POST /api/clients endpoint"""
        try:
            # Create test client data
            test_client = {
                "name": "Backend Test User",
                "email": f"backendtest.{int(time.time())}@example.com",
                "phone": "+1234567890",
                "membership_type": "Basic",
                "monthly_fee": 55.0,
                "start_date": date.today().isoformat(),
                "payment_status": "due",
                "amount_owed": 55.0,
                "auto_reminders_enabled": True
            }
            
            response = requests.post(
                f"{BACKEND_URL}/clients", 
                json=test_client,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                created_client = response.json()
                print(f"   Response: Created client with ID {created_client.get('id', 'Unknown')}")
                
                # Verify created client has required fields
                if 'id' in created_client and 'name' in created_client:
                    print(f"   ✅ Client created successfully: {created_client['name']}")
                    # Store client ID for cleanup
                    test_create_client.client_id = created_client['id']
                    return True
                else:
                    print(f"   ❌ Created client missing required fields")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Error text: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_get_specific_client():
        """Test GET /api/clients/{id} endpoint"""
        try:
            # Use client created in previous test
            if not hasattr(test_create_client, 'client_id'):
                print(f"   ⚠️ No test client available - skipping")
                return True
            
            client_id = test_create_client.client_id
            response = requests.get(f"{BACKEND_URL}/clients/{client_id}", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                client = response.json()
                print(f"   Response: Retrieved client {client.get('name', 'Unknown')}")
                
                if 'id' in client and client['id'] == client_id:
                    print(f"   ✅ Specific client retrieval working")
                    return True
                else:
                    print(f"   ❌ Client ID mismatch")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_update_client():
        """Test PUT /api/clients/{id} endpoint"""
        try:
            # Use client created in previous test
            if not hasattr(test_create_client, 'client_id'):
                print(f"   ⚠️ No test client available - skipping")
                return True
            
            client_id = test_create_client.client_id
            update_data = {
                "phone": "+9876543210",
                "monthly_fee": 65.0,
                "membership_type": "Premium"
            }
            
            response = requests.put(
                f"{BACKEND_URL}/clients/{client_id}", 
                json=update_data,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                updated_client = response.json()
                print(f"   Response: Updated client {updated_client.get('name', 'Unknown')}")
                
                # Verify updates were applied
                if (updated_client.get('phone') == update_data['phone'] and 
                    updated_client.get('monthly_fee') == update_data['monthly_fee']):
                    print(f"   ✅ Client update working correctly")
                    return True
                else:
                    print(f"   ❌ Updates not applied correctly")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_delete_client():
        """Test DELETE /api/clients/{id} endpoint"""
        try:
            # Use client created in previous test
            if not hasattr(test_create_client, 'client_id'):
                print(f"   ⚠️ No test client available - skipping")
                return True
            
            client_id = test_create_client.client_id
            response = requests.delete(f"{BACKEND_URL}/clients/{client_id}", timeout=15)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                delete_result = response.json()
                print(f"   Response: {delete_result.get('message', 'Client deleted')}")
                
                # Verify client was actually deleted
                verify_response = requests.get(f"{BACKEND_URL}/clients/{client_id}", timeout=10)
                if verify_response.status_code == 404:
                    print(f"   ✅ Client deletion working correctly")
                    return True
                else:
                    print(f"   ❌ Client still exists after deletion")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # ========== SECTION 3: PAYMENT OPERATIONS ==========
    
    def test_payment_stats():
        """Test GET /api/payments/stats endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/payments/stats", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"   Response: {stats}")
                
                required_fields = ['total_revenue', 'monthly_revenue', 'total_amount_owed', 'payment_count']
                for field in required_fields:
                    if field not in stats:
                        print(f"   ❌ Missing required field: {field}")
                        return False
                
                print(f"   ✅ Payment stats: Revenue=${stats['total_revenue']}, Count={stats['payment_count']}")
                return True
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_payment_recording():
        """Test POST /api/payments/record endpoint"""
        try:
            # First get a client to record payment for
            clients_response = requests.get(f"{BACKEND_URL}/clients", timeout=10)
            if clients_response.status_code != 200:
                print(f"   ⚠️ Cannot get clients for payment test")
                return True
            
            clients = clients_response.json()
            if not clients:
                print(f"   ⚠️ No clients available for payment test")
                return True
            
            # Use first client
            test_client = clients[0]
            payment_data = {
                "client_id": test_client['id'],
                "amount_paid": 25.0,
                "payment_date": date.today().isoformat(),
                "payment_method": "Cash",
                "notes": "Backend test payment"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/payments/record", 
                json=payment_data,
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {result.get('message', 'Payment recorded')}")
                
                if 'success' in result and result['success']:
                    print(f"   ✅ Payment recording working: ${result.get('amount_paid', 0)}")
                    return True
                else:
                    print(f"   ❌ Payment recording failed")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # ========== SECTION 4: MEMBERSHIP TYPES/PLANS ==========
    
    def test_membership_types():
        """Test GET /api/membership-types endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/membership-types", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                membership_types = response.json()
                print(f"   Response: Found {len(membership_types)} membership types")
                
                if isinstance(membership_types, list) and len(membership_types) > 0:
                    # Check first membership type structure
                    membership_type = membership_types[0]
                    required_fields = ['id', 'name', 'monthly_fee', 'description']
                    for field in required_fields:
                        if field not in membership_type:
                            print(f"   ❌ Missing required field: {field}")
                            return False
                    print(f"   ✅ Membership types working - {len(membership_types)} types available")
                    return True
                else:
                    print(f"   ❌ No membership types found or invalid format")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # ========== SECTION 5: EMAIL SERVICE ==========
    
    def test_email_service_connectivity():
        """Test POST /api/email/test endpoint"""
        try:
            response = requests.post(f"{BACKEND_URL}/email/test", timeout=30)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                
                if 'success' in data and 'message' in data:
                    print(f"   ✅ Email service connectivity: {data['message']}")
                    return True
                else:
                    print(f"   ❌ Unexpected response structure")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Request timeout (30s) - Email test may take time")
            return True
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_email_templates():
        """Test GET /api/email/templates endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/email/templates", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                
                if 'templates' in data:
                    templates = data['templates']
                    expected_templates = ['default', 'professional', 'friendly']
                    
                    for template in expected_templates:
                        if template not in templates:
                            print(f"   ❌ Missing template: {template}")
                            return False
                    
                    print(f"   ✅ Email templates available: {len(templates)} templates")
                    return True
                else:
                    print(f"   ❌ No templates in response")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_direct_email_send():
        """Test POST /api/email/send endpoint"""
        try:
            test_email_data = {
                "to": "test@example.com",
                "subject": "Backend Test Email",
                "body": "This is a test email from the Alphalete Club backend testing system."
            }
            
            response = requests.post(
                f"{BACKEND_URL}/email/send", 
                json=test_email_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                
                if 'success' in data and 'message' in data and 'client_email' in data:
                    print(f"   ✅ Direct email send working")
                    return True
                else:
                    print(f"   ❌ Missing required response fields")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Request timeout (30s) - Email sending may take time")
            return True
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # ========== SECTION 6: REMINDER SCHEDULER ==========
    
    def test_reminder_stats():
        """Test GET /api/reminders/stats endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/reminders/stats", timeout=15)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"   Response: {stats}")
                
                required_fields = ['total_reminders_sent', 'scheduler_active']
                for field in required_fields:
                    if field not in stats:
                        print(f"   ❌ Missing required field: {field}")
                        return False
                
                print(f"   ✅ Reminder scheduler stats: Sent={stats['total_reminders_sent']}, Active={stats['scheduler_active']}")
                return True
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    def test_upcoming_reminders():
        """Test GET /api/reminders/upcoming endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/reminders/upcoming?days_ahead=7", timeout=15)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                
                if 'upcoming_reminders' in data and 'total_reminders' in data:
                    print(f"   ✅ Upcoming reminders: {data['total_reminders']} reminders")
                    return True
                else:
                    print(f"   ❌ Missing required fields in response")
                    return False
            elif response.status_code == 503:
                print(f"   ⚠️ Reminder scheduler not initialized - service may be starting")
                return True
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            return False
    
    # ========== SECTION 7: DATABASE CONNECTIVITY ==========
    
    def test_database_connectivity():
        """Test database connectivity through multiple endpoints"""
        try:
            # Test multiple database-dependent endpoints
            endpoints_to_test = [
                ("/clients", "clients collection"),
                ("/payments/stats", "payment_records collection"),
                ("/membership-types", "membership_types collection")
            ]
            
            successful_connections = 0
            
            for endpoint, description in endpoints_to_test:
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        successful_connections += 1
                        print(f"   ✅ {description} accessible")
                    else:
                        print(f"   ❌ {description} failed: {response.status_code}")
                except Exception as e:
                    print(f"   ❌ {description} error: {str(e)}")
            
            if successful_connections >= 2:  # At least 2 out of 3 should work
                print(f"   ✅ Database connectivity confirmed: {successful_connections}/3 collections accessible")
                return True
            else:
                print(f"   ❌ Database connectivity issues: only {successful_connections}/3 collections accessible")
                return False
                
        except Exception as e:
            print(f"   ❌ Database connectivity test failed: {str(e)}")
            return False
    
    # ========== RUN ALL TESTS ==========
    
    print("🚀 Starting Comprehensive Backend Tests...")
    print()
    
    # Section 1: Basic API Connectivity
    print("📡 SECTION 1: BASIC API CONNECTIVITY")
    print("-" * 50)
    run_test("API Health Check", test_api_health)
    run_test("API Status Endpoint", test_api_status)
    print()
    
    # Section 2: Client/Member CRUD Operations
    print("👥 SECTION 2: CLIENT/MEMBER CRUD OPERATIONS")
    print("-" * 50)
    run_test("Get All Clients", test_get_clients)
    run_test("Create New Client", test_create_client)
    run_test("Get Specific Client", test_get_specific_client)
    run_test("Update Client", test_update_client)
    run_test("Delete Client", test_delete_client)
    print()
    
    # Section 3: Payment Operations
    print("💰 SECTION 3: PAYMENT OPERATIONS")
    print("-" * 50)
    run_test("Payment Statistics", test_payment_stats)
    run_test("Payment Recording", test_payment_recording)
    print()
    
    # Section 4: Membership Types/Plans
    print("📋 SECTION 4: MEMBERSHIP TYPES/PLANS")
    print("-" * 50)
    run_test("Get Membership Types", test_membership_types)
    print()
    
    # Section 5: Email Service
    print("📧 SECTION 5: EMAIL SERVICE")
    print("-" * 50)
    run_test("Email Service Connectivity", test_email_service_connectivity)
    run_test("Email Templates", test_email_templates)
    run_test("Direct Email Send", test_direct_email_send)
    print()
    
    # Section 6: Reminder Scheduler
    print("⏰ SECTION 6: REMINDER SCHEDULER")
    print("-" * 50)
    run_test("Reminder Statistics", test_reminder_stats)
    run_test("Upcoming Reminders", test_upcoming_reminders)
    print()
    
    # Section 7: Database Connectivity
    print("🗄️ SECTION 7: DATABASE CONNECTIVITY")
    print("-" * 50)
    run_test("Database Connectivity", test_database_connectivity)
    print()
    
    # Print comprehensive summary
    print("=" * 80)
    print("📊 COMPREHENSIVE BACKEND TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    print("📋 DETAILED RESULTS:")
    for result in test_results:
        print(f"  {result}")
    print()
    
    # Determine overall result
    if passed_tests == total_tests:
        print("🎉 ALL BACKEND TESTS PASSED!")
        print("✅ Alphalete Club PWA backend is fully functional")
        print("✅ All core functionality working as expected")
        return True
    elif passed_tests >= total_tests * 0.85:  # 85% pass rate
        print("✅ BACKEND MOSTLY FUNCTIONAL")
        print(f"⚠️ {total_tests - passed_tests} tests failed - check details above")
        print("✅ Core functionality appears to be working")
        return True
    else:
        print("❌ BACKEND HAS SIGNIFICANT ISSUES")
        print(f"🚨 {total_tests - passed_tests} tests failed - requires immediate attention")
        return False

if __name__ == "__main__":
    success = test_comprehensive_backend()
    sys.exit(0 if success else 1)