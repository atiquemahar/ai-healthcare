from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, datetime
import httpx
import os

from database import get_db
from models import (
    Appointment, IntakeSession, Patient, Encounter,
    Prescription, AppointmentStatus, EncounterStatus,
    PrescriptionStatus, IntakeStatus
)
from schemas import EncounterComplete
from routers.auth import require_doctor
from utils.pdf import generate_prescription_pdf, save_pdf_locally
from utils.email import send_prescription_email

router = APIRouter()


# ─── Doctor Dashboard ─────────────────────────────────────────────────────────

@router.get("/dashboard")
def doctor_dashboard(
    target_date: str = None,
    current_doctor=Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Returns today's appointments with intake status for each."""

    query_date = date.fromisoformat(target_date) if target_date else date.today()

    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == current_doctor.id,
        Appointment.scheduled_date == query_date,
        Appointment.status != AppointmentStatus.cancelled,
    ).order_by(Appointment.scheduled_time).all()

    items = []
    for appt in appointments:
        intake = appt.intake_session
        items.append({
            "appointment_id" : appt.id,
            "patient_id"     : appt.patient_id,
            "patient_name"   : appt.patient.full_name,
            "scheduled_time" : appt.scheduled_time,
            "status"         : appt.status,
            "reason"         : appt.reason,
            "intake_status"  : intake.status if intake else "none",
            "risk_level"     : intake.ai_risk_level if intake else None,
            "intake_summary" : intake.ai_summary if intake else None,
        })

    completed = sum(1 for a in appointments if a.status == AppointmentStatus.completed)

    return {
        "date"        : str(query_date),
        "total_today" : len(appointments),
        "completed"   : completed,
        "pending"     : len(appointments) - completed,
        "appointments": items,
    }


# ─── Full Patient History ─────────────────────────────────────────────────────

