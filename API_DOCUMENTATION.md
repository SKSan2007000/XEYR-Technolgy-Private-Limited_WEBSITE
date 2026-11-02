# XEYR Technologies - REST API Documentation

This document describes all API endpoints implemented in the XEYR Business Operating System. All endpoints are prefixed with `/api/`.

---

## 1. Authentication & Session

### `POST /api/auth/login/`
Authenticate user session and return role profile.
- **Payload:**
  ```json
  {
    "username": "admin",
    "password": "XeyrAdmin@2026"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "message": "Login successful",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@xeyr.in",
      "role": "SUPER_ADMIN",
      "first_name": "Antigravity",
      "last_name": "Admin"
    }
  }
  ```

### `POST /api/auth/logout/`
Terminates current authenticated session.
- **Response `200 OK`:** `{"message": "Logged out successfully"}`

### `GET /api/auth/profile/`
Returns current authenticated user details and permissions.

---

## 2. Public Website Submissions (Frontend Forms)

### `POST /api/enquiries/submit/`
Submits enquiry from SolveX or general contact form.
- **Payload:**
  ```json
  {
    "contact_person": "Alex Rivers",
    "email": "alex@nexus.io",
    "phone": "+91 9876543210",
    "organization_name": "Nexus Dynamics",
    "organization_type": "ENTERPRISE",
    "service_required": "SOLVEX_CUSTOM",
    "project_title": "Enterprise Microservices Modernization",
    "project_description": "Migrating legacy monolith into distributed Python/Django microservices.",
    "budget_range": "INR 5L - 10L",
    "expected_timeline": "3-4 Months",
    "preferred_contact_method": "EMAIL"
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "success": true,
    "reference_id": "XEYR-ENQ-2026-0002",
    "message": "Enquiry submitted successfully."
  }
  ```

### `POST /api/events/register/`
Registers attendee for an upcoming XEYR event.
- **Payload:** `{"event_id": 1, "attendee_name": "...", "email": "...", "phone": "..."}`

### `POST /api/events/college-enquiry/`
Registers college/institutional partnership for XEYR SkillBridge.

### `POST /api/events/trainer-apply/`
Submits professional trainer/expert application for SkillBridge.

---

## 3. CRM & Enquiry Management

### `GET /api/enquiries/`
Lists enquiries with search and filtering by status, service, and date.
- **Query Params:** `?status=QUALIFIED&search=Nexus`
- **Requires:** Authenticated user with CRM/Sales permission.

### `GET /api/enquiries/<id>/`
Retrieves complete enquiry detail including status history, CRM activities, and qualification status.

### `POST /api/enquiries/<id>/qualify/`
Marks enquiry as `QUALIFIED` and initiates the qualification assessment.
- **Payload:**
  ```json
  {
    "business_opportunity": "High probability enterprise modernization project",
    "client_needs": "Scalable REST APIs and cloud automation",
    "service_fit": "EXCELLENT",
    "estimated_project_value": 750000.00,
    "budget_confirmed": true,
    "timeline_confirmed": true,
    "decision_maker_details": "Alex Rivers, CTO",
    "technical_feasibility": "FEASIBLE",
    "internal_assessment": "Core competencies align with team stack",
    "next_action": "Requirements gathering meeting"
  }
  ```

### `POST /api/enquiries/<id>/reject/`
Rejects enquiry with mandatory category and detailed reasoning.
- **Payload:**
  ```json
  {
    "rejection_category": "BUDGET_MISMATCH",
    "reason_detail": "Client target budget is below minimum viable threshold for custom enterprise architecture.",
    "allow_future_followup": false
  }
  ```
- **Validation:** If `rejection_category` or `reason_detail` is missing, returns `400 Bad Request`.

### `POST /api/enquiries/<id>/reopen/`
Reopens a previously rejected enquiry with audit trail.
- **Payload:** `{"reopen_reason": "Client increased project budget to align with proposal."}`

---

## 4. Client Requirements Workspace

### `GET /api/requirements/?enquiry_id=<id>`
Fetches the current requirements workspace for an enquiry.

