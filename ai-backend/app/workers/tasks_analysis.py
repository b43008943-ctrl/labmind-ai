"""
LabMind AI — Analysis Worker Tasks
Background execution of the V1 Rebuild diagnostic engine via Celery.
"""

import os
import tempfile
import time
import traceback

from app.core.constants import AnalysisStatus, AuditAction
from app.db.database import SessionLocal

# Import ALL models so SQLAlchemy's mapper registry has foreign key
# targets (e.g., 'users', 'patients', 'lab_cases') resolved before
# any ORM flush / commit operations.
import app.db.models.user           # noqa: F401
import app.db.models.patient        # noqa: F401
import app.db.models.lab_case       # noqa: F401
import app.db.models.case_asset     # noqa: F401
import app.db.models.analysis_run   # noqa: F401
import app.db.models.analysis_result  # noqa: F401
from app.db.models.analysis_result import AnalysisResult
import app.db.models.audit_log      # noqa: F401

from app.workers.celery_app import celery_app


@celery_app.task(name="labmind.run_analysis", bind=True, max_retries=0)
def run_analysis_task(self, run_id: str):
    """
    Execute V34 blood smear analysis in the background.
    Steps:
    1. Download the asset image to a temp path
    2. Run V34 provider
    3. Persist results in DB
    4. Update run status and audit log
    """
    db = SessionLocal()
    tmp_path = None  # Track for cleanup on failure
    try:
        from app.providers.ai_provider_v1 import V1Provider
        from app.providers.storage_provider_local import LocalStorageProvider
        from app.repositories.analysis_repository import AnalysisRepository
        from app.repositories.asset_repository import AssetRepository
        from app.services.audit_service import AuditService

        repo = AnalysisRepository(db)
        audit = AuditService(db)
        storage = LocalStorageProvider()

        # 1. Load the run
        run = repo.get_run(run_id)
        if not run:
            return {"error": "Run not found"}

        # 2. Mark as running
        repo.update_status(run, AnalysisStatus.RUNNING)
        audit.log(
            action=AuditAction.ANALYSIS_STARTED,
            user_id=run.triggered_by,
            entity_type="analysis_run",
            entity_id=run.id,
            ip_address=None,
        )

        # 3. Get the image from storage
        asset_repo = AssetRepository(db)
        asset = asset_repo.get_by_id(run.asset_id)
        if not asset:
            raise ValueError("Asset not found in database")

        image_data = storage.download(asset.storage_key)

        # Write to temp file for OpenCV
        ext = asset.original_filename.rsplit(".", 1)[-1] if "." in asset.original_filename else "jpg"
        fd, tmp_path = tempfile.mkstemp(suffix=f".{ext}")
        os.write(fd, image_data)
        os.close(fd)

        # 4. Run V1 engine
        start_ms = time.monotonic_ns()
        provider = V1Provider()
        ai_result = provider.analyze(tmp_path)
        duration_ms = int((time.monotonic_ns() - start_ms) / 1_000_000)

        # Clean up temp file
        os.unlink(tmp_path)
        tmp_path = None

        # 5. Persist result
        result = AnalysisResult(
            run_id=run.id,
            total_cells=ai_result["total_cells"],
            sickle_count=ai_result["sickle_count"],
            normal_count=ai_result["normal_count"],
            sickle_percentage=ai_result["sickle_percentage"],
            cell_details={"detections": ai_result["cell_details"]} if isinstance(ai_result["cell_details"], list) else ai_result["cell_details"],
            annotated_image_key=ai_result.get("annotated_image_path"),
            quality_score=ai_result.get("quality_score"),
            quality_status=ai_result.get("quality_status"),
            rejection_reason=ai_result.get("rejection_reason"),
        )
        repo.create_result(result)

        # 6. Mark as completed
        repo.update_status(run, AnalysisStatus.COMPLETED, duration_ms=duration_ms)
        audit.log(
            action=AuditAction.ANALYSIS_COMPLETED,
            user_id=run.triggered_by,
            entity_type="analysis_run",
            entity_id=run.id,
            details={
                "duration_ms": duration_ms,
                "total_cells": ai_result["total_cells"],
                "sickle_count": ai_result["sickle_count"],
            },
            ip_address=None,
        )

        return {
            "run_id": str(run.id),
            "status": "completed",
            "total_cells": ai_result["total_cells"],
            "duration_ms": duration_ms,
        }

    except Exception as e:
        # Mark as failed — use a FRESH session to avoid broken transaction state
        err_db = SessionLocal()
        try:
            from app.repositories.analysis_repository import AnalysisRepository
            from app.services.audit_service import AuditService

            err_repo = AnalysisRepository(err_db)
            err_audit = AuditService(err_db)
            run = err_repo.get_run(run_id)
            if run:
                err_repo.update_status(
                    run,
                    AnalysisStatus.FAILED,
                    error_message=str(e)[:2000],
                )
                err_audit.log(
                    action=AuditAction.ANALYSIS_FAILED,
                    user_id=run.triggered_by,
                    entity_type="analysis_run",
                    entity_id=run.id,
                    details={"error": str(e)[:500], "traceback": traceback.format_exc()[:2000]},
                    ip_address=None,
                )
        except Exception:
            pass
        finally:
            err_db.close()

        return {"run_id": run_id, "status": "failed", "error": str(e)}

    finally:
        # Always clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        db.close()
