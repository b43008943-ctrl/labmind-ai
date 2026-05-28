"""
Train YOLOv8-nano to detect urine sediment cells (RBC, pus/WBC, epithelial).

Uses the YOLO dataset prepared by prepare_urine_yolo_dataset.py.
Best weights are saved automatically by ultralytics.
"""

import json
import os
import sys
import torch
from datetime import datetime
from pathlib import Path

import psutil

# Cap CPU threads to avoid thrashing on limited hardware
os.environ['OMP_NUM_THREADS'] = '4'
torch.set_num_threads(4)

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent / "dataset_urine" / "yolo_dataset"
DATA_YAML = PROJECT_DIR / "data.yaml"
REPORT_DIR = SCRIPT_DIR.parent / "dataset_urine" / "reports"
RUN_NAME = "urine_cell_detector"
CLASS_NAMES = ["rbc", "pus", "ep"]


def main():
    print("=" * 65)
    print("  YOLOv8-nano Urine Sediment Cell Detector Training")
    print("=" * 65)

    # ── 1. Device check ────────────────────────────────────────────────────
    cuda_available = torch.cuda.is_available()
    device = 0 if cuda_available else "cpu"
    print(f"\nCUDA available : {cuda_available}")
    if cuda_available:
        print(f"GPU device     : {torch.cuda.get_device_name(0)}")
        print(f"GPU memory     : {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
    else:
        print("Falling back to CPU (training will be slow)")
    print(f"Using device   : {device}")

    # ── 2. Verify dataset ──────────────────────────────────────────────────
    if not DATA_YAML.exists():
        print(f"\nERROR: data.yaml not found at {DATA_YAML}")
        print("Run prepare_urine_yolo_dataset.py first.")
        sys.exit(1)
    print(f"\nDataset config : {DATA_YAML}")

    # ── 3. Memory check ────────────────────────────────────────────────────
    ram = psutil.virtual_memory()
    print(f"\nRAM total      : {ram.total / 1024**3:.1f} GB")
    print(f"RAM available  : {ram.available / 1024**3:.1f} GB")
    print(f"RAM used       : {ram.percent}%")

    # ── 4. Train ───────────────────────────────────────────────────────────
    from ultralytics import YOLO

    model = YOLO("yolov8n.pt")
    print("\nStarting training...\n")

    results = model.train(
        data=str(DATA_YAML),
        epochs=60,
        imgsz=416,
        batch=4,
        patience=15,
        device=device,
        workers=0,
        cache=False,
        project=str(PROJECT_DIR),
        name=RUN_NAME,
        exist_ok=True,
        # Augmentation — tuned for small medical dataset
        hsv_h=0.015,
        hsv_s=0.4,
        hsv_v=0.3,
        degrees=15,
        translate=0.1,
        scale=0.3,
        fliplr=0.5,
        flipud=0.3,
        mosaic=0.0,
        mixup=0.0,
        save=True,
        verbose=True,
    )

    # ── 4. Locate best weights ─────────────────────────────────────────────
    best_weights = PROJECT_DIR / RUN_NAME / "weights" / "best.pt"
    if not best_weights.exists():
        print(f"\nWARNING: best.pt not found at expected path {best_weights}")
        # Try to find it
        candidates = list(PROJECT_DIR.rglob("best.pt"))
        if candidates:
            best_weights = candidates[0]
            print(f"Found best.pt at: {best_weights}")
        else:
            print("ERROR: Could not locate best.pt anywhere.")
            sys.exit(1)

    print(f"\nBest weights: {best_weights}")

    # ── 5. Validate on test set ────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  Validation on TEST set")
    print("=" * 65 + "\n")

    best_model = YOLO(str(best_weights))
    metrics = best_model.val(
        data=str(DATA_YAML),
        split="test",
        imgsz=416,
        device=device,
        verbose=True,
    )

    # Extract per-class metrics
    per_class = {}
    for i, cls_name in enumerate(CLASS_NAMES):
        per_class[cls_name] = {
            "precision": float(metrics.box.p[i]) if i < len(metrics.box.p) else 0.0,
            "recall":    float(metrics.box.r[i]) if i < len(metrics.box.r) else 0.0,
            "mAP50":     float(metrics.box.ap50[i]) if i < len(metrics.box.ap50) else 0.0,
            "mAP50_95":  float(metrics.box.ap[i]) if i < len(metrics.box.ap) else 0.0,
        }

    # Print results table
    print(f"\n{'Class':<12} {'Precision':>10} {'Recall':>10} {'mAP@50':>10} {'mAP@50-95':>10}")
    print("-" * 55)
    for cls_name, m in per_class.items():
        print(f"{cls_name:<12} {m['precision']:>10.4f} {m['recall']:>10.4f} {m['mAP50']:>10.4f} {m['mAP50_95']:>10.4f}")
    print("-" * 55)
    print(f"{'ALL':<12} {float(metrics.box.mp):>10.4f} {float(metrics.box.mr):>10.4f} {float(metrics.box.map50):>10.4f} {float(metrics.box.map):>10.4f}")

    # ── 6. Save report ─────────────────────────────────────────────────────
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "date": datetime.now().isoformat(),
        "base_model": "yolov8n.pt",
        "epochs_configured": 60,
        "early_stopping_patience": 15,
        "device": str(device),
        "best_mAP50": float(metrics.box.map50),
        "best_mAP50_95": float(metrics.box.map),
        "mean_precision": float(metrics.box.mp),
        "mean_recall": float(metrics.box.mr),
        "per_class_metrics": per_class,
        "model_path": str(best_weights),
        "data_yaml": str(DATA_YAML),
    }

    report_path = REPORT_DIR / "yolo_training_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport saved to: {report_path}")
    print(f"Best weights at: {best_weights}")

    print("\n" + "=" * 65)
    print("  TRAINING COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    main()
