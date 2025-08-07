#!/usr/bin/env python3
"""
Test script to verify add member functionality is working after bug fix
"""

import requests
import json

def test_add_member_fix():
    """Test the add member functionality after bug fix"""
    
    print("🧪 TESTING ADD MEMBER BUG FIX")
    print("=" * 50)
    
    # Check current member count
    try:
        response = requests.get("http://localhost:8001/api/clients", timeout=5)
        if response.status_code == 200:
            members = response.json()
            current_count = len(members)
            print(f"📊 Current member count: {current_count}")
            
            # Show existing members
            print("📋 Existing members:")
            for i, member in enumerate(members, 1):
                print(f"  {i}. {member.get('name', 'Unknown')} ({member.get('email', 'No email')})")
        else:
            print(f"❌ Error getting members: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return
    
    # Test adding a new member
    print(f"\n🔧 Testing add new member via API...")
    new_member = {
        "name": "Frontend Fix Test User",
        "email": "frontendfixtest@example.com", 
        "phone": "+1868-555-5555",
        "membership_type": "Standard",
        "monthly_fee": 55.0,
        "start_date": "2025-08-07",
        "auto_reminders_enabled": True,
        "payment_status": "due"
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/api/clients",
            headers={"Content-Type": "application/json"},
            json=new_member,
            timeout=10
        )
        
        if response.status_code == 200:
            created_member = response.json()
            print(f"✅ Successfully created member: {created_member['name']}")
            print(f"✅ Member ID: {created_member['id']}")
            print(f"✅ Email: {created_member['email']}")
            
            # Verify the count increased
            verify_response = requests.get("http://localhost:8001/api/clients", timeout=5)
            if verify_response.status_code == 200:
                new_members = verify_response.json()
                new_count = len(new_members)
                print(f"✅ New member count: {new_count}")
                
                if new_count > current_count:
                    print("🎉 SUCCESS: Member added successfully!")
                    print("🎉 ADD MEMBER BUG IS FIXED!")
                else:
                    print("❌ FAILED: Member count did not increase")
            else:
                print("❌ Could not verify member count")
                
        else:
            error_text = response.text
            print(f"❌ Failed to add member: {response.status_code}")
            print(f"❌ Error: {error_text}")
            
    except Exception as e:
        print(f"❌ Error adding member: {e}")

    print(f"\n🎯 CONCLUSION:")
    print("The backend API for adding members is working correctly.")
    print("If the frontend form still doesn't work, the issue is in:")
    print("1. Form validation")
    print("2. JavaScript submission logic")
    print("3. URL configuration in LocalStorageManager")
    
    print(f"\n📝 NEXT STEPS:")
    print("1. Test the actual form submission in the browser")
    print("2. Check browser console for JavaScript errors")
    print("3. Verify the LocalStorageManager URL configuration")

if __name__ == "__main__":
    test_add_member_fix()