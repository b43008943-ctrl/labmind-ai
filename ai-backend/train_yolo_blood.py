"""
LabMind AI -- Train YOLOv8 Blood Cell Detector
================================================

Fine-tunes YOLOv8-nano on the erythrocytesIDB mask-derived dataset
(87 images, 3654 annotations, 3 classes: circular/elongated/other).

Output: yolo_dataset/blood_cell_detector/weights/best.pt
"""

import json
import os
import random
import shutil
import sys
import time
import traceback
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import cv2
import numpy as np

random.seed(42)
np.random.seed(42)

# -- Paths --
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


# ========================================================
#  STEP 1 -- TRAIN YOLO
# ========================================================

def step1_train() -> dict:
    """Fine-tune YOLOv8 on the blood cell dataset."""
    sep("STEP 1 -- TRAIN YOLOv8 BLOOD CELL DETECTOR")

    from ultralytics import YOLO

    if not DATA_YAML.exists():
        print(f"  [X] data.yaml not found at {DATA_YAML}")
        sys.exit(1)

    if not GENERIC_MODEL_PATH.exists():
        print(f"  [X] Base model not found at {GENERIC_MODEL_PATH}")
        print("       Downloading yolov8n.pt ...")
        base_model = YOLO("yolov8n.pt")
    else:
        print(f"  Base model: {GENERIC_MODEL_PATH}")
        base_model = YOLO(str(GENERIC_MODEL_PATH))

    print(f"  Dataset: {DATA_YAML}")
    print(f"  Output: {YOLO_DATASET_DIR / 'blood_cell_detector'}")
    print()

    t0 = time.time()
    batch_size = 8

    try:
        results = base_model.train(
            data=str(DATA_YAML),
            epochs=100,
            imgsz=640,
            batch=batch_size,
            patience=20,
            save=True,
            project=str(YOLO_DATASET_DIR),
            name="blood_cell_detector",
            exist_ok=True,

            # Data augmentation for medical images
            hsv_h=0.01,        # slight hue shift (staining variation)
            hsv_s=0.3,         # saturation variation
            hsv_v=0.2,         # brightness variation
            degrees=180,       # cells have no preferred orientation
            flipud=0.5,        # vertical flip
            fliplr=0.5,        # horizontal flip
            scale=0.3,         # scale variation (different magnifications)
            mosaic=0.5,        # mosaic augmentation

            # Loss weights
            cls=1.0,
            box=7.5,
        )
    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
            print(f"\n  [!] OOM with batch={batch_size}, retrying with batch=4...")
            batch_size = 4
            try:
                results = base_model.train(
                    data=str(DATA_YAML),
                    epochs=100,
                    imgsz=640,
                    batch=batch_size,
                    patience=20,
                    save=True,
                    project=str(YOLO_DATASET_DIR),
                    name="blood_cell_detector",
                    exist_ok=True,
                    hsv_h=0.01, hsv_s=0.3, hsv_v=0.2,
                    degrees=180, flipud=0.5, fliplr=0.5,
                    scale=0.3, mosaic=0.5,
                    cls=1.0, box=7.5,
                )
            except RuntimeError as e2:
                if "out of memory" in str(e2).lower():
                    print(f"\n  [!] OOM with batch=4, retrying with batch=2...")
                    batch_size = 2
                    results = base_model.train(
                        data=str(DATA_YAML),
                        epochs=100,
                        imgsz=640,
                        batch=batch_size,
                        patience=20,
                        save=True,
                        project=str(YOLO_DATASET_DIR),
                        name="blood_cell_detector",
                        exist_ok=True,
                        hsv_h=0.01, hsv_s=0.3, hsv_v=0.2,
                        degrees=180, flipud=0.5, fliplr=0.5,
                        scale=0.3, mosaic=0.5,
                        cls=1.0, box=7.5,
                    )
                else:
                    raise
        else:
            raise

    elapsed_min = (time.time() - t0) / 60.0
    print(f"\n  Training completed in {elapsed_min:.1f} minutes (batch={batch_size})")

    return {"results": results, "elapsed_min": elapsed_min, "batch_size": batch_size}


# ========================================================
#  STEP 2 -- EVALUATE
# ========================================================

