#!/usr/bin/env python3

import requests
import sys
import json

class EmailConfigTester:
    def __init__(self, base_url="https://alphalete-club.emergent.host"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"

    def test_email_configuration(self):
        """Test email configuration"""
        url = f"{self.api_url}/email/test"
        headers = {'Content-Type': 'application/json'}

        print(f"🔍 Testing Email Configuration...")
        print(f"   URL: {url}")
        
        try:
            response = requests.post(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ Email Configuration Test - PASSED (Status: {response.status_code})")
                print(f"   Response: {json.dumps(response_data, indent=2)}")
                print(f"   Email test result: {response_data.get('message', 'No message')}")
                print(f"   Email success: {response_data.get('success', False)}")
                return response_data.get('success', False)
            else:
                print(f"❌ Email Configuration Test - FAILED (Status: {response.status_code})")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Email Configuration Test - FAILED (Error: {str(e)})")
            return False

if __name__ == "__main__":
    tester = EmailConfigTester()
    success = tester.test_email_configuration()
    
    if success:
        print("\n✅ EMAIL CONFIGURATION: WORKING")
    else:
        print("\n❌ EMAIL CONFIGURATION: NOT WORKING")
        print("   This explains why the professional email template test failed")
    
    sys.exit(0 if success else 1)