"""
LabMind AI — Build YOLO Training Dataset from ErythrocytesIDB Masks
====================================================================

Converts the pre-annotated masks in erythrocytesIDB2/ and erythrocytesIDB3/
into YOLO-format bounding box annotations, then structures the data for
YOLO training.

Sources:
  - erythrocytesIDB2: 50 subfolders, each with source.jpg + per-class masks
  - erythrocytesIDB3: 30 subfolders, same structure
  - validation_smears: 10 images (pseudo-labeled via current YOLO)

Class mapping:
  0 = circular (normal RBCs)
  1 = elongated (sickle cells)
  2 = other (other deformed cells)

Output: ai-backend/yolo_dataset/
"""

import json
import os
import random
import shutil
import sys
import time
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import cv2
import numpy as np

# ── Reproducibility ──
random.seed(42)
np.random.seed(42)

# ── Paths ──
SCRIPT_DIR = Path(__file__).resolve().parent
IDB2_DIR = SCRIPT_DIR / "dataset_robust" / "raw" / "source_erythrocytesIDB" / "erythrocytesIDB2"
IDB3_DIR = SCRIPT_DIR / "dataset_robust" / "raw" / "source_erythrocytesIDB" / "erythrocytesIDB3"
VAL_SMEARS_DIR = SCRIPT_DIR / "validation_smears"
YOLO_MODEL_PATH = SCRIPT_DIR / "blood_ai_v2.pt"
OUTPUT_DIR = SCRIPT_DIR / "yolo_dataset"

# ── YOLO annotation parameters ──
MIN_CONTOUR_AREA = 100   # pixels^2 -- ignore noise dots
CLASS_MAP = {
    "mask-circular": 0,   # normal RBCs
    "mask-elongated": 1,  # sickle cells
    "mask-other": 2,      # other deformed
}
CLASS_NAMES = {0: "circular", 1: "elongated", 2: "other"}

# ── V1Provider-matching parameters for pseudo-labels ──
YOLO_CONF = 0.05
TILE_SIZE = 640
OVERLAP_RATIO = 0.25
NMS_IOU = 0.35
BORDER_SKIP = 5

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def separator(title: str):
    print(f"\n{'=' * 90}")
    print(f"  {title}")
    print('=' * 90)


# ══════════════════════════════════════════════════════════
#  STEP 1 — SCAN AND COUNT
# ══════════════════════════════════════════════════════════

def scan_idb_directory(idb_dir: Path, suffix: str) -> list[dict]:
    """Scan an IDB directory and verify each subfolder has required files."""
    if not idb_dir.exists():
        print(f"  [X] Directory not found: {idb_dir}")
        return []

    required_files = ["source.jpg", "mask.jpg", "mask-circular.jpg",
                      "mask-elongated.jpg", "mask-other.jpg"]
    subfolders = sorted([
        d for d in idb_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])

    results = []
    for sf in subfolders:
        info = {"name": sf.name, "path": str(sf), "valid": True, "missing": []}

        for req in required_files:
            fpath = sf / req
            if not fpath.exists():
                info["missing"].append(req)
                info["valid"] = False

        # Read source image dimensions if available
        src = sf / "source.jpg"
        if src.exists():
            img = cv2.imread(str(src))
            if img is not None:
                h, w = img.shape[:2]
                info["width"] = w
                info["height"] = h
            else:
                info["width"] = 0
                info["height"] = 0
                info["valid"] = False
                info["missing"].append("source.jpg (unreadable)")
        results.append(info)

    return results


