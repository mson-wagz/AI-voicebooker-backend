import os
import asyncio
import httpx

os.environ["SERPER_API_KEY"] = ""
os.environ["SERPAPI_KEY"] = ""
os.environ["GOOGLE_CSE_ID"] = ""
os.environ["GOOGLE_API_KEY"] = ""


async def test_ddg():
    async with httpx.AsyncClient() as client:
        query = "The Spotted Pig restaurant New York reservation"
        resp = await client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (compatible; RestoBot/1.0)"},
            timeout=15,
            follow_redirects=True,
        )
        print(f"Status: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")

        # Check for results
        if "result" in resp.text.lower():
            print("Found 'result' in response")
            # Show a snippet
            print(resp.text[:2000])
        else:
            print("No results found in response")
            print(resp.text[:500])


asyncio.run(test_ddg())
