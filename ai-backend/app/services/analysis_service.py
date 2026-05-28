"""
LabMind AI — Analysis Service
Orchestrates analysis trigger, status queries, and result retrieval.

Authorization model:
- TRIGGER: Any authenticated user can trigger analysis on a valid case/asset.
- VIEW: Only the user who triggered the run (or admin) can view results.
- DUPLICATE PREVENTION: Only one active run per asset at a time.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import AnalysisStatus, AssetType, AuditAction, UserRole
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException
from app.db.models.analysis_run import AnalysisRun
from app.db.models.user import User
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.case_repository import CaseRepository
from app.services.audit_service import AuditService


SUPPORTED_ASSET_TYPES = {AssetType.BLOOD_SMEAR}


class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalysisRepository(db)
        self.case_repo = CaseRepository(db)
        self.asset_repo = AssetRepository(db)
        self.audit = AuditService(db)

    # ── Ownership helper ──

    @staticmethod
    def _check_run_access(run: AnalysisRun, user: User) -> None:
        """Ensure the user triggered this run, or is an admin."""
        if user.role == UserRole.ADMIN:
            return
        if run.triggered_by != user.id:
            raise ForbiddenException(detail="You can only view your own analysis runs.")

    def trigger(
        self, case_id: UUID, asset_id: UUID, user_id: UUID, ip: str | None = None
    ) -> AnalysisRun:
        """Validate inputs and queue a V34 analysis run."""

        # 1. Validate case exists
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundException(detail="Lab case not found.")

        # 2. Validate asset exists
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundException(detail="Case asset not found.")

        # 3. Validate asset belongs to this case
        if asset.case_id != case_id:
            raise ValidationException(detail="Asset does not belong to the specified case.")

        # 4. Validate asset type is supported
        if asset.asset_type not in SUPPORTED_ASSET_TYPES:
            raise ValidationException(
                detail=f"Asset type '{asset.asset_type.value}' is not supported for V34 analysis. "
                       f"Supported types: {[t.value for t in SUPPORTED_ASSET_TYPES]}"
            )

        # 5. Prevent duplicate analysis on the same asset
        if self.repo.has_active_run(asset_id):
            raise ConflictException(
                detail="An analysis is already queued or running for this asset. "
                       "Wait for it to complete before triggering another."
            )

        # 6. Config snapshot — static data, no model loading needed
        engine_version = "V1"
        config = {
            "engine": engine_version,
            "tile_size": 640,
            "overlap_pct": 0.25,
            "yolo_conf": 0.05,
            "nms_iou": 0.35,
            "min_contour_area": 30,
            "area_filter_low": 0.2,
            "area_filter_high": 3.0,
            "circularity_veto": 0.75,
            "aspect_ratio_min": 1.20,
            "solidity_veto": 0.95,
        }

        # 7. Create run record
        run = AnalysisRun(
            case_id=case_id,
            asset_id=asset_id,
            triggered_by=user_id,
            engine_version=engine_version,
            status=AnalysisStatus.QUEUED,
            config_snapshot=config,
        )
        created = self.repo.create_run(run)

        # 8. Audit
        self.audit.log(
            action=AuditAction.ANALYSIS_QUEUED,
            user_id=user_id,
            entity_type="analysis_run",
            entity_id=created.id,
            details={
                "case_id": str(case_id),
                "asset_id": str(asset_id),
                "engine": engine_version,
            },
            ip_address=ip,
        )

        # 9. Dispatch Celery task
        from app.workers.celery_app import celery_app
        celery_app.send_task("labmind.run_analysis", args=[str(created.id)])

        return created

    def get_run(self, run_id: UUID, user: User) -> AnalysisRun:
        run = self.repo.get_run(run_id)
        if not run:
            raise NotFoundException(detail="Analysis run not found.")
        self._check_run_access(run, user)
        return run

    def get_result(self, run_id: UUID, user: User):
        run = self.repo.get_run(run_id)
        if not run:
            raise NotFoundException(detail="Analysis run not found.")
        self._check_run_access(run, user)
        return self.repo.get_result_by_run(run_id)

    def list_by_case(self, case_id: UUID):
        return self.repo.list_by_case(case_id)
