"""
Browser Automation Tool for Vapi Integration
Provides automated restaurant booking capabilities through browser automation
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

from ..automation.browser_use import BrowserAutomation, BookingResult, get_booking_processor
from ..metadata.storage import CallMetadata, metadata_storage

logger = logging.getLogger(__name__)

class VapiBrowserAutomationTool:
    """Browser automation tool that can be called from Vapi"""
    
    def __init__(self):
        self.browser_automation = BrowserAutomation()
        self.booking_processor = get_booking_processor()
    
    async def automate_booking(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automate restaurant booking using browser automation
        
        Parameters:
        - restaurant_id: ID of the restaurant
        - customer_name: Customer's full name
        - customer_phone: Customer's phone number
        - booking_date: Date for booking (YYYY-MM-DD format)
        - booking_time: Time for booking (HH:MM format)
        - party_size: Number of people
        - special_requests: Any special requests (optional)
        """
        try:
            logger.info(f"[BROWSER TOOL] Starting automated booking for restaurant: {parameters.get('restaurant_id')}")
            
            # Validate required parameters
            required_params = ['restaurant_id', 'customer_name', 'customer_phone', 'booking_date', 'booking_time', 'party_size']
            missing_params = [param for param in required_params if not parameters.get(param)]
            
            if missing_params:
                return {
                    "success": False,
                    "error": f"Missing required parameters: {', '.join(missing_params)}",
                    "error_code": "MISSING_PARAMETERS"
                }
            
            # Create call metadata for the booking processor
            call_metadata = CallMetadata(
                call_id=f"vapi_browser_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                restaurant_id=parameters['restaurant_id'],
                customer_phone=parameters['customer_phone'],
                booking_request={
                    'date': parameters['booking_date'],
                    'time': parameters['booking_time'],
                    'party_size': parameters['party_size'],
                    'customer_name': parameters['customer_name'],
                    'customer_phone': parameters['customer_phone'],
                    'special_requests': parameters.get('special_requests', ''),
                    'source': 'vapi_browser_automation'
                },
                created_at=datetime.utcnow()
            )
            
            # Store the call metadata
            await metadata_storage.store_call_metadata(call_metadata)
            
            # ✅ ASYNC FIX: Start booking in background and return immediately
            logger.info(f"[BROWSER TOOL] Starting background booking process...")
            
            # Start the booking process in the background
            import asyncio
            background_task = asyncio.create_task(self._process_booking_background(call_metadata))
            
            # Return immediate response with call_id for tracking
            return {
                "success": True,
                "message": f"🍽️ **Booking Started Successfully!**\n\nI've started the automated booking process for {parameters['customer_name']} at {parameters['restaurant_id']}.\n\n📅 **Details:**\n• Date: {parameters['booking_date']}\n• Time: {parameters['booking_time']}\n• Party Size: {parameters['party_size']}\n\n🔍 **Call ID:** {call_metadata.call_id}\n\nThe booking is now being processed in the background. You can check the status using the call ID above. You'll receive a confirmation once the booking is complete.",
                "call_id": call_metadata.call_id,
                "status": "processing",
                "estimated_time": "30-60 seconds",
                "next_step": "Use check_booking_status function to track progress"
            }
                
        except Exception as e:
            logger.error(f"[BROWSER TOOL] Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error during booking automation: {str(e)}",
                "error_code": "UNEXPECTED_ERROR"
            }
    
    async def _process_booking_background(self, call_metadata: CallMetadata):
        """Process booking in background without blocking the main call"""
        try:
            logger.info(f"[BACKGROUND] Processing booking for call {call_metadata.call_id}")
            
            # Move to processing status
            await metadata_storage.move_to_processing(call_metadata.call_id)
            
            # Get restaurant configuration
            restaurant_config = self.browser_automation._get_restaurant_config(call_metadata.restaurant_id)
            if not restaurant_config:
                logger.error(f"[BACKGROUND] No configuration found for restaurant {call_metadata.restaurant_id}")
                await metadata_storage.move_to_failed(
                    call_metadata.call_id,
                    f"No configuration found for restaurant {call_metadata.restaurant_id}"
                )
                return
            
            # Initialize browser if needed
            if not self.browser_automation.is_initialized:
                await self.browser_automation.initialize()
            
            # Create and execute booking agent
            agent = await self.browser_automation._create_booking_agent(call_metadata, restaurant_config)
            result = await self.browser_automation._execute_booking(agent, call_metadata, restaurant_config)
            
            # Store result
            if result.success:
                await metadata_storage.move_to_completed(call_metadata.call_id, result.dict())
                logger.info(f"[BACKGROUND] Booking successful: {result.booking_reference}")
            else:
                await metadata_storage.move_to_failed(call_metadata.call_id, result.error_message or "Unknown error")
                logger.error(f"[BACKGROUND] Booking failed: {result.error_message}")
                
        except Exception as e:
            logger.error(f"[BACKGROUND] Error processing booking: {e}")
            await metadata_storage.move_to_failed(call_metadata.call_id, str(e))
    
    async def check_booking_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the status of a browser automation booking
        
        Parameters:
        - call_id: The call ID from the original booking request
        """
        try:
            call_id = parameters.get('call_id')
            if not call_id:
                return {
                    "success": False,
                    "error": "Missing required parameter: call_id",
                    "error_code": "MISSING_PARAMETERS"
                }
            
            # Get call metadata from storage
            call_metadata = await metadata_storage.get_call_metadata(call_id)
            if not call_metadata:
                return {
                    "success": False,
                    "error": f"No booking found with call ID: {call_id}",
                    "error_code": "CALL_NOT_FOUND"
                }
            
            # Check current status
            current_status = await metadata_storage.get_call_status(call_id)
            
            response = {
                "success": True,
                "call_id": call_id,
                "status": current_status,
                "restaurant_id": call_metadata.restaurant_id,
                "booking_request": call_metadata.booking_request,
                "created_at": call_metadata.created_at.isoformat()
            }
            
            # Add result if completed
            if current_status in ['completed', 'failed']:
                result = await metadata_storage.get_call_result(call_id)
                if result:
                    response["result"] = result
            
            return response
            
        except Exception as e:
            logger.error(f"[BROWSER TOOL] Error checking booking status: {str(e)}")
            return {
                "success": False,
                "error": f"Error checking booking status: {str(e)}",
                "error_code": "STATUS_CHECK_ERROR"
            }
    
    async def get_supported_restaurants(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get list of restaurants that support browser automation booking
        
        Parameters: None
        """
        try:
            # Get restaurant configurations from browser automation
            configs = self.browser_automation.restaurant_configs
            
            supported_restaurants = []
            for restaurant_id, config in configs.items():
                supported_restaurants.append({
                    "restaurant_id": restaurant_id,
                    "name": config.name,
                    "url": config.url,
                    "requires_login": config.requires_login,
                    "booking_path": config.booking_path
                })
            
            return {
                "success": True,
                "supported_restaurants": supported_restaurants,
                "total_count": len(supported_restaurants)
            }
            
        except Exception as e:
            logger.error(f"[BROWSER TOOL] Error getting supported restaurants: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting supported restaurants: {str(e)}",
                "error_code": "RESTAURANT_LIST_ERROR"
            }

