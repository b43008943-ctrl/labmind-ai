import json
import os
import random
from pathlib import Path
import cv2
import numpy as np

# Force UTF-8 output on Windows
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
YOLO_DATASET_DIR = SCRIPT_DIR / "yolo_dataset"
DATA_YAML = YOLO_DATASET_DIR / "data.yaml"
GENERIC_MODEL_PATH = SCRIPT_DIR / "yolov8n.pt"
VAL_SMEARS_DIR = SCRIPT_DIR / "validation_smears"
KAGGLE_POS_DIR = (SCRIPT_DIR / "dataset_robust" / "raw" / "source_kaggle_scd"
                  / "Positive" / "Labelled")
COMPARISON_DIR = YOLO_DATASET_DIR / "comparison_results"

CLASS_NAMES = {0: "circular", 1: "elongated", 2: "other"}
CLASS_COLORS = {
    0: (0, 255, 0),     # green  = circular
    1: (0, 0, 255),     # red    = elongated
    2: (255, 0, 0),     # blue   = other
}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

def sep(title: str):
    print(f"\n{'=' * 90}")
    print(f"  {title}")
    print("=" * 90)

from ultralytics import YOLO
best_pt = YOLO_DATASET_DIR / "blood_cell_detector" / "weights" / "best.pt"

if not best_pt.exists():
    print(f"ERROR: No best.pt found at {best_pt}")
    sys.exit(1)

metrics = {"mAP50": 0.0758, "mAP50_95": 0.0286, "precision": 0.671, "recall": 0.0642}

def collect_test_images():
    test_images = []
    # 2 random val images
    val_dir = YOLO_DATASET_DIR / "images" / "val"
    if val_dir.exists():
        val_imgs = [f for f in val_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
        if len(val_imgs) >= 2:
            test_images.extend(random.sample(val_imgs, 2))
        elif val_imgs:
            test_images.append(val_imgs[0])
    
    # 2 validation smears
    if VAL_SMEARS_DIR.exists():
        smear_imgs = []
        for sub in ["normal", "sickle"]:
            sub_dir = VAL_SMEARS_DIR / sub
            if sub_dir.exists():
                smear_imgs.extend([f for f in sub_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS])
        if len(smear_imgs) >= 2:
            test_images.extend(random.sample(smear_imgs, 2))

    # 1 kaggle pos
    if KAGGLE_POS_DIR.exists():
        kaggle_imgs = [f for f in KAGGLE_POS_DIR.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
        if kaggle_imgs:
            test_images.append(random.choice(kaggle_imgs))

    return test_images

def run_model_on_image(model, img_path: Path, conf: float) -> dict:
    results = model(str(img_path), conf=conf, imgsz=640, verbose=False)
    all_boxes, all_scores, all_classes = [], [], []
    for r in results:
        boxes = r.boxes.xyxy.cpu().numpy()
        scores = r.boxes.conf.cpu().numpy()
        classes = r.boxes.cls.cpu().numpy()
        for i in range(len(boxes)):
            all_boxes.append(boxes[i].tolist())
            all_scores.append(float(scores[i]))
            all_classes.append(int(classes[i]))
    avg_conf = float(np.mean(all_scores)) if all_scores else 0.0
    return {"detections": len(all_boxes), "avg_confidence": round(avg_conf, 4), "boxes": all_boxes, "scores": all_scores, "classes": all_classes}

def draw_detections(img: np.ndarray, det: dict, model_name: str, class_names: dict) -> np.ndarray:
    out = img.copy()
    for i in range(len(det["boxes"])):
        x1, y1, x2, y2 = map(int, det["boxes"][i])
        cls_id = det["classes"][i]
        conf = det["scores"][i]
        cls_name = class_names.get(cls_id, f"cls{cls_id}")
        color = CLASS_COLORS.get(cls_id, (200, 200, 200))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"{cls_name} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        cv2.rectangle(out, (x1, max(y1 - th - 6, 0)), (x1 + tw, y1), color, -1)
        cv2.putText(out, label, (x1, max(y1 - 2, th + 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1, cv2.LINE_AA)
    overlay = out.copy()
    cv2.rectangle(overlay, (5, 5), (350, 50), (0, 0, 0), -1)
    out = cv2.addWeighted(overlay, 0.7, out, 0.3, 0)
    cv2.putText(out, f"{model_name}: {det['detections']} dets, conf={det['avg_confidence']:.3f}", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    return out

generic_model = YOLO(str(GENERIC_MODEL_PATH))
blood_model = YOLO(str(best_pt))
generic_classes = generic_model.names if hasattr(generic_model, "names") else {0: "person", 1: "bicycle", 2: "car"}
blood_classes = CLASS_NAMES

test_images = collect_test_images()
COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
comparison_results = []
print("Comparing models...")
for img_path in test_images:
    img = cv2.imread(str(img_path))
    if img is None: continue
    old_det = run_model_on_image(generic_model, img_path, conf=0.05)
    new_det = run_model_on_image(blood_model, img_path, conf=0.25)
    
    left = draw_detections(img, old_det, "Generic YOLO (0.05)", generic_classes)
    right = draw_detections(img, new_det, "Blood YOLO (0.25)", blood_classes)
    
    target_h = max(left.shape[0], right.shape[0])
    if left.shape[0] < target_h: left = np.vstack([left, np.zeros((target_h - left.shape[0], left.shape[1], 3), dtype=np.uint8)])
    if right.shape[0] < target_h: right = np.vstack([right, np.zeros((target_h - right.shape[0], right.shape[1], 3), dtype=np.uint8)])
    
    target_w = max(left.shape[1], right.shape[1])
    if left.shape[1] < target_w: left = np.hstack([left, np.zeros((left.shape[0], target_w - left.shape[1], 3), dtype=np.uint8)])
    if right.shape[1] < target_w: right = np.hstack([right, np.zeros((right.shape[0], target_w - right.shape[1], 3), dtype=np.uint8)])
    
    gap = np.zeros((left.shape[0], 4, 3), dtype=np.uint8) + 128
    combined = np.hstack([left, gap, right])
    out_path = COMPARISON_DIR / f"compare_{img_path.stem}.png"
    cv2.imwrite(str(out_path), combined)
    
    comparison_results.append({
        "image": img_path.name,
        "old_detections": old_det["detections"],
        "new_detections": new_det["detections"],
        "old_avg_conf": old_det["avg_confidence"],
        "new_avg_conf": new_det["avg_confidence"],
        "comparison_image": str(out_path)
    })
    print(f"  {img_path.name}")
    print(f"    Old: {old_det['detections']} dets (conf {old_det['avg_confidence']})")
    print(f"    New: {new_det['detections']} dets (conf {new_det['avg_confidence']})")

import csv
best_epoch = "unknown"
training_epochs = "unknown"
csv_path = YOLO_DATASET_DIR / "blood_cell_detector" / "results.csv"
if csv_path.exists():
    try:
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        training_epochs = len(rows)
        best_map = -1
        for i, row in enumerate(rows):
            for key in row:
                if "mAP50" in key and "mAP50-95" not in key:
                    val = float(row[key].strip())
                    if val > best_map: best_map = val; best_epoch = i + 1
                    break
    except Exception: pass

report = {
    "training_epochs": training_epochs,
    "best_epoch": best_epoch,
    "best_mAP50": metrics["mAP50"],
    "best_mAP50_95": metrics["mAP50_95"],
    "best_weights_path": str(best_pt),
    "comparison_results": comparison_results
}
report_path = YOLO_DATASET_DIR / "training_report.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, default=str)

print("\nFINISH SCRIPT DONE.")
