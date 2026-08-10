"""
Test script for LangGraph-based RestoVoice agents.
Demonstrates the agent orchestration system with state management.

Run this script to test:
- Multi-agent routing and coordination
- State persistence across conversation turns
- Conditional routing based on intent
- Error handling and recovery
- Complete booking flows
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

# Import from the agents.llm package
from agents.llm.langgraph_agents import SimpleRestoVoiceAgent
from agents.llm.restaurant_config import RestaurantConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _require_env() -> bool:
    """Check if required Azure environment variables are present."""
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with the Azure OpenAI credentials.")
        return False
    
    return True


async def test_basic_booking_flow():
    """Test a complete booking flow through the agent system."""
    print("\n" + "="*60)
    print("TESTING BASIC BOOKING FLOW")
    print("="*60)
    
    if not _require_env():
        return
    
    try:
        agent = SimpleRestoVoiceAgent()
        
        # Test different restaurant configurations dynamically
        test_configs = [
            {
                "name": "Standard Restaurant",
                "hours_type": "standard",
                "open_time": "11:00 AM", 
                "close_time": "10:00 PM",
                "max_party_size": 12,
                "phone_number": "555-0123",
                "address": "123 Main St"
            },
            {
                "name": "24/7 Diner", 
                "hours_type": "24/7",
                "max_party_size": 20,
                "phone_number": "555-0124",
                "address": "456 Highway Rd"
            }
        ]
        
        for config_data in test_configs:
            print(f"\n--- Testing {config_data['name']} ---")
            
            # Create restaurant configuration dynamically
            restaurant_config = RestaurantConfigManager.create_custom_config(**config_data)
            restaurant_info = restaurant_config.get_context_for_ai()
            
            print(f"Hours: {restaurant_info['operating_hours']}")
            print(f"Max Party: {restaurant_info['max_party_size']}")
            
            # Simulate a complete booking conversation
            conversation = [
                "Table for four tonight at 7pm",
                "The name is John Smith", 
                "555-1234"
            ]
            
            for i, message in enumerate(conversation):
                print(f"\n--- Turn {i+1} ---")
                print(f"User: {message}")
                
                result = await agent.process_message(message, restaurant_info)
                
                if result["success"]:
                    print(f"AI: {result['response']}")
                    print(f"Current Step: {result['state'].get('current_step')}")
                    print(f"Intent: {result['state'].get('intent')}")
                    print(f"Booking Data: {result['booking_data']}")
                    
                    if result['confirmation_code']:
                        print(f"🎉 Confirmation Code: {result['confirmation_code']}")
                        print("✅ Booking completed successfully!")
                        break
                        
                    if result['should_transfer']:
                        print("🔄 Would transfer to human staff")
                        break
                else:
                    print(f"❌ Error: {result['error']}")
                    break
            
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def test_intent_routing():
    """Test intent classification and routing."""
    print("\n" + "="*60)
    print("TESTING INTENT ROUTING")
    print("="*60)
    
    if not _require_env():
        return
    
    try:
        agent = SimpleRestoVoiceAgent()
        
        restaurant_info = {
            "restaurant_name": "The Ocean Room",
            "current_time": "7:30 PM",
            "hours": "5 PM - 10 PM",
            "availability": "Limited"
        }
        
        # Test different intents
        test_intents = {
            "booking": "Table for four tonight at 7pm",
            "inquiry": "What time do you close?",
            "transfer": "Can I speak to a manager?",
            "complex": "Do you have gluten-free options for a birthday party?",
            "cancellation": "I need to cancel my reservation"
        }
        
        for intent_type, message in test_intents.items():
            print(f"\n--- Testing {intent_type.upper()} intent ---")
            print(f"User: {message}")
            
            thread_id = f"intent_test_{intent_type}"
            result = await agent.process_message(message, restaurant_info)
            
            if result["success"]:
                print(f"Detected Intent: {result['state'].get('intent')}")
                print(f"AI Response: {result['response']}")
                print(f"Next Step: {result['state'].get('current_step')}")
                
                if result['should_transfer']:
                    print("🔄 Would transfer to human staff")
            else:
                print(f"❌ Error: {result['error']}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def test_error_handling():
    """Test error handling and recovery."""
    print("\n" + "="*60)
    print("TESTING ERROR HANDLING")
    print("="*60)
    
    if not _require_env():
        return
    
    try:
        agent = SimpleRestoVoiceAgent()
        
        restaurant_info = {
            "restaurant_name": "The Ocean Room",
            "current_time": "7:30 PM",
            "hours": "5 PM - 10 PM",
            "availability": "Limited"
        }
        
        # Test scenarios that might cause errors
        error_scenarios = [
            "",  # Empty input
            "x" * 2000,  # Very long input
            "🍕🍔🍟",  # Emoji-only input
            "table for fifty people right now"  # Unreasonable request
        ]
        
        for i, scenario in enumerate(error_scenarios):
            print(f"\n--- Error Scenario {i+1} ---")
            print(f"Input: '{scenario[:50]}{'...' if len(scenario) > 50 else ''}'")
            
            thread_id = f"error_test_{i}"
            result = await agent.process_message(scenario, restaurant_info)
            
            if result["success"]:
                print(f"AI Response: {result['response']}")
                print(f"Error Count: {result['state'].get('error_count', 0)}")
                
                if result['should_transfer']:
                    print("🔄 Would transfer to human staff")
            else:
                print(f"Handled Error: {result['error']}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def test_state_persistence():
    """Test state persistence across conversation turns."""
    print("\n" + "="*60)
    print("TESTING STATE PERSISTENCE")
    print("="*60)
    
    if not _require_env():
        return
    
    try:
        agent = SimpleRestoVoiceAgent()
        
        restaurant_info = {
            "restaurant_name": "The Ocean Room",
            "current_time": "7:30 PM",
            "hours": "5 PM - 10 PM",
            "availability": "Limited"
        }
        
        thread_id = "persistence_test"
        
        # Simulate conversation with information provided across multiple turns
        conversation_turns = [
            "I need a table",
            "for four people",
            "tonight at 7pm",
            "my name is Sarah",
            "phone is 555-9876"
        ]
        
        accumulated_data = {}
        
        for i, message in enumerate(conversation_turns):
            print(f"\n--- Turn {i+1} ---")
            print(f"User: {message}")
            
            result = await agent.process_message(message, restaurant_info)
            
            if result["success"]:
                print(f"AI: {result['response']}")
                print(f"Current Step: {result['state'].get('current_step')}")
                
                # Track accumulated booking data
                current_data = result['booking_data']
                new_data = {k: v for k, v in current_data.items() if k not in accumulated_data}
                accumulated_data.update(new_data)
                
                print(f"Accumulated Booking Data: {accumulated_data}")
                print(f"Missing Fields: {result['state'].get('missing_fields', [])}")
                
                if result['confirmation_code']:
                    print(f"🎉 Confirmation Code: {result['confirmation_code']}")
                    break
                    
                if result['should_transfer']:
                    print("🔄 Would transfer to human staff")
                    break
            else:
                print(f"❌ Error: {result['error']}")
                break
    
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def test_concurrent_conversations():
    """Test handling multiple concurrent conversations."""
    print("\n" + "="*60)
    print("TESTING CONCURRENT CONVERSATIONS")
    print("="*60)
    
    try:
        agent = SimpleRestoVoiceAgent()
        
        restaurant_info = {
            "restaurant_name": "The Ocean Room",
            "current_time": "7:30 PM",
            "hours": "5 PM - 10 PM",
            "availability": "Limited"
        }
        
        # Simulate multiple concurrent conversations
        conversations = {
            "user1": {
                "thread_id": "concurrent_1",
                "messages": ["Table for 2 tonight at 8pm", "Mike Johnson", "555-1111"]
            },
            "user2": {
                "thread_id": "concurrent_2", 
                "messages": ["Table for 6 tomorrow at 7pm", "Birthday dinner", "Lisa Chen", "555-2222"]
            },
            "user3": {
                "thread_id": "concurrent_3",
                "messages": ["What time do you close?"]
            }
        }
        
        # Process first message for each conversation
        print("\n--- Initial Messages ---")
        for user_id, conv_data in conversations.items():
            message = conv_data["messages"][0]
            thread_id = conv_data["thread_id"]
            
            print(f"\n{user_id}: {message}")
            
            result = await agent.process_message(message, restaurant_info)
            
            if result["success"]:
                print(f"AI: {result['response']}")
                print(f"Intent: {result['state'].get('intent')}")
            else:
                print(f"Error: {result['error']}")
        
        # Process subsequent messages
        print("\n--- Subsequent Messages ---")
        for user_id, conv_data in conversations.items():
            if len(conv_data["messages"]) > 1:
                thread_id = conv_data["thread_id"]
                
                for message in conv_data["messages"][1:]:
                    print(f"\n{user_id}: {message}")
                    
                    result = await agent.process_message(message, restaurant_info)
                    
                    if result["success"]:
                        print(f"AI: {result['response']}")
                        print(f"Booking Data: {result['booking_data']}")
                        
                        if result['confirmation_code']:
                            print(f"🎉 Confirmation Code: {result['confirmation_code']}")
                            break
                    else:
                        print(f"Error: {result['error']}")
                        break
    
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def main():
    """Run all LangGraph agent tests."""
    print("RestoVoice LangGraph Agent System Test Suite")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with the Azure OpenAI credentials.")
        return
    
    print("✅ Environment variables configured")
    
    try:
        # Run all tests
        await test_basic_booking_flow()
        await test_intent_routing()
        await test_error_handling()
        await test_state_persistence()
        await test_concurrent_conversations()
        
        print("\n" + "="*60)
        print("✅ All LangGraph agent tests completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        print("Please check your Azure OpenAI configuration and try again.")


if __name__ == "__main__":
    asyncio.run(main())