### `POST /api/requirements/`
Creates or updates requirements (Sections A to F).
- **Key Fields:**
  - Client Info (Legal name, contact, GST/Tax ID, address)
  - Project Overview (Scope of work, deliverables, features list)
  - Commercial Details (Quoted price, approved budget, milestones)
  - Design Requirements (Colors, typography, reference URLs, UI guidelines)
  - Technical Requirements (Frameworks, databases, deployment targets, APIs)
  - Project Management (Priority, delivery checklist, acceptance criteria)

### `POST /api/requirements/<id>/approve/`
Marks requirements as approved by client or internal sign-off.
- **Payload:**
  ```json
  {
    "approval_type": "CLIENT",
    "approval_reference": "Email sign-off from Alex Rivers dated 2026-10-25",
    "approval_notes": "All functional specifications accepted without reservation."
  }
  ```

---

## 5. Client Brand Assets Management

### `GET /api/assets/?enquiry_id=<id>`
Lists all uploaded assets for a client/project with SHA-256 checksums and verification status.

### `POST /api/assets/upload/`
Uploads asset with category classification.
- **Form Data:**
  - `enquiry`: `<id>`
  - `asset_category`: `PRIMARY_LOGO` | `BRAND_GUIDELINES_PDF` | `FAVICON` | etc.
  - `file`: `<Binary File>`
  - `notes`: `Official high-res vector logo`

### `POST /api/assets/<id>/update-status/`
Updates status to `APPROVED`, `REJECTED`, or `REPLACEMENT_REQUIRED`.

---

## 6. Developer Handover ZIP Generator

### `GET /api/handover/readiness-check/?enquiry_id=<id>`
Runs pre-flight readiness checklist:
- Enquiry qualification check
- Requirements completion check
- Brand assets verification check
- Acceptance criteria defined check
- Commercial approval check

### `POST /api/handover/generate/`
Builds real downloadable ZIP archive adhering to the specification directory layout.
- **Payload:**
  ```json
  {
    "enquiry_id": 1,
    "notes": "Version 1.0 Developer Handover Package"
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "success": true,
    "handover_id": 1,
    "version": "v1.0",
    "filename": "XEYR_Project_Handover_PRJ-2026-0001_v1.0.zip",
    "download_url": "/api/handover/1/download/"
  }
  ```

### `GET /api/handover/<id>/download/`
Downloads the real generated handover ZIP file. Increments download counter.

---

## 7. Developer Projects & Progress

### `GET /api/projects/`
Lists projects assigned or monitored.

### `POST /api/projects/assign/`
Assigns project to a developer user.
- **Payload:**
  ```json
  {
    "project_id": 1,
    "developer_id": 4,
    "priority": "HIGH",
    "expected_delivery_date": "2026-12-15",
    "handover_instructions": "Review REQUIREMENTS/requirements_summary.pdf before commencing sprint 1."
  }
  ```

### `PATCH /api/projects/<id>/update-status/`
Updates project status (`IN_PROGRESS`, `BLOCKED`, `COMPLETED`), progress percentage, and blocker notes.

---

## 8. Business Intelligence & Analytics

### `GET /api/analytics/dashboard/?period=last_30_days`
Returns aggregated business metrics, KPI summary cards, conversion funnels, service demand breakdown, and revenue statistics.
- **Supported Periods:** `today`, `yesterday`, `this_week`, `last_week`, `last_30_days`, `this_month`, `last_month`, `this_quarter`, `this_year`, `custom`

### `GET /api/analytics/insights/`
Returns deterministic rule-based business insights generated from real database records.

### `GET /api/analytics/export-csv/?type=enquiries&period=last_30_days`
Generates and downloads a CSV export file.
- **Supported Types:** `enquiries`, `rejections`, `projects`, `financials`

---

## 9. Event Management, Dynamic Forms & Razorpay Payment APIs

### `GET /api/events/public/`
Public feed for homepage event listings and empty-state notification rules.
- **Returns:**
  ```json
  {
    "has_upcoming": true,
    "empty_state_cta": false,
    "upcoming_count": 2,
    "upcoming_events": [...],
    "has_completed": true,
    "completed_count": 1,
    "completed_events": [...]
  }
  ```

