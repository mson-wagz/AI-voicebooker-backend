"""
Vapi API endpoints for call orchestration
"""
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from ..voice.voice_handler import voice_handler, CallRequest
# from ..voice.elevenlabs import ElevenLabsConfig, ElevenLabsManager, get_voice_recommendation
from ..database.connection import get_db
from ..ai.call_processor import get_call_processor
from ..metadata.storage import CallMetadata
from ..automation.browser_use import BrowserAutomation
# from prisma.models import Restaurant, CallRecord, Booking
# from prisma import Client as Any

# Configure logging
logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/v1/vapi", tags=["vapi"])

# Pydantic models
class OutboundCallRequest(BaseModel):
    restaurant_id: str
    customer_number: str
    assistant_id: str = None

class WebhookEvent(BaseModel):
    type: str

# Simple test endpoint
@router.get("/test")
async def test_vapi():
    """Test Vapi functionality"""
    return {"status": "working", "message": "Vapi router is accessible"}

# Pydantic models
class OutboundCallRequest(BaseModel):
    restaurant_id: str
    customer_number: str
    assistant_id: str = None

class WebhookEvent(BaseModel):
    type: str
    call: Dict[str, Any] = {}
    timestamp: str = None

class AssistantConfig(BaseModel):
    restaurant_id: str
    name: str = None
    welcome_message: str = None
    voice_provider: str = "elevenlabs"
    voice_id: str = "rachel"
    elevenlabs_settings: Optional[Dict[str, Any]] = None

# Endpoints

@router.post("/configure-inbound")
async def configure_inbound_calling():
    """Configure Vapi phone number for inbound calls"""
    try:
        return {
            "success": True,
            "message": "Inbound calling configured successfully",
            "status": "test_mode"
        }
        
    except Exception as e:
        logger.error(f"Failed to configure inbound calling: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure inbound calling: {str(e)}")

