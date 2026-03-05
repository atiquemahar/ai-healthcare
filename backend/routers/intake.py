from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
import os

from database import get_db
from models import (
    Appointment, IntakeSession, ConversationMessage,
    AppointmentStatus, IntakeStatus, MessageRole
)
from schemas import (
    IntakeSessionCreate, IntakeSessionResponse,
    ChatMessageRequest, ChatMessageResponse, PatientHistoryContext
)
from routers.auth import require_patient
from utils.ai import get_ai_response, generate_intake_summary, build_patient_context

router = APIRouter()


# ─── Start intake session ─────────────────────────────────────────────────────

@router.post("/sessions", response_model=IntakeSessionResponse)
def start_intake_session(
    data: IntakeSessionCreate,
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Called when patient clicks 'Start Chat' after booking confirmed.
    Creates the intake session and returns session_id.
    Handles concurrent requests gracefully by returning existing session.
    """
    # Verify appointment belongs to this patient
    appointment = db.query(Appointment).filter(
        Appointment.id == data.appointment_id,
        Appointment.patient_id == current_patient.id,
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Check if session already exists (patient refreshed page or concurrent request)
    existing = db.query(IntakeSession).filter(
        IntakeSession.appointment_id == data.appointment_id
    ).first()

    if existing:
        return existing  # Resume existing session (handles race condition)

    # Create new session
    try:
        session = IntakeSession(
            appointment_id = data.appointment_id,
            patient_id     = current_patient.id,
            doctor_id      = appointment.doctor_id,
            status         = IntakeStatus.in_progress,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    except Exception as e:
        # Handle race condition: another request created the session concurrently
        db.rollback()
        
        # Try to fetch the existing session
        existing = db.query(IntakeSession).filter(
            IntakeSession.appointment_id == data.appointment_id
        ).first()
        
        if existing:
            return existing
        
        # If still not found, it's a different error
        print(f"Intake session creation error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to create intake session. Please try again in a moment."
        )


# ─── Get patient history context (loaded before chat starts) ──────────────────

@router.get("/sessions/{session_id}/context")
def get_session_context(
    session_id: int,
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Loads patient history for the AI system prompt.
    Called once when chat interface initializes.
    """
    session = db.query(IntakeSession).filter(
        IntakeSession.id == session_id,
        IntakeSession.patient_id == current_patient.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    context = build_patient_context(session, current_patient, db)
    return context


# ─── Send a message and get AI reply ─────────────────────────────────────────

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def send_message(
    session_id: int,
    data: ChatMessageRequest,
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Core chat endpoint.
    Patient sends a message → Claude responds → both saved to DB.
    """
    session = db.query(IntakeSession).filter(
        IntakeSession.id == session_id,
        IntakeSession.patient_id == current_patient.id,
        IntakeSession.status == IntakeStatus.in_progress,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    # Cap at 40 messages to control AI costs
    if session.total_messages >= 40:
        raise HTTPException(
            status_code=400,
            detail="Message limit reached. Please complete the intake."
        )

    # Get all previous messages for context
    previous_messages = db.query(ConversationMessage).filter(
        ConversationMessage.session_id == session_id
    ).order_by(ConversationMessage.message_number).all()

    # Build conversation history for Claude
    history = [
        {"role": "user" if m.role == MessageRole.patient else "assistant", "content": m.content}
        for m in previous_messages
    ]

    # Load patient context (for system prompt)
    context = build_patient_context(session, current_patient, db)

    # Get AI response from Claude
    ai_reply = get_ai_response(
        patient_message=data.content,
        conversation_history=history,
        context=context,
    )

    # Save patient message
    msg_number = session.total_messages + 1
    patient_msg = ConversationMessage(
        session_id     = session_id,
        role           = MessageRole.patient,
        content        = data.content,
        message_number = msg_number,
    )
    db.add(patient_msg)

    # Save AI message
    ai_msg = ConversationMessage(
        session_id     = session_id,
        role           = MessageRole.ai_assistant,
        content        = ai_reply,
        message_number = msg_number + 1,
    )
    db.add(ai_msg)

    # Update message count
    session.total_messages = msg_number + 1
    db.commit()

    return ChatMessageResponse(
        patient_message=data.content,
        ai_response=ai_reply,
        session_id=session_id,
        message_number=msg_number,
    )


# ─── Complete intake and generate summary ─────────────────────────────────────

@router.post("/sessions/{session_id}/complete")
def complete_intake(
    session_id: int,
    current_patient=Depends(require_patient),
    db: Session = Depends(get_db),
):
    """
    Called when patient clicks 'Done' in chat.
    Generates structured AI summary and marks session complete.
    """
    session = db.query(IntakeSession).filter(
        IntakeSession.id == session_id,
        IntakeSession.patient_id == current_patient.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == IntakeStatus.completed:
        return {"message": "Already completed", "session_id": session_id}

    # Get full transcript
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.session_id == session_id
    ).order_by(ConversationMessage.message_number).all()

    transcript = "\n".join([
        f"{'Patient' if m.role == MessageRole.patient else 'AI'}: {m.content}"
        for m in messages
    ])

    # Generate structured summary via Claude
    summary_data = generate_intake_summary(transcript)

    # Update session with summary
    session.status               = IntakeStatus.completed
    session.ai_summary           = summary_data.get("summary", "")
    session.ai_risk_level        = summary_data.get("risk_level", "low")
    session.ai_risk_flags        = summary_data.get("risk_flags", [])
    session.chief_complaint      = summary_data.get("chief_complaint", "")
    session.symptoms             = summary_data.get("symptoms", [])
    session.current_medications  = summary_data.get("current_medications", [])
    session.allergies_reported   = summary_data.get("allergies", [])
    session.family_history       = summary_data.get("family_history", "")
    session.medical_history      = summary_data.get("medical_history", "")
    session.completed_at         = datetime.utcnow()

    # Update appointment status
    session.appointment.status = AppointmentStatus.intake_done

    db.commit()

    # Fire N8N webhook to notify doctor intake is ready (non-blocking)
    n8n_url = os.getenv("N8N_WEBHOOK_INTAKE_COMPLETE", "")
    if n8n_url:
        try:
            import asyncio
            doctor = session.appointment.doctor
            asyncio.create_task(
                _fire_intake_webhook(n8n_url, {
                    "appointment_id" : session.appointment_id,
                    "patient_name"   : current_patient.full_name,
                    "doctor_name"    : doctor.full_name,
                    "doctor_email"   : doctor.email,
                    "scheduled_time" : session.appointment.scheduled_time,
                    "risk_level"     : session.ai_risk_level,
                    "ai_summary"     : session.ai_summary or "",
                })
            )
        except Exception:
            pass  # Never block patient for N8N failure

    return {
        "message": "Intake complete",
        "session_id": session_id,
        "risk_level": session.ai_risk_level,
    }


async def _fire_intake_webhook(url: str, payload: dict):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json=payload)
    except Exception:
        pass
