# Arbeit Talent Portal - Product Requirements Document

## Overview
Arbeit Talent Portal is a multi-tenant web application for recruitment management. It enables recruiters to manage job requirements, upload and parse candidate CVs with AI, and facilitate client review workflows.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React with Tailwind CSS and shadcn/ui
- **Database**: MongoDB
- **Authentication**: JWT with granular RBAC

## User Roles
1. **Admin** - Full system access, can manage all clients and users
2. **Recruiter** - Can manage jobs and candidates across clients
3. **Client User** - Can only view/manage their own client's data

## Test Credentials
- Admin: `connect@arbeit.co.in` / `admin123`
- Recruiter: `recruiter@arbeit.com` / `recruiter123`
- Client User: `client@acme.com` / `client123`
- **Candidate Portal**: `test.candidate@example.com` / `test123`

---

## Implemented Features ✅

### Phase 1: Authentication
- User registration and login
- JWT token-based auth
- Role-based access control

### Phase 2: Client Management
- CRUD operations for clients
- User management per client
- Default role creation for new clients

### Phase 3: Job Requirements
- Job CRUD with tenant isolation
- Enhanced validation (experience, CTC, city, notice period)

### Phase 4: Candidate Management
- CV upload with AI parsing (PDF, DOCX, TXT support)
- **Enhanced CV Parsing (Jan 24, 2026):**
  - Proper PDF text extraction using pdfplumber
  - DOCX parsing using python-docx
  - Improved AI prompt for extracting Email, Phone, LinkedIn, Skills
  - Contact info (email, phone) now reliably extracted
- AI story generation with accurate fit scoring
- **Improved Fit Score Calculation:**
  - Skills match (45% weight) - compares candidate skills to job requirements
  - Experience match (35% weight) - compares years of experience
  - Role alignment (20% weight) - compares current role to job title
  - No longer defaults to 90% - provides realistic assessment
- **Career Timeline** now populated from actual CV experience data
- Candidate CRUD with tenant filtering
- Status workflow

### Phase 5: Client Review Workflow
- Review actions (APPROVE, PIPELINE, REJECT, COMMENT)
- Review history per candidate
- PDF export of candidate stories

### Phase 6: Enterprise Governance ✅
- Client-specific roles with granular permissions
- Audit logging for all critical actions
- User-role assignments
- Access matrix viewer
- CSV export for governance reports
- **Fully functional UI** for all governance features

### Phase 7: Interview Orchestration ✅
**Backend:**
- Interview Creation with multiple time slots
- Slot Booking by candidates
- Status Workflow: Awaiting → Confirmed → Scheduled → Completed/No Show/Cancelled
- No-Show Tracking
- Pipeline Statistics

**Frontend - Calendar Scheduler:**
- Visual calendar for date selection
- Time slot picker
- Interview mode/duration/timezone selectors
- Meeting link and instructions fields
- Interactive slot booking

### Phase 8: Dashboard Enhancements ✅
- **Admin Dashboard**: Quick stats (Clients, Jobs, Candidates, Interviews) + Interview Pipeline widget
- **Client Dashboard**: Quick stats + Interview Pipeline widget
- Pipeline widget shows: Awaiting, Confirmed, Scheduled, Completed, No Shows, Cancelled

### Phase 9: Public Candidate Booking ✅
- **Public booking page** at `/book/:interviewId/:token`
- No login required for candidates
- Shareable booking links with secure tokens
- Candidates can view interview details and select preferred slot
- Automatic confirmation on slot selection

### Phase 10: Simplified CV Viewing ✅
- Direct CV viewing (PDF inline, other formats with Open/Download)
- Removed resume versioning complexity
- Supports all file formats (PDF, Word, images, etc.)

### Phase 11: Notification System (Partial) ✅
- Email notifications via Pica API / Gmail integration
- In-app notifications with notification bell UI
- Recruiters notified on new job creation
- Notification center in recruiter/admin dashboards

### Phase 12: Candidate Portal ✅ (Jan 24, 2026)
**Backend:**
- Candidate registration with validation (Name, Email, Password, Phone required)
- Separate JWT authentication for candidates
- Profile management (`/me` endpoint)
- Interview listing for logged-in candidates
- Slot booking with ownership verification

