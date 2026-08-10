"""
Test script for RestoVoice AI Prompt System.
Demonstrates the prompt templates working with Azure OpenAI.

Run this script to test:
- Intent classification
- Booking detail extraction  
- Natural conversation flows
- Error handling
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Load environment variables from .env file
load_dotenv()

# Import from the agents.llm package
from agents.llm.prompt_manager import PromptManager, ConversationState, AIResponse, IntentType
from agents.llm.restaurant_config import RestaurantConfigManager


def _require_env() -> bool:
    """Check if required Azure environment variables are present."""
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with the Azure OpenAI credentials.")
        return False
    
    return True


def test_intent_classification():
    """Test intent classification with various user inputs."""
    print("\n" + "="*50)
    print("TESTING INTENT CLASSIFICATION")
    print("="*50)
    
    if not _require_env():
        return
    
    manager = PromptManager()
    conversation_state = ConversationState()
    
    test_inputs = [
        "Table for four tonight at 7",
        "What time do you close?", 
        "I need to cancel my reservation",
        "Can I speak to a manager?",
        "Do you have gluten-free options?",
        "I'd like to change my reservation"
    ]
    
    for user_input in test_inputs:
        print(f"\nUser: \"{user_input}\"")
        response = manager.classify_intent(user_input, conversation_state)
        print(f"Intent: {response.intent.value}")
        print(f"Confidence: {response.confidence_score}")
        print(f"Extracted: {response.extracted_data}")


def test_booking_extraction():
    """Test booking detail extraction from natural speech."""
    print("\n" + "="*50)
    print("TESTING BOOKING EXTRACTION")
    print("="*50)
    
    if not _require_env():
        return
    
    manager = PromptManager()
    conversation_state = ConversationState()
    
    test_inputs = [
        "I need a table for four people tonight at 7pm, my name is John",
        "Tomorrow at 8pm for 2 people, Sarah",
        "Birthday dinner for 6 people this Friday at 7:30, Mike",
        "Just need a table for 1 at 6pm today"
    ]
    
    for user_input in test_inputs:
        print(f"\nUser: \"{user_input}\"")
        response = manager.extract_booking_details(user_input, conversation_state)
        print(f"Extracted Data: {response.extracted_data}")
        print(f"Missing Fields: {conversation_state.missing_fields}")
        print(f"Next Action: {response.next_action}")


def test_conversation_flow():
    """Test complete conversation flow from greeting to confirmation."""
    print("\n" + "="*50)
    print("TESTING CONVERSATION FLOW")
    print("="*50)
    
    if not _require_env():
        return
    
    manager = PromptManager()
    
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
        },
        {
            "name": "Fine Dining",
            "hours_type": "standard",
            "open_time": "5:30 PM",
            "close_time": "11:00 PM",
            "max_party_size": 8,
            "deposit_required_for_parties_above": 4,
            "deposit_amount": 50.0,
            "phone_number": "555-0125",
            "address": "789 Elegant Ave"
        }
    ]
    
    for config_data in test_configs:
        print(f"\n--- Testing {config_data['name']} ---")
        
        # Create restaurant configuration dynamically
        restaurant_config = RestaurantConfigManager.create_custom_config(**config_data)
        restaurant_info = restaurant_config.get_context_for_ai()
        
        # Add missing current_time for greeting template
        restaurant_info["current_time"] = "7:30 PM"
        # Map name to restaurant_name for template compatibility
        restaurant_info["restaurant_name"] = restaurant_info.get("name", "Unknown Restaurant")
        # Map operating_hours to hours for template compatibility  
        restaurant_info["hours"] = restaurant_info.get("operating_hours", "Unknown hours")
        # Add availability for template
        restaurant_info["availability"] = "Available"
        
        print(f"Hours: {restaurant_info['operating_hours']}")
        print(f"Max Party: {restaurant_info['max_party_size']}")
        
        # Start with greeting
        greeting_response = manager.generate_greeting(restaurant_info)
        print(f"AI: {greeting_response.text}")
        
        # Simulate user booking request
        conversation_state = ConversationState()
        user_input = "Table for four tonight at 7pm"
        
        print(f"User: {user_input}")
        
        # Classify intent
        intent_response = manager.classify_intent(user_input, conversation_state)
        print(f"Detected Intent: {intent_response.intent.value}")
        
        # Extract booking details with restaurant config
        booking_response = manager.extract_booking_details(user_input, conversation_state, restaurant_config)
        print(f"Collected Data: {conversation_state.collected_data}")
        print(f"Missing Fields: {conversation_state.missing_fields}")
        
        # Collect missing information
        if conversation_state.missing_fields:
            data_response = manager.collect_missing_data(conversation_state, restaurant_info)
            print(f"AI: {data_response.text}")
            
            # Simulate user providing missing info
            user_input = "The name is John Smith, phone is 555-1234"
            print(f"User: {user_input}")
            booking_response = manager.extract_booking_details(user_input, conversation_state, restaurant_config)
            print(f"Updated Data: {conversation_state.collected_data}")
        
        # Validate booking
        restaurant_policies = restaurant_config.policies.to_dict()
        validation_response = manager.validate_booking(conversation_state, restaurant_policies)
        print(f"AI: {validation_response.text}")
        print(f"Next Action: {validation_response.next_action}")
        
        # Generate confirmation
        if validation_response.next_action == "confirm_booking":
            confirmation_response = manager.generate_confirmation(conversation_state, restaurant_info)
            print(f"AI: {confirmation_response.text}")
            print(f"SMS Content: {confirmation_response.extracted_data.get('sms_content', '')}")
        
        print("-" * 30)


def test_error_handling():
    """Test various error handling scenarios."""
    print("\n" + "="*50)
    print("TESTING ERROR HANDLING")
    print("="*50)
    
    if not _require_env():
        return
    
    manager = PromptManager()
    conversation_state = ConversationState()
    conversation_state.last_response = "How many people will be dining with us?"
    
    # Test no response handling
    print("\n1. NO RESPONSE (10 seconds of silence)")
    error_response = manager.handle_error("no_response", conversation_state, {"duration": 10})
    print(f"AI: {error_response.text}")
    print(f"Action: {error_response.next_action}")
    
    # Test unclear speech handling
    print("\n2. UNCLEAR SPEECH")
    error_response = manager.handle_error("unclear_speech", conversation_state, {
        "clarity_score": 0.3,
        "confidence_levels": {"party_size": 0.2, "time": 0.1}
    })
    print(f"AI: {error_response.text}")
    print(f"Action: {error_response.next_action}")
    
    # Test system error handling
    print("\n3. SYSTEM ERROR")
    error_response = manager.handle_error("no_response", conversation_state, {
        "recovery_options": ["retry", "transfer"]
    })
    print(f"AI: {error_response.text}")
    print(f"Should Transfer: {error_response.should_transfer}")


def test_prompt_templates():
    """Test the prompt template system directly."""
    print("\n" + "="*50)
    print("TESTING PROMPT TEMPLATES")
    print("="*50)
    
    from agents.llm.prompts import PromptTemplates
    
    # List all available prompts
    available = PromptTemplates.list_prompts()
    print("\nAvailable Prompts:")
    for category, prompts in available.items():
        print(f"\n{category.upper()}:")
        for prompt in prompts:
            print(f"  - {prompt}")
    
    # Test a formatted prompt
    print("\nSample Greeting Prompt:")
    greeting = PromptTemplates.get_prompt("conversation", "greeting",
        restaurant_name="The Ocean Room",
        current_time="7:30 PM",
        hours="5 PM - 10 PM",
        availability="Limited"
    )
    print(greeting)


def main():
    """Run all tests."""
    print("RestoVoice AI Prompt System Test")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with the Azure OpenAI credentials.")
        return
    
    print("✅ Environment variables configured")
    
    try:
        # Run tests
        test_prompt_templates()
        test_intent_classification()
        test_booking_extraction()
        test_conversation_flow()
        test_error_handling()
        
        print("\n" + "="*50)
        print("✅ All tests completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Please check your Azure OpenAI configuration and try again.")


if __name__ == "__main__":
    main()
