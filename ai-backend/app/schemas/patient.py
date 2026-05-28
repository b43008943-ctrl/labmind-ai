"""
LabMind AI — Patient Pydantic Schemas
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.constants import Gender


class PatientCreate(BaseModel):
    patient_code: str
    full_name: str
    date_of_birth: date | None = None
    gender: Gender | None = None
    blood_type: str | None = None
    contact_phone: str | None = None
    notes: str | None = None


class PatientResponse(BaseModel):
    id: UUID
    patient_code: str
    full_name: str
    date_of_birth: date | None = None
    gender: Gender | None = None
    blood_type: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PatientUpdate(BaseModel):
    full_name: str | None = None
    date_of_birth: date | None = None
    gender: Gender | None = None
    blood_type: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
