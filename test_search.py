import os
import asyncio
import sys

sys.path.insert(0, "/app")

os.environ["PYTHONPATH"] = "/app"

from src.core.automation.browser_use import (
    RestaurantSearcher,
    BrowserAutomation,
    BookingResult,
)


async def test_search():
    s = RestaurantSearcher()
    try:
        r = await s.search("The Spotted Pig", "New York")
        print(f"Found {len(r)} results")
        for i, res in enumerate(r[:5]):
            print(f"  {i + 1}. {res.name} ({res.platform}) - {res.url[:60]}")
    except Exception as e:
        print(f"Search Error: {e}")
    finally:
        await s.close()


async def test_browser():
    print("\nTesting BrowserAutomation...")
    ba = BrowserAutomation()
    try:
        await ba.initialize()
        print("BrowserAutomation initialized")
    except Exception as e:
        print(f"Init Error: {e}")


async def main():
    await test_search()
    await test_browser()


asyncio.run(main())
