"""
Internal API endpoints — called by N8N, not by the frontend.
Protected by a static secret key (simpler than JWT for machine-to-machine).
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import date, timedelta
import os

from database import get_db
from models import Appointment, IntakeSession, AppointmentStatus, IntakeStatus

router = APIRouter()

INTERNAL_SECRET = os.getenv("N8N_INTERNAL_SECRET", "")


def verify_internal_secret(x_internal_secret: str = Header(...)):
    """N8N passes this header. Rejects anything without the right key."""
    if not INTERNAL_SECRET or x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/reminders/intake-due")
def get_intake_due_reminders(
    db: Session = Depends(get_db),
    _=Depends(verify_internal_secret),
):
    """
    Called by N8N daily cron at 8AM.
    Returns all appointments TOMORROW where intake is not yet completed.
    N8N then emails each patient.
    """
    tomorrow = date.today() + timedelta(days=1)

    appointments = db.query(Appointment).filter(
        Appointment.scheduled_date == tomorrow,
        Appointment.status == AppointmentStatus.scheduled,
    ).all()

    results = []
    for appt in appointments:
        intake = appt.intake_session
        intake_done = intake and intake.status == IntakeStatus.completed

        if not intake_done:
            results.append({
                "appointment_id"  : appt.id,
                "patient_name"    : appt.patient.full_name,
                "patient_email"   : appt.patient.email,
                "doctor_name"     : appt.doctor.full_name,
                "scheduled_date"  : str(appt.scheduled_date),
                "scheduled_time"  : appt.scheduled_time,
                "intake_url"      : f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/book",
            })

    return {"count": len(results), "reminders": results}
