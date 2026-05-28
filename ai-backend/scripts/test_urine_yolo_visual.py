"""
test_urine_yolo_visual.py
─────────────────────────
Runs the trained urine YOLO model on a sample of test images and saves
annotated results for visual inspection, including side-by-side comparisons
with ground truth bounding boxes.

Usage:
    python scripts/test_urine_yolo_visual.py
"""

import os
import csv
import copy
from pathlib import Path
from collections import defaultdict

import cv2
import numpy as np
from ultralytics import YOLO


# ────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────
MODEL_PATH = r"D:\New folder\ai-backend\dataset_urine\yolo_dataset\urine_cell_detector\weights\best.pt"
TEST_IMAGES_DIR = r"D:\New folder\ai-backend\dataset_urine\yolo_dataset\images\test"
GT_CSV_PATH = r"D:\New folder\ai-backend\dataset_urine\source_umid\test.csv"
OUTPUT_DIR = r"D:\New folder\ai-backend\dataset_urine\reports\visual_test"

IMGSZ = 416
CONF_THRESH = 0.25
IOU_THRESH = 0.45
NUM_IMAGES = 10
PICK_EVERY_N = 6  # Pick every 6th image for variety

# Class names (must match data.yaml order: 0=rbc, 1=pus, 2=ep)
CLASS_NAMES = ["rbc", "pus", "ep"]

# Display-friendly names and BGR colors for drawing
CLASS_DISPLAY = {
    "rbc": {"label": "RBC",  "color": (0, 0, 255)},    # Red in BGR
    "pus": {"label": "Pus",  "color": (0, 200, 0)},     # Green in BGR
    "ep":  {"label": "Ep",   "color": (255, 100, 0)},    # Blue in BGR
}

# Font settings
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.5
FONT_THICKNESS = 1
BOX_THICKNESS = 2


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def load_ground_truth(csv_path: str) -> dict:
    """
    Parse test.csv and return a dict mapping image filename → list of
    annotation dicts: {xmin, ymin, xmax, ymax, label}.
    """
    gt = defaultdict(list)
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gt[row["image"]].append({
                "xmin": float(row["xmin"]),
                "ymin": float(row["ymin"]),
                "xmax": float(row["xmax"]),
                "ymax": float(row["ymax"]),
                "label": row["label"].strip().lower(),
            })
    return dict(gt)


def select_test_images(images_dir: str, every_n: int, max_count: int) -> list:
    """
    Sort images by filename (numerically where possible) and pick every
    `every_n`-th image, returning up to `max_count` paths.
    """
    all_files = sorted(
        [f for f in os.listdir(images_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))],
        key=lambda x: int(Path(x).stem) if Path(x).stem.isdigit() else x,
    )
    selected = all_files[::every_n][:max_count]
    return [os.path.join(images_dir, f) for f in selected]


