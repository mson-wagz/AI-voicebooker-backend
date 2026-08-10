"""
Simplified LangGraph-based agent system for RestoVoice.
This version focuses on core functionality without complex routing.

Key Features:
- State-based conversation management
- Intent classification and routing
- Booking flow orchestration
- Error handling and recovery
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from google import genai
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.llm.prompts import PromptTemplates, IntentType
from agents.llm.prompt_manager import validate_user_input, safe_json_parse, generate_confirmation_code
from agents.llm.restaurant_config import RestaurantConfig, RestaurantConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationState(TypedDict):
    """Simplified conversation state for LangGraph."""
    messages: List
    intent: Optional[str]
    booking_data: Dict[str, Any]
    missing_fields: List[str]
    current_step: str
    confidence_score: float
    should_transfer: bool
    transfer_reason: Optional[str]
    restaurant_info: Dict[str, Any]
    error_count: int
    confirmation_code: Optional[str]


class SimpleRestoVoiceAgent:
    """Simplified LangGraph agent for RestoVoice.   """
    
    def __init__(self):
        """Initialize the agent system."""
        try:
            # Initialize Google Gemini
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Missing GEMINI_API_KEY")
            
            self.client = genai.Client(api_key=api_key)
            self.model = "gemma-3-27b"
            
            # Build and compile the graph
            self.graph = self._build_graph()
            
            logger.info("Simple RestoVoice agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    def _build_graph(self) -> StateGraph:
        """Build a simplified state graph."""
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("handle_booking", self._handle_booking)
        workflow.add_node("handle_inquiry", self._handle_inquiry)
        workflow.add_node("handle_transfer", self._handle_transfer)
        workflow.add_node("handle_error", self._handle_error)
        
        # Set entry point
        workflow.set_entry_point("classify_intent")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "booking": "handle_booking",
                "inquiry": "handle_inquiry", 
                "transfer": "handle_transfer",
                "complex": "handle_transfer",
                "error": "handle_error",
                "end": END
            }
        )
        
        # All other nodes end the conversation
        workflow.add_edge("handle_booking", END)
        workflow.add_edge("handle_inquiry", END)
        workflow.add_edge("handle_transfer", END)
        workflow.add_edge("handle_error", END)
        
    def _classify_intent(self, state: ConversationState) -> ConversationState:
        """Classify user intent."""
        try:
            # Get the latest message
            latest_message = state["messages"][-1] if state["messages"] else None
            if not latest_message:
                return self._update_state(state, {
                    "current_step": "error",
                    "should_transfer": True,
                    "transfer_reason": "No message provided"
                })
            
            # Classify intent using prompt
            intent_prompt = PromptTemplates.get_prompt("intent", "primary_intent")
            
            full_prompt = f"{intent_prompt}\n\nUser said: \"{latest_message.content}\"\n\nClassify the intent and return as valid JSON:"
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            result = safe_json_parse(response.text, {
                "primary_intent": "inquiry",
                "confidence_score": 0.0,
                "key_entities": {}
            })
            
            intent = result.get("primary_intent", "inquiry")
            confidence = float(result.get("confidence_score", 0.0))
            
            # Update state
            updates = {
                "intent": intent,
                "confidence_score": confidence,
                "current_step": intent
            }
            
            # Extract key entities if available
            key_entities = result.get("key_entities", {})
            if key_entities:
                updates["booking_data"] = {**state.get("booking_data", {}), **key_entities}
            
            return self._update_state(state, updates)
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return self._update_state(state, {
                "current_step": "error",
                "error_count": state.get("error_count", 0) + 1
            })
    
    def _handle_booking(self, state: ConversationState) -> ConversationState:
        """Handle booking requests."""
        try:
            latest_message = state["messages"][-1]
            current_booking_data = state.get("booking_data", {})
            restaurant_info = state.get("restaurant_info", {})
            
            # Get restaurant configuration from restaurant_info
            config_params = {
                "name": restaurant_info.get("restaurant_name", "Restaurant"),
                "hours_type": restaurant_info.get("hours_type", "standard"),
                "open_time": restaurant_info.get("open_time", "11:00 AM"),
                "close_time": restaurant_info.get("close_time", "10:00 PM"),
                "max_party_size": restaurant_info.get("max_party_size", 20),
                "phone_number": restaurant_info.get("phone_number", "555-0000"),
                "address": restaurant_info.get("address", "Address")
            }
            restaurant_config = RestaurantConfigManager.create_custom_config(**config_params)
            
            # Extract booking details
            booking_prompt = PromptTemplates.get_prompt("intent", "booking_intent")
            
            context = {
                "collected_data": json.dumps(current_booking_data),
                "missing_fields": json.dumps(state.get("missing_fields", [])),
                "restaurant_context": json.dumps(restaurant_config.get_context_for_ai())
            }
            
            full_prompt = f"{booking_prompt.format(**context)}\n\nUser said: \"{latest_message.content}\"\n\nExtract booking details and return as valid JSON:"
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            result = safe_json_parse(response.text, {
                "extracted_fields": {},
                "missing_fields": [],
                "confidence_scores": {}
            })
            
            # Update booking data
            extracted = result.get("extracted_fields", {})
            updated_booking_data = {**current_booking_data, **extracted}
            missing_fields = result.get("missing_fields", [])
            
            # Generate response
            if all(field in updated_booking_data for field in ["party_size", "date", "time", "name", "contact"]):
                # Complete booking - generate confirmation
                confirmation_code = generate_confirmation_code(updated_booking_data)
                confirmation_text = f"Perfect! I've got your reservation for {updated_booking_data.get('party_size')} people on {updated_booking_data.get('date')} at {updated_booking_data.get('time')}. Your confirmation code is {confirmation_code}. You'll receive a text message shortly."
                
                return self._update_state(state, {
                    "messages": state["messages"] + [dict(content=confirmation_text)],
                    "booking_data": updated_booking_data,
                    "missing_fields": [],
                    "confirmation_code": confirmation_code,
                    "current_step": "complete"
                })
            else:
                # Need more information
                response_text = self._generate_data_collection_response(missing_fields)
                
                return self._update_state(state, {
                    "messages": state["messages"] + [dict(content=response_text)],
                    "booking_data": updated_booking_data,
                    "missing_fields": missing_fields,
                    "current_step": "collecting_data"
                })
            
        except Exception as e:
            logger.error(f"Booking handling error: {e}")
            return self._update_state(state, {
                "current_step": "error",
                "error_count": state.get("error_count", 0) + 1
            })
    
    def _handle_inquiry(self, state: ConversationState) -> ConversationState:
        """Handle general inquiries."""
        try:
            latest_message = state["messages"][-1]
            restaurant_info = state.get("restaurant_info", {})
            
            # Generate inquiry response
            inquiry_prompt = f"""You are a helpful restaurant host. Answer the user's question naturally and professionally.

