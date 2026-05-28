"""
LabMind AI — Analysis Pydantic Schemas
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.constants import AnalysisStatus


class AnalysisTriggerRequest(BaseModel):
    case_id: UUID
    asset_id: UUID


class AnalysisRunResponse(BaseModel):
    id: UUID
    case_id: UUID
    asset_id: UUID
    triggered_by: UUID
    engine_version: str
    status: AnalysisStatus
    config_snapshot: dict | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class AnalysisResultResponse(BaseModel):
    id: UUID
    run_id: UUID
    total_cells: int
    sickle_count: int
    normal_count: int
    sickle_percentage: float
    cell_details: dict | list | None = None
    annotated_image_key: str | None = None
    quality_score: float | None = None
    quality_status: str | None = None
    rejection_reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisDetailResponse(BaseModel):
    """Combined run + result for full detail view."""
    run: AnalysisRunResponse
    result: AnalysisResultResponse | None = None