**Frontend:**
- Login/Registration page at `/candidate/login`
- Toggle between Sign In and Create Account modes
- Registration form with all fields:
  - Full Name (required)
  - Phone Number (required)
  - Email Address (required)
  - Password (required)
  - LinkedIn URL (optional)
  - Current Company (optional)
  - Experience Years (optional)
- Protected Dashboard at `/candidate/dashboard`
- Interview stats: Pending Action, Upcoming, Completed
- Interview cards with company/job details
- Slot selection modal with time options
- Interview booking confirmation

### Phase 13: Selection Notification System ✅ (Jan 24, 2026)
**Complete Workflow:**
1. Client shortlists candidate → Admin clicks "Send Selection Notification"
2. System creates candidate portal account (if not exists)
3. Email sent to candidate with:
   - Congratulations message
   - Job position and company details
   - Portal login URL
   - Email/Username
   - Temporary password
   - Instructions to change password on first login
4. Candidate status auto-updated to SHORTLISTED
5. First login prompts password change (security)

**Backend Endpoints:**
- `POST /api/candidates/{id}/send-selection-notification` - Triggers notification
- `POST /api/candidate-portal/change-password` - Password change for first login
- `must_change_password` flag on candidate portal users

**Email Template:**
- Professional HTML email with branded header
- Credentials box with portal URL, email, temp password
- Warning about password change requirement
- Next steps guide (4 steps to interview booking)

---

## API Endpoints Summary

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login and get JWT
- `GET /api/auth/me` - Get current user

### Clients
- `GET /api/clients` - List clients
- `POST /api/clients` - Create client
- `GET /api/clients/{id}` - Get client
- `PUT /api/clients/{id}` - Update client
- `DELETE /api/clients/{id}` - Delete client

### Jobs
- `GET /api/jobs` - List jobs
- `POST /api/jobs` - Create job
- `GET /api/jobs/{id}` - Get job
- `PUT /api/jobs/{id}` - Update job
- `DELETE /api/jobs/{id}` - Delete job

### Candidates
- `POST /api/candidates/upload` - Upload CV
- `GET /api/jobs/{id}/candidates` - List candidates
- `GET /api/candidates/{id}` - Get candidate
- `PUT /api/candidates/{id}` - Update candidate
- `DELETE /api/candidates/{id}` - Delete candidate

### Interviews
- `POST /api/interviews` - Create interview
- `GET /api/interviews` - List interviews
- `GET /api/interviews/{id}` - Get interview
- `PUT /api/interviews/{id}` - Update interview
- `POST /api/interviews/{id}/book-slot` - Book slot (authenticated)
- `POST /api/interviews/{id}/send-invite` - Send invite
- `POST /api/interviews/{id}/mark-completed` - Mark completed
- `POST /api/interviews/{id}/mark-no-show` - Mark no-show
- `POST /api/interviews/{id}/cancel` - Cancel
- `GET /api/interviews/stats/pipeline` - Pipeline statistics
- `GET /api/interviews/{id}/booking-link` - Get shareable booking link

### Public Booking (No Auth)
- `GET /api/public/interviews/{id}?token=xxx` - Get interview details
- `POST /api/public/interviews/{id}/book?slot_id=xxx&token=xxx` - Book slot

### Candidate Portal
- `POST /api/candidate-portal/register` - Register new candidate
- `POST /api/candidate-portal/login` - Candidate login
- `GET /api/candidate-portal/me` - Get candidate profile
- `GET /api/candidate-portal/my-interviews` - List candidate's interviews
- `POST /api/candidate-portal/interviews/{id}/book-slot` - Book interview slot

### Governance
- `GET /api/governance/roles` - List roles
- `POST /api/governance/roles` - Create role
- `PUT /api/governance/roles/{id}` - Update role
- `DELETE /api/governance/roles/{id}` - Delete role
- `POST /api/governance/user-roles` - Assign role
- `GET /api/governance/user-roles` - List assignments
- `DELETE /api/governance/user-roles/{id}` - Revoke role
- `GET /api/governance/audit` - Audit logs
- `GET /api/governance/access-matrix` - Access matrix

