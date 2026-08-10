"""
Debug Google Gemini configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Debugging Google Gemini Configuration:")
print("=" * 50)

# Check all variables
vars_to_check = [
    "GEMINI_API_KEY",
    "AZURE_OPENAI_API_KEY",  # Check for old Azure variables
    "AZURE_OPENAI_ENDPOINT", 
    "AZURE_OPENAI_DEPLOYMENT",
    "AZURE_API_KEY",
    "AZURE_API_BASE",
    "AZURE_API_MODEL"
]

for var in vars_to_check:
    value = os.getenv(var)
    if value:
        if "KEY" in var:
            # Show only first 20 chars for keys
            print(f"   {var}: {value[:20]}... (length: {len(value)})")
        else:
            print(f"   {var}: {value}")
    else:
        print(f"   {var}: NOT SET")

# Test with a simple request using the exact same method as llm.py
from google import genai

try:
    api_key = os.getenv("GEMINI_API_KEY")
    
    print("\n🚀 Testing with Gemini client:")
    print(f"   API Key length: {len(api_key) if api_key else 0}")
    
    if api_key:
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemma-3-27b",
            contents="Say 'Hello' if you can read this"
        )
        
        print(f"✅ Success! Response: {response.text}")
        
    else:
        print("❌ Missing GEMINI_API_KEY")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPossible issues:")
    print("1. API key is invalid or expired")
    print("2. Model name is incorrect")
    print("3. Network connectivity issues")
    print("4. API quota exceeded")
