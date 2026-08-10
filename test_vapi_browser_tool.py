"""
Test script for Vapi Browser Automation Tool
"""

import asyncio
import sys
import os

# Add the ai-backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.voice.vapi_browser_tool import (
    VapiBrowserAutomationTool,
    AUTOMATE_BOOKING_FUNCTION,
    CHECK_BOOKING_STATUS_FUNCTION,
    GET_SUPPORTED_RESTAURANTS_FUNCTION
)

async def test_browser_automation_tool():
    """Test the browser automation tool functions"""
    
    print("Testing Vapi Browser Automation Tool")
    print("=" * 50)
    
    tool = VapiBrowserAutomationTool()
    
    # Test 1: Get supported restaurants
    print("\n1. Testing get_supported_restaurants...")
    try:
        result = await tool.get_supported_restaurants({})
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Found {result['total_count']} supported restaurants:")
            for restaurant in result['supported_restaurants']:
                print(f"  - {restaurant['name']} ({restaurant['restaurant_id']})")
        else:
            print(f"Error: {result['error']}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 2: Test automate_booking with sample data
    print("\n2. Testing automate_booking...")
    try:
        booking_params = {
            "restaurant_id": "restaurant_1",
            "customer_name": "Test Customer",
            "customer_phone": "+1234567890",
            "booking_date": "2024-12-25",
            "booking_time": "19:00",
            "party_size": 2,
            "special_requests": "Window seat preferred"
        }
        
        result = await tool.automate_booking(booking_params)
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Booking Reference: {result.get('booking_reference')}")
            print(f"Message: {result.get('message')}")
            print(f"Time taken: {result.get('time_taken_seconds', 0)} seconds")
        else:
            print(f"Error: {result['error']}")
            print(f"Error Code: {result.get('error_code')}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 3: Test check_booking_status
    print("\n3. Testing check_booking_status...")
    try:
        status_params = {
            "call_id": "test_call_123"
        }
        
        result = await tool.check_booking_status(status_params)
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Status: {result.get('status')}")
            print(f"Restaurant ID: {result.get('restaurant_id')}")
        else:
            print(f"Error: {result['error']}")
            print(f"Error Code: {result.get('error_code')}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("\n" + "=" * 50)
    print("Browser Automation Tool Tests Completed!")

def test_function_definitions():
    """Test that function definitions are properly formatted"""
    
    print("\nTesting Vapi Function Definitions")
    print("=" * 50)
    
    functions = [
        ("Automate Booking", AUTOMATE_BOOKING_FUNCTION),
        ("Check Booking Status", CHECK_BOOKING_STATUS_FUNCTION),
        ("Get Supported Restaurants", GET_SUPPORTED_RESTAURANTS_FUNCTION)
    ]
    
    for name, func_def in functions:
        print(f"\n{name} Function:")
        print(f"  Name: {func_def['name']}")
        print(f"  Description: {func_def['description'][:80]}...")
        print(f"  Required Parameters: {len(func_def['parameters']['required'])}")
        
        required_params = func_def['parameters']['required']
        if required_params:
            print(f"    Required: {', '.join(required_params)}")
        
        optional_params = [
            param for param in func_def['parameters']['properties'].keys()
            if param not in required_params
        ]
        if optional_params:
            print(f"    Optional: {', '.join(optional_params)}")
    
    print("\nAll function definitions are valid!")
    print("Copy these to your Vapi Dashboard > Assistant > Functions")

if __name__ == "__main__":
    print("Starting Vapi Browser Automation Tool Tests")
    
    # Test function definitions
    test_function_definitions()
    
    # Test the actual tool (note: this may require browser-use to be installed)
    try:
        asyncio.run(test_browser_automation_tool())
    except Exception as e:
        print(f"\nBrowser automation tests failed (expected if browser-use not installed): {e}")
        print("Install browser-use with: pip install browser-use")
        print("Set OPENAI_API_KEY environment variable for full functionality")
    
    print("\nSetup Instructions:")
    print("1. Install browser-use: pip install browser-use")
    print("2. Set OPENAI_API_KEY environment variable")
    print("3. Copy function definitions to Vapi Dashboard")
    print("4. Test by calling your Vapi number")
    
    print("\nFor detailed setup, see: VAPI_BROWSER_AUTOMATION_SETUP.md")
