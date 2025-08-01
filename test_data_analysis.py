#!/usr/bin/env python3

import requests
import sys
import json
import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from collections import defaultdict

class TestDataAnalyzer:
    def __init__(self, base_url="https://8beb6460-0117-4864-a970-463f629aa57c.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.all_clients = []
        self.test_clients = []
        self.real_clients = []
        self.analytics_impact = {}

    def fetch_all_clients(self):
        """Fetch all clients from the API"""
        try:
            response = requests.get(f"{self.api_url}/clients", timeout=30)
            if response.status_code == 200:
                self.all_clients = response.json()
                print(f"✅ Successfully fetched {len(self.all_clients)} clients from database")
                return True
            else:
                print(f"❌ Failed to fetch clients: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error fetching clients: {str(e)}")
            return False

    def is_test_client(self, client):
        """Determine if a client is test/fake data based on various criteria"""
        test_indicators = []
        
        # Check name for test patterns
        name = client.get('name', '').lower()
        test_name_patterns = [
            'test', 'fake', 'demo', 'sample', 'example', 'dummy', 
            'john doe', 'jane doe', 'foo', 'bar', 'lorem', 'ipsum',
            'admin', 'debug', 'temp', 'temporary', 'placeholder'
        ]
        
        for pattern in test_name_patterns:
            if pattern in name:
                test_indicators.append(f"Name contains '{pattern}'")
                break
        
        # Check email for test patterns
        email = client.get('email', '').lower()
        test_email_patterns = [
            '@example.com', '@test.com', '@demo.com', '@sample.com',
            '@fake.com', '@dummy.com', '@localhost', '@tempmail',
            'test@', 'demo@', 'fake@', 'sample@', 'admin@',
            'noreply@', 'donotreply@'
        ]
        
        for pattern in test_email_patterns:
            if pattern in email:
                test_indicators.append(f"Email contains '{pattern}'")
                break
        
        # Check for sequential/pattern-based emails
        if re.search(r'test_?\d+@', email) or re.search(r'user_?\d+@', email):
            test_indicators.append("Sequential test email pattern")
        
        # Check phone numbers for test patterns
        phone = client.get('phone', '') or ''
        test_phone_patterns = [
            '(555)', '555-', '123-456', '000-000', '111-111',
            '999-999', '(123)', '(000)', '(111)', '(999)'
        ]
        
        for pattern in test_phone_patterns:
            if pattern in phone:
                test_indicators.append(f"Phone contains test pattern '{pattern}'")
                break
        
        # Check for unrealistic membership fees (too low or too high)
        monthly_fee = client.get('monthly_fee', 0)
        if monthly_fee <= 10 or monthly_fee >= 500:
            test_indicators.append(f"Unrealistic monthly fee: ${monthly_fee}")
        
        # Check creation date patterns (bulk creation on same day)
        created_at = client.get('created_at', '')
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                # This will be checked in bulk analysis
            except:
                pass
        
        # Check for default/placeholder values
        if client.get('membership_type') == 'Test':
            test_indicators.append("Membership type is 'Test'")
        
        return test_indicators

    def analyze_client_data(self):
        """Analyze all clients and categorize them"""
        print("\n" + "="*80)
        print("🔍 ANALYZING CLIENT DATA FOR TEST/FAKE ENTRIES")
        print("="*80)
        
        if not self.all_clients:
            print("❌ No client data available for analysis")
            return False
        
        # Categorize clients
        bulk_creation_dates = defaultdict(list)
        
        for client in self.all_clients:
            test_indicators = self.is_test_client(client)
            
            if test_indicators:
                self.test_clients.append({
                    'client': client,
                    'indicators': test_indicators
                })
            else:
                self.real_clients.append(client)
            
            # Track creation dates for bulk analysis
            created_at = client.get('created_at', '')
            if created_at:
                try:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                    bulk_creation_dates[created_date].append(client)
                except:
                    pass
        
        # Check for bulk creation patterns
        for date_created, clients_on_date in bulk_creation_dates.items():
            if len(clients_on_date) >= 5:  # 5 or more clients created on same day
                print(f"\n⚠️  BULK CREATION DETECTED: {len(clients_on_date)} clients created on {date_created}")
                for client in clients_on_date:
                    # Check if already marked as test
                    already_test = any(tc['client']['id'] == client['id'] for tc in self.test_clients)
                    if not already_test:
                        # Add to test clients with bulk creation indicator
                        self.test_clients.append({
                            'client': client,
                            'indicators': [f"Bulk created on {date_created} with {len(clients_on_date)} others"]
                        })
                        # Remove from real clients if it was there
                        self.real_clients = [rc for rc in self.real_clients if rc['id'] != client['id']]
        
        return True

    def display_analysis_results(self):
        """Display the analysis results"""
        total_clients = len(self.all_clients)
        test_count = len(self.test_clients)
        real_count = len(self.real_clients)
        
        print(f"\n📊 CLIENT DATA ANALYSIS SUMMARY")
        print(f"{'='*50}")
        print(f"Total Clients in Database: {total_clients}")
        print(f"Identified Test/Fake Clients: {test_count} ({test_count/total_clients*100:.1f}%)")
        print(f"Identified Real Clients: {real_count} ({real_count/total_clients*100:.1f}%)")
        
        if test_count > 0:
            print(f"\n🚨 TEST/FAKE CLIENTS IDENTIFIED:")
            print(f"{'='*50}")
            
            for i, test_client_data in enumerate(self.test_clients, 1):
                client = test_client_data['client']
                indicators = test_client_data['indicators']
                
                print(f"\n{i}. {client.get('name', 'Unknown Name')}")
                print(f"   Email: {client.get('email', 'No email')}")
                print(f"   Phone: {client.get('phone', 'No phone')}")
                print(f"   Membership: {client.get('membership_type', 'Unknown')} - ${client.get('monthly_fee', 0)}/month")
                print(f"   Status: {client.get('status', 'Unknown')}")
                print(f"   Created: {client.get('created_at', 'Unknown')}")
                print(f"   🔍 Test Indicators:")
                for indicator in indicators:
                    print(f"      • {indicator}")
        
        if real_count > 0:
            print(f"\n✅ SAMPLE REAL CLIENTS:")
            print(f"{'='*50}")
            
            # Show first 5 real clients as examples
            for i, client in enumerate(self.real_clients[:5], 1):
                print(f"\n{i}. {client.get('name', 'Unknown Name')}")
                print(f"   Email: {client.get('email', 'No email')}")
                print(f"   Phone: {client.get('phone', 'No phone')}")
                print(f"   Membership: {client.get('membership_type', 'Unknown')} - ${client.get('monthly_fee', 0)}/month")
                print(f"   Status: {client.get('status', 'Unknown')}")
            
            if real_count > 5:
                print(f"\n   ... and {real_count - 5} more real clients")

    def calculate_analytics_impact(self):
        """Calculate how test data affects analytics"""
        print(f"\n💰 ANALYTICS IMPACT ASSESSMENT")
        print(f"{'='*50}")
        
        # Calculate revenue impact
        total_revenue = sum(client.get('monthly_fee', 0) for client in self.all_clients if client.get('status') == 'Active')
        test_revenue = sum(tc['client'].get('monthly_fee', 0) for tc in self.test_clients if tc['client'].get('status') == 'Active')
        real_revenue = total_revenue - test_revenue
        
        # Calculate member counts
        total_active = len([c for c in self.all_clients if c.get('status') == 'Active'])
        test_active = len([tc['client'] for tc in self.test_clients if tc['client'].get('status') == 'Active'])
        real_active = total_active - test_active
        
        # Calculate overdue payments (assuming next_payment_date < today means overdue)
        today = date.today()
        total_overdue = 0
        test_overdue = 0
        
        for client in self.all_clients:
            if client.get('status') == 'Active':
                next_payment = client.get('next_payment_date')
                if next_payment:
                    try:
                        payment_date = datetime.fromisoformat(next_payment).date() if isinstance(next_payment, str) else next_payment
                        if payment_date < today:
                            total_overdue += 1
                            # Check if this is a test client
                            if any(tc['client']['id'] == client['id'] for tc in self.test_clients):
                                test_overdue += 1
                    except:
                        pass
        
        real_overdue = total_overdue - test_overdue
        
        print(f"📈 REVENUE ANALYSIS:")
        print(f"   Total Monthly Revenue (with test data): TTD {total_revenue:,.2f}")
        print(f"   Test Data Revenue Impact: TTD {test_revenue:,.2f}")
        print(f"   Actual Business Revenue: TTD {real_revenue:,.2f}")
        if total_revenue > 0:
            print(f"   Revenue Inflation from Test Data: {test_revenue/total_revenue*100:.1f}%")
        
        print(f"\n👥 MEMBER COUNT ANALYSIS:")
        print(f"   Total Active Members (with test data): {total_active}")
        print(f"   Test/Fake Active Members: {test_active}")
        print(f"   Actual Active Members: {real_active}")
        if total_active > 0:
            print(f"   Member Count Inflation: {test_active/total_active*100:.1f}%")
        
        print(f"\n⏰ OVERDUE PAYMENTS ANALYSIS:")
        print(f"   Total Overdue (with test data): {total_overdue}")
        print(f"   Test Data Overdue: {test_overdue}")
        print(f"   Actual Overdue: {real_overdue}")
        if total_overdue > 0:
            print(f"   Overdue Count Inflation: {test_overdue/total_overdue*100:.1f}%")
        
        # Store for summary
        self.analytics_impact = {
            'total_revenue': total_revenue,
            'test_revenue': test_revenue,
            'real_revenue': real_revenue,
            'total_active': total_active,
            'test_active': test_active,
            'real_active': real_active,
            'total_overdue': total_overdue,
            'test_overdue': test_overdue,
            'real_overdue': real_overdue
        }

    def generate_cleanup_recommendations(self):
        """Generate recommendations for cleaning up test data"""
        print(f"\n🧹 CLEANUP RECOMMENDATIONS")
        print(f"{'='*50}")
        
        if len(self.test_clients) == 0:
            print("✅ No test/fake data detected. Database appears clean!")
            return
        
        print(f"📋 RECOMMENDED ACTIONS:")
        print(f"   1. Review and delete {len(self.test_clients)} identified test/fake clients")
        print(f"   2. This will improve analytics accuracy by:")
        
        impact = self.analytics_impact
        if impact.get('test_revenue', 0) > 0:
            print(f"      • Reducing revenue by TTD {impact['test_revenue']:,.2f} (removing inflated numbers)")
        if impact.get('test_active', 0) > 0:
            print(f"      • Reducing active member count by {impact['test_active']} (removing fake members)")
        if impact.get('test_overdue', 0) > 0:
            print(f"      • Reducing overdue count by {impact['test_overdue']} (removing fake overdue accounts)")
        
        print(f"\n🎯 PRIORITY CLEANUP LIST:")
        
        # Sort test clients by impact (revenue first, then by number of indicators)
        sorted_test_clients = sorted(
            self.test_clients, 
            key=lambda x: (
                x['client'].get('monthly_fee', 0) if x['client'].get('status') == 'Active' else 0,
                len(x['indicators'])
            ), 
            reverse=True
        )
        
        for i, test_client_data in enumerate(sorted_test_clients[:10], 1):  # Top 10 priority
            client = test_client_data['client']
            indicators = test_client_data['indicators']
            
            revenue_impact = client.get('monthly_fee', 0) if client.get('status') == 'Active' else 0
            print(f"\n   {i}. {client.get('name')} ({client.get('email')})")
            print(f"      Revenue Impact: TTD {revenue_impact}/month")
            print(f"      Client ID: {client.get('id')}")
            print(f"      Confidence: {len(indicators)} indicators")
        
        if len(self.test_clients) > 10:
            print(f"\n   ... and {len(self.test_clients) - 10} more test clients to review")
        
        print(f"\n⚠️  IMPORTANT NOTES:")
        print(f"   • Always backup database before bulk deletions")
        print(f"   • Review each client manually before deletion to avoid false positives")
        print(f"   • Consider archiving instead of deleting for audit trail")
        print(f"   • Update any reports or dashboards after cleanup")

    def export_test_client_list(self):
        """Export list of test clients for manual review"""
        if not self.test_clients:
            return
        
        print(f"\n📄 EXPORTABLE TEST CLIENT LIST")
        print(f"{'='*50}")
        print("Client ID,Name,Email,Phone,Membership,Monthly Fee,Status,Test Indicators")
        
        for test_client_data in self.test_clients:
            client = test_client_data['client']
            indicators = "; ".join(test_client_data['indicators'])
            
            print(f"{client.get('id', '')},{client.get('name', '')},{client.get('email', '')},{client.get('phone', '')},{client.get('membership_type', '')},{client.get('monthly_fee', 0)},{client.get('status', '')},\"{indicators}\"")

    def run_complete_analysis(self):
        """Run the complete test data analysis"""
        print("🚀 STARTING COMPREHENSIVE TEST DATA ANALYSIS")
        print("="*80)
        
        # Step 1: Fetch all clients
        if not self.fetch_all_clients():
            return False
        
        # Step 2: Analyze client data
        if not self.analyze_client_data():
            return False
        
        # Step 3: Display results
        self.display_analysis_results()
        
        # Step 4: Calculate analytics impact
        self.calculate_analytics_impact()
        
        # Step 5: Generate cleanup recommendations
        self.generate_cleanup_recommendations()
        
        # Step 6: Export test client list
        self.export_test_client_list()
        
        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"{'='*80}")
        
        return True

def main():
    """Main function to run the test data analysis"""
    analyzer = TestDataAnalyzer()
    
    try:
        success = analyzer.run_complete_analysis()
        
        if success:
            print("\n✅ Test data analysis completed successfully!")
            print("📋 Review the results above to identify and clean up test/fake data")
            print("💡 This will improve the accuracy of your business analytics")
        else:
            print("\n❌ Test data analysis failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error during analysis: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())