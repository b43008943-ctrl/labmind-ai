"""
LabMind AI — Microbiology (Gram Stain) API Routes
Endpoints for Gram stain bacteria detection using the YOLO-based pipeline.
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.ai_provider_microbiology_v1 import (
    DEFAULT_CONF,
    DEFAULT_IOU,
    DEFAULT_IMGSZ,
    BACTERIA_CLASS_MAP,
    BACTERIA_CLINICAL_INFO,
    YOLO_MODEL_PATH,
    analyze_microbiology_sample,
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

logger = logging.getLogger("labmind.routes.microbiology")

router = APIRouter(prefix="/api/microbiology", tags=["Microbiology"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}


def _validate_image_upload(filename: str, content_type: str | None, data: bytes) -> None:
    """Validate uploaded image: size, MIME type, and extension."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise PayloadTooLargeException(
            detail=f"File too large ({len(data) / 1024 / 1024:.1f} MB). Maximum is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
        )
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValidationException(detail=f"Unsupported file type '{content_type}'. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}")
    ext = ""
    if filename and "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(detail=f"Unsupported extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")


def _save_temp_image(data: bytes, original_filename: str) -> str:
    """Save uploaded image bytes to a temp file and return the path."""
    ext = ".jpg"
    if original_filename and "." in original_filename:
        ext = "." + original_filename.rsplit(".", 1)[-1].lower()
    from app.core.config import get_settings
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR) / "microbiology"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"microbiology_{uuid.uuid4().hex}{ext}"
    filepath = str(upload_dir / filename)
    with open(filepath, "wb") as f:
        f.write(data)
    return filepath


@router.post("/analyze", status_code=200)
async def analyze_microbiology(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Analyze a Gram-stained microscopy image for bacteria."""
    file_data = await file.read()
    filename = file.filename or "upload.jpg"
    _validate_image_upload(filename, file.content_type, file_data)
    image_path = _save_temp_image(file_data, filename)

    try:
        result = analyze_microbiology_sample(image_path)
    except Exception as exc:
        logger.error("Microbiology analysis failed: %s", exc, exc_info=True)
        raise ServiceUnavailableException(detail=f"Analysis engine error: {exc}")
    finally:
        try:
            os.remove(image_path)
        except OSError:
            pass

    if result.get("status") == "error":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Analysis failed."))
    return result


@router.post("/analyze-annotated", status_code=200)
async def analyze_microbiology_annotated(
    file: UploadFile = File(...),
    confidence: float = Form(None),
    current_user: User = Depends(get_current_user),
):
    """Analyze a Gram-stained image and return results with annotated image."""
    file_data = await file.read()
    filename = file.filename or "upload.jpg"
    _validate_image_upload(filename, file.content_type, file_data)
    image_path = _save_temp_image(file_data, filename)

    try:
        conf_val = confidence if confidence is not None else DEFAULT_CONF
        result = analyze_microbiology_sample(image_path, conf=conf_val)
        if result.get("status") == "error":
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Analysis failed."))
        annotated_bytes = generate_annotated_image(image_path, result["detections"])
        result["annotated_image_base64"] = base64.b64encode(annotated_bytes).decode("ascii")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Microbiology annotated analysis failed: %s", exc, exc_info=True)
        raise ServiceUnavailableException(detail=f"Analysis engine error: {exc}")
    finally:
        try:
            os.remove(image_path)
        except OSError:
            pass
    return result


@router.get("/model-info", status_code=200)
def get_model_info(current_user: User = Depends(get_current_user)):
    """Return metadata about the loaded microbiology YOLO model."""
    model_exists = os.path.isfile(YOLO_MODEL_PATH)
    file_size_mb = None
    if model_exists:
        file_size_mb = round(os.path.getsize(YOLO_MODEL_PATH) / (1024 * 1024), 2)

    return {
        "model_type": "YOLOv8n (Ultralytics)",
        "model_path": YOLO_MODEL_PATH,
        "model_exists": model_exists,
        "file_size_mb": file_size_mb,
        "classes": {str(k): v for k, v in BACTERIA_CLASS_MAP.items()},
        "class_clinical_info": {
            name: {"appearance": info["appearance"], "clinical_significance": info["clinical_significance"], "color_on_stain": info["color_on_stain"]}
            for name, info in BACTERIA_CLINICAL_INFO.items()
        },
        "num_classes": len(BACTERIA_CLASS_MAP),
        "default_confidence_threshold": DEFAULT_CONF,
        "default_iou_threshold": DEFAULT_IOU,
        "default_imgsz": DEFAULT_IMGSZ,
    }


@router.post("/reload-model", status_code=200)
def reload_microbiology_model(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Hot-reload the microbiology YOLO model weights. Admin only."""
    try:
        reload_model()
    except Exception as exc:
        logger.error("Model reload failed: %s", exc, exc_info=True)
        raise ServiceUnavailableException(detail=f"Failed to reload model: {exc}")
    return {"message": "Microbiology YOLO model reloaded successfully."}


class MicrobiologyClinicalReportRequest(BaseModel):
    """Request body for the clinical report endpoint."""
    bacteria_counts: dict = {}
    bacteria_info: list = []
    patient_context: dict | None = None
    use_ai: bool = True


@router.post("/clinical-report", status_code=200)
async def get_clinical_report(
    request: MicrobiologyClinicalReportRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a clinical reasoning report from Gram stain detection results."""
    try:
        from app.services.microbiology_ai_enhancer import generate_full_clinical_report
        report = await generate_full_clinical_report(
            bacteria_counts=request.bacteria_counts,
            bacteria_info=request.bacteria_info or None,
            patient_context=request.patient_context,
            use_ai=request.use_ai,
        )
        return report
    except Exception as exc:
        logger.error("Clinical report generation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report generation failed: {exc}")
