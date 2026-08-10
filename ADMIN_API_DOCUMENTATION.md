# RestoVoice Admin API Documentation

## Overview

This document describes all the admin dashboard endpoints available in the RestoVoice AI Backend. These endpoints provide comprehensive functionality for restaurant owners and administrators to manage their restaurant operations, view analytics, and configure settings.

## Authentication

All admin endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### Authentication

#### Login
```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "owner@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "jwt_token_here",
  "user": {
    "id": "user_id",
    "email": "owner@example.com",
    "name": "Restaurant Owner",
    "role": "OWNER"
  }
}
```

---

### Dashboard Overview

#### Get Overview Statistics
```http
GET /owner/dashboard/overview-stats?days=30
```

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "totalCalls": 150,
  "successfulBookings": 45,
  "successfulBookingsChange": 12.5,
  "failedBookings": 15,
  "failedBookingsChange": -5.2,
  "conversionRate": 75.0,
  "conversionRateChange": 3.1
}
```

---

### Call Management

#### Get Call Logs
```http
GET /owner/dashboard/calls?page=1&limit=50&status=COMPLETED&start_date=2024-01-01&end_date=2024-01-31
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50, max: 100)
- `status` (optional): Filter by call status
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)

**Response:**
```json
{
  "calls": [
    {
      "id": "call_id",
      "customer_phone": "+1234567890",
      "call_duration": 120,
      "call_status": "COMPLETED",
      "booking_result": "CONFIRMED",
      "timestamp": "2024-01-15T10:30:00Z",
      "transcript": "Call transcript...",
      "sentiment": "positive"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50
}
```

#### Get Call Details
```http
GET /owner/dashboard/call/{call_id}
```

**Response:**
```json
{
  "id": "call_id",
  "customer_phone": "+1234567890",
  "call_duration": 120,
  "call_status": "COMPLETED",
  "timestamp": "2024-01-15T10:30:00Z",
  "transcript": "Full call transcript...",
  "sentiment": "positive",
  "recording_url": "https://example.com/recording.mp3",
  "booking": {
    "id": "booking_id",
    "status": "CONFIRMED"
  },
  "ai_analysis": {
    "intent": "booking",
    "confidence": 0.95
  }
}
```

---

### Booking Management

