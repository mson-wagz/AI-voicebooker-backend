#!/usr/bin/env python3
"""
Get Vapi assistant information
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def get_assistant_info():
    """Get all assistants and their IDs"""
    
    api_key = os.getenv("VAPI_API_KEY")
    if not api_key:
        print("❌ VAPI_API_KEY not found in environment variables")
        return
    
    print("🔍 Getting Vapi assistants...")
    
    try:
        response = requests.get(
            "https://api.vapi.ai/assistant",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get assistants: {response.status_code}")
            print(f"📄 Error: {response.text}")
            return
        
        assistants = response.json()
        
        if not assistants:
            print("❌ No assistants found")
            return
        
        print(f"✅ Found {len(assistants)} assistant(s):")
        print("=" * 60)
        
        for i, assistant in enumerate(assistants, 1):
            print(f"📞 Assistant {i}:")
            print(f"   ID: {assistant.get('id')}")
            print(f"   Name: {assistant.get('name', 'No name')}")
            print(f"   Model: {assistant.get('model', {}).get('model', 'Unknown')}")
            print(f"   Voice: {assistant.get('voice', {}).get('voiceId', 'Unknown')}")
            print(f"   First Message: {assistant.get('firstMessage', 'No message')[:100]}...")
            print()
        
        # Return the first assistant ID for easy use
        if assistants:
            print(f"🎯 First Assistant ID (copy this): {assistants[0]['id']}")
            return assistants[0]['id']
            
    except Exception as e:
        print(f"❌ Error getting assistants: {e}")
        return None

def get_phone_numbers():
    """Get all phone numbers and their configurations"""
    
    api_key = os.getenv("VAPI_API_KEY")
    if not api_key:
        print("❌ VAPI_API_KEY not found in environment variables")
        return
    
    print("📱 Getting Vapi phone numbers...")
    
    try:
        response = requests.get(
            "https://api.vapi.ai/phone-number",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get phone numbers: {response.status_code}")
            print(f"📄 Error: {response.text}")
            return
        
        phone_numbers = response.json()
        
        if not phone_numbers:
            print("❌ No phone numbers found")
            return
        
        print(f"✅ Found {len(phone_numbers)} phone number(s):")
        print("=" * 60)
        
        for i, pn in enumerate(phone_numbers, 1):
            print(f"📞 Phone Number {i}:")
            print(f"   ID: {pn.get('id')}")
            print(f"   Number: {pn.get('number')}")
            print(f"   Name: {pn.get('name', 'No name')}")
            print(f"   Provider: {pn.get('provider', 'Unknown')}")
            print(f"   Assistant ID: {pn.get('assistant', {}).get('id', 'None')}")
            print(f"   Webhook URL: {pn.get('webhookUrl', 'Not set')}")
            print()
            
    except Exception as e:
        print(f"❌ Error getting phone numbers: {e}")

if __name__ == "__main__":
    print("🧪 Vapi Configuration Checker")
    print("=" * 50)
    
    # Get assistant info
    assistant_id = get_assistant_info()
    
    print("\n" + "=" * 50)
    
    # Get phone number info
    get_phone_numbers()
    
    print("\n📋 Next Steps:")
    print("1. Update your Vapi phone number webhook URL to:")
    print("   https://little-peaches-make.loca.lt/v1/vapi/webhooks/vapi")
    print("2. Make sure your assistant is assigned to the phone number")
    print(f"3. Use the assistant ID above for your outbound calls")
