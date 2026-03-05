from datetime import time

from database import SessionLocal
from models import Doctor, DoctorAvailability


def seed_default_availability():
    """
    Create default Monday–Friday 9:00–17:00 availability for all doctors
    that do not already have any availability configured.
    """
    db = SessionLocal()
    try:
        doctors = db.query(Doctor).all()
        created = 0

        for doctor in doctors:
            # Skip doctors that already have availability rows
            existing = (
                db.query(DoctorAvailability)
                .filter(DoctorAvailability.doctor_id == doctor.id)
                .first()
            )
            if existing:
                continue

            for day in range(0, 5):  # 0=Mon .. 4=Fri
                avail = DoctorAvailability(
                    doctor_id=doctor.id,
                    day_of_week=day,
                    start_time=time(hour=9, minute=0),
                    end_time=time(hour=17, minute=0),
                )
                db.add(avail)
                created += 1

        db.commit()
        print(f"Seeded {created} availability rows.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_default_availability()

