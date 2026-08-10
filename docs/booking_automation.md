# Restaurant Booking Automation System

Production-ready system that automates restaurant bookings through AI-powered call processing and browser automation.

## Overview

The system implements a complete flow:
1. **AI Call Processing**: Extracts booking details from customer calls using GPT-4
2. **Metadata Storage**: Saves booking data in JSON format for processing
3. **Browser Automation**: Uses browser-use to automatically make reservations online

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Vapi Call     │───▶│  AI Processor   │───▶│  JSON Storage  │
│   (Customer)    │    │ (GPT-4)        │    │ (Metadata)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Restaurant    │◀───│ Browser-Use     │◀───│  Automation    │
│   Confirmation  │    │ (Automation)    │    │  Service      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components

### 1. Call Processor (`src/core/ai/call_processor.py`)
- Uses GPT-4 to extract booking details from call transcripts
- Normalizes phone numbers and validates data
- Determines processing priority based on booking details

### 2. Metadata Storage (`src/core/metadata/storage.py`)
- Stores call metadata in JSON files
- Organizes by status: pending, processing, completed, failed
- Supports retry logic and cleanup of old files

### 3. Browser Automation (`src/core/automation/browser_use.py`)
- Integrates with browser-use for web automation
- Supports multiple restaurant booking sites
- Handles login, form filling, and confirmation extraction

### 4. Automation Service (`src/core/automation/service.py`)
- Runs continuously in the background
- Processes pending calls automatically
- Manages cleanup and retry operations

## API Endpoints

### Process Call for Booking
```
POST /v1/vapi/process-call
```

Process call data for automated booking.

**Request Body:**
```json
{
  "restaurant_id": "restaurant_1",
  "customer_phone": "+1-555-123-4567",
  "transcript": "Customer call transcript...",
  "status": "completed",
  "recording_url": "https://example.com/recording.mp3"
}
```

**Response:**
```json
{
  "success": true,
  "call_id": "uuid-generated-id",
  "message": "Call processed successfully for booking automation",
  "status": "pending_automation"
}
```

### Vapi Webhook
```
POST /v1/vapi/webhooks/vapi
```

Receives Vapi webhook events and automatically processes completed calls for booking.

### Health Check
```
GET /health
```

Returns system status including automation service status.

## Configuration

### Environment Variables

```bash
# Azure OpenAI API for call processing
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo-preview

# Vapi Configuration
VAPI_API_KEY=your_vapi_api_key
VAPI_PHONE_NUMBER=your_vapi_phone_number

# Restaurant Configurations (JSON format)
RESTAURANT_CONFIGS='{
  "restaurant_1": {
    "name": "Restaurant Name",
    "url": "https://restaurant-website.com",
    "booking_path": "/reservations",
    "selectors": {
      "date_field": "#date",
      "time_field": "#time",
      "party_size": "#party-size"
    }
  }
}'

# Optional: Login credentials for sites requiring authentication
OPENTABLE_EMAIL=your_email@example.com
OPENTABLE_PASSWORD=your_password
```

## File Structure

```
ai-backend/
├── src/core/
│   ├── ai/
│   │   └── call_processor.py      # AI call processing
│   ├── automation/
│   │   ├── browser_use.py         # Browser automation
│   │   └── service.py           # Automation service
│   ├── metadata/
│   │   └── storage.py           # JSON metadata storage
│   └── voice/
│       └── vapi_api.py          # Vapi integration
├── call_metadata/                # JSON storage directory
│   ├── pending/                # Pending bookings
│   ├── processing/             # Currently processing
│   ├── completed/              # Successfully completed
│   └── failed/                # Failed bookings
└── test_booking_flow.py        # Test script
```

## Deployment

### Production Deployment

1. **Install Dependencies:**
```bash
uv sync
```

2. **Set Environment Variables:**
```bash
export AZURE_OPENAI_API_KEY="your_key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4-turbo-preview"
export VAPI_API_KEY="your_key"
export RESTAURANT_CONFIGS='{"..."}'
```

3. **Run the Service:**
```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The automation service will start automatically and process bookings in the background.

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Testing

Run the complete flow test:
```bash
uv run python test_booking_flow.py
```

This will:
1. Process a sample call transcript
2. Extract booking details using AI
3. Save metadata to JSON
4. Simulate automation processing

## Monitoring

### Health Endpoint
Check `/health` endpoint for service status:
- Automation service running status
- Number of pending bookings
- Individual service statuses

### Logs
Monitor logs for:
- Call processing status
- Booking automation results
- Error details and retry attempts

## Restaurant Setup

To add a new restaurant:

1. **Create Configuration:**
```json
{
  "restaurant_id": {
    "name": "Restaurant Name",
    "url": "https://restaurant.com",
    "booking_path": "/reservations",
    "selectors": {
      "date_field": "#reservation-date",
      "time_field": "#reservation-time",
      "party_size": "#party-size",
      "name_field": "#customer-name",
      "phone_field": "#customer-phone",
      "submit_button": "#submit-reservation"
    },
    "requires_login": false,
    "special_handling": {
      "handle_waitlist": true,
      "alternative_times": true
    }
  }
}
```

2. **Add to Environment:**
Update `RESTAURANT_CONFIGS` with the new restaurant.

3. **Test Automation:**
Use the test script to verify the booking works correctly.

## Error Handling

### Retry Logic
- Failed bookings are retried up to 3 times
- Exponential backoff between retries
- Failed calls are moved to `failed/` directory

### Common Issues
1. **Website Changes**: Update selectors in restaurant config
2. **CAPTCHA**: May require manual intervention or CAPTCHA solving service
3. **Rate Limiting**: Built-in delays between requests
4. **Login Required**: Configure credentials in environment

## Security

- All sensitive data stored locally in JSON files
- Phone numbers normalized and validated
- No customer PII logged
- Browser runs in headless mode in production

## Performance

- Concurrent processing of up to 3 bookings
- Automatic cleanup of old files (30 days)
- Efficient JSON storage with file-based locking
- Background processing doesn't block API responses

## Support

For issues:
1. Check logs for error details
2. Verify restaurant configurations
3. Test with `test_booking_flow.py`
4. Monitor `/health` endpoint status
