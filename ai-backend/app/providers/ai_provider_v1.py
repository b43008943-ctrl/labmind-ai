"""
LabMind AI — V1 Rebuild Diagnostic Engine Provider
Clean rebuild of the hematology analysis pipeline.

Phase 1: Quality gate + existing detection/classification logic.
Phase 2: Class-aware YOLO detection (rbc/wbc/plt/sickle), class-aware NMS & dedup.
Phase 3: 4-class CNN as primary RBC label authority; morphology features for audit only.

This runs synchronously and is intended to be called from a Celery worker only.
"""

import logging
import os
import uuid
import warnings
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision
from torchvision import transforms

from app.core.config import get_settings
from app.providers.ai_provider import AIProvider

warnings.filterwarnings("ignore")
logger = logging.getLogger("labmind.v1provider")

# ── YOLO class map for blood_ai_v2.pt ──
YOLO_CLASS_MAP = {0: "plt", 1: "rbc", 2: "wbc", 3: "sickle"}

# ── RBC CNN class map (Phase 3: 4-class target) ──
# When 4-class weights are loaded:
RBC_CLASS_MAP_4 = {0: "normal", 1: "sickle", 2: "target", 3: "other_abnormal"}
# When falling back to 2-class weights (cell_classifier_v3.pth):
RBC_CLASS_MAP_2 = {0: "normal", 1: "sickle"}

# Box color per class for annotated image (BGR)
CLASS_COLORS = {
    "rbc": (0, 255, 0),        # green — normal rbc
    "normal": (0, 255, 0),     # green
    "wbc": (255, 180, 0),      # cyan-ish
    "plt": (255, 0, 255),      # magenta
    "sickle": (0, 0, 255),     # red
    "target": (0, 165, 255),   # orange
    "other_abnormal": (0, 255, 255),  # yellow
}


# ── CNN Architecture (same structure, parameterized num_classes) ──
class CellClassifierCNN(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2, 2),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.5), nn.Linear(128 * 8 * 8, 256), nn.ReLU(), nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