---

## Database Collections
- `users` - User accounts
- `clients` - Client companies
- `jobs` - Job requirements
- `candidates` - Candidate profiles
- `candidate_reviews` - Review history
- `client_roles` - Custom roles per client
- `user_client_roles` - User-role assignments
- `audit_logs` - Audit trail
- `interviews` - Interview scheduling
- `candidate_portal_users` - Candidate portal accounts (separate from job candidates)
- `notifications` - In-app notifications

---

## Completed in This Session (Jan 2026)
1. ✅ Interview Orchestration Backend (13 endpoints)
2. ✅ Calendar-style Interview Scheduler UI
3. ✅ Public Candidate Booking Page with secure tokens
4. ✅ Dashboard Interview Pipeline Stats widgets
5. ✅ Simplified CV Viewer (removed versioning)
6. ✅ Governance Console fully wired to backend
7. ✅ Notification System (Email via Pica/Gmail + In-app notifications)
8. ✅ **Candidate Portal** - Full registration, login, dashboard with interview booking

---

### Phase 14: UI/UX Enhancements ✅ (Jan 26, 2026)
**Dashboard Navigation:**
- Clickable stat cards (Clients, Active Jobs, Candidates, Interviews) navigate to underlying data
- Interview Pipeline cards (Awaiting, Confirmed, Scheduled, Completed, No Shows, Cancelled) navigate to filtered interview list

**Candidate Management:**
- Delete candidate button on Candidate Detail page (admin only)
- Delete confirmation with warning about associated data removal

**Client Management:**
- Extended client fields: Industry, Website, Phone, Address, City, State, Country, Postal Code, Notes
- Edit client information via Client Detail page
- Client User management: Edit (name, phone, email) and Delete client users
- **Email change triggers automatic welcome email with new temp password**

**Client User Onboarding:**
- Welcome email with login credentials sent on user creation
- Temporary password with mandatory change on first login
- Password Change Required dialog on login page
- Email change triggers new account setup email

**Interview Pipeline:**
- Fixed status filter values to match backend (Awaiting Candidate Confirmation)
- Back to Dashboard navigation fixed on all pages

**Backend Enhancements:**
- Extended `ClientCreate`, `ClientUpdate`, `ClientResponse` models
- `ClientUserUpdate` model with email field for user editing
- `PUT /api/clients/{client_id}/users/{user_email}` - Update client user (including email)
- `DELETE /api/clients/{client_id}/users/{user_email}` - Delete client user
- `POST /api/auth/change-password` - Password change endpoint
- `UserResponse` model now includes phone and user_id fields
- Login response includes `must_change_password` flag

### Phase 15: Interview Invitation Flow ✅ (Jan 26, 2026)
**Complete End-to-End Implementation:**
- Send interview invitation endpoint (`POST /api/interviews/{id}/send-invite`)
- Google Calendar integration via Pica API for auto-creating events with Google Meet links
- Professional interview invitation email template
- Interview status automatically updated to "Scheduled" when invite sent
- Meeting link, calendar event ID, and calendar link stored in interview record

### Phase 16: Candidate Portal Management & Notification System ✅ (Jan 26, 2026)
**Candidate Portal Admin Features:**
- New "Portal Users" management page for admins/recruiters
- View all portal users with status, contact info, company details
- Create new portal users with automatic welcome email + temp password
- Edit user details (name, phone, company, LinkedIn, status)
- Reset password and send email notification
- Delete portal users
- Stats cards: Active Users, Pending Password Change, Inactive Users

**Backend Endpoints Added:**
- `GET /api/admin/candidate-portal-users` - List all portal users
- `GET /api/admin/candidate-portal-users/{id}` - Get single user
- `POST /api/admin/candidate-portal-users` - Create portal user
- `PUT /api/admin/candidate-portal-users/{id}` - Update portal user
- `DELETE /api/admin/candidate-portal-users/{id}` - Delete portal user
- `POST /api/admin/candidate-portal-users/{id}/reset-password` - Reset password

**P0 Notification System:**
- Automatic notifications on candidate status change to recruiters/admins
- Automatic notifications on interview booking to recruiters, clients, and admins
- In-app notifications stored in database
- Email notifications via Pica API

