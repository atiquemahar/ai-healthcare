from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, time, timedelta, date as date_type
import httpx
import os

from database import get_db
from models import Appointment, Doctor, AppointmentStatus, DoctorAvailability
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


# ─── Helper: compute available 30-minute slots ────────────────────────────────

def _generate_slots_for_availability(avail, target_date: date_type, existing_appointments):
    """
    Given a DoctorAvailability row, a date, and existing appointments,
    return all free 30-minute slot strings ("HH:MM") within that window.
    """
    # Build naive datetimes for start/end on the target date
    start_dt = datetime.combine(target_date, avail.start_time)
    end_dt = datetime.combine(target_date, avail.end_time)

    slot_length = timedelta(minutes=30)
    slots = []

    # Pre-build a set of taken times ("HH:MM") for quick lookup
    taken_times = {
        appt.scheduled_time
        for appt in existing_appointments
    }

    current = start_dt
    # Only create slots where the full 30 minutes fit before end_dt
    while current + slot_length <= end_dt:
        slot_str = current.strftime("%H:%M")
        if slot_str not in taken_times:
            slots.append(slot_str)
        current += slot_length

    return slots


@router.get("/doctors/{doctor_id}/available-slots")
def get_available_slots(
    doctor_id: int,
    date: str = Query(..., description="Date in YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Returns available 30-minute time slots for a doctor on a given date,
    based on their weekly availability and existing non-cancelled appointments.
    """
    # Verify doctor exists and is active
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active == True).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    day_of_week = target_date.weekday()  # Monday=0

    # Get availability blocks for this weekday
    availability_blocks = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.day_of_week == day_of_week,
    ).all()

    if not availability_blocks:
        return {"date": date, "doctor_id": doctor_id, "slots": []}

    # Get existing appointments for that date (non-cancelled)
    existing_appts = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.scheduled_date == target_date,
        Appointment.status != AppointmentStatus.cancelled,
    ).all()

    all_slots = []
    for avail in availability_blocks:
        all_slots.extend(_generate_slots_for_availability(avail, target_date, existing_appts))

    # Sort slots just in case
    all_slots = sorted(set(all_slots))

    return {
        "date": date,
        "doctor_id": doctor_id,
        "slots": all_slots,
    }


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
    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id, Doctor.is_active == True).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Enforce availability window (doctor must have availability for this day/time)
    if not data.scheduled_date:
        raise HTTPException(status_code=400, detail="scheduled_date is required")
    if not data.scheduled_time:
        raise HTTPException(status_code=400, detail="scheduled_time is required")

    # Parse date and time
    try:
        target_date = data.scheduled_date
        appt_time = datetime.strptime(data.scheduled_time, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="scheduled_time must be in HH:MM format")

    day_of_week = target_date.weekday()

    availability_blocks = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == data.doctor_id,
        DoctorAvailability.day_of_week == day_of_week,
    ).all()

    if not availability_blocks:
        raise HTTPException(
            status_code=400,
            detail="Doctor is not available on this day.",
        )

    # Ensure requested time falls within at least one availability block
    in_window = any(avail.start_time <= appt_time < avail.end_time for avail in availability_blocks)
    if not in_window:
        raise HTTPException(
            status_code=400,
            detail="Selected time is outside the doctor's working hours.",
        )

    # Check if this time slot is already booked
    slot_taken = db.query(Appointment).filter(
        Appointment.doctor_id      == data.doctor_id,
        Appointment.scheduled_date == data.scheduled_date,
        Appointment.scheduled_time == data.scheduled_time,
        Appointment.status         != AppointmentStatus.cancelled,
    ).first()

    if slot_taken:
        raise HTTPException(
            status_code=400, 
            detail="This time slot is already booked. Please choose another time."
        )

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
