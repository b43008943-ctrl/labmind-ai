"""
LabMind AI — Report Service
Orchestrates report lifecycle, workflow state machine, and reviews.

Authorization model:
- OWNERSHIP: Users can only edit/submit/archive their OWN reports.
- ADMIN BYPASS: Admins can act on any report.
- REVIEW: Only clinicians and admins can approve/reject/request_changes.
- PERSONAL ARCHIVE: Each user manages their own archived reports.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import (
    AuditAction,
    ReportStatus,
    ReviewDecision,
    REVIEWER_ROLES,
    UserRole,
)
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException
from app.db.models.diagnostic_report import DiagnosticReport
from app.db.models.report_review import ReportReview
from app.db.models.user import User
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportCreate, ReportUpdate
from app.services.audit_service import AuditService


# ── Allowed state transitions ──
VALID_TRANSITIONS: dict[ReportStatus, set[ReportStatus]] = {
    ReportStatus.DRAFT: {ReportStatus.PRELIMINARY, ReportStatus.PENDING_REVIEW},
    ReportStatus.PROCESSING: {ReportStatus.PRELIMINARY, ReportStatus.DRAFT},
    ReportStatus.PRELIMINARY: {ReportStatus.PENDING_REVIEW, ReportStatus.DRAFT},
    ReportStatus.PENDING_REVIEW: {ReportStatus.APPROVED, ReportStatus.REJECTED, ReportStatus.DRAFT},
    ReportStatus.APPROVED: {ReportStatus.ARCHIVED},
    ReportStatus.REJECTED: {ReportStatus.DRAFT},
    ReportStatus.ARCHIVED: set(),  # terminal state
}


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportRepository(db)
        self.audit = AuditService(db)

    # ── Ownership helper ──

    @staticmethod
    def _check_ownership(report: DiagnosticReport, user: User, action: str) -> None:
        """Ensure the user owns the report, or is an admin."""
        if user.role == UserRole.ADMIN:
            return  # admins can act on any report
        if report.created_by != user.id:
            raise ForbiddenException(
                detail=f"You can only {action} your own reports."
            )

    # ── CRUD ──

    def create(
        self, data: ReportCreate, user_id: UUID, ip: str | None = None
    ) -> DiagnosticReport:
        report = DiagnosticReport(
            case_id=data.case_id,
            run_id=data.run_id,
            created_by=user_id,
            status=ReportStatus.DRAFT,
            title=data.title,
            summary=data.summary,
            findings=data.findings,
            recommendations=data.recommendations,
            clinician_notes=data.clinician_notes,
            ai_summary=data.ai_summary,
        )
        created = self.repo.create(report)

        self.audit.log(
            action=AuditAction.REPORT_CREATED,
            user_id=user_id,
            entity_type="diagnostic_report",
            entity_id=created.id,
            details={"case_id": str(data.case_id), "title": data.title},
            ip_address=ip,
        )
        return created

    def get(self, report_id: UUID) -> DiagnosticReport:
        report = self.repo.get_by_id(report_id)
        if not report:
            raise NotFoundException(detail="Diagnostic report not found.")
        return report

    def update(
        self, report_id: UUID, data: ReportUpdate, user: User, ip: str | None = None
    ) -> DiagnosticReport:
        report = self.get(report_id)
        self._check_ownership(report, user, "edit")

        if report.status not in (ReportStatus.DRAFT, ReportStatus.REJECTED):
            raise ValidationException(
                detail=f"Cannot edit report in '{report.status.value}' status. Only draft or rejected reports can be edited."
            )

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return report

        updated = self.repo.update(report, updates)

        self.audit.log(
            action=AuditAction.REPORT_UPDATED,
            user_id=user.id,
            entity_type="diagnostic_report",
            entity_id=report_id,
            details={"updated_fields": list(updates.keys())},
            ip_address=ip,
        )
        return updated

    def submit_for_review(
        self, report_id: UUID, user: User, ip: str | None = None
    ) -> DiagnosticReport:
        report = self.get(report_id)
        self._check_ownership(report, user, "submit")
        self._validate_transition(report.status, ReportStatus.PENDING_REVIEW)

        updated = self.repo.update_status(report, ReportStatus.PENDING_REVIEW)

        self.audit.log(
            action=AuditAction.REPORT_SUBMITTED,
            user_id=user.id,
            entity_type="diagnostic_report",
            entity_id=report_id,
            ip_address=ip,
        )
        return updated

    def review(
        self,
        report_id: UUID,
        reviewer: User,
        decision: ReviewDecision,
        comments: str | None = None,
        ip: str | None = None,
    ) -> tuple[DiagnosticReport, ReportReview]:
        # Authorization: only clinicians and admins can review
        if reviewer.role not in REVIEWER_ROLES:
            raise ForbiddenException(
                detail=f"Role '{reviewer.role.value}' cannot review reports. "
                       f"Required: {[r.value for r in REVIEWER_ROLES]}"
            )

        report = self.get(report_id)
        if report.status != ReportStatus.PENDING_REVIEW:
            raise ValidationException(
                detail=f"Report is in '{report.status.value}' status. "
                       "Only reports in 'pending_review' can be reviewed."
            )

        # Determine target status from decision
        status_map = {
            ReviewDecision.APPROVED: ReportStatus.APPROVED,
            ReviewDecision.REJECTED: ReportStatus.REJECTED,
            ReviewDecision.REQUEST_CHANGES: ReportStatus.DRAFT,
        }
        new_status = status_map[decision]

        # Create review record
        review_record = ReportReview(
            report_id=report_id,
            reviewer_id=reviewer.id,
            decision=decision,
            comments=comments,
        )
        created_review = self.repo.add_review(review_record)

        # Update report status
        updated_report = self.repo.update_status(report, new_status)

        self.audit.log(
            action=AuditAction.REPORT_REVIEWED,
            user_id=reviewer.id,
            entity_type="diagnostic_report",
            entity_id=report_id,
            details={
                "decision": decision.value,
                "new_status": new_status.value,
                "comments": comments,
            },
            ip_address=ip,
        )
        return updated_report, created_review

    def archive(
        self, report_id: UUID, user: User, ip: str | None = None
    ) -> DiagnosticReport:
        report = self.get(report_id)
        self._check_ownership(report, user, "archive")
        self._validate_transition(report.status, ReportStatus.ARCHIVED)

        updated = self.repo.update_status(report, ReportStatus.ARCHIVED)

        self.audit.log(
            action=AuditAction.REPORT_ARCHIVED,
            user_id=user.id,
            entity_type="diagnostic_report",
            entity_id=report_id,
            ip_address=ip,
        )
        return updated

    # ── Listings ──

    def list_by_case(self, case_id: UUID) -> list[DiagnosticReport]:
        return self.repo.list_by_case(case_id)

    def list_by_status(self, status: ReportStatus, skip: int = 0, limit: int = 50) -> list[DiagnosticReport]:
        return self.repo.list_by_status(status, skip=skip, limit=limit)

    def list_pending_review(self, skip: int = 0, limit: int = 50) -> list[DiagnosticReport]:
        return self.repo.list_by_status(ReportStatus.PENDING_REVIEW, skip=skip, limit=limit)

    def list_my_reports(self, user_id: UUID, skip: int = 0, limit: int = 50) -> list[DiagnosticReport]:
        return self.repo.list_by_user(user_id, skip=skip, limit=limit)

    def list_my_archive(self, user_id: UUID) -> list[DiagnosticReport]:
        return self.repo.list_by_user_and_status(user_id, ReportStatus.ARCHIVED)

    def get_reviews(self, report_id: UUID) -> list[ReportReview]:
        return self.repo.get_reviews(report_id)

    @staticmethod
    def _validate_transition(current: ReportStatus, target: ReportStatus) -> None:
        allowed = VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise ValidationException(
                detail=f"Cannot transition from '{current.value}' to '{target.value}'. "
                       f"Allowed: {[s.value for s in allowed]}"
            )
