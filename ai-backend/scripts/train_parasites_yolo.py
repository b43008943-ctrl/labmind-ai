"""
Train YOLOv8 Parasite Egg Detector
===================================
Trains a YOLOv8n model to detect 11 types of parasitic eggs
in microscopic stool images (Chula-ParasiteEgg-11 dataset).

Expected training time: Several hours on CPU, ~30-60 min on GPU.
"""

import os
os.environ['OMP_NUM_THREADS'] = '4'

import torch
torch.set_num_threads(4)

import psutil
print(f"RAM available: {psutil.virtual_memory().available / 1024**3:.1f} GB")

import json
import sys
from datetime import datetime
from pathlib import Path

from ultralytics import YOLO


def check_device():
    """Check CUDA availability and print device info."""
    print("=" * 60)
    print("DEVICE INFORMATION")
    print("=" * 60)
    print(f"PyTorch version : {torch.__version__}")
    print(f"CUDA available  : {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        device = 0
        print(f"CUDA device     : {torch.cuda.get_device_name(0)}")
        print(f"CUDA version    : {torch.version.cuda}")
        gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1024**3
        print(f"GPU memory      : {gpu_mem:.1f} GB")
    else:
        device = 'cpu'
        print("No CUDA GPU detected — training will run on CPU.")
        print("This is expected to take many hours.")

    print(f"CPU cores       : {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")
    print(f"Total RAM       : {psutil.virtual_memory().total / 1024**3:.1f} GB")
    print(f"Available RAM   : {psutil.virtual_memory().available / 1024**3:.1f} GB")
    print(f"Selected device : {device}")
    print("=" * 60)
    return device


def train_model(device):
    """Train YOLOv8n on the parasite egg dataset."""

    # Paths
    data_yaml = "d:/New folder/ai-backend/dataset_parasites/yolo_dataset/data.yaml"
    project_dir = "d:/New folder/ai-backend/dataset_parasites/yolo_dataset"

    # Verify data.yaml exists
    if not os.path.exists(data_yaml):
        print(f"ERROR: data.yaml not found at: {data_yaml}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("STARTING YOLOv8n TRAINING — PARASITE EGG DETECTOR")
    print("=" * 60)
    print(f"Data config : {data_yaml}")
    print(f"Project dir : {project_dir}")
    print(f"Run name    : parasite_egg_detector")
    print(f"Start time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # Load pretrained YOLOv8n
    model = YOLO('yolov8n.pt')

    # Train
    results = model.train(
        # --- Core config (CPU-optimized) ---
        data=data_yaml,
        epochs=50,
        imgsz=416,
        batch=4,
        patience=15,
        device=device,
        workers=0,
        cache=False,
        project=project_dir,
        name='parasite_egg_detector',
        exist_ok=True,

        # --- Data augmentation ---
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
    )

    return model, results


def validate_and_report(model):
    """Run validation, print metrics, and save JSON report."""

    data_yaml = "d:/New folder/ai-backend/dataset_parasites/yolo_dataset/data.yaml"
    best_weights = "d:/New folder/ai-backend/dataset_parasites/yolo_dataset/parasite_egg_detector/weights/best.pt"

    print("\n" + "=" * 60)
    print("VALIDATION ON VAL SET")
    print("=" * 60)

    # Load best weights for validation
    best_model = YOLO(best_weights)
    val_results = best_model.val(data=data_yaml)

    # --- Extract overall metrics ---
    map50 = float(val_results.box.map50)
    map50_95 = float(val_results.box.map)
    precision = float(val_results.box.mp)
    recall = float(val_results.box.mr)

    print("\n" + "-" * 60)
    print("OVERALL METRICS")
    print("-" * 60)
    print(f"  mAP@50      : {map50:.4f}")
    print(f"  mAP@50-95   : {map50_95:.4f}")
    print(f"  Precision    : {precision:.4f}")
    print(f"  Recall       : {recall:.4f}")

    # --- Per-class mAP@50 ---
    class_names = val_results.names  # dict {idx: name}
    per_class_ap50 = val_results.box.ap50  # array of AP@50 per class

    print("\n" + "-" * 60)
    print("PER-CLASS mAP@50")
    print("-" * 60)

    per_class_metrics = {}
    for i, ap in enumerate(per_class_ap50):
        name = class_names[i]
        ap_val = float(ap)
        per_class_metrics[name] = {
            "mAP50": round(ap_val, 4)
        }
        print(f"  {name:<35s} : {ap_val:.4f}")

    # --- Save JSON report ---
    report_dir = Path("d:/New folder/ai-backend/dataset_parasites/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "yolo_training_report.json"

    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": "YOLOv8n",
        "dataset": "Chula-ParasiteEgg-11",
        "epochs_run": int(val_results.speed.get("epochs", 50)) if hasattr(val_results, 'speed') else 50,
        "best_mAP50": round(map50, 4),
        "mAP50_95": round(map50_95, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "per_class_metrics": per_class_metrics,
        "model_path": best_weights,
        "imgsz": 416,
        "batch": 4,
    }

    # Try to get actual epochs run from training results CSV
    results_csv = Path("d:/New folder/ai-backend/dataset_parasites/yolo_dataset/parasite_egg_detector/results.csv")
    if results_csv.exists():
        import csv
        with open(results_csv, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            # Subtract header row
            report["epochs_run"] = len(rows) - 1 if len(rows) > 1 else 0

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Report saved to : {report_path}")
    print(f"Best weights at : {best_weights}")
    print("=" * 60)

    return report


def main():
    print("\n" + "=" * 60)
    print("  YOLOv8 PARASITE EGG DETECTOR — TRAINING PIPELINE")
    print("  11-class detection on Chula-ParasiteEgg-11 dataset")
    print("=" * 60 + "\n")

    # Step 1: Check device
    device = check_device()

    # Step 2: Train
    model, results = train_model(device)

    # Step 3: Validate & report
    report = validate_and_report(model)

    print("\nDone. Training pipeline finished successfully.")


if __name__ == '__main__':
    main()
