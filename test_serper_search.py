#!/usr/bin/env python3
"""
Test Serper.dev search functionality
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_serper_search():
    """Test Serper.dev search with real key"""
    
    print("Testing Serper.dev Search")
    print("=" * 30)
    
    try:
        from src.core.automation.browser_use import BrowserAutomation
        
        # Initialize automation
        automation = BrowserAutomation()
        await automation.initialize()
        
        # Test search with Serper.dev
        print("\nTesting restaurant search with Serper.dev:")
        
        search_results = await automation.search_restaurants(
            restaurant_name="Italian restaurant",
            location="New York"
        )
        
        print(f"Found {len(search_results)} restaurants")
        
        if search_results:
            print("\nTop results:")
            for i, result in enumerate(search_results[:5]):
                print(f"{i+1}. {result.name}")
                print(f"   Platform: {result.platform}")
                print(f"   URL: {result.url}")
                print()
        else:
            print("No results found")
        
        # Test availability check
        print("\nTesting availability check:")
        
        availability_result = await automation.check_availability(
            restaurant_name="Italian restaurant",
            location="New York",
            requested_date="2024-12-25",
            requested_time="19:00",
            party_size=4
        )
        
        print(f"Available: {availability_result['available']}")
        print(f"Requested time available: {availability_result['requested_time_available']}")
        print(f"Message: {availability_result['message']}")
        
        if availability_result['alternatives']:
            print("\nAlternative options:")
            for alt in availability_result['alternatives'][:3]:
                print(f"  - {alt['time']} at {alt['restaurant']}")
        
        await automation.cleanup()
        
        return len(search_results) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Serper.dev Test for Restaurant Search")
    print("=" * 40)
    
    # Check Serper.dev key
    serper_key = os.getenv("SERPER_API_KEY")
    if serper_key:
        print(f"Serper.dev key found: {serper_key[:8]}...")
    else:
        print("Serper.dev key not found")
        return
    
    success = await test_serper_search()
    
    if success:
        print("\nSUCCESS! Serper.dev search is working!")
        print("\nYour availability flow is now fully functional!")
    else:
        print("\nSearch still not working - check Serper.dev key")

if __name__ == "__main__":
    asyncio.run(main())