def step2_evaluate(train_info: dict) -> dict:
    """Print training metrics."""
    sep("STEP 2 -- EVALUATE TRAINING RESULTS")

    results = train_info["results"]

    # Find best weights
    best_pt = YOLO_DATASET_DIR / "blood_cell_detector" / "weights" / "best.pt"
    last_pt = YOLO_DATASET_DIR / "blood_cell_detector" / "weights" / "last.pt"

    print(f"  Best weights: {best_pt}  ({'EXISTS' if best_pt.exists() else 'NOT FOUND'})")
    print(f"  Last weights: {last_pt}  ({'EXISTS' if last_pt.exists() else 'NOT FOUND'})")

    # Extract metrics from results
    metrics = {}
    try:
        # results.results_dict contains the final metrics
        rd = results.results_dict if hasattr(results, "results_dict") else {}
        metrics["mAP50"] = round(rd.get("metrics/mAP50(B)", 0), 4)
        metrics["mAP50_95"] = round(rd.get("metrics/mAP50-95(B)", 0), 4)
        metrics["precision"] = round(rd.get("metrics/precision(B)", 0), 4)
        metrics["recall"] = round(rd.get("metrics/recall(B)", 0), 4)

        print(f"\n  Overall Metrics:")
        print(f"    mAP@50:    {metrics['mAP50']}")
        print(f"    mAP@50-95: {metrics['mAP50_95']}")
        print(f"    Precision: {metrics['precision']}")
        print(f"    Recall:    {metrics['recall']}")
    except Exception as e:
        print(f"  [!] Could not extract metrics from results object: {e}")

    # Per-class metrics -- validate on the trained model
    per_class = {}
    try:
        from ultralytics import YOLO
        best_model = YOLO(str(best_pt))
        val_results = best_model.val(data=str(DATA_YAML), verbose=False)

        if hasattr(val_results, "box"):
            box = val_results.box
            # box.maps is per-class mAP50-95, box.ap50 or similar
            if hasattr(box, "maps") and box.maps is not None:
                for i, m in enumerate(box.maps):
                    cls_name = CLASS_NAMES.get(i, f"class_{i}")
                    per_class[cls_name] = round(float(m), 4)
                    print(f"    {cls_name} mAP50-95: {per_class[cls_name]}")

            if hasattr(box, "ap50") and box.ap50 is not None:
                print(f"\n  Per-class mAP@50:")
                per_class_50 = {}
                for i, m in enumerate(box.ap50):
                    cls_name = CLASS_NAMES.get(i, f"class_{i}")
                    per_class_50[cls_name] = round(float(m), 4)
                    print(f"    {cls_name}: {per_class_50[cls_name]}")
                metrics["per_class_mAP50"] = per_class_50
    except Exception as e:
        print(f"  [!] Could not run per-class validation: {e}")

    # Try to find confusion matrix image
    cm_path = YOLO_DATASET_DIR / "blood_cell_detector" / "confusion_matrix.png"
    if cm_path.exists():
        print(f"\n  Confusion matrix saved at: {cm_path}")
    else:
        # Check alternative paths
        for alt in ["confusion_matrix_normalized.png", "confusion_matrix.png"]:
            alt_path = YOLO_DATASET_DIR / "blood_cell_detector" / alt
            if alt_path.exists():
                print(f"\n  Confusion matrix: {alt_path}")
                break

    # Check for training curves
    curves_path = YOLO_DATASET_DIR / "blood_cell_detector" / "results.png"
    if curves_path.exists():
        print(f"  Training curves: {curves_path}")

    metrics["per_class_mAP"] = per_class
    metrics["best_weights"] = str(best_pt)

    return metrics


# ========================================================
#  STEP 3 -- COMPARE WITH GENERIC YOLO
# ========================================================

