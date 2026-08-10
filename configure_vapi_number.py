#!/usr/bin/env python3
"""
Configure Vapi provider number for inbound calls
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def configure_vapi_number():
    """Configure Vapi provider number with assistant and webhook"""
    
    api_key = os.getenv("VAPI_API_KEY")
    phone_number_id = "7714a9b1-6771-486f-a9d1-d79d7b3cd6c7"  # Vapi provider number
    assistant_id = "a0451c17-f06f-4283-9398-f7ad09295538"  # Your RestoVoice assistant
    webhook_url = "https://neat-games-lose.loca.lt/v1/vapi/webhooks/vapi"
    
    if not api_key:
        print("❌ VAPI_API_KEY not found")
        return
    
    print("🔧 Configuring Vapi provider number...")
    
    try:
        response = requests.patch(
            f"https://api.vapi.ai/phone-number/{phone_number_id}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "name": "RestoVoice Vapi Number",
                "assistantId": assistant_id,
                "serverUrl": webhook_url
            }
        )
        
        if response.status_code == 200:
            print("✅ Vapi number configured successfully!")
            data = response.json()
            print(f"   Name: {data.get('name')}")
            print(f"   Number: {data.get('number')}")
            print(f"   Provider: {data.get('provider')}")
            print(f"   Assistant ID: {data.get('assistantId', 'None')}")
            print(f"   Server URL: {data.get('serverUrl', 'Not set')}")
        else:
            print(f"❌ Failed to configure: {response.status_code}")
            print(f"📄 Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def verify_configuration():
    """Verify the Vapi number configuration"""
    
    api_key = os.getenv("VAPI_API_KEY")
    phone_number_id = "7714a9b1-6771-486f-a9d1-d79d7b3cd6c7"
    
    try:
        response = requests.get(
            f"https://api.vapi.ai/phone-number/{phone_number_id}",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n📋 Vapi Number Configuration:")
            print(f"   Number: {data.get('number')}")
            print(f"   Name: {data.get('name')}")
            print(f"   Provider: {data.get('provider')}")
            print(f"   Assistant ID: {data.get('assistantId', 'None')}")
            print(f"   Server URL: {data.get('serverUrl', 'Not set')}")
            
        else:
            print(f"❌ Failed to get phone number: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Configure Vapi Provider Number")
    print("=" * 50)
    
    configure_vapi_number()
    verify_configuration()
    
    print("\n📋 Test Inbound Calls:")
    print("📞 Call the Vapi number: +17179989304")
    print("📊 Monitor logs: docker-compose -f docker-compose.dev.yml logs -f ai-backend")
    print("✅ This should bypass Twilio trial limitations!")
