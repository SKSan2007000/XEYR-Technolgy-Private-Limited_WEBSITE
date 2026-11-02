# XEYR Technologies Private Limited — Windows Setup & Enterprise Admin Dashboard Guide

This guide provides beginner-friendly, step-by-step instructions to set up and run the complete **XEYR Technologies Enterprise Platform**, including the **Django Backend with PostgreSQL 17**, the preserved **Static Public Website**, and the dedicated **React + TypeScript + Vite Enterprise Admin Dashboard**.

---

## 1. Architecture Overview

| Component | Technology | Directory | Development URL | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Public Website** | HTML5, CSS3, Vanilla JS | `XEYR_Website_Frontend/` | `http://127.0.0.1:8000/` or local browser | Preserved public brand identity, SolveX, SkillBridge, orbit animations, event listings, contact forms |
| **Admin Dashboard** | React 19, TypeScript, Vite, Chart.js, Lucide Icons | `XEYR_Admin_Dashboard/` | `http://127.0.0.1:5173/` | Enterprise administration interface, business analytics, CRM qualification, deliverables, handovers, payments |
| **Backend API** | Django 5.2, Django REST Framework | `backend/` | `http://127.0.0.1:8000/api/` | Secure REST API, session authentication, PostgreSQL ORM, ZIP generators, Razorpay signatures |
| **Database** | PostgreSQL 17.10 | Service `postgresql-x64-17` | `localhost:5432` (`xeyr_db`) | 38 relational tables, ACID transactions, audit logs, ledger records |

---

## 2. Prerequisites on Windows

1. **Python 3.10+** (Confirm with `python --version` in PowerShell).
2. **Node.js 18+ & npm** (Confirm with `node -v` and `npm -v`).
3. **PostgreSQL 14+** (PostgreSQL 17 recommended; check Windows Services `services.msc` -> `postgresql-x64-17` is **Running**).
4. **Visual Studio Code** (VS Code).

---

## 3. Step-by-Step Setup Guide

### Step 1: Open the Project in VS Code
1. Launch **Visual Studio Code**.
2. Go to **File** -> **Open Folder...**
3. Select the folder:
   `C:\Users\B SANTHOSH KUMAR\Downloads\XEYR_Website_Final_LogoOnly_Orbit_Refined`

---

### Step 2: Configure Environment Variables (Without Exposing Secrets)
1. In the `backend/` folder, check the `.env` file (or copy from `.env.example` if on a new machine).
2. Ensure the following variables are present:
   ```env
   SECRET_KEY=xeyr-secure-production-secret-key-change-in-production-2026-xyz
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

   USE_SQLITE=False
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=xeyr_db
   DB_USER=postgres
   DB_PASSWORD=YOUR_POSTGRES_PASSWORD
   DB_HOST=localhost
   DB_PORT=5432

   # CORS Configuration for the separate React Dashboard
   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000
   CORS_ALLOW_CREDENTIALS=True
   CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000

   # Razorpay in Test Mode
   RAZORPAY_KEY_ID=rzp_test_placeholder
   RAZORPAY_KEY_SECRET=placeholder_secret
   ```
   > **Note:** Never commit real production secrets to source control. `.env` is listed in `.gitignore`.

---

### Step 3: Activate Backend Virtual Environment & Install Dependencies
1. Open a new terminal in VS Code (**Terminal** -> **New Terminal**, or `Ctrl + Shift + \``).
2. Navigate to `backend/`:
   ```powershell
   cd backend
   ```
3. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   *(If script execution is disabled in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once).*
4. Install backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

### Step 4: Verify PostgreSQL Connection & Apply Migrations
1. Run Django migrations to verify that PostgreSQL is running and connected:
   ```powershell
   python manage.py migrate
   ```
2. Verify system health check:
   ```powershell
   python manage.py check
   ```
   *(Should report: `System check identified no issues (0 silenced).`)*

---

### Step 5: Start the Django Backend Server
In your backend terminal, start Django:
```powershell
python manage.py runserver 127.0.0.1:8000
```
- Django API will be live at: `http://127.0.0.1:8000/api/`
- Backend health check at: `http://127.0.0.1:8000/api/health/`

---

### Step 6: Open the React Admin Dashboard Folder in a New Terminal
1. Open a **second terminal tab** in VS Code (click the `+` icon in the terminal panel).
2. Navigate to the `XEYR_Admin_Dashboard` folder:
   ```powershell
   cd XEYR_Admin_Dashboard
   ```
   > **Important:** Do NOT run `npm install` inside the static `XEYR_Website_Frontend` folder. Only run `npm` inside `XEYR_Admin_Dashboard/`.

---

### Step 7: Install Frontend Dependencies
In the `XEYR_Admin_Dashboard` terminal, run:
```powershell
npm install
```
*(Dependencies installed: React 19, Lucide React, Chart.js, Vite, TypeScript).*

---

### Step 8: Start the Dashboard Development Server
In the `XEYR_Admin_Dashboard` terminal, run:
```powershell
npm run dev
```
- The dashboard will start on: **`http://localhost:5173/`** (or `http://127.0.0.1:5173/`).

