"""
LabMind AI — Report & Review Pydantic Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.constants import ReportStatus, ReviewDecision


# ── Report Schemas ──

class ReportCreate(BaseModel):
    case_id: UUID
    run_id: UUID | None = None
    title: str
    summary: str | None = None
    findings: str | None = None
    recommendations: str | None = None
    clinician_notes: str | None = None
    ai_summary: dict | None = None


class ReportUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    findings: str | None = None
    recommendations: str | None = None
    clinician_notes: str | None = None


class ReportResponse(BaseModel):
    id: UUID
    case_id: UUID
    run_id: UUID | None = None
    created_by: UUID
    status: ReportStatus
    title: str
    summary: str | None = None
    findings: str | None = None
    recommendations: str | None = None
    clinician_notes: str | None = None
    ai_summary: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id: UUID
    case_id: UUID
    status: ReportStatus
    title: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Review Schemas ──

class ReviewRequest(BaseModel):
    decision: ReviewDecision
    comments: str | None = None


class ReviewResponse(BaseModel):
    id: UUID
    report_id: UUID
    reviewer_id: UUID
    decision: ReviewDecision
    comments: str | None = None
    reviewed_at: datetime

    model_config = {"from_attributes": True}


class ReportDetailResponse(BaseModel):
    """Full report with review history."""
    report: ReportResponse
    reviews: list[ReviewResponse] = []
