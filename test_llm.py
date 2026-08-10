from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content_stream(
    model="gemma-3-27b",
    contents=["Explain how AI works"]
)
for chunk in response:
    print(chunk.text, end="")