def step1_scan():
    """Step 1: Scan and count all IDB subfolders."""
    separator("STEP 1 -- SCAN AND COUNT")

    scan_results = {}

    for name, idb_dir, suffix in [
        ("erythrocytesIDB2", IDB2_DIR, "erythrocytesIDB2"),
        ("erythrocytesIDB3", IDB3_DIR, "erythrocytesIDB3"),
    ]:
        print(f"\n  Scanning {name}: {idb_dir}")
        results = scan_idb_directory(idb_dir, suffix)
        scan_results[name] = results

        valid = [r for r in results if r["valid"]]
        invalid = [r for r in results if not r["valid"]]

        print(f"    Total subfolders: {len(results)}")
        print(f"    Valid (all files present): {len(valid)}")
        print(f"    Invalid / missing files: {len(invalid)}")

        if invalid:
            for inv in invalid:
                print(f"      [X] {inv['name']}: missing {inv['missing']}")

        if valid:
            widths = [r["width"] for r in valid if r.get("width")]
            heights = [r["height"] for r in valid if r.get("height")]
            if widths:
                print(f"    Image dimensions: {min(widths)}x{min(heights)} to "
                      f"{max(widths)}x{max(heights)}")
                print(f"    Average: {np.mean(widths):.0f}x{np.mean(heights):.0f}")

    return scan_results


# ══════════════════════════════════════════════════════════
#  STEP 2 — CONVERT MASKS TO YOLO ANNOTATIONS
# ══════════════════════════════════════════════════════════

def extract_boxes_from_mask(mask_path: Path, class_id: int,
                            img_w: int, img_h: int) -> list[tuple]:
    """
    Extract bounding boxes from a binary mask image.

    Returns list of (class_id, x_center_norm, y_center_norm, w_norm, h_norm).
    """
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return []

    # Binary threshold
    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_CONTOUR_AREA:
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        # Convert to YOLO normalized format
        x_center = (x + w / 2.0) / img_w
        y_center = (y + h / 2.0) / img_h
        w_norm = w / img_w
        h_norm = h / img_h

        # Clamp to [0, 1]
        x_center = max(0.0, min(1.0, x_center))
        y_center = max(0.0, min(1.0, y_center))
        w_norm = max(0.0, min(1.0, w_norm))
        h_norm = max(0.0, min(1.0, h_norm))

        boxes.append((class_id, x_center, y_center, w_norm, h_norm))

    return boxes


def convert_subfolder(sf_path: Path) -> tuple[list[tuple], int, int]:
    """
    Convert all masks in a subfolder to YOLO annotation lines.

    Returns (boxes, img_w, img_h).
    """
    src_path = sf_path / "source.jpg"
    img = cv2.imread(str(src_path))
    if img is None:
        return [], 0, 0

    img_h, img_w = img.shape[:2]
    all_boxes = []

    for mask_name, class_id in CLASS_MAP.items():
        mask_path = sf_path / f"{mask_name}.jpg"
        if mask_path.exists():
            boxes = extract_boxes_from_mask(mask_path, class_id, img_w, img_h)
            all_boxes.extend(boxes)

    return all_boxes, img_w, img_h


def step2_convert(scan_results: dict) -> dict:
    """Step 2: Convert all masks to YOLO annotations."""
    separator("STEP 2 -- CONVERT MASKS TO YOLO ANNOTATIONS")

    # Collect all annotation data
    # Structure: list of {"source_path", "annotation_lines", "name", "dataset"}
    all_data = []
    total_boxes = 0
    class_counts = {0: 0, 1: 0, 2: 0}

    for dataset_name, results in scan_results.items():
        valid = [r for r in results if r["valid"]]
        ds_boxes = 0

        for info in valid:
            sf_path = Path(info["path"])
            boxes, img_w, img_h = convert_subfolder(sf_path)

            # Count per class
            for box in boxes:
                class_counts[box[0]] += 1

            # Format annotation lines
            lines = []
            for cls_id, xc, yc, wn, hn in boxes:
                lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}")

            all_data.append({
                "source_path": str(sf_path / "source.jpg"),
                "annotation_lines": lines,
                "name": info["name"],
                "dataset": dataset_name,
                "img_w": img_w,
                "img_h": img_h,
                "box_count": len(boxes),
            })

            ds_boxes += len(boxes)
            total_boxes += len(boxes)

        print(f"\n  {dataset_name}: {len(valid)} images -> {ds_boxes} bounding boxes")

    print(f"\n  Total annotations: {total_boxes}")
    print(f"  Per-class counts:")
    for cls_id, count in class_counts.items():
        print(f"    {CLASS_NAMES[cls_id]}: {count}")

    avg_per_img = total_boxes / len(all_data) if all_data else 0
    print(f"  Average cells per image: {avg_per_img:.1f}")

    return {
        "all_data": all_data,
        "total_boxes": total_boxes,
        "class_counts": class_counts,
    }


