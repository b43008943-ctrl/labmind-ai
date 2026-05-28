"""
LabMind AI — Lab Case API Routes
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_client_ip, get_current_user, require_role
from app.core.constants import CaseStatus, UserRole
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.case import CaseCreate, CaseDetail, CaseResponse, CaseStatusUpdate
from app.services.case_service import CaseService

router = APIRouter(prefix="/api/cases", tags=["Lab Cases"])


@router.post("/", response_model=CaseResponse, status_code=201)
def create_case(
    body: CaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip = get_client_ip(request)
    service = CaseService(db)
    return service.create(body, clinician_id=current_user.id, ip=ip)


@router.get("/", response_model=list[CaseResponse])
def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: CaseStatus | None = Query(None),
    department: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CaseService(db)
    return service.list_all(skip=skip, limit=limit, status=status, department=department)


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CaseService(db)
    return service.get(case_id)


@router.patch("/{case_id}/status", response_model=CaseResponse)
def update_case_status(
    case_id: UUID,
    body: CaseStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLINICIAN, UserRole.ADMIN)),
):
    ip = get_client_ip(request)
    service = CaseService(db)
    return service.update_status(case_id, body.status, user_id=current_user.id, ip=ip)
