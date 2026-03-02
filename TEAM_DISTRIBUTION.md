# Team Work Distribution

## Overview

```
Member B → Backend + Database     (STARTS DAY 1 ALONE)
Member A → Patient Frontend       (Starts Day 4)
Member C → AI Chat + N8N          (Starts Day 4)
Member D → Doctor Frontend + PDF  (Starts Day 4)
```

Everyone uses the same GitHub repo. Different people work in different folders.
Conflicts are rare if you stick to your folder.

---

## Member B — Backend Lead

### Your Folder
```
backend/
```

### Your Responsibility
You are the foundation. Nobody else can work with real data until your database and
APIs exist. You start first and you are the unblocking person for the whole team.

### Files You Own
```
backend/main.py          ← app entry point (already created)
backend/database.py      ← DB connection (already created)
backend/models.py        ← all 7 tables (already created)
backend/schemas.py       ← request/response shapes (already created)
backend/routers/auth.py  ← login, register (already created)
backend/routers/patients.py   ← patient APIs (already created)
backend/routers/appointments.py ← booking APIs (already created)
backend/routers/doctor.py     ← doctor APIs (already created)
backend/utils/email.py        ← email sending (already created)
backend/utils/pdf.py          ← PDF generation (already created)
```

### Week 1 Tasks (Days 1-5, working alone)
- [ ] Set up Python virtual environment
- [ ] Install all requirements from requirements.txt
- [ ] Create .env file from .env.example, add real DATABASE_URL from Neon
- [ ] Run `uvicorn main:app --reload` — fix any startup errors
- [ ] Open http://localhost:8000/docs — verify all endpoints are listed
- [ ] Manually add 2 doctors directly in the database for testing:
      ```sql
      INSERT INTO doctors (first_name, last_name, email, password_hash, specialization, license_number)
      VALUES ('Sarah', 'Johnson', 'sarah@clinic.com', '<hashed_password>', 'Cardiologist', 'MED-001');
      ```
      Use Python to hash: `from passlib.context import CryptContext; CryptContext(['bcrypt']).hash('password123')`
