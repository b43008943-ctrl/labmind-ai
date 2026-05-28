"""
LabMind AI — Lab Case Service
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import AuditAction, CaseStatus
from app.core.exceptions import NotFoundException
from app.db.models.lab_case import LabCase
from app.repositories.case_repository import CaseRepository
from app.schemas.case import CaseCreate
from app.services.audit_service import AuditService


class CaseService:
    def __init__(self, db: Session):
        self.repo = CaseRepository(db)
        self.audit = AuditService(db)

    def create(self, data: CaseCreate, clinician_id: UUID, ip: str | None = None) -> LabCase:
        case_number = self.repo.generate_case_number()

        case = LabCase(
            case_number=case_number,
            patient_id=data.patient_id,
            clinician_id=clinician_id,
            department=data.department,
            test_type=data.test_type,
            priority=data.priority,
            status=CaseStatus.OPEN,
            notes=data.notes,
        )
        created = self.repo.create(case)

        self.audit.log(
            action=AuditAction.CASE_CREATED,
            user_id=clinician_id,
            entity_type="lab_case",
            entity_id=created.id,
            details={"case_number": case_number, "department": data.department.value},
            ip_address=ip,
        )
        return created

    def get(self, case_id: UUID) -> LabCase:
        case = self.repo.get_by_id(case_id)
        if not case:
            raise NotFoundException(detail="Lab case not found.")
        return case

    def update_status(
        self, case_id: UUID, new_status: CaseStatus, user_id: UUID, ip: str | None = None
    ) -> LabCase:
        case = self.get(case_id)
        old_status = case.status.value
        updated = self.repo.update_status(case, new_status)

        self.audit.log(
            action=AuditAction.CASE_STATUS_CHANGED,
            user_id=user_id,
            entity_type="lab_case",
            entity_id=case_id,
            details={"old_status": old_status, "new_status": new_status.value},
            ip_address=ip,
        )
        return updated

    def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status: CaseStatus | None = None,
        department: str | None = None,
    ):
        return self.repo.list_all(skip=skip, limit=limit, status=status, department=department)
