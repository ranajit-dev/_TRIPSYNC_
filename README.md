> **Phase F v1.3.0 release candidate:** See [GitHub + Render Deployment Guide](docs/PHASE_F_DEPLOYMENT.md) for a secure production launch. Includes improved Gunicorn port binding, GitHub CI and the Firestore regression-test fix. A live Render deployment is not yet confirmed.

> **v1.2 UI update:** The login screen now matches the editorial landing page, includes Back to the website / Return to Dashboard navigation, and displays a dashboard CTA for already authenticated users. See [`docs/LOGIN_DESIGN_UPDATE.md`](docs/LOGIN_DESIGN_UPDATE.md).

> **v1.1 update:** TripSync now opens on a public, animated travel homepage at `/` with a **Log in** link in the top navigation. See [Landing Page Update](docs/LANDING_PAGE_UPDATE.md) for installation and changes.

# 🧭 TripSync — Travel Booking Data Organizer (v1.3.0)
> **Full-Stack College IT Workshop Mini Project**  
> Built with **Python Flask**, **Firebase Cloud Firestore**, **Firebase Authentication**, **Bootstrap 5**, and **Chart.js**.

---

## 📋 Table of Contents
1. [Project Overview](#-project-overview)
2. [Key Features](#-key-features)
3. [Technology Stack](#-technology-stack)
4. [System Architecture & Folder Structure](#-system-architecture--folder-structure)
5. [Local Quickstart & Installation](#-local-quickstart--installation)
6. [Firebase Configuration](#-firebase-configuration)
7. [User Roles & Permissions (RBAC)](#-user-roles--permissions-rbac)
8. [Automated Testing](#-automated-testing)
9. [Render Cloud Deployment](#-render-cloud-deployment)
10. [Application Security](#-application-security)
11. [Documentation Links](#-documentation-links)

---

## 🌟 Project Overview

**TripSync (Travel Booking Data Organizer)** is a professional web-based reservation management system designed to centralize, organize, track, and analyze travel booking records across four primary categories:
1. ✈️ **Flights**
2. 🚆 **Trains**
3. 🚌 **Buses**
4. 🏨 **Hotels**

The system is specifically engineered for travel agencies, coordinators, and college IT Workshop project evaluations. It replaces disorganized spreadsheets and manual paper ledgers with a secure, real-time command center.

> **Note:** TripSync is a record-management and accounting system. It is not intended to purchase live third-party tickets or process real bank transactions.

---

## 🚀 Key Features

- **Sequential Booking IDs:** Automatic, collision-free transaction IDs (`TB-0001`, `TB-0002`, etc.) generated via Cloud Firestore transactions.
- **Dynamic Adaptive Forms:** Smart form fields that switch between transport bookings (source, destination, passengers) and hotel stays (hotel name, rooms, check-in, check-out, guests).
- **Integer Paise Financial Calculations:** Prevents floating-point rounding errors by performing all financial computations in integer paise and formatting in Indian Rupees (`₹1,25,000.00`).
- **Payment Reconciliation:** Live calculation of outstanding balances with dynamic payment statuses:
  - 🟢 **Paid:** Full payment received.
  - 🟡 **Partially Paid:** Partial advance collected; displays remaining balance due.
  - 🔴 **Unpaid:** Zero amount recorded.
- **Upcoming Journeys & Countdowns:** Detects trips scheduled within the next 7 days in the `Asia/Kolkata` timezone, featuring intuitive countdown badges (*"Today"*, *"Tomorrow"*, *"In 3 days"*).
- **Print-Ready Vouchers:** Dedicated print layout (`@media print`) that formats booking details into clean, standardized A4 confirmation vouchers with official disclaimers.
- **Visual Analytics:** Interactive Chart.js visualizations for category distribution, payment status breakdowns, and popular Indian travel destinations.
- **Admin-Only CSV Export:** Safe data export with spreadsheet formula-injection neutralization (`=, +, -, @`).
- **Role-Based Access Control (RBAC):** Distinct permissions separating **Administrators** from **Staff Members**.
- **Subtle 3D Interface:** Custom CSS perspective tilt effects on cards, glowing status badges, and full accessibility support for `prefers-reduced-motion`.

---

## 🛠️ Technology Stack

| Layer | Component | Technology |
|---|---|---|
| **Frontend** | Markup & Structure | HTML5, Jinja2 Templates |
| | Styling & UI | Bootstrap 5.3, Bootstrap Icons, Custom CSS3 |
| | Interactivity | Vanilla JavaScript (ES6+), 3D Perspective Transforms |
| | Visualizations | Chart.js 4.4 |
| **Backend** | Application Framework | Python 3 with Flask 3.1 |
| | WSGI Production Server | Gunicorn (Linux/Render) |
| **Database & Auth** | Cloud Database | Firebase Cloud Firestore |
| | Authentication | Firebase Authentication (Email/Password) |
| | Server Integration | Firebase Admin SDK for Python (`firebase-admin` 7.7+) |
| **Configuration** | Environment Secrets | `python-dotenv`, Environment Variables |
| **Testing** | QA & Test Suite | `pytest` 9.1+, Flask Test Client |
| **Deployment** | Cloud Platform | Render Web Service (`render.yaml`) |

---

## 📁 System Architecture & Folder Structure

```
TRIPSYNC/
│
├── app.py                     # Flask application factory, routes, and WSGI export
├── config.py                  # Environment config and cookie security parameters
├── constants.py               # Application constants, roles, and category enums
├── firebase_config.py         # Thread-safe Firebase Admin SDK initializer
├── auth.py                    # Server token verification and session cookies
├── decorators.py              # Security guards (@login_required, @admin_required, CSRF)
├── database.py                # Firestore collection operations and transactions
├── services.py                # Business logic, integer paise math, filters, CSV export
├── seed_data.py               # CLI script seeding 25 realistic Indian travel records
│
├── requirements.txt           # Production and development dependencies
├── .python-version            # Pinned to Python 3.11.9
├── .env.example               # Template for environment configuration
├── .gitignore                 # Excludes secrets, venvs, and build artifacts
├── render.yaml                # Render Blueprint deployment definition
│
├── scripts/
│   └── provision_user.py      # CLI script to provision Admin/Staff users
│
├── templates/
│   ├── base.html              # Master layout shell
│   ├── _navbar.html           # Top navigation bar
│   ├── _sidebar.html          # Collapsible navigation drawer
│   ├── _toast.html            # Alert toast notification partial
│   ├── _booking_form.html     # Reusable dynamic booking form partial
│   ├── login.html             # Two-column login page with 3D graphics
│   ├── dashboard.html         # Operations dashboard with KPI cards and charts
│   ├── bookings.html          # Bookings table with multi-parameter filters
│   ├── add_booking.html       # Create new booking view
│   ├── edit_booking.html      # Edit existing booking view
│   ├── booking_details.html   # Detailed reservation record view
│   ├── booking_print.html     # Print-friendly confirmation voucher
│   ├── upcoming.html          # Dedicated 7-day upcoming trips countdown view
│   ├── reports.html           # Administrative analytics and charts view
│   └── errors/
│       ├── 403.html           # 403 Forbidden error page
│       ├── 404.html           # 404 Not Found error page
│       └── 500.html           # 500 Server Error page
│
├── static/
│   ├── css/
│   │   ├── style.css          # Design system tokens and layout
│   │   ├── components.css     # Glass cards, KPI cards, badges, buttons, tables
│   │   ├── animations.css     # 3D transforms, keyframes, reduced-motion rules
│   │   └── print.css          # Dedicated A4 voucher print styling
│   └── js/
│       ├── app.js             # Navigation drawer, toast init, 3D card tilt
│       ├── firebase-auth.js   # Client authentication and session cookie exchange
│       ├── forms.js           # Real-time fare and balance calculations
│       ├── bookings.js        # Filter handling and search resets
│       └── charts.js          # Chart.js initialization for distributions
│
├── tests/
│   ├── conftest.py            # Pytest fixtures and mock client configurations
│   ├── test_services.py       # Domain math, validation, and CSV safety tests
│   ├── test_auth.py           # Authentication, session, and role boundary tests
│   ├── test_bookings.py       # CRUD operations, cancellation, and deletion tests
│   └── test_reports.py        # Analytics calculations and CSV delivery tests
│
└── docs/
    ├── architecture.md        # Technical architecture documentation
    ├── firebase-setup.md      # Detailed Firebase project configuration guide
    ├── deployment.md          # Step-by-step Render deployment manual
    └── project-report.md      # Complete IT Workshop academic project report
```

---

## ⚡ Local Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/tripsync.git
cd tripsync
```

### 2. Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file:
```bash
cp .env.example .env
```
**Firebase credentials are required for normal use.** The application does not offer a demo-password bypass or temporary storage. Automated tests explicitly enable an isolated in-memory repository.

### 5. Seed Demonstration Data (Optional)
Populate 25 realistic Indian travel records:
```bash
python seed_data.py --force
```

### 6. Start the Flask Application
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🔑 User Roles & Permissions (RBAC)

TripSync enforces strict role boundaries:

| Permission / Action | Administrator | Staff Member |
|---|:---:|:---:|
| View Dashboard & Booking Records | ✅ | ✅ |
| Create New Bookings | ✅ | ✅ |
| Edit Permitted Booking Details | ✅ | ✅ |
| Record / Update Paid Amounts | ✅ | ✅ |
| View Upcoming Journeys (Countdowns) | ✅ | ✅ |
| Preview & Print Internal Vouchers | ✅ | ✅ |
| Cancel Bookings (Soft Status Update) | ✅ | ❌ |
| Permanently Delete Records | ✅ | ❌ |
| Access Financial Reports & Analytics | ✅ | ❌ |
| Export Booking Dataset to CSV | ✅ | ❌ |

### Initial accounts
Provision your own Admin and Staff accounts through `scripts/provision_user.py` and Firebase Authentication. Use unique email addresses and strong private passwords. Built-in demo accounts and quick-fill buttons have been removed.

---

## 🧪 Automated Testing

Automated tests are implemented using `pytest`. The test suite runs independently of live cloud credentials using in-memory isolation.

To execute the test suite:
```bash
pytest tests/ -v
```

### Test suite coverage
Original tests plus Phase A–C regression tests cover application routes, permissions, booking calculations, reporting, CSV export and fail-closed behavior. Run `pytest -q tests` in your own environment; live Firebase integration and full browser QA require separate verification. This release was checked in an isolated environment using mock Firebase modules and vendored pure-Python Flask libraries, not live Firebase.

---

## ☁️ Render Cloud Deployment

TripSync includes full native support for **Render**:
1. Connect your GitHub repository to [Render](https://render.com).
2. Choose **Web Service** with runtime **Python 3**.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `gunicorn app:app`
5. Upload your `serviceAccountKey.json` under **Secret Files** at `/etc/secrets/serviceAccountKey.json`.
6. Add environment variable `GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/serviceAccountKey.json`.
7. Verify live health check at `https://<your-service>.onrender.com/healthz`.

*For detailed instructions, see [docs/deployment.md](docs/deployment.md).*

---

## 🔒 Application Security

- **Server-Side Session Cookies:** Uses `HttpOnly`, `SameSite=Lax`, and `Secure` (in production) cookies.
- **CSRF Defense:** Cryptographic CSRF tokens required on all mutating requests (`POST`, `PUT`, `DELETE`).
- **Formula Injection Mitigation:** Leading `=, +, -, @` characters in exported CSV records are safely quoted to prevent spreadsheet command execution.
- **Strict Input Validation:** Indian 10-digit phone number regex (`^[6-9]\d{9}$`), positive integers for travelers, departure/destination dissimilarity, and chronological check-out validation.
- **Defense-in-Depth:** Zero service-account credentials exposed to client-side code; all Firestore access is mediated through server-side authorization decorators.

---

## 📚 Documentation Links

- [System Architecture](docs/architecture.md)
- [Firebase Setup Guide](docs/firebase-setup.md)
- [Render Deployment Manual](docs/deployment.md)
- [Academic Mini Project Report](docs/project-report.md)

---

## 📄 License & Academic Integrity
Developed as an academic mini project for the **College IT Workshop**. Designed for demonstration, evaluation, and educational use.

---

## Phase A–D Maintenance Update

See [`docs/PHASES_A_D_CHANGELOG.md`](docs/PHASES_A_D_CHANGELOG.md) for the security and reliability changes, regression test results and browser QA limitations.

**Release readiness:** Do not publish with real customer data until Firebase login/session verification and responsive browser behavior have been verified against the deployed application.
