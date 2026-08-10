#!/usr/bin/env python3
"""
Test voice call to browser automation integration
"""

import os
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_voice_to_automation():
    """Test the complete flow from voice call to browser automation"""
    
    print("🧪 Testing Voice Call → Browser Automation Integration")
    print("=" * 60)
    
    try:
        # Import the processors
        from src.core.ai.call_processor import get_call_processor
        from src.core.automation.browser_use import get_booking_processor
        from src.core.metadata.storage import metadata_storage
        
        # 1. Simulate a completed voice call
        print("📞 1. Simulating completed voice call...")
        
        call_data = {
            "restaurantId": "restaurant_1",  # Example Restaurant
            "customer": {"number": "+254703222614"},
            "transcript": """Customer: Hi, I'd like to make a reservation for 4 people at The Italian Restaurant tomorrow at 7 PM.
Assistant: I'd be happy to help you with that reservation. Let me confirm - you need a table for 4 people at The Italian Restaurant tomorrow at 7 PM?
Customer: Yes, that's correct.
Assistant: Perfect! I've noted your reservation request for 4 people at The Italian Restaurant tomorrow at 7 PM. Is there anything else I should know about your reservation?
Customer: No, that's all. Thank you!
Assistant: You're welcome! Your reservation request has been recorded. Have a great day!""",
            "status": "completed",
            "recordingUrl": "https://example.com/recording.mp3"
        }
        
        # 2. Process the call
        print("🧠 2. Processing call with AI...")
        call_processor = get_call_processor()
        call_id = await call_processor.process_call(call_data)
        print(f"✅ Call processed with ID: {call_id}")
        
        # 3. Get the extracted metadata
        print("📋 3. Checking extracted booking details...")
        call_metadata = await metadata_storage.get_call_metadata(call_id)
        
        if call_metadata:
            print("✅ Booking details extracted:")
            print(f"   Restaurant: {call_metadata.booking_request.get('restaurant_name', 'N/A')}")
            print(f"   Date: {call_metadata.booking_request.get('date', 'N/A')}")
            print(f"   Time: {call_metadata.booking_request.get('time', 'N/A')}")
            print(f"   Party Size: {call_metadata.booking_request.get('party_size', 'N/A')}")
            print(f"   Customer: {call_metadata.customer_name or 'N/A'}")
            
            # 4. Validate booking
            print("🔍 4. Validating booking details...")
            validation = await call_processor.validate_booking(call_metadata.booking_request)
            
            if validation["is_valid"]:
                print("✅ Booking details are valid!")
                print("🤖 5. Browser automation will process this booking...")
                print("   (The browser automation loop will pick this up automatically)")
                
                # Show what the browser automation will do
                booking_processor = get_booking_processor()
                restaurant_config = booking_processor.browser_automation._get_restaurant_config("restaurant_1")
                
                if restaurant_config:
                    print(f"🌐 Browser will navigate to: {restaurant_config.url}")
                    print(f"📝 Will book at: {restaurant_config.name}")
                else:
                    print("⚠️ No restaurant configuration found for restaurant_1")
                    
            else:
                print("❌ Booking validation failed:")
                for error in validation["errors"]:
                    print(f"   - {error}")
        else:
            print("❌ No call metadata found")
            
        print("\n🎉 Integration test completed!")
        print("📊 Monitor logs: docker-compose -f docker-compose.dev.yml logs -f ai-backend")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_voice_to_automation())
