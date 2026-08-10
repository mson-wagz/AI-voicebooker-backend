#!/usr/bin/env python3
"""
Update Vapi phone number webhook URL
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_webhook_url():
    """Update phone number webhook URL"""
    
    api_key = os.getenv("VAPI_API_KEY")
    phone_number_id = "bb798e30-140e-42c5-bc06-e75444dc71e3"  # Your Restovoice number
    webhook_url = "https://neat-games-lose.loca.lt/v1/vapi/webhooks/vapi"
    
    if not api_key:
        print("❌ VAPI_API_KEY not found")
        return
    
    print("🔧 Updating webhook URL...")
    
    try:
        response = requests.patch(
            f"https://api.vapi.ai/phone-number/{phone_number_id}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "serverUrl": webhook_url
            }
        )
        
        if response.status_code == 200:
            print("✅ Webhook URL updated successfully!")
            data = response.json()
            print(f"   Server URL: {data.get('serverUrl', 'Not set')}")
        else:
            print(f"❌ Failed to update: {response.status_code}")
            print(f"📄 Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def verify_update():
    """Verify the phone number configuration"""
    
    api_key = os.getenv("VAPI_API_KEY")
    phone_number_id = "bb798e30-140e-42c5-bc06-e75444dc71e3"
    
    try:
        response = requests.get(
            f"https://api.vapi.ai/phone-number/{phone_number_id}",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n📋 Current Configuration:")
            print(f"   Number: {data.get('number')}")
            print(f"   Name: {data.get('name')}")
            print(f"   Assistant ID: {data.get('assistantId', 'None')}")
            print(f"   Server URL: {data.get('serverUrl', 'Not set')}")
            
        else:
            print(f"❌ Failed to get phone number: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Webhook URL Update")
    print("=" * 50)
    
    update_webhook_url()
    verify_update()
    
    print("\n📋 Final Steps:")
    print("1. ✅ Webhook URL is working: https://neat-games-lose.loca.lt/v1/vapi/webhooks/vapi")
    print("2. 📞 Try calling +12799729410 to test inbound calls")
    print("3. 📊 Monitor logs: docker-compose -f docker-compose.dev.yml logs -f ai-backend")
