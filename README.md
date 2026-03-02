# AI Healthcare Assistant — MVP

> AI-powered pre-visit intake system. Patient books → chat starts immediately → doctor sees clean summary → prescription generated.

---

## What This Builds

```
Patient books appointment (UI)
        ↓
N8N confirms booking in background
        ↓
Chat interface appears on same page
        ↓
Claude asks intake questions via text chat
        ↓
Doctor logs in → sees AI-generated summary
        ↓
Doctor fills diagnosis + medicines
        ↓
PDF prescription generated + emailed to patient
```

---

## Tech Stack

| Layer | Technology | Hosting | Cost |
|---|---|---|---|
| Frontend | React + Tailwind CSS | Vercel | Free |
| Backend | Python + FastAPI | Railway | $5/mo |
| Database | PostgreSQL | Neon | Free |
| AI | Claude API (Anthropic) | API | Pay per use |
| Automation | N8N | Self-hosted on Railway | Free |
| Email | Resend | Resend.com | Free (100/day) |
| PDF | WeasyPrint (Python) | Same as backend | Free |
| Code | GitHub | GitHub.com | Free |

**Estimated monthly cost: ~$10–30 during validation**

---

## Team Structure

| Member | Role | Primary Responsibility |
|---|---|---|
| Member B | Backend Lead | Database + All APIs (STARTS FIRST) |
| Member A | Patient Frontend | All patient-facing pages |
| Member C | AI + Automations | Claude integration + N8N flows |
| Member D | Doctor Frontend + PDF | Doctor dashboard + prescription system |

---

## Project Structure

```
ai-healthcare/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── database.py              # DB connection + session
│   ├── models.py                # All 7 database table models
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variables template
│   ├── routers/
│   │   ├── auth.py              # Login, register, logout
│   │   ├── patients.py          # Patient dashboard, appointments
│   │   ├── appointments.py      # Booking, available slots
│   │   ├── intake.py            # AI chat session management
│   │   └── doctor.py           # Doctor dashboard, encounters, prescriptions
│   └── utils/
│       ├── ai.py                # Claude API calls + prompt building
│       ├── pdf.py               # WeasyPrint PDF generation
│       └── email.py             # Resend email sending
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Routes
│   │   ├── main.jsx             # Entry point
│   │   ├── context/
│   │   │   └── AuthContext.jsx  # Global auth state
│   │   ├── hooks/
│   │   │   ├── useAuth.js       # Auth hook
│   │   │   └── usePolling.js    # Appointment polling hook
│   │   ├── utils/
│   │   │   └── api.js           # Axios instance + API calls
│   │   ├── pages/
│   │   │   ├── patient/
│   │   │   │   ├── Register.jsx
│   │   │   │   ├── Login.jsx
│   │   │   │   ├── Dashboard.jsx
│   │   │   │   ├── BookAppointment.jsx  # Booking + chat on same page
│   │   │   │   └── Prescriptions.jsx
│   │   │   └── doctor/
│   │   │       ├── Login.jsx
│   │   │       ├── Dashboard.jsx
│   │   │       ├── Encounter.jsx
│   │   │       └── PatientHistory.jsx
│   │   └── components/
│   │       ├── patient/
│   │       │   ├── BookingForm.jsx     # Step 1
│   │       │   ├── BookingConfirmed.jsx # Step 2 (with polling)
│   │       │   └── IntakeChat.jsx      # Step 3 (chat UI)
│   │       ├── doctor/
│   │       │   ├── IntakeSummary.jsx
│   │       │   ├── PrescriptionForm.jsx
│   │       │   └── PatientTimeline.jsx
│   │       └── shared/
│   │           ├── Navbar.jsx
│   │           └── ProtectedRoute.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── .env.example
└── README.md
```

---

## Local Setup (Read This First)

### Prerequisites
- Node.js 18+ installed
- Python 3.11+ installed
- Git installed
- A code editor (VS Code recommended)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_TEAM/ai-healthcare.git
cd ai-healthcare
```

### Step 2 — Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Now open .env and fill in your API keys (see API Keys section below)

# Run the backend
uvicorn main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs` ← very useful, shows all endpoints

### Step 3 — Frontend Setup