class V1Provider(AIProvider):
    """
    Hematology Rebuild V1 — Clean diagnostic pipeline.

    Pipeline stages:
      1. Quality Gate (blur, saturation, brightness)
      2. YOLO Tiling — class-aware (rbc/wbc/plt/sickle)
      3. Class-aware Global NMS (batched_nms by class)
      4. Watershed De-clustering (rbc/sickle only)
      5. Contour Refinement + Cropping (rbc/sickle only)
      6. CNN Classification — PRIMARY LABEL AUTHORITY for RBC morphology
      7. Class-aware Spatial Deduplication
      8. Annotated Image + Structured Report
    """

    _yolo_model = None
    _cnn_model = None
    _cnn_num_classes = None  # 2 or 4 depending on loaded weights
    _cnn_class_map = None    # RBC_CLASS_MAP_2 or RBC_CLASS_MAP_4
    _classifier_mode = None  # 4class / trained_2class / legacy_2class / disabled
    _device = None
    _transform = None

    def __init__(self):
        if V1Provider._device is None:
            self._load_models()

    @classmethod
    def _load_models(cls):
        settings = get_settings()
        cls._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # ── YOLO ──
        from ultralytics import YOLO
        cls._yolo_model = YOLO(settings.YOLO_MODEL_PATH)

        # ── CNN: Priority order ──
        # 1. cell_classifier_v1_rebuild.pth  → 4-class  (Phase 3 full)
        # 2. cell_classifier_2class.pth      → trained 2-class (Phase 3.5)
        # 3. cell_classifier_v3.pth          → legacy 2-class fallback
        # 4. None                            → disabled
        cnn_v1_path = settings.CNN_V1_MODEL_PATH
        cnn_2class_path = settings.CNN_2CLASS_MODEL_PATH

        if os.path.exists(cnn_v1_path):
            # Priority 1: Full 4-class weights
            cls._cnn_num_classes = 4
            cls._cnn_class_map = RBC_CLASS_MAP_4
            cls._cnn_model = CellClassifierCNN(num_classes=4).to(cls._device)
            cls._cnn_model.load_state_dict(
                torch.load(cnn_v1_path, map_location=cls._device, weights_only=True)
            )
            cls._classifier_mode = "4class"
            logger.info("Loaded 4-class CNN weights from %s", cnn_v1_path)
        elif os.path.exists(cnn_2class_path):
            # Priority 2: Trained 2-class weights (Phase 3.5)
            cls._cnn_num_classes = 2
            cls._cnn_class_map = RBC_CLASS_MAP_2
            cls._cnn_model = CellClassifierCNN(num_classes=2).to(cls._device)
            cls._cnn_model.load_state_dict(
                torch.load(cnn_2class_path, map_location=cls._device, weights_only=True)
            )
            cls._classifier_mode = "trained_2class"
            logger.info(
                "Loaded trained 2-class CNN weights from %s (normal/sickle). "
                "Upgrade to 4-class by training with target + other_abnormal data.",
                cnn_2class_path,
            )
        elif os.path.exists(settings.CNN_MODEL_PATH):
            # Priority 3: Legacy 2-class fallback
            cls._cnn_num_classes = 2
            cls._cnn_class_map = RBC_CLASS_MAP_2
            cls._cnn_model = CellClassifierCNN(num_classes=2).to(cls._device)
            cls._cnn_model.load_state_dict(
                torch.load(settings.CNN_MODEL_PATH, map_location=cls._device, weights_only=True)
            )
            cls._classifier_mode = "legacy_2class"
            logger.warning(
                "Using legacy 2-class fallback (%s). "
                "RBC classification limited to normal/sickle only.",
                settings.CNN_MODEL_PATH,
            )
        else:
            # No CNN weights at all
            cls._cnn_num_classes = 0
            cls._cnn_class_map = {}
            cls._cnn_model = None
            cls._classifier_mode = "disabled"
            logger.error(
                "No CNN weights found. RBC classification disabled.",
            )

        if cls._cnn_model is not None:
            cls._cnn_model.eval()

        cls._transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def get_version(self) -> str:
        return "V1"

    # ════════════════════════════════════════════════════════════
    # STAGE 1: QUALITY GATE
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def quality_check(img: np.ndarray) -> dict:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        blur_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sat_mean = float(hsv[:, :, 1].mean())
        val_mean = float(hsv[:, :, 2].mean())

        blur_component = min(40.0, (blur_var / 50.0) * 40.0)
        sat_component = min(30.0, (sat_mean / 128.0) * 30.0)
        val_component = min(30.0, (val_mean / 180.0) * 30.0)
        score = round(blur_component + sat_component + val_component, 1)

        reasons = []
        if blur_var < 10:
            reasons.append("Image is extremely blurry")
        if sat_mean < 15:
            reasons.append("Image has almost no color saturation")
        if val_mean < 30:
            reasons.append("Image is too dark")
        if val_mean > 240:
            reasons.append("Image is overexposed")

        if score < 30 or len(reasons) >= 2:
            status = "rejected"
        elif score < 50 or len(reasons) == 1:
            status = "warning"
        else:
            status = "good"

        return {
            "quality_score": score,
            "quality_status": status,
            "rejection_reason": "; ".join(reasons) if reasons else None,
            "details": {
                "blur_variance": round(blur_var, 2),
                "saturation_mean": round(sat_mean, 2),
                "brightness_mean": round(val_mean, 2),
            },
        }

    # ════════════════════════════════════════════════════════════
    # MAIN ANALYSIS ENTRY POINT
    # ════════════════════════════════════════════════════════════

    def analyze(self, image_path: str) -> dict:
        """Run the full V1 pipeline on a single image."""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")

        # ── Stage 1: Quality Gate ──
        quality = self.quality_check(img)
        if quality["quality_status"] == "rejected":
            annotated_path = self._save_annotated_rejected(img, image_path, quality)
            return {
                "total_cells": 0, "sickle_count": 0, "normal_count": 0,
                "sickle_percentage": 0.0, "cell_details": [],
                "annotated_image_path": annotated_path,
                "quality_score": quality["quality_score"],
                "quality_status": quality["quality_status"],
                "rejection_reason": quality["rejection_reason"],
                "counts": {}, "classifier_mode": self._classifier_mode_label(),
            }

        output_img = img.copy()
        h_img, w_img = img.shape[:2]

        # ── Stage 2: YOLO Tiling — class-aware ──
        tile_size = 640
        overlap = int(tile_size * 0.25)
        step = tile_size - overlap
        global_boxes, global_scores, global_classes = [], [], []

        for y in range(0, h_img, step):
            for x in range(0, w_img, step):
                y_end = min(y + tile_size, h_img)
                x_end = min(x + tile_size, w_img)
                tile = img[y:y_end, x:x_end]
                if tile.shape[0] < 100 or tile.shape[1] < 100:
                    continue
                results = self._yolo_model(tile, conf=0.05, imgsz=tile_size, verbose=False)
                for result in results:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    scores = result.boxes.conf.cpu().numpy()
                    classes = result.boxes.cls.cpu().numpy()
                    for i, box in enumerate(boxes):
                        tx1, ty1, tx2, ty2 = map(int, box)
                        if tx1 <= 5 or ty1 <= 5 or tx2 >= tile.shape[1] - 5 or ty2 >= tile.shape[0] - 5:
                            continue
                        global_boxes.append([x + tx1, y + ty1, x + tx2, y + ty2])
                        global_scores.append(float(scores[i]))
                        global_classes.append(int(classes[i]))

        # ── Stage 3: Class-aware Global NMS ──
        valid_boxes, valid_classes, valid_scores = [], [], []
        if global_boxes:
            gb = torch.tensor(global_boxes, dtype=torch.float32)
            gs = torch.tensor(global_scores, dtype=torch.float32)
            gc = torch.tensor(global_classes, dtype=torch.int64)
            keep = torchvision.ops.batched_nms(gb, gs, gc, 0.35)
            for idx in keep:
                i = idx.item()
                valid_boxes.append(global_boxes[i])
                valid_classes.append(global_classes[i])
                valid_scores.append(global_scores[i])

        if not valid_boxes:
            annotated_path = self._save_annotated_v2(output_img, image_path, {})
            return {
                "total_cells": 0, "sickle_count": 0, "normal_count": 0,
                "sickle_percentage": 0.0, "cell_details": [],
                "annotated_image_path": annotated_path,
                "quality_score": quality["quality_score"],
                "quality_status": quality["quality_status"],
                "rejection_reason": None,
                "counts": {}, "classifier_mode": self._classifier_mode_label(),
            }

        # ── Stage 4: Watershed Decluster (rbc/sickle only) ──
        rbc_areas, rbc_widths, rbc_heights = [], [], []
        for i, box in enumerate(valid_boxes):
            cn = YOLO_CLASS_MAP.get(valid_classes[i], "unknown")
            if cn in ("rbc", "sickle"):
                w, h = box[2] - box[0], box[3] - box[1]
                rbc_areas.append(w * h)
                rbc_widths.append(w)
                rbc_heights.append(h)

        median_area = float(np.median(rbc_areas)) if rbc_areas else 0
        median_w = float(np.median(rbc_widths)) if rbc_widths else 0
        median_h = float(np.median(rbc_heights)) if rbc_heights else 0

        dec_boxes, dec_classes, dec_scores = [], [], []
        for i, box in enumerate(valid_boxes):
            cn = YOLO_CLASS_MAP.get(valid_classes[i], "unknown")
            if cn in ("rbc", "sickle") and median_w > 0 and median_h > 0:
                x1, y1, x2, y2 = map(int, box)
                bw, bh = x2 - x1, y2 - y1
                if bw > 1.5 * median_w or bh > 1.5 * median_h:
                    subcells = self._watershed_decluster(img, box, median_area, w_img, h_img)
                    for sc in subcells:
                        dec_boxes.append(sc)
                        dec_classes.append(valid_classes[i])
                        dec_scores.append(valid_scores[i])
                    continue
            dec_boxes.append(box)
            dec_classes.append(valid_classes[i])
            dec_scores.append(valid_scores[i])

        # ── Stage 5 + 6: Classification ──
        detected_cells = []
        for i, box in enumerate(dec_boxes):
            class_id = dec_classes[i]
            class_name = YOLO_CLASS_MAP.get(class_id, "unknown")
            confidence = dec_scores[i]

            if class_name in ("rbc", "sickle"):
                try:
                    cell_data = self._classify_rbc(img, box, class_id, confidence, median_area, w_img, h_img)
                    if cell_data:
                        detected_cells.append(cell_data)
                except Exception:
                    continue
            else:
                x1, y1, x2, y2 = map(int, box)
                detected_cells.append({
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "class_id": class_id,
                    "class_name": class_name,
                    "label": class_name.upper(),
                    "confidence": round(confidence, 4),
                    "cnn_probability": None,
                    "cnn_class_probabilities": None,
                    "circularity": None,
                    "aspect_ratio": None,
                    "solidity": None,
                })

        # ── Stage 7: Class-aware Spatial Deduplication ──
        final_cells = []
        for cell in detected_cells:
            cx = (cell["x1"] + cell["x2"]) / 2
            cy = (cell["y1"] + cell["y2"]) / 2
            dup = False
            for fc in final_cells:
                if fc["class_name"] != cell["class_name"]:
                    continue
                fcx = (fc["x1"] + fc["x2"]) / 2
                fcy = (fc["y1"] + fc["y2"]) / 2
                if np.sqrt((cx - fcx) ** 2 + (cy - fcy) ** 2) < 15:
                    dup = True
                    break
            if not dup:
                final_cells.append(cell)

        # ── Stage 8: Aggregate + Annotate ──
        counts = {"rbc": 0, "wbc": 0, "plt": 0, "sickle": 0, "target": 0, "other_abnormal": 0}
        total_cells = 0
        for cell in final_cells:
            total_cells += 1
            cn = cell["class_name"]
            if cn in counts:
                counts[cn] += 1
            x1, y1, x2, y2 = cell["x1"], cell["y1"], cell["x2"], cell["y2"]
            color = CLASS_COLORS.get(cn, (200, 200, 200))
            thickness = 4 if cn in ("sickle", "target", "other_abnormal") else (2 if cn in ("wbc", "rbc") else 1)
            cv2.rectangle(output_img, (x1, y1), (x2, y2), color, thickness)

        sickle_count = counts["sickle"]
        normal_count = counts["rbc"]
        total_rbc = counts["rbc"] + counts["sickle"] + counts["target"] + counts["other_abnormal"]
        sickle_pct = (sickle_count / total_rbc * 100) if total_rbc > 0 else 0.0
        annotated_path = self._save_annotated_v2(output_img, image_path, counts)

        # ── Stage 9: Field-Level Screening Interpretation ──
        field_interpretation = self._interpret_field(sickle_count, total_rbc, sickle_pct)

        return {
            "total_cells": total_cells,
            "sickle_count": sickle_count,
            "normal_count": normal_count,
            "sickle_percentage": round(sickle_pct, 2),
            "cell_details": final_cells,
            "annotated_image_path": annotated_path,
            "quality_score": quality["quality_score"],
            "quality_status": quality["quality_status"],
            "rejection_reason": None,
            "counts": counts,
            "classifier_mode": self._classifier_mode_label(),
            "field_interpretation": field_interpretation,
        }

    # ════════════════════════════════════════════════════════════
    # CNN CLASSIFICATION — PRIMARY LABEL AUTHORITY (Phase 3)
    # ════════════════════════════════════════════════════════════

    def _classify_rbc(self, img, box, yolo_class_id, yolo_confidence, median_area, w_img, h_img) -> dict | None:
        """
        Classify a single RBC/sickle detection.

        FP/FN-balanced: CNN is primary with morphology confirmation for sickle.
        CNN sickle threshold at 0.55 (dual-gate) with 0.85 CNN-only override.
        Blur filter at 30 rejects only genuinely blurry/artifact crops.
        Cell-level validation gates prevent false sickle from bad crops.
        """
        orig_x1, orig_y1, orig_x2, orig_y2 = map(int, box)
        x1, y1, x2, y2 = orig_x1, orig_y1, orig_x2, orig_y2
        pad = 15
        rx1, ry1 = max(0, x1 - pad), max(0, y1 - pad)
        rx2, ry2 = min(w_img, x2 + pad), min(h_img, y2 + pad)
        roi = img[ry1:ry2, rx1:rx2]
        if roi.size == 0:
            return None

        # Contour refinement — select contour NEAREST to YOLO box center (not largest)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            # Fallback: use original YOLO box when no contour found (improves recall)
            contours = None
            mc = None
            contour_area = (orig_x2 - orig_x1) * (orig_y2 - orig_y1)
            cx, cy = 0, 0
            cw, ch = orig_x2 - orig_x1 - 2 * pad, orig_y2 - orig_y1 - 2 * pad
            x1, y1, x2, y2 = orig_x1, orig_y1, orig_x2, orig_y2
            cell_crop = img[y1:y2, x1:x2]
            if cell_crop.size == 0:
                return None

        else:
            # Select contour nearest to YOLO box center (prevents snapping to adjacent cells)
            yolo_cx_local = (orig_x1 + orig_x2) / 2.0 - rx1
            yolo_cy_local = (orig_y1 + orig_y2) / 2.0 - ry1
            min_area_threshold = 100  # ignore tiny noise contours

            best_contour = None
            best_dist = float('inf')
            for cnt in contours:
                cnt_area = cv2.contourArea(cnt)
                if cnt_area < min_area_threshold:
                    continue
                M = cv2.moments(cnt)
                if M["m00"] == 0:
                    continue
                cnt_cx = M["m10"] / M["m00"]
                cnt_cy = M["m01"] / M["m00"]
                dist = np.sqrt((cnt_cx - yolo_cx_local) ** 2 + (cnt_cy - yolo_cy_local) ** 2)
                if dist < best_dist:
                    best_dist = dist
                    best_contour = cnt

            # Fallback to largest contour if no contour met area threshold
            if best_contour is None:
                best_contour = max(contours, key=cv2.contourArea)

            mc = best_contour
            contour_area = cv2.contourArea(mc)
            cx, cy, cw, ch = cv2.boundingRect(mc)
            x1, y1 = rx1 + cx, ry1 + cy
            x2, y2 = x1 + cw, y1 + ch

            cell_crop = img[y1:y2, x1:x2]
            if cell_crop.size == 0:
                return None

        # ── Multi-cell merge guard ──
        # If refined box area is much larger than original YOLO box, contour merged multiple cells
        orig_area = max((orig_x2 - orig_x1) * (orig_y2 - orig_y1), 1)
        refined_area = max((x2 - x1) * (y2 - y1), 1)
        if refined_area > orig_area * 2.0:
            # Merged contour → force Normal to prevent multi-cell confusion
            return {
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "class_id": 1, "class_name": "rbc",
                "label": "Normal", "confidence": 0.5,
                "cnn_probability": 0.0,
                "cnn_class_probabilities": {"normal": 1.0, "sickle": 0.0},
                "circularity": 0.0, "aspect_ratio": 0.0, "solidity": 0.0,
            }

        # Helper: forced-Normal return for crops that fail quality gates
        def _force_normal():
            return {
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "class_id": 1, "class_name": "rbc",
                "label": "Normal", "confidence": 0.5,
                "cnn_probability": 0.0,
                "cnn_class_probabilities": {"normal": 1.0, "sickle": 0.0},
                "circularity": 0.0, "aspect_ratio": 0.0, "solidity": 0.0,
            }

        # ══════════════════════════════════════════════════════════
        # CELL-LEVEL VALIDATION GATES (prevent false sickle from bad crops)
        # ══════════════════════════════════════════════════════════

        crop_area = max((x2 - x1) * (y2 - y1), 1)

        # Gate 1: Foreground ratio — reject crops that are mostly background
        # If the actual contour fills < 25% of the crop, it's noise/artifact
        foreground_ratio = contour_area / crop_area
        if foreground_ratio < 0.25:
            return _force_normal()

        # Gate 2: Fill ratio — contour should meaningfully fill its bounding rect
        # A sparse contour (thin speck in a large rect) is not a real cell
        contour_rect_area = max(cw * ch, 1)
        fill_ratio = contour_area / contour_rect_area
        if fill_ratio < 0.30:
            return _force_normal()

        # Gate 3: Centrality — contour center should be near original YOLO box center
        # If contour snapped to an artifact far from the intended detection, reject
        orig_cx = (orig_x1 + orig_x2) / 2.0
        orig_cy = (orig_y1 + orig_y2) / 2.0
        contour_cx = (x1 + x2) / 2.0
        contour_cy = (y1 + y2) / 2.0
        orig_w = max(orig_x2 - orig_x1, 1)
        orig_h = max(orig_y2 - orig_y1, 1)
        dx = abs(contour_cx - orig_cx) / orig_w
        dy = abs(contour_cy - orig_cy) / orig_h
        if dx > 0.4 or dy > 0.4:
            return _force_normal()

        # Gate 4: Extreme contour aspect ratio — scratches/artifacts, not cells
        contour_ar = max(cw, ch) / (min(cw, ch) + 1e-5)
        if contour_ar > 4.0:
            return _force_normal()

        # ── Area filter ──
        cell_area = crop_area
        if median_area > 0 and (cell_area < median_area * 0.15 or cell_area > median_area * 4.0):
            return None

        # ── Crop quality filter: reject blurry/artifact crops ──
        gray_crop = cv2.cvtColor(cell_crop, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray_crop, cv2.CV_64F).var()
        if blur_score < 30:
            return _force_normal()

        # ── Minimum crop size: reject fragments < 20x20 px ──
        if (x2 - x1) < 20 or (y2 - y1) < 20:
            return None

        # ── CNN INFERENCE ──
        cnn_label = None
        cnn_confidence = 0.0
        cnn_class_probabilities = {}
        sickle_prob = 0.0

        if self._cnn_model is not None:
            tensor = self._transform(cell_crop).unsqueeze(0).to(self._device)
            with torch.no_grad():
                logits = self._cnn_model(tensor)
                probs = torch.softmax(logits, dim=1)[0]

            # Build probability map for all classes
            for cls_idx, cls_name in self._cnn_class_map.items():
                cnn_class_probabilities[cls_name] = round(probs[cls_idx].item(), 4)

            # Get sickle probability specifically
            sickle_idx = {v: k for k, v in self._cnn_class_map.items()}.get("sickle")
            if sickle_idx is not None:
                sickle_prob = probs[sickle_idx].item()

            # CNN argmax for label
            top_idx = probs.argmax().item()
            top_prob = probs[top_idx].item()
            cnn_label = self._cnn_class_map.get(top_idx, "unknown")
            cnn_confidence = round(top_prob, 4)

            # Low-confidence → uncertain
            if top_prob < 0.5:
                cnn_label = "uncertain"
        else:
            cnn_label = "unclassified"
            cnn_confidence = 0.0
            cnn_class_probabilities = {"error": "CNN weights not loaded"}

        # ── MORPHOLOGY FEATURES ──
        # Light preprocessing to preserve sickle crescent shapes
        circularity, aspect_ratio, solidity = 0.0, 0.0, 0.0
        morphology_abnormal = False

        blurred = cv2.GaussianBlur(gray_crop, (5, 5), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(blurred)
        norm = cv2.normalize(clahe, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        at = cv2.adaptiveThreshold(norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 2)

        # Morphology preprocessing: moderate closure to reduce noise while preserving shape
        k_large = np.ones((5, 5), np.uint8)
        at = cv2.morphologyEx(at, cv2.MORPH_CLOSE, k_large, iterations=2)
        k_small = np.ones((3, 3), np.uint8)
        at = cv2.dilate(at, k_small, iterations=1)
        at = cv2.erode(at, k_small, iterations=1)

        ct, _ = cv2.findContours(at, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if ct:
            mc2 = max(ct, key=cv2.contourArea)
            m_area = cv2.contourArea(mc2)
            if m_area >= 30:
                perim = cv2.arcLength(mc2, True)
                circularity = (4 * np.pi * m_area) / (perim ** 2) if perim > 0 else 1.0
                rect = cv2.minAreaRect(mc2)
                rw, rh = rect[1]
                aspect_ratio = max(rw, rh) / (min(rw, rh) + 1e-5)
                hull = cv2.convexHull(mc2)
                hull_area = cv2.contourArea(hull)
                solidity = m_area / float(hull_area) if hull_area > 0 else 0.0

                # Edge exclusion
                if rx1 <= 5 or ry1 <= 5 or rx2 >= w_img - 5 or ry2 >= h_img - 5:
                    morphology_abnormal = False
                # Round cells are normal
                elif circularity > 0.80 or aspect_ratio < 1.25:
                    morphology_abnormal = False
                # Moderately elongated but solid → safe normal (not sickle)
                # Sickle cells have lower solidity (concave crescent)
                elif 1.25 <= aspect_ratio < 1.7 and solidity > 0.92:
                    morphology_abnormal = False
                else:
                    morphology_abnormal = True

        # ── BORDER CELL REJECTION FOR SICKLE ──
        border_cell = (x1 <= 3 or y1 <= 3 or x2 >= w_img - 3 or y2 >= h_img - 3)

        # morphology_veto moved after light-pass (see below)

        # ── LIGHT-PASS MORPHOLOGY (for composite ranking score + CNN override gate) ──
        # The heavy-pass (above) rounds sickle crescents making AR unreliable for ranking.
        # This lighter pass preserves crescent shapes for more accurate composite scoring.
        light_ar, light_circ, light_sol = aspect_ratio, circularity, solidity  # defaults
        at_light = cv2.adaptiveThreshold(norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY_INV, 15, 2)
        k_light = np.ones((3, 3), np.uint8)
        at_light = cv2.morphologyEx(at_light, cv2.MORPH_CLOSE, k_light, iterations=1)
        ct_light, _ = cv2.findContours(at_light, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if ct_light:
            mc_light = max(ct_light, key=cv2.contourArea)
            la = cv2.contourArea(mc_light)
            if la >= 30:
                lp = cv2.arcLength(mc_light, True)
                light_circ = (4 * np.pi * la) / (lp ** 2) if lp > 0 else 1.0
                lr = cv2.minAreaRect(mc_light)
                lrw, lrh = lr[1]
                light_ar = max(lrw, lrh) / (min(lrw, lrh) + 1e-5)
                lhull = cv2.convexHull(mc_light)
                lha = cv2.contourArea(lhull)
                light_sol = la / float(lha) if lha > 0 else 0.0

        # ── MORPHOLOGY VETO (uses light-pass for accuracy) ──
        # Heavy-pass distorts sickle crescents into round shapes (AR~1.0, circ>0.80).
        # Light-pass preserves shape — only TRULY round cells should be vetoed.
        morphology_veto = (light_ar > 0 and light_ar < 1.15
                           and light_circ > 0.75 and light_sol > 0.90)

        # ── COMPOSITE SICKLE SCORE (uses light-pass features for accurate ranking) ──
        morph_elongation = min(max(light_ar - 1.0, 0.0) / 2.0, 1.0)      # 0→1 as AR goes 1→3
        morph_concavity = min(max(1.0 - light_sol, 0.0) / 0.3, 1.0)      # 0→1 as sol drops 1→0.7
        morph_irregularity = min(max(1.0 - light_circ, 0.0) / 0.5, 1.0)  # 0→1 as circ drops 1→0.5
        morph_score = (morph_elongation * 0.5 + morph_concavity * 0.3 + morph_irregularity * 0.2)
        composite_sickle_score = sickle_prob * 0.60 + morph_score * 0.40

        # ── CNN OVERRIDE GUARD (uses light-pass multi-metric check) ──
        # Cell must appear non-round by ANY of the lighter/more-accurate measurements.
        # Some sickle crescents have near-round AR but reveal shape via low circ or low sol.
        light_pass_non_round = (light_ar >= 1.10 or light_circ < 0.60 or light_sol < 0.85)

        # ── FINAL LABEL: CNN + morphology dual-gate for sickle ──
        # Primary: CNN >= 0.55 AND heavy-pass morphology_abnormal (dual-gate)
        # Override: CNN >= 0.70 AND light-pass multi-metric says non-round
        if border_cell or morphology_veto:
            final_class_name = "rbc"
            final_label = "Normal"
            final_confidence = round(1.0 - sickle_prob, 4) if cnn_label == "sickle" else cnn_confidence
        elif cnn_label == "sickle" and sickle_prob >= 0.55 and morphology_abnormal:
            final_class_name = "sickle"
            final_label = "Sickle"
            final_confidence = round(composite_sickle_score, 4)
        elif cnn_label == "sickle" and sickle_prob >= 0.70 and light_pass_non_round and not morphology_veto:
            # CNN override: light-pass confirms non-round shape
            final_class_name = "sickle"
            final_label = "Sickle"
            final_confidence = round(composite_sickle_score, 4)
        elif (morph_score >= 0.55 and sickle_prob >= 0.40
              and not morphology_veto and not border_cell
              and not (circularity > 0.80 and solidity > 0.95)):
            # Morphology-driven gate (standard): moderate sickle shape + some CNN signal
            final_class_name = "sickle"
            final_label = "Sickle"
            final_confidence = round(composite_sickle_score, 4)
        elif (morph_score >= 0.70 and sickle_prob >= 0.15
              and not morphology_veto and not border_cell
              and not (circularity > 0.80 and solidity > 0.95)):
            # Morphology-dominant gate: extreme sickle shape
            final_class_name = "sickle"
            final_label = "Sickle"
            final_confidence = round(composite_sickle_score, 4)
        elif cnn_label in ("normal", "uncertain", "unclassified"):
            final_class_name = "rbc"
            final_label = "Normal"
            final_confidence = cnn_confidence
        elif cnn_label == "sickle":
            # CNN says sickle but evidence insufficient → downgrade
            final_class_name = "rbc"
            final_label = "Normal"
            final_confidence = round(1.0 - sickle_prob, 4)
        elif cnn_label == "target":
            final_class_name = "target"
            final_label = "Target"
            final_confidence = cnn_confidence
        elif cnn_label == "other_abnormal":
            final_class_name = "other_abnormal"
            final_label = "Other Abnormal"
            final_confidence = cnn_confidence
        else:
            final_class_name = "rbc"
            final_label = "Normal"
            final_confidence = cnn_confidence

        class_id_map = {"rbc": 1, "sickle": 3, "target": 4, "other_abnormal": 5}

        return {
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "class_id": class_id_map.get(final_class_name, 1),
            "class_name": final_class_name,
            "label": final_label,
            "confidence": final_confidence,
            "cnn_probability": cnn_confidence,
            "cnn_class_probabilities": cnn_class_probabilities,
            "circularity": round(circularity, 4),
            "aspect_ratio": round(aspect_ratio, 4),
            "solidity": round(solidity, 4),
            "light_ar": round(light_ar, 4),
            "light_circ": round(light_circ, 4),
            "light_sol": round(light_sol, 4),
            "morph_score": round(morph_score, 4),
            "composite_score": round(composite_sickle_score, 4),
        }

    # ════════════════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════════════════

    def _classifier_mode_label(self) -> str:
        """Report which classifier mode is active, for transparency."""
        mode_labels = {
            "4class": "4-class (normal/sickle/target/other_abnormal)",
            "trained_2class": "trained_2class (normal/sickle — Phase 3.5)",
            "legacy_2class": "legacy_2class fallback (normal/sickle only)",
            "disabled": "disabled (no CNN weights)",
        }
        return mode_labels.get(self._classifier_mode, "unknown")

    def _watershed_decluster(self, img, box, median_area, w_img, h_img):
        x1, y1, x2, y2 = map(int, box)
        pad = 10
        rx1, ry1 = max(0, x1 - pad), max(0, y1 - pad)
        rx2, ry2 = min(w_img, x2 + pad), min(h_img, y2 + pad)
        roi = img[ry1:ry2, rx1:rx2]
        if roi.size == 0:
            return [box]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        sure_bg = cv2.dilate(opening, kernel, iterations=3)
        dist = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist, 0.3 * dist.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)
        _, markers = cv2.connectedComponents(sure_fg)
        markers += 1
        markers[unknown == 255] = 0
        markers = cv2.watershed(roi, markers)

        subcells = []
        found = False
        for m in np.unique(markers):
            if m in (1, -1):
                continue
            mask = np.zeros(gray.shape, dtype="uint8")
            mask[markers == m] = 255
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                c = max(contours, key=cv2.contourArea)
                if cv2.contourArea(c) > median_area * 0.2:
                    bx, by, bw, bh = cv2.boundingRect(c)
                    subcells.append([rx1 + bx, ry1 + by, rx1 + bx + bw, ry1 + by + bh])
                    found = True
        return subcells if found else [box]

    # ── Field-Level Screening Interpretation (Step 5) ──

    @staticmethod
    def _interpret_field(sickle_count: int, total_rbc: int, sickle_pct: float) -> dict:
        """
        Produce a field-level screening interpretation from cell-level counts.

        Three-level classification:
          NEGATIVE                → no sickle evidence
          REVIEW                  → ambiguous / weak evidence, needs manual review
          SICKLE_SCREEN_POSITIVE  → strong screening signal (NOT definitive diagnosis)

        Dual-threshold for SICKLE_SCREEN_POSITIVE:
          sickle_count >= 3  AND  sickle_pct >= 5.0%
        This protects normal fields with stray FPs from being called positive.
        """

        # ── Evidence strength ──
        if sickle_count == 0:
            evidence = "none"
        elif sickle_count <= 2:
            evidence = "weak"
        elif sickle_count >= 10 and sickle_pct >= 10.0:
            evidence = "strong"
        elif sickle_count >= 3 and sickle_pct >= 5.0:
            evidence = "moderate"
        else:
            evidence = "weak"

        # ── Screening classification ──
        if sickle_count == 0:
            result = "NEGATIVE"
            confidence = 1.0
            summary = "No confident sickle-like morphology detected in this field."

        elif sickle_count >= 3 and sickle_pct >= 5.0:
            result = "SICKLE_SCREEN_POSITIVE"
            confidence = round(min(1.0, sickle_pct / 20.0), 4)
            summary = (
                f"Sickle cells detected: {sickle_count} cells "
                f"({sickle_pct:.1f}% of RBCs). "
                f"Evidence strength: {evidence}. "
                f"Screening positive — confirmatory testing recommended."
            )

        else:
            # 1-2 sickle, or >=3 but <5%
            result = "REVIEW"
            confidence = round(min(1.0, sickle_pct / 10.0), 4)
            summary = (
                f"Low-level sickle signal detected "
                f"({sickle_count} cells, {sickle_pct:.1f}%). "
                f"Manual review recommended."
            )

        return {
            "screening_result": result,
            "confidence": confidence,
            "sickle_percentage": round(sickle_pct, 2),
            "total_rbc_counted": total_rbc,
            "sickle_count": sickle_count,
            "evidence_strength": evidence,
            "summary": summary,
        }

    # ── Annotated Image Generation ──

    @staticmethod
    def _save_annotated_v2(output_img, source_path, counts):
        rbc = counts.get("rbc", 0)
        wbc = counts.get("wbc", 0)
        plt_count = counts.get("plt", 0)
        sickle = counts.get("sickle", 0)
        target = counts.get("target", 0)
        other_abn = counts.get("other_abnormal", 0)
        total = rbc + wbc + plt_count + sickle + target + other_abn
        total_rbc = rbc + sickle + target + other_abn
        sickle_pct = (sickle / total_rbc * 100) if total_rbc > 0 else 0.0

        oh, ow = 240, 480
        overlay = output_img.copy()
        cv2.rectangle(overlay, (15, 15), (15 + ow, 15 + oh), (0, 0, 0), -1)
        out = cv2.addWeighted(overlay, 0.75, output_img, 0.25, 0)
        y_pos = 50
        cv2.putText(out, "LabMind AI - V1 ANALYSIS", (30, y_pos), 2, 0.8, (255, 255, 255), 2)
        y_pos += 35
        cv2.putText(out, f"Total Detections: {total}", (30, y_pos), 2, 0.55, (200, 200, 200), 1)
        y_pos += 28
        cv2.putText(out, f"RBC (Normal): {rbc}", (30, y_pos), 2, 0.55, (0, 255, 0), 1)
        y_pos += 28
        cv2.putText(out, f"Sickle: {sickle} ({sickle_pct:.1f}%)", (30, y_pos), 2, 0.55, (0, 0, 255), 2)
        y_pos += 28
        cv2.putText(out, f"Target: {target}", (30, y_pos), 2, 0.55, (0, 165, 255), 1)
        y_pos += 28
        cv2.putText(out, f"Other Abnormal: {other_abn}", (30, y_pos), 2, 0.55, (0, 255, 255), 1)
        y_pos += 28
        cv2.putText(out, f"WBC: {wbc}  |  PLT: {plt_count}", (30, y_pos), 2, 0.55, (255, 180, 0), 1)

        settings = get_settings()
        annotated_dir = Path(settings.UPLOAD_DIR) / "annotated"
        annotated_dir.mkdir(parents=True, exist_ok=True)
        out_filename = f"analysis_{uuid.uuid4().hex}.jpg"
        out_path = str(annotated_dir / out_filename)
        cv2.imwrite(out_path, out)
        return f"annotated/{out_filename}"

    @staticmethod
    def _save_annotated_rejected(img, source_path, quality):
        out = img.copy()
        h, w = out.shape[:2]
        overlay = out.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 80), -1)
        out = cv2.addWeighted(overlay, 0.4, out, 0.6, 0)

        cv2.putText(out, "IMAGE QUALITY REJECTED", (30, 60), 2, 1.0, (0, 0, 255), 3)
        cv2.putText(out, f"Score: {quality['quality_score']}/100", (30, 100), 2, 0.7, (200, 200, 200), 2)
        if quality["rejection_reason"]:
            reason = quality["rejection_reason"][:100]
            cv2.putText(out, reason, (30, 140), 2, 0.5, (180, 180, 180), 1)

        settings = get_settings()
        annotated_dir = Path(settings.UPLOAD_DIR) / "annotated"
        annotated_dir.mkdir(parents=True, exist_ok=True)
        out_filename = f"rejected_{uuid.uuid4().hex}.jpg"
        out_path = str(annotated_dir / out_filename)
        cv2.imwrite(out_path, out)
        return f"annotated/{out_filename}"
