# Implementation Guide — Local Setup & Testing

## Before You Start — Get These Accounts (30 minutes)

| Service | URL | Who Needs It | What To Get |
|---|---|---|---|
| GitHub | github.com | ALL | Create org, invite team |
| Neon (database) | neon.tech | Member B | Connection string |
| Anthropic | console.anthropic.com | Member C | API key |
| Resend (email) | resend.com | Member C | API key |

---

## Step 1 — GitHub Repository Setup (Member B does this, 15 mins)

```bash
# Create the repo on GitHub first (github.com → New Repository)
# Name: ai-healthcare
# Visibility: Private
# Initialize with README: No (we have our own)

# Then push this code:
cd ai-healthcare
git init
git add .
git commit -m "Initial project scaffold — all base files"
git branch -M main
git remote add origin https://github.com/YOUR_ORG/ai-healthcare.git
git push -u origin main
```

Then invite your 3 teammates:
GitHub repo → Settings → Collaborators → Add people (by email or username)

Each teammate then:
```bash
git clone https://github.com/YOUR_ORG/ai-healthcare.git
cd ai-healthcare
```

---

## Step 2 — Backend Setup (Member B, Day 1)

```bash
cd backend

# 1. Create Python virtual environment
python -m venv venv

# 2. Activate it
source venv/bin/activate       # Mac/Linux
# OR
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Open .env and fill in:
# DATABASE_URL = your Neon connection string
# SECRET_KEY = any 32+ char random string
# (Leave AI keys blank for now — Member C adds those)

# 5. Start the backend
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
INFO:     Application startup complete.
```

**Verify everything works:**
Open http://localhost:8000/docs
You should see a page with all API endpoints listed.

---

## Step 3 — Add Test Doctors to Database (Member B, Day 1)

The admin panel doesn't exist yet, so add doctors directly.
Open a new terminal (keep backend running in first terminal):

```bash
cd backend
source venv/bin/activate

python3 -c "
from passlib.context import CryptContext
pwd = CryptContext(schemes=['bcrypt'])
print(pwd.hash('doctor123'))
"
# Copy the output — it's the hashed password
```

Then open http://localhost:8000/docs, find POST /api/auth/login,
and add doctors via a direct SQL approach.

Alternatively, create a quick setup script:

```bash
# Create this file: backend/seed_doctors.py
cat > seed_doctors.py << 'EOF'
from database import SessionLocal
from models import Doctor
from passlib.context import CryptContext

db = SessionLocal()
pwd = CryptContext(schemes=["bcrypt"])

doctors = [
    Doctor(
        first_name="Sarah", last_name="Johnson",
        email="sarah@clinic.com",
        password_hash=pwd.hash("doctor123"),
        specialization="Cardiologist",
        license_number="MED-2024-001"
    ),
    Doctor(
        first_name="Ahmed", last_name="Khan",
        email="ahmed@clinic.com",
        password_hash=pwd.hash("doctor123"),
        specialization="General Physician",
        license_number="MED-2024-002"
    ),
]

for d in doctors:
    existing = db.query(Doctor).filter(Doctor.email == d.email).first()
    if not existing:
        db.add(d)

db.commit()
print("Doctors added successfully!")
db.close()
EOF

python3 seed_doctors.py
```

---

## Step 4 — Frontend Setup (Member A, Day 4)

```bash
cd frontend

# 1. Install Node dependencies
npm install

# 2. Set up environment
cp .env.example .env
# Content: VITE_API_URL=http://localhost:8000

# 3. Start frontend
npm run dev
```

**Expected output:**
```
  VITE v5.x.x  ready in 300ms
  ➜  Local:   http://localhost:5173/
```

Open http://localhost:5173 — you should see the app.

---

## Step 5 — Configure Tailwind CSS (Member A, Day 4)

Create `frontend/tailwind.config.js`:
```js
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: { extend: {} },
  plugins: [],
}
```

Create `frontend/postcss.config.js`:
```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

Create `frontend/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Create `frontend/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Healthcare Assistant</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

Create `frontend/src/main.jsx`:
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

Create `frontend/vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
```

---

## Step 6 — Test the Full Booking + Chat Flow (End of Week 2)

Run through this manually to verify everything works:

### Test as Patient
```
1. Open http://localhost:5173/register
2. Register: name=Ahmed Khan, email=ahmed@test.com, password=test123
3. Should redirect to dashboard
4. Click "Book Appointment"
5. Select Dr. Sarah Johnson
6. Pick any future date and time
7. Click "Confirm Booking"
8. Watch: spinner → "Booking Confirmed!" → chat appears
9. Chat with the AI: answer a few questions
10. Click "I'm done answering"
11. Should show "Check-in Complete!"
```

### Test as Doctor
```
1. Open http://localhost:5173/doctor/login
2. Login: email=sarah@clinic.com, password=doctor123
3. Should see dashboard with Ahmed's appointment
4. See intake status: "Intake Done"
5. Click on Ahmed's appointment
6. See AI summary on the right
7. Click "Start Encounter"
8. Fill in: diagnosis + 1 medication
9. Click "Complete & Send Prescription"
10. Check Ahmed's email — should receive prescription
```

---

## Step 7 — Add AI (Member C, Week 2)

```bash
# Add to backend/.env
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Restart backend
uvicorn main:app --reload --port 8000
```

**Test AI is working:**
```bash
# Register a patient, book appointment, start intake session
# Then send a message:
curl -X POST http://localhost:8000/api/intake/sessions/1/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "I have chest pain"}'

