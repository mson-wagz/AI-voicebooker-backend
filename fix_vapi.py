#!/usr/bin/env python3
"""
Script to fix Vapi router import issues
"""
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test if imports work"""
    try:
        from core.voice.vapi_api_test import router
        print("✅ vapi_api_test import successful")
        
        from core.voice.voice_handler import VoiceHandler
        print("✅ voice_handler import successful")
        
        from core.voice.vapi_api import router
        print("✅ vapi_api import successful")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing imports...")
    if test_imports():
        print("✅ All imports working!")
    else:
        print("❌ Import issues found")
