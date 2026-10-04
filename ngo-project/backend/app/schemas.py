"""Pydantic schemas = the shape and validation rules of the JSON the API accepts/returns."""
import re
from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

Gender = Literal["Female", "Male", "Other", "Prefer not to say"]
Status = Literal["Active", "Inactive", "Follow-up Required", "Completed"]
Urgency = Literal["Low", "Medium", "High", "Critical"]

PHONE_RE = re.compile(r"[6-9]\d{9}")  # Indian mobile: 10 digits starting with 6-9
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def clean_phone(value: str) -> str:
    """Remove spaces/dashes and a leading +91, then check it is a valid mobile number."""
    digits = re.sub(r"[\s\-]", "", value)
    if not digits:
        raise ValueError("Phone number is required")
    if digits.startswith("+91"):
        digits = digits[3:]
    if not PHONE_RE.fullmatch(digits):
        raise ValueError("Enter a valid 10-digit mobile number")
    return digits


# ---------------------------------------------------------------- beneficiary fields
class BeneficiaryBase(BaseModel):
    """Fields shared by input and output schemas (with their basic constraints)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # required
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=120)
    gender: Gender
    phone: str = Field(max_length=20)
    city: str = Field(min_length=2, max_length=80)

    status: Status = "Active"

    # optional
    email: str | None = Field(None, max_length=120)
    dob: date | None = None
    address: str | None = Field(None, max_length=255)
    state: str | None = Field("Maharashtra", max_length=80)
    emergency: str | None = Field(None, max_length=20)
    gov_id_type: str | None = Field(None, max_length=30)
    gov_id_number: str | None = Field(None, max_length=30)
    marital: str | None = Field(None, max_length=20)
    occupation: str | None = Field(None, max_length=80)
    family_members: int | None = Field(None, ge=0, le=50)
    income: int | None = Field(None, ge=0)
    education: str | None = Field(None, max_length=40)
    primary_need: str | None = Field(None, max_length=40)
    secondary_needs: str | None = Field(None, max_length=200)
    need_description: str | None = Field(None, max_length=2000)
    urgency: Urgency = "Medium"
    assessment: str | None = Field(None, max_length=4000)
    program: str | None = Field(None, max_length=80)
    registration_date: date | None = None  # defaults to today when omitted
    assigned_staff: str | None = Field(None, max_length=80)


class BeneficiaryCreate(BeneficiaryBase):
    """Request body for POST. Adds the extra validation rules."""

    @field_validator(
        "email", "dob", "address", "state", "emergency", "gov_id_type", "gov_id_number",
        "marital", "occupation", "family_members", "income", "education", "primary_need",
        "secondary_needs", "need_description", "assessment", "program",
        "registration_date", "assigned_staff",
        mode="before",
    )
    @classmethod
    def blank_to_none(cls, value):
        """An empty form box ("") should be stored as NULL, not as an empty string."""
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value):
        return clean_phone(value)

    @field_validator("emergency")
    @classmethod
    def check_emergency(cls, value):
        return None if value is None else clean_phone(value)

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        if value is not None and not EMAIL_RE.fullmatch(value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("dob", "registration_date")
    @classmethod
    def not_in_future(cls, value):
        if value is not None and value > date.today():
            raise ValueError("Date cannot be in the future")
        return value


class BeneficiaryUpdate(BeneficiaryCreate):
    """Request body for PUT (full update - same rules as create)."""


class BeneficiaryOut(BeneficiaryBase):
    """Response body. Reads straight from the SQLAlchemy object."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    registration_date: date
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def as_utc(self, value: datetime):
        # SQLite returns naive datetimes; label them UTC so the browser converts correctly.
        return value.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------- dashboard
class ProgramCount(BaseModel):
    program: str
    count: int


class RegistrationPoint(BaseModel):
    label: str
    count: int


class RegistrationSeries(BaseModel):
    points: list[RegistrationPoint]
    total: int
    previous_total: int
    change_percent: float | None  # None when the previous period had 0 registrations


class RecentActivity(BaseModel):
    id: int
    code: str
    name: str
    program: str | None
    action: Literal["registered", "updated"]
    timestamp: datetime

    @field_serializer("timestamp")
    def as_utc(self, value: datetime):
        return value.replace(tzinfo=timezone.utc)


class DashboardStatistics(BaseModel):
    total_beneficiaries: int
    active_beneficiaries: int
    inactive_beneficiaries: int
    follow_up_required: int
    completed: int
    recent_days: int
    recent_beneficiaries: int
    by_program: list[ProgramCount]
    registrations: dict[str, RegistrationSeries]
    recent_activity: list[RecentActivity]