Restaurant Information:
- Name: {restaurant_info.get('restaurant_name', 'The Restaurant')}
- Hours: {restaurant_info.get('hours', '5 PM - 10 PM')}
- Current Time: {restaurant_info.get('current_time', '7:30 PM')}
- Availability: {restaurant_info.get('availability', 'Available')}

User Question: {latest_message.content}

Provide a helpful, concise answer. If they seem interested in making a reservation, offer to help with that."""
            
            full_prompt = f"You are a professional restaurant host.\n\n{inquiry_prompt}"
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            
            return self._update_state(state, {
                "messages": state["messages"] + [dict(content=response.text)],
                "current_step": "inquiry_answered"
            })
            
        except Exception as e:
            logger.error(f"Inquiry handling error: {e}")
            return self._update_state(state, {
                "messages": state["messages"] + [dict(content="I'd be happy to help you with that. Could you please tell me more?")],
                "current_step": "error"
            })
    
    def _handle_transfer(self, state: ConversationState) -> ConversationState:
        """Handle transfer to human staff."""
        try:
            transfer_reason = state.get("transfer_reason", "Guest requested human assistance")
            booking_data = state.get("booking_data", {})
            
            transfer_message = f"I'll connect you with one of our staff members right away ({transfer_reason}). "
            if booking_data:
                transfer_message += f"I've noted that you're interested in a reservation for {booking_data.get('party_size', 'X')} people."
            
            return self._update_state(state, {
                "messages": state["messages"] + [dict(content=transfer_message)],
                "should_transfer": True,
                "current_step": "transfer"
            })
            
        except Exception as e:
            logger.error(f"Transfer handling error: {e}")
            return self._update_state(state, {
                "messages": state["messages"] + [dict(content="I'm connecting you with our staff now.")],
                "should_transfer": True,
                "current_step": "transfer"
            })
    
    def _handle_error(self, state: ConversationState) -> ConversationState:
        """Handle errors."""
        try:
            error_count = state.get("error_count", 0)
            
            if error_count >= 3:
                # Too many errors, transfer to human
                return self._update_state(state, {
                    "messages": state["messages"] + [dict(content="I'm having trouble helping you. Let me connect you with our staff right away.")],
                    "should_transfer": True,
                    "transfer_reason": "Multiple errors occurred",
                    "current_step": "transfer"
                })
            
            # Try to recover
            recovery_message = "I'm having a bit of trouble. Could you please repeat that?"
            return self._update_state(state, {
                "messages": state["messages"] + [dict(content=recovery_message)],
                "current_step": "recovery"
            })
            
        except Exception as e:
            logger.error(f"Error handler failed: {e}")
            return self._update_state(state, {
                "messages": state["messages"] + [dict(content="I need to connect you with our staff.")],
                "should_transfer": True,
                "current_step": "transfer"
            })
    
    def _route_by_intent(self, state: ConversationState) -> str:
        """Route based on classified intent."""
        intent = state.get("intent", "inquiry")
        
        routing_map = {
            "booking": "booking",
            "payment": "booking",  # Handle payment through booking flow
            "transfer_request": "transfer",
            "complex_request": "transfer",
            "cancellation": "transfer",
            "modification": "transfer",
            "inquiry": "inquiry",
        }
        
        return routing_map.get(intent, "inquiry")
    
    def _update_state(self, state: ConversationState, updates: Dict[str, Any]) -> ConversationState:
        """Update state with new values."""
        updated_state = state.copy()
        updated_state.update(updates)
        return updated_state
    
    def _generate_data_collection_response(self, missing_fields: List[str]) -> str:
        """Generate response to collect missing booking data."""
        if not missing_fields:
            return "Perfect! I have all the information I need. Let me confirm those details with you."
        
        field_priority = ["party_size", "date", "time", "name", "contact"]
        for field in field_priority:
            if field in missing_fields:
                responses = {
                    "party_size": "How many people will be dining with us?",
                    "date": "What date would you like to come in?",
                    "time": "What time would you prefer?",
                    "name": "And what's your name for the reservation?",
                    "contact": "Could I get your phone number for the reservation?"
                }
                return responses.get(field, "Could you help me with a few more details?")
        
        return "Could you help me with a few more details about your reservation?"
    
    async def process_message(self, 
                            user_input: str,
                            restaurant_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process a user message through the agent system."""
        try:
            # Validate input
            sanitized_input = validate_user_input(user_input)
            
            # Initialize state
            initial_state = ConversationState(
                messages=[HumanMessage(content=sanitized_input)],
                intent=None,
                booking_data={},
                missing_fields=[],
                current_step="greeting",
                confidence_score=0.0,
                should_transfer=False,
                transfer_reason=None,
                restaurant_info=restaurant_info,
                error_count=0,
                confirmation_code=None
            )
            
            # Run the graph
            result = await self.graph.ainvoke(initial_state)
            
            # Extract the latest AI message
            ai_response = ""
            for message in reversed(result.get("messages", [])):
                if isinstance(message, dict):
                    ai_response = message.content
                    break
            
            return {
                "success": True,
                "response": ai_response,
                "state": result,
                "booking_data": result.get("booking_data", {}),
                "confirmation_code": result.get("confirmation_code"),
                "should_transfer": result.get("should_transfer", False),
                "intent": result.get("intent"),
                "current_step": result.get("current_step")
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm experiencing technical difficulties. Let me connect you with our staff.",
                "should_transfer": True
            }


