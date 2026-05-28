"""
LabMind AI — Alert API Routes
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_client_ip, get_current_user
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.alert import AlertDismissRequest, AlertResponse
from app.services.alert_service_domain import DomainAlertService

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    include_dismissed: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DomainAlertService(db)
    return service.list_for_user(current_user.id, include_dismissed=include_dismissed)


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DomainAlertService(db)
    return {"count": service.unread_count(current_user.id)}


@router.post("/{alert_id}/read")
def mark_alert_read(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DomainAlertService(db)
    service.mark_read(alert_id, current_user.id)
    return {"message": "Alert marked as read."}


@router.post("/{alert_id}/dismiss", response_model=AlertResponse)
def dismiss_alert(
    alert_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip = get_client_ip(request)
    service = DomainAlertService(db)
    return service.dismiss(alert_id, user_id=current_user.id, ip=ip)
