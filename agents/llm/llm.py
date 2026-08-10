import os
import logging
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_gemini_test():
    """Test Google Gemini connectivity and configuration."""
    # Validate environment variables
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error("Missing required Gemini API key")
        raise ValueError("Please set GEMINI_API_KEY")

    try:
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemma-3-27b",
            contents="simple test"
        )
        
        # Validate response
        if response and hasattr(response, 'text'):
            print(response.text)
        else:
            logger.warning("Received empty response from Gemini")
            print("No response received from Gemini")
            
    except Exception as e:
        logger.error(f"Gemini test failed: {e}")
        print(f"Error: {e}")
        print("Please check your Gemini configuration and try again.")

