"""
Clean version of prompt manager without hardcoded values and main functions.
"""

import os
import json
import re
import hashlib
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from google import genai
from dotenv import load_dotenv
from .prompts import PromptTemplates, IntentType
from .restaurant_config import RestaurantConfig, RestaurantConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_user_input(user_input: str) -> str:
    """Validate and sanitize user input."""
    if not user_input or not isinstance(user_input, str):
        raise ValueError("Invalid user input: must be a non-empty string")
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\'\\]', '', user_input.strip())
    
    # Length validation - configurable limit
    max_input_length = int(os.getenv("MAX_INPUT_LENGTH", "1000"))
    if len(sanitized) > max_input_length:
        raise ValueError(f"Input too long: maximum {max_input_length} characters allowed")
    
    if len(sanitized) < 1:
        raise ValueError("Input too short: minimum 1 character required")
    
    return sanitized


def safe_json_parse(json_string: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """Safely parse JSON with fallback."""
    try:
        if not json_string or not isinstance(json_string, str):
            return fallback
        
        result = json.loads(json_string)
        if not isinstance(result, dict):
            return fallback
        
        return result
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"JSON parsing failed: {e}")
        return fallback


def generate_confirmation_code(booking_data: Dict[str, Any]) -> str:
    """Generate a safe confirmation code."""
    try:
        # Create a stable string representation
        data_str = json.dumps(booking_data, sort_keys=True)
        # Use SHA256 for consistent hashing
        hash_obj = hashlib.sha256(data_str.encode())
        # Take first 6 characters of hex digest
        return "RV" + hash_obj.hexdigest()[:6].upper()
    except Exception as e:
        logger.warning(f"Confirmation code generation failed: {e}")
        # Fallback to random code
        import random
        return "RV" + f"{random.randint(100000, 999999)}"


@dataclass
class ConversationState:
    """Tracks the current state of a conversation."""
    intent: Optional[IntentType] = None
    collected_data: Dict[str, Any] = None
    missing_fields: List[str] = None
    current_step: str = "greeting"
    confidence_score: float = 0.0
    error_count: int = 0
    last_response: Optional[str] = None
    
    def __post_init__(self):
        if self.collected_data is None:
            self.collected_data = {}
        if self.missing_fields is None:
            self.missing_fields = []


@dataclass
class AIResponse:
    """Structured response from the AI agent."""
    text: str
    intent: Optional[IntentType] = None
    extracted_data: Dict[str, Any] = None
    next_action: str = "continue"
    confidence_score: float = 0.0
    should_transfer: bool = False
    transfer_reason: Optional[str] = None
    
    def __post_init__(self):
        if self.extracted_data is None:
            self.extracted_data = {}


