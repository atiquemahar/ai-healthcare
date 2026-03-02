# N8N Setup Guide — How to Import and Configure Workflows

## Step 1 — Install N8N Locally (for development)

```bash
# Option A: npx (no install needed)
npx n8n
# Opens at http://localhost:5678

# Option B: global install
npm install -g n8n
n8n start
```

---

## Step 2 — Set N8N Environment Variables

Before importing workflows, set these in N8N.

Go to: N8N Settings → Environment Variables (or set in your shell):

```bash
# The Resend API key for sending emails
RESEND_API_KEY=re_your_key_here

# Your backend API URL
BACKEND_API_URL=http://localhost:8000

# Must match N8N_INTERNAL_SECRET in backend .env
N8N_INTERNAL_SECRET=your-random-secret-key

# The email address emails are sent FROM
CLINIC_FROM_EMAIL=noreply@yourclinic.com

# Frontend URL (for links in emails)
FRONTEND_URL=http://localhost:5173
```

In N8N: Settings (gear icon) → n8n environment variables → Add each one.

---

## Step 3 — Import All 4 Workflows

For each workflow JSON file:

1. Open N8N at http://localhost:5678
2. Click "Workflows" in left sidebar
3. Click "Add workflow" → "Import from file"
4. Select the JSON file from `n8n-workflows/` folder
5. Click "Import"
6. Repeat for all 4 files

After import you should see 4 workflows:
```
✓ Workflow 1 — Booking Confirmed → Doctor Notification
✓ Workflow 2 — Intake Complete → Alert Doctor
✓ Workflow 3 — Prescription Sent → Email Patient + Schedule Follow-up
✓ Workflow 4 — Daily 8AM → Intake Reminders for Tomorrow's Patients
```

---

## Step 4 — Get Webhook URLs

After importing Workflows 1, 2, and 3:

1. Open each workflow
2. Click on the Webhook node (first node)
3. Look for "Webhook URL" — copy it
4. It looks like: `http://localhost:5678/webhook/booking-confirmed`

Add these to your backend `.env`:

```env
N8N_WEBHOOK_BOOKING=http://localhost:5678/webhook/booking-confirmed
N8N_WEBHOOK_INTAKE_COMPLETE=http://localhost:5678/webhook/intake-complete
N8N_WEBHOOK_PRESCRIPTION=http://localhost:5678/webhook/prescription-sent
```

Restart backend after adding these.

---

## Step 5 — Activate All Workflows

Each workflow must be ACTIVATED to receive webhooks and run on schedule.

In each workflow:
1. Click the toggle at top right: `Inactive → Active`
2. Green dot = active and listening

⚠️ Workflow 3 uses a "Wait" node. N8N must stay running for the wait to complete.
On Railway (production), this is automatic. Locally, don't close your terminal.

---

## Step 6 — Test Each Workflow Manually

### Test Workflow 1 (Booking Notification)
```bash
curl -X POST http://localhost:5678/webhook/booking-confirmed \
  -H "Content-Type: application/json" \
  -d '{
    "appointment_id": 1,
    "patient_name": "Ahmed Khan",
    "patient_email": "ahmed@test.com",
    "doctor_name": "Dr. Sarah Johnson",
    "doctor_email": "sarah@clinic.com",
    "scheduled_date": "2026-03-05",
    "scheduled_time": "10:00",
    "reason": "chest pain"
  }'
```
Expected: Doctor email arrives. Check N8N execution log for success/error.

### Test Workflow 2 (Intake Alert)
```bash
curl -X POST http://localhost:5678/webhook/intake-complete \
  -H "Content-Type: application/json" \
  -d '{
    "appointment_id": 1,
    "patient_name": "Ahmed Khan",
    "doctor_name": "Dr. Sarah Johnson",
    "doctor_email": "sarah@clinic.com",
    "scheduled_time": "10:00",
    "risk_level": "high",
    "ai_summary": "Patient reports severe chest pain for 3 days with shortness of breath."
  }'
```
Expected: Urgent red email to doctor (high risk path).

