import json
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
        return _client
    except ImportError:
        print("openai package not installed. Run: pip install openai")
        return None

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def build_system_prompt(context: dict) -> str:
    patient_name     = context.get("patient_name", "Patient")
    doctor_name      = context.get("doctor_name", "the doctor")
    specialization   = context.get("doctor_specialization", "")
    appt_date        = context.get("appointment_date", "")
    appt_time        = context.get("appointment_time", "")
    is_returning     = context.get("is_returning_patient", False)
    previous_visits  = context.get("previous_visits", [])
    active_meds      = context.get("active_medications", [])
    known_allergies  = context.get("known_allergies", [])
    known_conditions = context.get("known_conditions", [])

    history_section = ""
    if is_returning and previous_visits:
        history_section = "\n-- PATIENT HISTORY (returning patient) --\n"
        for visit in previous_visits[:5]:
            history_section += f"- {visit.get('date')}: {visit.get('diagnosis')} -> Prescribed: {visit.get('medications')}\n"
        if active_meds:
            history_section += "\nActive medications:\n"
            for med in active_meds:
                history_section += f"- {med.get('name')} {med.get('dosage')} -- {med.get('frequency')}\n"
        if known_allergies:
            history_section += f"\nKnown allergies: {', '.join(known_allergies)}\n"
        if known_conditions:
            history_section += f"\nKnown conditions: {', '.join(known_conditions)}\n"

    returning_instructions = ""
    if is_returning and previous_visits:
        last = previous_visits[0]
        returning_instructions = f"\n-- RETURNING PATIENT -- ALSO ASK --\n- Are you still taking {last.get('medications', 'your medication')}?\n- Has your condition improved since {last.get('date', 'last time')}?\n- Any new symptoms since your last visit?\n"

    first_name = patient_name.split()[0] if patient_name else "there"

    return f"""You are a friendly medical intake assistant helping collect information before the patient's appointment with {doctor_name}{f' ({specialization})' if specialization else ''}.

YOUR ONLY JOB: Ask questions and collect information. YOU ARE NOT A DOCTOR. Never diagnose or suggest medicines.

APPOINTMENT: {patient_name} with {doctor_name} on {appt_date} at {appt_time}
{history_section}

RULES:
1. Greet patient by first name, ask ONE question at a time
2. Use simple everyday language, be warm and empathetic
3. Keep responses to 2-3 sentences max
{returning_instructions}
QUESTIONS TO ASK IN ORDER:
1. What brings you in today?
2. How long have you had this problem?
3. On a scale of 1-10, how bad is it?
4. Is it constant or does it come and go?
5. Any other symptoms?
6. Are you taking any medicines?
7. Any allergies?
8. Family history of similar issues?
9. How is your sleep and stress?
10. Anything else for {doctor_name}?

SAFETY: If chest pain + breathing difficulty -> tell them to call emergency services immediately.
After all questions: summarize and say "Thank you {first_name}! {doctor_name} will have all this ready for your visit. Take care!"
"""


def get_ai_response(patient_message: str, conversation_history: list, context: dict) -> str:
    client = _get_client()

    if not client:
        if patient_message == "__start__":
            first_name = context.get("patient_name", "there").split()[0]
            return f"Hi {first_name}! I'm your pre-visit assistant. I'll ask a few quick questions so your doctor is prepared. What brings you in today?"
        return "Thanks for sharing that. Your doctor will review everything you've typed. Is there anything else you'd like to add?"

    if patient_message == "__start__" and not conversation_history:
        patient_message = "Please begin the intake by greeting the patient by first name and asking what brings them in today."

    messages = [{"role": "system", "content": build_system_prompt(context)}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": patient_message})

    try:
        response = client.chat.completions.create(model=MODEL, max_tokens=500, messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "I'm sorry, I'm having a technical issue. Please try again in a moment."


def generate_intake_summary(transcript: str) -> dict:
    client = _get_client()

    if not client:
        return {"summary": "AI summary unavailable.", "chief_complaint": "", "symptoms": [], "current_medications": [], "allergies": [], "family_history": "", "medical_history": "", "lifestyle_factors": "", "risk_level": "low", "risk_flags": []}

    prompt = f"""Extract patient intake info as JSON from this conversation:

{transcript}

Return ONLY valid JSON (no markdown):
{{"summary": "3-5 sentence summary for doctor", "chief_complaint": "main reason", "symptoms": [{{"name": "", "severity": "", "duration": ""}}], "current_medications": [{{"name": "", "dosage": "", "frequency": ""}}], "allergies": [], "family_history": "", "medical_history": "", "lifestyle_factors": "", "risk_level": "low|medium|high", "risk_flags": []}}

Risk: high=chest pain/breathing/self-harm, medium=pain 6+/10 or chronic flare, low=routine"""

    try:
        response = client.chat.completions.create(model=MODEL, max_tokens=1000, messages=[{"role": "user", "content": prompt}])
        raw = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"Summary error: {e}")
        return {"summary": "Unable to generate summary.", "chief_complaint": "", "symptoms": [], "current_medications": [], "allergies": [], "family_history": "", "medical_history": "", "lifestyle_factors": "", "risk_level": "low", "risk_flags": []}


def build_patient_context(session, patient, db) -> dict:
    from sqlalchemy import desc
    from models import IntakeSession, IntakeStatus

    past_sessions = db.query(IntakeSession).filter(
        IntakeSession.patient_id == patient.id,
        IntakeSession.id != session.id,
        IntakeSession.status == IntakeStatus.completed,
    ).order_by(desc(IntakeSession.completed_at)).limit(5).all()

    previous_visits = []
    active_medications = []
    known_allergies = []

    for s in past_sessions:
        encounter = s.appointment.encounter if s.appointment and s.appointment.encounter else None
        visit = {"date": str(s.completed_at.date()) if s.completed_at else "unknown", "chief_complaint": s.chief_complaint or "", "diagnosis": "", "medications": ""}
        if encounter and encounter.diagnosis:
            visit["diagnosis"] = ", ".join([d.get("condition_name", "") for d in encounter.diagnosis])
        if encounter and encounter.prescription:
            meds = encounter.prescription.medications or []
            visit["medications"] = ", ".join([f"{m.get('drug_name')} {m.get('dosage', '')}" for m in meds])
        previous_visits.append(visit)

        if s == past_sessions[0] and s.current_medications:
            active_medications = s.current_medications
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
        "known_conditions": [],
    }

