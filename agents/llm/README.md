# RestoVoice AI Prompt System

A comprehensive prompt management system for the RestoVoice AI voice reservation agent, built on Azure OpenAI.

## Overview

This system provides:
- **Reusable prompt templates** for all conversation scenarios
- **Azure OpenAI integration** with your configured deployment
- **Conversation state management** for natural dialog flow
- **Intent classification** and **booking detail extraction**
- **Error handling** for edge cases and system failures
- **Policy validation** against restaurant rules

## Architecture

### Files Structure

```
agents/llm/
├── llm.py              # Basic Azure OpenAI client setup
├── prompts.py          # Comprehensive prompt templates
├── prompt_manager.py   # Main prompt management and AI integration
├── test_prompts.py     # Test suite and examples
└── README.md          # This documentation
```

### Core Components

1. **PromptTemplates** (`prompts.py`)
   - Centralized prompt templates for all scenarios
   - Categories: System, Intent, Conversation, Error, Policy
   - Dynamic formatting with context variables

2. **PromptManager** (`prompt_manager.py`)
   - Azure OpenAI integration
   - Conversation state tracking
   - Response parsing and validation
   - Error handling and recovery

3. **ConversationState** (`prompt_manager.py`)
   - Tracks current conversation progress
   - Manages collected booking data
   - Handles missing fields and validation

## Setup

### Environment Variables

Create a `.env` file in the `ai-backend` directory:


```

### Dependencies

```bash
uv add openai python-dotenv
```

## Usage

### Basic Usage

```python
from agents.llm.prompt_manager import PromptManager, ConversationState

# Initialize the manager
manager = PromptManager()

# Start a conversation
conversation_state = ConversationState()

# Generate greeting
restaurant_info = {
    "restaurant_name": "The Ocean Room",
    "current_time": "7:30 PM",
    "hours": "5 PM - 10 PM",
    "availability": "Limited"
}

greeting = manager.generate_greeting(restaurant_info)
print(greeting.text)  # "Good evening, thank you for calling The Ocean Room..."

# Classify user intent
user_input = "Table for four tonight at 7"
intent_response = manager.classify_intent(user_input, conversation_state)
print(intent_response.intent)  # IntentType.BOOKING

# Extract booking details
booking_response = manager.extract_booking_details(user_input, conversation_state)
print(booking_response.extracted_data)  # {"party_size": 4, "time": "7pm", "date": "tonight"}
```

### Complete Conversation Flow

```python
# 1. Greeting
greeting = manager.generate_greeting(restaurant_info)

# 2. User says: "Table for four tonight at 7pm"
intent = manager.classify_intent("Table for four tonight at 7pm", conversation_state)
booking = manager.extract_booking_details("Table for four tonight at 7pm", conversation_state)

# 3. Collect missing info
if conversation_state.missing_fields:
    data_question = manager.collect_missing_data(conversation_state, restaurant_info)
    # AI: "Great! And can I get your name and phone number for the reservation?"

# 4. User provides: "John Smith, 555-1234"
booking = manager.extract_booking_details("John Smith, 555-1234", conversation_state)

# 5. Validate against policies
validation = manager.validate_booking(conversation_state, restaurant_policies)

# 6. Confirm booking
if validation.next_action == "confirm_booking":
    confirmation = manager.generate_confirmation(conversation_state, restaurant_info)
    print(confirmation.text)  # "Perfect! I've got your reservation for 4 people..."
```

## Prompt Categories

### System Prompts
- `main_agent`: Primary AI agent behavior and personality
- `payment_agent`: PCI-compliant payment collection
- `availability_agent`: Real-time availability checking
- `transfer_agent`: Human transfer coordination

### Intent Classification
- `primary_intent`: Classify overall conversation intent
- `booking_intent`: Extract specific booking details

### Conversation Flows
- `greeting`: Natural restaurant greeting
- `data_collection`: Collect missing booking information
- `confirmation`: Booking confirmation summary
- `alternatives`: Suggest alternative time slots

### Error Handling
- `no_response`: Handle silence/no input
- `unclear_speech`: Handle mumbled or unclear speech
- `system_error`: Handle technical failures

### Policy Validation
- `booking_rules`: Validate against restaurant policies
- `deposit_rules`: Determine deposit requirements

## Testing

Run the test suite to verify everything works:

```bash
uv run python agents/llm/test_prompts.py
```

This will test:
- Intent classification accuracy
- Booking detail extraction
- Complete conversation flows
- Error handling scenarios
- Prompt template formatting

## Integration with RestoVoice Architecture

This AI service follows the monorepo guidelines:

### Python AI Service Responsibilities
- ✅ Voice processing and intent recognition
- ✅ Natural language understanding
- ✅ Policy evaluation (read-only)
- ✅ JSON payload generation for Next.js

### Next.js Platform Responsibilities  
- ❌ Database operations
- ❌ Authentication/authorization
- ❌ Payment processing
- ❌ Webhook integrations
- ❌ Frontend dashboards

## Customization

### Adding New Prompts

1. Add to the appropriate category in `prompts.py`
2. Include context variables with `{variable_name}` format
3. Update `PromptTemplates.list_prompts()` if needed

```python
# Example: New custom prompt
CUSTOM_PROMPTS = {
    "special_occasion": """Handle special occasion requests.

Context:
- Occasion: {occasion_type}
- Party details: {party_details}
- Restaurant capabilities: {capabilities}

Response: JSON with accommodation_options, pricing, next_steps"""
}
```

### Modifying AI Behavior

Adjust the system prompts in `PromptTemplates.SYSTEM_AGENTS` to change:
- Personality and tone
- Safety rules and boundaries
- Response formats
- Error handling strategies

### Adding New Intents

1. Add to `IntentType` enum
2. Update classification prompt examples
3. Add handling logic in `PromptManager.classify_intent()`

## Best Practices

1. **Temperature Settings**:
   - Classification: 0.1-0.2 (consistent results)
   - Conversation: 0.5-0.7 (natural variation)
   - Error handling: 0.3-0.4 (balanced reliability)

2. **Response Validation**:
   - Always validate JSON responses
   - Provide fallbacks for API failures
   - Monitor confidence scores

3. **Safety First**:
   - Never expose system errors to users
   - Always offer human transfer for complex cases
   - Maintain PCI compliance during payments

4. **Performance**:
   - Cache frequently used prompts
   - Limit response tokens for faster replies
   - Use streaming for long conversations

## Troubleshooting

### Common Issues

1. **Azure OpenAI Connection Errors**
   - Check environment variables
   - Verify endpoint URL format
   - Confirm deployment name

2. **JSON Parsing Errors**
   - Validate response format in prompts
   - Add try-catch blocks around JSON parsing
   - Monitor for unexpected AI responses

3. **Low Confidence Scores**
   - Adjust temperature settings
   - Improve prompt clarity
   - Add more examples to prompts

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- API request/response details
- Prompt templates being used
- Conversation state changes
- Error stack traces

## Contributing

When adding new features:

1. Follow the existing code structure
2. Add comprehensive tests
3. Update documentation
4. Respect the AI/Platform boundary
5. Maintain backward compatibility

## Support

For issues with:
- **Azure OpenAI**: Check Azure portal and deployment status
- **Prompt Logic**: Review prompt templates and test outputs
- **Integration**: Verify environment variables and API keys
- **Architecture**: Refer to `.github/agent.md` for guidelines
