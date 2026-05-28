"""
LabMind AI — Diagnostic Report API Routes
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_client_ip, get_current_user, require_role
from app.core.constants import ReportStatus, ReviewDecision, REVIEWER_ROLES, UserRole

from app.db.database import get_db
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.report import (
    ReportCreate,
    ReportDetailResponse,
    ReportListItem,
    ReportResponse,
    ReportUpdate,
    ReviewRequest,
    ReviewResponse,
)
from app.services.alert_service_domain import DomainAlertService
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["Diagnostic Reports"])


@router.post("/", response_model=ReportResponse, status_code=201)
def create_report(
    body: ReportCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip = get_client_ip(request)
    service = ReportService(db)
    return service.create(body, user_id=current_user.id, ip=ip)


@router.get("/", response_model=list[ReportListItem])
def list_reports(
    case_id: UUID | None = Query(None),
    status: ReportStatus | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    if case_id:
        return service.list_by_case(case_id)
    if status:
        return service.list_by_status(status, skip=skip, limit=limit)
    return []


@router.get("/my-reports", response_model=list[ReportListItem])
def list_my_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reports created by the current user (personal workspace)."""
    service = ReportService(db)
    return service.list_my_reports(current_user.id, skip=skip, limit=limit)


@router.get("/my-archive", response_model=list[ReportListItem])
def list_my_archive(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's archived reports (personal archive)."""
    service = ReportService(db)
    return service.list_my_archive(current_user.id)


@router.get("/pending-review", response_model=list[ReportListItem])
def list_pending_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    return service.list_pending_review(skip=skip, limit=limit)


@router.get("/{report_id}", response_model=ReportDetailResponse)
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    report = service.get(report_id)
    reviews = service.get_reviews(report_id)
    return ReportDetailResponse(
        report=ReportResponse.model_validate(report),
        reviews=[ReviewResponse.model_validate(r) for r in reviews],
    )


@router.patch("/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: UUID,
    body: ReportUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip = get_client_ip(request)
    service = ReportService(db)
    return service.update(report_id, body, user=current_user, ip=ip)


@router.post("/{report_id}/submit", response_model=ReportResponse)
def submit_for_review(
    report_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip = get_client_ip(request)
    service = ReportService(db)
    updated = service.submit_for_review(report_id, user=current_user, ip=ip)

    # Generate alerts for all users with reviewer roles (clinician, admin)
    alert_service = DomainAlertService(db)
    user_repo = UserRepository(db)
    reviewers = user_repo.list_by_roles(list(REVIEWER_ROLES))
    for reviewer in reviewers:
        if reviewer.id != current_user.id:
            alert_service.on_report_submitted(
                reviewer_id=reviewer.id,
                report_id=report_id,
                submitted_by_name=current_user.full_name,
            )
    return updated


@router.post("/{report_id}/review", response_model=ReviewResponse)
def review_report(
    report_id: UUID,
    body: ReviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLINICIAN, UserRole.ADMIN)),
):
    ip = get_client_ip(request)
    service = ReportService(db)
    updated_report, review = service.review(
        report_id=report_id,
        reviewer=current_user,
        decision=body.decision,
        comments=body.comments,
        ip=ip,
    )

    # Generate rejection alert to the report author
    if body.decision == ReviewDecision.REJECTED:
        alert_service = DomainAlertService(db)
        alert_service.on_report_rejected(
            author_id=updated_report.created_by,
            report_id=report_id,
            reviewer_name=current_user.full_name,
            comments=body.comments,
        )

    return ReviewResponse.model_validate(review)


@router.post("/{report_id}/archive", response_model=ReportResponse)
def archive_report(
    report_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip = get_client_ip(request)
    service = ReportService(db)
    return service.archive(report_id, user=current_user, ip=ip)