---

### Step 9: Open the Dashboard & Log In
1. Open your browser and navigate to:
   **`http://localhost:5173/`**
2. You will be greeted by the secure **XEYR Enterprise Authentication Portal**.
3. Log in using the authorized administrator account:
   - **Username:** `admin`
   - **Password:** `XeyrAdmin@2026`
4. The dashboard will securely authenticate via session cookies with Django (`/api/auth/login/`) and load real database records into the Executive Overview.

---

### Step 10: Run Automated Tests
Open a terminal in the root workspace folder and execute:
```powershell
# 1. Django 31-test suite
cd backend
python manage.py test

# 2. End-to-end integration and security test
cd ..
python scratch_verify_system.py

# 3. CRM qualification and mandatory rejection reason test
python scratch_test_enquiry_rules.py
```
All tests run against real PostgreSQL database tables and verify zero regressions.

---

## 4. Strict Separation of Public Website & Admin Dashboard

### Why Did the Public Website Previously Open `C:/dashboard/`?
In the original `XEYR_Website_Frontend/index.html`, relative root links like `<a href="/dashboard/">Admin Portal</a>` were used. When opening `index.html` as a local `file:///` in a web browser, clicking a root-relative link resolves relative to the drive root `file:///C:/`, causing browsers to open `file:///C:/dashboard/` (which showed `ERR_FILE_NOT_FOUND`).

### Architectural Solution: Complete Separation & Independent Access
1. **Removed from Public Website:** As required for strict security and brand separation, the Admin Portal button and all related links have been **completely removed** from desktop navigation, mobile navigation, and the footer in `XEYR_Website_Frontend/index.html`.
2. **Dedicated Private Application:** The administration dashboard is an independent React 19 + TypeScript + Vite application running in `XEYR_Admin_Dashboard/`. It is never accessed via public website links, but directly and securely via its own private URL:
   - **Dashboard URL:** `http://localhost:5173/` (or `http://127.0.0.1:5173/`)
3. **Public Website Navigation:** The public website keeps its clean public navigation intact: **Home**, **Workshops & Events**, **Services**, **About**, **Contact**, and **Register**.

---

## 5. Pre-Configured Administrator Credentials

| Role | Username | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Super Administrator** | `admin` | `XeyrAdmin@2026` | Full enterprise access across CRM, Engineering, Finance, Events, and Settings |
| **Sales / CRM Lead** | `sales_lead` | `XeyrStaff@2026` | Enquiries pipeline, lead qualification, rejection with mandatory reasons |
| **Project Manager** | `project_mgr` | `XeyrStaff@2026` | Requirements workspace, brand assets, developer handover ZIP packages |
| **Developer** | `lead_dev` | `XeyrStaff@2026` | Assigned projects, sprint progress, milestones, deliverable submissions |

---

## 6. Dashboard Modules & Business Intelligence Features

1. **Executive Overview (BI & KPIs):**
   - 9 Live KPI Cards derived strictly from PostgreSQL queries.
   - Interactive Funnel, Service Distribution, and Financial Reconciliation Charts using `Chart.js`.
   - Real-time rule-based actionable insights generated on the backend.
2. **Client Enquiries & CRM:**
   - Filter by status (`NEW`, `UNDER_REVIEW`, `QUALIFIED`, `REJECTED`, `CONVERTED`).
   - Detailed modal review, service type categorization, and timeline.
   - Reject modal with **mandatory reason requirement** and categorized rejection codes.
3. **Qualified Leads:**
   - Review budget confirmations, timeline confirmations, estimated contract values, and direct transition to engineering workspaces.
4. **Client Requirements Workspaces:**
   - Functional specifications, deliverable checklists, technical stack definitions, and readiness checks.
5. **Brand Assets & Cryptographic Files:**
   - Upload brand logos, style guides, and assets with SHA-256 integrity checksum calculation and secure download routes.
6. **Developer Handover Packages (ZIP):**
   - Automated ZIP archive generation containing manifests, technical specs, and deliverables.
   - **Strict Security:** Automatically excludes `.env` files, passwords, database dumps, and private credentials.
7. **Projects & Sprint Progress:**
   - Track active engineering projects, milestones, progress percentages, and deliverables.
8. **Workshops & Events Management:**
   - Create, edit, and publish events; switch between Upcoming and Completed tabs; configure custom dynamic registration fields.
9. **Participant Registrations:**
   - View attendee lists, search by name/email/college, filter by confirmation status, and export CSV attendee rosters.
10. **System Security Alerts & Notifications:**
    - Real-time unread counter badge, detailed audit logs, and one-click "Mark as Read".
11. **Finance & Invoicing:**
    - Real financial records distinguishing Quoted, Invoiced, Paid, Pending, and Failed.
12. **Social Media & QR Code Graphics:**
    - Update public social links and preview verified QR code graphics.
13. **Verified Reports & CSV Exports:**
    - On-demand CSV report exports for CRM, Financials, Handovers, and Events.
14. **Settings & Administrator Profile:**
    - View administrator identity, security session information, and live PostgreSQL 17 connection status.