### Phase 17: Multi-Round Interview System ✅ (Jan 26, 2026)
**Interview Round Progression:**
- Added `interview_round` (1, 2, 3...) and `round_name` fields
- Added `feedback` and `rating` (1-5) fields to interviews
- New interview statuses: `Passed`, `Failed`

**Client Decision Actions:**
- `POST /api/interviews/{id}/move-to-next-round` - Pass candidate, enable next round
- `POST /api/interviews/{id}/reject` - Reject candidate after interview
- `POST /api/interviews/{id}/initiate-hiring` - Start hiring process (final selection)

**Candidate Interview History:**
- `GET /api/candidates/{id}/interview-history` - View all rounds for a candidate

**Candidate Status Flow:**
- NEW → IN_REVIEW → IN_PROGRESS (passing rounds) → SELECTED or REJECTED

### Phase 18: Technical Documentation ✅ (Jan 26, 2026)
**Created Documentation:**
- `/app/docs/DATABASE_SCHEMA.md` - Complete database schema with all collections and fields
- `/app/docs/API_REFERENCE.md` - Full API endpoint documentation with examples

### Phase 19: Multi-Round Interview UI & CV Parsing V3 ✅ (Jan 29, 2026)
**Frontend Multi-Round Interview:**
- Added Interview Decision Dialog with Pass/Fail/Hire options
- Interview Scorecard with 5 categories: Technical Skills, Problem Solving, Communication, Cultural Fit, Experience Relevance
- Star rating (1-5) for each category
- Detailed feedback fields: Strengths, Areas for Improvement
- Hiring details: Salary Offered, Joining Date, Offer Notes
- Round badges (R1, R2, R3...) on interview cards
- Status colors: Passed (green), Failed (red)

**CV Parsing V3 Improvements:**
- FIXED: AI no longer hallucinates "career transitions" 
- Stricter domain matching for job fit scores
- Mismatched profiles now get realistic 15-35% scores
- Regex backup for email/phone extraction if AI misses
- Increased CV text processing to 6000 chars
- Added debug logging for parsing

---

## Upcoming Tasks

### P1 - Reminder Engine
- [ ] Email reminders for upcoming interviews (24h, 2h before)
- [ ] WhatsApp/SMS integration (Twilio via Pica API)
- [ ] Automated no-show detection

### P1 - Status Terminology Update
- [ ] Refactor candidate status to: Shortlisted, Not Shortlisted, Maybe (from APPROVED/REJECTED)

### P2 - Backend Refactoring
- [ ] Split `server.py` into domain routers
- [ ] Separate models into dedicated files

### P2 - Cleanup
- [ ] Deprecate public booking page after candidate portal is fully adopted
- [ ] Remove old `/book/:interviewId/:bookingToken` route

### P2 - Data Quality
- [ ] Fix interview records missing candidate_name field
- [ ] Ensure all interview creation properly populates denormalized fields

---

## File Structure
```
/app/
├── backend/
│   ├── server.py
│   ├── notification_service.py
│   ├── requirements.txt
│   └── tests/
│       ├── test_governance_rbac.py
│       ├── test_cv_versioning.py
│       ├── test_interviews.py
│       ├── test_candidate_portal.py
│       └── test_p1_p2_features.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── AdminDashboard.js
│   │   │   ├── ClientDashboard.js
│   │   │   ├── CandidateDetail.js
│   │   │   ├── candidate-portal/
│   │   │   │   ├── CandidateLogin.js
│   │   │   │   └── CandidateDashboard.js
│   │   │   ├── interviews/
│   │   │   │   └── CandidateBookingPage.js (deprecated)
│   │   │   └── governance/
│   │   ├── contexts/
│   │   │   ├── AuthContext.js
│   │   │   └── CandidateAuthContext.js
│   │   └── components/
│   │       ├── interviews/
│   │       │   ├── InterviewScheduler.js
│   │       │   ├── InterviewsList.js
│   │       │   └── InterviewPipelineStats.js
│   │       └── notifications/
│   │           └── NotificationBell.js
└── memory/
    └── PRD.md
```

---

Last Updated: January 26, 2026
