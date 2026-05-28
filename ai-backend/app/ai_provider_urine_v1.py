"""
LabMind AI — Urinalysis Microscopy AI Provider (V1)
Urine sediment analysis pipeline using YOLO-based cell detection.

Unlike the hematology pipeline (ai_provider_v1.py) which uses YOLO + CNN
in a multi-stage pipeline, the urine pipeline is simpler:
  • Single YOLO model directly classifies into 3 classes: RBC, Pus/WBC, Epithelial
  • No separate CNN classifier needed
  • Clinical interpretation is based on cell counts per high-power field (HPF)

This module is a standalone provider — no API routes are defined here.
"""

from __future__ import annotations

import io
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger("labmind.urine_v1")

# ────────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────────

YOLO_MODEL_PATH = (
    r"D:\New folder\ai-backend\dataset_urine\yolo_dataset"
    r"\urine_cell_detector\weights\best.pt"
)

# YOLO class indices → canonical label  (must match data.yaml order)
URINE_CLASS_MAP: dict[int, str] = {0: "rbc", 1: "pus", 2: "ep"}

# Display-friendly names
CLASS_DISPLAY_NAMES: dict[str, str] = {
    "rbc": "RBC",
    "pus": "Pus/WBC",
    "ep":  "Epithelial",
}

# BGR colours for annotated-image drawing
CLASS_COLORS_BGR: dict[str, tuple[int, int, int]] = {
    "rbc": (0, 0, 255),       # Red   (#FF0000)
    "pus": (0, 255, 0),       # Green (#00FF00)
    "ep":  (255, 0, 0),       # Blue  (#0000FF)
}

# Inference defaults
DEFAULT_IMGSZ = 640
DEFAULT_CONF = 0.30
DEFAULT_IOU = 0.45

# Font settings for annotation overlays
_FONT = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE = 0.50
_FONT_THICKNESS = 1
_BOX_THICKNESS = 2


# ────────────────────────────────────────────────────────────────────
# Module-level model cache
# ────────────────────────────────────────────────────────────────────

_yolo_model: Any | None = None


def _get_model() -> Any:
    """
    Return the cached YOLO model, loading it on first call.

    Raises
    ------
    FileNotFoundError
        If the model weights file does not exist on disk.
    RuntimeError
        If the YOLO model fails to load for any reason.
    """
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model

    if not os.path.isfile(YOLO_MODEL_PATH):
        raise FileNotFoundError(
            f"Urine YOLO model not found at: {YOLO_MODEL_PATH}"
        )

    try:
        from ultralytics import YOLO
        _yolo_model = YOLO(YOLO_MODEL_PATH)
        logger.info("Loaded urine YOLO model from %s", YOLO_MODEL_PATH)
    except Exception as exc:
        logger.error("Failed to load urine YOLO model: %s", exc)
        raise RuntimeError(f"Failed to load urine YOLO model: {exc}") from exc

    return _yolo_model


def reload_model() -> None:
    """
    Force-reload the YOLO model from disk.

    Useful for hot-reloading after the weights file has been updated
    (e.g. after retraining) without restarting the application.
    """
    global _yolo_model
    _yolo_model = None
    _get_model()
    logger.info("Urine YOLO model hot-reloaded successfully.")


# ────────────────────────────────────────────────────────────────────
# Clinical interpretation helpers
# ────────────────────────────────────────────────────────────────────

def _interpret_rbc(count: int) -> dict[str, str]:
    """
    Interpret RBC count per high-power field.

    Clinical reference ranges (per HPF):
      • Normal:  0-2
      • Mild:    3-5  → mild hematuria
      • High:    >5   → significant hematuria
    """
    if count <= 2:
        return {
            "count": count,
            "status": "normal",
            "message": f"Normal (0-2 RBCs/HPF) — {count} detected",
        }
    elif count <= 5:
        return {
            "count": count,
            "status": "abnormal",
            "message": f"Mild hematuria (3-5 RBCs/HPF) — {count} detected",
        }
    else:
        return {
            "count": count,
            "status": "abnormal",
            "message": (
                f"Significant hematuria (>5 RBCs/HPF) — {count} detected"
                " - requires clinical correlation"
            ),
        }


