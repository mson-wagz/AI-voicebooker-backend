#!/usr/bin/env python3
"""
Script to set up ngrok and configure Vapi webhook for inbound calling
"""
import os
import subprocess
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_ngrok():
    """Start ngrok tunnel"""
    print("Starting ngrok tunnel...")
    try:
        # Start ngrok in background
        process = subprocess.Popen([
            './ngrok.exe', 'http', '8000'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for ngrok to start
        time.sleep(3)
        
        # Get ngrok URL
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            tunnels = response.json()['tunnels']
            if tunnels:
                ngrok_url = tunnels[0]['public_url']
                print(f"ngrok tunnel created: {ngrok_url}")
                return ngrok_url
            else:
                print("No ngrok tunnels found")
                return None
        except Exception as e:
            print(f"Failed to get ngrok URL: {e}")
            return None
            
    except Exception as e:
        print(f"Failed to start ngrok: {e}")
        return None

def configure_vapi_webhook(ngrok_url):
    """Configure Vapi webhook URL"""
    webhook_url = f"{ngrok_url}/v1/vapi/webhooks/vapi"
    print(f"Configuring Vapi webhook: {webhook_url}")
    
    # This would typically be done through Vapi dashboard or API
    # For now, we'll just show the URL
    print(f"Please configure this webhook URL in your Vapi dashboard: {webhook_url}")
    
    return webhook_url

def main():
    print("Setting up inbound calling with ngrok...")
    
    # Start ngrok
    ngrok_url = start_ngrok()
    if not ngrok_url:
        print("Failed to start ngrok")
        return
    
    # Configure webhook
    webhook_url = configure_vapi_webhook(ngrok_url)
    
    print("\nSetup complete!")
    print(f"Webhook URL: {webhook_url}")
    print(f"Test your inbound calling by calling your Vapi phone number")
    print("Make sure your server is running on http://localhost:8000")

if __name__ == "__main__":
    main()
