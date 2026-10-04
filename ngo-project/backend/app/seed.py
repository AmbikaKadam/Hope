"""Sample data so the dashboard and beneficiary pages have something to show.

- Runs automatically on startup, but only if the table is empty.
- To wipe the database and start again:   python -m app.seed
Registration dates are relative to today ("4 days ago"), so the dashboard's
"recently added" numbers and charts always look sensible whenever you run it.
"""
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Beneficiary

P = {
    "mental": "Mental Wellness Program",
    "edu": "Education Support Program",
    "women": "Women Skill Development",
    "health": "Healthcare Support Program",
    "livelihood": "Livelihood Development Program",
    "nutrition": "Community Nutrition Program",
}

# name, age, gender, phone, city, programme, status, registered N days ago, primary need
SAMPLE = [
    ("Priya Sharma", 28, "Female", "9876543210", "Pune", P["mental"], "Active", 4, "Mental Health"),
    ("Rahul Patil", 34, "Male", "9876501234", "Pimpri", P["livelihood"], "Active", 6, "Employment"),
    ("Sneha More", 19, "Female", "9867456123", "Pune", P["edu"], "Follow-up Required", 10, "Education"),
    ("Aarav Kulkarni", 12, "Male", "9822014321", "Hadapsar", P["edu"], "Active", 8, "Education"),
    ("Meera Joshi", 42, "Female", "9890123456", "Kothrud", P["women"], "Active", 3, "Women Empowerment"),
    ("Vikram Deshmukh", 51, "Male", "9765432109", "Pimpri", P["health"], "Inactive", 47, "Healthcare"),
    ("Ananya Pawar", 24, "Female", "9823456781", "Wakad", P["women"], "Active", 5, "Employment"),
    ("Sanjay Gaikwad", 46, "Male", "9898765432", "Baramati", P["livelihood"], "Follow-up Required", 11, "Financial Support"),
    ("Kavita Jadhav", 31, "Female", "9812345670", "Pune", P["nutrition"], "Active", 7, "Food/Nutrition"),
    ("Imran Shaikh", 17, "Male", "9867012345", "Kondhwa", P["edu"], "Active", 9, "Education"),
    ("Pooja Bhosale", 27, "Female", "9890011223", "Saswad", P["mental"], "Active", 2, "Mental Health"),
    ("Nitin Chavan", 38, "Male", "9765001122", "Pune", P["health"], "Completed", 23, "Healthcare"),
    ("Asha Waghmare", 55, "Female", "9822009876", "Daund", P["nutrition"], "Active", 12, "Healthcare"),
    ("Omkar Shinde", 22, "Male", "9876012345", "Pimpri", P["livelihood"], "Active", 4, "Employment"),
    ("Fatima Qureshi", 29, "Female", "9898981212", "Kondhwa", P["women"], "Follow-up Required", 13, "Women Empowerment"),
    ("Rohan Thorat", 14, "Male", "9765400011", "Hinjewadi", P["edu"], "Active", 8, "Education"),
    ("Lata Kamble", 63, "Female", "9822098765", "Pune", P["health"], "Active", 15, "Healthcare"),
    ("Siddharth Naik", 33, "Male", "9890111222", "Wakad", P["livelihood"], "Completed", 18, "Employment"),
    # a few older registrations so the 6-month / 1-year charts have data
    ("Deepak Mane", 36, "Male", "9823001122", "Pune", P["livelihood"], "Active", 75, "Employment"),
    ("Sunita Gawade", 41, "Female", "9890223344", "Hadapsar", P["nutrition"], "Active", 112, "Food/Nutrition"),
    ("Mohan Salunkhe", 58, "Male", "9765123456", "Baramati", P["health"], "Inactive", 160, "Healthcare"),
    ("Reshma Sayyed", 26, "Female", "9811223344", "Wakad", P["women"], "Completed", 240, "Women Empowerment"),
]


def seed_if_empty(db: Session) -> int:
    """Insert the sample rows if the table has no data. Returns how many rows were added."""
    if db.scalars(select(Beneficiary).limit(1)).first():
        return 0
    today = date.today()
    for name, age, gender, phone, city, program, status, days_ago, need in SAMPLE:
        registered = today - timedelta(days=days_ago)
        stamp = datetime.combine(registered, time(10, 0))
        db.add(Beneficiary(
            name=name, age=age, gender=gender, phone=phone, city=city, program=program,
            status=status, primary_need=need, state="Maharashtra", urgency="Medium",
            assigned_staff="Anjali Joshi", registration_date=registered,
            secondary_needs="Community support",
            need_description="Ongoing support and access to program services.",
            assessment="Enrolled in the program and receiving regular community support.",
            created_at=stamp, updated_at=stamp,
        ))
    db.commit()
    return len(SAMPLE)


if __name__ == "__main__":
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        print(f"Database reset. Inserted {seed_if_empty(session)} sample beneficiaries.")