def draw_boxes(
    image: np.ndarray,
    boxes: list,
    title: str | None = None,
    show_confidence: bool = False,
) -> np.ndarray:
    """
    Draw bounding boxes on a copy of `image`.

    Each entry in `boxes` is a dict with keys:
        xmin, ymin, xmax, ymax, label   (and optionally 'conf')
    """
    img = image.copy()
    counts = defaultdict(int)

    for box in boxes:
        label = box["label"]
        info = CLASS_DISPLAY.get(label, {"label": label.upper(), "color": (200, 200, 200)})
        color = info["color"]
        display_label = info["label"]

        x1, y1 = int(box["xmin"]), int(box["ymin"])
        x2, y2 = int(box["xmax"]), int(box["ymax"])

        # Draw rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), color, BOX_THICKNESS)

        # Build text label
        text = display_label
        if show_confidence and "conf" in box:
            text += f" {box['conf']:.2f}"

        # Draw label background
        (tw, th), _ = cv2.getTextSize(text, FONT, FONT_SCALE, FONT_THICKNESS)
        cv2.rectangle(img, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(img, text, (x1 + 2, y1 - 4), FONT, FONT_SCALE, (255, 255, 255), FONT_THICKNESS)

        counts[label] += 1

    # Draw class counts in top-left corner
    y_offset = 25
    for cls_name in CLASS_NAMES:
        count = counts.get(cls_name, 0)
        info = CLASS_DISPLAY[cls_name]
        count_text = f"{info['label']}: {count}"
        cv2.putText(img, count_text, (10, y_offset), FONT, 0.6, info["color"], 2)
        y_offset += 25

    # Draw optional title
    if title:
        cv2.putText(img, title, (10, y_offset + 10), FONT, 0.7, (255, 255, 255), 2)

    return img


def create_comparison(
    image: np.ndarray,
    gt_boxes: list,
    pred_boxes: list,
    filename: str,
) -> np.ndarray:
    """
    Create a side-by-side image: ground truth (left) vs predictions (right).
    """
    gt_img = draw_boxes(image, gt_boxes, title="Ground Truth")
    pred_img = draw_boxes(image, pred_boxes, title="Predictions", show_confidence=True)

    # Add a thin white separator
    h = gt_img.shape[0]
    separator = np.full((h, 4, 3), 255, dtype=np.uint8)

    comparison = np.hstack([gt_img, separator, pred_img])

    # Add filename header
    header_h = 35
    header = np.zeros((header_h, comparison.shape[1], 3), dtype=np.uint8)
    cv2.putText(header, filename, (10, 24), FONT, 0.7, (255, 255, 255), 2)
    comparison = np.vstack([header, comparison])

    return comparison


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────

def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load model
    print(f"Loading model from: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)

    # Load ground truth
    print(f"Loading ground truth from: {GT_CSV_PATH}")
    gt_data = load_ground_truth(GT_CSV_PATH)

    # Select test images
    image_paths = select_test_images(TEST_IMAGES_DIR, PICK_EVERY_N, NUM_IMAGES)
    print(f"Selected {len(image_paths)} test images:\n")

    # Tracking for summary
    all_counts = []
    summary_rows = []

    for img_path in image_paths:
        filename = os.path.basename(img_path)
        stem = Path(filename).stem

        # Read image
        img = cv2.imread(img_path)
        if img is None:
            print(f"  ⚠ Could not read: {filename}, skipping.")
            continue

        # Run inference
        results = model.predict(
            source=img_path,
            imgsz=IMGSZ,
            conf=CONF_THRESH,
            iou=IOU_THRESH,
            verbose=False,
        )

        # Parse predictions
        pred_boxes = []
        pred_counts = defaultdict(int)
        for result in results:
            for box in result.boxes:
                cls_idx = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls_name = CLASS_NAMES[cls_idx]
                pred_boxes.append({
                    "xmin": x1, "ymin": y1,
                    "xmax": x2, "ymax": y2,
                    "label": cls_name,
                    "conf": conf,
                })
                pred_counts[cls_name] += 1

        total_det = sum(pred_counts.values())

        # ── 1. Save annotated prediction image ──
        annotated = draw_boxes(img, pred_boxes, show_confidence=True)
        det_path = os.path.join(OUTPUT_DIR, f"{stem}_detected.jpg")
        cv2.imwrite(det_path, annotated)

        # ── 2. Save side-by-side comparison ──
        gt_boxes = gt_data.get(filename, [])
        comparison = create_comparison(img, gt_boxes, pred_boxes, filename)
        cmp_path = os.path.join(OUTPUT_DIR, f"{stem}_comparison.jpg")
        cv2.imwrite(cmp_path, comparison)

        # ── 3. Track summary ──
        row = {
            "filename": filename,
            "rbc": pred_counts.get("rbc", 0),
            "pus": pred_counts.get("pus", 0),
            "ep": pred_counts.get("ep", 0),
            "total": total_det,
        }
        summary_rows.append(row)
        all_counts.append(total_det)

        print(f"  ✓ {filename:>10s}  |  RBC: {row['rbc']:>3}  Pus: {row['pus']:>3}  Ep: {row['ep']:>3}  |  Total: {total_det}")

    # ────────────────────────────────────────────────
    # Print summary
    # ────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("DETECTION SUMMARY")
    print("=" * 72)
    print(f"{'Image':<15} {'RBC':>5} {'Pus':>5} {'Ep':>5} {'Total':>6}")
    print("-" * 72)
    for row in summary_rows:
        print(f"{row['filename']:<15} {row['rbc']:>5} {row['pus']:>5} {row['ep']:>5} {row['total']:>6}")
    print("-" * 72)

    if all_counts:
        avg = sum(all_counts) / len(all_counts)
        total_rbc = sum(r["rbc"] for r in summary_rows)
        total_pus = sum(r["pus"] for r in summary_rows)
        total_ep  = sum(r["ep"]  for r in summary_rows)
        print(f"{'TOTAL':<15} {total_rbc:>5} {total_pus:>5} {total_ep:>5} {sum(all_counts):>6}")
        print(f"{'AVG/IMAGE':<15} {total_rbc/len(all_counts):>5.1f} {total_pus/len(all_counts):>5.1f} {total_ep/len(all_counts):>5.1f} {avg:>6.1f}")

    print(f"\nAnnotated images saved to: {OUTPUT_DIR}")
    print("Done!")


if __name__ == "__main__":
    main()
