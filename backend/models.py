from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    ForeignKey, Text, JSON, Enum, Date, Time
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


# ─── Enums ───────────────────────────────────────────────────────────────────

class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    intake_done = "intake_done"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class IntakeStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"

class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class EncounterStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"

class PrescriptionStatus(str, enum.Enum):
    draft = "draft"
    finalized = "finalized"
    sent = "sent"

class MessageRole(str, enum.Enum):
    patient = "patient"
    ai_assistant = "ai_assistant"


# ─── Table 1: Patients ───────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id            = Column(Integer, primary_key=True, index=True)
    first_name    = Column(String(100), nullable=False)
    last_name     = Column(String(100), nullable=False)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone         = Column(String(20))
    date_of_birth = Column(Date)
    gender        = Column(String(20))
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    appointments    = relationship("Appointment", back_populates="patient")
    intake_sessions = relationship("IntakeSession", back_populates="patient")
    encounters      = relationship("Encounter", back_populates="patient")
    prescriptions   = relationship("Prescription", back_populates="patient")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# ─── Table 2: Doctors ────────────────────────────────────────────────────────

class Doctor(Base):
    __tablename__ = "doctors"

    id              = Column(Integer, primary_key=True, index=True)
    first_name      = Column(String(100), nullable=False)
    last_name       = Column(String(100), nullable=False)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    password_hash   = Column(String(255), nullable=False)
    specialization  = Column(String(100))
    license_number  = Column(String(100))
    phone           = Column(String(20))
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    appointments  = relationship("Appointment", back_populates="doctor")
    encounters    = relationship("Encounter", back_populates="doctor")
    prescriptions = relationship("Prescription", back_populates="doctor")

    @property
    def full_name(self):
        return f"Dr. {self.first_name} {self.last_name}"


# ─── Table 3: Doctor Availability ─────────────────────────────────────────────

class DoctorAvailability(Base):
    """
    Weekly recurring availability blocks for each doctor.
    day_of_week: 0 = Monday ... 6 = Sunday
    start_time / end_time: working hours for that day.
    """
    __tablename__ = "doctor_availability"

    id          = Column(Integer, primary_key=True, index=True)
    doctor_id   = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Mon-Sun)
    start_time  = Column(Time, nullable=False)
    end_time    = Column(Time, nullable=False)


# ─── Table 4: Appointments ───────────────────────────────────────────────────

class Appointment(Base):
    __tablename__ = "appointments"

    id               = Column(Integer, primary_key=True, index=True)
    patient_id       = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id        = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    scheduled_date   = Column(Date, nullable=False)
    scheduled_time   = Column(String(10), nullable=False)  # "10:00"
    duration_minutes = Column(Integer, default=30)
    status           = Column(Enum(AppointmentStatus), default=AppointmentStatus.scheduled)
    appointment_type = Column(String(20), default="new_visit")  # new_visit / follow_up
    reason           = Column(Text)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient         = relationship("Patient", back_populates="appointments")
    doctor          = relationship("Doctor", back_populates="appointments")
    intake_session  = relationship("IntakeSession", back_populates="appointment", uselist=False)
    encounter       = relationship("Encounter", back_populates="appointment", uselist=False)


# ─── Table 5: Intake Sessions ────────────────────────────────────────────────

class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id             = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, unique=True)
    patient_id     = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id      = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    status         = Column(Enum(IntakeStatus), default=IntakeStatus.in_progress)

    # AI extracted data (filled during conversation)
    chief_complaint      = Column(Text)
    symptoms             = Column(JSON)           # [{name, severity, duration}]
    current_medications  = Column(JSON)           # [{name, dosage, frequency}]
    allergies_reported   = Column(JSON)           # [{allergen, reaction}]
    family_history       = Column(Text)
    medical_history      = Column(Text)
    lifestyle_factors    = Column(Text)

    # AI generated after conversation ends
    ai_summary    = Column(Text)
    ai_risk_level = Column(Enum(RiskLevel), default=RiskLevel.low)
    ai_risk_flags = Column(JSON)  # ["chest_pain", "family_cardiac_history"]

    total_messages = Column(Integer, default=0)
    started_at     = Column(DateTime(timezone=True), server_default=func.now())
    completed_at   = Column(DateTime(timezone=True))

    # Relationships
    appointment = relationship("Appointment", back_populates="intake_session")
    patient     = relationship("Patient", back_populates="intake_sessions")
    messages    = relationship("ConversationMessage", back_populates="session",
                               order_by="ConversationMessage.message_number")


# ─── Table 6: Conversation Messages ──────────────────────────────────────────

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id             = Column(Integer, primary_key=True, index=True)
    session_id     = Column(Integer, ForeignKey("intake_sessions.id"), nullable=False)
    role           = Column(Enum(MessageRole), nullable=False)
    content        = Column(Text, nullable=False)
    message_number = Column(Integer, nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("IntakeSession", back_populates="messages")


# ─── Table 7: Encounters ─────────────────────────────────────────────────────

class Encounter(Base):
    __tablename__ = "encounters"

    id                = Column(Integer, primary_key=True, index=True)
    appointment_id    = Column(Integer, ForeignKey("appointments.id"), nullable=False, unique=True)
    patient_id        = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id         = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    intake_session_id = Column(Integer, ForeignKey("intake_sessions.id"), nullable=True)

    # Doctor inputs
    examination_notes = Column(Text)
    diagnosis         = Column(JSON)    # [{condition_name, icd10_code}]
    treatment_plan    = Column(Text)

    status       = Column(Enum(EncounterStatus), default=EncounterStatus.in_progress)
    started_at   = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    appointment  = relationship("Appointment", back_populates="encounter")
    patient      = relationship("Patient", back_populates="encounters")
    doctor       = relationship("Doctor", back_populates="encounters")
    prescription = relationship("Prescription", back_populates="encounter", uselist=False)


# ─── Table 8: Prescriptions ──────────────────────────────────────────────────

class Prescription(Base):
    __tablename__ = "prescriptions"

    id          = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False, unique=True)
    patient_id  = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id   = Column(Integer, ForeignKey("doctors.id"), nullable=False)

    # Prescription content
    medications             = Column(JSON)  # [{drug_name, dosage, frequency, duration, instructions}]
    additional_instructions = Column(Text)
    follow_up_date          = Column(Date)
    follow_up_notes         = Column(Text)

    # PDF
    pdf_url          = Column(String(500))
    pdf_generated_at = Column(DateTime(timezone=True))

    # Status
    status     = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.draft)
    sent_at    = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    encounter = relationship("Encounter", back_populates="prescription")
    patient   = relationship("Patient", back_populates="prescriptions")
    doctor    = relationship("Doctor", back_populates="prescriptions")