# ══════════════════════════════════════════════════════════
#  STEP 3 — CREATE YOLO DATASET STRUCTURE
# ══════════════════════════════════════════════════════════

def step3_create_structure(conversion_data: dict) -> dict:
    """Step 3: Create YOLO dataset structure with train/val split."""
    separator("STEP 3 -- CREATE YOLO DATASET STRUCTURE")

    all_data = conversion_data["all_data"]

    # Create directory structure
    dirs = {
        "images_train": OUTPUT_DIR / "images" / "train",
        "images_val": OUTPUT_DIR / "images" / "val",
        "labels_train": OUTPUT_DIR / "labels" / "train",
        "labels_val": OUTPUT_DIR / "labels" / "val",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    # Shuffle and split 80/20
    indices = list(range(len(all_data)))
    random.shuffle(indices)
    split_idx = int(len(indices) * 0.8)
    train_indices = set(indices[:split_idx])

    train_count, val_count = 0, 0
    train_boxes, val_boxes = 0, 0

    for i, item in enumerate(all_data):
        is_train = i in train_indices
        split = "train" if is_train else "val"

        # Generate a clean filename
        safe_name = item["name"].replace(" ", "_")
        img_dst = dirs[f"images_{split}"] / f"{safe_name}.jpg"
        lbl_dst = dirs[f"labels_{split}"] / f"{safe_name}.txt"

        # Copy source image
        shutil.copy2(item["source_path"], str(img_dst))

        # Write YOLO annotation file
        with open(lbl_dst, "w") as f:
            f.write("\n".join(item["annotation_lines"]))
            if item["annotation_lines"]:
                f.write("\n")

        if is_train:
            train_count += 1
            train_boxes += item["box_count"]
        else:
            val_count += 1
            val_boxes += item["box_count"]

    print(f"\n  Train: {train_count} images, {train_boxes} annotations")
    print(f"  Val:   {val_count} images, {val_boxes} annotations")

    # Create data.yaml
    yaml_content = f"""path: {OUTPUT_DIR.as_posix()}
train: images/train
val: images/val
names:
  0: circular
  1: elongated
  2: other
nc: 3
"""
    yaml_path = OUTPUT_DIR / "data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
    print(f"  [OK] data.yaml created: {yaml_path}")

    return {
        "train_count": train_count,
        "val_count": val_count,
        "train_boxes": train_boxes,
        "val_boxes": val_boxes,
    }


# ══════════════════════════════════════════════════════════
#  STEP 4 — ADD VALIDATION SMEARS WITH PSEUDO-LABELS
# ══════════════════════════════════════════════════════════

def generate_pseudo_labels(yolo_model, img_path: Path) -> tuple[list[str], int]:
    """
    Run current YOLO on a validation smear to generate pseudo-labels.

    Uses the same tiling as V1Provider. Maps YOLO classes to our dataset classes:
      YOLO class 1 (rbc) -> class 0 (circular)
      YOLO class 3 (sickle) -> class 1 (elongated)
      YOLO class 2 (wbc) -> skip (not in our class set)
      YOLO class 0 (plt) -> skip (not in our class set)
    """
    import torch
    import torchvision

    img = cv2.imread(str(img_path))
    if img is None:
        return [], 0

    h_img, w_img = img.shape[:2]
    tile_size = TILE_SIZE
    overlap = int(tile_size * OVERLAP_RATIO)
    step = tile_size - overlap

    raw_boxes, raw_scores, raw_classes = [], [], []

    for y in range(0, h_img, step):
        for x in range(0, w_img, step):
            y_end = min(y + tile_size, h_img)
            x_end = min(x + tile_size, w_img)
            tile = img[y:y_end, x:x_end]
            if tile.shape[0] < 100 or tile.shape[1] < 100:
                continue

            results = yolo_model(tile, conf=YOLO_CONF, imgsz=tile_size, verbose=False)
            for result in results:
                boxes = result.boxes.xyxy.cpu().numpy()
                scores = result.boxes.conf.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy()
                for i, box in enumerate(boxes):
                    tx1, ty1, tx2, ty2 = map(int, box)
                    if (tx1 <= BORDER_SKIP or ty1 <= BORDER_SKIP or
                            tx2 >= tile.shape[1] - BORDER_SKIP or
                            ty2 >= tile.shape[0] - BORDER_SKIP):
                        continue
                    raw_boxes.append([x + tx1, y + ty1, x + tx2, y + ty2])
                    raw_scores.append(float(scores[i]))
                    raw_classes.append(int(classes[i]))

    # NMS
    if not raw_boxes:
        return [], 0

    gb = torch.tensor(raw_boxes, dtype=torch.float32)
    gs = torch.tensor(raw_scores, dtype=torch.float32)
    gc = torch.tensor(raw_classes, dtype=torch.int64)
    keep = torchvision.ops.batched_nms(gb, gs, gc, NMS_IOU)

    # Map YOLO classes to our dataset classes
    # Only keep rbc->circular and sickle->elongated; skip wbc/plt
    YOLO_TO_DATASET = {1: 0, 3: 1}  # rbc->circular, sickle->elongated

    lines = []
    for idx in keep:
        i = idx.item()
        yolo_cls = raw_classes[i]
        conf = raw_scores[i]

        # Only pseudo-label confident detections
        if conf < 0.15:
            continue

        ds_cls = YOLO_TO_DATASET.get(yolo_cls)
        if ds_cls is None:
            continue  # Skip WBC/PLT -- not in our class set

        x1, y1, x2, y2 = raw_boxes[i]
        xc = ((x1 + x2) / 2.0) / w_img
        yc = ((y1 + y2) / 2.0) / h_img
        wn = (x2 - x1) / w_img
        hn = (y2 - y1) / h_img

        # Clamp
        xc = max(0.0, min(1.0, xc))
        yc = max(0.0, min(1.0, yc))
        wn = max(0.0, min(1.0, wn))
        hn = max(0.0, min(1.0, hn))

        lines.append(f"{ds_cls} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}")

    return lines, len(lines)


def step4_add_validation_smears() -> dict:
    """Step 4: Add validation smears with YOLO pseudo-labels."""
    separator("STEP 4 -- ADD VALIDATION SMEARS WITH PSEUDO-LABELS")

    # Collect all validation smear images
    val_images = []
    for sub in ["normal", "sickle", "borderline"]:
        sub_dir = VAL_SMEARS_DIR / sub
        if sub_dir.exists():
            for f in sorted(sub_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                    val_images.append((f, sub))

    print(f"  Found {len(val_images)} validation smear images")

    if not val_images:
        print("  [!] No validation smears found. Skipping.")
        return {"added": 0, "total_pseudo_boxes": 0}

    # Load YOLO model
    if not YOLO_MODEL_PATH.exists():
        print(f"  [X] YOLO model not found at {YOLO_MODEL_PATH}")
        return {"added": 0, "total_pseudo_boxes": 0}

    print(f"  Loading YOLO model for pseudo-labeling...")
    from ultralytics import YOLO
    yolo_model = YOLO(str(YOLO_MODEL_PATH))
    print(f"  [OK] YOLO loaded.")

    # Add to TRAINING set (not val) — so YOLO learns from these images
    images_train = OUTPUT_DIR / "images" / "train"
    labels_train = OUTPUT_DIR / "labels" / "train"

    added = 0
    total_pseudo_boxes = 0

    for img_path, category in val_images:
        # Generate pseudo-labels
        lines, n_boxes = generate_pseudo_labels(yolo_model, img_path)

        # Clean filename with val_ prefix
        stem = img_path.stem.replace(".", "_")
        safe_name = f"val_{category}_{stem}"

        img_dst = images_train / f"{safe_name}.jpg"
        lbl_dst = labels_train / f"{safe_name}.txt"

        # Copy source image
        shutil.copy2(str(img_path), str(img_dst))

        # Write pseudo-label file
        with open(lbl_dst, "w") as f:
            f.write("\n".join(lines))
            if lines:
                f.write("\n")

        print(f"    >> {img_path.name} -> {safe_name}.jpg  "
              f"({n_boxes} pseudo-labels, category={category})")
        added += 1
        total_pseudo_boxes += n_boxes

    print(f"\n  [OK] Added {added} validation smears to training set")
    print(f"  [OK] Total pseudo-label boxes: {total_pseudo_boxes}")

    return {"added": added, "total_pseudo_boxes": total_pseudo_boxes}


# ══════════════════════════════════════════════════════════
#  STEP 5 — VERIFICATION REPORT
# ══════════════════════════════════════════════════════════

def step5_verification(scan_results: dict, conversion_data: dict,
                       split_data: dict, val_data: dict) -> dict:
    """Step 5: Generate verification report."""
    separator("STEP 5 -- VERIFICATION REPORT")

    # Count actual files in the dataset
    train_images = list((OUTPUT_DIR / "images" / "train").glob("*.jpg"))
    val_images = list((OUTPUT_DIR / "images" / "val").glob("*.jpg"))
    train_labels = list((OUTPUT_DIR / "labels" / "train").glob("*.txt"))
    val_labels = list((OUTPUT_DIR / "labels" / "val").glob("*.txt"))

    # Count total annotations and per-class
    total_boxes = 0
    class_counts = {0: 0, 1: 0, 2: 0}

    all_label_files = train_labels + val_labels
    for lbl_path in all_label_files:
        with open(lbl_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                cls_id = int(line.split()[0])
                total_boxes += 1
                if cls_id in class_counts:
                    class_counts[cls_id] += 1

    avg_cells = total_boxes / len(all_label_files) if all_label_files else 0

    print(f"\n  Total images: {len(train_images) + len(val_images)}")
    print(f"    Train images: {len(train_images)}")
    print(f"    Val images:   {len(val_images)}")
    print(f"    Train labels: {len(train_labels)}")
    print(f"    Val labels:   {len(val_labels)}")
    print(f"\n  Total annotations (bounding boxes): {total_boxes}")
    print(f"  Per-class counts:")
    for cls_id, count in class_counts.items():
        print(f"    {CLASS_NAMES[cls_id]}: {count}")
    print(f"  Average cells per image: {avg_cells:.1f}")

    # Show sample annotation files
    print(f"\n  Sample annotation files:")
    sample_labels = random.sample(all_label_files, min(2, len(all_label_files)))
    for lbl_path in sample_labels:
        print(f"\n    -- {lbl_path.name} --")
        with open(lbl_path, "r") as f:
            lines = f.readlines()
        for line in lines[:3]:
            parts = line.strip().split()
            if len(parts) == 5:
                cls_name = CLASS_NAMES.get(int(parts[0]), "?")
                print(f"      {line.strip()}  -> {cls_name}")
        if len(lines) > 3:
            print(f"      ... ({len(lines)} total lines)")

    # Build report
    report = {
        "dataset_path": str(OUTPUT_DIR),
        "total_images": len(train_images) + len(val_images),
        "train_images": len(train_images),
        "val_images": len(val_images),
        "total_annotations": total_boxes,
        "class_counts": {CLASS_NAMES[k]: v for k, v in class_counts.items()},
        "avg_cells_per_image": round(avg_cells, 1),
        "validation_smears_added": val_data.get("added", 0),
        "pseudo_label_boxes": val_data.get("total_pseudo_boxes", 0),
        "idb2_subfolders": len(scan_results.get("erythrocytesIDB2", [])),
        "idb3_subfolders": len(scan_results.get("erythrocytesIDB3", [])),
        "data_yaml": str(OUTPUT_DIR / "data.yaml"),
    }

    report_path = OUTPUT_DIR / "build_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n  [OK] Report saved to: {report_path}")

    return report


# ══════════════════════════════════════════════════════════
#  STEP 6 — VISUAL VERIFICATION
# ══════════════════════════════════════════════════════════

def step6_visual_verification():
    """Step 6: Create side-by-side visualizations for 5 random images."""
    separator("STEP 6 -- VISUAL VERIFICATION")

    # Collect all train+val images with their labels
    pairs = []
    for split in ["train", "val"]:
        img_dir = OUTPUT_DIR / "images" / split
        lbl_dir = OUTPUT_DIR / "labels" / split
        for img_path in sorted(img_dir.glob("*.jpg")):
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            if lbl_path.exists():
                pairs.append((img_path, lbl_path))

    if len(pairs) < 5:
        print(f"  [!] Only {len(pairs)} image-label pairs found.")
        sample = pairs
    else:
        sample = random.sample(pairs, 5)

    # Class colors (BGR)
    CLASS_COLORS = {
        0: (0, 255, 0),     # green = circular/normal
        1: (0, 0, 255),     # red   = elongated/sickle
        2: (255, 0, 0),     # blue  = other
    }

    panels = []

    for img_path, lbl_path in sample:
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        h_img, w_img = img.shape[:2]
        annotated = img.copy()

        # Parse annotations and draw boxes
        box_count = 0
        with open(lbl_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                cls_id = int(parts[0])
                xc, yc, wn, hn = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])

                # Convert back to pixel coords
                bw = int(wn * w_img)
                bh = int(hn * h_img)
                bx = int(xc * w_img - bw / 2)
                by = int(yc * h_img - bh / 2)

                color = CLASS_COLORS.get(cls_id, (200, 200, 200))
                cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh), color, 2)

                label = CLASS_NAMES.get(cls_id, "?")
                cv2.putText(annotated, label, (bx, by - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA)
                box_count += 1

        # Add title text
        cv2.putText(img, f"Original: {img_path.stem}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(annotated, f"Annotated: {box_count} boxes",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Side-by-side
        combined = np.hstack([img, annotated])
        panels.append(combined)
        print(f"  >> {img_path.stem}: {box_count} boxes drawn")

    if not panels:
        print("  [X] No panels to assemble.")
        return

    # Normalize widths for vertical stacking
    max_w = max(p.shape[1] for p in panels)
    normalized = []
    for p in panels:
        if p.shape[1] < max_w:
            pad = np.zeros((p.shape[0], max_w - p.shape[1], 3), dtype=np.uint8)
            p = np.hstack([p, pad])
        normalized.append(p)

    # Add a small gap between rows
    gap = np.zeros((8, max_w, 3), dtype=np.uint8)
    stacked = []
    for i, panel in enumerate(normalized):
        stacked.append(panel)
        if i < len(normalized) - 1:
            stacked.append(gap)

    final = np.vstack(stacked)

    # Add legend at the top
    legend_h = 40
    legend = np.zeros((legend_h, max_w, 3), dtype=np.uint8)
    x_pos = 10
    for cls_id, color in CLASS_COLORS.items():
        label = CLASS_NAMES.get(cls_id, "?")
        cv2.rectangle(legend, (x_pos, 10), (x_pos + 20, 30), color, -1)
        cv2.putText(legend, label, (x_pos + 25, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        x_pos += 150

    final = np.vstack([legend, final])

    out_path = OUTPUT_DIR / "annotation_verification.png"
    cv2.imwrite(str(out_path), final)
    print(f"\n  [OK] Verification image saved: {out_path}")


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    separator("LabMind AI -- Build YOLO Training Dataset from ErythrocytesIDB Masks")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"  Min contour area: {MIN_CONTOUR_AREA} px^2")
    print(f"  Class mapping: {CLASS_NAMES}")
    t0 = time.time()

    # Step 1
    scan_results = step1_scan()

    # Step 2
    conversion_data = step2_convert(scan_results)

    # Step 3
    split_data = step3_create_structure(conversion_data)

    # Step 4
    val_data = step4_add_validation_smears()

    # Step 5
    report = step5_verification(scan_results, conversion_data, split_data, val_data)

    # Step 6
    step6_visual_verification()

    elapsed = time.time() - t0
    separator("BUILD COMPLETE")
    print(f"\n  Total time: {elapsed:.1f}s")
    print(f"  Dataset ready at: {OUTPUT_DIR}")
    print(f"  data.yaml: {OUTPUT_DIR / 'data.yaml'}")
    print(f"  To train: yolo detect train data={OUTPUT_DIR / 'data.yaml'} ...")
    print()


if __name__ == "__main__":
    main()