class PromptManager:
    """Manages AI prompts and Google Gemini integration."""
    
    def __init__(self):
        """Initialize the prompt manager with Google Gemini client."""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                raise ValueError("Missing required Gemini API key")
            
            self.client = genai.Client(api_key=api_key)
            self.model = "gemma-3-27b"
            logger.info("PromptManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PromptManager: {e}")
            raise
    
    def _call_gemini(self, prompt: str, temperature: float = 0.1, max_tokens: int = 200) -> str:
        """Helper method to call Gemini API."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )
        
        if not response or not hasattr(response, 'text'):
            raise ValueError("Invalid response structure from Gemini")
        
        content = response.text
        if not content:
            raise ValueError("Empty response content from Gemini")
        
        return content
    
    def classify_intent(self, user_input: str, conversation_state: ConversationState) -> AIResponse:
        """Classify the user's intent from their speech input."""
        try:
            # Validate input
            sanitized_input = validate_user_input(user_input)
            
            prompt = PromptTemplates.get_prompt("intent", "primary_intent")
            
            # Create prompt for Gemini
            full_prompt = f"{prompt}\n\nUser said: \"{sanitized_input}\"\n\nClassify the intent and return as valid JSON:"
            
            content = self._call_gemini(full_prompt, temperature=0.1, max_tokens=200)
            
            result = safe_json_parse(content, {
                "primary_intent": "inquiry",
                "confidence_score": 0.0,
                "key_entities": {}
            })
            
            return AIResponse(
                text="",
                intent=IntentType(result.get("primary_intent", "inquiry")),
                confidence_score=float(result.get("confidence_score", 0.0)),
                extracted_data=result.get("key_entities", {})
            )
            
        except ValueError as e:
            logger.warning(f"Input validation error in classify_intent: {e}")
            return AIResponse(
                text="I'm having trouble understanding. Could you please repeat that?",
                intent=IntentType.INQUIRY,
                confidence_score=0.0,
                should_transfer=True,
                transfer_reason="Input validation error"
            )
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return AIResponse(
                text="I'm having trouble understanding. Could you please repeat that?",
                intent=IntentType.INQUIRY,
                confidence_score=0.0,
                should_transfer=True,
                transfer_reason="Classification error"
            )
    
    def extract_booking_details(self, user_input: str, conversation_state: ConversationState, restaurant_config: RestaurantConfig = None, restaurant_info: Dict[str, Any] = None) -> AIResponse:
        """Extract booking details from user input."""
        try:
            # Validate input
            sanitized_input = validate_user_input(user_input)
            
            prompt = PromptTemplates.get_prompt("intent", "booking_intent")
            
            # Use provided config or create minimal default from restaurant_info
            if restaurant_config is None:
                if restaurant_info is None:
                    restaurant_info = {}
                config_params = {
                    "name": restaurant_info.get("restaurant_name", "Restaurant"),
                    "hours_type": restaurant_info.get("hours_type", "standard"),
                    "open_time": restaurant_info.get("open_time"),
                    "close_time": restaurant_info.get("close_time"),
                    "max_party_size": restaurant_info.get("max_party_size", 0),
                    "phone_number": restaurant_info.get("phone_number", ""),
                    "address": restaurant_info.get("address", "")
                }
                restaurant_config = RestaurantConfigManager.create_custom_config(**config_params)
            
            context = {
                "collected_data": json.dumps(conversation_state.collected_data),
                "missing_fields": json.dumps(conversation_state.missing_fields),
                "restaurant_context": json.dumps(restaurant_config.get_context_for_ai())
            }
            
            full_prompt = f"{prompt.format(**context)}\n\nUser said: \"{sanitized_input}\"\n\nExtract booking details and return as valid JSON:"
            
            content = self._call_gemini(full_prompt, temperature=0.2, max_tokens=300)
            
            result = safe_json_parse(content, {
                "extracted_fields": {},
                "missing_fields": [],
                "confidence_scores": {}
            })
            
            # Update conversation state with extracted data
            extracted = result.get("extracted_fields", {})
            if isinstance(extracted, dict):
                conversation_state.collected_data.update(extracted)
            
            missing_fields = result.get("missing_fields", [])
            if isinstance(missing_fields, list):
                conversation_state.missing_fields = missing_fields
            
            return AIResponse(
                text="",
                intent=IntentType.BOOKING,
                extracted_data=extracted if isinstance(extracted, dict) else {},
                confidence_score=result.get("confidence_scores", {}).get("overall", 0.0),
                next_action="validate_booking"
            )
            
        except ValueError as e:
            logger.warning(f"Input validation error in extract_booking_details: {e}")
            return AIResponse(
                text="I'm having trouble getting those details. Let me connect you with someone who can help.",
                should_transfer=True,
                transfer_reason="Input validation error"
            )
        except Exception as e:
            logger.error(f"Booking extraction error: {e}")
            return AIResponse(
                text="I'm having trouble getting those details. Let me connect you with someone who can help.",
                should_transfer=True,
                transfer_reason="Extraction error"
            )
    
    def generate_greeting(self, restaurant_info: Dict[str, Any]) -> AIResponse:
        """Generate a natural restaurant greeting."""
        prompt = PromptTemplates.get_prompt("conversation", "greeting", **restaurant_info)
        
        full_prompt = f"You are a professional restaurant host. Generate a warm, natural greeting.\n\n{prompt}"
        
        try:
            content = self._call_gemini(full_prompt, temperature=0.7, max_tokens=150)
            
            result = safe_json_parse(content, {
                "greeting_text": "Thank you for calling! How can I help you today?"
            })
            
            return AIResponse(
                text=result.get("greeting_text", "Thank you for calling! How can I help you today?"),
                next_action="listen_for_intent"
            )
            
        except Exception as e:
            logger.error(f"Greeting generation error: {e}")
            return AIResponse(
                text="Thank you for calling! How can I help you today?",
                next_action="listen_for_intent"
            )
    
    def collect_missing_data(self, conversation_state: ConversationState, restaurant_info: Dict[str, Any]) -> AIResponse:
        """Generate questions to collect missing booking information."""
        if not conversation_state.missing_fields:
            return AIResponse(
                text="Perfect! I have all the information I need. Let me confirm those details with you.",
                next_action="confirm_booking"
            )
        
        context = {
            "collected_data": json.dumps(conversation_state.collected_data),
            "missing_fields": json.dumps(conversation_state.missing_fields),
            "restaurant_context": json.dumps(restaurant_info)
        }
        
        prompt = PromptTemplates.get_prompt("conversation", "data_collection", **context)
        
        full_prompt = f"You are a restaurant host collecting reservation details naturally.\n\n{prompt}"
        
        try:
            content = self._call_gemini(full_prompt, temperature=0.5, max_tokens=200)
            
            result = safe_json_parse(content, {
                "next_question": "Could you help me with a few more details?",
                "field_being_collected": "general",
                "helpful_context": ""
            })
            
            return AIResponse(
                text=result.get("next_question", "Could you help me with a few more details?"),
                next_action="listen_for_details"
            )
            
        except Exception as e:
            logger.error(f"Data collection error: {e}")
            # Fallback to simple question based on most important missing field
            if "party_size" in conversation_state.missing_fields:
                return AIResponse(text="How many people will be dining with us?")
            elif "date" in conversation_state.missing_fields:
                return AIResponse(text="What date would you like to come in?")
            else:
                return AIResponse(text="Could you provide a few more details about your reservation?")
    
    def validate_booking(self, conversation_state: ConversationState, restaurant_policies: Dict[str, Any]) -> AIResponse:
        """Validate booking against restaurant policies."""
        context = {
            "booking_request": json.dumps(conversation_state.collected_data),
            "policies": json.dumps(restaurant_policies),
            "availability": json.dumps({"status": "checking"})  # Would be populated from real availability check
        }
        
        prompt = PromptTemplates.get_prompt("policy", "booking_rules", **context)
        
        full_prompt = f"You are validating a restaurant booking request against policies.\n\n{prompt}"
        
        try:
            content = self._call_gemini(full_prompt, temperature=0.1, max_tokens=300)
            
            result = safe_json_parse(content, {
                "validation_result": "invalid",
                "policy_violations": [],
                "suggested_modifications": []
            })
            
            validation_result = result.get("validation_result", "invalid")
            
            if validation_result == "valid":
                return AIResponse(
                    text="Great! That time works perfectly. Let me confirm all the details with you.",
                    next_action="confirm_booking"
                )
            elif validation_result == "alternatives_available":
                alternatives = result.get("suggested_modifications", [])
                if not isinstance(alternatives, list) or not alternatives:
                    return AIResponse(
                        text="That time isn't available. Would you like to try a different time or speak with a staff member?",
                        next_action="handle_rejection",
                        should_transfer=True,
                        transfer_reason="No alternatives available"
                    )
                
                alt_text = "That time isn't available, but I do have some alternatives. "
                for i, alt in enumerate(alternatives[:2]):  # Limit to 2 alternatives
                    if isinstance(alt, dict):
                        time_slot = alt.get('time', alt.get('time_slot', f'slot {i+1}'))
                        alt_text += f"I could do {time_slot}"
                        if i < len(alternatives[:2]) - 1:
                            alt_text += " or "
                        else:
                            alt_text += ". "
                
                return AIResponse(
                    text=alt_text,
                    next_action="offer_alternatives",
                    extracted_data={"alternatives": alternatives[:2]}
                )
            else:
                violations = result.get("policy_violations", [])
                return AIResponse(
                    text=f"I'm sorry, but I can't make that reservation due to: {', '.join(violations)}. Would you like to try a different time or speak with a staff member?",
                    next_action="handle_rejection",
                    should_transfer=True,
                    transfer_reason="Policy violation"
                )
                
        except Exception as e:
            logger.error(f"Booking validation error: {e}")
            return AIResponse(
                text="I'm having trouble checking availability. Let me connect you with our staff right away.",
                should_transfer=True,
                transfer_reason="Validation system error"
            )
    
    def generate_confirmation(self, conversation_state: ConversationState, restaurant_info: Dict[str, Any]) -> AIResponse:
        """Generate booking confirmation summary."""
        context = {
            "booking_details": json.dumps(conversation_state.collected_data),
            "restaurant_info": json.dumps(restaurant_info),
            "payment_info": json.dumps({"deposit_required": False})  # Would be populated from payment check
        }
        
        prompt = PromptTemplates.get_prompt("conversation", "confirmation", **context)
        
        full_prompt = f"You are confirming a restaurant reservation with a guest.\n\n{prompt}"
        
        try:
            content = self._call_gemini(full_prompt, temperature=0.3, max_tokens=400)
            
            result = safe_json_parse(content, {
                "confirmation_text": "Your reservation is confirmed!",
                "sms_content": ""
            })
            
            return AIResponse(
                text=result.get("confirmation_text", "Your reservation is confirmed!"),
                next_action="complete_booking",
                extracted_data={
                    "sms_content": result.get("sms_content", ""),
                    "confirmation_code": generate_confirmation_code(conversation_state.collected_data)
                }
            )
            
        except Exception as e:
            logger.error(f"Confirmation generation error: {e}")
            # Fallback confirmation
            details = conversation_state.collected_data
            return AIResponse(
                text=f"Perfect! I've got your reservation for {details.get('party_size', 'X')} people on {details.get('date', 'X')} at {details.get('time', 'X')}. You'll receive a confirmation text shortly.",
                next_action="complete_booking",
                extracted_data={
                    "confirmation_code": generate_confirmation_code(conversation_state.collected_data)
                }
            )
    
    def handle_error(self, error_type: str, conversation_state: ConversationState, context: Dict[str, Any]) -> AIResponse:
        """Handle various error situations gracefully."""
        prompt_context = {
            "silence_seconds": str(context.get("duration", 0)),
            "last_question": conversation_state.last_response or "No previous question",
            "conversation_state": conversation_state.current_step,
            "clarity_score": str(context.get("clarity_score", context.get("clarity", 0.5))),
            "attempted_data": json.dumps(context.get("attempted_data", {})),
            "confidence_levels": json.dumps(context.get("confidence_levels", {})),
            "error_type": error_type,
            "recovery_options": json.dumps(context.get("recovery_options", []))
        }
        
        if error_type == "no_response":
            prompt = PromptTemplates.get_prompt("error", "no_response", **prompt_context)
        elif error_type == "unclear_speech":
            prompt = PromptTemplates.get_prompt("error", "unclear_speech", **prompt_context)
        else:
            prompt = PromptTemplates.get_prompt("error", "system_error", **prompt_context)
        
        full_prompt = f"You are handling an error situation in a restaurant reservation call.\n\n{prompt}"
        
        try:
            content = self._call_gemini(full_prompt, temperature=0.4, max_tokens=200)
            
            result = safe_json_parse(content, {
                "message": "I'm having trouble. Let me connect you with someone who can help.",
                "action": "transfer"
            })
            
            return AIResponse(
                text=result.get("message", "I'm having trouble. Let me connect you with someone who can help."),
                next_action=result.get("action", "transfer"),
                should_transfer=result.get("escalation_needed", False),
                transfer_reason=error_type
            )
            
        except Exception as e:
            logger.error(f"Error handling error: {e}")
            return AIResponse(
                text="I'm experiencing technical difficulties. Let me connect you with our staff.",
                should_transfer=True,
                transfer_reason="System error"
            )
