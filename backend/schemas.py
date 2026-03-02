from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import date, datetime
from models import AppointmentStatus, IntakeStatus, RiskLevel, EncounterStatus, PrescriptionStatus


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class PatientRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str  # "patient" or "doctor"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


# ─── Doctor Schemas ───────────────────────────────────────────────────────────

class DoctorBasic(BaseModel):
    id: int
    full_name: str
    specialization: Optional[str]
    email: str

    class Config:
        from_attributes = True


# ─── Appointment Schemas ──────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    doctor_id: int
    scheduled_date: date
    scheduled_time: str   # "10:00"
    reason: Optional[str] = None
    appointment_type: str = "new_visit"

class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    scheduled_date: date
    scheduled_time: str
    status: AppointmentStatus
    reason: Optional[str]
    appointment_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class AppointmentWithDoctor(AppointmentResponse):
    doctor: DoctorBasic


# ─── Intake Schemas ───────────────────────────────────────────────────────────

class IntakeSessionCreate(BaseModel):
    appointment_id: int

class IntakeSessionResponse(BaseModel):
    id: int
    appointment_id: int
    status: IntakeStatus
    ai_risk_level: Optional[RiskLevel]
    ai_summary: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ChatMessageRequest(BaseModel):
    content: str  # what patient typed

class ChatMessageResponse(BaseModel):
    patient_message: str
    ai_response: str
    session_id: int
    message_number: int

class PatientHistoryContext(BaseModel):
    """Loaded before AI conversation starts"""
    patient_name: str
    doctor_name: str
    doctor_specialization: Optional[str]
    appointment_date: str
    appointment_time: str
    is_returning_patient: bool
    previous_visits: List[dict]      # past encounters summary
    active_medications: List[dict]   # from last intake
    known_allergies: List[str]
    known_conditions: List[str]


# ─── Encounter Schemas ────────────────────────────────────────────────────────

class EncounterCreate(BaseModel):
    appointment_id: int

class EncounterUpdate(BaseModel):
    examination_notes: Optional[str] = None
    diagnosis: Optional[List[dict]] = None   # [{condition_name, icd10_code}]
    treatment_plan: Optional[str] = None

class PrescriptionData(BaseModel):
    medications: List[dict]  # [{drug_name, dosage, frequency, duration, instructions}]
    additional_instructions: Optional[str] = None
    follow_up_date: Optional[date] = None
    follow_up_notes: Optional[str] = None

class EncounterComplete(BaseModel):
    examination_notes: str
    diagnosis: List[dict]
    treatment_plan: Optional[str] = None
    prescription: PrescriptionData

class EncounterResponse(BaseModel):
    id: int
    appointment_id: int
    status: EncounterStatus
    examination_notes: Optional[str]
    diagnosis: Optional[List[dict]]
    treatment_plan: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Doctor Dashboard Schemas ─────────────────────────────────────────────────

class AppointmentDashboardItem(BaseModel):
    appointment_id: int
    patient_id: int
    patient_name: str
    scheduled_time: str
    status: AppointmentStatus
    intake_status: Optional[str]   # "done" / "pending" / "none"
    risk_level: Optional[RiskLevel]

class DoctorDashboardResponse(BaseModel):
    date: str
    total_today: int
    completed: int
    pending: int
    appointments: List[AppointmentDashboardItem]


# ─── Patient Dashboard Schemas ────────────────────────────────────────────────

class PatientDashboardResponse(BaseModel):
    patient_name: str
    upcoming_appointments: List[AppointmentWithDoctor]
    past_visits_count: int
    pending_intake: Optional[AppointmentWithDoctor]  # if they haven't done intake yet


# ─── Prescription Schemas ─────────────────────────────────────────────────────

class PrescriptionResponse(BaseModel):
    id: int
    encounter_id: int
    medications: Optional[List[dict]]
    additional_instructions: Optional[str]
    follow_up_date: Optional[date]
    pdf_url: Optional[str]
    status: PrescriptionStatus
    created_at: datetime

    class Config:
        from_attributes = True
