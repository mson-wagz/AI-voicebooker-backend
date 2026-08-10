#!/usr/bin/env python3
"""
Configure real inbound calling with Vapi
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def configure_inbound():
    """Configure inbound calling with real Vapi integration"""
    
    # Get Vapi configuration
    vapi_api_key = os.getenv("VAPI_API_KEY")
    phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
    
    if not vapi_api_key or not phone_number_id:
        print("❌ Missing VAPI_API_KEY or VAPI_PHONE_NUMBER_ID in .env")
        return
    
    print(f"🔧 Configuring inbound calling...")
    print(f"📞 Phone Number ID: {phone_number_id}")
    print(f"🌐 Webhook URL: https://sad-turtles-peel.loca.lt/v1/vapi/webhooks/vapi")
    
    # Create assistant for inbound calls
    assistant_data = {
        "name": "RestoVoice Reservation Agent",
        "model": {
            "provider": "openai",
            "model": "gpt-4"
        },
        "voice": {
            "provider": "vapi",
            "voiceId": "Clara"
        }
    }
    
    # Create assistant via Vapi API
    headers = {
        "Authorization": f"Bearer {vapi_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "https://api.vapi.ai/assistant",
            json=assistant_data,
            headers=headers
        )
        
        if response.status_code == 201:
            assistant = response.json()
            assistant_id = assistant["id"]
            print(f"✅ Assistant created: {assistant_id}")
            
            # Update phone number with assistant
            phone_update = {
                "assistantId": assistant_id
            }
            
            update_response = requests.patch(
                f"https://api.vapi.ai/phone-number/{phone_number_id}",
                json=phone_update,
                headers=headers
            )
            
            if update_response.status_code == 200:
                print(f"✅ Phone number updated with assistant")
                print(f"🎉 Inbound calling configured successfully!")
                print(f"📞 Call your Vapi number to test")
            else:
                print(f"❌ Failed to update phone number: {update_response.text}")
                
        else:
            print(f"❌ Failed to create assistant: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    configure_inbound()
