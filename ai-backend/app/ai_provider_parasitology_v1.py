"""
LabMind AI — Parasitology Microscopy AI Provider (V1)
Parasite egg detection pipeline using YOLO-based object detection
on stool microscopy images.

Architecture mirrors the urinalysis pipeline (ai_provider_urine_v1.py):
  • Single YOLOv8n model classifies into 11 parasite egg species
  • No separate CNN classifier needed
  • Clinical interpretation provides species info, disease, and severity

Supported classes (Chula-ParasiteEgg-11 dataset):
  0: Ascaris_lumbricoides      6: Hymenolepis_nana
  1: Capillaria_philippinensis 7: Opisthorchis_viverrine
  2: Enterobius_vermicularis   8: Paragonimus_spp
  3: Fasciolopsis_buski        9: Taenia_spp
  4: Hookworm                 10: Trichuris_trichiura
  5: Hymenolepis_diminuta

This module is a standalone provider — no API routes are defined here.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger("labmind.parasitology_v1")

# ────────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────────

YOLO_MODEL_PATH = (
    r"D:\New folder\ai-backend\dataset_parasites\yolo_dataset"
    r"\parasite_egg_detector\weights\best.pt"
)

# YOLO class indices → canonical label  (must match data.yaml order)
PARASITE_CLASS_MAP: dict[int, str] = {
    0: "Ascaris_lumbricoides",
    1: "Capillaria_philippinensis",
    2: "Enterobius_vermicularis",
    3: "Fasciolopsis_buski",
    4: "Hookworm",
    5: "Hymenolepis_diminuta",
    6: "Hymenolepis_nana",
    7: "Opisthorchis_viverrine",
    8: "Paragonimus_spp",
    9: "Taenia_spp",
    10: "Trichuris_trichiura",
}

# Clinical information per parasite species
PARASITE_CLINICAL_INFO: dict[str, dict[str, str]] = {
    "Ascaris_lumbricoides": {
        "common_name": "Roundworm",
        "disease": "Ascariasis",
        "severity": "moderate",
        "description": "Large oval egg (60x45 um) with thick mammillated shell",
    },
    "Capillaria_philippinensis": {
        "common_name": "Capillaria",
        "disease": "Intestinal Capillariasis",
        "severity": "moderate",
        "description": "Peanut-shaped egg with striated shell and bipolar plugs",
    },
    "Enterobius_vermicularis": {
        "common_name": "Pinworm",
        "disease": "Enterobiasis",
        "severity": "mild",
        "description": "Asymmetric oval egg, one side flattened, thin shell",
    },
    "Fasciolopsis_buski": {
        "common_name": "Giant intestinal fluke",
        "disease": "Fasciolopsiasis",
        "severity": "moderate",
        "description": "Large oval egg (130x80 um) with thin shell and operculum",
    },
    "Hookworm": {
        "common_name": "Hookworm",
        "disease": "Hookworm infection (Ancylostomiasis)",
        "severity": "moderate_to_severe",
        "description": "Oval thin-shelled egg (64x40 um) with clear space between shell and morula",
    },
    "Hymenolepis_diminuta": {
        "common_name": "Rat tapeworm",
        "disease": "Hymenolepiasis",
        "severity": "mild",
        "description": "Round egg (60-80 um) with thick shell, no polar filaments",
    },
    "Hymenolepis_nana": {
        "common_name": "Dwarf tapeworm",
        "disease": "Hymenolepiasis",
        "severity": "mild",
        "description": "Round egg (30-47 um) with thin shell and polar filaments",
    },
    "Opisthorchis_viverrine": {
        "common_name": "Liver fluke",
        "disease": "Opisthorchiasis",
        "severity": "moderate_to_severe",
        "description": "Small oval egg (22-32 um) with operculum and knob at posterior end",
    },
    "Paragonimus_spp": {
        "common_name": "Lung fluke",
        "disease": "Paragonimiasis",
        "severity": "severe",
        "description": "Large oval egg (77-80 um) with thick shell and operculum",
    },
    "Taenia_spp": {
        "common_name": "Tapeworm",
        "disease": "Taeniasis",
        "severity": "moderate",
        "description": "Round egg (30-35 um) with thick radially striated shell",
    },
    "Trichuris_trichiura": {
        "common_name": "Whipworm",
        "disease": "Trichuriasis",
        "severity": "mild_to_moderate",
        "description": "Barrel-shaped egg (50x22 um) with bipolar plugs",
    },
}

# BGR colours for annotated-image drawing — distinct palette for 11 classes
CLASS_COLORS_BGR: dict[str, tuple[int, int, int]] = {
    "Ascaris_lumbricoides":      (0, 0, 255),       # Red
    "Capillaria_philippinensis": (0, 165, 255),      # Orange
    "Enterobius_vermicularis":   (0, 255, 255),      # Yellow
    "Fasciolopsis_buski":        (0, 255, 0),        # Green
    "Hookworm":                  (255, 255, 0),      # Cyan
    "Hymenolepis_diminuta":      (255, 0, 0),        # Blue
    "Hymenolepis_nana":          (255, 0, 128),      # Purple-blue
    "Opisthorchis_viverrine":    (255, 0, 255),      # Magenta
    "Paragonimus_spp":           (128, 0, 255),      # Purple
    "Taenia_spp":                (0, 128, 255),      # Dark orange
    "Trichuris_trichiura":       (128, 255, 0),      # Lime
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
            f"Parasitology YOLO model not found at: {YOLO_MODEL_PATH}"
        )

    try:
        from ultralytics import YOLO
        _yolo_model = YOLO(YOLO_MODEL_PATH)
        logger.info("Loaded parasitology YOLO model from %s", YOLO_MODEL_PATH)
    except Exception as exc:
        logger.error("Failed to load parasitology YOLO model: %s", exc)
        raise RuntimeError(f"Failed to load parasitology YOLO model: {exc}") from exc

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
    logger.info("Parasitology YOLO model hot-reloaded successfully.")


# ────────────────────────────────────────────────────────────────────
# Clinical interpretation helpers
# ────────────────────────────────────────────────────────────────────

def _build_species_info(parasite_counts: dict[str, int]) -> list[dict[str, Any]]:
    """
    Build a list of clinical info dicts for each detected parasite species.

    Parameters
    ----------
    parasite_counts : dict[str, int]
        Mapping of species name → detection count.

    Returns
    -------
    list[dict]
        List of species info entries, sorted by count descending.
    """
    species_info: list[dict[str, Any]] = []

    for species, count in sorted(parasite_counts.items(), key=lambda x: -x[1]):
        if count == 0:
            continue

        clinical = PARASITE_CLINICAL_INFO.get(species, {})
        species_info.append({
            "species": species,
            "common_name": clinical.get("common_name", species),
            "disease": clinical.get("disease", "Unknown"),
            "severity": clinical.get("severity", "unknown"),
            "count": count,
            "description": clinical.get("description", ""),
        })

    return species_info


def _build_overall_assessment(
    parasite_counts: dict[str, int],
    species_detected: list[str],
) -> str:
    """
    Generate a single-line overall assessment string.

    Returns one of:
      • "POSITIVE — Parasitic eggs detected: Hookworm (2), Ascaris_lumbricoides (1)"
      • "NEGATIVE — No parasitic eggs detected in this field"
    """
    if not species_detected:
        return "NEGATIVE — No parasitic eggs detected in this field"

    parts: list[str] = []
    for species in species_detected:
        count = parasite_counts.get(species, 0)
        # Use common name if available for readability
        common = PARASITE_CLINICAL_INFO.get(species, {}).get("common_name", species)
        parts.append(f"{common} ({count})")

    return f"POSITIVE — Parasitic eggs detected: {', '.join(parts)}"


# ────────────────────────────────────────────────────────────────────
# Main analysis pipeline
# ────────────────────────────────────────────────────────────────────

def analyze_parasitology_sample(
    image_path: str,
    *,
    imgsz: int = DEFAULT_IMGSZ,
    conf: float = DEFAULT_CONF,
    iou: float = DEFAULT_IOU,
) -> dict[str, Any]:
    """
    Run the full parasitology analysis pipeline on a single stool
    microscopy image.

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
        Structured result containing detections, parasite counts, species
        info, clinical assessment, and model metadata.
        On error, returns a dict with ``"status": "error"`` and a
        descriptive ``"message"``.

    Examples
    --------
    >>> result = analyze_parasitology_sample(r"D:\\images\\stool_001.jpg")
    >>> result["parasite_counts"]
    {'Hookworm': 2, 'Ascaris_lumbricoides': 1}
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
    parasite_counts: dict[str, int] = {}

    for result in results:
        for box in result.boxes:
            cls_idx = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_name = PARASITE_CLASS_MAP.get(cls_idx, "unknown")

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

            parasite_counts[cls_name] = parasite_counts.get(cls_name, 0) + 1

    total_eggs = sum(parasite_counts.values())
    species_detected = sorted(parasite_counts.keys())

    # ── Clinical interpretation ──
    species_info = _build_species_info(parasite_counts)
    overall = _build_overall_assessment(parasite_counts, species_detected)

    # ── Build result ──
    return {
        "status": "success",
        "image_path": image_path,
        "image_size": [w_img, h_img],
        "detections": detections,
        "parasite_counts": parasite_counts,
        "total_eggs_detected": total_eggs,
        "species_detected": species_detected,
        "species_info": species_info,
        "overall_assessment": overall,
        "model_info": {
            "yolo_version": "yolov8n",
            "confidence_threshold": conf,
            "iou_threshold": iou,
            "imgsz": imgsz,
            "classes": len(PARASITE_CLASS_MAP),
        },
        "timestamp": timestamp,
    }


