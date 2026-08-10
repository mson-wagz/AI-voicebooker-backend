#!/usr/bin/env python3
"""
Test script for making actual Vapi calls
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def make_test_call():
    """Make an outbound test call using Vapi API"""
    
    api_key = os.getenv("VAPI_API_KEY")
    phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
    
    if not api_key or not phone_number_id:
        print("❌ Missing VAPI_API_KEY or VAPI_PHONE_NUMBER_ID")
        return False
    
    print("📞 Making test call via Vapi...")
    
    # Create outbound call
    response = requests.post(
        "https://api.vapi.ai/call",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "assistant": {
                "firstMessage": "Hello! This is a test call from RestoVoice AI. I'm here to help you make a restaurant reservation. What restaurant would you like to book?",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.1
                },
                "voice": {
                    "provider": "vapi",
                    "voiceId": "Dan"
                }
            },
            "phoneNumberId": phone_number_id,
            "customer": {
                "number": "+254703222614"  # Your actual phone number to receive the call
            },
            "assistant": {
                "id": "a0451c17-f06f-4283-9398-f7ad09295538"  # Your RestoVoice assistant
            }
        }
    )
    
    if response.status_code in [200, 201]:
        call_data = response.json()
        call_id = call_data.get("id")
        print(f"✅ Call initiated successfully!")
        print(f"📞 Call ID: {call_id}")
        print(f"📞 Status: {call_data.get('status', 'unknown')}")
        print(f"📞 Assistant ID: {call_data.get('assistant', {}).get('id')}")
        return call_id
    else:
        print(f"❌ Failed to make call: {response.status_code}")
        print(f"📄 Error: {response.text}")
        return False

def get_call_status(call_id):
    """Get status of a call"""
    
    api_key = os.getenv("VAPI_API_KEY")
    
    response = requests.get(
        f"https://api.vapi.ai/call/{call_id}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to get call status: {response.status_code}")
        return None

if __name__ == "__main__":
    # Make test call
    call_id = make_test_call()
    
    if call_id:
        print(f"\n🔍 Checking call status...")
        status = get_call_status(call_id)
        if status:
            print(f"📊 Call Status: {status.get('status')}")
            print(f"📊 Duration: {status.get('analysis', {}).get('duration', 'N/A')} seconds")
            print(f"📊 Transcript available: {'Yes' if status.get('transcript') else 'No'}")
            print(f"📊 Summary: {status.get('analysis', {}).get('summary', 'N/A')}")
    
    print("\n📞 Your webhook endpoint should receive events for this call!")
    print("🌐 Webhook URL: http://localhost:8000/v1/vapi/webhooks/vapi")
