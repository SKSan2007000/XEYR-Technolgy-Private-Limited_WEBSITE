# XEYR TECHNOLOGIES PRIVATE LIMITED
## COMPLETE BUSINESS OPERATING SYSTEM

### Enterprise Backend, CRM, Business Intelligence, Client Requirements & Developer Handover

---

## Executive Overview

This system extends the official website of **XEYR Technologies Private Limited** into a complete, enterprise-grade business management system. It integrates a production-ready **Python Django** backend, **Django REST Framework**, and **PostgreSQL 17** database while strictly preserving the existing frontend visual identity, branding, typography (`DM Sans` & `Manrope`), color palette (`#07132e`, `#1465f4`, `#27d4f4`), orbit animations, and interactive modules (SolveX, SkillBridge, Events, and Contact forms).

---

## Key Highlights & Core Capabilities

1. **Preserved Frontend & Asynchronous Form Integration**
   - The original website in `XEYR_Website_Frontend/` remains completely intact.
   - All forms (`#solvex-form`, `#college-form`, `#individual-form`, `#registration-form`) now asynchronously submit data to Django REST endpoints (`/api/enquiries/submit/`, etc.) with responsive button loading states and reference IDs (`XEYR-ENQ-2026-XXXX`).
   - Seamless offline fallback to `localStorage` when backend is disconnected.

2. **Role-Based Administration Portal (`/dashboard/`)**
   - Built with the exact same XEYR visual language (dark navy glassmorphic aesthetic, cyan accents, clean typography).
   - 8 distinct roles: Super Admin, Business Admin, Sales/CRM, Account Manager, Project Manager, Developer, Finance Executive, Read-Only Analyst.
   - Comprehensive modules: CRM Enquiries, Qualification, Rejection History, Client Requirements Workspace, Brand Assets, Developer Handover, Developer Projects, Financials, and Business Intelligence.

3. **Multi-Stage Qualification & Rejection Workflow**
   - **Enquiry Qualification:** Assesses business opportunity, service fit, technical feasibility, decision maker, and estimated value.
   - **Mandatory Rejection Reasons:** Enforces one of 11 standardized categories (`BUDGET_MISMATCH`, `SERVICE_NOT_OFFERED`, `TECHNICAL_INFEASIBILITY`, etc.) with mandatory explanation notes. Rejection cannot be submitted without a reason.
   - Reopen capability with full audit logging.

4. **Structured Client Requirements Workspace**
   - 6 structured sections:
     - **A. Client Profile:** Legal name, contacts, tax/GST, address.
     - **B. Project Scope:** Business goals, features, functional/non-functional requirements.
     - **C. Commercial Terms:** Quoted vs. approved budget, milestone schedules.
     - **D. Design Preferences:** Color palettes, typography, UI wireframes, design benchmarks.
     - **E. Technical Architecture:** Frameworks, database engines, security, API integrations.
     - **F. Project Governance:** Milestones, priority, acceptance criteria, delivery checklist.

5. **Client Brand Assets with SHA-256 Checksums**
   - Categorized uploads across 19 asset types (logos, vector favicons, brand PDF guidelines, wireframes, screenshots).
   - Real SHA-256 checksums calculated upon storage.
   - Approval/rejection workflow per asset.

6. **Automated Developer Handover ZIP Generator**
   - Generates real, structured ZIP packages named `XEYR_Project_Handover_<ProjectID>_v<Ver>.zip`.
   - Complete directory layout:
     ```
     XEYR_Project_Handover_<ProjectID>/
     ├── README.md
     ├── PROJECT_SUMMARY.md
     ├── CLIENT_INFORMATION/
     │   └── client_profile.json
     ├── REQUIREMENTS/
     │   ├── requirements_summary.pdf
     │   ├── requirements_summary.md
     │   ├── functional_requirements.json
     │   ├── technical_requirements.json
     │   ├── design_requirements.json
     │   ├── scope_and_deliverables.json
     │   └── acceptance_criteria.json
     ├── BRAND_ASSETS/
     │   ├── logos/
     │   ├── icons/
     │   ├── brand_guidelines/
     │   └── reference_images/
     ├── DESIGN_REFERENCES/
     │   ├── screenshots/
     │   ├── wireframes/
     │   └── reference_links.md
     ├── TECHNICAL_DOCUMENTATION/
     │   ├── architecture_requirements.md
     │   ├── integrations.json
     │   ├── deployment_requirements.md
     │   └── testing_requirements.md
     ├── PROJECT_MANAGEMENT/
     │   ├── milestones.json
     │   ├── task_checklist.csv
     │   ├── delivery_checklist.md
     │   └── risk_register.json
     ├── COMMERCIAL_SUMMARY/
     │   └── approved_commercial_summary.pdf
     └── HANDOVER_METADATA/
         ├── manifest.json
         └── asset_inventory.csv
     ```
   - Includes real ReportLab-generated PDFs, markdown reports, JSON configurations, CSV checklists, actual approved uploaded brand files, and SHA-256 manifests.
   - Excludes secret keys, passwords, database credentials, or cross-client data.

7. **Developer Project Tracking**
   - Projects linked directly to origin enquiry and handover ZIP.
   - Milestone tracking, progress percentage, blockers, deliverable uploads, and QA checklist.

8. **Business Intelligence Dashboard with Chart.js & CSV Exports**
   - Interactive charts (Conversion Funnel, Service Demand Breakdown, Revenue Overview).
   - Global date range filtering (`Today`, `Yesterday`, `Last 7 Days`, `Last 30 Days`, `This Quarter`, `This Year`, etc.).
   - Deterministic rule-based insights generated from actual database records.
   - Real CSV exports for enquiries, rejections, projects, and financial records.