- [ ] Test register endpoint via /docs
- [ ] Test login endpoint via /docs
- [ ] Share your LOCAL API URL with the team (e.g. http://localhost:8000)

### Week 2 Tasks
- [ ] Verify all 16 endpoints return correct data
- [ ] Write a simple test script that registers a patient and books an appointment
- [ ] Document any endpoint format changes in the team chat
- [ ] Help Member A connect their pages to real APIs

### Week 3 Tasks
- [ ] Support Member C on intake API questions
- [ ] Support Member D on encounter/prescription API questions
- [ ] Add proper error messages to all endpoints
- [ ] Test the full flow: book → intake → encounter → prescription

### Week 4 Tasks
- [ ] Security review: check every query filters by the right user
- [ ] Test with multiple patients and doctors
- [ ] Prepare for Railway deployment

### What to Tell Other Members
Send this message to the team on Day 4:
```
Backend is ready. Here's what you need:
- API base URL: http://localhost:8000
- API docs: http://localhost:8000/docs
- Test patient: email=test@patient.com, password=test123 (register via /docs)
- Test doctor: email=sarah@clinic.com, password=doctor123
- Doctor ID: 1 (use this when building booking form)
```

---

## Member A — Patient Frontend

### Your Folder
```
frontend/src/pages/patient/
frontend/src/components/patient/   (if you need shared components)
```

### Files You Build
```
pages/patient/Register.jsx        ← registration form
pages/patient/Login.jsx           ← login form
pages/patient/Dashboard.jsx       ← patient home (appointments, prescriptions)
pages/patient/BookAppointment.jsx ← ALREADY CREATED (booking + chat flow)
pages/patient/Prescriptions.jsx   ← list of past prescriptions
```

### Week 1 Tasks (Days 1-5, while waiting for backend)
- [ ] Set up React project: `npm install` in frontend/
- [ ] Run `npm run dev` — verify it starts
- [ ] Build Register.jsx with hardcoded fake data (no API yet)
- [ ] Build Login.jsx with hardcoded fake data
- [ ] Build Dashboard.jsx with hardcoded fake data
      (fake upcoming appointments, fake past visits)
- [ ] Set up routing in App.jsx (already created — just verify)
- [ ] Set up Tailwind CSS styling on all pages

### Week 2 Tasks (Backend is ready)
- [ ] Connect Register.jsx to POST /api/auth/register
- [ ] Connect Login.jsx to POST /api/auth/login, save token
- [ ] Connect Dashboard.jsx to GET /api/patients/me/dashboard
- [ ] Review BookAppointment.jsx (already created) — understand the flow
- [ ] Test: register → login → see dashboard → book appointment → chat appears

### Week 3 Tasks
- [ ] Build Prescriptions.jsx — list all prescriptions, show PDF download button
- [ ] Add "Complete your pre-visit check-in" banner on Dashboard
      (shown when patient has upcoming appointment with no intake)
- [ ] Handle edge cases: loading states, error states, empty states
- [ ] Polish all pages for consistent look

### Week 4 Tasks
- [ ] Full patient flow test: register → book → chat → view prescription
- [ ] Fix any UI bugs
- [ ] Test on mobile (does it look good on phone?)

### How to Build with Fake Data First

```jsx
// Example: Dashboard.jsx with fake data
// Week 1: use this
const fakeData = {
  patient_name: "Ahmed Khan",
  upcoming: [{
    appointment_id: 1,
    doctor_name: "Dr. Sarah Johnson",
    scheduled_date: "2026-03-05",
    scheduled_time: "10:00",
    status: "scheduled",
    intake_done: false,
  }],
  past_visits: [],
}

// Week 2: replace with real API call
const { data } = await patientAPI.dashboard()
```

### Key Component: BookAppointment.jsx
This file is already written. Study it carefully:
- Line 30-90: Form submission + polling logic
- Line 91-110: Chat initialization
- Line 111-140: Message sending
- Line 180+: The UI rendering per step

---

## Member C — AI Chat + N8N

### Your Folder
```
backend/utils/ai.py           ← AI prompts and Claude calls
backend/routers/intake.py     ← intake API endpoints
(N8N is configured on the N8N dashboard, not in code files)
```

### Your Responsibility
Making Claude work correctly. The AI prompt quality directly affects the product quality.
Also building the 2 N8N workflows.

### Files You Own/Modify
```
backend/utils/ai.py       ← ALREADY CREATED — review and improve the system prompt
backend/routers/intake.py ← ALREADY CREATED — review the chat logic
```

### Week 1 Tasks
- [ ] Create Anthropic account → get API key → add to backend .env
- [ ] Test Claude API directly in Python:
      ```python
      import anthropic
      client = anthropic.Anthropic(api_key="your-key")
      response = client.messages.create(
          model="claude-opus-4-20250514",
          max_tokens=500,
          messages=[{"role": "user", "content": "Say hello"}]
      )
      print(response.content[0].text)
      ```
- [ ] Read through utils/ai.py carefully
- [ ] Read through routers/intake.py carefully
- [ ] Improve the system prompt in build_system_prompt() — make it sound better
- [ ] Test the full chat flow via Postman or /docs:
      1. Start session: POST /api/intake/sessions
      2. Send messages: POST /api/intake/sessions/{id}/messages
      3. Complete: POST /api/intake/sessions/{id}/complete
      4. Check that summary is generated correctly

### Important: The __start__ Message
In BookAppointment.jsx, when chat starts, it sends `__start__` as the first message.
Your AI should detect this and respond with a greeting, not reply to "__start__".
Add this to the system prompt:
```
If the user's first message is exactly "__start__", respond with your opening greeting.
Do not reference the word "start" in your response.
```

### Week 2 Tasks
- [ ] Test with returning patient (second booking by same patient)
      Verify AI mentions their previous visit
- [ ] Test summary generation — does it extract data correctly?
- [ ] Tweak prompt until summary quality is high
- [ ] Set up N8N (see N8N section below)

### Week 3 Tasks
- [ ] N8N Workflow 1: Booking confirmation → notify doctor
- [ ] N8N Workflow 2: Prescription sent → confirmation email to patient
- [ ] Test with different patient scenarios
- [ ] Improve risk detection: "high" risk should trigger for serious symptoms

### N8N Setup

**Step 1:** Install N8N locally for testing
```bash
npx n8n
# Opens at http://localhost:5678
```

**Step 2:** Workflow 1 — Doctor Notification on New Booking
```
Trigger: Webhook (POST) → Receive booking data from backend
Node 2:  Send Email (via Resend/Gmail SMTP)
         To: doctor email
         Subject: "New appointment: {patient_name} on {date}"
         Body: Patient name, date, time, reason
```

**Step 3:** Workflow 2 — Prescription Email
```
Trigger: Webhook (POST) → Receive prescription data
Node 2:  HTTP Request → Download PDF from backend
Node 3:  Send Email to patient with PDF attached
```

**Step 4:** Copy webhook URLs into backend .env:
```
N8N_WEBHOOK_BOOKING=http://localhost:5678/webhook/booking
```

### Testing AI Quality Checklist
Test these scenarios and verify the output makes sense:
- [ ] New patient, first visit, chest pain symptoms
- [ ] Returning patient — AI mentions last visit
- [ ] Patient with allergies — AI asks about them
- [ ] Patient mentions feeling suicidal — AI gives emergency response
- [ ] Summary JSON is valid and contains the right fields

---

## Member D — Doctor Frontend + PDF

### Your Folder
```
frontend/src/pages/doctor/
frontend/src/components/doctor/
```

### Files You Build
```
pages/doctor/Login.jsx          ← doctor login
pages/doctor/Dashboard.jsx      ← today's appointments list
pages/doctor/Encounter.jsx      ← treat patient + fill prescription
pages/doctor/PatientHistory.jsx ← full patient timeline
```

### Week 1 Tasks (while waiting for backend)
- [ ] Set up your doctor pages with hardcoded fake data
- [ ] Doctor Login.jsx — same structure as patient login, different route
- [ ] Dashboard.jsx with fake appointment list:
      ```
      09:00 — Ahmed K. — Intake Done — [Start]
      09:30 — Maria R. — Intake Done ⚠ High Risk — [Start]
      10:00 — John D. — Intake Pending — [Start]
      ```
- [ ] Encounter.jsx layout — TOP: patient summary, MIDDLE: forms, BOTTOM: prescription

### Week 2 Tasks
- [ ] Connect Doctor Login to POST /api/auth/login (role=doctor)
- [ ] Connect Dashboard to GET /api/doctor/dashboard
- [ ] Click patient → show intake summary panel on right side
- [ ] "Start Encounter" button → POST /api/doctor/encounters

### Week 3 Tasks
- [ ] Build full Encounter.jsx form:
      - Examination notes text area
      - Diagnosis input (text field for MVP, not dropdown)
      - Add medicine form: name, dosage, frequency, duration
      - Additional instructions
      - Follow-up date picker
      - "Complete & Send Prescription" button → POST /api/doctor/encounters/{id}/complete
- [ ] Connect PatientHistory.jsx to GET /api/doctor/patients/{id}/history
- [ ] Build the visit timeline UI

### Week 4 Tasks
- [ ] Test full doctor flow: login → dashboard → start encounter → complete → verify email sent
- [ ] Risk level visual indicator:
      - 🟢 Low risk
      - 🟡 Medium risk
      - 🔴 High risk
- [ ] PDF viewing: if pdf_url exists, show "Download Prescription" button
- [ ] Patient history timeline — show visits chronologically

### Encounter Form Example Structure

```jsx
// Encounter.jsx layout
<div className="grid grid-cols-2 gap-6 h-screen">

  {/* Left: Patient Context */}
  <div className="overflow-y-auto border-r p-6">
    <h2>AI Intake Summary</h2>
    <p>{intakeData.ai_summary}</p>

    <h3>Previous Visits</h3>
    {history.map(visit => (
      <div key={visit.encounter_id}>
        <p>{visit.date} — {visit.chief_complaint}</p>
      </div>
    ))}
  </div>

  {/* Right: Doctor fills this */}
  <div className="overflow-y-auto p-6">
    <h2>Examination Notes</h2>
    <textarea onChange={...} />

    <h2>Diagnosis</h2>
    <input type="text" placeholder="e.g., Anxiety-related chest tightness" />

    <h2>Medications</h2>
    {medications.map((med, i) => (
      <MedicationRow key={i} med={med} onChange={...} />
    ))}
    <button onClick={addMedication}>+ Add Medicine</button>

    <button onClick={handleComplete}>
      ✓ Complete & Send Prescription
    </button>
  </div>
</div>
```

---

## Collaboration Rules

### API Contract Meeting (Do This Before Building)
Before Week 2, all 4 members spend 30 minutes together agreeing on:
- What does each API response look like?
- Use the /docs page to verify actual response formats
- Member A/D: "I need this field" → Member B: "It's called this in the response"

### When You're Stuck
1. Check /docs — the actual API response is shown there
2. Check the browser Network tab — see the actual request/response
3. Ask your teammate (don't struggle alone for more than 30 minutes)
4. Ask Claude Opus — paste your code + error + what you expected

### Daily Check-in (5 minutes)
Every day, send one message in group chat:
```
Done today: [what you finished]
Tomorrow: [what you're working on next]
Blocked by: [if anything]
```

### Friday Test Sessions
Every Friday, all 4 members run through the system together:
- Member A acts as patient
- Member D acts as doctor
- Member B watches for API errors
- Member C watches for AI behavior
- Note every bug → fix over the weekend