# ────────────────────────────────────────────────────────────────────
# Annotated image generation
# ────────────────────────────────────────────────────────────────────

def generate_annotated_image(
    image_path: str,
    detections: list[dict[str, Any]] | None = None,
    *,
    imgsz: int = DEFAULT_IMGSZ,
    conf: float = DEFAULT_CONF,
    iou: float = DEFAULT_IOU,
) -> bytes:
    """
    Generate a JPEG-encoded annotated image with color-coded bounding
    boxes for each parasite species.

    If ``detections`` are provided, they are used directly (avoids
    re-running inference).  Otherwise the model is invoked on
    ``image_path`` to obtain them.

    Parameters
    ----------
    image_path : str
        Path to the source microscopy image.
    detections : list[dict] | None
        Pre-computed detections from :func:`analyze_parasitology_sample`.
    imgsz, conf, iou
        Inference parameters (used only when detections are not provided).

    Returns
    -------
    bytes
        JPEG-encoded annotated image.

    Raises
    ------
    ValueError
        If the image cannot be loaded or analysis fails.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    # If detections not supplied, run inference
    if detections is None:
        result = analyze_parasitology_sample(
            image_path, imgsz=imgsz, conf=conf, iou=iou,
        )
        if result.get("status") != "success":
            raise ValueError(result.get("message", "Analysis failed"))
        detections = result["detections"]

    output = img.copy()

    # ── Draw bounding boxes ──
    for det in detections:
        cls_name = det["class"]
        confidence = det["confidence"]
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]

        color = CLASS_COLORS_BGR.get(cls_name, (200, 200, 200))
        # Use common name for display label
        display_name = PARASITE_CLINICAL_INFO.get(cls_name, {}).get(
            "common_name", cls_name,
        )

        # Rectangle
        cv2.rectangle(output, (x1, y1), (x2, y2), color, _BOX_THICKNESS)

        # Label text: species name + confidence
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
