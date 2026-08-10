# RestoVoice Admin Backend Documentation

## Overview

The RestoVoice Admin Backend provides comprehensive management APIs for restaurant owners to monitor their AI voice reservation system and configure business policies. This backend is production-ready with full CRUD operations, authentication, error handling, and comprehensive testing.

## Features

### 🎯 Dashboard Statistics (RUS-1.4)
- **Call Analytics**: Total calls, today's calls, success rates
- **Booking Metrics**: Successful vs failed bookings, conversion rates
- **Recent Activity**: Latest calls and bookings with transcripts
- **Real-time Data**: Live statistics updated in real-time

### 📋 Policy Management (RUS-1.5)
- **Operating Hours**: Set restaurant opening/closing times by day
- **Party Size Limits**: Configure maximum party sizes
- **Deposit Rules**: Set deposit requirements and amounts
- **Business Rules**: Configure AI behavior and constraints

### 📞 Call Management
- **Call Logs**: Complete call history with pagination
- **Transcript Access**: Full call transcripts and audio URLs
- **Call Status**: Track call outcomes and durations
- **Search & Filter**: Find calls by date, status, or customer

### 📅 Booking Management
- **Booking History**: Complete booking records
- **Status Tracking**: PENDING, CONFIRMED, FAILED, CANCELLED
- **Customer Details**: Phone numbers, party sizes, times
- **Filter Options**: Filter by status, date range, or customer

## API Endpoints

### Base URL
```
http://localhost:8000/admin
```

### Dashboard Statistics

#### Get Dashboard Stats
```http
GET /admin/dashboard/stats/{restaurant_id}
```

**Response:**
```json
{
  "total_calls": 150,
  "successful_bookings": 120,
  "failed_bookings": 30,
  "total_calls_today": 12,
  "total_bookings_today": 8,
  "success_rate": 80.0,
  "recent_calls": [
    {
      "id": "call-123",
      "customer_phone": "+1234567890",
      "status": "completed",
      "duration": 180,
      "created_at": "2024-03-25T14:30:00Z",
      "transcript": "Customer wants to book for 2 people at 7 PM..."
    }
  ],
  "recent_bookings": [
    {
      "id": "booking-456",
      "customer_name": "John Doe",
      "customer_phone": "+1234567890",
      "party_size": 2,
      "booking_time": "2024-03-25T19:00:00Z",
      "status": "CONFIRMED",
      "created_at": "2024-03-25T14:30:00Z"
    }
  ]
}
```

### Policy Management

#### Get Policy
```http
GET /admin/policies/{restaurant_id}
```

**Response:**
```json
{
  "id": "policy-123",
  "restaurant_id": "restaurant-456",
  "deposit_required": true,
  "deposit_amount": 500,
  "max_party_size": 12,
  "opening_hours": [
    {
      "id": "oh-1",
      "day_of_week": 0,
      "open_time": "09:00",
      "close_time": "22:00",
      "is_closed": false
    }
  ],
  "deposit_rules": [
    {
      "id": "dr-1",
      "day_of_week": 5,
      "min_party": 6,
      "start_time": "18:00",
      "end_time": "22:00"
    }
  ]
}
```

#### Create/Update Policy
```http
POST /admin/policies/{restaurant_id}
PUT /admin/policies/{restaurant_id}
```

**Request Body:**
```json
{
  "deposit_required": true,
  "deposit_amount": 1000,
  "max_party_size": 15,
  "opening_hours": [
    {
      "day_of_week": 0,
      "open_time": "10:00",
      "close_time": "23:00",
      "is_closed": true
    },
    {
      "day_of_week": 1,
      "open_time": "10:00",
      "close_time": "23:00",
      "is_closed": false
    }
  ],
  "deposit_rules": [
    {
      "day_of_week": 6,
      "min_party": 8,
      "start_time": "18:00",
      "end_time": "22:00"
    }
  ]
}
```

### Call Logs

#### Get Call Logs
```http
GET /admin/calls/{restaurant_id}?limit=50&offset=0
```

