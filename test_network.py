import os
import asyncio
import httpx


async def test_network():
    async with httpx.AsyncClient() as client:
        tests = [
            ("https://api.duckduckgo.com/?q=test&format=json", "DuckDuckGo API"),
            ("https://httpbin.org/get", "HTTPBin"),
            ("https://google.com", "Google"),
        ]

        for url, name in tests:
            try:
                resp = await client.get(
                    url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
                )
                print(f"{name}: {resp.status_code}")
            except Exception as e:
                print(f"{name}: Error - {e}")


asyncio.run(test_network())
