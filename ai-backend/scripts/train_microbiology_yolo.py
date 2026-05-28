"""
Train YOLOv8n — Clinical Bacteria Detection (4-class Gram-stain)
=================================================================
Classes:
  0: G-_Bacillus   (Gram-negative bacilli / rods)
  1: G+_Coccus     (Gram-positive cocci / spheres)
  2: G-_Coccus     (Gram-negative cocci / spheres)
  3: G+_Bacillus   (Gram-positive bacilli / rods)

Dataset: 6,004 images (640x640), pre-split 70/20/10
"""

# ── Thread / memory guards (MUST be before any heavy imports) ─────
import os
os.environ['OMP_NUM_THREADS'] = '4'

import torch
torch.set_num_threads(4)

import psutil
print(f"RAM available: {psutil.virtual_memory().available / 1024**3:.1f} GB")
print(f"RAM total    : {psutil.virtual_memory().total / 1024**3:.1f} GB")

# ── Imports ───────────────────────────────────────────────────────
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from ultralytics import YOLO

# ── Paths ─────────────────────────────────────────────────────────
DATA_YAML  = Path(r"D:\New folder\ai-backend\dataset_microbiology\yolo_dataset\data.yaml")
PROJECT    = Path(r"D:\New folder\ai-backend\dataset_microbiology\yolo_dataset")
RUN_NAME   = "bacteria_detector"
REPORT_DIR = Path(r"D:\New folder\ai-backend\dataset_microbiology\reports")

CLASS_NAMES = ["G-_Bacillus", "G+_Coccus", "G-_Coccus", "G+_Bacillus"]

SEP = "=" * 70

# ── Device check ──────────────────────────────────────────────────
print(f"\n{SEP}")
print("  DEVICE INFO")
print(SEP)

cuda_available = torch.cuda.is_available()
if cuda_available:
    device = 0
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem  = torch.cuda.get_device_properties(0).total_mem / 1024**3
    print(f"  CUDA available : YES")
    print(f"  GPU            : {gpu_name}")
    print(f"  GPU memory     : {gpu_mem:.1f} GB")
    print(f"  Training device: cuda:0")
else:
    device = "cpu"
    print(f"  CUDA available : NO")
    print(f"  Training device: cpu")
    print(f"  NOTE: Training on CPU will be very slow (expect 10-20+ hours)")

print(f"  PyTorch version: {torch.__version__}")
print(f"  CPU threads    : {torch.get_num_threads()}")

# ── Pre-flight checks ────────────────────────────────────────────
print(f"\n{SEP}")
print("  PRE-FLIGHT CHECKS")
print(SEP)

assert DATA_YAML.exists(), f"data.yaml not found: {DATA_YAML}"
print(f"  data.yaml      : {DATA_YAML}  [OK]")

for split in ["train", "val", "test"]:
    img_dir = PROJECT / "images" / split
    lbl_dir = PROJECT / "labels" / split
    n_img = len(list(img_dir.glob("*"))) if img_dir.exists() else 0
    n_lbl = len(list(lbl_dir.glob("*"))) if lbl_dir.exists() else 0
    status = "OK" if n_img == n_lbl and n_img > 0 else "PROBLEM"
    print(f"  {split:6s}: {n_img:5d} images, {n_lbl:5d} labels  [{status}]")

avail_gb = psutil.virtual_memory().available / 1024**3
if avail_gb < 2.0:
    print(f"\n  WARNING: Only {avail_gb:.1f} GB RAM available. Training may fail.")
    print(f"  Consider closing other applications.")

# ── Load model ────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  LOADING YOLOv8n PRETRAINED MODEL")
print(SEP)

model = YOLO("yolov8n.pt")
print(f"  Model loaded: yolov8n.pt")
print(f"  Parameters  : {sum(p.numel() for p in model.model.parameters()):,}")

# ── Train ─────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  STARTING TRAINING")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

t0 = time.time()