```bash
# Open a new terminal tab
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
# VITE_API_URL=http://localhost:8000

# Run the frontend
npm run dev
```

Frontend runs at: `http://localhost:5173`

### Step 4 — Database Setup

Create a free account at [neon.tech](https://neon.tech).
Copy your connection string into backend `.env` as `DATABASE_URL`.
Tables are created automatically when you first run the backend.

---

## API Keys You Need

| Key | Where to Get | Who Needs It |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com | Member C |
| `DATABASE_URL` | neon.tech | Member B |
| `RESEND_API_KEY` | resend.com | Member C |
| `N8N_WEBHOOK_URL` | Your N8N instance | Member C |
| `SECRET_KEY` | Generate any random string | Member B |

---

## Git Workflow (All Members Follow This)

```bash
# Before starting work each day
git pull origin main

# Create your own branch for each feature
git checkout -b feature/patient-login

# Make changes, then commit often
git add .
git commit -m "Add patient login page with form validation"

# Push your branch
git push origin feature/patient-login

# On GitHub: open a Pull Request → ask a teammate to review
# After approval: merge to main
```

### Branch Naming Convention
```
feature/patient-login       ← new feature
fix/booking-form-error      ← bug fix
update/ai-prompt-v2         ← updating existing thing
```

---

## Environment Variables

### Backend `.env`
```env
DATABASE_URL=postgresql://user:password@host/dbname
SECRET_KEY=your-random-secret-key-at-least-32-chars
ANTHROPIC_API_KEY=sk-ant-...
RESEND_API_KEY=re_...
N8N_WEBHOOK_BOOKING=https://your-n8n.com/webhook/booking
FRONTEND_URL=http://localhost:5173
```

### Frontend `.env`
```env
VITE_API_URL=http://localhost:8000
```

---

## Database Tables (7 total)

```
patients              → registered patients
doctors               → registered doctors (added manually for MVP)
appointments          → booked appointments
intake_sessions       → AI chat sessions (one per appointment)
conversation_messages → every message in every chat
encounters            → doctor's diagnosis + treatment notes
prescriptions         → final prescription + PDF link
```

---

## API Endpoints (16 total)

```
Auth (4 endpoints)
  POST /api/auth/register
  POST /api/auth/login
  POST /api/auth/logout
  GET  /api/auth/me

Patient (4 endpoints)
  GET  /api/patients/me/dashboard
  GET  /api/patients/me/appointments
  POST /api/appointments
  GET  /api/patients/me/prescriptions

AI Intake (4 endpoints)
  POST /api/intake/sessions
  POST /api/intake/sessions/{id}/messages
  GET  /api/intake/sessions/{id}/context
  POST /api/intake/sessions/{id}/complete

Doctor (4 endpoints)
  GET  /api/doctor/dashboard
  GET  /api/doctor/patients/{id}/history
  POST /api/encounters
  POST /api/encounters/{id}/complete
```

---

## Weekly Timeline

| Week | Goal | Success Metric |
|---|---|---|
| 1 | Foundation | Backend runs, DB tables exist, login works |
| 2 | Core pages | Patient can register, book, see dashboard |
| 3 | AI chat works | Full intake flow saves to DB |
| 4 | Doctor side | Doctor sees summary, generates prescription |
| 5 | End-to-end | One full patient journey works completely |

---

## Rules for the Team

1. **Member B starts first** — nobody else can connect to real data until the database and auth APIs exist
2. **Build with fake/hardcoded data first** — don't wait for APIs, mock them
3. **Agree on API response format before building** — 30 min meeting saves days of confusion
4. **Commit small and often** — don't write 500 lines then commit everything at once
5. **If stuck for 30+ minutes** — ask a teammate or ask Claude
6. **Don't add features not in this plan** — validate the core first
7. **Test together every Friday** — one person acts as patient, one as doctor

---

## Need Help?

- Backend API docs: `http://localhost:8000/docs` (auto-generated by FastAPI)
- Claude API docs: `https://docs.anthropic.com`
- N8N docs: `https://docs.n8n.io`
- Tailwind CSS: `https://tailwindcss.com/docs`
- FastAPI: `https://fastapi.tiangolo.com`