9. **Financial Data Foundation**
   - Invoices, quotes, received payments, refunds, and expenses.
   - Prepared for Razorpay gateway integration without collecting live card numbers.

---

## Directory Structure

```
XEYR_Website_Final_LogoOnly_Orbit_Refined/
│
├── README.md                           # Main Architecture & System Overview
├── WINDOWS_SETUP_GUIDE.md              # Windows Setup, Environment & Operations
├── API_DOCUMENTATION.md                # Comprehensive REST API Catalog
│
├── XEYR_Website_Frontend/              # Preserved Public Website
│   ├── index.html                      # Landing page with orbit animations & sections
│   ├── styles.css                      # Brand CSS styling and variables
│   ├── script.js                       # Asynchronous REST submission & dialog handlers
│   └── assets/                         # SVG logos, icons, and graphic assets
│
└── backend/                            # Django 5 Backend & REST APIs
    ├── manage.py                       # Django CLI entrypoint
    ├── requirements.txt                # Python package dependencies
    ├── .env.example                    # Environment template with PostgreSQL config
    ├── .env                            # Active environment configuration
    │
    ├── xeyr_backend/                   # Core Django project settings & URLs
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    │
    ├── core/                           # Custom User, RBAC, AuditLog, Tests
    │   ├── models.py                   # User, AuditLog, Notification, SystemSetting
    │   ├── tests.py                    # 18 automated business workflow tests
    │   └── management/commands/
    │       └── seed_xeyr_data.py       # Seeds users, events, and sample lifecycle data
    │
    ├── crm/                            # Enquiry, Qualification, Rejection, Follow-ups
    ├── requirements/                   # Structured Requirements Workspace & Approvals
    ├── assets_mgmt/                    # Brand Assets, Checksums & Private Storage
    ├── handover/                       # ZIP Generator, PDF Reports & Manifest
    ├── projects/                       # Developer Projects, Milestones & Progress
    ├── analytics/                      # Chart.js Dashboard, Date Filters & CSV Export
    ├── finance/                        # Invoices, Payments & Prepared Razorpay Schema
    ├── events_mgmt/                    # Events, Dynamic Forms, Razorpay, Notifications & Social QR
    │   ├── models.py                   # EventListing, EventFormField, EventPaymentOrder, SocialMediaConfig
    │   ├── views.py                    # Public feeds, Dynamic register, Verify payment, CSV export
    │   └── serializers.py              # DRF serializers for events and payment orders
    │
    └── templates/
        └── dashboard.html              # Full XEYR Dark Navy Glassmorphic Admin Portal
```

---

## 9. Final Add-On Suite: Events, Dynamic Forms, Razorpay & Social QR

1. **Centralised Event Management System**
   - Admin view to create, edit, publish/unpublish, schedule, and archive events with unique IDs and slugs.
   - Distinct modes (`Online`, `Offline`, `Hybrid`), venues, capacities, and pricing (Free vs. Paid).
   - Event status lifecycle: `DRAFT`, `PUBLISHED`, `UPCOMING`, `ONGOING`, `COMPLETED`, `CANCELLED`, `ARCHIVED`.

2. **Upcoming & Completed Event Archive**
   - Public tabs dynamically segregate upcoming events from completed archive events.
   - Completed events automatically move out of the upcoming listing based on date or explicit status.

3. **Intelligent "Get Notified" Call-To-Action**
   - When upcoming events exist, redundant notification blocks are completely hidden.
   - When no upcoming events exist, a clean notification CTA appears: **"Events Are Coming Up — Get Notified"**.
   - Subscriptions (Name, Email, category preferences) persist in PostgreSQL with consent tracking and a one-click unsubscribe mechanism.
   - Administrators can broadcast new event announcements to all active subscribers.

4. **Dynamic Form Builder per Event**
   - Custom fields configured by administrators without editing source code (text, textarea, dropdown, radio, checkbox, date, college, department, year of study, phone, consent).
   - Dynamic form inputs rendered on the registration modal and stored in structured `JSONField` responses.

5. **Production Razorpay Payment Integration**
   - Real server-side order creation via official `razorpay` library.
   - Official Razorpay Checkout experience with client-side key safety (secret never exposed to frontend).
   - Cryptographic server-side HMAC SHA256 signature verification (`/api/events/verify-payment/`).
   - Payment success is never inferred from browser redirect alone.
   - Idempotent order confirmation and automatic creation of financial ledger `PaymentRecord`.
   - Backend-enforced seat capacity limits to prevent overselling.

6. **Social Media & Real QR Codes**
   - Configurable footer links (Instagram, LinkedIn, GitHub, YouTube).
   - Admin section to upload, preview, and toggle real high-resolution QR codes.
   - Clickable preview modal on the public website footer.

7. **Smooth Scrolling & Scroll-Triggered Motion**
   - Native smooth scrolling with fixed navigation header margin offsets.
   - Subtle `IntersectionObserver` reveal-on-scroll animations (`.reveal-on-scroll`, `.stagger-children`).
   - Strict adherence to `prefers-reduced-motion` for accessibility.

---

## Quick Start on Windows

1. Ensure PostgreSQL 17 is running on `localhost:5432` with database `xeyr_db`.
2. Start the server from `backend/`:
   ```powershell
   cd backend
   python manage.py runserver 127.0.0.1:8000
   ```
3. Open in your browser:
   - **Website:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - **Admin Portal:** [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
   - **Login Credentials:** `admin` / `XeyrAdmin@2026`
4. Run all 31 automated tests:
   ```powershell
   python manage.py test core --no-input
   ```
