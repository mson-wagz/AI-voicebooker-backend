# RestoVoice AI Backend Authentication System

This document describes the simplified authentication system implemented for the RestoVoice AI Backend.

## Overview

The authentication system provides:
- **Owner signup and login** - Restaurant owners can create accounts and log in
- **Onboarding flow** - New users complete restaurant setup
- **JWT-based authentication** - Secure token-based authentication
- **Dashboard shell** - Authenticated user dashboard access

## API Endpoints

### Authentication Routes (`/v1/auth`)

#### Public Endpoints
- `POST /v1/auth/owner/signup` - Create new owner account
- `POST /v1/auth/login` - User login

#### Protected Endpoints (Require Authentication)
- `GET /v1/auth/me` - Get current user info
- `GET /v1/auth/dashboard` - Get user dashboard data
- `POST /v1/auth/onboarding/complete` - Complete onboarding
- `POST /v1/auth/logout` - Logout (client-side token removal)

## Request/Response Schemas

### Owner Signup Request
```json
{
  "first_name": "John",
  "last_name": "Doe", 
  "restaurant_name": "My Restaurant",
  "email": "john@example.com",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "phone_number": "+1234567890",
  "country_state": "CA",
  "city": "San Francisco",
  "postal_code": "94102",
  "agree_to_terms": true
}
```

### Login Request
```json
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

### Onboarding Request
```json
{
  "restaurant_id": "uuid",
  "timezone": "America/Los_Angeles",
  "phone_number": "+1234567890",
  "address": "123 Main St",
  "cuisine_type": "Italian",
  "max_party_size": 10,
  "deposit_required": false,
  "deposit_amount": 0
}
```

### Authentication Response
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "jwt_token_here",
    "token_type": "bearer",
    "expires_in": 2592000,
    "user": {
      "id": "user_uuid",
      "email": "john@example.com",
      "name": "John Doe",
      "role": "OWNER",
      "onboarding_complete": false,
      "restaurant_id": "restaurant_uuid"
    },
    "restaurant": {
      "id": "restaurant_uuid",
      "name": "My Restaurant",
      "phone_number": "+1234567890",
      "timezone": "UTC"
    }
  }
}
```

## Security Features

### JWT Token Management
- **Access tokens**: 30-day expiration
- **Token validation**: Automatic expiration and integrity checks
- **Secure token generation**: Using `secrets` module

### Password Security
- **Password hashing**: bcrypt with salt
- **Password validation**: Minimum 8 characters, uppercase, lowercase, digit

### Authentication Middleware
- **Request authentication**: Automatic JWT validation
- **Restaurant access validation**: Ensure users can only access their restaurant
- **Security headers**: XSS protection, content type options, etc.

### CORS Configuration
- **Allowed origins**: http://localhost:3000, https://restovoice.com
- **Credentials support**: For cookie-based authentication
- **Method restrictions**: GET, POST, PUT, DELETE

## Database Models

### User Model
- `id` - Primary key (UUID)
- `email` - Unique email address
- `name` - Full name
- `role` - OWNER (simplified)
- `onboarding_complete` - Boolean flag
- `restaurant_id` - Foreign key to Restaurant
- `created_at`, `updated_at` - Timestamps

### Restaurant Model
- `id` - Primary key (UUID)
- `name` - Restaurant name
- `phone_number` - Unique phone number
- `timezone` - Restaurant timezone
- `vapi_assistant_id` - Vapi integration
- `created_at`, `updated_at` - Timestamps

## Usage Examples

### Owner Signup Flow
1. POST `/v1/auth/owner/signup` with owner details
2. Creates User, Restaurant, and Policy records
3. Returns JWT token and user/restaurant data

### Login Flow
1. POST `/v1/auth/login` with email and password
2. Validates credentials (external auth assumed)
3. Returns JWT token and user data

### Onboarding Flow
1. POST `/v1/auth/onboarding/complete` with restaurant details
2. Updates Restaurant and Policy records
3. Marks user onboarding as complete

### Dashboard Access
1. GET `/v1/auth/dashboard` with valid JWT token
2. Returns user info, restaurant data, and available features

## Environment Variables

Add to your `.env` file:
```env
SECRET_KEY=your_secret_key_here
```

## Dependencies

The authentication system requires these additional packages:
- `python-jose[cryptography]>=3.3.0` - JWT handling
- `passlib[bcrypt]>=1.7.4` - Password hashing
- `python-multipart>=0.0.6` - Form data handling
- `email-validator>=2.1.0` - Email validation

## Security Considerations

1. **Secret Key**: Use a strong, unique SECRET_KEY in production
2. **HTTPS**: Always use HTTPS in production for token transmission
3. **Token Storage**: Store JWT tokens securely on the client side
4. **Password Policy**: Enforce strong password requirements
5. **Input Validation**: All inputs are validated using Pydantic schemas
6. **SQL Injection**: Using SQLAlchemy ORM prevents SQL injection
7. **XSS Protection**: Security headers are added automatically

## Testing

The authentication system includes comprehensive error handling and validation. Test with various scenarios:

- Valid owner signup
- Duplicate email attempts
- Invalid password formats
- Invalid JWT tokens
- Unauthorized access attempts

## Future Enhancements

To extend the authentication system:

1. **Email Integration**: Implement actual email sending
2. **Rate Limiting**: Add rate limiting to prevent brute force attacks
3. **Session Management**: Implement refresh token flow
4. **Audit Logging**: Add comprehensive audit logging
5. **Multi-factor Authentication**: Add 2FA support
6. **Social Login**: Integrate OAuth providers (Google, Facebook, etc.)
7. **Staff Management**: Re-enable staff invite system when needed

## Support

For questions or issues with the authentication system, please refer to the code documentation.
