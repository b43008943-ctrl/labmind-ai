"""
LabMind AI — Analysis API Routes
Endpoints: trigger analysis, poll status, get results, download annotated image.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_client_ip, get_current_user
from app.core.exceptions import NotFoundException
from app.db.database import get_db
from app.db.models.user import User
from app.providers.storage_provider_local import LocalStorageProvider
from app.schemas.analysis import (
    AnalysisDetailResponse,
    AnalysisResultResponse,
    AnalysisRunResponse,
    AnalysisTriggerRequest,
)
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/analyses", tags=["Analysis"])


@router.post("/trigger", response_model=AnalysisRunResponse, status_code=202)
def trigger_analysis(
    body: AnalysisTriggerRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue a V34 blood smear analysis. Returns immediately with run ID for polling."""
    ip = get_client_ip(request)
    service = AnalysisService(db)
    run = service.trigger(
        case_id=body.case_id,
        asset_id=body.asset_id,
        user_id=current_user.id,
        ip=ip,
    )
    return run


@router.get("/runs/{run_id}", response_model=AnalysisDetailResponse)
def get_analysis_status(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll analysis status. Returns run + result (if completed). Owner or admin only."""
    service = AnalysisService(db)
    run = service.get_run(run_id, user=current_user)
    result = service.get_result(run_id, user=current_user)
    return AnalysisDetailResponse(
        run=AnalysisRunResponse.model_validate(run),
        result=AnalysisResultResponse.model_validate(result) if result else None,
    )


@router.get("/cases/{case_id}", response_model=list[AnalysisRunResponse])
def list_analyses_by_case(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all analysis runs for a specific case."""
    service = AnalysisService(db)
    return service.list_by_case(case_id)


@router.get("/runs/{run_id}/annotated-image")
def get_annotated_image(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the annotated diagnostic image. Owner or admin only."""
    service = AnalysisService(db)
    result = service.get_result(run_id, user=current_user)
    if not result or not result.annotated_image_key:
        raise NotFoundException(detail="Annotated image not available.")

    storage = LocalStorageProvider()
    data = storage.download(result.annotated_image_key)
    return Response(
        content=data,
        media_type="image/jpeg",
        headers={"Content-Disposition": f'inline; filename="analysis_{run_id}.jpg"'},
    )
