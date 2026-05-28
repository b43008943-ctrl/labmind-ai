"""
LabMind AI — Domain Alert Service
Generates system alerts for clinical events and manages alert lifecycle.
Separate from AuditService (which logs audit trail events).
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import AlertPriority, AlertType, AuditAction
from app.db.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.services.audit_service import AuditService


class DomainAlertService:
    def __init__(self, db: Session):
        self.repo = AlertRepository(db)
        self.audit = AuditService(db)

    # ── Alert Generation Rules ──

    def on_critical_finding(
        self,
        user_id: UUID,
        report_id: UUID,
        sickle_percentage: float,
    ) -> Alert:
        """Generate alert when AI detects a critical sickle cell percentage."""
        alert = Alert(
            user_id=user_id,
            alert_type=AlertType.CRITICAL_FINDING,
            priority=AlertPriority.CRITICAL,
            title="Critical AI Finding Detected",
            message=(
                f"Sickle cell percentage of {sickle_percentage:.1f}% detected. "
                "Immediate clinical review recommended."
            ),
            entity_type="diagnostic_report",
            entity_id=report_id,
        )
        created = self.repo.create(alert)
        self.audit.log(
            action=AuditAction.ALERT_CREATED,
            user_id=user_id,
            entity_type="alert",
            entity_id=created.id,
            details={"alert_type": "critical_finding", "sickle_pct": sickle_percentage},
        )
        return created

    def on_report_submitted(
        self,
        reviewer_id: UUID,
        report_id: UUID,
        submitted_by_name: str,
    ) -> Alert:
        """Notify reviewer that a report is pending review."""
        alert = Alert(
            user_id=reviewer_id,
            alert_type=AlertType.REVIEW_REQUIRED,
            priority=AlertPriority.HIGH,
            title="Report Submitted for Review",
            message=f"A diagnostic report from {submitted_by_name} requires your review.",
            entity_type="diagnostic_report",
            entity_id=report_id,
        )
        created = self.repo.create(alert)
        self.audit.log(
            action=AuditAction.ALERT_CREATED,
            user_id=reviewer_id,
            entity_type="alert",
            entity_id=created.id,
            details={"alert_type": "review_required", "report_id": str(report_id)},
        )
        return created

    def on_report_rejected(
        self,
        author_id: UUID,
        report_id: UUID,
        reviewer_name: str,
        comments: str | None = None,
    ) -> Alert:
        """Notify report author that their report was rejected."""
        msg = f"Your diagnostic report was rejected by {reviewer_name}."
        if comments:
            msg += f" Reason: {comments}"
        alert = Alert(
            user_id=author_id,
            alert_type=AlertType.REPORT_REJECTED,
            priority=AlertPriority.HIGH,
            title="Report Rejected",
            message=msg,
            entity_type="diagnostic_report",
            entity_id=report_id,
        )
        created = self.repo.create(alert)
        self.audit.log(
            action=AuditAction.ALERT_CREATED,
            user_id=author_id,
            entity_type="alert",
            entity_id=created.id,
            details={"alert_type": "report_rejected", "report_id": str(report_id)},
        )
        return created

    # ── Alert Management ──

    def list_for_user(self, user_id: UUID, include_dismissed: bool = False) -> list[Alert]:
        return self.repo.list_by_user(user_id, include_dismissed=include_dismissed)

    def dismiss(self, alert_id: UUID, user_id: UUID, ip: str | None = None) -> Alert:
        alert = self.repo.get_by_id(alert_id)
        if not alert:
            from app.core.exceptions import NotFoundException
            raise NotFoundException(detail="Alert not found.")
        if alert.user_id != user_id:
            from app.core.exceptions import ForbiddenException
            raise ForbiddenException(detail="Cannot dismiss another user's alert.")

        dismissed = self.repo.dismiss(alert)
        self.audit.log(
            action=AuditAction.ALERT_DISMISSED,
            user_id=user_id,
            entity_type="alert",
            entity_id=alert_id,
            ip_address=ip,
        )
        return dismissed

    def mark_read(self, alert_id: UUID, user_id: UUID) -> None:
        alert = self.repo.get_by_id(alert_id)
        if alert and alert.user_id == user_id:
            self.repo.mark_read(alert_id)

    def unread_count(self, user_id: UUID) -> int:
        return self.repo.count_unread(user_id)