@router.get("/patients/{patient_id}/history")
def patient_history(
    patient_id: int,
    current_doctor=Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Full patient history — only accessible to doctors who have seen this patient."""

    # Verify this doctor has an appointment with this patient (security check)
    has_relationship = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id  == current_doctor.id,
    ).first()

    if not has_relationship:
        raise HTTPException(status_code=403, detail="Patient not associated with this doctor")

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get all completed encounters, newest first
    encounters = db.query(Encounter).filter(
        Encounter.patient_id == patient_id,
        Encounter.status     == EncounterStatus.completed,
    ).order_by(desc(Encounter.completed_at)).all()

    history = []
    for enc in encounters:
        intake = enc.appointment.intake_session if enc.appointment else None
        presc  = enc.prescription

        history.append({
            "encounter_id"     : enc.id,
            "date"             : str(enc.completed_at.date()) if enc.completed_at else None,
            "appointment_date" : str(enc.appointment.scheduled_date) if enc.appointment else None,
            "intake_summary"   : intake.ai_summary if intake else None,
            "chief_complaint"  : intake.chief_complaint if intake else None,
            "diagnosis"        : enc.diagnosis,
            "examination_notes": enc.examination_notes,
            "treatment_plan"   : enc.treatment_plan,
            "prescription"     : {
                "id"          : presc.id,
                "medications" : presc.medications,
                "follow_up"   : str(presc.follow_up_date) if presc.follow_up_date else None,
                "pdf_url"     : presc.pdf_url,
            } if presc else None,
        })

    # Get most recent intake for active medication/allergy info
    latest_intake = db.query(IntakeSession).filter(
        IntakeSession.patient_id == patient_id,
        IntakeSession.status     == IntakeStatus.completed,
    ).order_by(desc(IntakeSession.completed_at)).first()

    return {
        "patient": {
            "id"            : patient.id,
            "full_name"     : patient.full_name,
            "email"         : patient.email,
            "phone"         : patient.phone,
            "date_of_birth" : str(patient.date_of_birth) if patient.date_of_birth else None,
            "gender"        : patient.gender,
        },
        "active_medications" : latest_intake.current_medications if latest_intake else [],
        "known_allergies"    : latest_intake.allergies_reported if latest_intake else [],
        "visit_count"        : len(history),
        "history"            : history,
    }


# ─── Start Encounter ──────────────────────────────────────────────────────────

@router.post("/encounters")
def start_encounter(
    appointment_id: int,
    current_doctor=Depends(require_doctor),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(
        Appointment.id        == appointment_id,
        Appointment.doctor_id == current_doctor.id,
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Check if encounter already exists
    existing = db.query(Encounter).filter(
        Encounter.appointment_id == appointment_id
    ).first()
    if existing:
        return {"encounter_id": existing.id, "message": "Encounter already started"}

    intake = appointment.intake_session
    encounter = Encounter(
        appointment_id    = appointment_id,
        patient_id        = appointment.patient_id,
        doctor_id         = current_doctor.id,
        intake_session_id = intake.id if intake else None,
    )
    db.add(encounter)
    appointment.status = AppointmentStatus.in_progress
    db.commit()
    db.refresh(encounter)

    return {"encounter_id": encounter.id, "message": "Encounter started"}


# ─── Complete Encounter + Generate Prescription ───────────────────────────────

@router.post("/encounters/{encounter_id}/complete")
async def complete_encounter(
    encounter_id: int,
    data: EncounterComplete,
    current_doctor=Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """
    Doctor finalizes the encounter.
    Creates prescription, generates PDF, emails patient.
    """
    encounter = db.query(Encounter).filter(
        Encounter.id        == encounter_id,
        Encounter.doctor_id == current_doctor.id,
    ).first()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    # Update encounter
    encounter.examination_notes = data.examination_notes
    encounter.diagnosis         = data.diagnosis
    encounter.treatment_plan    = data.treatment_plan
    encounter.status            = EncounterStatus.completed
    encounter.completed_at      = datetime.utcnow()

    # Create prescription
    prescription = Prescription(
        encounter_id            = encounter.id,
        patient_id              = encounter.patient_id,
        doctor_id               = current_doctor.id,
        medications             = data.prescription.medications,
        additional_instructions = data.prescription.additional_instructions,
        follow_up_date          = data.prescription.follow_up_date,
        follow_up_notes         = data.prescription.follow_up_notes,
        status                  = PrescriptionStatus.finalized,
    )
    db.add(prescription)
    db.flush()  # get prescription.id before PDF generation

    # Generate PDF
    try:
        pdf_bytes = generate_prescription_pdf(
            prescription = prescription,
            encounter    = encounter,
            patient      = encounter.patient,
            doctor       = current_doctor,
        )
        pdf_path = save_pdf_locally(pdf_bytes, prescription.id)
        prescription.pdf_url          = pdf_path
        prescription.pdf_generated_at = datetime.utcnow()
    except Exception as e:
        print(f"PDF generation failed: {e}")
        pdf_path = None

    # Update appointment status
    encounter.appointment.status = AppointmentStatus.completed

    db.commit()

    # Send prescription email (non-blocking — failure doesn't crash the request)
    try:
        diagnosis_text = ", ".join([d.get("condition_name", "") for d in (data.diagnosis or [])])
        send_prescription_email(
            patient_email   = encounter.patient.email,
            patient_name    = encounter.patient.full_name,
            doctor_name     = current_doctor.full_name,
            prescription_id = prescription.id,
            diagnosis       = diagnosis_text,
            medications     = data.prescription.medications,
            follow_up_date  = str(data.prescription.follow_up_date) if data.prescription.follow_up_date else None,
            pdf_path        = pdf_path,
        )
        prescription.status  = PrescriptionStatus.sent
        prescription.sent_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        print(f"Email failed: {e}")

    # Fire N8N webhook for follow-up reminder scheduling (non-blocking)
    n8n_prescription_url = os.getenv("N8N_WEBHOOK_PRESCRIPTION", "")
    if n8n_prescription_url and data.prescription.follow_up_date:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(n8n_prescription_url, json={
                    "prescription_id"  : prescription.id,
                    "patient_name"     : encounter.patient.full_name,
                    "patient_email"    : encounter.patient.email,
                    "doctor_name"      : current_doctor.full_name,
                    "diagnosis"        : diagnosis_text,
                    "medications"      : data.prescription.medications,
                    "follow_up_date"   : str(data.prescription.follow_up_date),
                    "pdf_download_url" : f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/prescriptions/{prescription.id}/pdf",
                })
        except Exception as e:
            print(f"N8N prescription webhook failed: {e}")

    return {
        "message"        : "Encounter completed and prescription sent",
        "encounter_id"   : encounter.id,
        "prescription_id": prescription.id,
        "pdf_available"  : pdf_path is not None,
    }
