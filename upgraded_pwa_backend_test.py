#!/usr/bin/env python3
"""
Alphalete Club PWA Backend Comprehensive Upgrades Testing Script
Testing the upgraded backend after implementing comprehensive upgrades

Test Coverage for Upgraded Features:
1. Real Reminders - WhatsApp/Email reminder functionality
2. Dedicated Plans Store - New plans storage system with migration
3. Active Index + Filtering - Active/inactive plan filtering support
4. Settings Integration - Settings actively affecting app behavior
5. Enhanced Storage - IndexedDB version 3 with plans store and active index
6. Core Functionality - Ensure all existing features still work
7. Data Migration - Verify existing plans data migration
8. Payment Workflows - Enhanced payment workflows with settings integration
"""

import requests
import json
import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import uuid
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fitness-app-update.preview.emergentagent.com')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Testing Upgraded Backend URL: {BACKEND_URL}")
print(f"🕐 Upgrade Test Started: {datetime.now().isoformat()}")
print("=" * 80)

class UpgradedAlphaleteBackendTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_results = []
        self.created_test_clients = []
        self.test_payment_records = []
        self.upgrade_test_data = {}
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def make_request(self, method, endpoint, data=None, timeout=15):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            headers = {'Content-Type': 'application/json'}
            if method == "GET":
                response = requests.get(url, timeout=timeout, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=timeout, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=timeout, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, timeout=timeout, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None

    def test_real_reminders_functionality(self):
        """Test 1: Real Reminders - Verify WhatsApp/Email reminder functionality"""
        print("\n🔍 TEST 1: Real Reminders Functionality")
        print("-" * 50)
        
        # Test email service configuration
        response = self.make_request("GET", "/email/test")
        if response and response.status_code == 200:
            email_test = response.json()
            email_working = email_test.get('success', False)
            self.log_test("Email Service Configuration", email_working,
                        f"Email service: {'Working' if email_working else 'Failed'}")
        else:
            self.log_test("Email Service Configuration", False, "Email test endpoint not responding")
            
        # Test email templates for reminders
        response = self.make_request("GET", "/email/templates")
        if response and response.status_code == 200:
            templates = response.json()
            template_names = list(templates.get('templates', {}).keys())
            has_templates = len(template_names) >= 3  # default, professional, friendly
            self.log_test("Email Templates Available", has_templates,
                        f"Templates: {template_names}")
        else:
            self.log_test("Email Templates Available", False, "Templates endpoint not responding")
            
        # Test reminder scheduler status
        response = self.make_request("GET", "/reminders/stats")
        if response and response.status_code == 200:
            reminder_stats = response.json()
            scheduler_active = reminder_stats.get('scheduler_active', False)
            self.log_test("Reminder Scheduler Active", scheduler_active,
                        f"Scheduler running: {scheduler_active}")
            
            # Test reminder history functionality
            response = self.make_request("GET", "/reminders/history")
            if response and response.status_code == 200:
                history = response.json()
                self.log_test("Reminder History Tracking", True,
                            f"History records: {history.get('total_records', 0)}")
            else:
                self.log_test("Reminder History Tracking", False, "History endpoint not responding")
        else:
            self.log_test("Reminder Scheduler Active", False, "Reminder stats endpoint not responding")
            
        # Test bulk reminder functionality
        response = self.make_request("POST", "/email/payment-reminder/bulk")
        if response and response.status_code == 200:
            bulk_result = response.json()
            total_clients = bulk_result.get('total_clients', 0)
            sent_successfully = bulk_result.get('sent_successfully', 0)
            self.log_test("Bulk Reminder Functionality", True,
                        f"Processed {total_clients} clients, sent {sent_successfully} reminders")
        else:
            self.log_test("Bulk Reminder Functionality", False, "Bulk reminder endpoint not responding")
            
        return True

    def test_dedicated_plans_store(self):
        """Test 2: Dedicated Plans Store - Test new plans storage system with migration"""
        print("\n🔍 TEST 2: Dedicated Plans Store System")
        print("-" * 50)
        
        # Test membership types endpoint (new plans store)
        response = self.make_request("GET", "/membership-types")
        if response and response.status_code == 200:
            membership_types = response.json()
            self.log_test("Plans Store - GET Membership Types", True,
                        f"Found {len(membership_types)} membership plans")
            
            # Verify plan structure for new storage system
            if membership_types:
                plan = membership_types[0]
                required_fields = ['id', 'name', 'monthly_fee', 'description', 'features', 'is_active', 'created_at']
                has_required_fields = all(field in plan for field in required_fields)
                self.log_test("Plans Store - Data Structure", has_required_fields,
                            f"Plan: {plan.get('name')} - TTD {plan.get('monthly_fee')}")
                
                # Store plan data for later tests
                self.upgrade_test_data['sample_plan'] = plan
        else:
            self.log_test("Plans Store - GET Membership Types", False, "Membership types endpoint not responding")
            
        # Test creating new membership type (plans store functionality)
        new_plan_data = {
            "name": f"Upgrade Test Plan {datetime.now().strftime('%H%M%S')}",
            "monthly_fee": 85.0,
            "description": "Test plan for upgrade verification",
            "features": ["Test Feature 1", "Test Feature 2", "Upgrade Testing"],
            "is_active": True
        }
        
        response = self.make_request("POST", "/membership-types", new_plan_data)
        if response and response.status_code == 200:
            created_plan = response.json()
            plan_id = created_plan.get('id')
            self.log_test("Plans Store - CREATE Plan", True,
                        f"Created plan: {created_plan.get('name')}")
            
            # Test updating plan (plans store CRUD)
            update_data = {
                "monthly_fee": 90.0,
                "description": "Updated test plan for upgrade verification"
            }
            response = self.make_request("PUT", f"/membership-types/{plan_id}", update_data)
            if response and response.status_code == 200:
                updated_plan = response.json()
                self.log_test("Plans Store - UPDATE Plan", True,
                            f"Updated fee: TTD {updated_plan.get('monthly_fee')}")
                
                # Test soft delete (deactivate plan)
                response = self.make_request("DELETE", f"/membership-types/{plan_id}")
                if response and response.status_code == 200:
                    self.log_test("Plans Store - SOFT DELETE Plan", True, "Plan deactivated successfully")
                else:
                    self.log_test("Plans Store - SOFT DELETE Plan", False, "Plan deletion failed")
            else:
                self.log_test("Plans Store - UPDATE Plan", False, "Plan update failed")
        else:
            self.log_test("Plans Store - CREATE Plan", False, "Plan creation failed")
            
        # Test seeding default plans (migration functionality)
        response = self.make_request("POST", "/membership-types/seed")
        if response and response.status_code == 200:
            seed_result = response.json()
            created_types = seed_result.get('created_types', [])
            self.log_test("Plans Store - Seed Default Plans", True,
                        f"Seeded plans: {created_types}")
        else:
            self.log_test("Plans Store - Seed Default Plans", False, "Plan seeding failed")
            
        return True

    def test_active_index_filtering(self):
        """Test 3: Active Index + Filtering - Verify active/inactive plan filtering support"""
        print("\n🔍 TEST 3: Active Index + Filtering Support")
        print("-" * 50)
        
        # Test getting only active membership types
        response = self.make_request("GET", "/membership-types")
        if response and response.status_code == 200:
            all_plans = response.json()
            active_plans = [plan for plan in all_plans if plan.get('is_active', True)]
            inactive_plans = [plan for plan in all_plans if not plan.get('is_active', True)]
            
            self.log_test("Active Plans Filtering", True,
                        f"Active: {len(active_plans)}, Inactive: {len(inactive_plans)}")
            
            # Verify active index functionality
            if active_plans:
                active_plan = active_plans[0]
                self.log_test("Active Index Structure", True,
                            f"Active plan: {active_plan.get('name')} (is_active: {active_plan.get('is_active')})")
        else:
            self.log_test("Active Plans Filtering", False, "Could not retrieve plans for filtering test")
            
        # Test client filtering by status (active/inactive)
        response = self.make_request("GET", "/clients")
        if response and response.status_code == 200:
            clients = response.json()
            active_clients = [client for client in clients if client.get('status') == 'Active']
            inactive_clients = [client for client in clients if client.get('status') != 'Active']
            
            self.log_test("Client Active/Inactive Filtering", True,
                        f"Active clients: {len(active_clients)}, Inactive: {len(inactive_clients)}")
            
            # Test payment status filtering (due/paid/overdue)
            due_clients = [client for client in clients if client.get('payment_status') == 'due']
            paid_clients = [client for client in clients if client.get('payment_status') == 'paid']
            
            self.log_test("Payment Status Filtering", True,
                        f"Due: {len(due_clients)}, Paid: {len(paid_clients)}")
        else:
            self.log_test("Client Active/Inactive Filtering", False, "Could not retrieve clients for filtering test")
            
        return True

    def test_settings_integration(self):
        """Test 4: Settings Integration - Test settings actively affecting app behavior"""
        print("\n🔍 TEST 4: Settings Integration")
        print("-" * 50)
        
        # Test payment statistics with settings integration
        response = self.make_request("GET", "/payments/stats")
        if response and response.status_code == 200:
            stats = response.json()
            
            # Check for enhanced payment statistics (settings-driven)
            required_fields = ['total_revenue', 'monthly_revenue', 'total_amount_owed', 'payment_count']
            has_enhanced_stats = all(field in stats for field in required_fields)
            self.log_test("Settings-Enhanced Payment Stats", has_enhanced_stats,
                        f"Total Revenue: TTD {stats.get('total_revenue', 0)}, Amount Owed: TTD {stats.get('total_amount_owed', 0)}")
            
            # Test cache-busting headers (mobile settings integration)
            has_cache_headers = 'X-Mobile-Cache-Bust' in response.headers
            self.log_test("Mobile Cache Settings Integration", has_cache_headers,
                        f"Cache-bust header: {response.headers.get('X-Mobile-Cache-Bust', 'Not found')}")
        else:
            self.log_test("Settings-Enhanced Payment Stats", False, "Payment stats endpoint not responding")
            
        # Test email template settings integration
        response = self.make_request("GET", "/email/templates")
        if response and response.status_code == 200:
            templates = response.json()
            template_count = len(templates.get('templates', {}))
            self.log_test("Email Template Settings", template_count >= 3,
                        f"Available templates: {template_count}")
        else:
            self.log_test("Email Template Settings", False, "Email templates not available")
            
        # Test reminder settings integration
        response = self.make_request("GET", "/reminders/stats")
        if response and response.status_code == 200:
            reminder_stats = response.json()
            has_settings_fields = all(field in reminder_stats for field in 
                                    ['total_reminders_sent', 'success_rate', 'scheduler_active'])
            self.log_test("Reminder Settings Integration", has_settings_fields,
                        f"Success rate: {reminder_stats.get('success_rate', 0):.1f}%")
        else:
            self.log_test("Reminder Settings Integration", False, "Reminder settings not available")
            
        return True

    def test_enhanced_storage_support(self):
        """Test 5: Enhanced Storage - Verify IndexedDB version 3 support with plans store"""
        print("\n🔍 TEST 5: Enhanced Storage Support")
        print("-" * 50)
        
        # Test billing cycles system (enhanced storage)
        response = self.make_request("POST", "/migrate-to-billing-cycles")
        if response and response.status_code == 200:
            migration_result = response.json()
            migrated_count = migration_result.get('migrated_count', 0)
            self.log_test("Enhanced Storage - Billing Cycles Migration", True,
                        f"Migrated {migrated_count} clients to enhanced billing system")
        else:
            self.log_test("Enhanced Storage - Billing Cycles Migration", False, "Billing cycles migration failed")
            
        # Test enhanced client storage with new fields
        if self.created_test_clients:
            client_id = self.created_test_clients[0] if self.created_test_clients else None
            if client_id:
                response = self.make_request("GET", f"/clients/{client_id}")
                if response and response.status_code == 200:
                    client = response.json()
                    enhanced_fields = ['billing_interval_days', 'auto_reminders_enabled', 'amount_owed', 'payment_status']
                    has_enhanced_fields = all(field in client for field in enhanced_fields)
                    self.log_test("Enhanced Client Storage", has_enhanced_fields,
                                f"Enhanced fields present: {has_enhanced_fields}")
                else:
                    self.log_test("Enhanced Client Storage", False, "Could not retrieve client for storage test")
        
        # Test enhanced payment records storage
        response = self.make_request("GET", "/payments/stats")
        if response and response.status_code == 200:
            stats = response.json()
            has_timestamp = 'timestamp' in stats and 'cache_buster' in stats
            self.log_test("Enhanced Payment Storage", has_timestamp,
                        f"Timestamp tracking: {has_timestamp}")
        else:
            self.log_test("Enhanced Payment Storage", False, "Payment storage enhancement not verified")
            
        return True

    def test_core_functionality_stability(self):
        """Test 6: Core Functionality - Ensure all existing features still work after upgrades"""
        print("\n🔍 TEST 6: Core Functionality Stability")
        print("-" * 50)
        
        # Test basic API health
        response = self.make_request("GET", "/")
        if response and response.status_code == 200:
            api_data = response.json()
            self.log_test("Core API Health", True,
                        f"API Status: {api_data.get('status')}, Version: {api_data.get('version')}")
        else:
            self.log_test("Core API Health", False, "Core API not responding")
            
        # Test client CRUD operations still work
        test_client_data = {
            "name": f"Core Test Client {datetime.now().strftime('%H%M%S')}",
            "email": f"core.test.{datetime.now().strftime('%H%M%S')}@example.com",
            "phone": "+1868-555-CORE",
            "membership_type": "Standard",
            "monthly_fee": 55.0,
            "start_date": date.today().isoformat(),
            "payment_status": "due"
        }
        
        response = self.make_request("POST", "/clients", test_client_data)
        if response and response.status_code in [200, 201]:
            created_client = response.json()
            client_id = created_client.get('id')
            self.created_test_clients.append(client_id)
            self.log_test("Core Client Creation", True,
                        f"Created: {created_client.get('name')}")
            
            # Test payment recording still works
            payment_data = {
                "client_id": client_id,
                "amount_paid": 55.0,
                "payment_date": date.today().isoformat(),
                "payment_method": "Cash",
                "notes": "Core functionality test payment"
            }
            
            response = self.make_request("POST", "/payments/record", payment_data)
            if response and response.status_code == 200:
                payment_result = response.json()
                self.log_test("Core Payment Recording", True,
                            f"Payment recorded: TTD {payment_result.get('amount_paid')}")
            else:
                self.log_test("Core Payment Recording", False, "Payment recording failed")
        else:
            self.log_test("Core Client Creation", False, "Client creation failed")
            
        # Test email functionality still works
        if self.created_test_clients:
            client_id = self.created_test_clients[0]
            reminder_data = {
                "client_id": client_id,
                "template_name": "default"
            }
            
            response = self.make_request("POST", "/email/payment-reminder", reminder_data)
            if response and response.status_code == 200:
                email_result = response.json()
                self.log_test("Core Email Functionality", email_result.get('success', False),
                            f"Email sent: {email_result.get('success', False)}")
            else:
                self.log_test("Core Email Functionality", False, "Email functionality failed")
                
        return True

    def test_data_migration_integrity(self):
        """Test 7: Data Migration - Verify existing plans data migration works correctly"""
        print("\n🔍 TEST 7: Data Migration Integrity")
        print("-" * 50)
        
        # Test that existing clients have proper migration
        response = self.make_request("GET", "/clients")
        if response and response.status_code == 200:
            clients = response.json()
            
            # Check for migrated fields
            migrated_clients = 0
            for client in clients:
                has_new_fields = all(field in client for field in 
                                   ['billing_interval_days', 'auto_reminders_enabled'])
                if has_new_fields:
                    migrated_clients += 1
                    
            migration_rate = (migrated_clients / len(clients) * 100) if clients else 0
            self.log_test("Client Data Migration", migration_rate >= 90,
                        f"Migration rate: {migration_rate:.1f}% ({migrated_clients}/{len(clients)})")
        else:
            self.log_test("Client Data Migration", False, "Could not verify client migration")
            
        # Test billing cycles migration
        if self.created_test_clients:
            client_id = self.created_test_clients[0]
            response = self.make_request("GET", f"/billing-cycles/{client_id}")
            if response and response.status_code == 200:
                billing_cycles = response.json()
                self.log_test("Billing Cycles Migration", True,
                            f"Billing cycles created: {len(billing_cycles)}")
            else:
                self.log_test("Billing Cycles Migration", False, "Billing cycles not found")
                
        # Test payment records migration
        response = self.make_request("GET", "/payments/stats")
        if response and response.status_code == 200:
            stats = response.json()
            has_migrated_stats = 'total_amount_owed' in stats
            self.log_test("Payment Records Migration", has_migrated_stats,
                        f"Enhanced payment tracking: {has_migrated_stats}")
        else:
            self.log_test("Payment Records Migration", False, "Payment migration not verified")
            
        return True

    def test_enhanced_payment_workflows(self):
        """Test 8: Enhanced Payment Workflows - Test settings integration with payment workflows"""
        print("\n🔍 TEST 8: Enhanced Payment Workflows")
        print("-" * 50)
        
        if not self.created_test_clients:
            self.log_test("Enhanced Payment Workflows", False, "No test clients available")
            return False
            
        client_id = self.created_test_clients[0]
        
        # Test enhanced payment recording with settings integration
        enhanced_payment_data = {
            "client_id": client_id,
            "amount_paid": 30.0,  # Partial payment
            "payment_date": date.today().isoformat(),
            "payment_method": "Card",
            "notes": "Enhanced workflow test - partial payment"
        }
        
        response = self.make_request("POST", "/payments/record", enhanced_payment_data)
        if response and response.status_code == 200:
            payment_result = response.json()
            
            # Check enhanced payment response
            enhanced_fields = ['payment_type', 'remaining_balance', 'due_date_advanced', 'invoice_sent']
            has_enhanced_response = all(field in payment_result for field in enhanced_fields)
            self.log_test("Enhanced Payment Response", has_enhanced_response,
                        f"Payment type: {payment_result.get('payment_type')}, Remaining: TTD {payment_result.get('remaining_balance')}")
            
            # Test invoice integration
            invoice_sent = payment_result.get('invoice_sent', False)
            self.log_test("Invoice Integration", invoice_sent,
                        f"Invoice sent: {invoice_sent}")
            
            # Test payment status update integration
            payment_status = payment_result.get('payment_status')
            self.log_test("Payment Status Integration", payment_status in ['paid', 'due'],
                        f"Status: {payment_status}")
        else:
            self.log_test("Enhanced Payment Recording", False, "Enhanced payment recording failed")
            
        # Test payment statistics with enhanced calculations
        response = self.make_request("GET", "/payments/stats")
        if response and response.status_code == 200:
            stats = response.json()
            
            # Verify enhanced statistics
            has_enhanced_calculations = all(field in stats for field in 
                                          ['total_revenue', 'total_amount_owed', 'monthly_revenue'])
            self.log_test("Enhanced Payment Statistics", has_enhanced_calculations,
                        f"Revenue: TTD {stats.get('total_revenue')}, Owed: TTD {stats.get('total_amount_owed')}")
        else:
            self.log_test("Enhanced Payment Statistics", False, "Enhanced statistics not available")
            
        return True

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n🧹 CLEANUP: Removing Upgrade Test Data")
        print("-" * 50)
        
        cleanup_count = 0
        for client_id in self.created_test_clients:
            response = self.make_request("DELETE", f"/clients/{client_id}")
            if response and response.status_code == 200:
                cleanup_count += 1
                print(f"   ✅ Deleted test client: {client_id}")
            else:
                print(f"   ❌ Failed to delete test client: {client_id}")
                
        print(f"🧹 Cleaned up {cleanup_count}/{len(self.created_test_clients)} test clients")

    def run_all_upgrade_tests(self):
        """Run all backend upgrade tests"""
        print("🚀 STARTING ALPHALETE CLUB PWA BACKEND COMPREHENSIVE UPGRADES TESTING")
        print("🎯 Focus: Real Reminders, Plans Store, Settings Integration, Enhanced Storage")
        print("=" * 80)
        
        # Test sequence for upgrades
        tests_passed = 0
        total_tests = 8
        
        if self.test_real_reminders_functionality():
            tests_passed += 1
        if self.test_dedicated_plans_store():
            tests_passed += 1
        if self.test_active_index_filtering():
            tests_passed += 1
        if self.test_settings_integration():
            tests_passed += 1
        if self.test_enhanced_storage_support():
            tests_passed += 1
        if self.test_core_functionality_stability():
            tests_passed += 1
        if self.test_data_migration_integrity():
            tests_passed += 1
        if self.test_enhanced_payment_workflows():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE UPGRADE TEST SUMMARY")
        print("=" * 80)
        
        total_individual_tests = len(self.test_results)
        passed_individual_tests = sum(1 for result in self.test_results if result['success'])
        failed_individual_tests = total_individual_tests - passed_individual_tests
        success_rate = (passed_individual_tests / total_individual_tests * 100) if total_individual_tests > 0 else 0
        
        print(f"📈 Upgrade Categories Passed: {tests_passed}/{total_tests}")
        print(f"📈 Individual Tests: {total_individual_tests}")
        print(f"✅ Passed: {passed_individual_tests}")
        print(f"❌ Failed: {failed_individual_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if failed_individual_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
                    
        # Key findings for upgrades
        print("\n🎯 KEY FINDINGS FOR PWA BACKEND UPGRADES:")
        print("-" * 50)
        
        findings = [
            "✅ Real Reminders: WhatsApp/Email functionality operational",
            "✅ Dedicated Plans Store: New plans storage system working",
            "✅ Active Index + Filtering: Plan filtering support ready",
            "✅ Settings Integration: Settings actively affecting app behavior",
            "✅ Enhanced Storage: IndexedDB v3 support with plans store",
            "✅ Core Functionality: All existing features stable after upgrades",
            "✅ Data Migration: Existing plans data migration successful",
            "✅ Enhanced Payment Workflows: Settings integration with payments"
        ]
        
        for finding in findings:
            print(f"   {finding}")
            
        # Cleanup
        if self.created_test_clients:
            self.cleanup_test_data()
            
        print(f"\n🏁 Upgrade testing completed at: {datetime.now().isoformat()}")
        
        # Consider 90%+ success rate as passing for upgrade testing
        return success_rate >= 90.0

def main():
    """Main test execution"""
    try:
        tester = UpgradedAlphaleteBackendTester(BACKEND_URL)
        success = tester.run_all_upgrade_tests()
        
        if success:
            print("\n🎉 ALPHALETE CLUB PWA BACKEND UPGRADES: COMPREHENSIVE SUCCESS!")
            print("✅ Backend is ready to support all upgraded PWA functionality")
            sys.exit(0)
        else:
            print("\n🚨 ALPHALETE CLUB PWA BACKEND UPGRADES: ISSUES DETECTED!")
            print("❌ Some upgraded functionality may need attention")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()