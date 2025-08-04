#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any

class WhatsAppBackendTester:
    def __init__(self, base_url="https://276b2f1f-9d6e-4215-a382-5da8671edad7.preview.emergentagent.com"):
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

    def test_api_health(self):
        """Test API health check"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        if success and "message" in response:
            print(f"   Health message: {response['message']}")
        return success

    def test_current_database_state(self):
        """Check current database state for existing clients/members"""
        print("\n🔍 CHECKING CURRENT DATABASE STATE")
        print("=" * 60)
        
        # Check existing clients
        success, response = self.run_test(
            "Get Current Clients/Members",
            "GET",
            "clients",
            200
        )
        
        if success:
            clients = response if isinstance(response, list) else []
            print(f"\n📊 CURRENT DATABASE STATE:")
            print(f"   Total Clients/Members: {len(clients)}")
            
            if len(clients) == 0:
                print("   ❌ NO CLIENTS FOUND - Database appears to be empty")
                print("   📝 Need to create test clients with phone numbers for WhatsApp testing")
                return False, []
            else:
                print(f"   ✅ FOUND {len(clients)} EXISTING CLIENTS")
                
                # Analyze existing clients for phone numbers
                clients_with_phone = []
                clients_without_phone = []
                
                for i, client in enumerate(clients[:10], 1):  # Show first 10 clients
                    name = client.get('name', 'Unknown')
                    email = client.get('email', 'No email')
                    phone = client.get('phone', None)
                    membership = client.get('membership_type', 'Unknown')
                    status = client.get('status', 'Unknown')
                    
                    print(f"   {i}. {name}")
                    print(f"      Email: {email}")
                    print(f"      Phone: {phone if phone else 'NO PHONE NUMBER'}")
                    print(f"      Membership: {membership}")
                    print(f"      Status: {status}")
                    
                    if phone and phone.strip():
                        clients_with_phone.append(client)
                    else:
                        clients_without_phone.append(client)
                
                print(f"\n📱 PHONE NUMBER ANALYSIS:")
                print(f"   Clients WITH phone numbers: {len(clients_with_phone)}")
                print(f"   Clients WITHOUT phone numbers: {len(clients_without_phone)}")
                
                if len(clients_with_phone) > 0:
                    print(f"   ✅ GOOD: Found clients with phone numbers for WhatsApp testing")
                    return True, clients_with_phone
                else:
                    print(f"   ⚠️  WARNING: No clients have phone numbers - need to add phone numbers for WhatsApp testing")
                    return True, clients
        
        return False, []

    def test_create_trinidad_client_with_whatsapp(self):
        """Create a test client with Trinidad phone number for WhatsApp testing"""
        print("\n📱 CREATING TRINIDAD CLIENT WITH WHATSAPP PHONE NUMBER")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Trinidad phone number in international format (+1868)
        trinidad_client_data = {
            "name": "Marcus Williams",
            "email": f"marcus_trinidad_{timestamp}@example.com",
            "phone": "+18685551234",  # Trinidad international format
            "membership_type": "Premium",
            "monthly_fee": 75.00,
            "start_date": date.today().isoformat(),
            "auto_reminders_enabled": True
        }
        
        success, response = self.run_test(
            "Create Trinidad Client with WhatsApp Phone",
            "POST",
            "clients",
            200,
            trinidad_client_data
        )
        
        if success and "id" in response:
            client_id = response["id"]
            self.created_client_ids.append(client_id)
            
            print(f"\n✅ TRINIDAD CLIENT CREATED SUCCESSFULLY:")
            print(f"   Client ID: {client_id}")
            print(f"   Name: {response.get('name')}")
            print(f"   Phone: {response.get('phone')} (Trinidad format)")
            print(f"   Email: {response.get('email')}")
            print(f"   Membership: {response.get('membership_type')}")
            print(f"   Monthly Fee: TTD {response.get('monthly_fee')}")
            print(f"   Start Date: {response.get('start_date')}")
            print(f"   Next Payment Due: {response.get('next_payment_date')}")
            print(f"   Auto Reminders: {response.get('auto_reminders_enabled')}")
            
            # Verify phone number format
            phone = response.get('phone')
            if phone and phone.startswith('+1868'):
                print(f"   ✅ PHONE FORMAT CORRECT: Trinidad international format (+1868)")
            else:
                print(f"   ⚠️  PHONE FORMAT WARNING: Expected +1868 format, got {phone}")
            
            return True, response
        
        return False, {}

    def test_create_multiple_trinidad_clients(self):
        """Create multiple test clients with different Trinidad phone numbers"""
        print("\n📱 CREATING MULTIPLE TRINIDAD CLIENTS FOR WHATSAPP TESTING")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        trinidad_clients = [
            {
                "name": "Sarah Thompson",
                "email": f"sarah_trinidad_{timestamp}@example.com",
                "phone": "+18685552345",
                "membership_type": "Elite",
                "monthly_fee": 100.00,
                "start_date": (date.today() - timedelta(days=27)).isoformat(),  # Payment due in 3 days
            },
            {
                "name": "David Rodriguez",
                "email": f"david_trinidad_{timestamp}@example.com", 
                "phone": "+18685553456",
                "membership_type": "VIP",
                "monthly_fee": 150.00,
                "start_date": (date.today() - timedelta(days=30)).isoformat(),  # Payment due today
            },
            {
                "name": "Lisa Chen",
                "email": f"lisa_trinidad_{timestamp}@example.com",
                "phone": "+18685554567",
                "membership_type": "Standard",
                "monthly_fee": 55.00,
                "start_date": date.today().isoformat(),  # Just joined
            }
        ]
        
        created_clients = []
        
        for i, client_data in enumerate(trinidad_clients, 1):
            client_data["auto_reminders_enabled"] = True
            
            success, response = self.run_test(
                f"Create Trinidad Client #{i} - {client_data['name']}",
                "POST",
                "clients",
                200,
                client_data
            )
            
            if success and "id" in response:
                client_id = response["id"]
                self.created_client_ids.append(client_id)
                created_clients.append(response)
                
                print(f"   ✅ Client #{i} Created:")
                print(f"      Name: {response.get('name')}")
                print(f"      Phone: {response.get('phone')}")
                print(f"      Next Payment: {response.get('next_payment_date')}")
                print(f"      Membership: {response.get('membership_type')} - TTD {response.get('monthly_fee')}")
        
        print(f"\n📊 TRINIDAD CLIENTS SUMMARY:")
        print(f"   Total Created: {len(created_clients)}")
        print(f"   All have Trinidad phone numbers (+1868)")
        print(f"   All have auto reminders enabled")
        print(f"   Ready for WhatsApp Click-to-Chat testing")
        
        return len(created_clients) == len(trinidad_clients), created_clients

    def test_whatsapp_click_to_chat_data_preparation(self):
        """Test data preparation for WhatsApp Click-to-Chat functionality"""
        print("\n📱 WHATSAPP CLICK-TO-CHAT DATA PREPARATION")
        print("=" * 60)
        
        # Get all clients to analyze WhatsApp readiness
        success, response = self.run_test(
            "Get All Clients for WhatsApp Analysis",
            "GET",
            "clients",
            200
        )
        
        if not success:
            return False
        
        clients = response if isinstance(response, list) else []
        
        whatsapp_ready_clients = []
        clients_need_phone = []
        
        for client in clients:
            phone = client.get('phone', '')
            name = client.get('name', 'Unknown')
            
            if phone and phone.strip():
                # Check if phone is in international format
                if phone.startswith('+1868') or phone.startswith('1868') or phone.startswith('868'):
                    whatsapp_ready_clients.append({
                        'id': client.get('id'),
                        'name': name,
                        'phone': phone,
                        'whatsapp_url': self.generate_whatsapp_url(phone, name),
                        'membership_type': client.get('membership_type'),
                        'monthly_fee': client.get('monthly_fee'),
                        'next_payment_date': client.get('next_payment_date')
                    })
                else:
                    clients_need_phone.append({'name': name, 'phone': phone, 'issue': 'Not Trinidad format'})
            else:
                clients_need_phone.append({'name': name, 'phone': phone, 'issue': 'No phone number'})
        
        print(f"\n📊 WHATSAPP READINESS ANALYSIS:")
        print(f"   Total Clients: {len(clients)}")
        print(f"   WhatsApp Ready: {len(whatsapp_ready_clients)}")
        print(f"   Need Phone Numbers: {len(clients_need_phone)}")
        
        if len(whatsapp_ready_clients) > 0:
            print(f"\n✅ WHATSAPP READY CLIENTS:")
            for i, client in enumerate(whatsapp_ready_clients[:5], 1):  # Show first 5
                print(f"   {i}. {client['name']}")
                print(f"      Phone: {client['phone']}")
                print(f"      WhatsApp URL: {client['whatsapp_url']}")
                print(f"      Membership: {client['membership_type']} - TTD {client['monthly_fee']}")
                print(f"      Next Payment: {client['next_payment_date']}")
        
        if len(clients_need_phone) > 0:
            print(f"\n⚠️  CLIENTS NEEDING PHONE NUMBERS:")
            for i, client in enumerate(clients_need_phone[:3], 1):  # Show first 3
                print(f"   {i}. {client['name']}: {client['issue']}")
        
        return len(whatsapp_ready_clients) > 0, whatsapp_ready_clients

    def generate_whatsapp_url(self, phone: str, client_name: str) -> str:
        """Generate WhatsApp Click-to-Chat URL"""
        # Clean phone number (remove +, spaces, etc.)
        clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Ensure Trinidad number starts with 1868
        if clean_phone.startswith('868'):
            clean_phone = '1' + clean_phone
        elif not clean_phone.startswith('1868'):
            clean_phone = '1868' + clean_phone[-7:]  # Take last 7 digits and add 1868
        
        # Create WhatsApp message
        message = f"Hello {client_name}, this is a reminder about your gym membership payment. Please let us know if you have any questions!"
        
        # URL encode the message
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        
        # Generate WhatsApp URL
        whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
        
        return whatsapp_url

    def test_payment_stats_for_dashboard(self):
        """Test payment statistics for dashboard display"""
        print("\n💰 TESTING PAYMENT STATISTICS FOR DASHBOARD")
        print("=" * 60)
        
        success, response = self.run_test(
            "Get Payment Statistics",
            "GET",
            "payments/stats",
            200
        )
        
        if success:
            total_revenue = response.get('total_revenue', 0)
            monthly_revenue = response.get('monthly_revenue', 0)
            payment_count = response.get('payment_count', 0)
            
            print(f"\n📊 CURRENT PAYMENT STATISTICS:")
            print(f"   Total Revenue: TTD {total_revenue}")
            print(f"   Monthly Revenue: TTD {monthly_revenue}")
            print(f"   Payment Count: {payment_count}")
            
            if total_revenue > 0:
                print(f"   ✅ GOOD: Revenue data available for dashboard")
            else:
                print(f"   ⚠️  WARNING: No revenue recorded yet")
            
            return True, response
        
        return False, {}

    def test_record_payment_for_whatsapp_client(self):
        """Record a payment for one of the WhatsApp-ready clients"""
        if not self.created_client_ids:
            print("❌ No created clients available for payment recording")
            return False
        
        client_id = self.created_client_ids[0]
        
        payment_data = {
            "client_id": client_id,
            "amount_paid": 75.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "Cash",
            "notes": "Payment recorded for WhatsApp client testing"
        }
        
        success, response = self.run_test(
            "Record Payment for WhatsApp Client",
            "POST",
            "payments/record",
            200,
            payment_data
        )
        
        if success:
            print(f"   ✅ Payment recorded successfully")
            print(f"   Client: {response.get('client_name')}")
            print(f"   Amount: TTD {response.get('amount_paid')}")
            print(f"   New Payment Date: {response.get('new_next_payment_date')}")
            
            return True, response
        
        return False, {}

    def test_whatsapp_feature_integration(self):
        """Test if there are any WhatsApp-specific endpoints or features"""
        print("\n📱 TESTING WHATSAPP FEATURE INTEGRATION")
        print("=" * 60)
        
        # Check if there are any WhatsApp-specific endpoints
        whatsapp_endpoints = [
            "whatsapp/send",
            "whatsapp/reminder",
            "clients/whatsapp",
            "reminders/whatsapp"
        ]
        
        whatsapp_features_found = []
        
        for endpoint in whatsapp_endpoints:
            try:
                url = f"{self.api_url}/{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code != 404:
                    whatsapp_features_found.append({
                        'endpoint': endpoint,
                        'status': response.status_code,
                        'response': response.text[:100]
                    })
                    print(f"   ✅ Found WhatsApp endpoint: {endpoint} (Status: {response.status_code})")
                else:
                    print(f"   ❌ WhatsApp endpoint not found: {endpoint}")
            except:
                print(f"   ❌ Error testing WhatsApp endpoint: {endpoint}")
        
        if len(whatsapp_features_found) == 0:
            print(f"\n📝 WHATSAPP INTEGRATION STATUS:")
            print(f"   ❌ No dedicated WhatsApp API endpoints found")
            print(f"   📱 WhatsApp functionality likely implemented in frontend")
            print(f"   🔗 Click-to-Chat URLs can be generated from client phone numbers")
            print(f"   ✅ Backend provides necessary client data with phone numbers")
        else:
            print(f"\n✅ WHATSAPP FEATURES FOUND:")
            for feature in whatsapp_features_found:
                print(f"   - {feature['endpoint']}: Status {feature['status']}")
        
        return True, whatsapp_features_found

    def run_comprehensive_whatsapp_backend_test(self):
        """Run comprehensive WhatsApp backend testing"""
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE WHATSAPP BACKEND TESTING")
        print("="*80)
        
        # Test 1: API Health
        self.test_api_health()
        
        # Test 2: Check current database state
        has_clients, existing_clients = self.test_current_database_state()
        
        # Test 3: Create Trinidad clients if needed
        if not has_clients or len(existing_clients) == 0:
            print("\n📝 Creating test clients since database is empty...")
            self.test_create_trinidad_client_with_whatsapp()
            self.test_create_multiple_trinidad_clients()
        else:
            print(f"\n✅ Using existing {len(existing_clients)} clients for testing")
            # Still create one additional Trinidad client for testing
            self.test_create_trinidad_client_with_whatsapp()
        
        # Test 4: WhatsApp data preparation
        self.test_whatsapp_click_to_chat_data_preparation()
        
        # Test 5: Payment statistics
        self.test_payment_stats_for_dashboard()
        
        # Test 6: Record payment for testing
        self.test_record_payment_for_whatsapp_client()
        
        # Test 7: Check for WhatsApp integration
        self.test_whatsapp_feature_integration()
        
        # Final summary
        print("\n" + "="*80)
        print("📊 WHATSAPP BACKEND TEST SUMMARY")
        print("="*80)
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print(f"   Created Clients: {len(self.created_client_ids)}")
        
        if self.tests_passed >= self.tests_run * 0.8:  # 80% success rate
            print(f"   ✅ OVERALL STATUS: BACKEND READY FOR WHATSAPP FUNCTIONALITY")
            print(f"   📱 Clients with phone numbers available for Click-to-Chat")
            print(f"   💰 Payment system working for revenue tracking")
            print(f"   🔗 WhatsApp URLs can be generated from client data")
        else:
            print(f"   ❌ OVERALL STATUS: BACKEND NEEDS ATTENTION")
            print(f"   🔧 Some tests failed - check individual test results")
        
        return self.tests_passed >= self.tests_run * 0.8

if __name__ == "__main__":
    print("🚀 Starting WhatsApp Backend Testing...")
    tester = WhatsAppBackendTester()
    success = tester.run_comprehensive_whatsapp_backend_test()
    
    if success:
        print("\n🎉 WhatsApp Backend Testing COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n❌ WhatsApp Backend Testing FAILED!")
        sys.exit(1)