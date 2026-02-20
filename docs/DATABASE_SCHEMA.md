# Arbeit Talent Portal - Database Schema & API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Database Collections](#database-collections)
3. [API Endpoints](#api-endpoints)
4. [Authentication Flow](#authentication-flow)
5. [Multi-Round Interview Flow](#multi-round-interview-flow)
6. [Notification System](#notification-system)

---

## Overview

Arbeit Talent Portal is a multi-tenant recruitment management system built with:
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Frontend**: React with Tailwind CSS
- **Authentication**: JWT-based with two separate flows (Internal Users & Candidate Portal)

---

## Database Collections

### 1. `users` - Internal Users (Admin, Recruiter, Client Users)

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | Unique identifier (e.g., `user_abc123`) |
| `email` | string | Email address (login ID) |
| `password_hash` | string | bcrypt hashed password |
| `name` | string | Full name |
| `phone` | string | Phone number (optional) |
| `role` | string | `admin`, `recruiter`, or `client_user` |
| `client_id` | string | For client_user only - links to clients collection |
| `must_change_password` | boolean | Force password change on next login |
| `created_at` | ISO datetime | Account creation timestamp |
| `created_by` | string | Email of creator |

**Used in:**
- `/api/auth/login` - User authentication
- `/api/auth/register` - User registration
- `/api/clients/{client_id}/users` - Client user management
- `/api/auth/change-password` - Password change

---

### 2. `clients` - Client Companies

| Field | Type | Description |
|-------|------|-------------|
| `client_id` | string | Unique identifier (e.g., `client_001`) |
| `company_name` | string | Company name |
| `status` | string | `active` or `inactive` |
| `industry` | string | Industry sector (optional) |
| `website` | string | Company website (optional) |
| `phone` | string | Company phone (optional) |
| `address` | string | Street address (optional) |
| `city` | string | City (optional) |
| `state` | string | State/Province (optional) |
| `country` | string | Country (optional) |
| `postal_code` | string | ZIP/Postal code (optional) |
| `notes` | string | Internal notes (optional) |
| `created_at` | ISO datetime | Creation timestamp |

**Used in:**
- `/api/clients` - CRUD operations
- `/api/clients/{client_id}` - Client details
- Dashboard stats

---

### 3. `jobs` - Job Requirements

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Unique identifier (e.g., `job_abc123`) |
| `client_id` | string | Reference to clients collection |
| `title` | string | Job title |
| `description` | string | Job description |
| `department` | string | Department (optional) |
| `location` | string | Job location |
| `employment_type` | string | `full_time`, `part_time`, `contract`, `internship` |
| `experience_min` | integer | Minimum years of experience |
| `experience_max` | integer | Maximum years of experience |
| `salary_min` | number | Minimum salary (optional) |
| `salary_max` | number | Maximum salary (optional) |
| `required_skills` | array[string] | List of required skills |
| `nice_to_have_skills` | array[string] | Nice-to-have skills (optional) |
| `status` | string | `open`, `closed`, `on_hold`, `filled` |
| `priority` | string | `low`, `medium`, `high`, `urgent` |
| `openings` | integer | Number of positions |
| `created_at` | ISO datetime | Creation timestamp |
| `created_by` | string | Creator's email |

**Used in:**
- `/api/jobs` - CRUD operations
- `/api/jobs/{job_id}/candidates` - Candidates for a job
- Dashboard stats

---

### 4. `candidates` - Candidate Profiles

| Field | Type | Description |
|-------|------|-------------|
| `candidate_id` | string | Unique identifier (e.g., `cand_abc123`) |
| `job_id` | string | Reference to jobs collection |
| `name` | string | Full name |
| `email` | string | Email address |
| `phone` | string | Phone number |
| `linkedin` | string | LinkedIn URL (optional) |
| `current_role` | string | Current job title (optional) |
| `skills` | array[string] | List of skills |
| `experience` | array[object] | Work experience entries |
| `education` | array[object] | Education entries |
| `summary` | string | Professional summary |
| `cv_file_url` | string | Uploaded CV file path |
| `ai_story` | object | AI-generated candidate story |
| `status` | string | `NEW`, `IN_REVIEW`, `IN_PROGRESS`, `SHORTLISTED`, `REJECTED`, `SELECTED` |
| `current_round` | integer | Current interview round |
| `candidate_portal_id` | string | Link to portal user (optional) |
| `selected_at` | ISO datetime | Selection timestamp (optional) |
| `salary_offered` | string | Offered salary (optional) |
| `created_at` | ISO datetime | Creation timestamp |
| `created_by` | string | Creator's email |

**Used in:**
- `/api/jobs/{job_id}/candidates` - Candidate listing
- `/api/candidates/{candidate_id}` - Candidate details
- `/api/candidates/{candidate_id}/interview-history` - Interview rounds

---

### 5. `interviews` - Interview Records

| Field | Type | Description |
|-------|------|-------------|
| `interview_id` | string | Unique identifier (e.g., `int_abc123`) |
| `job_id` | string | Reference to jobs collection |
| `candidate_id` | string | Reference to candidates collection |
| `client_id` | string | Reference to clients collection |
| `interview_mode` | string | `Video`, `Phone`, or `Onsite` |
| `interview_duration` | integer | Duration in minutes |
| `time_zone` | string | Time zone (default: `Asia/Kolkata`) |
| `proposed_slots` | array[object] | Available time slots |
| `selected_slot_id` | string | Chosen slot ID (optional) |
| `scheduled_start_time` | ISO datetime | Scheduled start (optional) |
| `scheduled_end_time` | ISO datetime | Scheduled end (optional) |
| `interview_status` | string | See status values below |
| `interview_round` | integer | Round number (1, 2, 3...) |
| `round_name` | string | Round name (e.g., "Technical Round") |
| `meeting_link` | string | Video meeting URL (optional) |
| `additional_instructions` | string | Instructions (optional) |
| `invite_sent` | boolean | Whether invite email was sent |
| `invite_sent_by` | string | Who sent the invite |
| `feedback` | string | Interviewer feedback (optional) |
| `rating` | integer | Rating 1-5 (optional) |
| `no_show_flag` | boolean | Whether candidate didn't show |
| `no_show_count` | integer | Count of no-shows |
| `hiring_initiated` | boolean | Hiring process started |
| `created_at` | ISO datetime | Creation timestamp |
| `updated_at` | ISO datetime | Last update timestamp |
| `created_by` | string | Creator's email |

**Interview Status Values:**
- `Draft` - Not yet sent to candidate
- `Awaiting Candidate Confirmation` - Waiting for candidate to select slot
- `Confirmed` - Candidate confirmed slot
- `Scheduled` - Interview scheduled with calendar invite
- `Completed` - Interview completed, pending decision
- `Passed` - Candidate passed this round
- `Failed` - Candidate failed this round
- `No Show` - Candidate didn't attend
- `Cancelled` - Interview cancelled

**Used in:**
- `/api/interviews` - CRUD operations
- `/api/interviews/{id}/book-slot` - Slot booking
- `/api/interviews/{id}/move-to-next-round` - Round progression
- `/api/interviews/{id}/initiate-hiring` - Start hiring
- Dashboard pipeline stats

---

### 6. `candidate_portal_users` - Candidate Portal Accounts

| Field | Type | Description |
|-------|------|-------------|
| `candidate_portal_id` | string | Unique identifier (e.g., `cp_abc123`) |
| `email` | string | Email address (login ID) |
| `password_hash` | string | bcrypt hashed password |
| `name` | string | Full name |
| `phone` | string | Phone number |
| `linkedin_url` | string | LinkedIn profile (optional) |
| `current_company` | string | Current employer (optional) |
| `experience_years` | integer | Years of experience (optional) |
| `must_change_password` | boolean | Force password change |
| `status` | string | `active` or `inactive` |
| `linked_candidate_id` | string | Link to candidates collection |
| `created_at` | ISO datetime | Creation timestamp |
| `created_by` | string | Creator's email |

**Used in:**
- `/api/candidate-portal/login` - Candidate login
- `/api/candidate-portal/me` - Get current candidate
- `/api/admin/candidate-portal-users` - Admin management

---

### 7. `notifications` - In-App Notifications

| Field | Type | Description |
|-------|------|-------------|
| `notification_id` | string | Unique identifier |
| `type` | string | Notification type |
| `title` | string | Notification title |
| `message` | string | Notification body |
| `entity_type` | string | `candidate`, `interview`, `job` |
| `entity_id` | string | Related entity ID |
| `created_at` | ISO datetime | Creation timestamp |
| `read` | boolean | Read status |
| `recipients` | array[string] | Target roles/client_ids |

**Notification Types:**
- `candidate_status_change` - Candidate status updated
- `interview_booked` - Interview slot confirmed
- `interview_passed` - Candidate passed round
- `hiring_initiated` - Hiring process started
- `new_job` - New job posted

---

### 8. `audit_logs` - System Audit Trail

| Field | Type | Description |
|-------|------|-------------|
| `log_id` | string | Unique identifier |
| `timestamp` | ISO datetime | Event timestamp |
| `user_id` | string | Acting user ID |
| `user_email` | string | Acting user email |
| `user_role` | string | Acting user role |
| `action_type` | string | Action performed |
| `entity_type` | string | Affected entity type |
| `entity_id` | string | Affected entity ID |
| `client_id` | string | Related client (optional) |
| `old_value` | object | Previous state (optional) |
| `new_value` | object | New state (optional) |
| `metadata` | object | Additional context |

**Action Types:**
- `USER_LOGIN`, `USER_LOGOUT`
- `CLIENT_CREATE`, `CLIENT_UPDATE`, `CLIENT_DELETE`
- `JOB_CREATE`, `JOB_UPDATE`, `JOB_STATUS_CHANGE`
- `CANDIDATE_CREATE`, `CANDIDATE_STATUS_CHANGE`
- `INTERVIEW_CREATE`, `INTERVIEW_COMPLETED`, `INTERVIEW_PASSED`, `INTERVIEW_FAILED`
- `HIRING_INITIATED`

---

### 9. `roles` - Custom RBAC Roles

| Field | Type | Description |
|-------|------|-------------|
| `role_id` | string | Unique identifier |
| `role_name` | string | Role name |
| `description` | string | Role description |
| `permissions` | object | Permission flags |
| `client_id` | string | Client-specific role (optional) |
| `is_system_role` | boolean | System-defined role |
| `created_at` | ISO datetime | Creation timestamp |

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login and get JWT token |
| POST | `/api/auth/register` | Register new user |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/auth/change-password` | Change password |

### Candidate Portal Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/candidate-portal/login` | Candidate login |
| POST | `/api/candidate-portal/register` | Candidate registration |
| GET | `/api/candidate-portal/me` | Get current candidate |
| POST | `/api/candidate-portal/change-password` | Change password |

### Clients
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/clients` | List all clients |
| POST | `/api/clients` | Create new client |
| GET | `/api/clients/{id}` | Get client details |
| PUT | `/api/clients/{id}` | Update client |
| GET | `/api/clients/{id}/users` | List client users |
| POST | `/api/clients/{id}/users` | Create client user |
| PUT | `/api/clients/{id}/users/{email}` | Update client user |
| DELETE | `/api/clients/{id}/users/{email}` | Delete client user |

### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | List jobs |
| POST | `/api/jobs` | Create job |
| GET | `/api/jobs/{id}` | Get job details |
| PUT | `/api/jobs/{id}` | Update job |
| GET | `/api/jobs/{id}/candidates` | List candidates for job |

### Candidates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/candidates` | List all candidates |
| POST | `/api/jobs/{job_id}/candidates` | Upload CV/create candidate |
| GET | `/api/candidates/{id}` | Get candidate details |
| PUT | `/api/candidates/{id}` | Update candidate |
| DELETE | `/api/candidates/{id}` | Delete candidate |
| GET | `/api/candidates/{id}/interview-history` | Get all interview rounds |
| POST | `/api/candidates/{id}/send-selection-notification` | Send portal credentials |

### Interviews
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/interviews` | List interviews |
| POST | `/api/interviews` | Create interview |
| GET | `/api/interviews/{id}` | Get interview details |
| PUT | `/api/interviews/{id}` | Update interview |
| POST | `/api/interviews/{id}/book-slot` | Book time slot |
| POST | `/api/interviews/{id}/send-invite` | Send calendar invite |
| POST | `/api/interviews/{id}/mark-completed` | Mark as completed |
| POST | `/api/interviews/{id}/mark-no-show` | Mark as no-show |
| POST | `/api/interviews/{id}/cancel` | Cancel interview |
| POST | `/api/interviews/{id}/move-to-next-round` | Pass & enable next round |
| POST | `/api/interviews/{id}/reject` | Reject candidate |
| POST | `/api/interviews/{id}/initiate-hiring` | Start hiring process |
| GET | `/api/interviews/stats/pipeline` | Pipeline statistics |

### Admin - Portal Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/candidate-portal-users` | List portal users |
| POST | `/api/admin/candidate-portal-users` | Create portal user |
| PUT | `/api/admin/candidate-portal-users/{id}` | Update portal user |
| DELETE | `/api/admin/candidate-portal-users/{id}` | Delete portal user |
| POST | `/api/admin/candidate-portal-users/{id}/reset-password` | Reset password |

### Governance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/governance/roles` | List roles |
| POST | `/api/governance/roles` | Create role |
| GET | `/api/governance/audit-logs` | Get audit logs |
| GET | `/api/governance/access-matrix` | View access matrix |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Dashboard statistics |
| GET | `/api/notifications` | List notifications |

---

## Multi-Round Interview Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-ROUND INTERVIEW FLOW                    │
└─────────────────────────────────────────────────────────────────┘

1. SCHEDULE ROUND 1
   └─► POST /api/interviews (interview_round: 1)
       └─► Status: "Awaiting Candidate Confirmation"

2. CANDIDATE BOOKS SLOT
   └─► POST /api/interviews/{id}/book-slot
       └─► Status: "Confirmed"

3. SEND CALENDAR INVITE
   └─► POST /api/interviews/{id}/send-invite
       └─► Creates Google Calendar event
       └─► Status: "Scheduled"

4. INTERVIEW COMPLETED
   └─► POST /api/interviews/{id}/mark-completed
       └─► Status: "Completed"

5. CLIENT DECISION
   ├─► PASS: POST /api/interviews/{id}/move-to-next-round
   │   └─► Status: "Passed"
   │   └─► Candidate status: "IN_PROGRESS"
   │   └─► Ready for Round 2
   │
   ├─► FAIL: POST /api/interviews/{id}/reject
   │   └─► Status: "Failed"
   │   └─► Candidate status: "REJECTED"
   │
   └─► HIRE: POST /api/interviews/{id}/initiate-hiring
       └─► Status: "Passed"
       └─► Candidate status: "SELECTED"
       └─► hiring_initiated: true

6. SCHEDULE NEXT ROUND (if passed)
   └─► POST /api/interviews (interview_round: 2)
   └─► Repeat steps 2-5

CANDIDATE STATUS PROGRESSION:
NEW → IN_REVIEW → IN_PROGRESS → SELECTED (or REJECTED)
```

---

## Notification System

### Automatic Triggers

| Event | Recipients | Channel |
|-------|------------|---------|
| Candidate status change | Admin, Recruiter | Email + In-app |
| Interview slot booked | Admin, Recruiter, Client | Email + In-app |
| Interview passed | Admin, Recruiter, Client | In-app |
| Hiring initiated | Admin, Recruiter | Email + In-app |
| New job created | All Recruiters | Email |
| Portal user created | Candidate | Email (credentials) |

### Email Templates

1. **Welcome Email** - New portal user credentials
2. **Interview Invitation** - Calendar invite with meeting link
3. **Selection Notification** - Candidate shortlisted
4. **Status Change** - Candidate status update

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MONGO_URL` | MongoDB connection string |
| `DB_NAME` | Database name |
| `JWT_SECRET` | JWT signing secret |
| `PICA_SECRET_KEY` | Pica API key for email/calendar |
| `PICA_GMAIL_CONNECTION_KEY` | Gmail connection ID |
| `PICA_GOOGLE_CALENDAR_CONNECTION_KEY` | Calendar connection ID |
| `OPENAI_API_KEY` | OpenAI for CV parsing |
| `REACT_APP_BACKEND_URL` | Backend URL for frontend |
| `REACT_APP_FRONTEND_URL` | Frontend URL for emails |

---

*Last Updated: January 2026*
