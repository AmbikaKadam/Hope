"""SQLAlchemy models = the database tables."""
from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

STATUSES = ("Active", "Inactive", "Follow-up Required", "Completed")
_status_list = ", ".join(f"'{s}'" for s in STATUSES)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    # Constraints are enforced by SQLite itself, even if someone bypasses the API.
    __table_args__ = (
        CheckConstraint("age >= 0 AND age <= 120", name="ck_beneficiary_age"),
        CheckConstraint(f"status IN ({_status_list})", name="ck_beneficiary_status"),
        CheckConstraint("family_members IS NULL OR family_members >= 0", name="ck_beneficiary_family"),
        CheckConstraint("income IS NULL OR income >= 0", name="ck_beneficiary_income"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- required fields ---
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)

    # --- status doubles as the "soft delete" flag: deactivated = 'Inactive' ---
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Active", index=True)

    # --- optional personal details (all present in the existing React form) ---
    email: Mapped[str | None] = mapped_column(String(120))
    dob: Mapped[date | None] = mapped_column(Date)
    address: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str | None] = mapped_column(String(80), default="Maharashtra")
    emergency: Mapped[str | None] = mapped_column(String(15))
    gov_id_type: Mapped[str | None] = mapped_column(String(30))
    gov_id_number: Mapped[str | None] = mapped_column(String(30))
    marital: Mapped[str | None] = mapped_column(String(20))
    occupation: Mapped[str | None] = mapped_column(String(80))
    family_members: Mapped[int | None] = mapped_column(Integer)
    income: Mapped[int | None] = mapped_column(Integer)
    education: Mapped[str | None] = mapped_column(String(40))

    # --- needs assessment ---
    primary_need: Mapped[str | None] = mapped_column(String(40))
    secondary_needs: Mapped[str | None] = mapped_column(String(200))
    need_description: Mapped[str | None] = mapped_column(Text)
    urgency: Mapped[str] = mapped_column(String(10), nullable=False, default="Medium")
    assessment: Mapped[str | None] = mapped_column(Text)

    # --- programme information ---
    program: Mapped[str | None] = mapped_column(String(80))
    registration_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today, index=True)
    assigned_staff: Mapped[str | None] = mapped_column(String(80))

    # --- audit timestamps (stored in UTC) ---
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    @property
    def code(self) -> str:
        """Human-friendly ID shown in the UI, e.g. BEN-1001."""
        return f"BEN-{1000 + self.id}"
