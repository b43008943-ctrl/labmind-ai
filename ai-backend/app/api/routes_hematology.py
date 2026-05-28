"""
LabMind AI — Hematology Routes
==============================

API endpoints specific to the hematology (sickle cell) module.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.db.models.user import User

logger = logging.getLogger("labmind.routes_hematology")

router = APIRouter(prefix="/api/hematology", tags=["Hematology"])


# ── Pydantic models for clinical report ──────────────────────────────

class HematologyClinicalReportRequest(BaseModel):
    """Request body for the hematology clinical report endpoint."""
    cell_counts: dict = {}
    detections: list = []
    patient_context: dict | None = None
    use_ai: bool = True


@router.post("/clinical-report", status_code=200)
async def get_clinical_report(
    request: HematologyClinicalReportRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a full clinical reasoning report from hematology
    sickle cell detection results.

    Combines a deterministic rule-based analysis (5 clinical scenarios)
    with optional AI-enhanced insights from Gemini 2.0 Flash.

    The rule-based report is always returned.  AI enhancement adds
    pathophysiology, teaching pearls, rare considerations, and
    prioritised next steps.  If the AI call fails, the rule-based
    report is still returned with an ``ai_error`` field.
    """
    try:
        from app.services.hematology_ai_enhancer import generate_full_clinical_report

        report = await generate_full_clinical_report(
            cell_counts=request.cell_counts,
            detections=request.detections or None,
            patient_context=request.patient_context,
            use_ai=request.use_ai,
        )
        return report
    except Exception as exc:
        logger.error("Clinical report generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {exc}",
        )
