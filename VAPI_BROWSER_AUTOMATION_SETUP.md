# Vapi Function Tools for RestoVoice - Complete Setup
# Copy these JSON definitions into your Vapi Dashboard under Assistant > Functions

## 1. Check Availability Function
```json
{
  "name": "check_availability",
  "description": "Check if a table is available at a specific restaurant for a given date, time, and party size",
  "parameters": {
    "type": "object",
    "properties": {
      "restaurant_id": {
        "type": "string",
        "description": "The ID of the restaurant to check availability for"
      },
      "booking_timestamp": {
        "type": "string",
        "description": "The desired booking date and time in ISO format (e.g., '2024-03-25T19:00:00Z')"
      },
      "party_size": {
        "type": "integer",
        "description": "Number of people for the reservation"
      }
    },
    "required": ["restaurant_id", "booking_timestamp", "party_size"]
  }
}
```

## 2. Create Booking Function
```json
{
  "name": "create_booking",
  "description": "Create a new restaurant reservation booking directly in the system",
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
      "party_size": {
        "type": "integer",
        "description": "Number of people for the reservation"
      },
      "booking_time": {
        "type": "string",
        "description": "Booking date and time in ISO format (e.g., '2024-03-25T19:00:00Z')"
      }
    },
    "required": ["restaurant_id", "customer_name", "customer_phone", "party_size", "booking_time"]
  }
}
```

## 3. Modify Booking Function
```json
{
  "name": "modify_booking",
  "description": "Modify an existing restaurant reservation booking",
  "parameters": {
    "type": "object",
    "properties": {
      "booking_id": {
        "type": "string",
        "description": "The ID of the booking to modify"
      },
      "modifications": {
        "type": "object",
        "description": "Object containing the modifications to make (e.g., {'party_size': 4, 'booking_time': '2024-03-25T20:00:00Z'})"
      }
    },
    "required": ["booking_id", "modifications"]
  }
}
```

## 4. Cancel Booking Function
```json
{
  "name": "cancel_booking",
  "description": "Cancel an existing restaurant reservation booking",
  "parameters": {
    "type": "object",
    "properties": {
      "booking_id": {
        "type": "string",
        "description": "The ID of the booking to cancel"
      },
      "reason": {
        "type": "string",
        "description": "Reason for cancellation (optional)"
      }
    },
    "required": ["booking_id"]
  }
}
```

## 5. 🆕 AUTOMATE BOOKING Function (Browser Automation)
```json
{
  "name": "automate_booking",
  "description": "Automate restaurant booking using browser automation. Use this when the customer wants to make a reservation and you need to book directly on the restaurant's website. This is useful for restaurants that don't have API integration.",
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
```

## 6. 🆕 CHECK BOOKING STATUS Function
```json
{
  "name": "check_booking_status",
  "description": "Check the status of a browser automation booking that was previously initiated. Use this to follow up on automated bookings.",
  "parameters": {
    "type": "object",
    "properties": {
      "call_id": {
        "type": "string",
        "description": "The call ID from the original booking request (returned by automate_booking function)"
      }
    },
    "required": ["call_id"]
  }
}
```

## 7. 🆕 GET SUPPORTED RESTAURANTS Function
```json
{
  "name": "get_supported_restaurants",
  "description": "Get list of restaurants that support browser automation booking. Use this to see which restaurants can be booked using automation.",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

## 🚀 SETUP INSTRUCTIONS

### Step 1: Add Functions to Vapi Dashboard
1. Go to your Vapi Dashboard
2. Select your Assistant
3. Go to the "Functions" tab
4. Click "Add Function"
5. Copy and paste each JSON definition above
6. Save each function

### Step 2: Configure Webhook URL
Make sure your webhook URL is set to:
```
https://your-domain.com/v1/vapi/webhooks/vapi
```

### Step 3: Test the Functions
You can test the functions by calling your Vapi number and asking:
- "What restaurants support automated booking?" (tests get_supported_restaurants)
- "I'd like to book a table for 2 people tomorrow at 7 PM" (tests automate_booking)

### Step 4: Browser Automation Setup
For the browser automation to work, ensure:
1. `browser-use` package is installed: `pip install browser-use`
2. OpenAI API key is set in environment variables
3. Browser Use Cloud CDP URL is configured (optional)

## 🎯 USAGE EXAMPLES

### Example 1: Customer wants to book at a supported restaurant
```
Customer: "I'd like to book a table at Example Restaurant for 2 people tomorrow at 7 PM"

AI Flow:
1. Use get_supported_restaurants to confirm Example Restaurant supports automation
2. Use automate_booking with:
   - restaurant_id: "restaurant_1"
   - customer_name: "John Doe"
   - customer_phone: "+1234567890"
   - booking_date: "2024-03-26"
   - booking_time: "19:00"
   - party_size: 2
```

### Example 2: Following up on a booking
```
AI: "I've started the automated booking process. Let me check the status for you."

AI Flow:
1. Use check_booking_status with the call_id returned from automate_booking
2. Report status back to customer
```

## 🔧 CONFIGURATION

### Environment Variables Needed:
```env
# For browser automation
OPENAI_API_KEY=your_openai_api_key
BROWSER_USE_CDP_URL=your_browser_use_cdp_url  # Optional

# For existing functions
DATABASE_URL=your_database_url
```

### Restaurant Configuration:
Add restaurant configurations to your environment or database:
```json
{
  "restaurant_1": {
    "name": "Example Restaurant",
    "url": "https://example-restaurant.com",
    "booking_path": "/reservations"
  }
}
```

## 📞 RESPONSE FORMATS

### Successful automate_booking response:
```json
{
  "success": true,
  "booking_reference": "CONF123456",
  "confirmation_details": {
    "date": "2024-03-26",
    "time": "19:00",
    "party_size": 2
  },
  "message": "Successfully booked table for 2 people at 19:00 on 2024-03-26. Confirmation: CONF123456"
}
```

### Failed automate_booking response:
```json
{
  "success": false,
  "error": "No available tables at the requested time",
  "error_code": "BOOKING_FAILED"
}
```

## 🎉 BENEFITS

1. **Automated Booking**: Book directly on restaurant websites without APIs
2. **Real-time Status**: Track booking progress in real-time
3. **Fallback Option**: Use when direct API booking isn't available
4. **Confirmation Tracking**: Get booking references and confirmations
5. **Error Handling**: Graceful handling of booking failures

The browser automation tool provides a powerful fallback for restaurants that don't have API integration, allowing your AI agent to still make reservations automatically!
