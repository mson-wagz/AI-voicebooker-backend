#!/usr/bin/env python3
"""
Check Vapi configuration and available phone numbers
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_vapi_setup():
    """Check Vapi API connection and phone numbers"""
    
    api_key = os.getenv("VAPI_API_KEY")
    
    if not api_key:
        print("❌ VAPI_API_KEY not found in .env")
        return False
    
    print("🔍 Checking Vapi setup...")
    
    # Get phone numbers
    response = requests.get(
        "https://api.vapi.ai/phone-number",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        phone_numbers = response.json()
        print(f"✅ Found {len(phone_numbers)} phone number(s):")
        
        for phone in phone_numbers:
            print(f"📞 {phone.get('name', 'Unknown')}")
            print(f"   Number: {phone.get('number', 'N/A')}")
            print(f"   ID: {phone.get('id', 'N/A')}")
            print(f"   Provider: {phone.get('provider', 'N/A')}")
            print()
        
        return True
    else:
        print(f"❌ Failed to get phone numbers: {response.status_code}")
        print(f"📄 Error: {response.text}")
        return False

def get_assistants():
    """Get available Vapi assistants"""
    
    api_key = os.getenv("VAPI_API_KEY")
    
    response = requests.get(
        "https://api.vapi.ai/assistant",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        assistants = response.json()
        print(f"✅ Found {len(assistants)} assistant(s):")
        
        for assistant in assistants:
            print(f"🤖 {assistant.get('name', 'Unknown')}")
            print(f"   ID: {assistant.get('id', 'N/A')}")
            print(f"   Model: {assistant.get('model', {}).get('model', 'N/A')}")
            print(f"   Voice: {assistant.get('voice', {}).get('provider', 'N/A')}")
            print()
        
        return assistants
    else:
        print(f"❌ Failed to get assistants: {response.status_code}")
        return []

if __name__ == "__main__":
    print("🔧 Vapi Configuration Check")
    print("=" * 50)
    
    # Check phone numbers
    check_vapi_setup()
    
    print("\n🤖 Available Assistants:")
    print("=" * 50)
    get_assistants()
    
    print("\n📞 To make a test call:")
    print("1. Run: python test_vapi_call.py")
    print("2. Or call your Vapi phone number directly")
    print("3. Watch the webhook logs: docker-compose -f docker-compose.dev.yml logs -f ai-backend")
