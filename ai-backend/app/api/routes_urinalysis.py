"""
LabMind AI — Urinalysis Microscopy API Routes
Endpoints for urine sediment image analysis using the YOLO-based pipeline.
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai_provider_urine_v1 import (
    CLASS_DISPLAY_NAMES,
    DEFAULT_CONF,
    DEFAULT_IOU,
    DEFAULT_IMGSZ,
    URINE_CLASS_MAP,
    YOLO_MODEL_PATH,
    analyze_urine_sample,
    generate_annotated_image,
    reload_model,
)
from app.api.dependencies import get_current_user, require_role
from app.core.constants import UserRole
from app.core.exceptions import (
    PayloadTooLargeException,
    ServiceUnavailableException,
    ValidationException,
)
from app.db.models.user import User
from app.services.urinalysis_ai_enhancer import generate_full_clinical_report

logger = logging.getLogger("labmind.routes.urinalysis")

router = APIRouter(prefix="/api/urinalysis", tags=["Urinalysis"])

# ── Upload safety constants ──────────────────────────────────────────
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}


# ── Helpers ──────────────────────────────────────────────────────────

def _validate_image_upload(filename: str, content_type: str | None, data: bytes) -> None:
    """
    Validate uploaded image: size, MIME type, and extension.
    Raises the appropriate HTTP exception on failure.
    """
    if len(data) > MAX_UPLOAD_BYTES:
        raise PayloadTooLargeException(
            detail=(
                f"File too large ({len(data) / 1024 / 1024:.1f} MB). "
                f"Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
            )
        )

    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValidationException(
            detail=(
                f"Unsupported file type '{content_type}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            )
        )

    ext = ""
    if filename and "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(
            detail=(
                f"Unsupported file extension '{ext}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
        )


def _save_temp_image(data: bytes, original_filename: str) -> str:
    """
    Save uploaded image bytes to a temp file and return the path.
    The caller is responsible for cleaning up the file after use.
    """
    ext = ".jpg"
    if original_filename and "." in original_filename:
        ext = "." + original_filename.rsplit(".", 1)[-1].lower()

    from app.core.config import get_settings
    settings = get_settings()

    upload_dir = Path(settings.UPLOAD_DIR) / "urinalysis"
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"urine_{uuid.uuid4().hex}{ext}"
    filepath = str(upload_dir / filename)

    with open(filepath, "wb") as f:
        f.write(data)

    return filepath


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("/analyze", status_code=200)
async def analyze_urine(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a urine sediment microscopy image.

    Accepts a single image file (JPG/PNG, max 10 MB) and returns
    structured detection results with clinical interpretation.
    """
    file_data = await file.read()
    filename = file.filename or "upload.jpg"

    _validate_image_upload(filename, file.content_type, file_data)

    # Save to temp location
    image_path = _save_temp_image(file_data, filename)

    try:
        result = analyze_urine_sample(image_path)
    except Exception as exc:
        logger.error("Urine analysis failed: %s", exc, exc_info=True)
        raise ServiceUnavailableException(
            detail=f"Analysis engine error: {exc}"
        )
    finally:
        # Clean up temp file
        try:
            os.remove(image_path)
        except OSError:
            pass

    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Analysis failed."),
        )

    return result


@router.post("/analyze-annotated", status_code=200)
async def analyze_urine_annotated(
    file: UploadFile = File(...),
    confidence: float = Form(None),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a urine sediment image and return results **with** an
    annotated image (bounding boxes + overlay) as a base64-encoded JPEG.

    The response includes all fields from ``/analyze`` plus an
    ``annotated_image_base64`` field.
    """
    file_data = await file.read()
    filename = file.filename or "upload.jpg"

    _validate_image_upload(filename, file.content_type, file_data)

    image_path = _save_temp_image(file_data, filename)

    try:
        # Run analysis
        conf_val = confidence if confidence is not None else DEFAULT_CONF
        result = analyze_urine_sample(image_path, conf=conf_val)

        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Analysis failed."),
            )

        # Generate annotated image using the already-computed detections
        annotated_bytes = generate_annotated_image(
            image_path,
            result["detections"],
            result["cell_counts"],
        )

        result["annotated_image_base64"] = base64.b64encode(annotated_bytes).decode("ascii")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Urine annotated analysis failed: %s", exc, exc_info=True)
        raise ServiceUnavailableException(
            detail=f"Analysis engine error: {exc}"
        )
    finally:
        try:
            os.remove(image_path)
        except OSError:
            pass

    return result


@router.get("/model-info", status_code=200)
def get_model_info(
    current_user: User = Depends(get_current_user),
):
    """
    Return metadata about the loaded urine sediment YOLO model.

    Includes version, supported classes, confidence threshold,
    model file path, and file size on disk.
    """
    model_exists = os.path.isfile(YOLO_MODEL_PATH)
    file_size_mb = None
    if model_exists:
        file_size_mb = round(os.path.getsize(YOLO_MODEL_PATH) / (1024 * 1024), 2)

    return {
        "model_type": "YOLOv8n (Ultralytics)",
        "model_path": YOLO_MODEL_PATH,
        "model_exists": model_exists,
        "file_size_mb": file_size_mb,
        "classes": {str(k): v for k, v in URINE_CLASS_MAP.items()},
        "class_display_names": CLASS_DISPLAY_NAMES,
        "num_classes": len(URINE_CLASS_MAP),
        "default_confidence_threshold": DEFAULT_CONF,
        "default_iou_threshold": DEFAULT_IOU,
        "default_imgsz": DEFAULT_IMGSZ,
    }


@router.post("/reload-model", status_code=200)
def reload_urine_model(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """
    Hot-reload the urine YOLO model weights from disk.

    **Admin only.** Use after updating the model weights file
    (e.g. after retraining) to pick up the new weights without
    restarting the application.
    """
    try:
        reload_model()
    except Exception as exc:
        logger.error("Model reload failed: %s", exc, exc_info=True)
        raise ServiceUnavailableException(
            detail=f"Failed to reload model: {exc}"
        )

    return {"message": "Urine YOLO model reloaded successfully."}


# ── Pydantic models for clinical report ──────────────────────────────

class ClinicalReportRequest(BaseModel):
    """Request body for the clinical report endpoint."""
    cell_counts: dict
    detections: list = []
    patient_context: dict | None = None
    use_ai: bool = True


@router.post("/clinical-report", status_code=200)
async def get_clinical_report(
    request: ClinicalReportRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a full clinical reasoning report from urine sediment
    cell counts.

    Combines a deterministic rule-based analysis (8 clinical scenarios)
    with optional AI-enhanced insights from Gemini 2.0 Flash.

    The rule-based report is always returned.  AI enhancement adds
    pathophysiology, teaching pearls, rare considerations, and
    prioritised next steps.  If the AI call fails, the rule-based
    report is still returned with an ``ai_error`` field.
    """
    try:
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
