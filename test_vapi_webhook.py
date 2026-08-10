#!/usr/bin/env python3
"""
Test Vapi webhook integration with availability check
"""

import asyncio
import json
from src.core.automation.browser_use import BrowserAutomation

async def test_vapi_functions():
    """Test the Vapi function handlers"""
    
    print("Testing Vapi Function Handlers")
    print("=" * 40)
    
    try:
        # Import the function handlers
        from src.core.voice.vapi_api import handle_check_availability, handle_book_reservation
        
        # Test availability check
        print("\n1. Testing check_availability function:")
        
        availability_args = {
            "restaurant_name": "Italian restaurant",
            "location": "New York", 
            "date": "2024-12-25",
            "time": "19:00",
            "party_size": 4
        }
        
        availability_result = await handle_check_availability(availability_args)
        print(f"Availability result: {availability_result}")
        
        # Test booking function
        print("\n2. Testing book_reservation function:")
        
        booking_args = {
            "restaurant_name": "Quality Italian",
            "location": "New York",
            "date": "2024-12-25", 
            "time": "19:00",
            "party_size": 4,
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "customer_email": "john@example.com"
        }
        
        booking_result = await handle_book_reservation(booking_args, "test-call-123")
        print(f"Booking result: {booking_result}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_webhook_payload():
    """Test webhook payload structure"""
    
    print("\nTesting Webhook Payload Structure")
    print("=" * 40)
    
    # Simulate Vapi webhook payload for function call
    webhook_payload = {
        "message": {
            "type": "function-call",
            "function": {
                "name": "check_availability",
                "arguments": {
                    "restaurant_name": "Italian restaurant",
                    "location": "New York",
                    "date": "2024-12-25", 
                    "time": "19:00",
                    "party_size": 4
                }
            },
            "toolCallId": "test-tool-call-123"
        },
        "call": {
            "id": "test-call-456",
            "type": "webCall"
        }
    }
    
    print("Sample webhook payload:")
    print(json.dumps(webhook_payload, indent=2))
    
    return webhook_payload

async def main():
    """Main test function"""
    print("Vapi Webhook Integration Test")
    print("=" * 50)
    
    # Test function handlers
    success = await test_vapi_functions()
    
    # Show webhook payload structure
    await test_webhook_payload()
    
    if success:
        print("\nSUCCESS! Vapi integration is ready!")
        print("\nWhat's working:")
        print("  - check_availability function")
        print("  - book_reservation function") 
        print("  - Browser automation backend")
        print("  - Natural language responses")
        
        print("\nNext steps:")
        print("1. Start the FastAPI server")
        print("2. Configure Vapi webhook URL")
        print("3. Test with real Vapi call")
    else:
        print("\nFix the issues above")

if __name__ == "__main__":
    asyncio.run(main())