### `GET /api/events/public/<slug_or_id>/`
Fetches detailed event metadata, poster URL, venue, mode, fee amount, pricing details, and configured dynamic registration form fields.

### `POST /api/events/<event_id>/register-dynamic/`
Dynamic event registration submission supporting individual and team details with admin-configured fields.
- **Payload:**
  ```json
  {
    "full_name": "Santhosh Kumar",
    "email": "santhosh@example.com",
    "phone": "+91 80562 53897",
    "custom_fields": {
      "college": "Anna University",
      "year_of_study": "Final Year",
      "primary_focus": "Agentic AI Systems"
    }
  }
  ```
- **Response (Free Event - `201 Created`):**
  ```json
  {
    "success": true,
    "is_paid": false,
    "payment_required": false,
    "registration_id": 4,
    "registration_status": "CONFIRMED",
    "payment_status": "NOT_REQUIRED",
    "registration_reference": "XEYR-REG-2026-1004",
    "message": "Your registration has been confirmed! We look forward to seeing you."
  }
  ```
- **Response (Paid Event - `201 Created`):**
  ```json
  {
    "success": true,
    "is_paid": true,
    "payment_required": true,
    "registration_id": 5,
    "registration_status": "PENDING_PAYMENT",
    "payment_status": "ORDER_CREATED",
    "registration_reference": "XEYR-REG-2026-1005",
    "razorpay_order_id": "order_test_XEYR_REG_2026_1005",
    "amount": 499.00,
    "amount_in_paise": 49900,
    "currency": "INR",
    "key_id": "rzp_test_..."
  }
  ```

### `POST /api/events/verify-payment/`
Server-side cryptographic verification of Razorpay payment outcome.
- **Payload:**
  ```json
  {
    "razorpay_order_id": "order_test_XEYR_REG_2026_1005",
    "razorpay_payment_id": "pay_test_karthik_123",
    "razorpay_signature": "<hmac_sha256_hex_digest>",
    "registration_id": 5
  }
  ```
- **Response (`200 OK` on signature verification):**
  ```json
  {
    "success": true,
    "message": "Payment successfully verified! Your event registration is confirmed.",
    "registration_reference": "XEYR-REG-2026-1005",
    "registration_status": "CONFIRMED",
    "payment_status": "PAID",
    "transaction_id": "pay_test_karthik_123",
    "amount_paid": 499.00
  }
  ```

### `POST /api/events/subscribe/`
Collects visitor name and email for "Events Are Coming Up — Get Notified" when no upcoming events exist.
- **Payload:** `{"full_name": "Dev User", "email": "dev@example.com", "categories": "Workshop"}`
- **Response `201 Created`:** `{"success": true, "message": "You have been subscribed to event notifications."}`

### `GET /api/events/subscribers/unsubscribe/<token>/`
One-click unsubscribe endpoint from transactional notification emails.

### `GET /api/events/manage/` & `POST /api/events/manage/`
Admin CRUD for events: draft, publish, unpublish, archive, set pricing, dates, and max participants.

### `GET /api/events/manage/<event_id>/fields/` & `POST /api/events/manage/<event_id>/fields/`
Dynamic form field builder per event: add text, dropdown, date, phone, college, and custom inputs.

### `POST /api/events/manage/<event_id>/notify-subscribers/`
Broadcasts new event announcement to all consented active subscribers and records delivery status.

### `GET /api/events/manage/<event_id>/export-csv/`
Downloads clean CSV participant list for registered attendees.

### `GET /api/events/payments/dashboard/`
Returns payment management KPIs (total revenue, verified orders, failed transactions, refunds).

---

## 10. Social Media & QR Code APIs

### `GET /api/social-links/public/`
Returns active social platforms and real uploaded QR code image URLs for footer rendering.

### `POST /api/social-links/manage/`
Admin update for platform URLs, public visibility toggles, and genuine high-resolution QR image uploads.
