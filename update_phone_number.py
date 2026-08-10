#!/usr/bin/env python3
"""
Update Vapi phone number configuration
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_phone_number():
    """Update phone number with assistant and webhook URL"""
    
    api_key = os.getenv("VAPI_API_KEY")
    phone_number_id = "bb798e30-140e-42c5-bc06-e75444dc71e3"  # Your Restovoice number
    assistant_id = "a0451c17-f06f-4283-9398-f7ad09295538"  # Your RestoVoice assistant
    webhook_url = "https://olive-coins-move.loca.lt/v1/vapi/webhooks/vapi"
    
    if not api_key:
        print("❌ VAPI_API_KEY not found")
        return
    
    print("🔧 Updating phone number configuration...")
    
    try:
        response = requests.patch(
            f"https://api.vapi.ai/phone-number/{phone_number_id}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "assistantId": assistant_id
            }
        )
        
        if response.status_code == 200:
            print("✅ Phone number updated successfully!")
            data = response.json()
            print(f"   Assistant ID: {data.get('assistant', {}).get('id', 'None')}")
            print(f"   Webhook URL: {data.get('webhookUrl', 'Not set')}")
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
            print(f"   Assistant ID: {data.get('assistant', {}).get('id', 'None')}")
            print(f"   Webhook URL: {data.get('webhookUrl', 'Not set')}")
            
        else:
            print(f"❌ Failed to get phone number: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Phone Number Configuration Update")
    print("=" * 50)
    
    update_phone_number()
    verify_update()
    
    print("\n📋 Next Steps:")
    print("1. Try calling +12799729410 to test inbound calls")
    print("2. Monitor logs: docker-compose -f docker-compose.dev.yml logs -f ai-backend")
