from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from database import engine, Base
import models  # noqa: F401 — ensures models are registered before create_all

from routers import auth, patients, appointments, intake, doctor, internal

load_dotenv()

# ─── Create all tables on startup ─────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Healthcare Assistant API",
    description="Backend API for AI-powered pre-visit intake system",
    version="1.0.0"
)

# ─── CORS (allows frontend to call backend) ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/api/auth",     tags=["Auth"])
app.include_router(patients.router,     prefix="/api/patients", tags=["Patients"])
app.include_router(appointments.router, prefix="/api",          tags=["Appointments"])
app.include_router(intake.router,       prefix="/api/intake",   tags=["AI Intake"])
app.include_router(doctor.router,       prefix="/api/doctor",   tags=["Doctor"])
app.include_router(internal.router,     prefix="/api/internal", tags=["Internal (N8N)"])


@app.get("/")
def root():
    return {"status": "AI Healthcare API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
