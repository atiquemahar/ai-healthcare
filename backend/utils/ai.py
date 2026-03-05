import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# ─── OpenAI Client ──────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")


def _ensure_client() -> bool:
  """
  Returns True if an OpenAI client is configured.
  If not, we don't raise — we let callers fall back to a friendly message so
  local demos still work without a real API key.
  """
  return client is not None


# ─── System Prompt Builder ──────────────────────────────────────────────────────

def build_system_prompt(context: dict) -> str:
  """
  Builds the full system prompt for the intake assistant based on patient context.
  """
  patient_name = context.get("patient_name", "Patient")
  doctor_name = context.get("doctor_name", "the doctor")
  specialization = context.get("doctor_specialization", "")
  appt_date = context.get("appointment_date", "")
  appt_time = context.get("appointment_time", "")
  is_returning = context.get("is_returning_patient", False)
  previous_visits = context.get("previous_visits", [])
  active_meds = context.get("active_medications", [])
  known_allergies = context.get("known_allergies", [])
  known_conditions = context.get("known_conditions", [])

  history_section = ""
  if is_returning and previous_visits:
    history_section = "\n── PATIENT HISTORY (returning patient) ──\n"
    for visit in previous_visits[:5]:
      history_section += (
        f"- {visit.get('date')}: {visit.get('diagnosis')} → "
        f"Prescribed: {visit.get('medications')}\n"
      )

    if active_meds:
      history_section += "\nActive medications:\n"
      for med in active_meds:
        history_section += (
          f"- {med.get('name')} {med.get('dosage')} — {med.get('frequency')}\n"
        )

    if known_allergies:
      history_section += f"\nKnown allergies: {', '.join(known_allergies)}\n"

    if known_conditions:
      history_section += f"\nKnown conditions: {', '.join(known_conditions)}\n"

  returning_instructions = ""
  if is_returning and previous_visits:
    last = previous_visits[0]
    returning_instructions = f"""
── RETURNING PATIENT — ALSO ASK ──
- "Last time you were prescribed {last.get('medications', 'medication')}. Are you still taking it?"
- "Has your condition improved since your visit on {last.get('date', 'last time')}?"
- "Any new symptoms since your last visit?"
"""

  prompt = f"""You are a friendly medical intake assistant.
You are helping collect information before the patient's appointment with {doctor_name}{f' ({specialization})' if specialization else ''}.

YOUR ONLY JOB: Ask questions and collect information. Nothing else.
YOU ARE NOT A DOCTOR. Never diagnose. Never suggest medicines. Never reassure about serious symptoms.

── APPOINTMENT DETAILS ──
Patient Name: {patient_name}
Doctor: {doctor_name}
Appointment: {appt_date} at {appt_time}
{history_section}

── CONVERSATION RULES ──
1. Greet the patient warmly by first name
2. If returning patient: Mention their last visit and ask about progress FIRST
3. Ask ONE question at a time
4. Use simple, everyday language — no medical jargon
5. Be warm and empathetic
6. Keep responses concise (2-3 sentences max per turn)

── QUESTIONS TO ASK (in this order) ──
1. "What brings you in today?" — chief complaint
2. "How long have you had this problem?" — duration
3. "On a scale of 1 to 10, how bad is it?" — severity
4. "Is it constant or does it come and go?" — pattern
5. "Any other symptoms along with this?" — associated symptoms
6. "Are you currently taking any medicines?" — medications
7. "Any allergies we should know about?" — allergies
8. "Has anyone in your family had similar issues?" — family history
9. "How is your sleep and stress lately?" — lifestyle
10. "Anything else you'd like {doctor_name} to know?"
{returning_instructions}

── SAFETY RULES — NEVER VIOLATE ──
- NEVER say "you might have" or "it sounds like you have [condition]"
- NEVER recommend any medicine or treatment
- If patient mentions chest pain + difficulty breathing:
  Say: "This sounds like it needs immediate attention. Please call emergency services or go to the nearest emergency room right away."
- If patient mentions self-harm or suicidal thoughts:
  Say: "I'm concerned about your safety. Please contact emergency services or a crisis helpline right away."
- Always end with "Dr. {doctor_name.replace('Dr. ', '')} will review everything you've shared carefully."

── ENDING THE CONVERSATION ──
After all questions are asked, summarize what was collected and ask:
"Did I capture everything correctly? Anything to add or correct?"
Then say: "Thank you {patient_name.split()[0]}! {doctor_name} will have all this ready for your visit. Take care!"
"""
  return prompt


# ─── Get AI Response ────────────────────────────────────────────────────────────

def get_ai_response(
  patient_message: str,
  conversation_history: list,
  context: dict,
) -> str:
  """
  Send patient message to OpenAI and get response.
  conversation_history: list of {role: 'user'|'assistant', content: str}
  """
  # If no API key is configured, fall back to a canned response so the
  # intake flow still works in local demos.
  if not _ensure_client():
    if patient_message == "__start__":
      return (
        "Hi! I'm your pre‑visit intake assistant. To get ready for your appointment, "
        "can you tell me in your own words what brings you in today?"
      )
    return (
      "Thanks for sharing that. For this local demo, I'm not connected to the live "
      "AI service, but your doctor will still review everything you type here."
    )

  # Special handling for the synthetic "__start__" message used by the frontend
  if patient_message == "__start__" and not conversation_history:
    # Let the model treat this as "start the intake" rather than literal text
    patient_message = (
      "Please begin the intake by greeting the patient by first name and asking "
      "what brings them in today."
    )

  system_prompt = build_system_prompt(context)

  messages = [{"role": "system", "content": system_prompt}]
  messages.extend(conversation_history)
  messages.append({"role": "user", "content": patient_message})

  try:
    response = client.chat.completions.create(
      model=GPT_MODEL,
      max_tokens=500,
      messages=messages,
    )
    return response.choices[0].message.content
  except Exception as e:
    print(f"OpenAI API error in get_ai_response: {e}")
    return (
      "I'm sorry, I'm having a technical issue. Please try again in a moment."
    )