@router.get("/phone-numbers")
async def get_phone_numbers():
    """Get available phone numbers for debugging"""
    try:
        from ..voice.vapi_config import VapiConfig
        config = VapiConfig()
        phone_numbers = config.vapi.phone_numbers.list()
        return {
            "phone_numbers": [
                {
                    "id": pn.id,
                    "number": pn.number,
                    "name": pn.name,
                    "provider": pn.provider,
                    "capabilities": getattr(pn, 'capabilities', 'unknown')
                }
                for pn in phone_numbers
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/calls/initiate")
async def initiate_outbound_call(
    request: OutboundCallRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    try:
        restaurant = await db.restaurant.find_unique(where={"id": request.restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        call_request = CallRequest(
            customer_number=request.customer_number,
            restaurant_id=request.restaurant_id,
            assistant_id=request.assistant_id
        )
        
        result = await voice_handler.initiate_call(call_request)
        
        background_tasks.add_task(
            create_call_record_task,
            db,
            result["call_id"],
            request.customer_number,
            request.restaurant_id
        )
        
        return {
            "success": True,
            "call_id": result["call_id"],
            "status": result["status"],
            "message": "Call initiated successfully"
        }
        
    except HTTPException:
        raise  # ← Let FastAPI handle 404, 422, etc. naturally
    except Exception as e:
        logger.error(f"Failed to initiate call. Error type: {type(e).__name__}, Message: {str(e)}")
        logger.error(f"Full error details: {repr(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)} (Type: {type(e).__name__})")

        

@router.post("/process-call")
async def process_call_for_booking(
    call_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Process call data for automated booking
    This endpoint receives call data and processes it for booking automation
    """
    try:
        # Get call processor
        processor = get_call_processor()
        
        # Process call and extract booking metadata
        call_id = await processor.process_call(call_data)
        
        return {
            "success": True,
            "call_id": call_id,
            "message": "Call processed successfully for booking automation",
            "status": "pending_automation"
        }
        
    except Exception as e:
        logger.error(f"Failed to process call for booking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process call: {str(e)}")

@router.post("/webhooks/vapi")
@router.options("/webhooks/vapi")
async def handle_vapi_webhook(
    webhook_data: Dict[str, Any] = None,
    background_tasks: BackgroundTasks = None,
    db = Depends(get_db)
):
    """
    Handle Vapi webhook events
    """
    # Handle CORS preflight
    if webhook_data is None:
        return JSONResponse(
            content={"status": "CORS preflight handled"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
    
    logger.info(f"🔔 === VAPI WEBHOOK RECEIVED ===")
    logger.info(f"📦 Raw payload type: {type(webhook_data)}")
    logger.info(f"📦 Raw payload keys: {list(webhook_data.keys())}")
    
    try:
        # Handle if webhook_data is a string (JSON)
        if isinstance(webhook_data, str):
            import json
            webhook_data = json.loads(webhook_data)
        
        # Vapi wraps real events under a "message" key
        message = webhook_data.get("message", webhook_data)
        
        # Ensure message is a dict
        if isinstance(message, str):
            import json
            message = json.loads(message)
            
        event_type = message.get("type")
        call_data = message.get("call", {})

        logger.info(f"📞 Event Type: {event_type}")
        logger.info(f"📞 Call ID: {call_data.get('id')}")
        logger.info(f"📞 Call Type: {call_data.get('type')}")

        # Inbound call — return full transient assistant config so backend controls everything
        if event_type == "assistant-request":
            # Create dynamic system prompt based on context
            system_prompt = """You are RestoVoice, an AI voice reservation agent. You're currently processing a restaurant booking request.

Your personality:
- Confident and professional
- Think out loud when processing
- Sound like you're actively working
- Use natural conversation fillers when thinking

Example responses:
- "Alright, let me check availability for you..."
- "Hmm, that time looks busy, let me try a different slot..."
- "Got it! I found a perfect table for you."
- "Your reservation is confirmed. You're all set."

Always speak clearly and confirm details before booking."""
            
            # Add thinking prompts for complex bookings
            if call_data.get("type") == "webCall":
                system_prompt += "\n\nThis is a web call, so take your time to think through the booking process out loud."
            
            call_type = call_data.get("type", "webCall")
            logger.info(f"📞 assistant-request ({call_type}) — returning transient assistant config")
            return {
                "assistant": {
                    "name": "RestoVoice Reservation Agent",
                    "firstMessage": "Hi! Thank you for calling RestoVoice. I'm here to help you make a restaurant reservation. How can I help you today?",
                    "firstMessageMode": "assistant-speaks-first",
                    "model": {
                        "provider": "openai",
                        "model": "gpt-4",
                        "systemPrompt": system_prompt,
                        "temperature": 0.1
                    },
                    "voice": {
                        "provider": "vapi",
                        "voiceId": "Clara"
                    },
                    "recordingEnabled": True,
                    "endCallFunctionEnabled": True,
                    "serverUrl": os.getenv("WEBHOOK_URL", "http://localhost:8000/v1/vapi/webhooks/vapi"),
                    "functions": [
                        {
                            "name": "check_availability",
                            "description": "Check restaurant availability for a specific date, time, and party size",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "restaurant_name": {
                                        "type": "string",
                                        "description": "Name or type of restaurant (e.g., 'Italian restaurant', 'sushi', 'steakhouse')"
                                    },
                                    "location": {
                                        "type": "string", 
                                        "description": "City or area (e.g., 'New York', 'Manhattan', 'Brooklyn')"
                                    },
                                    "date": {
                                        "type": "string",
                                        "description": "Date for reservation (YYYY-MM-DD format)"
                                    },
                                    "time": {
                                        "type": "string",
                                        "description": "Preferred time (e.g., '7:00 PM', '19:00')"
                                    },
                                    "party_size": {
                                        "type": "integer",
                                        "description": "Number of people (1-10)"
                                    }
                                },
                                "required": ["restaurant_name", "location", "date", "time", "party_size"]
                            }
                        },
                        {
                            "name": "book_reservation",
                            "description": "Book a confirmed reservation at a restaurant",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "restaurant_name": {
                                        "type": "string",
                                        "description": "Name of restaurant to book"
                                    },
                                    "location": {
                                        "type": "string",
                                        "description": "Restaurant location"
                                    },
                                    "date": {
                                        "type": "string",
                                        "description": "Date for reservation (YYYY-MM-DD format)"
                                    },
                                    "time": {
                                        "type": "string",
                                        "description": "Confirmed time for reservation"
                                    },
                                    "party_size": {
                                        "type": "integer",
                                        "description": "Number of people"
                                    },
                                    "customer_name": {
                                        "type": "string",
                                        "description": "Customer's full name"
                                    },
                                    "customer_phone": {
                                        "type": "string",
                                        "description": "Customer's phone number"
                                    },
                                    "customer_email": {
                                        "type": "string",
                                        "description": "Customer's email (optional)"
                                    }
                                },
                                "required": ["restaurant_name", "location", "date", "time", "party_size", "customer_name", "customer_phone"]
                            }
                        }
                    ]
                }
            }

        # Handle function calls from Vapi assistant
        if event_type == "function-call":
            function_name = message.get("function", {}).get("name")
            function_args = message.get("function", {}).get("arguments", {})
            call_id = call_data.get("id")
            
            logger.info(f"🔧 Function call: {function_name} with args: {function_args}")
            
            try:
                if function_name == "check_availability":
                    result = await handle_check_availability(function_args)
                    return {
                        "results": [
                            {
                                "toolCallId": message.get("toolCallId"),
                                "result": result
                            }
                        ]
                    }
                
                elif function_name == "book_reservation":
                    result = await handle_book_reservation(function_args, call_id)
                    return {
                        "results": [
                            {
                                "toolCallId": message.get("toolCallId"),
                                "result": result
                            }
                        ]
                    }
                
                else:
                    logger.warning(f"Unknown function: {function_name}")
                    return {
                        "results": [
                            {
                                "toolCallId": message.get("toolCallId"),
                                "result": "Sorry, I don't know how to do that."
                            }
                        ]
                    }
                    
            except Exception as e:
                logger.error(f"Function call error: {e}")
                return {
                    "results": [
                        {
                            "toolCallId": message.get("toolCallId"),
                            "result": f"Sorry, something went wrong: {str(e)}"
                        }
                    ]
                }

        # Process call for booking automation when call ends
        if event_type in ("call.end", "end-of-call-report") and call_data.get("status") == "completed":
            background_tasks.add_task(process_completed_call_for_booking, call_data)

        # Handle other webhook events
        if event_type in ("call.started", "call-started"):
            background_tasks.add_task(handle_call_started_task, db, call_data)
        elif event_type in ("call.ended", "call-ended"):
            background_tasks.add_task(handle_call_ended_task, db, call_data)
        elif event_type == "transcript":
            background_tasks.add_task(handle_transcript_task, db, call_data)

        return JSONResponse(
            content={"status": "webhook received"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )

    except Exception as e:
        logger.error(f"❌ VAPI WEBHOOK ERROR: {str(e)}")
        logger.error(f"❌ VAPI WEBHOOK ERROR DETAILS: {repr(e)}")
        import traceback
        logger.error(f"❌ VAPI WEBHOOK TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

@router.post("/assistants/create")
async def create_assistant(
    config: AssistantConfig,
    db: Any = Depends(get_db)
):
    """
    Create Vapi assistant for restaurant with Eleven Labs voice
    """
    try:
        # Verify restaurant exists
        restaurant = await db.restaurant.find_unique(where={"id": config.restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Prepare Eleven Labs settings
        elevenlabs_settings = config.elevenlabs_settings or {
            "model_id": os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True
        }
        
        # Create assistant with Eleven Labs voice
        assistant_request = {
            "name": config.name or f"{restaurant.name} Reservation Agent",
            "first_message": config.welcome_message or f"Hi! My name is Alex, I'm here to help you with your booking at {restaurant.name}. How may I help you today?",
            "model": {
                "provider": "azure",
                "model": "gpt-4",
                "azure_region": os.getenv("AZURE_REGION", "eastus"),
                "azure_resource_id": os.getenv("AZURE_RESOURCE_ID")
            },
            "voice": {
                "provider": config.voice_provider,
                "voice_id": config.voice_id,
                "elevenlabs_settings": elevenlabs_settings
            },
            "first_message_mode": "assistant-speaks-first",
            "recording_enabled": True,
            "transcription_enabled": True
        }
        
        # Create assistant via Vapi
        vapi_client = voice_handler.vapi
        assistant = vapi_client.assistants.create(**assistant_request)
        
        # Update restaurant with assistant ID
        await db.restaurant.update(
            where={"id": config.restaurant_id},
            data={"vapiAssistantId": assistant.id}
        )
        
        return {
            "success": True,
            "assistant_id": assistant.id,
            "restaurant_id": config.restaurant_id,
            "voice_provider": config.voice_provider,
            "voice_id": config.voice_id,
            "message": "Assistant created successfully with Eleven Labs voice"
        }
        
    except Exception as e:
        logger.error(f"Failed to create assistant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create assistant: {str(e)}")

@router.get("/calls/{call_id}")
async def get_call_details(call_id: str, db: Any = Depends(get_db)):
    
    """
    Get call details by ID
    """
    try:
        call_record = db.callrecord.find_unique(where={"call_id": call_id})
        if not call_record:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return {
            "call_id": call_record.call_id,
            "restaurant_id": call_record.restaurant_id,
            "customer_phone": call_record.customer_phone,
            "status": call_record.status,
            "duration": call_record.duration,
            "transcript": call_record.transcript,
            "audio_url": call_record.audio_url,
            "booking_id": call_record.booking_id,
            "created_at": call_record.created_at,
            "updated_at": call_record.updated_at
        }
        
    except Exception as e:
        logger.error(f"Failed to get call details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get call details: {str(e)}")

@router.get("/restaurants/{restaurant_id}/calls")
async def get_restaurant_calls(
    restaurant_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Any = Depends(get_db)
):
    """
    Get all calls for a restaurant
    """
    try:
        # Verify restaurant exists
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        calls = db.query(CallRecord)\
            .filter(CallRecord.restaurant_id == restaurant_id)\
            .order_by(CallRecord.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return {
            "restaurant_id": restaurant_id,
            "total_calls": len(calls),
            "calls": [
                {
                    "call_id": call.call_id,
                    "customer_phone": call.customer_phone,
                    "status": call.status,
                    "duration": call.duration,
                    "created_at": call.created_at,
                    "booking_id": call.booking_id
                }
                for call in calls
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get restaurant calls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get restaurant calls: {str(e)}")

@router.get("/voices/elevenlabs")
async def get_elevenlabs_voices():
    """
    Get available Eleven Labs voices for restaurant assistants
    """
    try:
        voices = ElevenLabsConfig.list_available_voices()
        return {
            "provider": "elevenlabs",
            "voices": voices,
            "default_voice": ElevenLabsConfig.get_default_voice(),
            "default_settings": ElevenLabsConfig.get_default_settings().dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Eleven Labs voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")

@router.get("/voices/recommendations/{restaurant_type}")
async def get_voice_recommendations(restaurant_type: str):
    """
    Get voice recommendation based on restaurant type
    """
    try:
        recommended_voice = get_voice_recommendation(restaurant_type)
        voice_info = ElevenLabsConfig.get_voice_info(recommended_voice)
        
        return {
            "restaurant_type": restaurant_type,
            "recommended_voice": recommended_voice,
            "voice_info": voice_info.dict() if voice_info else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get voice recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendation: {str(e)}")

@router.get("/restaurants/{restaurant_id}/assistants")
async def get_restaurant_assistants(restaurant_id: str, db: Any = Depends(get_db)):
    """
    Get Vapi assistant information for restaurant
    """
    try:
        restaurant = db.restaurant.find_unique(where={"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        return {
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant.name,
            "vapi_assistant_id": restaurant.vapi_assistant_id,
            "has_assistant": restaurant.vapi_assistant_id is not None
        }
        
    except Exception as e:
        logger.error(f"Failed to get restaurant assistants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get restaurant assistants: {str(e)}")

# Background task functions
async def create_call_record_task(db, call_id: str, customer_phone: str, restaurant_id: str):
    """Create call record in background"""
    try:
        await db.callrecord.create(
            data={
                "callId": call_id,
                "customerPhone": customer_phone,
                "restaurantId": restaurant_id,
                "status": "initiated"
            }
        )
    except Exception as e:
        logger.error(f"Failed to create call record: {str(e)}")

async def handle_call_started_task(db: Any, call_data: Dict[str, Any]):
    """Handle call started event in background"""
    try:
        call_id = call_data.get("id")
        logger.info(f"Call started: {call_id}")
        # Update call record status
        await db.callrecord.update(
            where={"callId": call_id},
            data={"status": "started", "startedAt": datetime.utcnow()}
        )
    except Exception as e:
        logger.error(f"Failed to handle call started: {str(e)}")

# Function handlers for Vapi assistant
async def handle_check_availability(args: Dict[str, Any]) -> str:
    """Handle availability check function call"""
    try:
        logger.info(f"🔍 Checking availability with args: {args}")
        
        # Initialize browser automation
        automation = BrowserAutomation()
        await automation.initialize()
        
        # Check availability
        result = await automation.check_availability(
            restaurant_name=args.get("restaurant_name", ""),
            location=args.get("location", ""),
            requested_date=args.get("date", ""),
            requested_time=args.get("time", ""),
            party_size=args.get("party_size", 2)
        )
        
        await automation.cleanup()
        
        # Return natural language response for Vapi
        message = result.get("message", "I had trouble checking availability. Please try again.")
        
        logger.info(f"Availability check result: {message}")
        return message
        
    except Exception as e:
        logger.error(f"Availability check failed: {str(e)}")
        return f"Sorry, I had trouble checking availability: {str(e)}"

async def handle_book_reservation(args: Dict[str, Any], call_id: str) -> str:
    """Handle reservation booking function call"""
    try:
        logger.info(f"Booking reservation with args: {args}")
        
        # Create booking metadata
        booking_metadata = CallMetadata(
            call_id=call_id,
            restaurant_id=args.get("restaurant_name", ""),
            customer_phone=args.get("customer_phone", ""),
            booking_request=args,
            call_status="processing"
        )
        
        # Initialize browser automation
        automation = BrowserAutomation()
        await automation.initialize()
        
        # Process booking
        booking_result = await automation.process_booking(booking_metadata)
        
        await automation.cleanup()
        
        if booking_result.success:
            message = f"Perfect! Your reservation is confirmed. Reference: {booking_result.booking_reference or 'Confirmed'}. You're all set!"
        else:
            message = f"Sorry, I couldn't complete the booking: {booking_result.error_message or 'Unknown error'}"
        
        logger.info(f"Booking result: {message}")
        return message
        
    except Exception as e:
        logger.error(f"Booking failed: {str(e)}")
        return f"Sorry, I had trouble making the reservation: {str(e)}"

async def handle_call_ended_task(db: Any, call_data: Dict[str, Any]):
    """Handle call ended event in background"""
    try:
        call_id = call_data.get("id")
        status = call_data.get("status")
        duration = call_data.get("duration", 0)
        
        await db.callrecord.update(
            where={"callId": call_id},
            data={
                "status": status,
                "duration": duration
            }
        )
    except Exception as e:
        logger.error(f"Failed to handle call ended: {str(e)}")

async def handle_transcript_task(db: Any, call_data: Dict[str, Any]):
    """Handle transcript creation in background"""
    try:
        call_id = call_data.get("id")
        transcript = call_data.get("transcript", "")
        
        await db.callrecord.update(
            where={"callId": call_id},
            data={
                "transcript": transcript
            }
        )
    except Exception as e:
        logger.error(f"Failed to handle transcript: {str(e)}")

async def process_completed_call_for_booking(call_data: Dict[str, Any]):
    """Process completed call for booking automation"""
    try:
        # Get call processor
        processor = get_call_processor()
        
        # Prepare call data for processing
        processed_data = {
            "restaurant_id": call_data.get("restaurantId", "unknown"),
            "customer_phone": call_data.get("customer", {}).get("number", ""),
            "transcript": call_data.get("transcript", ""),
            "status": call_data.get("status", "completed"),
            "recording_url": call_data.get("recordingUrl", "")
        }
        
        # Process call and extract booking details
        call_id = await processor.process_call(processed_data)
        logger.info(f"Processed completed call {call_id} for booking automation")
        
        # Trigger browser automation if booking details are complete
        await trigger_browser_automation(call_id)
        
    except Exception as e:
        logger.error(f"Failed to process completed call for booking: {str(e)}")

async def trigger_browser_automation(call_id: str):
    """Trigger browser automation for a processed call with status updates"""
    try:
        from ..automation.browser_use import get_booking_processor
        from ..metadata.storage import metadata_storage
        
        # Get the call metadata
        call_metadata = await metadata_storage.get_call_metadata(call_id)
        if not call_metadata:
            logger.warning(f"[BOOKING ENGINE] No metadata found for call {call_id}")
            return
        
        # Validate booking details
        processor = get_call_processor()
        validation = await processor.validate_booking(call_metadata.booking_request)
        
        if validation["is_valid"]:
            logger.info(f"[BOOKING ENGINE] Starting automation for call {call_id}")
            logger.info(f"[AGENT] Executing booking for {call_metadata.booking_request.get('restaurant_name', 'Unknown')}")
            
            # The booking processor will pick this up in its processing loop
            logger.info(f"[SUCCESS] Booking automation triggered: {call_metadata.booking_request}")
        else:
            logger.warning(f"[BOOKING ENGINE] Validation failed: {validation['errors']}")
            
    except Exception as e:
        logger.error(f"[BOOKING ENGINE] Automation failed: {str(e)}")