def _interpret_pus(count: int) -> dict[str, str]:
    """
    Interpret WBC / Pus cell count per high-power field.

    Clinical reference ranges (per HPF):
      • Normal:  0-5
      • Mild:    6-10  → mild pyuria
      • High:    >10   → significant pyuria, suggests infection
    """
    if count <= 5:
        return {
            "count": count,
            "status": "normal",
            "message": f"Normal (0-5 WBCs/HPF) — {count} detected",
        }
    elif count <= 10:
        return {
            "count": count,
            "status": "abnormal",
            "message": f"Mild pyuria (6-10 WBCs/HPF) — {count} detected",
        }
    else:
        return {
            "count": count,
            "status": "abnormal",
            "message": (
                f"Significant pyuria (>10 WBCs/HPF) — {count} detected"
                " - suggests infection"
            ),
        }


def _interpret_ep(count: int) -> dict[str, str]:
    """
    Interpret epithelial cell count.

    Clinical reference ranges:
      • Few:      0-5   → adequate sample
      • Moderate: 6-15  → note
      • Many:     >15   → possible contamination
    """
    if count <= 5:
        return {
            "count": count,
            "status": "normal",
            "message": f"Few epithelial cells - adequate sample — {count} detected",
        }
    elif count <= 15:
        return {
            "count": count,
            "status": "note",
            "message": f"Moderate epithelial cells — {count} detected",
        }
    else:
        return {
            "count": count,
            "status": "abnormal",
            "message": (
                f"Many epithelial cells — {count} detected"
                " - possible contamination, consider recollection"
            ),
        }


_INTERPRETERS: dict[str, callable] = {
    "rbc": _interpret_rbc,
    "pus": _interpret_pus,
    "ep":  _interpret_ep,
}


def _build_overall_assessment(interpretation: dict[str, dict]) -> str:
    """
    Generate a single-line overall assessment string from per-class
    interpretation results.

    Returns one of:
      • "NORMAL - No significant findings"
      • "ABNORMAL - <details>"
      • "No significant findings - No cells detected"
    """
    abnormal_findings: list[str] = []

    for cls_name in ("rbc", "pus", "ep"):
        info = interpretation.get(cls_name, {})
        if info.get("status") == "abnormal":
            # Extract the short clinical phrase from the message
            msg = info.get("message", "")
            # Use the portion before the dash-separated detail
            short = msg.split("—")[0].strip() if "—" in msg else msg
            abnormal_findings.append(short)

    if not interpretation or all(
        v.get("count", 0) == 0 for v in interpretation.values()
    ):
        return "No significant findings - No cells detected"

    if abnormal_findings:
        return "ABNORMAL - " + "; ".join(abnormal_findings)

    return "NORMAL - No significant findings"


# ────────────────────────────────────────────────────────────────────
# Main analysis pipeline
# ────────────────────────────────────────────────────────────────────

