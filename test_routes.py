#!/usr/bin/env python3
"""
Simple test to check available routes
"""
import requests
import json

def test_routes():
    base_url = "http://localhost:8000"
    
    # Test health
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health: {response.status_code}")
    except Exception as e:
        print(f"❌ Health: {e}")
    
    # Test auth login
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )
        print(f"✅ Auth Login: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Auth Login: {e}")
    
    # Test admin dashboard
    try:
        response = requests.get(f"{base_url}/api/v1/owner/dashboard/overview-stats")
        print(f"✅ Admin Overview: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Admin Overview: {e}")
    
    # Test restaurant settings
    try:
        response = requests.get(f"{base_url}/api/v1/user/restaurant-settings")
        print(f"✅ Restaurant Settings: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Restaurant Settings: {e}")

if __name__ == "__main__":
    test_routes()
