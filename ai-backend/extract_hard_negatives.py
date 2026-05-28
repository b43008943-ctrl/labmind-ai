"""
LabMind — Hard-Negative Extraction (CNN FP Analysis)
Uses the actual pipeline's CNN (CellClassifierCNN) and YOLO to process
normal smears and identify cells with high sickle probability.

NO code changes. Read-only extraction.
"""
import json
import os
import sys
import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NORMAL_SMEARS_DIR = os.path.join("validation_smears", "normal")
OUTPUT_DIR = os.path.join("hard_negatives")
VALID_EXTS = ('.jpg', '.jpeg', '.png')

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ── Same CNN architecture as pipeline ──
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


# Same transform as pipeline (128x128)
TRANSFORM = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# CNN model paths (same priority order as pipeline)
CNN_PATHS = [
    ("cell_classifier_v1_rebuild.pth", 4, {0: "normal", 1: "sickle", 2: "target", 3: "other_abnormal"}),
    ("cell_classifier_2class.pth", 2, {0: "normal", 1: "sickle"}),
    ("cell_classifier_v3.pth", 2, {0: "normal", 1: "sickle"}),
]


def load_cnn_model():
    for wpath, num_classes, class_map in CNN_PATHS:
        if os.path.exists(wpath):
            model = CellClassifierCNN(num_classes=num_classes).to(DEVICE)
            model.load_state_dict(torch.load(wpath, map_location=DEVICE, weights_only=True))
            model.eval()
            print(f"  CNN loaded: {wpath} ({num_classes} classes)")
            return model, class_map
    print("  ERROR: No CNN weights found!")
    return None, {}


