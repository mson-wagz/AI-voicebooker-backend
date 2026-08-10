#!/usr/bin/env python3
"""
Test inbound call by simulating webhook events
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def simulate_inbound_call():
    """Simulate an inbound call to test webhook processing"""
    
    print("📞 Simulating inbound call flow...")
    
    # Step 1: Assistant request (AI speaks first)
    print("\n1️⃣ Sending assistant.request event (AI speaks first)...")
    assistant_request_payload = {
        "type": "assistant.request",
        "call": {
            "id": "test_call_12345",
            "status": "ringing",
            "phone_number": "+254703222614"
        },
        "timestamp": "2024-03-21T15:55:00Z"
    }
    
    response = requests.post(
        "http://localhost:8000/v1/vapi/webhooks/vapi",
        json=assistant_request_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print("✅ Assistant request sent successfully - AI should greet first!")
    else:
        print(f"❌ Failed to send assistant.request: {response.status_code}")
        return False
    
    # Step 2: Call started
    print("\n2️⃣ Sending call.started event...")
    started_payload = {
        "type": "call.started",
        "call": {
            "id": "test_call_12345",
            "status": "started",
            "phone_number": "+254703222614",
            "assistant_id": "a0451c17-f06f-4283-9398-f7ad09295538"
        },
        "timestamp": "2024-03-21T15:55:05Z"
    }
    
    response = requests.post(
        "http://localhost:8000/v1/vapi/webhooks/vapi",
        json=started_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print("✅ Call started event sent successfully")
    else:
        print(f"❌ Failed to send call.started: {response.status_code}")
        return False
    
    # Step 3: Call ended with transcript
    print("\n3️⃣ Sending call.end event with transcript...")
    ended_payload = {
        "type": "call.end",
        "call": {
            "id": "test_call_12345",
            "status": "completed",
            "phone_number": "+254703222614",
            "duration": 120,
            "assistant_id": "a0451c17-f06f-4283-9398-f7ad09295538",
            "transcript": """Assistant: Hello! This is RestoVoice AI. How can I help you make a restaurant reservation today?
Customer: Hi, I'd like to make a reservation for 4 people at The Italian Restaurant tomorrow at 7 PM.
Assistant: I'd be happy to help you with that reservation. Let me confirm - you need a table for 4 people at The Italian Restaurant tomorrow at 7 PM?
Customer: Yes, that's correct.
Assistant: Perfect! I've noted your reservation request for 4 people at The Italian Restaurant tomorrow at 7 PM. Is there anything else I should know about your reservation?
Customer: No, that's all. Thank you!
Assistant: You're welcome! Your reservation request has been recorded. Have a great day!"""
        },
        "timestamp": "2024-03-21T15:57:00Z"
    }
    
    response = requests.post(
        "http://localhost:8000/v1/vapi/webhooks/vapi",
        json=ended_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print("✅ Call ended event sent successfully")
        print("📞 Check the logs to see Groq processing the transcript!")
        return True
    else:
        print(f"❌ Failed to send call.end: {response.status_code}")
        print(f"📄 Error: {response.text}")
        return False

def get_direct_call_info():
    """Get information for making a direct call"""
    
    print("\n📞 Direct Call Test Options:")
    print("=" * 50)
    print("Since international calls aren't supported on free numbers, you can:")
    print()
    print("1. 📱 Call your Vapi number directly:")
    print("   +1 (279) 972-9410")
    print()
    print("2. 🌐 Use a VoIP service (Skype, Google Voice) to call:")
    print("   +1 (279) 972-9410")
    print()
    print("3. 📊 Monitor webhook events while calling:")
    print("   docker-compose -f docker-compose.dev.yml logs -f ai-backend")
    print()
    print("4. 🗣️ When you call, say something like:")
    print('   "Hi, I\'d like to make a reservation for 4 people at The Italian Restaurant tomorrow at 7 PM."')
    print()
    print("The system will:")
    print("- Answer with an AI assistant")
    print("- Send webhook events to localhost:8000")
    print("- Process the transcript with Groq AI")
    print("- Extract booking details")
    print("- Save call metadata")

if __name__ == "__main__":
    print("🧪 RestoVoice AI Call Testing")
    print("=" * 50)
    
    # Test webhook simulation
    success = simulate_inbound_call()
    
    if success:
        print("\n✅ Webhook test completed successfully!")
        print("📊 Check your Docker logs to see the processing:")
        print("   docker-compose -f docker-compose.dev.yml logs -f ai-backend")
    
    # Show direct call options
    get_direct_call_info()
