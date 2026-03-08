"""
Run this from the backend/ folder:
    python reset_doctors.py
"""
from database import SessionLocal
from models import Doctor
import bcrypt as _bcrypt

db = SessionLocal()

doctors = [
    {"email": "sarah@clinic.com",      "password": "doctor123"},
    {"email": "ahmed.doc@clinic.com",  "password": "doctor123"},
]

print("Resetting doctor passwords...")

for d in doctors:
    doc = db.query(Doctor).filter(Doctor.email == d["email"]).first()
    if doc:
        new_hash = _bcrypt.hashpw(
            d["password"].encode("utf-8"),
            _bcrypt.gensalt()
        ).decode("utf-8")
        doc.password_hash = new_hash
        print(f"  Updated: {d['email']}")
    else:
        print(f"  Not found: {d['email']} (skipping)")

db.commit()
db.close()
print("Done! Doctors can now login with: doctor123")