def analyze_urine_sample(
    image_path: str,
    *,
    imgsz: int = DEFAULT_IMGSZ,
    conf: float = DEFAULT_CONF,
    iou: float = DEFAULT_IOU,
) -> dict[str, Any]:
    """
    Run the full urine sediment analysis pipeline on a single image.

    Parameters
    ----------
    image_path : str
        Absolute path to a microscopy image (JPG / PNG, any resolution).
    imgsz : int
        YOLO inference image size (default 640).
    conf : float
        Confidence threshold for detections (default 0.30).
    iou : float
        IoU threshold for NMS (default 0.45).

    Returns
    -------
    dict
        Structured result containing detections, cell counts, clinical
        interpretation, overall assessment, and model metadata.
        On error, returns a dict with ``"status": "error"`` and a
        descriptive ``"message"``.

    Examples
    --------
    >>> result = analyze_urine_sample(r"D:\\images\\sample_001.jpg")
    >>> result["cell_counts"]
    {'rbc': 5, 'pus': 12, 'ep': 2}
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # ── Guard: model availability ──
    try:
        model = _get_model()
    except (FileNotFoundError, RuntimeError) as exc:
        logger.error("Model load failed: %s", exc)
        return {
            "status": "error",
            "message": str(exc),
            "timestamp": timestamp,
        }

    # ── Guard: image loading ──
    if not os.path.isfile(image_path):
        return {
            "status": "error",
            "message": f"Image file not found: {image_path}",
            "timestamp": timestamp,
        }

    img = cv2.imread(image_path)
    if img is None:
        return {
            "status": "error",
            "message": f"Failed to read image (corrupt or unsupported format): {image_path}",
            "timestamp": timestamp,
        }

    h_img, w_img = img.shape[:2]

    # ── YOLO inference ──
    try:
        results = model.predict(
            source=image_path,
            imgsz=imgsz,
            conf=conf,
            iou=iou,
            verbose=False,
        )
    except Exception as exc:
        logger.error("YOLO inference failed: %s", exc)
        return {
            "status": "error",
            "message": f"YOLO inference error: {exc}",
            "timestamp": timestamp,
        }

    # ── Parse detections ──
    detections: list[dict[str, Any]] = []
    cell_counts: dict[str, int] = {"rbc": 0, "pus": 0, "ep": 0}

    for result in results:
        for box in result.boxes:
            cls_idx = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_name = URINE_CLASS_MAP.get(cls_idx, "unknown")

            detections.append({
                "class": cls_name,
                "confidence": round(confidence, 4),
                "bbox": [
                    round(x1, 1),
                    round(y1, 1),
                    round(x2, 1),
                    round(y2, 1),
                ],
            })

            if cls_name in cell_counts:
                cell_counts[cls_name] += 1

    total_cells = sum(cell_counts.values())

    # ── Clinical interpretation ──
    interpretation: dict[str, dict] = {}
    for cls_name, interpreter_fn in _INTERPRETERS.items():
        interpretation[cls_name] = interpreter_fn(cell_counts[cls_name])

    overall = _build_overall_assessment(interpretation)

    # ── Build result ──
    return {
        "status": "success",
        "image_path": image_path,
        "image_size": [w_img, h_img],
        "detections": detections,
        "cell_counts": cell_counts,
        "total_cells": total_cells,
        "interpretation": interpretation,
        "overall_assessment": overall,
        "model_info": {
            "yolo_version": "yolov8n",
            "confidence_threshold": conf,
            "iou_threshold": iou,
            "imgsz": imgsz,
        },
        "timestamp": timestamp,
    }


# ────────────────────────────────────────────────────────────────────
# Annotated image generation
# ────────────────────────────────────────────────────────────────────

def generate_annotated_image(
    image_path: str,
    detections: list[dict[str, Any]] | None = None,
    cell_counts: dict[str, int] | None = None,
    *,
    imgsz: int = DEFAULT_IMGSZ,
    conf: float = DEFAULT_CONF,
    iou: float = DEFAULT_IOU,
) -> bytes:
    """
    Generate a JPEG-encoded annotated image with bounding boxes and an
    overlay summary.

    If ``detections`` and ``cell_counts`` are provided, they are used
    directly (avoids re-running inference).  Otherwise the model is
    invoked on ``image_path`` to obtain them.

    Parameters
    ----------
    image_path : str
        Path to the source microscopy image.
    detections : list[dict] | None
        Pre-computed detections from :func:`analyze_urine_sample`.
    cell_counts : dict[str, int] | None
        Pre-computed cell counts.
    imgsz, conf, iou
        Inference parameters (used only when detections are not provided).

    Returns
    -------
    bytes
        JPEG-encoded annotated image.

    Raises
    ------
    ValueError
        If the image cannot be loaded.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    # If detections not supplied, run inference
    if detections is None or cell_counts is None:
        result = analyze_urine_sample(
            image_path, imgsz=imgsz, conf=conf, iou=iou,
        )
        if result.get("status") != "success":
            raise ValueError(result.get("message", "Analysis failed"))
        detections = result["detections"]
        cell_counts = result["cell_counts"]

    output = img.copy()

    # ── Draw bounding boxes ──
    for det in detections:
        cls_name = det["class"]
        confidence = det["confidence"]
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]

        color = CLASS_COLORS_BGR.get(cls_name, (200, 200, 200))
        display_name = CLASS_DISPLAY_NAMES.get(cls_name, cls_name.upper())

        # Rectangle
        cv2.rectangle(output, (x1, y1), (x2, y2), color, _BOX_THICKNESS)

        # Label text
        label_text = f"{display_name} {confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label_text, _FONT, _FONT_SCALE, _FONT_THICKNESS)

        # Label background
        cv2.rectangle(
            output,
            (x1, y1 - th - 8),
            (x1 + tw + 6, y1),
            color,
            -1,
        )
        cv2.putText(
            output,
            label_text,
            (x1 + 3, y1 - 4),
            _FONT,
            _FONT_SCALE,
            (255, 255, 255),
            _FONT_THICKNESS,
        )


    # ── Encode to JPEG bytes ──
    success, buf = cv2.imencode(".jpg", output, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not success:
        raise RuntimeError("Failed to encode annotated image to JPEG")

    return bytes(buf)
