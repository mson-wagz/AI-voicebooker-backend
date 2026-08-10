# RestoVoice AI Backend - Vapi Integration Documentation

## Overview

The RestoVoice AI Backend has been enhanced with comprehensive Vapi AI telephone orchestration capabilities using **Eleven Labs** for ultra-realistic voice synthesis and database functionality moved from the Next.js frontend. This integration enables AI-powered voice calls for restaurant reservations with natural, human-like voices.

## Architecture

### Core Components

1. **Voice Handler** (`src/core/voice/voice_handler.py`)
   - Main Vapi integration logic with Eleven Labs voice provider
   - Call orchestration and webhook handling
   - Function call routing for booking operations

2. **Eleven Labs Integration** (`src/core/voice/elevenlabs.py`)
   - Voice configuration management
   - Restaurant-optimized voice settings
   - Voice recommendations based on restaurant type

3. **Database Layer** (`src/core/database/`)
   - SQLAlchemy models based on original Prisma schema
   - Connection management and CRUD operations
   - Support for restaurants, bookings, calls, and analytics

4. **API Endpoints** (`src/core/voice/vapi_api.py`, `src/core/database/api.py`)
   - RESTful APIs for Vapi operations
   - Database management endpoints
   - Webhook handling for real-time events

## Features

### Vapi + Eleven Labs Integration

- **Ultra-Realistic Voices**: High-quality voice synthesis using Eleven Labs
- **Voice Selection**: Multiple voice options optimized for restaurant service
- **Smart Voice Recommendations**: Voice suggestions based on restaurant type
- **Customizable Settings**: Fine-tune voice parameters for optimal experience

### Voice Options

- **Rachel** (Default): Warm, friendly, and professional female voice
- **Domi**: Energetic and enthusiastic female voice
- **Bella**: Sophisticated and elegant female voice
- **Antoni**: Professional and confident male voice
- **Elliot**: Friendly and approachable male voice
- **Josh**: Casual and conversational male voice

### Database Operations

- **Restaurant Management**: Create, update, and retrieve restaurant data
- **Booking System**: Complete booking lifecycle management
- **Policy Management**: Restaurant policies and opening hours
- **Analytics**: Call metrics and booking statistics

## Setup Instructions

### 1. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/restovoice

# Vapi AI
VAPI_API_KEY=your_vapi_api_key_here
VAPI_PHONE_NUMBER_ID=your_vapi_phone_number_id_here

# Azure OpenAI (for LLM)
AZURE_REGION=eastus
AZURE_RESOURCE_ID=your_azure_resource_id_here
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Eleven Labs Voice Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=rachel
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_STABILITY=0.5
ELEVENLABS_SIMILARITY_BOOST=0.5
ELEVENLABS_STYLE=0.0
ELEVENLABS_USE_SPEAKER_BOOST=true
```

### 2. Database Setup

```bash
# Install PostgreSQL and create database
createdb restovoice

