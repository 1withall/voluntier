# API Documentation

This document provides comprehensive documentation for the Voluntier REST API. The API follows RESTful design principles and provides endpoints for managing users, events, documents, and security features.

## Base URL

```
Development: http://localhost:8080/api/v1
Production: https://api.voluntier.org/api/v1
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "user_type": "individual",
    "verification_status": "verified"
  }
}
```

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer <token>
```

## User Management

### User Registration

#### Individual User Registration
```http
POST /users/register/individual
Content-Type: application/json

{
  "email": "volunteer@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-01",
  "skills": ["First Aid", "Event Planning"],
  "interests": ["Environment", "Education"],
  "availability": {
    "weekdays": true,
    "weekends": true,
    "hours_per_week": 10
  },
  "references": [
    {
      "name": "Jane Smith",
      "email": "jane@example.com",
      "relationship": "Former Supervisor"
    }
  ]
}
```

#### Organization Registration
```http
POST /users/register/organization
Content-Type: application/json

{
  "email": "contact@organization.org",
  "password": "securepassword",
  "organization_name": "Community Food Bank",
  "organization_type": "Non-profit",
  "mission_statement": "Fighting hunger in our community",
  "website": "https://foodbank.org",
  "phone": "+1234567890",
  "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "ST",
    "zip_code": "12345",
    "country": "US"
  },
  "contact_person": {
    "name": "Sarah Johnson",
    "title": "Volunteer Coordinator",
    "email": "sarah@foodbank.org",
    "phone": "+1234567891"
  },
  "registration_documents": ["tax_exempt_certificate", "organization_charter"]
}
```

#### Business Registration
```http
POST /users/register/business
Content-Type: application/json