#### Get Bookings
```http
GET /owner/dashboard/bookings?page=1&limit=50&status=CONFIRMED&start_date=2024-01-01&end_date=2024-01-31
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50, max: 100)
- `status` (optional): Filter by booking status
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)

**Response:**
```json
{
  "bookings": [
    {
      "id": "booking_id",
      "customer_name": "John Doe",
      "customer_phone": "+1234567890",
      "party_size": 4,
      "reservation_time": "2024-01-15T19:00:00Z",
      "status": "CONFIRMED",
      "deposit_amount": 50,
      "deposit_status": "PAID",
      "created_at": "2024-01-14T10:30:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 50
}
```

#### Get Booking Details
```http
GET /owner/dashboard/booking/{booking_id}
```

**Response:**
```json
{
  "id": "booking_id",
  "customer_name": "John Doe",
  "customer_phone": "+1234567890",
  "customer_email": "john@example.com",
  "party_size": 4,
  "reservation_time": "2024-01-15T19:00:00Z",
  "status": "CONFIRMED",
  "deposit_amount": 50,
  "deposit_status": "PAID",
  "special_requests": "Window seat preferred",
  "created_at": "2024-01-14T10:30:00Z",
  "updated_at": "2024-01-14T10:35:00Z"
}
```

#### Update Booking Status
```http
PUT /owner/dashboard/booking/{booking_id}/status
```

**Request Body:**
```json
{
  "status": "CANCELLED"
}
```

**Valid Statuses:**
- `CONFIRMED`
- `CANCELLED`
- `COMPLETED`
- `NO_SHOW`

---

### Analytics

#### Get Calls Trend
```http
GET /owner/dashboard/analytics/calls-trend?days=30
```

**Response:**
```json
{
  "trend": [
    {
      "date": "2024-01-15",
      "call_count": 25,
      "completed_calls": 20,
      "failed_calls": 5
    }
  ],
  "period": {
    "start": "2023-12-16T00:00:00Z",
    "end": "2024-01-15T23:59:59Z",
    "days": 30
  }
}
```

#### Get Performance Metrics
```http
GET /owner/dashboard/analytics/performance-metrics?days=30
```

**Response:**
```json
{
  "average_call_duration": 125.5,
  "peak_call_hours": [
    {
      "hour": 19,
      "call_count": 45
    }
  ],
  "success_rate_by_hour": [
    {
      "hour": 19,
      "total_calls": 45,
      "successful_bookings": 35
    }
  ],
  "period": {
    "start": "2023-12-16T00:00:00Z",
    "end": "2024-01-15T23:59:59Z",
    "days": 30
  }
}
```

---

### Restaurant Settings

#### Get Restaurant Settings
```http
GET /user/restaurant-settings
```

**Response:**
```json
{
  "id": "restaurant_id",
  "name": "My Restaurant",
  "phone_number": "+1234567890",
  "email": "restaurant@example.com",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "USA",
  "timezone": "America/New_York",
  "opening_hours": [
    {
      "id": "hours_id",
      "day_of_week": 0,
      "open_time": "09:00",
      "close_time": "22:00",
      "is_closed": false
    }
  ],
  "policy": {
    "deposit_required": true,
    "deposit_amount": 50
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Update Restaurant Settings
```http
PUT /user/restaurant-settings
```

**Request Body:**
```json
{
  "restaurant_name": "My Restaurant",
  "phone_number": "+1234567890",
  "email": "restaurant@example.com",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "USA",
  "timezone": "America/New_York",
  "opening_hours": [
    {
      "day_of_week": 0,
      "open_time": "09:00",
      "close_time": "22:00",
      "is_closed": false
    }
  ]
}
```

---

### Policy Settings

#### Get Policy Settings
```http
GET /user/policy-settings
```

**Response:**
```json
{
  "id": "policy_id",
  "deposit_required": true,
  "deposit_amount": 50,
  "deposit_deadline_hours": 24,
  "max_party_size": 10,
  "min_party_size": 1,
  "advance_booking_days": 30,
  "cancellation_policy": "24-hour cancellation policy",
  "auto_confirm": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Update Policy Settings
```http
PUT /user/policy-settings
```

**Request Body:**
```json
{
  "deposit_required": true,
  "deposit_amount": 50,
  "deposit_deadline_hours": 24,
  "max_party_size": 10,
  "min_party_size": 1,
  "advance_booking_days": 30,
  "cancellation_policy": "24-hour cancellation policy",
  "auto_confirm": false
}
```

---

### Opening Hours

#### Get Opening Hours
```http
GET /user/opening-hours
```

**Response:**
```json
{
  "opening_hours": [
    {
      "id": "hours_id",
      "day_of_week": 0,
      "day_name": "Monday",
      "open_time": "09:00",
      "close_time": "22:00",
      "is_closed": false
    }
  ]
}
```

#### Update Opening Hours
```http
PUT /user/opening-hours
```

**Request Body:**
```json
[
  {
    "day_of_week": 0,
    "open_time": "09:00",
    "close_time": "22:00",
    "is_closed": false
  }
]
```

---

### Availability

#### Get Restaurant Availability
```http
GET /user/availability?date=2024-01-15
```

**Response:**
```json
{
  "date": "2024-01-15",
  "is_closed": false,
  "open_time": "09:00",
  "close_time": "22:00",
  "available_slots": [
    {
      "time": "09:00",
      "available": true
    },
    {
      "time": "10:00",
      "available": true
    }
  ],
  "existing_bookings": 5
}
```

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Error message description"
}
```

## Testing

Use the provided test script to verify all endpoints:

```bash
cd ai-backend
python test_admin_endpoints.py
```

## Rate Limiting

Currently, no rate limiting is implemented, but it's recommended for production use.

## Pagination

Most list endpoints support pagination with `page` and `limit` parameters. The default limit is 50 items per page, with a maximum of 100.

## Date Formats

- All dates should be in `YYYY-MM-DD` format for query parameters
- DateTime responses use ISO 8601 format: `2024-01-15T10:30:00Z`

## Timezones

All timestamps are stored and returned in UTC. The restaurant's timezone setting is used for local time calculations in availability checks.