# ─── Generate Intake Summary ────────────────────────────────────────────────────

def generate_intake_summary(transcript: str) -> dict:
  """
  After conversation ends, send full transcript to OpenAI.
  Returns structured JSON summary for doctor.
  """
  # If no API key, return a minimal, safe summary stub instead of erroring.
  if not _ensure_client():
    return {
      "summary": "AI summary is not available in this local demo, but your intake responses were recorded.",
      "chief_complaint": "",
      "symptoms": [],
      "current_medications": [],
      "allergies": [],
      "family_history": "",
      "medical_history": "",
      "lifestyle_factors": "",
      "risk_level": "low",
      "risk_flags": [],
    }

  prompt = f"""You are a medical data extractor. 
Read this patient intake conversation and extract the information as JSON.

CONVERSATION:
{transcript}

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "summary": "A clear 3-5 sentence summary for the doctor",
  "chief_complaint": "Main reason for visit in one phrase",
  "symptoms": [
    {{"name": "symptom name", "severity": "1-10 or description", "duration": "how long"}}
  ],
  "current_medications": [
    {{"name": "medication", "dosage": "dosage", "frequency": "frequency"}}
  ],
  "allergies": ["allergen 1", "allergen 2"],
  "family_history": "relevant family health history",
  "medical_history": "relevant past medical history",
  "lifestyle_factors": "sleep, stress, exercise info",
  "risk_level": "low|medium|high",
  "risk_flags": ["flag1", "flag2"]
}}

Risk level guide:
- high: chest pain, difficulty breathing, suicidal ideation, severe symptoms
- medium: moderate pain (6+/10), multiple concerning symptoms, chronic condition flare
- low: routine visit, mild symptoms, follow-up

If information wasn't mentioned, use empty string or empty array."""

  try:
    response = client.chat.completions.create(
      model=GPT_MODEL,
      max_tokens=1000,
      messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
  except Exception as e:
    print(f"Summary generation error: {e}")
    return {
      "summary": "Unable to generate summary automatically. Please review transcript.",
      "chief_complaint": "",
      "symptoms": [],
      "current_medications": [],
      "allergies": [],
      "family_history": "",
      "medical_history": "",
      "lifestyle_factors": "",
      "risk_level": "low",
      "risk_flags": [],
    }


# ─── Build Patient Context ─────────────────────────────────────────────────────

def build_patient_context(session, patient, db) -> dict:
  """
  Loads patient history from DB and formats it for the AI system prompt.
  This is how the AI "remembers" returning patients — it's just reading the DB.
  """
  from sqlalchemy import desc
  from models import IntakeSession, IntakeStatus

  past_sessions = (
    db.query(IntakeSession)
    .filter(
      IntakeSession.patient_id == patient.id,
      IntakeSession.id != session.id,
      IntakeSession.status == IntakeStatus.completed,
    )
    .order_by(desc(IntakeSession.completed_at))
    .limit(5)
    .all()
  )

  previous_visits = []
  active_medications = []
  known_allergies = []
  known_conditions = []

  for s in past_sessions:
    encounter = (
      s.appointment.encounter
      if s.appointment and s.appointment.encounter
      else None
    )
    visit = {
      "date": str(s.completed_at.date()) if s.completed_at else "unknown",
      "chief_complaint": s.chief_complaint or "Not recorded",
      "diagnosis": "",
      "medications": "",
    }

    if encounter and encounter.diagnosis:
      visit["diagnosis"] = ", ".join(
        [d.get("condition_name", "") for d in encounter.diagnosis]
      )

    if encounter and encounter.prescription:
      meds = encounter.prescription.medications or []
      visit["medications"] = ", ".join(
        [f"{m.get('drug_name')} {m.get('dosage', '')}" for m in meds]
      )

    previous_visits.append(visit)

    # Use medications from the most recent completed session as "active"
    if s == past_sessions[0] and s.current_medications:
      active_medications = s.current_medications

    # Collect allergies
    if s.allergies_reported:
      for a in s.allergies_reported:
        allergen = a if isinstance(a, str) else a.get("allergen", "")
        if allergen and allergen not in known_allergies:
          known_allergies.append(allergen)

  return {
    "patient_name": patient.full_name,
    "doctor_name": session.appointment.doctor.full_name,
    "doctor_specialization": session.appointment.doctor.specialization,
    "appointment_date": str(session.appointment.scheduled_date),
    "appointment_time": session.appointment.scheduled_time,
    "is_returning_patient": len(past_sessions) > 0,
    "previous_visits": previous_visits,
    "active_medications": active_medications,
    "known_allergies": known_allergies,
    "known_conditions": known_conditions,
  }

