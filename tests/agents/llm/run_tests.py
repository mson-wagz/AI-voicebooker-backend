"""
Test runner for RestoVoice AI agents.
This script makes it easy to run all tests from the project root.

Usage:
    uv run python tests/agents/llm/run_tests.py
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_all_tests():
    """Run all test suites."""
    print("RestoVoice AI Agent Test Suite")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with the Azure OpenAI credentials.")
        return False
    
    print("✅ Environment variables configured")
    
    try:
        # Import test modules
        from test_prompts import test_prompt_templates, test_intent_classification, test_booking_extraction, test_conversation_flow, test_error_handling
        from test_langgraph import test_basic_booking_flow, test_intent_routing, test_error_handling as test_langgraph_error_handling
        
        # Run prompt manager tests
        print("\n" + "="*60)
        print("PROMPT MANAGER TESTS")
        print("="*60)
        
        test_prompt_templates()
        test_intent_classification()
        test_booking_extraction()
        test_conversation_flow()
        test_error_handling()
        
        # Run LangGraph tests
        print("\n" + "="*60)
        print("LANGGRAPH AGENT TESTS")
        print("="*60)
        
        await test_basic_booking_flow()
        await test_intent_routing()
        await test_langgraph_error_handling()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        logger.exception("Test suite failure")
        return False


async def run_prompt_tests_only():
    """Run only prompt manager tests."""
    print("RestoVoice Prompt Manager Tests")
    print("=" * 50)
    
    try:
        from test_prompts import test_prompt_templates, test_intent_classification, test_booking_extraction, test_conversation_flow, test_error_handling
        
        test_prompt_templates()
        test_intent_classification()
        test_booking_extraction()
        test_conversation_flow()
        test_error_handling()
        
        print("\n✅ Prompt manager tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Prompt tests failed: {e}")
        return False


async def run_langgraph_tests_only():
    """Run only LangGraph agent tests."""
    print("RestoVoice LangGraph Agent Tests")
    print("=" * 50)
    
    try:
        from test_langgraph import test_basic_booking_flow, test_intent_routing, test_error_handling
        
        await test_basic_booking_flow()
        await test_intent_routing()
        await test_error_handling()
        
        print("\n✅ LangGraph tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ LangGraph tests failed: {e}")
        return False


def show_restaurant_configs():
    """Display available restaurant configuration options."""
    from agents.llm.restaurant_config import RestaurantConfigManager, OperatingHoursType
    
    print("Flexible Restaurant Configuration System")
    print("=" * 50)
    print("All restaurant data is now dynamically configurable!")
    print("\nExample configurations you can create:")
    
    examples = [
        {
            "name": "24/7 Diner",
            "hours_type": "24/7",
            "max_party_size": 20,
            "phone_number": "555-0123",
            "address": "123 Highway Rd"
        },
        {
            "name": "Fine Dining Restaurant",
            "hours_type": "standard",
            "open_time": "5:30 PM",
            "close_time": "11:00 PM", 
            "max_party_size": 8,
            "deposit_required_for_parties_above": 4,
            "deposit_amount": 50.0,
            "phone_number": "555-0124",
            "address": "456 Elegant Ave"
        },
        {
            "name": "Late Night Spot",
            "hours_type": "extended",
            "open_time": "4:00 PM",
            "close_time": "2:00 AM",
            "max_party_size": 6,
            "phone_number": "555-0125",
            "address": "789 Night St"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}:")
        config = RestaurantConfigManager.create_custom_config(**example)
        context = config.get_context_for_ai()
        print(f"   Hours: {context['operating_hours']}")
        print(f"   Max Party: {context['max_party_size']}")
        print(f"   Deposit Policy: {context['deposit_policy']}")
    
    print("\nAvailable Hours Types:")
    for hours_type in OperatingHoursType:
        print(f"  - {hours_type.value}: {hours_type.name}")
    
    print("\nUsage: Create custom configs with RestaurantConfigManager.create_custom_config(**params)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RestoVoice AI agent tests")
    parser.add_argument("--prompts-only", action="store_true", help="Run only prompt manager tests")
    parser.add_argument("--langgraph-only", action="store_true", help="Run only LangGraph agent tests")
    parser.add_argument("--show-configs", action="store_true", help="Show available restaurant configurations")
    
    args = parser.parse_args()
    
    if args.show_configs:
        show_restaurant_configs()
    elif args.prompts_only:
        success = asyncio.run(run_prompt_tests_only())
        sys.exit(0 if success else 1)
    elif args.langgraph_only:
        success = asyncio.run(run_langgraph_tests_only())
        sys.exit(0 if success else 1)
    else:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
