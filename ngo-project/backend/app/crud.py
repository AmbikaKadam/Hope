"""CRUD = Create, Read, Update, Delete. All database queries live here."""
from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from . import models, schemas

B = models.Beneficiary


# ---------------------------------------------------------------- beneficiaries
def get_beneficiaries(db: Session, search: str | None = None, status: str | None = None,
                      skip: int = 0, limit: int = 1000):
    query = select(B)
    if search:
        like = f"%{search.strip()}%"
        query = query.where(or_(B.name.ilike(like), B.phone.ilike(like), B.city.ilike(like), B.program.ilike(like)))
    if status:
        query = query.where(B.status == status)
    query = query.order_by(B.created_at.desc(), B.id.desc()).offset(skip).limit(limit)
    return db.scalars(query).all()


def get_beneficiary(db: Session, beneficiary_id: int):
    return db.get(B, beneficiary_id)


def _clean(data: dict) -> dict:
    # registration_date=None means "not provided" -> let the model default (today) apply / keep old value
    if data.get("registration_date") is None:
        data.pop("registration_date", None)
    return data


def create_beneficiary(db: Session, payload: schemas.BeneficiaryCreate):
    beneficiary = B(**_clean(payload.model_dump()))
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


def update_beneficiary(db: Session, beneficiary: B, payload: schemas.BeneficiaryUpdate):
    for field, value in _clean(payload.model_dump()).items():
        setattr(beneficiary, field, value)
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


def deactivate_beneficiary(db: Session, beneficiary: B):
    """Soft delete: the row stays in the database, only its status changes."""
    beneficiary.status = "Inactive"
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


# ---------------------------------------------------------------- dashboard statistics
def _count_registered(db: Session, start: date, end: date) -> int:
    """How many beneficiaries have registration_date between start and end (inclusive)."""
    return db.scalar(
        select(func.count(B.id)).where(B.registration_date >= start, B.registration_date <= end)
    ) or 0


def _add_months(day: date, months: int) -> date:
    """First day of the month that is `months` away from `day`'s month."""
    index = day.year * 12 + (day.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def _daily_buckets(today: date, days: int):
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        yield day.strftime("%a"), day, day


def _weekly_buckets(today: date, weeks: int):
    for i in range(weeks - 1, -1, -1):
        end = today - timedelta(days=7 * i)
        yield f"Wk {weeks - i}", end - timedelta(days=6), end


def _monthly_buckets(today: date, months: int):
    for i in range(months - 1, -1, -1):
        start = _add_months(today, -i)
        end = min(_add_months(start, 1) - timedelta(days=1), today)
        yield start.strftime("%b"), start, end


def _build_series(db: Session, buckets) -> schemas.RegistrationSeries:
    buckets = list(buckets)
    points = [{"label": label, "count": _count_registered(db, start, end)} for label, start, end in buckets]
    total = sum(p["count"] for p in points)

    # Compare with the period of the same length immediately before this one.
    first_start, last_end = buckets[0][1], buckets[-1][2]
    span = (last_end - first_start).days + 1
    previous_total = _count_registered(db, first_start - timedelta(days=span), first_start - timedelta(days=1))
    change = round((total - previous_total) / previous_total * 100, 1) if previous_total else None
    return schemas.RegistrationSeries(points=points, total=total, previous_total=previous_total, change_percent=change)


def get_dashboard_statistics(db: Session, recent_days: int = 30) -> schemas.DashboardStatistics:
    today = date.today()

    total = db.scalar(select(func.count(B.id))) or 0
    by_status = dict(db.execute(select(B.status, func.count(B.id)).group_by(B.status)).all())
    recent = _count_registered(db, today - timedelta(days=recent_days), today)

    program_rows = db.execute(
        select(func.coalesce(B.program, "Unassigned"), func.count(B.id))
        .group_by(func.coalesce(B.program, "Unassigned"))
        .order_by(func.count(B.id).desc())
    ).all()

    registrations = {
        "7 Days": _build_series(db, _daily_buckets(today, 7)),
        "30 Days": _build_series(db, _weekly_buckets(today, 4)),
        "6 Months": _build_series(db, _monthly_buckets(today, 6)),
        "1 Year": _build_series(db, _monthly_buckets(today, 12)),
    }

    latest = db.scalars(select(B).order_by(B.updated_at.desc()).limit(5)).all()
    activity = [
        {
            "id": b.id, "code": b.code, "name": b.name, "program": b.program,
            # never edited since it was created -> it was a registration
            "action": "registered" if abs((b.updated_at - b.created_at).total_seconds()) < 1 else "updated",
            "timestamp": b.updated_at,
        }
        for b in latest
    ]

    return schemas.DashboardStatistics(
        total_beneficiaries=total,
        active_beneficiaries=by_status.get("Active", 0),
        inactive_beneficiaries=by_status.get("Inactive", 0),
        follow_up_required=by_status.get("Follow-up Required", 0),
        completed=by_status.get("Completed", 0),
        recent_days=recent_days,
        recent_beneficiaries=recent,
        by_program=[{"program": name, "count": count} for name, count in program_rows],
        registrations=registrations,
        recent_activity=activity,
    )
