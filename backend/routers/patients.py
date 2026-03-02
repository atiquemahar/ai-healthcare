from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date

from database import get_db
from models import Appointment, Prescription, IntakeSession, AppointmentStatus, IntakeStatus
from routers.auth import require_patient

router = APIRouter()


@router.get("/me/dashboard")
def patient_dashboard(
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    """Patient home — upcoming appointments, past visits, pending intake."""
    today = date.today()

    # Upcoming appointments
    upcoming = db.query(Appointment).filter(
        Appointment.patient_id    == current_patient.id,
        Appointment.scheduled_date >= today,
        Appointment.status.in_([AppointmentStatus.scheduled, AppointmentStatus.intake_done]),
    ).order_by(Appointment.scheduled_date, Appointment.scheduled_time).all()

    # Past visits
    past = db.query(Appointment).filter(
        Appointment.patient_id == current_patient.id,
        Appointment.status     == AppointmentStatus.completed,
    ).order_by(desc(Appointment.scheduled_date)).limit(10).all()

    # Check if any upcoming appointment needs intake
    pending_intake = None
    for appt in upcoming:
        if not appt.intake_session or appt.intake_session.status != IntakeStatus.completed:
            pending_intake = {
                "appointment_id": appt.id,
                "doctor_name"   : appt.doctor.full_name,
                "scheduled_date": str(appt.scheduled_date),
                "scheduled_time": appt.scheduled_time,
            }
            break

    return {
        "patient_name"   : current_patient.full_name,
        "pending_intake" : pending_intake,
        "upcoming"       : [
            {
                "appointment_id": a.id,
                "doctor_name"   : a.doctor.full_name,
                "specialization": a.doctor.specialization,
                "scheduled_date": str(a.scheduled_date),
                "scheduled_time": a.scheduled_time,
                "status"        : a.status,
                "intake_done"   : bool(a.intake_session and a.intake_session.status == IntakeStatus.completed),
            }
            for a in upcoming
        ],
        "past_visits": [
            {
                "appointment_id": a.id,
                "doctor_name"   : a.doctor.full_name,
                "scheduled_date": str(a.scheduled_date),
                "diagnosis"     : a.encounter.diagnosis if a.encounter else None,
                "has_prescription": bool(a.encounter and a.encounter.prescription),
                "prescription_id": a.encounter.prescription.id if a.encounter and a.encounter.prescription else None,
            }
            for a in past
        ],
    }


@router.get("/me/appointments")
def my_appointments(
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    appointments = db.query(Appointment).filter(
        Appointment.patient_id == current_patient.id,
    ).order_by(desc(Appointment.scheduled_date)).all()

    return [
        {
            "appointment_id": a.id,
            "doctor_name"   : a.doctor.full_name,
            "scheduled_date": str(a.scheduled_date),
            "scheduled_time": a.scheduled_time,
            "status"        : a.status,
            "reason"        : a.reason,
        }
        for a in appointments
    ]


@router.get("/me/prescriptions")
def my_prescriptions(
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == current_patient.id,
    ).order_by(desc(Prescription.created_at)).all()

    return [
        {
            "prescription_id"  : p.id,
            "doctor_name"      : p.doctor.full_name,
            "date"             : str(p.created_at.date()),
            "medications"      : p.medications,
            "follow_up_date"   : str(p.follow_up_date) if p.follow_up_date else None,
            "pdf_url"          : p.pdf_url,
            "status"           : p.status,
        }
        for p in prescriptions
    ]


@router.get("/me/prescriptions/{prescription_id}")
def get_prescription(
    prescription_id: int,
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    prescription = db.query(Prescription).filter(
        Prescription.id         == prescription_id,
        Prescription.patient_id == current_patient.id,  # security check
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return {
        "prescription_id"       : prescription.id,
        "doctor_name"           : prescription.doctor.full_name,
        "date"                  : str(prescription.created_at.date()),
        "medications"           : prescription.medications,
        "additional_instructions": prescription.additional_instructions,
        "follow_up_date"        : str(prescription.follow_up_date) if prescription.follow_up_date else None,
        "pdf_url"               : prescription.pdf_url,
    }
