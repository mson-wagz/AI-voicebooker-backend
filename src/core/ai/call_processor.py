"""
AI Call Processor - Handles incoming calls and extracts booking metadata
Production-ready implementation with advanced NLP for booking extraction
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import re
import uuid
from dotenv import load_dotenv
from groq import Groq

from ..metadata.storage import CallMetadata, metadata_storage

logger = logging.getLogger(__name__)

class BookingDetails(BaseModel):
    """Model for extracted booking details"""
    restaurant_name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    party_size: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    special_requests: Optional[str] = None
    occasion: Optional[str] = None
    dietary_restrictions: Optional[str] = None
    preferred_table: Optional[str] = None
    high_chair_needed: Optional[bool] = None
    outdoor_seating: Optional[bool] = None

class CallProcessor:
    """Service for processing call transcripts and extracting booking information"""
    
    def __init__(self):
        # Use Groq API instead of Gemini/OpenRouter
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise ValueError("Missing Groq API key. Please set GROQ_API_KEY")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"
        
        # System prompt for booking extraction
        self.system_prompt = """
        You are a restaurant booking assistant AI. Your task is to extract booking details from customer calls.
        
        Extract the following information from the call transcript:
        - restaurant_name: Name of the restaurant
        - date: Booking date (format: YYYY-MM-DD)
        - time: Booking time (format: HH:MM)
        - party_size: Number of people (integer)
        - customer_name: Customer's name if mentioned
        - customer_phone: Customer's phone number
        - special_requests: Any special requests or dietary restrictions
        - occasion: Occasion (birthday, anniversary, business, etc.)
        - dietary_restrictions: Any dietary restrictions
        - preferred_table: Table preference (window, booth, etc.)
        - high_chair_needed: If high chair is needed (boolean)
        - outdoor_seating: Preference for outdoor seating (boolean)
        
        Return ONLY a valid JSON object. Do not include explanations or additional text.
        Example format:
        {
            "restaurant_name": "The Italian Restaurant",
            "date": "2024-03-21",
            "time": "19:00",
            "party_size": 4,
            "customer_name": "John",
            "customer_phone": "+1-123-456-7890",
            "special_requests": "Window seat preferred",
            "occasion": "birthday",
            "dietary_restrictions": "gluten-free",
            "preferred_table": "window",
            "high_chair_needed": false,
            "outdoor_seating": true
        }
        5. Be conservative - if uncertain, leave as null
        6. Pay attention to context and conversational cues
        
        Output must be valid JSON matching the schema.
        """
        
        # Note: Using direct message creation instead of ChatPromptTemplate
        # to avoid langchain.prompts dependency
    
    async def process_call(self, call_data: Dict[str, Any]) -> str:
        """Process incoming call and extract booking metadata"""
        try:
            # Generate unique call ID
            call_id = str(uuid.uuid4())
            
            # Extract basic call info
            restaurant_id = call_data.get('restaurant_id', 'unknown')
            customer_phone = self._normalize_phone(call_data.get('customer_phone', ''))
            
            # Get transcript
            transcript = call_data.get('transcript', '')
            if not transcript:
                logger.warning(f"No transcript available for call {call_id}")
                transcript = ""
            
            # Extract booking details using AI
            booking_details = await self._extract_booking_details(transcript)
            
            # Create metadata
            metadata = CallMetadata(
                call_id=call_id,
                restaurant_id=restaurant_id,
                customer_phone=customer_phone,
                customer_name=booking_details.customer_name,
                booking_request=booking_details.dict(),
                call_status=call_data.get('status', 'completed'),
                transcript=transcript,
                recording_url=call_data.get('recording_url'),
                priority=self._determine_priority(booking_details)
            )
            
            # Save metadata
            await metadata_storage.save_call_metadata(metadata)
            
            logger.info(f"Processed call {call_id} for restaurant {restaurant_id}")
            return call_id
            
        except Exception as e:
            logger.error(f"Error processing call: {e}")
            raise
    
    async def _extract_booking_details(self, transcript: str) -> BookingDetails:
        """Extract booking details from transcript using Groq API"""
        try:
            # Create prompt for Groq
            prompt = f"{self.system_prompt}\n\nCall transcript: {transcript}\n\nExtract booking details and return as valid JSON:"
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_completion_tokens=1024,
                top_p=1,
                stream=False
            )
            
            if response and response.choices:
                content = response.choices[0].message.content
                
                # Try to extract JSON from response
                try:
                    # Look for JSON in the response
                    if '```json' in content:
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        json_content = content[json_start:json_end].strip()
                    elif '{' in content:
                        # Find first JSON object
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        json_content = content[json_start:json_end]
                    else:
                        json_content = content
                    
                    booking_data = json.loads(json_content)
                    return BookingDetails(**booking_data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from Groq response: {e}")
                    logger.error(f"Raw response: {content}")
                    return BookingDetails()
            else:
                logger.error("No response from Groq API")
                return BookingDetails()
            
        except Exception as e:
            logger.error(f"Error extracting booking details: {e}")
            return BookingDetails()
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to +1-XXX-XXX-XXXX format"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle different lengths
        if len(digits) == 10:
            # US number without country code
            return f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # US number with country code
            return f"+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
        else:
            # Return as-is if can't normalize
            return phone
    
    def _determine_priority(self, booking: BookingDetails) -> str:
        """Determine processing priority based on booking details"""
        # High priority for:
        # - Same day bookings
        # - Large parties (8+ people)
        # - Special occasions
        
        if booking.date:
            try:
                booking_date = datetime.strptime(booking.date, '%Y-%m-%d').date()
                today = datetime.utcnow().date()
                
                if booking_date == today:
                    return "high"
                elif booking.party_size and booking.party_size >= 8:
                    return "high"
                elif booking.occasion and booking.occasion.lower() in ['birthday', 'anniversary']:
                    return "high"
                    
            except ValueError:
                pass
        
        return "normal"
    
    async def validate_booking(self, booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted booking details"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Required fields
        required_fields = ['date', 'time', 'party_size']
        for field in required_fields:
            if not booking_details.get(field):
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Validate date format
        if booking_details.get('date'):
            try:
                datetime.strptime(booking_details['date'], '%Y-%m-%d')
            except ValueError:
                validation_result["is_valid"] = False
                validation_result["errors"].append("Invalid date format")
        
        # Validate time format
        if booking_details.get('time'):
            try:
                datetime.strptime(booking_details['time'], '%H:%M')
            except ValueError:
                validation_result["is_valid"] = False
                validation_result["errors"].append("Invalid time format")
        
        # Validate party size
        if booking_details.get('party_size'):
            try:
                size = int(booking_details['party_size'])
                if size <= 0:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append("Party size must be positive")
                elif size > 20:
                    validation_result["warnings"].append("Large party size may require special handling")
            except ValueError:
                validation_result["is_valid"] = False
                validation_result["errors"].append("Invalid party size")
        
        return validation_result

# Global processor instance
call_processor: Optional[CallProcessor] = None

def get_call_processor() -> CallProcessor:
    """Get global call processor instance"""
    global call_processor
    if call_processor is None:
        call_processor = CallProcessor()
    return call_processor
