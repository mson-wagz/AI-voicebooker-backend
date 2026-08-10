#!/usr/bin/env python3
"""
Manual Admin API Test Script
Tests all admin endpoints using Python requests
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
RESTAURANT_ID = "test-restaurant-1"
API_BASE = f"{BASE_URL}/admin"

def print_header(title):
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")

def print_success(message):
    print(f"PASS: {message}")

def print_error(message):
    print(f"FAIL: {message}")

def print_info(message):
    print(f"INFO: {message}")

def test_endpoint(method, endpoint, data=None, expected_status=200, description=""):
    print_header(description)
    print(f"Method: {method}")
    print(f"URL: {API_BASE}{endpoint}")
    print(f"Expected Status: {expected_status}")
    
    try:
        if data:
            print(f"Data: {json.dumps(data, indent=2)}")
        
        # Make request
        if method.upper() == "GET":
            response = requests.get(f"{API_BASE}{endpoint}")
        elif method.upper() == "POST":
            response = requests.post(f"{API_BASE}{endpoint}", json=data)
        elif method.upper() == "PUT":
            response = requests.put(f"{API_BASE}{endpoint}", json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print_success(f"Status: {response.status_code} (Expected: {expected_status})")
        else:
            print_error(f"Status: {response.status_code} (Expected: {expected_status})")
        
        print("Response:")
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
        except:
            print(response.text)
        
        return response.status_code == expected_status
        
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def main():
    print_header("RestoVoice Admin Backend API Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Restaurant ID: {RESTAURANT_ID}")
    print(f"API Base: {API_BASE}")
    
    # Check if server is running
    print_header("Checking Server Connection")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Server is running")
            health_data = response.json()
            print(f"Services: {health_data.get('services', {})}")
        else:
            print_error(f"Server returned status {response.status_code}")
            return
    except Exception as e:
        print_error(f"Server is not running: {e}")
        print("Please start the server first:")
        print("python -m uvicorn src.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Test results
    test_results = []
    
    # Test 1: Admin Health Check
    result = test_endpoint("GET", "/health", description="Admin Health Check")
    test_results.append(("Admin Health Check", result))
    
    # Test 2: Get Dashboard Stats
    result = test_endpoint("GET", f"/dashboard/stats/{RESTAURANT_ID}", description="Get Dashboard Statistics")
    test_results.append(("Dashboard Statistics", result))
    
    # Test 3: Get Policy
    result = test_endpoint("GET", f"/policies/{RESTAURANT_ID}", description="Get Restaurant Policy")
    test_results.append(("Get Policy", result))
    
    # Test 4: Create Policy
    policy_data = {
        "deposit_required": True,
        "deposit_amount": 500,
        "max_party_size": 12,
        "opening_hours": [
            {
                "day_of_week": 0,
                "open_time": "09:00",
                "close_time": "22:00",
                "is_closed": True
            },
            {
                "day_of_week": 1,
                "open_time": "09:00",
                "close_time": "22:00",
                "is_closed": False
            }
        ],
        "deposit_rules": [
            {
                "day_of_week": 5,
                "min_party": 6,
                "start_time": "18:00",
                "end_time": "22:00"
            }
        ]
    }
    result = test_endpoint("POST", f"/policies/{RESTAURANT_ID}", policy_data, description="Create/Update Policy")
    test_results.append(("Create Policy", result))
    
    # Test 5: Update Policy
    update_data = {
        "deposit_required": False,
        "max_party_size": 15
    }
    result = test_endpoint("PUT", f"/policies/{RESTAURANT_ID}", update_data, description="Update Policy (Partial)")
    test_results.append(("Update Policy", result))
    
    # Test 6: Get Call Logs
    result = test_endpoint("GET", f"/calls/{RESTAURANT_ID}?limit=5&offset=0", description="Get Call Logs")
    test_results.append(("Call Logs", result))
    
    # Test 7: Get Booking Logs
    result = test_endpoint("GET", f"/bookings/{RESTAURANT_ID}?limit=5&offset=0", description="Get Booking Logs")
    test_results.append(("Booking Logs", result))
    
    # Test 8: Get Booking Logs with Status Filter
    result = test_endpoint("GET", f"/bookings/{RESTAURANT_ID}?status=CONFIRMED&limit=5&offset=0", description="Get Booking Logs (Status Filter)")
    test_results.append(("Booking Logs (Confirmed)", result))
    
    # Test 9: Error Case - Non-existent Restaurant
    result = test_endpoint("GET", "/dashboard/stats/non-existent-restaurant", expected_status=404, description="Error Case - Non-existent Restaurant")
    test_results.append(("Error - Non-existent Restaurant", result))
    
    # Test 10: Error Case - Invalid Policy Data
    invalid_policy = {
        "deposit_required": "not_boolean",
        "max_party_size": -5,
        "opening_hours": "not_array"
    }
    result = test_endpoint("POST", f"/policies/{RESTAURANT_ID}", invalid_policy, expected_status=422, description="Error Case - Invalid Policy Data")
    test_results.append(("Error - Invalid Policy Data", result))
    
    # Test 11: Error Case - Limit Too High
    result = test_endpoint("GET", f"/calls/{RESTAURANT_ID}?limit=150", expected_status=422, description="Error Case - Limit Too High")
    test_results.append(("Error - Limit Too High", result))
    
    # Test 12: Error Case - Wrong HTTP Method
    result = test_endpoint("POST", f"/calls/{RESTAURANT_ID}", expected_status=405, description="Error Case - Wrong HTTP Method")
    test_results.append(("Error - Wrong HTTP Method", result))
    
    # Summary
    print_header("Test Summary")
    
    passed_count = sum(1 for _, passed in test_results if passed)
    total_count = len(test_results)
    
    print(f"Tests Passed: {passed_count}/{total_count}")
    
    print("\nTest Results:")
    for test_name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        print(f"{status} {test_name}")
    
    if passed_count == total_count:
        print_success("All admin endpoint tests passed!")
    else:
        print_error(f"Some tests failed: {total_count - passed_count} failed")
    
    print_info("Check the responses above to verify functionality")
    
    print_header("Quick Reference")
    print(f"- Dashboard Stats: GET {API_BASE}/dashboard/stats/{RESTAURANT_ID}")
    print(f"- Policy Management: GET/POST/PUT {API_BASE}/policies/{RESTAURANT_ID}")
    print(f"- Call Logs: GET {API_BASE}/calls/{RESTAURANT_ID}")
    print(f"- Booking Logs: GET {API_BASE}/bookings/{RESTAURANT_ID}")
    print(f"- Health Check: GET {API_BASE}/health")

if __name__ == "__main__":
    main()
