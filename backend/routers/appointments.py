from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import os

from database import get_db
from models import Appointment, Doctor, AppointmentStatus
from schemas import AppointmentCreate, AppointmentResponse
from routers.auth import require_patient

router = APIRouter()

N8N_WEBHOOK_BOOKING = os.getenv("N8N_WEBHOOK_BOOKING", "")


# ─── List all doctors (patient uses this to pick who to book) ─────────────────

@router.get("/doctors")
def list_doctors(db: Session = Depends(get_db)):
    """Return all active doctors. Patient uses this on booking form."""
    doctors = db.query(Doctor).filter(Doctor.is_active == True).all()
    return [
        {
            "id": d.id,
            "full_name": d.full_name,
            "specialization": d.specialization,
            "email": d.email,
        }
        for d in doctors
    ]


# ─── Book appointment ─────────────────────────────────────────────────────────

@router.post("/appointments", response_model=AppointmentResponse)
async def book_appointment(
    data: AppointmentCreate,
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Step 1: Save appointment to DB immediately (so polling works).
    Step 2: Fire N8N webhook in background (doctor notification, reminder scheduling).
    Returns the appointment_id which frontend uses to open the chat.
    """
    # Verify doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Create appointment
    appointment = Appointment(
        patient_id       = current_patient.id,
        doctor_id        = data.doctor_id,
        scheduled_date   = data.scheduled_date,
        scheduled_time   = data.scheduled_time,
        reason           = data.reason,
        appointment_type = data.appointment_type,
        status           = AppointmentStatus.scheduled,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Fire N8N webhook (non-blocking — we don't wait for it)
    if N8N_WEBHOOK_BOOKING:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(N8N_WEBHOOK_BOOKING, json={
                    "appointment_id"  : appointment.id,
                    "patient_name"    : current_patient.full_name,
                    "patient_email"   : current_patient.email,
                    "doctor_name"     : doctor.full_name,
                    "doctor_email"    : doctor.email,
                    "scheduled_date"  : str(data.scheduled_date),
                    "scheduled_time"  : data.scheduled_time,
                    "reason"          : data.reason,
                })
        except Exception:
            # N8N failure should NOT block the patient — just log and continue
            pass

    return appointment


# ─── Check if appointment is ready (frontend polls this) ─────────────────────

@router.get("/appointments/{appointment_id}/status")
def check_appointment_status(
    appointment_id: int,
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Frontend polls this every second after booking form submission.
    Returns {ready: true, appointment_id: X} when confirmed.
    This is needed for Option B (polling) UX.
    """
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.patient_id == current_patient.id,
    ).first()

    if not appointment:
        return {"ready": False}

    return {
        "ready": True,
        "appointment_id": appointment.id,
        "doctor_name": appointment.doctor.full_name,
        "scheduled_date": str(appointment.scheduled_date),
        "scheduled_time": appointment.scheduled_time,
    }


# ─── Cancel appointment ───────────────────────────────────────────────────────

@router.put("/appointments/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: int,
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.patient_id == current_patient.id,
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status == AppointmentStatus.completed:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed appointment")

    appointment.status = AppointmentStatus.cancelled
    db.commit()
    return {"message": "Appointment cancelled"}
