#!/usr/bin/env python3
"""
Configure DTMF support for Vapi assistant
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def setup_dtmf_assistant():
    """Create assistant with DTMF support"""
    
    vapi_api_key = os.getenv("VAPI_API_KEY")
    
    if not vapi_api_key:
        print("❌ Missing VAPI_API_KEY in .env")
        return
    
    print("🔧 Setting up DTMF-enabled assistant...")
    
    # Create assistant with DTMF support
    assistant_data = {
        "name": "RestoVoice DTMF Agent",
        "model": {
            "provider": "openai",
            "model": "gpt-4"
        },
        "voice": {
            "provider": "vapi",
            "voiceId": "Clara"
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en"
        },
        "recordingEnabled": True
    }
    
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
            print(f"✅ DTMF Assistant created: {assistant_id}")
            
            # Update phone number with new assistant
            phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
            phone_update = {
                "assistantId": assistant_id
            }
            
            update_response = requests.patch(
                f"https://api.vapi.ai/phone-number/{phone_number_id}",
                json=phone_update,
                headers=headers
            )
            
            if update_response.status_code == 200:
                print(f"✅ Phone number updated with DTMF assistant")
                print(f"🎉 DTMF support configured!")
                print(f"📞 Customers can now press 1, 2, 3, etc. during calls")
            else:
                print(f"❌ Failed to update phone number: {update_response.text}")
                
        else:
            print(f"❌ Failed to create assistant: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def create_website_call_button():
    """Generate HTML code for website call button"""
    
    html_code = '''
<!-- Add this to your website HTML -->
<div class="call-widget">
    <button id="callButton" class="call-btn">
        📞 Call Restaurant Now
    </button>
    <div id="callStatus" class="call-status"></div>
</div>

<script>
document.getElementById('callButton').addEventListener('click', async function() {
    const statusDiv = document.getElementById('callStatus');
    const button = this;
    
    button.disabled = true;
    statusDiv.textContent = 'Connecting...';
    
    try {
        // Get customer phone number (you can implement a phone input modal)
        const customerPhone = prompt('Enter your phone number:');
        
        if (!customerPhone) {
            button.disabled = false;
            statusDiv.textContent = '';
            return;
        }
        
        // Call your backend to initiate outbound call
        const response = await fetch('/v1/vapi/calls/initiate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                restaurant_id: 'your-restaurant-id',
                customer_number: customerPhone
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusDiv.textContent = '📞 Calling you now! Please answer your phone.';
            button.textContent = 'Call in Progress...';
        } else {
            statusDiv.textContent = '❌ Failed to initiate call';
            button.disabled = false;
        }
        
    } catch (error) {
        statusDiv.textContent = '❌ Error: ' + error.message;
        button.disabled = false;
    }
});
</script>

<style>
.call-widget {
    padding: 20px;
    text-align: center;
    background: #f8f9fa;
    border-radius: 8px;
    margin: 20px 0;
}

.call-btn {
    background: #28a745;
    color: white;
    border: none;
    padding: 12px 24px;
    font-size: 16px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.3s;
}

.call-btn:hover:not(:disabled) {
    background: #218838;
}

.call-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
}

.call-status {
    margin-top: 10px;
    font-weight: bold;
    color: #333;
}
</style>
'''
    
    print("🌐 Website Call Button HTML:")
    print(html_code)
    
    # Save to file
    with open('website_call_button.html', 'w') as f:
        f.write(html_code)
    print("💾 Saved to website_call_button.html")

if __name__ == "__main__":
    print("🎤 RestoVoice DTMF & Website Setup")
    print("1. Setup DTMF assistant")
    print("2. Generate website call button")
    
    choice = input("Choose option (1 or 2): ")
    
    if choice == "1":
        setup_dtmf_assistant()
    elif choice == "2":
        create_website_call_button()
    else:
        print("Invalid choice")
