#!/usr/bin/env python3
"""
Test Serper.dev in complete isolation
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("SERPER_API_KEY", "").strip()

print("RAW KEY:", repr(api_key))
print("KEY LENGTH:", len(api_key))

url = "https://google.serper.dev/search"
headers = {
    "X-API-KEY": api_key,
    "Content-Type": "application/json"
}
payload = {
    "q": "Italian restaurant New York"
}

response = requests.post(url, json=payload, headers=headers, timeout=15)

print("STATUS:", response.status_code)
print("TEXT:", response.text)
