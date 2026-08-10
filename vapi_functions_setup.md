# Vapi Function Tools for RestoVoice
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
  "description": "Create a new restaurant reservation booking",
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
        "description": "The booking date and time in ISO format (e.g., '2024-03-25T19:00:00Z')"
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
  "description": "Modify an existing restaurant reservation",
  "parameters": {
    "type": "object",
    "properties": {
      "booking_id": {
        "type": "string",
        "description": "The ID of the existing booking to modify"
      },
      "modifications": {
        "type": "object",
        "description": "Object containing the fields to modify. Can include: customer_name, customer_phone, party_size, booking_time",
        "properties": {
          "customer_name": {
            "type": "string",
            "description": "Updated customer name"
          },
          "customer_phone": {
            "type": "string",
            "description": "Updated customer phone number"
          },
          "party_size": {
            "type": "integer",
            "description": "Updated party size"
          },
          "booking_time": {
            "type": "string",
            "description": "Updated booking date and time in ISO format"
          }
        }
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
  "description": "Cancel an existing restaurant reservation",
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

## 5. End Call Function (Built-in Vapi)
```json
{
  "name": "end_call",
  "description": "End the current call when booking is complete or customer requests it",
  "parameters": {
    "type": "object",
    "properties": {
      "reason": {
        "type": "string",
        "description": "Reason for ending the call (e.g., 'booking_completed', 'customer_request')"
      }
    },
    "required": []
  }
}
```

# Setup Instructions:

1. **Go to Vapi Dashboard** → Assistants → Select your RestoVoice assistant
2. **Scroll to Functions section** → Click "Add Function"
3. **Copy and paste each JSON definition** above as separate functions
4. **Set the Function URL** to: `https://restovoice.loca.lt/v1/vapi/webhooks/vapi`
5. **Enable Function Calling** in the assistant settings
6. **Save the assistant**

# Important Notes:

- Make sure your backend is running and accessible via the tunnel URL
- The `serverUrl` in your assistant config should point to the same webhook URL
- These functions will automatically be called by the AI when customers ask to:
  - Check availability ("Do you have a table for 2 at 7 PM?")
  - Make bookings ("I'd like to make a reservation")
  - Change bookings ("Can I move my reservation to 8 PM?")
  - Cancel bookings ("I need to cancel my reservation")

# Testing:
1. Use the "Test Webhook Directly" button in your HTML test page
2. Start a call and ask: "I'd like to make a reservation for 2 people tonight at 7 PM"
3. The AI should call the `check_availability` function first, then `create_booking`