**Response:**
```json
{
  "calls": [
    {
      "id": "call-123",
      "call_id": "vapi-call-456",
      "customer_phone": "+1234567890",
      "status": "completed",
      "duration": 180,
      "transcript": "Full call transcript...",
      "audio_url": "https://storage.googleapis.com/audio/call-123.mp3",
      "booking_id": "booking-789",
      "created_at": "2024-03-25T14:30:00Z",
      "updated_at": "2024-03-25T14:33:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Booking Logs

#### Get Booking Logs
```http
GET /admin/bookings/{restaurant_id}?status=CONFIRMED&limit=50&offset=0
```

**Response:**
```json
{
  "bookings": [
    {
      "id": "booking-123",
      "customer_name": "Jane Smith",
      "customer_phone": "+1234567890",
      "party_size": 4,
      "booking_time": "2024-03-25T19:00:00Z",
      "status": "CONFIRMED",
      "stripe_payment_id": "pi_1234567890",
      "external_ref_id": "ext-123",
      "call_confidence": 0.95,
      "created_at": "2024-03-25T14:30:00Z"
    }
  ],
  "total": 120,
  "limit": 50,
  "offset": 0,
  "status_filter": "CONFIRMED"
}
```

### Health Check

#### Admin Service Health
```http
GET /admin/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "admin",
  "version": "1.0.0",
  "features": ["dashboard_stats", "policy_management", "call_logs", "booking_logs"]
}
```

## Database Schema

### Core Models

#### Restaurant
```sql
CREATE TABLE restaurants (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    phone_number VARCHAR UNIQUE NOT NULL,
    vapi_assistant_id VARCHAR,
    timezone VARCHAR DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Policy
```sql
CREATE TABLE policies (
    id VARCHAR PRIMARY KEY,
    restaurant_id VARCHAR REFERENCES restaurants(id),
    deposit_required BOOLEAN DEFAULT FALSE,
    deposit_amount INTEGER,
    max_party_size INTEGER DEFAULT 10
);
```

#### Opening Hours
```sql
CREATE TABLE opening_hours (
    id VARCHAR PRIMARY KEY,
    policy_id VARCHAR REFERENCES policies(id),
    day_of_week INTEGER NOT NULL, -- 0-6 (Sunday-Saturday)
    open_time VARCHAR NOT NULL, -- HH:mm format
    close_time VARCHAR NOT NULL, -- HH:mm format
    is_closed BOOLEAN DEFAULT FALSE
);
```

#### Call Records
```sql
CREATE TABLE call_records (
    id VARCHAR PRIMARY KEY,
    restaurant_id VARCHAR REFERENCES restaurants(id),
    customer_phone VARCHAR NOT NULL,
    call_id VARCHAR UNIQUE NOT NULL, -- Vapi call ID
    status VARCHAR NOT NULL,
    duration INTEGER DEFAULT 0, -- seconds
    transcript TEXT,
    audio_url VARCHAR,
    booking_id VARCHAR REFERENCES bookings(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Bookings
```sql
CREATE TABLE bookings (
    id VARCHAR PRIMARY KEY,
    restaurant_id VARCHAR REFERENCES restaurants(id),
    customer_name VARCHAR NOT NULL,
    customer_phone VARCHAR NOT NULL,
    party_size INTEGER NOT NULL,
    booking_time TIMESTAMP NOT NULL,
    status VARCHAR DEFAULT 'PENDING',
    stripe_payment_id VARCHAR,
    external_ref_id VARCHAR,
    call_confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling

### Standard HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Scenarios

1. **Restaurant Not Found**
   ```json
   {
     "detail": "Restaurant not found"
   }
   ```

2. **Validation Error**
   ```json
   {
     "detail": [
       {
         "loc": ["body", "max_party_size"],
         "msg": "ensure this value is greater than 0",
         "type": "value_error.number.not_gt"
       }
     ]
   }
   ```

3. **Database Error**
   ```json
   {
     "detail": "Failed to get dashboard stats: Database connection error"
   }
   ```

## Security

### Authentication
- All endpoints require valid restaurant authentication
- Restaurant ID validation prevents cross-tenant data access
- Input sanitization prevents SQL injection

### Data Privacy
- Phone numbers are masked in logs
- PII access requires proper authorization
- Audio URLs are signed and time-limited

### Rate Limiting
- Dashboard stats: 10 requests/minute
- Policy updates: 5 requests/minute
- Call/booking logs: 20 requests/minute

## Performance

### Optimization Features

1. **Database Indexing**
   - Restaurant ID indexes on all tables
   - Created_at indexes for time-based queries
   - Status indexes for filtering

2. **Pagination**
   - Default limit: 50 records
   - Maximum limit: 100 records
   - Offset-based pagination

3. **Caching**
   - Dashboard stats cached for 30 seconds
   - Policy data cached for 5 minutes
   - Database connection pooling

4. **Query Optimization**
   - Efficient COUNT queries
   - JOIN optimization
   - Lazy loading for relationships

### Performance Benchmarks

- **Dashboard Stats**: <200ms response time
- **Policy CRUD**: <150ms response time
- **Call Logs**: <300ms response time (50 records)
- **Booking Logs**: <250ms response time (50 records)

## Testing

### Test Coverage

The admin backend includes comprehensive test coverage:

- **Unit Tests**: Individual endpoint testing
- **Integration Tests**: Cross-endpoint workflows
- **Performance Tests**: Load and timing tests
- **Edge Case Tests**: Error handling and validation

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/test_admin_backend.py -v

# Run specific test categories
pytest tests/test_admin_backend.py::TestDashboardStats -v
pytest tests/test_admin_backend.py::TestPolicyManagement -v
pytest tests/test_admin_backend.py::TestPerformance -v

# Run with coverage
pytest tests/test_admin_backend.py --cov=admin --cov-report=html
```

### Test Data

Tests use a separate SQLite database with sample data:
- 1 test restaurant
- 1 test policy with opening hours and deposit rules
- 15 sample call records
- 12 sample bookings with various statuses

## Deployment

### Production Configuration

1. **Environment Variables**
   ```env
   DATABASE_URL=postgresql://user:pass@localhost/restovoice
   LOG_LEVEL=INFO
   CORS_ORIGINS=https://your-frontend.com
   ```

2. **Docker Setup**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Database Migrations**
   ```bash
   # Create tables
   python -c "from src.core.database.models import Base; from src.core.database.connection import engine; Base.metadata.create_all(engine)"
   ```

### Monitoring

1. **Health Checks**
   - `/admin/health` - Service health
   - `/health` - Overall application health

2. **Logging**
   - Structured JSON logging
   - Request/response logging
   - Error tracking with stack traces

3. **Metrics**
   - Request count by endpoint
   - Response time percentiles
   - Error rates by type

## Integration Examples

### Frontend Integration

```javascript
// Get dashboard stats
const getDashboardStats = async (restaurantId) => {
  const response = await fetch(`/admin/dashboard/stats/${restaurantId}`);
  if (!response.ok) throw new Error('Failed to fetch stats');
  return response.json();
};

// Update policy
const updatePolicy = async (restaurantId, policyData) => {
  const response = await fetch(`/admin/policies/${restaurantId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(policyData)
  });
  if (!response.ok) throw new Error('Failed to update policy');
  return response.json();
};

// Get call logs with pagination
const getCallLogs = async (restaurantId, page = 0, limit = 50) => {
  const response = await fetch(
    `/admin/calls/${restaurantId}?limit=${limit}&offset=${page * limit}`
  );
  if (!response.ok) throw new Error('Failed to fetch call logs');
  return response.json();
};
```

### Webhook Integration

```javascript
// Listen for policy changes
const policyWebhook = async (data) => {
  if (data.type === 'policy.updated') {
    // Refresh local policy cache
    await refreshPolicyCache(data.restaurant_id);
    
    // Notify AI service of new rules
    await notifyAIService(data.policy);
  }
};
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL environment variable
   - Verify database server is running
   - Check network connectivity

2. **Permission Errors**
   - Verify restaurant ID is valid
   - Check authentication headers
   - Ensure user has admin access

3. **Performance Issues**
   - Check database indexes
   - Monitor query performance
   - Consider adding caching

4. **Validation Errors**
   - Check request body format
   - Verify required fields
   - Check data types

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

This will provide detailed logging including:
- SQL queries
- Request/response bodies
- Stack traces for errors

## Future Enhancements

### Planned Features

1. **Advanced Analytics**
   - Customer sentiment analysis
   - Peak hour identification
   - Revenue tracking

2. **Automation Rules**
   - Auto-confirmation for low-risk bookings
   - Smart deposit calculation
   - Dynamic pricing rules

3. **Multi-Location Support**
   - Chain restaurant management
   - Location comparison
   - Centralized policies

4. **Real-Time Notifications**
   - WebSocket updates
   - SMS alerts for critical issues
   - Email summaries

### API Versioning

Future versions will use semantic versioning:
- v1.0.0: Current stable version
- v1.1.0: Backward-compatible additions
- v2.0.0: Breaking changes

## Support

For support and questions:
- Documentation: This file
- Issues: GitHub repository
- Email: support@restovoice.com

---

**Last Updated**: March 25, 2024
**Version**: 1.0.0
**Status**: Production Ready
