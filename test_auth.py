"""
Test script for authentication endpoints
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_endpoints():
    """Test all authentication endpoints"""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Authentication Endpoints")
        print("=" * 50)
        
        # Test 1: Health check
        print("\n1. Testing health check...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Root endpoint
        print("\n2. Testing root endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 3: Owner signup
        print("\n3. Testing owner signup...")
        signup_data = {
            "first_name": "John",
            "last_name": "Doe",
            "restaurant_name": "Test Restaurant",
            "email": "john.doe@test.com",
            "password": "SecurePass123",
            "confirm_password": "SecurePass123",
            "phone_number": "+1234567890",
            "country_state": "CA",
            "city": "San Francisco",
            "postal_code": "94102",
            "agree_to_terms": True
        }
        
        try:
            response = await client.post(f"{BASE_URL}/v1/auth/owner/signup", json=signup_data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("data", {}).get("access_token")
                print(f"✅ Signup successful! Token received: {access_token[:50]}...")
                
                # Test 4: Login with same credentials
                print("\n4. Testing login...")
                login_data = {
                    "email": "john.doe@test.com",
                    "password": "SecurePass123"
                }
                
                response = await client.post(f"{BASE_URL}/v1/auth/login", json=login_data)
                print(f"Status: {response.status_code}")
                print(f"Response: {response.json()}")
                
                if response.status_code == 200:
                    login_data = response.json()
                    access_token = login_data.get("data", {}).get("access_token")
                    headers = {"Authorization": f"Bearer {access_token}"}
                    
                    # Test 5: Get current user info
                    print("\n5. Testing /me endpoint...")
                    try:
                        response = await client.get(f"{BASE_URL}/v1/auth/me", headers=headers)
                        print(f"Status: {response.status_code}")
                        print(f"Response: {response.json()}")
                    except Exception as e:
                        print(f"Error: {e}")
                    
                    # Test 6: Get dashboard
                    print("\n6. Testing dashboard endpoint...")
                    try:
                        response = await client.get(f"{BASE_URL}/v1/auth/dashboard", headers=headers)
                        print(f"Status: {response.status_code}")
                        print(f"Response: {response.json()}")
                    except Exception as e:
                        print(f"Error: {e}")
                    
                    # Test 7: Complete onboarding
                    print("\n7. Testing onboarding completion...")
                    user_data = login_data.get("data", {}).get("user", {})
                    restaurant_data = login_data.get("data", {}).get("restaurant", {})
                    
                    if restaurant_data:
                        onboarding_data = {
                            "restaurant_id": restaurant_data.get("id"),
                            "timezone": "America/Los_Angeles",
                            "phone_number": "+1234567890",
                            "address": "123 Main St",
                            "cuisine_type": "Italian",
                            "max_party_size": 10,
                            "deposit_required": False,
                            "deposit_amount": 0
                        }
                        
                        try:
                            response = await client.post(f"{BASE_URL}/v1/auth/onboarding/complete", 
                                                        json=onboarding_data, headers=headers)
                            print(f"Status: {response.status_code}")
                            print(f"Response: {response.json()}")
                        except Exception as e:
                            print(f"Error: {e}")
                    
                    # Test 8: Logout
                    print("\n8. Testing logout...")
                    try:
                        response = await client.post(f"{BASE_URL}/v1/auth/logout", headers=headers)
                        print(f"Status: {response.status_code}")
                        print(f"Response: {response.json()}")
                    except Exception as e:
                        print(f"Error: {e}")
                
            else:
                print("❌ Signup failed")
            
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 9: Invalid login
        print("\n9. Testing invalid login...")
        try:
            invalid_login = {
                "email": "nonexistent@test.com",
                "password": "wrongpassword"
            }
            response = await client.post(f"{BASE_URL}/v1/auth/login", json=invalid_login)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 10: Protected endpoint without token
        print("\n10. Testing protected endpoint without token...")
        try:
            response = await client.get(f"{BASE_URL}/v1/auth/me")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