### Test Workflow 3 (Prescription)
```bash
curl -X POST http://localhost:5678/webhook/prescription-sent \
  -H "Content-Type: application/json" \
  -d '{
    "prescription_id": 1,
    "patient_name": "Ahmed Khan",
    "patient_email": "ahmed@test.com",
    "doctor_name": "Dr. Sarah Johnson",
    "diagnosis": "Anxiety-related chest tightness",
    "medications": [{"drug_name": "Propranolol", "dosage": "20mg", "frequency": "twice daily", "duration": "14 days"}],
    "follow_up_date": "2026-03-19",
    "pdf_download_url": "http://localhost:8000/api/prescriptions/1/pdf"
  }'
```
Expected: Prescription email sent to patient. Wait node activates for follow-up.

### Test Workflow 4 (Daily Cron — manual trigger)
In N8N:
1. Open Workflow 4
2. Click "Test workflow" button (plays the cron manually)
3. Should call your backend and email any patients with tomorrow's appointments

---

## How Data Flows Through Each Workflow

### Workflow 1 — Booking
```
Backend saves appointment
        ↓
Backend POST → N8N webhook
        ↓
N8N immediately responds 200 (so backend isn't blocked)
        ↓ (in parallel)
N8N calls Resend API
        ↓
Doctor receives email: "New appointment booked"
```

### Workflow 2 — Intake Alert
```
Backend generates AI summary
        ↓
Backend POST → N8N webhook
        ↓
N8N checks: risk_level == "high"?
        ↓ YES                      ↓ NO
Doctor gets              Doctor gets
🚨 RED urgent email      ✅ GREEN normal email
```

### Workflow 3 — Prescription + Follow-up
```
Doctor clicks Complete Encounter
        ↓
Backend generates PDF → saves → POST → N8N webhook
        ↓
N8N formats medication list
        ↓
N8N emails patient (with PDF link)
        ↓
N8N checks: does follow_up_date exist?
        ↓ YES                      ↓ NO
Wait until                     Workflow ends
2 days before follow-up
        ↓
Email patient: "Follow-up in 2 days, book now"
```

### Workflow 4 — Daily Cron
```
Every day at 8:00 AM
        ↓
N8N calls: GET /api/internal/reminders/intake-due
  (with secret header for auth)
        ↓
Backend returns list of tomorrow's appointments with no intake
        ↓
N8N splits into individual patients
        ↓
For EACH patient → N8N emails: "Complete your check-in →"
```

---

## Deployment to Railway (Production)

```
1. In Railway: New Service → Docker Image → n8nio/n8n
2. Set environment variables (same as Step 2 above)
3. Set PORT=5678
4. Deploy → get Railway N8N URL (e.g. https://n8n-xxx.railway.app)
5. Re-import workflows OR update webhook URLs in already-imported ones
6. Update backend .env with production webhook URLs
7. Update BACKEND_API_URL in N8N to production backend URL
8. Activate all 4 workflows
```

⚠️ Important: On Railway, N8N needs a volume for persistent storage.
Add a Railway volume at `/home/node/.n8n` so your workflows survive restarts.

---

## Troubleshooting

**Webhook returns 404**
→ Workflow is not activated. Toggle to Active.

**Email not received**
→ Check Resend API key is correct in N8N environment variables.
→ Check Resend dashboard — is the domain verified?
→ For testing, use a Resend test email address.

**Workflow 4 backend call fails (403)**
→ N8N_INTERNAL_SECRET in N8N doesn't match N8N_INTERNAL_SECRET in backend .env

**Workflow 3 wait node not firing**
→ N8N process must stay running. On Railway this is automatic.
   Locally: don't close the terminal running N8N.

**Workflow 2 always goes to "normal" path even for high risk**
→ risk_level value must be exactly "high" (lowercase string).
   Check the IF node condition matches your backend's output.