def main():
    print("=" * 70)
    print("  LabMind — Hard-Negative CNN FP Extraction")
    print("  Identifying normal cells the CNN incorrectly scores as sickle")
    print("=" * 70)
    print()

    model, class_map = load_cnn_model()
    if model is None:
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load YOLO
    from ultralytics import YOLO
    yolo_path = "blood_ai_v2.pt"
    if not os.path.exists(yolo_path):
        # Check models/ dir
        yolo_path = os.path.join("models", "blood_ai_v2.pt")
    if not os.path.exists(yolo_path):
        # Search for any .pt YOLO model
        for f in os.listdir("."):
            if f.endswith(".pt") and "yolo" not in f.lower() and "classifier" not in f.lower():
                yolo_path = f
                break
    print(f"  YOLO: {yolo_path}")
    yolo_model = YOLO(yolo_path)

    normal_smears = sorted([
        f for f in os.listdir(NORMAL_SMEARS_DIR) if f.lower().endswith(VALID_EXTS)
    ])
    print(f"  Normal smears: {len(normal_smears)}")
    print()

    all_hard_negatives = []
    per_smear_summary = []

    for smear_file in normal_smears:
        smear_path = os.path.join(NORMAL_SMEARS_DIR, smear_file)
        smear_name = smear_file.replace(".jpg.jpg", "").replace(".jpg", "")
        print(f"  Processing: {smear_file} ...")

        img = cv2.imread(smear_path)
        if img is None:
            continue
        h_img, w_img = img.shape[:2]

        # YOLO detection
        results = yolo_model.predict(img, conf=0.05, iou=0.35, verbose=False)

        cells = []
        for result in results:
            if result.boxes is None:
                continue
            for box_data in result.boxes:
                box = box_data.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, box)

                # Contour refinement (same as pipeline)
                pad = 15
                rx1, ry1 = max(0, x1 - pad), max(0, y1 - pad)
                rx2, ry2 = min(w_img, x2 + pad), min(h_img, y2 + pad)
                roi = img[ry1:ry2, rx1:rx2]
                if roi.size == 0:
                    continue

                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    yolo_cx = (x1 + x2) / 2.0 - rx1
                    yolo_cy = (y1 + y2) / 2.0 - ry1
                    best_cnt, best_d = None, float('inf')
                    for cnt in contours:
                        if cv2.contourArea(cnt) < 100:
                            continue
                        M = cv2.moments(cnt)
                        if M["m00"] == 0:
                            continue
                        d = np.sqrt((M["m10"]/M["m00"] - yolo_cx)**2 + (M["m01"]/M["m00"] - yolo_cy)**2)
                        if d < best_d:
                            best_d, best_cnt = d, cnt
                    if best_cnt is None:
                        best_cnt = max(contours, key=cv2.contourArea)
                    cx, cy, cw, ch = cv2.boundingRect(best_cnt)
                    cx1, cy1 = rx1 + cx, ry1 + cy
                    cx2, cy2 = cx1 + cw, cy1 + ch
                else:
                    cx1, cy1, cx2, cy2 = x1, y1, x2, y2

                cell_crop = img[cy1:cy2, cx1:cx2]
                if cell_crop.size == 0 or (cx2-cx1) < 20 or (cy2-cy1) < 20:
                    continue

                # CNN
                tensor = TRANSFORM(cell_crop).unsqueeze(0).to(DEVICE)
                with torch.no_grad():
                    probs = torch.softmax(model(tensor), dim=1)[0]

                sickle_idx = {v: k for k, v in class_map.items()}.get("sickle")
                sickle_prob = probs[sickle_idx].item() if sickle_idx is not None else 0.0
                top_idx = probs.argmax().item()

                # Blur score
                gc = cv2.cvtColor(cell_crop, cv2.COLOR_BGR2GRAY)
                blur = cv2.Laplacian(gc, cv2.CV_64F).var()

                cells.append({
                    "sickle_prob": round(sickle_prob, 4),
                    "cnn_label": class_map.get(top_idx, "unknown"),
                    "cnn_conf": round(probs[top_idx].item(), 4),
                    "blur": round(blur, 1),
                    "w": cx2 - cx1, "h": cy2 - cy1,
                    "crop": cell_crop,
                    "smear": smear_name,
                })

        high = [c for c in cells if c["sickle_prob"] >= 0.50]
        moderate = [c for c in cells if 0.40 <= c["sickle_prob"] < 0.50]
        hard_negs = [c for c in cells if c["sickle_prob"] >= 0.40]

        print(f"    Cells: {len(cells)}  |  sickle_prob≥0.50: {len(high)}  |  0.40-0.50: {len(moderate)}  |  HN total: {len(hard_negs)}")

        per_smear_summary.append({
            "smear": smear_name, "total_cells": len(cells),
            "high_sickle": len(high), "moderate_sickle": len(moderate),
            "hard_negatives": len(hard_negs),
        })
        all_hard_negatives.extend(hard_negs)

    print()
    print(f"  ═══ TOTAL HARD NEGATIVES: {len(all_hard_negatives)} ═══")

    # Sort by sickle probability (worst first)
    all_hard_negatives.sort(key=lambda x: x["sickle_prob"], reverse=True)

    # Save crops + manifest
    labels = []
    for idx, hn in enumerate(all_hard_negatives):
        fname = f"hn_{idx:04d}_{hn['smear']}.jpg"
        cv2.imwrite(os.path.join(OUTPUT_DIR, fname), hn["crop"])
        labels.append({
            "filename": fname, "true_class": "normal",
            "cnn_predicted": hn["cnn_label"], "sickle_prob": hn["sickle_prob"],
            "cnn_confidence": hn["cnn_conf"], "source_smear": hn["smear"],
            "blur_score": hn["blur"], "dimensions": f"{hn['w']}x{hn['h']}",
        })

    manifest = {
        "version": "v1-baseline-hard-negatives",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_hard_negatives": len(all_hard_negatives),
        "sickle_prob_threshold": 0.40,
        "per_smear_summary": per_smear_summary,
        "distribution": {
            "prob_090_100": len([l for l in labels if l["sickle_prob"] >= 0.90]),
            "prob_080_090": len([l for l in labels if 0.80 <= l["sickle_prob"] < 0.90]),
            "prob_070_080": len([l for l in labels if 0.70 <= l["sickle_prob"] < 0.80]),
            "prob_060_070": len([l for l in labels if 0.60 <= l["sickle_prob"] < 0.70]),
            "prob_050_060": len([l for l in labels if 0.50 <= l["sickle_prob"] < 0.60]),
            "prob_040_050": len([l for l in labels if 0.40 <= l["sickle_prob"] < 0.50]),
        },
        "labels": labels,
    }

    mpath = os.path.join(OUTPUT_DIR, "hard_negatives.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n  Saved to: {os.path.abspath(OUTPUT_DIR)}/")
    print(f"  Manifest: {mpath}")
    print()
    for key, label in [("prob_090_100","0.90-1.00"),("prob_080_090","0.80-0.90"),
                        ("prob_070_080","0.70-0.80"),("prob_060_070","0.60-0.70"),
                        ("prob_050_060","0.50-0.60"),("prob_040_050","0.40-0.50")]:
        print(f"    {label}: {manifest['distribution'][key]}")
    print()
    print("  TOP 10 WORST:")
    for l in labels[:10]:
        print(f"    {l['filename']}: sickle_prob={l['sickle_prob']} from {l['source_smear']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
