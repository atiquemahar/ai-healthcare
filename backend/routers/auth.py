from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from database import get_db
from models import Patient, Doctor
from schemas import PatientRegister, LoginRequest, TokenResponse, UserResponse

load_dotenv()

router = APIRouter()

# ─── Security setup ───────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))


# ─── Helpers ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decode JWT and return the current user (patient or doctor)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if role == "patient":
        user = db.query(Patient).filter(Patient.id == user_id).first()
    elif role == "doctor":
        user = db.query(Doctor).filter(Doctor.id == user_id).first()
    else:
        raise credentials_exception

    if user is None or not user.is_active:
        raise credentials_exception

    user.role = role  # attach role to object for downstream use
    return user

def require_patient(current_user=Depends(get_current_user)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patients only")
    return current_user

def require_doctor(current_user=Depends(get_current_user)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctors only")
    return current_user


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse)
def register_patient(data: PatientRegister, db: Session = Depends(get_db)):
    """Register a new patient account."""
    existing = db.query(Patient).filter(Patient.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    patient = Patient(
        first_name    = data.first_name,
        last_name     = data.last_name,
        email         = data.email,
        password_hash = hash_password(data.password),
        phone         = data.phone,
        date_of_birth = data.date_of_birth,
        gender        = data.gender,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    token = create_token({"sub": patient.id, "role": "patient"})
    return TokenResponse(access_token=token, role="patient")


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login for patients and doctors. Returns JWT token + role."""

    # Try patient first
    user = db.query(Patient).filter(Patient.email == data.email).first()
    role = "patient"

    # Try doctor if not found as patient
    if not user:
        user = db.query(Doctor).filter(Doctor.email == data.email).first()
        role = "doctor"

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_token({"sub": user.id, "role": role})
    return TokenResponse(access_token=token, role=role)


@router.post("/logout")
def logout():
    """Client should delete the token. Server is stateless."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    """Return current logged-in user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
    )
