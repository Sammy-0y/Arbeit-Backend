# Arbeit Talent Portal - API Reference

## Base URL
```
Production: https://your-domain.com/api
Development: http://localhost:8001/api
```

## Authentication

All API endpoints (except login/register) require JWT authentication.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## Authentication Endpoints

### Login
```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "email": "user@example.com",
    "name": "John Doe",
    "role": "admin",
    "client_id": null
  },
  "must_change_password": false
}
```

### Change Password
```http
POST /api/auth/change-password
```

**Request Body:**
```json
{
  "current_password": "oldPassword123",
  "new_password": "newPassword456"
}
```

---

## Interview Endpoints

### Create Interview (Schedule Round)
```http
POST /api/interviews
```

**Request Body:**
```json
{
  "job_id": "job_abc123",
  "candidate_id": "cand_xyz789",
  "interview_mode": "Video",
  "interview_duration": 60,
  "time_zone": "Asia/Kolkata",
  "interview_round": 1,
  "round_name": "Technical Round",
  "proposed_slots": [
    {
      "start_time": "2026-02-01T10:00:00+05:30",
      "end_time": "2026-02-01T11:00:00+05:30"
    },
    {
      "start_time": "2026-02-02T14:00:00+05:30",
      "end_time": "2026-02-02T15:00:00+05:30"
    }
  ],
  "additional_instructions": "Please have your code samples ready"
}
```

**Response (201):**
```json
{
  "interview_id": "int_123abc",
  "job_id": "job_abc123",
  "candidate_id": "cand_xyz789",
  "interview_status": "Awaiting Candidate Confirmation",
  "interview_round": 1,
  "round_name": "Technical Round",
  "proposed_slots": [...],
  "created_at": "2026-01-26T10:00:00Z"
}
```

### Book Slot (Candidate Action)
```http
POST /api/interviews/{interview_id}/book-slot
```

**Request Body:**
```json
{
  "slot_id": "slot_001",
  "confirmed": true
}
```

### Send Calendar Invite
```http
POST /api/interviews/{interview_id}/send-invite
```

**Request Body:**
```json
{
  "meeting_link": "https://meet.google.com/abc-def-ghi",
  "interview_mode": "Video",
  "duration_minutes": 60,
  "auto_create_calendar_event": true
}
```

**Response:**
```json
{
  "message": "Interview invitation sent successfully",
  "interview_id": "int_123abc",
  "email_sent": true,
  "calendar_event_created": true
}
```

### Move to Next Round
```http
POST /api/interviews/{interview_id}/move-to-next-round
```

**Request Body:**
```json
{
  "feedback": "Strong technical skills, good communication",
  "rating": 4,
  "next_round_name": "Manager Round"
}
```

**Response:**
```json
{
  "message": "Candidate passed Round 1. Ready for Round 2.",
  "interview_id": "int_123abc",
  "current_round": 1,
  "next_round": 2,
  "candidate_id": "cand_xyz789",
  "status": "Passed"
}
```

### Reject Candidate
```http
POST /api/interviews/{interview_id}/reject
```

**Request Body:**
```json
{
  "feedback": "Did not meet technical requirements",
  "rating": 2
}
```

### Initiate Hiring
```http
POST /api/interviews/{interview_id}/initiate-hiring
```

**Request Body:**
```json
{
  "feedback": "Excellent candidate, recommended for hire",
  "rating": 5,
  "salary_offered": "15 LPA",
  "joining_date": "2026-03-01",
  "offer_notes": "Senior Developer position"
}
```

**Response:**
```json
{
  "message": "Hiring initiated for candidate after 3 round(s)",
  "interview_id": "int_123abc",
  "candidate_id": "cand_xyz789",
  "candidate_name": "John Doe",
  "status": "SELECTED",
  "rounds_cleared": 3,
  "salary_offered": "15 LPA",
  "joining_date": "2026-03-01"
}
```

### Get Interview History
```http
GET /api/candidates/{candidate_id}/interview-history
```

**Response:**
```json
{
  "candidate_id": "cand_xyz789",
  "candidate_name": "John Doe",
  "candidate_status": "IN_PROGRESS",
  "total_rounds": 2,
  "current_round": 3,
  "interviews": [
    {
      "interview_id": "int_001",
      "round": 1,
      "round_name": "Technical Round",
      "status": "Passed",
      "scheduled_time": "2026-01-15T10:00:00Z",
      "feedback": "Strong coding skills",
      "rating": 4,
      "interview_mode": "Video"
    },
    {
      "interview_id": "int_002",
      "round": 2,
      "round_name": "System Design",
      "status": "Passed",
      "scheduled_time": "2026-01-20T14:00:00Z",
      "feedback": "Good architecture thinking",
      "rating": 5,
      "interview_mode": "Video"
    }
  ]
}
```

---

## Portal Management Endpoints

### List Portal Users
```http
GET /api/admin/candidate-portal-users
```

**Query Parameters:**
- `search` (optional): Search by name/email/phone
- `status` (optional): `active`, `inactive`, or `all`

### Create Portal User
```http
POST /api/admin/candidate-portal-users
```

**Request Body:**
```json
{
  "email": "candidate@example.com",
  "name": "Jane Doe",
  "phone": "+91 98765 43210",
  "linkedin_url": "https://linkedin.com/in/janedoe",
  "current_company": "Tech Corp",
  "experience_years": 5,
  "send_welcome_email": true
}
```

### Reset Portal Password
```http
POST /api/admin/candidate-portal-users/{portal_id}/reset-password
```

**Response:**
```json
{
  "message": "Password reset email sent to candidate@example.com"
}
```

---

## Candidate Endpoints

### Update Candidate Status
```http
PUT /api/candidates/{candidate_id}
```

**Request Body:**
```json
{
  "status": "SHORTLISTED"
}
```

**Note:** Status change triggers notification to recruiters.

### Delete Candidate
```http
DELETE /api/candidates/{candidate_id}
```

---

## Client User Management

### Create Client User
```http
POST /api/clients/{client_id}/users
```

**Request Body:**
```json
{
  "email": "user@client.com",
  "password": "tempPass123",
  "name": "Client User",
  "phone": "+91 98765 43210"
}
```

**Note:** Welcome email with credentials is automatically sent.

### Update Client User
```http
PUT /api/clients/{client_id}/users/{user_email}
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "phone": "+91 12345 67890",
  "email": "newemail@client.com"
}
```

**Note:** If email is changed, new credentials email is sent.

---

## Dashboard Stats

### Get Dashboard Statistics
```http
GET /api/dashboard/stats
```

**Response:**
```json
{
  "clients": 12,
  "jobs": 25,
  "candidates": 150,
  "interviews": {
    "total": 45,
    "awaiting_confirmation": 5,
    "confirmed": 8,
    "scheduled": 12,
    "completed": 15,
    "no_shows": 2,
    "cancelled": 3
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request body"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid email or password"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

---

## Rate Limits

- Standard: 100 requests/minute
- Bulk operations: 10 requests/minute
- File uploads: 5 requests/minute

---

*Last Updated: January 2026*