results = model.train(
    # ── Data ──
    data=str(DATA_YAML),

    # ── Training schedule ──
    epochs=50,
    imgsz=416,
    batch=4,
    patience=15,

    # ── Device ──
    device=device,
    workers=0,
    cache=False,

    # ── Output ──
    project=str(PROJECT),
    name=RUN_NAME,
    exist_ok=True,

    # ── Augmentation (tuned for microscopy) ──
    hsv_h=0.015,       # minimal hue shift — stain colors matter
    hsv_s=0.4,         # moderate saturation variation
    hsv_v=0.3,         # moderate brightness variation
    degrees=15,         # slight rotation — bacteria can be any orientation
    translate=0.1,      # small translation
    scale=0.3,          # moderate scale variation
    fliplr=0.5,         # horizontal flip — orientation-invariant
    flipud=0.3,         # vertical flip — less common but valid
    mosaic=0.0,         # disabled — microscopy crops are already dense
    mixup=0.0,          # disabled — mixing slides is not realistic
)

elapsed = time.time() - t0
elapsed_str = str(timedelta(seconds=int(elapsed)))

print(f"\n{SEP}")
print(f"  TRAINING COMPLETE")
print(f"  Duration: {elapsed_str}")
print(SEP)

# ── Validation ────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  VALIDATION ON VAL SET")
print(SEP)

best_weights = PROJECT / RUN_NAME / "weights" / "best.pt"
if not best_weights.exists():
    # Fallback: try last.pt
    best_weights = PROJECT / RUN_NAME / "weights" / "last.pt"

print(f"  Weights: {best_weights}")

val_model = YOLO(str(best_weights))
val_results = val_model.val(
    data=str(DATA_YAML),
    split="val",
    imgsz=416,
    batch=4,
    device=device,
    workers=0,
)

# Extract metrics
box = val_results.box
map50     = float(box.map50)       # mAP@0.5
map50_95  = float(box.map)         # mAP@0.5:0.95
precision = float(box.mp)          # mean precision
recall    = float(box.mr)          # mean recall

# Per-class mAP@50
per_class_map50 = {}
if hasattr(box, 'ap50') and box.ap50 is not None:
    ap50_arr = box.ap50
    for i, name in enumerate(CLASS_NAMES):
        if i < len(ap50_arr):
            per_class_map50[name] = float(ap50_arr[i])

print(f"\n  Overall Metrics:")
print(f"    mAP@50       : {map50:.4f}")
print(f"    mAP@50-95    : {map50_95:.4f}")
print(f"    Precision    : {precision:.4f}")
print(f"    Recall       : {recall:.4f}")

print(f"\n  Per-Class mAP@50:")
for name, ap in per_class_map50.items():
    bar = "#" * int(ap * 30)
    print(f"    {name:<14s}: {ap:.4f}  {bar}")

# ── Save report ───────────────────────────────────────────────────
print(f"\n{SEP}")
print("  SAVING TRAINING REPORT")
print(SEP)

REPORT_DIR.mkdir(parents=True, exist_ok=True)
report_path = REPORT_DIR / "yolo_training_report.json"

report = {
    "model": "yolov8n",
    "dataset": str(DATA_YAML),
    "classes": CLASS_NAMES,
    "nc": len(CLASS_NAMES),
    "training": {
        "epochs": 50,
        "imgsz": 416,
        "batch": 4,
        "device": "cuda:0" if cuda_available else "cpu",
        "duration_seconds": int(elapsed),
        "duration_human": elapsed_str,
        "completed_at": datetime.now().isoformat(),
    },
    "augmentation": {
        "hsv_h": 0.015, "hsv_s": 0.4, "hsv_v": 0.3,
        "degrees": 15, "translate": 0.1, "scale": 0.3,
        "fliplr": 0.5, "flipud": 0.3,
        "mosaic": 0.0, "mixup": 0.0,
    },
    "validation": {
        "map50": map50,
        "map50_95": map50_95,
        "precision": precision,
        "recall": recall,
        "per_class_map50": per_class_map50,
    },
    "weights": {
        "best": str(best_weights),
        "last": str(PROJECT / RUN_NAME / "weights" / "last.pt"),
    },
}

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"  Report saved: {report_path}")

# ── Final summary ─────────────────────────────────────────────────
print(f"\n{SEP}")
print("  DONE")
print(SEP)
print(f"  Best weights : {best_weights}")
print(f"  Report       : {report_path}")
print(f"  Duration     : {elapsed_str}")
print(f"  mAP@50       : {map50:.4f}")
print(f"  mAP@50-95    : {map50_95:.4f}")
print(f"{SEP}")
