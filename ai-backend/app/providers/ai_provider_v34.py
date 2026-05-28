"""
LabMind AI — V34 Diagnostic Engine Provider
Wraps the existing main_diagnostic_system.py pipeline as an AIProvider.
This runs synchronously and is intended to be called from a Celery worker only.
"""

import os
import sys
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


# ── Stage 2 CNN Architecture (identical to main_diagnostic_system.py) ──
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
            nn.Dropout(0.5), nn.Linear(128 * 8 * 8, 256), nn.ReLU(), nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


class V34Provider(AIProvider):
    """
    Wraps the full V34 diagnostic pipeline:
    YOLO tiling → Global NMS → Watershed decluster → CNN classify → Morphology decision tree
    """

    _yolo_model = None
    _cnn_model = None
    _device = None
    _transform = None

    def __init__(self):
        if V34Provider._device is None:
            self._load_models()

    @classmethod
    def _load_models(cls):
        settings = get_settings()
        cls._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Import YOLO here to avoid import at module level
        from ultralytics import YOLO
        cls._yolo_model = YOLO(settings.YOLO_MODEL_PATH)

        cls._cnn_model = CellClassifierCNN(num_classes=2).to(cls._device)
        cls._cnn_model.load_state_dict(
            torch.load(settings.CNN_MODEL_PATH, map_location=cls._device, weights_only=True)
        )
        cls._cnn_model.eval()

        cls._transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def get_version(self) -> str:
        return "V34"

    def get_config_snapshot(self) -> dict:
        """Return pipeline configuration for audit trail."""
        return {
            "engine": "V34",
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

    def analyze(self, image_path: str) -> dict:
        """Run the full V34 pipeline on a single image."""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")

        output_img = img.copy()
        h_img, w_img = img.shape[:2]

        # ── Stage 1: YOLO Tiling ──
        tile_size = 640
        overlap = int(tile_size * 0.25)
        step = tile_size - overlap
        global_boxes, global_scores = [], []

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
                    for i, box in enumerate(boxes):
                        tx1, ty1, tx2, ty2 = map(int, box)
                        if tx1 <= 5 or ty1 <= 5 or tx2 >= tile.shape[1] - 5 or ty2 >= tile.shape[0] - 5:
                            continue
                        global_boxes.append([x + tx1, y + ty1, x + tx2, y + ty2])
                        global_scores.append(float(scores[i]))

        # ── Stage 2: Global NMS ──
        valid_boxes = []
        if global_boxes:
            gb = torch.tensor(global_boxes, dtype=torch.float32)
            gs = torch.tensor(global_scores, dtype=torch.float32)
            keep = torchvision.ops.nms(gb, gs, 0.35)
            for idx in keep:
                valid_boxes.append(global_boxes[idx.item()])

        if not valid_boxes:
            # Generate annotated image and return zero results
            annotated_path = self._save_annotated(output_img, image_path, 0, 0, 0)
            return {
                "total_cells": 0, "sickle_count": 0, "normal_count": 0,
                "sickle_percentage": 0.0, "cell_details": [],
                "annotated_image_path": annotated_path,
            }

        # ── Stage 3: Watershed Decluster ──
        areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in valid_boxes]
        widths = [b[2] - b[0] for b in valid_boxes]
        heights = [b[3] - b[1] for b in valid_boxes]
        median_area = float(np.median(areas)) if areas else 0
        median_w = float(np.median(widths)) if widths else 0
        median_h = float(np.median(heights)) if heights else 0

        declustered = []
        for box in valid_boxes:
            x1, y1, x2, y2 = map(int, box)
            w, h = x2 - x1, y2 - y1
            if w > 1.5 * median_w or h > 1.5 * median_h:
                subcells = self._watershed_decluster(img, box, median_area, w_img, h_img)
                declustered.extend(subcells)
            else:
                declustered.append(box)
        valid_boxes = declustered

        # ── Stage 4: Classification ──
        total_cells, sickle_count, normal_count = 0, 0, 0
        detected_cells = []

        for box in valid_boxes:
            try:
                cell_data = self._classify_cell(img, box, median_area, w_img, h_img)
                if cell_data:
                    detected_cells.append(cell_data)
            except Exception:
                continue

        # ── Stage 5: Spatial Deduplication ──
        final_cells = []
        for cell in detected_cells:
            cx = (cell["x1"] + cell["x2"]) / 2
            cy = (cell["y1"] + cell["y2"]) / 2
            dup = False
            for fc in final_cells:
                fcx = (fc["x1"] + fc["x2"]) / 2
                fcy = (fc["y1"] + fc["y2"]) / 2
                if np.sqrt((cx - fcx) ** 2 + (cy - fcy) ** 2) < 15:
                    dup = True
                    break
            if not dup:
                final_cells.append(cell)

        for cell in final_cells:
            total_cells += 1
            x1, y1, x2, y2 = cell["x1"], cell["y1"], cell["x2"], cell["y2"]
            if cell["label"] == "Sickle":
                sickle_count += 1
                cv2.rectangle(output_img, (x1, y1), (x2, y2), (0, 0, 255), 4)
            else:
                normal_count += 1
                cv2.rectangle(output_img, (x1, y1), (x2, y2), (0, 255, 0), 1)

        sickle_pct = (sickle_count / total_cells * 100) if total_cells > 0 else 0.0
        annotated_path = self._save_annotated(output_img, image_path, total_cells, sickle_count, normal_count)

        return {
            "total_cells": total_cells,
            "sickle_count": sickle_count,
            "normal_count": normal_count,
            "sickle_percentage": round(sickle_pct, 2),
            "cell_details": final_cells,
            "annotated_image_path": annotated_path,
        }

    # ── Helpers ──

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
                    cx, cy, cw, ch = cv2.boundingRect(c)
                    subcells.append([rx1 + cx, ry1 + cy, rx1 + cx + cw, ry1 + cy + ch])
                    found = True
        return subcells if found else [box]

    def _classify_cell(self, img, box, median_area, w_img, h_img) -> dict | None:
        x1, y1, x2, y2 = map(int, box)
        pad = 15
        rx1, ry1 = max(0, x1 - pad), max(0, y1 - pad)
        rx2, ry2 = min(w_img, x2 + pad), min(h_img, y2 + pad)
        roi = img[ry1:ry2, rx1:rx2]
        if roi.size == 0:
            return None

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        mc = max(contours, key=cv2.contourArea)
        cx, cy, cw, ch = cv2.boundingRect(mc)
        x1, y1 = rx1 + cx, ry1 + cy
        x2, y2 = x1 + cw, y1 + ch

        cell_crop = img[y1:y2, x1:x2]
        if cell_crop.size == 0:
            return None

        # ── Area filter ──
        cell_area = (x2 - x1) * (y2 - y1)
        if cell_area < median_area * 0.2 or cell_area > median_area * 3.0:
            return None

        # ── Crop quality filter: reject blurry/artifact crops ──
        # Laplacian variance below threshold → too blurry to classify reliably
        gray_crop = cv2.cvtColor(cell_crop, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray_crop, cv2.CV_64F).var()
        if blur_score < 100:
            # Low-quality crop → classify as normal, don't risk FP
            return {
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "label": "Normal", "confidence": 0.5,
                "cnn_probability": 0.0, "circularity": 0.0,
                "aspect_ratio": 0.0, "solidity": 0.0,
            }

        # ── Minimum crop size: reject fragments < 20x20 px ──
        if (x2 - x1) < 20 or (y2 - y1) < 20:
            return None

        # ── CNN probability ──
        tensor = self._transform(cell_crop).unsqueeze(0).to(self._device)
        with torch.no_grad():
            probs = torch.softmax(self._cnn_model(tensor), dim=1)[0]
            sickle_prob = probs[1].item()

        # ── Morphology-based shape analysis ──
        blurred = cv2.GaussianBlur(gray_crop, (5, 5), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(blurred)
        norm = cv2.normalize(clahe, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        at = cv2.adaptiveThreshold(norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 2)

        k_large = np.ones((5, 5), np.uint8)
        at = cv2.morphologyEx(at, cv2.MORPH_CLOSE, k_large, iterations=2)
        k_small = np.ones((3, 3), np.uint8)
        at = cv2.dilate(at, k_small, iterations=1)
        at = cv2.erode(at, k_small, iterations=1)

        ct, _ = cv2.findContours(at, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        morphology_abnormal = False
        circularity = aspect_ratio = solidity = 0.0

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

                # Edge exclusion — cells touching image boundary are unreliable
                if rx1 <= 5 or ry1 <= 5 or rx2 >= w_img - 5 or ry2 >= h_img - 5:
                    morphology_abnormal = False
                # Round cells are normal — raised veto from 0.75 to 0.78
                elif circularity > 0.78 or aspect_ratio < 1.40:
                    morphology_abnormal = False
                # Moderately elongated but very solid → still normal
                elif 1.40 <= aspect_ratio < 2.0 and solidity > 0.92:
                    morphology_abnormal = False
                else:
                    # Elongated + low solidity → genuinely suspicious shape
                    morphology_abnormal = True

        # ── Final decision: require BOTH strong CNN AND morphology ──
        # CNN threshold raised to 0.75 to compensate for sickle-heavy training bias
        # (training data: 155 sickle / 128 normal → model biased toward sickle)
        label = "Normal"
        if morphology_abnormal and sickle_prob >= 0.75:
            label = "Sickle"

        # Combined confidence for frontend tiered interpretation
        confidence = sickle_prob if label == "Sickle" else (1.0 - sickle_prob)

        return {
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "label": label,
            "confidence": round(confidence, 4),
            "cnn_probability": round(sickle_prob, 4),
            "circularity": round(circularity, 4),
            "aspect_ratio": round(aspect_ratio, 4),
            "solidity": round(solidity, 4),
        }

    @staticmethod
    def _save_annotated(output_img, source_path, total, sickle, normal):
        sickle_pct = (sickle / total * 100) if total > 0 else 0.0
        oh, ow = 160, 480
        overlay = output_img.copy()
        cv2.rectangle(overlay, (15, 15), (15 + ow, 15 + oh), (0, 0, 0), -1)
        out = cv2.addWeighted(overlay, 0.75, output_img, 0.25, 0)
        cv2.putText(out, "LabMind AI - SICKLE CELL REPORT", (30, 50), 2, 0.8, (255, 255, 255), 2)
        cv2.putText(out, f"Total Cells: {total}", (30, 90), 2, 0.6, (200, 200, 200), 1)
        cv2.putText(out, f"Sickle Count: {sickle} ({sickle_pct:.1f}%)", (30, 120), 2, 0.6, (0, 0, 255), 2)
        cv2.putText(out, f"Normal Count: {normal}", (30, 150), 2, 0.6, (0, 255, 0), 1)

        settings = get_settings()
        annotated_dir = Path(settings.UPLOAD_DIR) / "annotated"
        annotated_dir.mkdir(parents=True, exist_ok=True)
        out_filename = f"analysis_{uuid.uuid4().hex}.jpg"
        out_path = str(annotated_dir / out_filename)
        cv2.imwrite(out_path, out)
        return f"annotated/{out_filename}"
