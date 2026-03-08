from database import SessionLocal
from models import Doctor
import bcrypt as _bcrypt

db = SessionLocal()

doctors = [
    {"email": "sarah@clinic.com", "password": "doctor123"},
    {"email": "ahmed.doc@clinic.com", "password": "doctor123"},
]

for d in doctors:
    doc = db.query(Doctor).filter(Doctor.email == d["email"]).first()
    if doc:
        new_hash = _bcrypt.hashpw(d["password"].encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
        doc.password_hash = new_hash
        print(f"Updated: {d['email']}")
    else:
        print(f"Not found: {d['email']}")

db.commit()
db.close()
print("Done - doctors passwords reset successfully")