{
  "email": "csr@company.com",
  "password": "securepassword",
  "company_name": "Tech Solutions Inc",
  "industry": "Technology",
  "company_size": "51-200",
  "website": "https://techsolutions.com",
  "csr_mission": "Supporting local education and technology access",
  "employee_volunteer_program": true,
  "contact_person": {
    "name": "Michael Chen",
    "title": "CSR Manager",
    "email": "michael@techsolutions.com",
    "phone": "+1234567892"
  },
  "address": {
    "street": "456 Business Blvd",
    "city": "Anytown",
    "state": "ST",
    "zip_code": "12345",
    "country": "US"
  }
}
```

### User Profile Management

#### Get User Profile
```http
GET /users/profile
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "user123",
  "email": "volunteer@example.com",
  "user_type": "individual",
  "verification_status": "verified",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "skills": ["First Aid", "Event Planning"],
    "volunteer_hours": 45,
    "events_attended": 12,
    "verification_documents": ["government_id", "skill_certificates"]
  }
}
```

#### Update User Profile
```http
PUT /users/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "skills": ["First Aid", "Event Planning", "Translation"],
  "availability": {
    "weekdays": true,
    "weekends": false,
    "hours_per_week": 15
  }
}
```

## Event Management

### Events

#### List Events
```http
GET /events?category=environment&skills=first_aid&location=city&date_from=2024-01-01&date_to=2024-12-31&limit=20&offset=0
Authorization: Bearer <token>
```

**Query Parameters:**
- `category`: Filter by event category
- `skills`: Filter by required skills (comma-separated)
- `location`: Filter by location/city
- `date_from`: Filter events after this date (ISO format)
- `date_to`: Filter events before this date (ISO format)
- `limit`: Number of events to return (default: 20)
- `offset`: Number of events to skip (default: 0)

**Response:**
```json
{
  "events": [
    {
      "id": "event123",
      "title": "Community Park Cleanup",
      "description": "Join us for a morning of environmental stewardship",
      "organization": {
        "id": "org456",
        "name": "Green Earth Society",
        "verified": true
      },
      "date": "2024-02-15",
      "start_time": "09:00:00",
      "end_time": "13:00:00",
      "location": {
        "name": "Central Park",
        "address": "123 Park Ave, Anytown, ST",
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "volunteers_needed": 30,
      "volunteers_registered": 18,
      "skills_required": ["Physical Work"],
      "category": "Environment",
      "verified": true,
      "registration_deadline": "2024-02-13T23:59:59Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Event Details
```http
GET /events/{event_id}
Authorization: Bearer <token>
```

#### Create Event (Organizations only)
```http
POST /events
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Food Drive Coordination",
  "description": "Help sort and distribute food donations to families in need",
  "date": "2024-03-01",
  "start_time": "10:00:00",
  "end_time": "16:00:00",
  "location": {
    "name": "Community Center",
    "address": "789 Community St, Anytown, ST",
    "latitude": 40.7589,
    "longitude": -73.9851
  },
  "volunteers_needed": 15,
  "skills_required": ["Organization", "Communication"],
  "category": "Social Services",
  "registration_deadline": "2024-02-28T23:59:59Z",
  "special_instructions": "Please wear comfortable clothes and closed-toe shoes",
  "contact_info": {
    "name": "Sarah Johnson",
    "phone": "+1234567891",
    "email": "sarah@foodbank.org"
  }
}
```

#### Register for Event
```http
POST /events/{event_id}/register
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "I'm excited to help with this event!",
  "emergency_contact": {
    "name": "Jane Doe",
    "phone": "+1234567890",
    "relationship": "Spouse"
  }
}
```

#### Unregister from Event
```http
DELETE /events/{event_id}/register
Authorization: Bearer <token>
```

## Document Management

### Document Upload

#### Upload Document
```http
POST /documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary_file_data>
document_type: government_id
description: Driver's License for identity verification
```

**Supported Document Types:**
- `government_id`: Government-issued identification
- `skill_certificate`: Professional or skill certifications
- `background_check`: Background check documentation
- `reference_letter`: Reference letters
- `tax_exempt_certificate`: Tax exemption documents (organizations)
- `business_license`: Business licenses and permits

**Response:**
```json
{
  "document_id": "doc123",
  "document_type": "government_id",
  "filename": "drivers_license.pdf",
  "file_size": 2048576,
  "upload_status": "success",
  "verification_status": "pending",
  "uploaded_at": "2024-01-15T14:30:00Z",
  "processing_results": {
    "virus_scan": "clean",
    "format_validation": "valid",
    "content_analysis": "pending"
  }
}
```

#### Bulk Document Upload
```http
POST /documents/bulk-upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

files: <multiple_binary_files>
document_types: ["government_id", "skill_certificate", "reference_letter"]
```

#### Get Document Status
```http
GET /documents/{document_id}
Authorization: Bearer <token>
```

#### List User Documents
```http
GET /documents?status=verified&type=government_id&limit=10&offset=0
Authorization: Bearer <token>
```

### Document Verification

#### Get Verification Status
```http
GET /documents/{document_id}/verification
Authorization: Bearer <token>
```

**Response:**
```json
{
  "document_id": "doc123",
  "verification_status": "verified",
  "verification_date": "2024-01-16T10:00:00Z",
  "verification_results": {
    "authenticity_score": 0.95,
    "content_match": true,
    "quality_assessment": "high",
    "extracted_data": {
      "name": "John Doe",
      "id_number": "***-***-1234",
      "expiration_date": "2028-01-15"
    }
  },
  "verifier_notes": "Document verified successfully",
  "appeals_available": false
}
```

## Verification System

### QR Code Verification

#### Generate QR Code for Verification
```http
POST /verification/qr-code/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "verification_type": "in_person",
  "purpose": "volunteer_registration",
  "expires_in": 3600
}
```

**Response:**
```json
{
  "qr_code_id": "qr123",
  "qr_code_data": "voluntier://verify/qr123/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2024-01-15T16:00:00Z",
  "verification_url": "https://app.voluntier.org/verify/qr123"
}
```

#### Scan QR Code
```http
POST /verification/qr-code/scan
Authorization: Bearer <token>
Content-Type: application/json

{
  "qr_code_data": "voluntier://verify/qr123/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  }
}
```

### Reference Verification

#### Request Reference
```http
POST /verification/references/request
Authorization: Bearer <token>
Content-Type: application/json

{
  "reference_email": "reference@example.com",
  "reference_name": "Jane Smith",
  "relationship": "Former Supervisor",
  "message": "Please provide a reference for my volunteer application"
}
```

#### Submit Reference Response
```http
POST /verification/references/{reference_id}/submit
Content-Type: application/json

{
  "reference_token": "ref_token_123",
  "responses": {
    "reliability": 5,
    "communication": 4,
    "teamwork": 5,
    "recommendation": true,
    "comments": "John is a reliable and dedicated volunteer"
  }
}
```

## Notification System

### Notifications

#### Get User Notifications
```http
GET /notifications?status=unread&category=event&limit=20&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "notifications": [
    {
      "id": "notif123",
      "type": "event_reminder",
      "title": "Event Reminder: Community Park Cleanup",
      "message": "Your volunteer event is tomorrow at 9:00 AM",
      "status": "unread",
      "priority": "normal",
      "created_at": "2024-01-14T18:00:00Z",
      "scheduled_for": "2024-01-14T18:00:00Z",
      "metadata": {
        "event_id": "event123",
        "event_title": "Community Park Cleanup",
        "event_date": "2024-02-15"
      }
    }
  ],
  "total_unread": 3,
  "total": 15
}
```

#### Mark Notification as Read
```http
PUT /notifications/{notification_id}/read
Authorization: Bearer <token>
```

#### Update Notification Preferences
```http
PUT /notifications/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "email_notifications": {
    "event_reminders": true,
    "registration_confirmations": true,
    "verification_updates": true,
    "security_alerts": true
  },
  "push_notifications": {
    "event_reminders": true,
    "urgent_alerts": true
  },
  "frequency": {
    "digest": "weekly",
    "immediate": ["security_alerts", "urgent_updates"]
  }
}
```

## Security

### Security Dashboard

#### Get Security Overview
```http
GET /security/dashboard
Authorization: Bearer <token>
```

**Response:**
```json
{
  "security_score": 85,
  "active_sessions": 2,
  "recent_logins": [
    {
      "timestamp": "2024-01-15T14:30:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "location": "Anytown, ST",
      "success": true
    }
  ],
  "security_events": [
    {
      "type": "login_attempt",
      "severity": "low",
      "timestamp": "2024-01-15T14:25:00Z",
      "description": "Failed login attempt from new location"
    }
  ],
  "verification_status": {
    "identity": "verified",
    "background_check": "pending",
    "references": "verified"
  }
}
```

#### List Security Events
```http
GET /security/events?severity=high&type=authentication&limit=50&offset=0
Authorization: Bearer <token>
```

#### Terminate Session
```http
DELETE /security/sessions/{session_id}
Authorization: Bearer <token>
```

### Threat Analysis

#### Analyze Potential Threat
```http
POST /security/analyze-threat
Authorization: Bearer <token>
Content-Type: application/json

{
  "ip_address": "192.168.1.200",
  "user_agent": "Suspicious Bot/1.0",
  "request_pattern": "rapid_requests",
  "additional_context": "Multiple failed login attempts"
}
```

## Analytics and Reporting

### User Analytics

#### Get User Impact Summary
```http
GET /analytics/impact
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_volunteer_hours": 156,
  "events_participated": 23,
  "impact_metrics": {
    "people_helped": 45,
    "projects_completed": 8,
    "community_rating": 4.8
  },
  "skill_development": [
    {
      "skill": "Event Planning",
      "level": "Intermediate",
      "hours_practiced": 32
    }
  ],
  "achievements": [
    {
      "id": "dedication_badge",
      "name": "Dedication Badge",
      "description": "Volunteered for 50+ hours",
      "earned_date": "2024-01-10T00:00:00Z"
    }
  ]
}
```

### Organization Analytics

#### Get Organization Metrics
```http
GET /analytics/organization
Authorization: Bearer <token>
```

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content returned
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate email)
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided data is invalid",
    "details": [
      {
        "field": "email",
        "message": "Email address is required"
      },
      {
        "field": "password",
        "message": "Password must be at least 8 characters"
      }
    ],
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_FAILED`: Invalid credentials
- `AUTHORIZATION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `DUPLICATE_RESOURCE`: Resource already exists
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `FILE_UPLOAD_ERROR`: File upload failed
- `VERIFICATION_FAILED`: Document or identity verification failed
- `SECURITY_VIOLATION`: Security policy violation

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **General API**: 1000 requests per hour per user
- **Authentication**: 10 login attempts per 15 minutes per IP
- **File Upload**: 50 uploads per hour per user
- **Security Events**: 100 requests per hour per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642694400
```

## Webhooks

### Event Notifications

Organizations can configure webhooks to receive real-time notifications:

```http
POST /webhooks/configure
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks/voluntier",
  "events": ["volunteer_registered", "event_completed", "verification_completed"],
  "secret": "your_webhook_secret"
}
```

### Webhook Payload Example

```json
{
  "event": "volunteer_registered",
  "timestamp": "2024-01-15T14:30:00Z",
  "data": {
    "event_id": "event123",
    "volunteer_id": "user456",
    "registration_date": "2024-01-15T14:30:00Z"
  },
  "signature": "sha256=abc123..."
}
```

## SDK and Client Libraries

### Official SDKs

- **JavaScript/TypeScript**: `@voluntier/sdk-js`
- **Python**: `voluntier-sdk-python`
- **React**: `@voluntier/react-components`

### Example Usage (JavaScript)

```javascript
import { VoluntierAPI } from '@voluntier/sdk-js'

const client = new VoluntierAPI({
  baseURL: 'https://api.voluntier.org/api/v1',
  token: 'your_access_token'
})

// Get user profile
const profile = await client.users.getProfile()

// List events
const events = await client.events.list({
  category: 'environment',
  limit: 10
})

// Register for event
await client.events.register('event123', {
  message: 'Excited to participate!'
})
```

## Testing

### Test Environment

A test environment is available for development and testing:
- **Base URL**: `https://api-test.voluntier.org/api/v1`
- **Test Data**: Pre-populated with sample users, events, and organizations
- **Rate Limits**: Relaxed for testing purposes

### Test Accounts

Test accounts are available for different user types:
- **Individual**: `test_individual@voluntier.org` / `1Fake_passw0rd.`
- **Organization**: `test_organization@voluntier.org` / `1Fake_passw0rd.`
- **Business**: `test_business@voluntier.org` / `1Fake_passw0rd.`

### API Testing Tools

- **Postman Collection**: Available for download with example requests
- **OpenAPI Spec**: Interactive documentation at `/docs`
- **curl Examples**: Command-line examples for all endpoints

---

For additional support and detailed examples, visit our [GitHub repository](https://github.com/voluntier/voluntier) or contact our development team.