# Should return an AI response asking follow-up questions
```

---

## Step 8 — N8N Setup (Member C, Week 2)

```bash
# Install and run N8N locally
npx n8n
# Opens at http://localhost:5678
```

**Create Workflow 1 — Doctor Notification:**
1. Open http://localhost:5678
2. New Workflow → Add node → Webhook
3. Set webhook path: `/webhook/booking`
4. Add node → Send Email
5. Set To: `{{ $json.doctor_email }}`
6. Subject: `New Appointment: {{ $json.patient_name }}`
7. Body: Patient name, date, time, reason
8. Activate workflow
9. Copy webhook URL → add to backend/.env as N8N_WEBHOOK_BOOKING

---

## Common Errors & Fixes

### Backend won't start
```
Error: No module named 'fastapi'
Fix: Make sure virtual environment is activated
     source venv/bin/activate  (Mac/Linux)
     venv\Scripts\activate     (Windows)
```

```
Error: Connection refused to database
Fix: Check DATABASE_URL in .env — is it the right Neon connection string?
```

```
Error: Table doesn't exist
Fix: Backend creates tables on startup automatically.
     If they're not created, check database connection.
```

### Frontend API errors
```
Error: Network Error / CORS
Fix: Is backend running on port 8000?
     Is VITE_API_URL=http://localhost:8000 in frontend/.env?
     Restart both frontend and backend after changing .env
```

```
Error: 401 Unauthorized
Fix: Token is missing or expired.
     Clear localStorage and log in again.
```

### AI not responding
```
Error: Claude API error
Fix: Check ANTHROPIC_API_KEY in backend/.env
     Make sure it starts with sk-ant-
     Check you have credits in Anthropic console
```

### PDF generation fails
```
Error: WeasyPrint installation error
Fix (Ubuntu/Debian): sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
Fix (Mac): brew install pango
```

---

## Local Testing Checklist (Friday Sessions)

Run through this every Friday with the full team:

**Auth**
- [ ] Patient can register
- [ ] Patient can login
- [ ] Doctor can login
- [ ] Wrong password gives proper error
- [ ] Token persists across page refresh

**Patient Flow**
- [ ] Patient sees correct dashboard after login
- [ ] Patient can book appointment with a doctor
- [ ] Polling works: confirmed card appears before chat
- [ ] Chat starts automatically after confirmation
- [ ] AI responds to patient messages
- [ ] Patient can complete intake
- [ ] Patient sees prescription in dashboard after doctor completes encounter

**Doctor Flow**
- [ ] Doctor sees today's appointments
- [ ] Intake status shows correctly (Done / Pending / None)
- [ ] Doctor can see AI summary for completed intakes
- [ ] Doctor can start encounter
- [ ] Doctor can fill diagnosis and medicines
- [ ] Doctor can complete encounter
- [ ] PDF is generated (check backend/pdfs/ folder)
- [ ] Patient receives prescription email

**AI Quality**
- [ ] AI asks questions in the right order
- [ ] AI doesn't suggest diagnoses
- [ ] Returning patient — AI mentions last visit
- [ ] Summary is accurate and readable

---

## Deployment (Week 5)

### Frontend → Vercel
```bash
# Install Vercel CLI
npm i -g vercel

cd frontend
vercel

# Follow prompts:
# Project name: ai-healthcare
# Framework: Vite
# Build command: npm run build
# Output directory: dist

# Add environment variable in Vercel dashboard:
# VITE_API_URL = https://your-backend.railway.app
```

### Backend → Railway
```
1. Create account at railway.app
2. New Project → Deploy from GitHub repo
3. Select: ai-healthcare repo → backend folder
4. Add environment variables (all from your .env)
5. Railway auto-detects Python and deploys
6. Copy the Railway URL → set as VITE_API_URL in Vercel
```

### N8N → Railway (free self-hosting)
```
1. New service in Railway
2. Deploy from Docker image: n8nio/n8n
3. Set port: 5678
4. Copy Railway N8N URL → update backend .env N8N_WEBHOOK_BOOKING
```
