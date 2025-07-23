#!/usr/bin/env python3

import requests
import json

def test_bulk_email_quick():
    """Quick test of bulk email with shorter timeout"""
    url = "https://6b64051f-ce9a-4270-be16-1060b67d4f80.preview.emergentagent.com/api/email/payment-reminder/bulk"
    headers = {'Content-Type': 'application/json'}
    
    print("🔍 Testing Bulk Email with 60 second timeout...")
    print(f"   URL: {url}")
    
    try:
        response = requests.post(url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Bulk Email Test - SUCCESS")
            print(f"   Total clients: {data.get('total_clients', 0)}")
            print(f"   Sent successfully: {data.get('sent_successfully', 0)}")
            print(f"   Failed: {data.get('failed', 0)}")
            
            # Show some results
            results = data.get('results', [])
            if results:
                print(f"   Sample results (first 5):")
                for i, result in enumerate(results[:5]):
                    status = "✅" if result.get('success') else "❌"
                    print(f"     {i+1}. {result.get('client_name')} ({result.get('client_email')}): {status}")
            
            return True
        else:
            print(f"❌ Bulk Email Test - FAILED (Status: {response.status_code})")
            return False
            
    except requests.exceptions.Timeout:
        print("⚠️  Bulk Email Test - TIMEOUT (but may still be processing on server)")
        return False
    except Exception as e:
        print(f"❌ Bulk Email Test - ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_bulk_email_quick()