# Run migrations (when implemented)
alembic upgrade head
```

### 3. Install Dependencies

```bash
cd ai-backend
pip install -e .
```

### 4. Start the Application

```bash
python src/main.py
# or
uvicorn src.main:app --reload
```

## API Endpoints

### Voice Management

#### Get Available Voices
```http
GET /v1/vapi/voices/elevenlabs
```

#### Get Voice Recommendations
```http
GET /v1/vapi/voices/recommendations/{restaurant_type}
# Examples: fine_dining, casual, family, sports_bar, coffee_shop
```

### Vapi Operations

#### Initiate Call
```http
POST /v1/vapi/calls/initiate
{
  "restaurant_id": "restaurant-123",
  "customer_number": "+1234567890",
  "assistant_id": "assistant-123"  # optional
}
```

#### Create Assistant with Eleven Labs Voice
```http
POST /v1/vapi/assistants/create
{
  "restaurant_id": "restaurant-123",
  "name": "Restaurant Name Agent",
  "welcome_message": "Custom welcome message",
  "voice_provider": "elevenlabs",
  "voice_id": "rachel",
  "elevenlabs_settings": {
    "model_id": "eleven_multilingual_v2",
    "stability": 0.6,
    "similarity_boost": 0.7,
    "style": 0.3,
    "use_speaker_boost": true
  }
}
```

#### Webhook Handler
```http
POST /v1/vapi/webhooks/vapi
{
  "type": "call.ended",
  "call": { ... }
}
```

### Database Operations

#### Create Restaurant
```http
POST /v1/db/restaurants
{
  "name": "Restaurant Name",
  "phone_number": "+1234567890",
  "timezone": "UTC"
}
```

#### Create Booking
```http
POST /v1/db/bookings
{
  "restaurant_id": "restaurant-123",
  "customer_name": "John Doe",
  "customer_phone": "+1234567890",
  "party_size": 4,
  "booking_time": "2024-02-06T19:00:00Z"
}
```

## Voice Configuration

### Restaurant-Optimized Settings

The system automatically applies restaurant-optimized voice settings:

- **Model**: `eleven_multilingual_v2` (best for customer service)
- **Stability**: 0.6 (slightly more stable for professional tone)
- **Similarity Boost**: 0.7 (higher similarity for clarity)
- **Style**: 0.3 (moderate style for friendly but professional)
- **Speaker Boost**: Enabled

### Voice Recommendations by Restaurant Type

| Restaurant Type | Recommended Voice | Characteristics |
|----------------|-------------------|-----------------|
| Fine Dining | Bella | Elegant and sophisticated |
| Casual | Rachel | Warm and friendly |
| Family | Domi | Energetic and enthusiastic |
| Sports Bar | Elliot | Friendly and approachable |
| Coffee Shop | Rachel | Warm and inviting |
| Formal | Antoni | Professional and confident |

## Database Schema

The database models mirror the original Prisma schema:

- **Users**: Restaurant owners and staff
- **Restaurants**: Restaurant information and Vapi assistant IDs
- **Policies**: Booking policies and deposit rules
- **OpeningHours**: Restaurant operating hours
- **Bookings**: Reservation details
- **CallRecords**: Vapi call logs and transcripts
- **DailyMetrics**: Analytics data

## Call Flow

1. **Call Initiation**: System triggers outbound call via Vapi
2. **Voice Synthesis**: Eleven Labs generates ultra-realistic voice
3. **Assistant Interaction**: AI assistant handles conversation naturally
4. **Function Calls**: Assistant triggers booking operations
5. **Webhook Events**: Real-time call status updates
6. **Data Storage**: Call records and transcripts stored

## Function Calls During Calls

The AI assistant can trigger these operations:

- `check_availability`: Check table availability
- `create_booking`: Create new reservation
- `modify_booking`: Modify existing booking
- `cancel_booking`: Cancel reservation

## Error Handling

- Comprehensive error logging
- Graceful fallbacks for API failures
- Database transaction rollbacks
- Webhook retry mechanisms
- Voice configuration validation

## Security

- Environment variable configuration
- CORS protection
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- API key protection for Eleven Labs

## Development

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## Monitoring

- Health check endpoint: `/health`
- Service status monitoring
- Call analytics dashboard
- Voice performance metrics
- Error tracking and logging

## Troubleshooting

### Common Issues

1. **Eleven Labs API Key Errors**
   - Verify ELEVENLABS_API_KEY in environment
   - Check API key permissions and quota

2. **Voice Configuration Issues**
   - Validate voice ID using `/v1/vapi/voices/elevenlabs`
   - Check voice settings are within valid ranges

3. **Vapi Integration Issues**
   - Verify VAPI_API_KEY in environment
   - Check webhook URL in Vapi dashboard

4. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check PostgreSQL service status

## Performance Optimization

### Voice Settings for Different Use Cases

**High-Volume Call Centers**:
- Stability: 0.7
- Similarity Boost: 0.6
- Style: 0.2

**Premium Restaurants**:
- Stability: 0.5
- Similarity Boost: 0.8
- Style: 0.4

**Casual Dining**:
- Stability: 0.6
- Similarity Boost: 0.7
- Style: 0.3

## Next Steps

1. **Testing**: Set up test environment with Vapi and Eleven Labs sandboxes
2. **Voice Customization**: Create voice cloning for restaurant brands
3. **Analytics**: Build dashboard for call metrics and voice performance
4. **Scaling**: Add load balancing for high call volumes
5. **Multi-language**: Add support for multiple languages

## Support

For issues and questions:
- Check application logs
- Verify environment configuration
- Review API documentation
- Test with Vapi playground
- Validate Eleven Labs voice settings