# Global tool instance
browser_tool = VapiBrowserAutomationTool()

# Vapi function definitions
AUTOMATE_BOOKING_FUNCTION = {
    "name": "automate_booking",
    "description": "Automate restaurant booking using browser automation. Use this when the customer wants to make a reservation and you need to book directly on the restaurant's website.",
    "parameters": {
        "type": "object",
        "properties": {
            "restaurant_id": {
                "type": "string",
                "description": "The ID of the restaurant where the booking should be made"
            },
            "customer_name": {
                "type": "string",
                "description": "Full name of the customer making the reservation"
            },
            "customer_phone": {
                "type": "string",
                "description": "Phone number of the customer (include country code if available)"
            },
            "booking_date": {
                "type": "string",
                "description": "Date for booking in YYYY-MM-DD format (e.g., '2024-03-25')"
            },
            "booking_time": {
                "type": "string",
                "description": "Time for booking in HH:MM format (e.g., '19:00' for 7 PM)"
            },
            "party_size": {
                "type": "integer",
                "description": "Number of people for the reservation"
            },
            "special_requests": {
                "type": "string",
                "description": "Any special requests or notes for the restaurant (optional)"
            }
        },
        "required": ["restaurant_id", "customer_name", "customer_phone", "booking_date", "booking_time", "party_size"]
    }
}

CHECK_BOOKING_STATUS_FUNCTION = {
    "name": "check_booking_status",
    "description": "Check the status of a browser automation booking that was previously initiated",
    "parameters": {
        "type": "object",
        "properties": {
            "call_id": {
                "type": "string",
                "description": "The call ID from the original booking request"
            }
        },
        "required": ["call_id"]
    }
}

GET_SUPPORTED_RESTAURANTS_FUNCTION = {
    "name": "get_supported_restaurants",
    "description": "Get list of restaurants that support browser automation booking",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

# Tool handler functions for voice handler integration
async def handle_automate_booking(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle automate_booking function call from Vapi"""
    return await browser_tool.automate_booking(parameters)

async def handle_check_booking_status(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle check_booking_status function call from Vapi"""
    return await browser_tool.check_booking_status(parameters)

async def handle_get_supported_restaurants(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_supported_restaurants function call from Vapi"""
    return await browser_tool.get_supported_restaurants(parameters)
