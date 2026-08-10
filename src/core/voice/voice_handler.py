# Main voice call handling and processing logic
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from vapi import Vapi
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

from .elevenlabs import ElevenLabsConfig, ElevenLabsManager, create_restaurant_voice_config

class VapiConfig:
    """Configuration for Vapi AI integration"""
    
    def __init__(self):
        self.api_key = os.getenv("VAPI_API_KEY")
        self.phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
    
    def get_client(self) -> Vapi:
        """Get configured Vapi client"""
        if not self.api_key:
            logger.warning("VAPI_API_KEY not set, Vapi functionality will be disabled")
            return None
        return Vapi(token=self.api_key)

class CallRequest(BaseModel):
    """Model for incoming call requests"""
    customer_number: str
    restaurant_id: str
    assistant_id: Optional[str] = None

class VoiceHandler:
    """Main voice call handler with Vapi integration"""
    
    def __init__(self):
        self.config = VapiConfig()
        self.vapi = self.config.get_client()
        if not self.vapi:
            logger.warning("VoiceHandler initialized without Vapi client - voice features will be limited")
    
    async def create_assistant(self, restaurant_id: str, db_session=None, voice_id: Optional[str] = None) -> str:
        """Create or get Vapi assistant for restaurant with Eleven Labs voice"""
        try:
            # Import here to avoid circular imports
            from ..database.connection import prisma
            
            # Get restaurant from database
            if db_session:
                restaurant = await db_session.restaurant.find_unique(where={"id": restaurant_id})
                if not restaurant:
                    raise Exception(f"Restaurant {restaurant_id} not found")
                restaurant_name = restaurant.name
            else:
                # Fallback for testing without database
                restaurant_name = "Restaurant"
            
            logger.info(f"🏪 Restaurant Name: {restaurant_name}")
            
            # Get Eleven Labs voice configuration
            voice_config = create_restaurant_voice_config(
                restaurant_name=restaurant_name,
                voice_id=voice_id
            )
            
            # Check if assistant already exists for this restaurant
            assistant_id = None  # For now, always create new assistant
            logger.info(f"🔍 Checking for existing assistant...")
            
            if assistant_id:
                logger.info(f"✅ Using existing assistant: {assistant_id}")
                return assistant_id
            
            # Create new assistant
            logger.info(f"🔧 Creating new assistant...")
            
            assistant_request = {
                "name": f"{restaurant_name} Reservation Agent",
                "first_message": f"Hi! My name is Alex, I'm here to help you with your booking at {restaurant_name}. How may I help you today?",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4"
                },
                "voice": {
                    "provider": "vapi",
                    "voice_id": "Clara"
                },
                "first_message_mode": "assistant-speaks-first"
            }
            
            logger.info(f"📤 Assistant Request: {assistant_request}")
            
            assistant = self.vapi.assistants.create(**assistant_request)
            assistant_id = assistant.id
            
            logger.info(f"✅ Assistant created successfully: {assistant_id}")
            logger.info(f"🤖 === CREATE ASSISTANT COMPLETED ===")
            
            # Update restaurant with assistant ID if database session is available
            if db_session and restaurant:
                await db_session.restaurant.update(
                    where={"id": restaurant_id},
                    data={"vapiAssistantId": assistant.id}
                )
            
            return assistant.id
            
        except Exception as e:
            raise Exception(f"Failed to create assistant: {str(e)}")
    
    async def initiate_call(self, request: CallRequest) -> Dict[str, Any]:
        """Initiate outbound call for restaurant booking"""
        try:
            # Get or create assistant for restaurant
            assistant_id = request.assistant_id
            if not assistant_id:
                assistant_id = await self.create_assistant(request.restaurant_id)
            
            # Create call
            call_request = {
                "phone_number_id": self.config.phone_number_id,
                "customer": {"number": request.customer_number},
                "assistant_id": assistant_id
            }
            
            call = self.vapi.calls.create(**call_request)
            
            return {
                "call_id": call.id,
                "status": call.status,
                "assistant_id": assistant_id,
                "restaurant_id": request.restaurant_id
            }
            
        except Exception as e:
            import traceback
            logger.error(f"VoiceHandler Error - Type: {type(e).__name__}, Message: {str(e)}")
            logger.error(f"Full error details: {repr(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to initiate call: {str(e)} (Type: {type(e).__name__})")
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Vapi webhook events"""
        try:
            message = webhook_data.get("message", webhook_data)
            event_type = message.get("type", webhook_data.get("type"))
            call_data = message.get("call", webhook_data.get("call", {}))
            
            # Log everything for debugging
            logger.info(f"🔔 WEBHOOK RECEIVED: {event_type}")
            logger.info(f"📊 FULL WEBHOOK DATA: {webhook_data}")
            logger.info(f"📞 CALL DATA: {call_data}")
            
            if event_type == "call.ended":
                logger.info(f"📞 CALL ENDED: {call_data.get('id')}")
                await self._handle_call_ended(call_data)
            elif event_type == "call.started":
                logger.info(f"📞 CALL STARTED: {call_data.get('id')}")
                await self._handle_call_started(call_data)
            elif event_type == "transcript.created":
                logger.info(f"📝 TRANSCRIPT: {call_data.get('id')}")
                await self._handle_transcript(call_data)
            elif event_type == "function-call" or event_type == "function_call":
                logger.info(f"🔧 FUNCTION CALL: {call_data.get('id')}")
                return await self._handle_function_call(call_data)
            elif event_type == "assistant-request" or event_type == "call.incoming":
                logger.info(f"📞 INCOMING CALL / ASSISTANT REQUEST: {call_data.get('id')}")
                return await self._handle_assistant_request(call_data)
            else:
                logger.warning(f"❓ UNKNOWN EVENT TYPE: {event_type}")
            
            return {"status": "processed", "event_type": event_type}
            
        except Exception as e:
            logger.error(f"❌ WEBHOOK ERROR: {str(e)}")
            logger.error(f"❌ WEBHOOK ERROR DETAILS: {repr(e)}")
            import traceback
            logger.error(f"❌ WEBHOOK TRACEBACK: {traceback.format_exc()}")
            raise Exception(f"Failed to handle webhook: {str(e)}")
    
    async def _handle_call_ended(self, call_data: Dict[str, Any], db_session=None):
        """Handle call ended event"""
        call_id = call_data.get("id")
        status = call_data.get("status")
        duration = call_data.get("duration", 0)
        
        if db_session:
            try:
                # Update call record
                await db_session.callrecord.update(
                    where={"callId": call_id},
                    data={
                        "status": status,
                        "duration": duration
                    }
                )
                print(f"Call {call_id} ended with status {status} and duration {duration}")
            except Exception as e:
                print(f"Failed to update call record: {str(e)}")
        else:
            print(f"Call {call_id} ended with status {status} and duration {duration}")
    
    async def _handle_call_started(self, call_data: Dict[str, Any], db_session=None):
        """Handle call started event"""
        call_id = call_data.get("id")
        customer_number = call_data.get("customer", {}).get("number")
        assistant_id = call_data.get("assistant", {}).get("id")
        
        if db_session:
            try:
                # Create call record
                await db_session.callrecord.create(
                    data={
                        "callId": call_id,
                        "customerPhone": customer_number,
                        "status": "started",
                        "assistantId": assistant_id
                    }
                )
                print(f"Call {call_id} started with customer {customer_number}")
            except Exception as e:
                print(f"Failed to create call record: {str(e)}")
        else:
            print(f"Call {call_id} started with customer {customer_number}")
    
    async def _handle_transcript(self, call_data: Dict[str, Any], db_session=None):
        """Handle transcript creation"""
        call_id = call_data.get("id")
        transcript = call_data.get("transcript", "")
        
        if db_session:
            try:
                # Update transcript
                await db_session.callrecord.update(
                    where={"callId": call_id},
                    data={
                        "transcript": transcript
                    }
                )
                print(f"Transcript updated for call {call_id}")
            except Exception as e:
                print(f"Failed to update transcript: {str(e)}")
        else:
            print(f"Transcript received for call {call_id}: {transcript[:100]}...")
    
    async def _handle_function_call(self, call_data: Dict[str, Any]):
        """Handle AI function calls during conversation"""
        function_call = call_data.get("functionCall")
        if not function_call:
            return
        
        function_name = function_call.get("name")
        parameters = function_call.get("parameters", {})
        
        # Route to appropriate function handler
        if function_name == "check_availability":
            return await self._handle_check_availability(parameters)
        elif function_name == "create_booking":
            return await self._handle_create_booking(parameters)
        elif function_name == "modify_booking":
            return await self._handle_modify_booking(parameters)
        elif function_name == "cancel_booking":
            return await self._handle_cancel_booking(parameters)
        elif function_name == "automate_booking":
            return await self._handle_automate_booking(parameters)
        elif function_name == "check_booking_status":
            return await self._handle_check_booking_status(parameters)
        elif function_name == "get_supported_restaurants":
            return await self._handle_get_supported_restaurants(parameters)
    
    async def _handle_check_availability(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle availability check function call"""
        from src.core.ai.availability import check_availability, AvailabilityRequest
        
        request = AvailabilityRequest(
            restaurant_id=parameters.get("restaurant_id"),
            booking_timestamp=parameters.get("booking_timestamp"),
            party_size=parameters.get("party_size")
        )
        
        result = await check_availability(request)
        return result.dict()
    
    async def _handle_create_booking(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle booking creation function call"""
        from src.core.reservations.booking_manager import create_booking
        
        result = await create_booking(
            restaurant_id=parameters.get("restaurant_id"),
            customer_name=parameters.get("customer_name"),
            customer_phone=parameters.get("customer_phone"),
            party_size=parameters.get("party_size"),
            booking_time=parameters.get("booking_time")
        )
        
        return result.dict()
    
    async def _handle_modify_booking(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle booking modification function call"""
        from src.core.reservations.booking_manager import modify_booking
        
        result = await modify_booking(
            booking_id=parameters.get("booking_id"),
            modifications=parameters.get("modifications", {})
        )
        
        return result.dict()
    
    async def _handle_cancel_booking(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle booking cancellation function call"""
        from src.core.reservations.booking_manager import cancel_booking
        
        result = await cancel_booking(
            booking_id=parameters.get("booking_id"),
            reason=parameters.get("reason", "Customer cancellation")
        )
        
        return result.dict()
    
    async def _handle_automate_booking(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle browser automation booking function call"""
        from .vapi_browser_tool import handle_automate_booking
        
        result = await handle_automate_booking(parameters)
        return result
    
    async def _handle_check_booking_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle booking status check function call"""
        from .vapi_browser_tool import handle_check_booking_status
        
        result = await handle_check_booking_status(parameters)
        return result
    
    async def _handle_get_supported_restaurants(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get supported restaurants function call"""
        from .vapi_browser_tool import handle_get_supported_restaurants
        
        result = await handle_get_supported_restaurants(parameters)
        return result
    
    async def create_assistant(self, restaurant_name: str = "default"):
        """Create or get Vapi assistant for restaurant"""
        try:
            logger.info(f"🤖 === CREATE ASSISTANT STARTED ===")
            logger.info(f"🏪 Restaurant Name: {restaurant_name}")
            
            assistant_request = {
                "name": f"{restaurant_name} Reservation Agent",
                "firstMessage": f"Hi! My name is Alex, I'm here to help you with your booking at {restaurant_name}. How may I help you today?",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4"
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "rachel"
                }
            }
            
            logger.info(f"📤 Assistant Request: {assistant_request}")
            
            assistant = self.vapi.assistants.create(**assistant_request)
            assistant_id = assistant.id
            
            logger.info(f"✅ Assistant created successfully: {assistant_id}")
            logger.info(f"🤖 === CREATE ASSISTANT COMPLETED ===")
            
            return assistant_id
            
        except Exception as e:
            logger.error(f"❌ CREATE ASSISTANT ERROR: {str(e)}")
            logger.error(f"❌ CREATE ASSISTANT DETAILS: {repr(e)}")
            import traceback
            logger.error(f"❌ CREATE ASSISTANT TRACEBACK: {traceback.format_exc()}")
            raise Exception(f"Failed to create assistant: {str(e)}")

    async def _handle_assistant_request(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming call from customer / assistant-request"""
        call_id = call_data.get("id")
        customer_number = call_data.get("customer", {}).get("number")
        phone_number_id = call_data.get("phoneNumberId")
        
        logger.info(f"📞 === ASSISTANT REQUEST HANDLER STARTED ===")
        logger.info(f"🆔 Call ID: {call_id}")
        logger.info(f"📱 Customer Number: {customer_number}")
        logger.info(f"📞 Phone Number ID: {phone_number_id}")
        
        try:
            # Create or get default assistant for incoming calls
            logger.info(f"🤖 Creating/getting assistant for inbound call...")
            assistant_id = await self.create_assistant("default")
            logger.info(f"✅ Assistant ID: {assistant_id}")
            
            # Store call record
            try:
                from ..database.connection import prisma
                call_record = await prisma.callrecord.create({
                    "callId": call_id,
                    "customerNumber": customer_number,
                    "phoneNumberId": phone_number_id,
                    "assistantId": assistant_id,
                    "status": "incoming",
                    "direction": "inbound",
                    "createdAt": call_data.get("createdAt", datetime.utcnow())
                })
                logger.info(f"✅ Call record created")
            except Exception as db_error:
                logger.error(f"❌ Failed to create call record: {db_error}")
            
            logger.info(f"📞 === ASSISTANT REQUEST HANDLER COMPLETED ===")
            # MUST RETURN ASSISTANT ID TO VAPI
            return {"assistantId": assistant_id}
            
        except Exception as e:
            logger.error(f"❌ ASSISTANT REQUEST HANDLER ERROR: {str(e)}")
            import traceback
            logger.error(f"❌ ASSISTANT REQUEST TRACEBACK: {traceback.format_exc()}")
            return {}

# Global voice handler instance
voice_handler = VoiceHandler()
