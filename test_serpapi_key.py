#!/usr/bin/env python3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_serpapi_key():
    api_key = os.getenv("SERPAPI_KEY", "").strip()

    print("RAW KEY REPR:", repr(api_key))
    print("KEY LENGTH:", len(api_key))

    if not api_key:
        print("No SerpAPI key found")
        return False

    url = "https://serpapi.com/search"
    params = {
        "api_key": api_key,
        "engine": "google",
        "q": "Italian restaurant New York",
        "num": 5
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        print(f"Status code: {response.status_code}")
        print(f"Final URL: {response.url}")

        if response.status_code == 200:
            data = response.json()
            print("API key works!")
            print("Results found:", len(data.get("organic_results", [])))
            return True
        else:
            print("Error response:", response.text)
            return False

    except Exception as e:
        print("Request failed:", e)
        return False

if __name__ == "__main__":
    print("SerpAPI Key Test")
    print("=" * 20)
    test_serpapi_key()