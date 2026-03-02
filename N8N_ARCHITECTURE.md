# N8N — Where It's Used & Why

## The Exact Role of N8N

N8N handles all **time-based and notification logic** so the backend stays clean.
The backend's job is data. N8N's job is communication and scheduling.

```
Backend (FastAPI)                N8N
─────────────────                ────────────────────────────────
Save appointment to DB    ──→    Notify doctor by email
                                 Schedule 24hr patient reminder

Intake session completed  ──→    Notify doctor (intake ready)

Encounter completed       ──→    Send prescription email to patient
                                 Schedule follow-up reminder

Daily cron (N8N owned)   ──→    Find tomorrow's appointments
                                 Send intake reminder to patients
                                 who haven't done their check-in yet
```

---

## The 3 Webhook Endpoints (Backend Fires → N8N Receives)

### 1. POST to N8N_WEBHOOK_BOOKING
**Fired from:** `routers/appointments.py` — after appointment saved  
**Payload:**
```json
{
  "appointment_id": 42,
  "patient_name": "Ahmed Khan",
  "patient_email": "ahmed@email.com",
  "doctor_name": "Dr. Sarah Johnson",
  "doctor_email": "sarah@clinic.com",
  "scheduled_date": "2026-03-05",
  "scheduled_time": "10:00",
  "reason": "chest pain"
}
```

### 2. POST to N8N_WEBHOOK_INTAKE_COMPLETE
**Fired from:** `routers/intake.py` — after AI summary generated  
**Payload:**
```json
{
  "appointment_id": 42,
  "patient_name": "Ahmed Khan",
  "doctor_name": "Dr. Sarah Johnson",
  "doctor_email": "sarah@clinic.com",
  "scheduled_time": "10:00",
  "risk_level": "medium",
  "ai_summary": "Patient reports chest tightness for 1 week..."
}
```

### 3. POST to N8N_WEBHOOK_PRESCRIPTION
**Fired from:** `routers/doctor.py` — after encounter completed and PDF generated  
**Payload:**
```json
{
  "prescription_id": 15,
  "patient_name": "Ahmed Khan",
  "patient_email": "ahmed@email.com",
  "doctor_name": "Dr. Sarah Johnson",
  "diagnosis": "Anxiety-related chest tightness",
  "medications": [
    {"drug_name": "Propranolol", "dosage": "20mg", "frequency": "twice daily", "duration": "14 days"}
  ],
  "follow_up_date": "2026-03-19",
  "pdf_download_url": "http://your-api.com/api/prescriptions/15/pdf"
}
```

---

## The 1 Internal API (N8N Calls → Backend)

N8N's daily cron needs to know which patients need an intake reminder.
Rather than querying the database directly, N8N calls this backend endpoint:

```
GET /api/internal/reminders/intake-due
Returns: list of appointments tomorrow with no completed intake
```

This is a protected internal endpoint with a secret key header (not JWT).

---

## The 4 N8N Workflows

| # | Workflow | Trigger | Does |
|---|---|---|---|
| 1 | Booking Notification | Webhook (from backend) | Emails doctor about new appointment |
| 2 | Intake Complete Alert | Webhook (from backend) | Emails doctor "intake ready" with summary + risk level |
| 3 | Prescription Delivery | Webhook (from backend) | Emails patient prescription PDF + schedules follow-up reminder |
| 4 | Daily Intake Reminder | Cron (8AM every day) | Finds patients with tomorrow's appointment + no intake → emails them |

---

## Environment Variables to Add

```env
# In backend/.env
N8N_WEBHOOK_BOOKING=https://your-n8n.com/webhook/booking-confirmed
N8N_WEBHOOK_INTAKE_COMPLETE=https://your-n8n.com/webhook/intake-complete
N8N_WEBHOOK_PRESCRIPTION=https://your-n8n.com/webhook/prescription-sent
N8N_INTERNAL_SECRET=your-random-internal-secret-key

# In N8N (as credentials or environment)
RESEND_API_KEY=re_your_key
BACKEND_API_URL=https://your-api.railway.app
N8N_INTERNAL_SECRET=same-random-internal-secret-key (must match backend)
CLINIC_FROM_EMAIL=noreply@yourclinic.com
```
