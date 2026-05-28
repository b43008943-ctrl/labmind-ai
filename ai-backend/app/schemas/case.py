"""
LabMind AI — Lab Case Pydantic Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.constants import CasePriority, CaseStatus, Department
from app.schemas.patient import PatientResponse


class CaseCreate(BaseModel):
    patient_id: UUID
    department: Department
    test_type: str
    priority: CasePriority = CasePriority.ROUTINE
    notes: str | None = None


class CaseResponse(BaseModel):
    id: UUID
    case_number: str
    patient_id: UUID
    clinician_id: UUID
    department: Department
    test_type: str
    priority: CasePriority
    status: CaseStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseDetail(CaseResponse):
    """Extended response with nested patient info."""
    patient: PatientResponse | None = None

    model_config = {"from_attributes": True}


class CaseStatusUpdate(BaseModel):
    status: CaseStatus