def collect_test_images() -> list[tuple[Path, str]]:
    """Collect test images from multiple sources."""
    test_images = []

    # 2 random val images
    val_dir = YOLO_DATASET_DIR / "images" / "val"
    if val_dir.exists():
        val_imgs = [f for f in val_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
        if len(val_imgs) >= 2:
            sample = random.sample(val_imgs, 2)
            for img in sample:
                test_images.append((img, "yolo_val"))
        elif val_imgs:
            test_images.append((val_imgs[0], "yolo_val"))

    # 2 validation smears
    if VAL_SMEARS_DIR.exists():
        smear_imgs = []
        for sub in ["normal", "sickle"]:
            sub_dir = VAL_SMEARS_DIR / sub
            if sub_dir.exists():
                for f in sub_dir.iterdir():
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                        smear_imgs.append((f, f"val_smear_{sub}"))
        if len(smear_imgs) >= 2:
            sample = random.sample(smear_imgs, 2)
            test_images.extend(sample)
        elif smear_imgs:
            test_images.append(smear_imgs[0])

    # 1 kaggle positive
    if KAGGLE_POS_DIR.exists():
        kaggle_imgs = [f for f in KAGGLE_POS_DIR.iterdir()
                       if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
        if kaggle_imgs:
            test_images.append((random.choice(kaggle_imgs), "kaggle_pos"))

    return test_images


def run_model_on_image(model, img_path: Path, conf: float) -> dict:
    """Run a YOLO model on a single image and return detection stats."""
    results = model(str(img_path), conf=conf, imgsz=640, verbose=False)

    all_boxes = []
    all_scores = []
    all_classes = []

    for r in results:
        boxes = r.boxes.xyxy.cpu().numpy()
        scores = r.boxes.conf.cpu().numpy()
        classes = r.boxes.cls.cpu().numpy()
        for i in range(len(boxes)):
            all_boxes.append(boxes[i].tolist())
            all_scores.append(float(scores[i]))
            all_classes.append(int(classes[i]))

    avg_conf = float(np.mean(all_scores)) if all_scores else 0.0

    return {
        "detections": len(all_boxes),
        "avg_confidence": round(avg_conf, 4),
        "boxes": all_boxes,
        "scores": all_scores,
        "classes": all_classes,
    }


def draw_detections(img: np.ndarray, det: dict, model_name: str,
                    class_names: dict) -> np.ndarray:
    """Draw bounding boxes on an image."""
    out = img.copy()

    for i in range(len(det["boxes"])):
        x1, y1, x2, y2 = map(int, det["boxes"][i])
        cls_id = det["classes"][i]
        conf = det["scores"][i]
        cls_name = class_names.get(cls_id, f"cls{cls_id}")

        # Color by class
        color = CLASS_COLORS.get(cls_id, (200, 200, 200))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

        label = f"{cls_name} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        cv2.rectangle(out, (x1, max(y1 - th - 6, 0)), (x1 + tw, y1), color, -1)
        cv2.putText(out, label, (x1, max(y1 - 2, th + 2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1, cv2.LINE_AA)

    # Header
    h, w = out.shape[:2]
    overlay = out.copy()
    cv2.rectangle(overlay, (5, 5), (350, 50), (0, 0, 0), -1)
    out = cv2.addWeighted(overlay, 0.7, out, 0.3, 0)
    cv2.putText(out, f"{model_name}: {det['detections']} dets, "
                     f"avg conf={det['avg_confidence']:.3f}",
                (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    return out


def step3_compare(metrics: dict) -> list[dict]:
    """Compare generic YOLO vs blood-specific YOLO on test images."""
    sep("STEP 3 -- COMPARE GENERIC vs BLOOD-SPECIFIC YOLO")

    from ultralytics import YOLO

    best_pt = YOLO_DATASET_DIR / "blood_cell_detector" / "weights" / "best.pt"
    if not best_pt.exists():
        print("  [X] best.pt not found. Skipping comparison.")
        return []

    print("  Loading models...")
    generic_model = YOLO(str(GENERIC_MODEL_PATH))
    blood_model = YOLO(str(best_pt))
    print("  [OK] Both models loaded.")

    # Generic YOLO class names (from blood_ai_v2 / yolov8n)
    generic_classes = {0: "person", 1: "bicycle", 2: "car"}  # COCO defaults
    # Try to get actual names from the model
    if hasattr(generic_model, "names"):
        generic_classes = generic_model.names

    # Blood model class names
    blood_classes = CLASS_NAMES
    if hasattr(blood_model, "names"):
        blood_classes = blood_model.names

    test_images = collect_test_images()
    print(f"  Test images: {len(test_images)}")

    # Comparison table header
    print(f"\n  {'Image':<35} | {'Old Dets':>8} | {'New Dets':>8} | "
          f"{'Old Conf':>8} | {'New Conf':>8} | Source")
    print(f"  {'-'*35}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+--------")

    comparison_results = []
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)

    for img_path, source in test_images:
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  [!] Cannot read: {img_path}")
            continue

        # Run both models
        old_det = run_model_on_image(generic_model, img_path, conf=0.05)
        new_det = run_model_on_image(blood_model, img_path, conf=0.25)

        print(f"  {img_path.name:<35} | {old_det['detections']:>8} | "
              f"{new_det['detections']:>8} | {old_det['avg_confidence']:>8.4f} | "
              f"{new_det['avg_confidence']:>8.4f} | {source}")

        # Save side-by-side comparison
        left = draw_detections(img, old_det, "Generic YOLO (conf=0.05)", generic_classes)
        right = draw_detections(img, new_det, "Blood YOLO (conf=0.25)", blood_classes)

        # Normalize heights for hstack
        h_left, h_right = left.shape[0], right.shape[0]
        if h_left != h_right:
            target_h = max(h_left, h_right)
            if h_left < target_h:
                pad = np.zeros((target_h - h_left, left.shape[1], 3), dtype=np.uint8)
                left = np.vstack([left, pad])
            if h_right < target_h:
                pad = np.zeros((target_h - h_right, right.shape[1], 3), dtype=np.uint8)
                right = np.vstack([right, pad])

        # Normalize widths
        w_left, w_right = left.shape[1], right.shape[1]
        if w_left != w_right:
            target_w = max(w_left, w_right)
            if w_left < target_w:
                pad = np.zeros((left.shape[0], target_w - w_left, 3), dtype=np.uint8)
                left = np.hstack([left, pad])
            if w_right < target_w:
                pad = np.zeros((right.shape[0], target_w - w_right, 3), dtype=np.uint8)
                right = np.hstack([right, pad])

        # Gap between panels
        gap = np.zeros((left.shape[0], 4, 3), dtype=np.uint8) + 128
        combined = np.hstack([left, gap, right])

        safe_name = img_path.stem.replace(".", "_")
        out_path = COMPARISON_DIR / f"compare_{safe_name}.png"
        cv2.imwrite(str(out_path), combined)

        comparison_results.append({
            "image": img_path.name,
            "source": source,
            "old_detections": old_det["detections"],
            "new_detections": new_det["detections"],
            "old_avg_conf": old_det["avg_confidence"],
            "new_avg_conf": new_det["avg_confidence"],
            "comparison_image": str(out_path),
        })

    print(f"\n  [OK] {len(comparison_results)} comparison images saved to: {COMPARISON_DIR}")
    return comparison_results


# ========================================================
#  STEP 5 -- FINAL REPORT
# ========================================================

def step5_report(train_info: dict, metrics: dict,
                 comparison_results: list[dict]):
    """Save final training report."""
    sep("STEP 5 -- FINAL REPORT")

    best_pt = YOLO_DATASET_DIR / "blood_cell_detector" / "weights" / "best.pt"

    # Try to figure out best epoch from training results
    best_epoch = "unknown"
    training_epochs = "unknown"
    try:
        results = train_info["results"]
        # The results object has epoch info
        if hasattr(results, "epoch"):
            training_epochs = results.epoch
    except Exception:
        pass

    # Check results CSV for best epoch
    csv_path = YOLO_DATASET_DIR / "blood_cell_detector" / "results.csv"
    if csv_path.exists():
        try:
            import csv
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            training_epochs = len(rows)

            # Find best epoch by mAP50
            best_map = -1
            for i, row in enumerate(rows):
                # Column names may have spaces
                for key in row:
                    if "mAP50" in key and "mAP50-95" not in key:
                        val = float(row[key].strip())
                        if val > best_map:
                            best_map = val
                            best_epoch = i + 1
                        break
        except Exception as e:
            print(f"  [!] Could not parse results.csv: {e}")

    report = {
        "training_epochs": training_epochs,
        "best_epoch": best_epoch,
        "best_mAP50": metrics.get("mAP50", 0),
        "best_mAP50_95": metrics.get("mAP50_95", 0),
        "precision": metrics.get("precision", 0),
        "recall": metrics.get("recall", 0),
        "per_class_mAP": metrics.get("per_class_mAP", {}),
        "per_class_mAP50": metrics.get("per_class_mAP50", {}),
        "best_weights_path": str(best_pt),
        "training_time_minutes": round(train_info["elapsed_min"], 1),
        "batch_size": train_info["batch_size"],
        "dataset_yaml": str(DATA_YAML),
        "comparison_results": comparison_results,
    }

    report_path = YOLO_DATASET_DIR / "training_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  [OK] Report saved to: {report_path}")

    # Print summary
    print(f"\n  TRAINING SUMMARY:")
    print(f"    Epochs trained:  {training_epochs}")
    print(f"    Best epoch:      {best_epoch}")
    print(f"    Best mAP@50:     {metrics.get('mAP50', 'N/A')}")
    print(f"    Best mAP@50-95:  {metrics.get('mAP50_95', 'N/A')}")
    print(f"    Precision:       {metrics.get('precision', 'N/A')}")
    print(f"    Recall:          {metrics.get('recall', 'N/A')}")
    print(f"    Training time:   {train_info['elapsed_min']:.1f} min")
    print(f"    Best weights:    {best_pt}")

    return report


# ========================================================
#  MAIN
# ========================================================

def main():
    sep("LabMind AI -- YOLOv8 Blood Cell Detector Training")
    print(f"  Dataset: {YOLO_DATASET_DIR}")
    print(f"  Base model: {GENERIC_MODEL_PATH}")

    try:
        # Step 1: Train
        train_info = step1_train()

        # Step 2: Evaluate
        metrics = step2_evaluate(train_info)

        # Step 3 + 4: Compare and save diagnostic images
        comparison_results = step3_compare(metrics)

        # Step 5: Final report
        report = step5_report(train_info, metrics, comparison_results)

        sep("TRAINING COMPLETE")
        print(f"\n  Best weights: {report['best_weights_path']}")
        print(f"  Report: {YOLO_DATASET_DIR / 'training_report.json'}")
        print(f"  Comparisons: {COMPARISON_DIR}")
        print()

    except Exception as e:
        print(f"\n\n  [FATAL ERROR]")
        print(f"  {type(e).__name__}: {e}")
        print(f"\n  Full traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
