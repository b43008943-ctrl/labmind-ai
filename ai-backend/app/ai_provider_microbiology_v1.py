"""
LabMind AI — Microbiology (Gram Stain) AI Provider (V1)
Bacteria detection pipeline using YOLO-based object detection
on Gram-stained microscopy images.

Supported classes:
  0: G-_Bacillus   1: G+_Coccus   2: G-_Coccus   3: G+_Bacillus

This module is a standalone provider — no API routes are defined here.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger("labmind.microbiology_v1")

YOLO_MODEL_PATH = (
    r"D:\New folder\ai-backend\dataset_microbiology\yolo_dataset"
    r"\bacteria_detector\weights\best.pt"
)

BACTERIA_CLASS_MAP: dict[int, str] = {
    0: "G-_Bacillus", 1: "G+_Coccus", 2: "G-_Coccus", 3: "G+_Bacillus",
}

BACTERIA_CLINICAL_INFO: dict[str, dict[str, str]] = {
    "G-_Bacillus": {
        "appearance": "Pink/red rod-shaped bacteria",
        "clinical_significance": "Often associated with Enterobacteriaceae (E.coli, Klebsiella, Pseudomonas). Common in UTIs, pneumonia, sepsis",
        "color_on_stain": "Pink/Red",
    },
    "G+_Coccus": {
        "appearance": "Purple/blue spherical bacteria, often in clusters or chains",
        "clinical_significance": "Staphylococcus (clusters), Streptococcus (chains), Enterococcus. Common in skin infections, pneumonia, endocarditis",
        "color_on_stain": "Purple/Blue",
    },
    "G-_Coccus": {
        "appearance": "Pink/red spherical bacteria, often in pairs (diplococci)",
        "clinical_significance": "Neisseria species (N. meningitidis, N. gonorrhoeae). Important in meningitis and STIs",
        "color_on_stain": "Pink/Red",
    },
    "G+_Bacillus": {
        "appearance": "Purple/blue rod-shaped bacteria",
        "clinical_significance": "Bacillus, Clostridium, Corynebacterium, Listeria. Can cause anthrax, tetanus, botulism, food poisoning",
        "color_on_stain": "Purple/Blue",
    },
}

CLASS_COLORS_BGR: dict[str, tuple[int, int, int]] = {
    "G-_Bacillus": (0, 0, 255),    # Red
    "G+_Coccus":   (255, 0, 0),    # Blue
    "G-_Coccus":   (0, 165, 255),  # Orange
    "G+_Bacillus": (128, 0, 128),  # Purple
}

DEFAULT_IMGSZ = 640
DEFAULT_CONF = 0.30
DEFAULT_IOU = 0.45

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE = 0.50
_FONT_THICKNESS = 1
_BOX_THICKNESS = 2

# ────────────────────────────────────────────────────────────────────
# Module-level model cache
# ────────────────────────────────────────────────────────────────────

_yolo_model: Any | None = None


def _get_model() -> Any:
    """Return the cached YOLO model, loading it on first call."""
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model
    if not os.path.isfile(YOLO_MODEL_PATH):
        raise FileNotFoundError(f"Microbiology YOLO model not found at: {YOLO_MODEL_PATH}")
    try:
        from ultralytics import YOLO
        _yolo_model = YOLO(YOLO_MODEL_PATH)
        logger.info("Loaded microbiology YOLO model from %s", YOLO_MODEL_PATH)
    except Exception as exc:
        logger.error("Failed to load microbiology YOLO model: %s", exc)
        raise RuntimeError(f"Failed to load microbiology YOLO model: {exc}") from exc
    return _yolo_model


def reload_model() -> None:
    """Force-reload the YOLO model from disk."""
    global _yolo_model
    _yolo_model = None
    _get_model()
    logger.info("Microbiology YOLO model hot-reloaded successfully.")


# ────────────────────────────────────────────────────────────────────
# Clinical interpretation helpers
# ────────────────────────────────────────────────────────────────────

def _build_bacteria_info(bacteria_counts: dict[str, int]) -> list[dict[str, Any]]:
    """Build clinical info list for each detected bacterial type, sorted by count desc."""
    info: list[dict[str, Any]] = []
    for species, count in sorted(bacteria_counts.items(), key=lambda x: -x[1]):
        if count == 0:
            continue
        clinical = BACTERIA_CLINICAL_INFO.get(species, {})
        info.append({
            "species": species,
            "appearance": clinical.get("appearance", species),
            "clinical_significance": clinical.get("clinical_significance", "Unknown"),
            "color_on_stain": clinical.get("color_on_stain", "Unknown"),
            "count": count,
        })
    return info


def _build_gram_summary(bacteria_counts: dict[str, int]) -> dict[str, int]:
    """Build Gram-positive/negative and cocci/bacilli summary."""
    gp, gn, cocci, bacilli = 0, 0, 0, 0
    for species, count in bacteria_counts.items():
        if species.startswith("G+"):
            gp += count
        elif species.startswith("G-"):
            gn += count
        if "Coccus" in species:
            cocci += count
        elif "Bacillus" in species:
            bacilli += count
    return {"gram_positive": gp, "gram_negative": gn, "cocci": cocci, "bacilli": bacilli}


def _build_overall_assessment(bacteria_counts: dict[str, int], species_detected: list[str]) -> str:
    """Generate single-line assessment string."""
    if not species_detected:
        return "NO BACTERIA DETECTED"
    _FRIENDLY = {
        "G-_Bacillus": "Gram-negative bacilli", "G+_Coccus": "Gram-positive cocci",
        "G-_Coccus": "Gram-negative cocci", "G+_Bacillus": "Gram-positive bacilli",
    }
    parts = [f"{_FRIENDLY.get(sp, sp)} ({bacteria_counts.get(sp, 0)})" for sp in species_detected]
    return f"BACTERIA DETECTED — {', '.join(parts)}"


# ────────────────────────────────────────────────────────────────────
# Main analysis pipeline
# ────────────────────────────────────────────────────────────────────

def analyze_microbiology_sample(
    image_path: str, *, imgsz: int = DEFAULT_IMGSZ,
    conf: float = DEFAULT_CONF, iou: float = DEFAULT_IOU,
) -> dict[str, Any]:
    """Run the full microbiology analysis pipeline on a Gram-stained image."""
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        model = _get_model()
    except (FileNotFoundError, RuntimeError) as exc:
        logger.error("Model load failed: %s", exc)
        return {"status": "error", "message": str(exc), "timestamp": timestamp}

    if not os.path.isfile(image_path):
        return {"status": "error", "message": f"Image file not found: {image_path}", "timestamp": timestamp}

    img = cv2.imread(image_path)
    if img is None:
        return {"status": "error", "message": f"Failed to read image: {image_path}", "timestamp": timestamp}

    h_img, w_img = img.shape[:2]

    try:
        results = model.predict(source=image_path, imgsz=imgsz, conf=conf, iou=iou, verbose=False)
    except Exception as exc:
        logger.error("YOLO inference failed: %s", exc)
        return {"status": "error", "message": f"YOLO inference error: {exc}", "timestamp": timestamp}

    detections: list[dict[str, Any]] = []
    bacteria_counts: dict[str, int] = {}

    for result in results:
        for box in result.boxes:
            cls_idx = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_name = BACTERIA_CLASS_MAP.get(cls_idx, "unknown")
            detections.append({
                "class": cls_name, "confidence": round(confidence, 4),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            })
            bacteria_counts[cls_name] = bacteria_counts.get(cls_name, 0) + 1

    total_bacteria = sum(bacteria_counts.values())
    species_detected = sorted(bacteria_counts.keys())

    return {
        "status": "success", "image_path": image_path, "image_size": [w_img, h_img],
        "detections": detections, "bacteria_counts": bacteria_counts,
        "total_bacteria_detected": total_bacteria,
        "gram_summary": _build_gram_summary(bacteria_counts),
        "species_detected": species_detected,
        "bacteria_info": _build_bacteria_info(bacteria_counts),
        "overall_assessment": _build_overall_assessment(bacteria_counts, species_detected),
        "model_info": {
            "yolo_version": "yolov8n", "confidence_threshold": conf,
            "iou_threshold": iou, "imgsz": imgsz, "classes": len(BACTERIA_CLASS_MAP),
        },
        "timestamp": timestamp,
    }


# ────────────────────────────────────────────────────────────────────
# Annotated image generation
# ────────────────────────────────────────────────────────────────────

def generate_annotated_image(
    image_path: str, detections: list[dict[str, Any]] | None = None,
    *, imgsz: int = DEFAULT_IMGSZ, conf: float = DEFAULT_CONF, iou: float = DEFAULT_IOU,
) -> bytes:
    """Generate JPEG-encoded annotated image with color-coded bounding boxes."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    if detections is None:
        result = analyze_microbiology_sample(image_path, imgsz=imgsz, conf=conf, iou=iou)
        if result.get("status") != "success":
            raise ValueError(result.get("message", "Analysis failed"))
        detections = result["detections"]

    output = img.copy()

    for det in detections:
        cls_name = det["class"]
        confidence = det["confidence"]
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        color = CLASS_COLORS_BGR.get(cls_name, (200, 200, 200))
        display_name = cls_name.replace("_", " ")

        cv2.rectangle(output, (x1, y1), (x2, y2), color, _BOX_THICKNESS)
        label_text = f"{display_name} {confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label_text, _FONT, _FONT_SCALE, _FONT_THICKNESS)
        cv2.rectangle(output, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
        cv2.putText(output, label_text, (x1 + 3, y1 - 4), _FONT, _FONT_SCALE, (255, 255, 255), _FONT_THICKNESS)

    success, buf = cv2.imencode(".jpg", output, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not success:
        raise RuntimeError("Failed to encode annotated image to JPEG")
    return bytes(buf)
