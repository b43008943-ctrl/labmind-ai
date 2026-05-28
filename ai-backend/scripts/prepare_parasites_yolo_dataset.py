"""
LabMind AI — Chula-ParasiteEgg-11 → YOLO Dataset Converter
===========================================================

Converts the Chula-ParasiteEgg-11 dataset from COCO annotation format
to YOLO format for training a YOLOv8 parasite egg detector.

Source: Chula-ParasiteEgg-11 (11,000 training images, 11 classes)

Strategy:
    - Selects a balanced subset per class for CPU-friendly training
    - 450 images/class → TRAIN  (4,950 total)
    - 50 images/class  → VAL    (  550 total)
    - Remaining 500/class stay unused for future expansion
    - Test images copied as-is (no labels available)

Usage:
    python scripts/prepare_parasites_yolo_dataset.py

Output:
    dataset_parasites/yolo_dataset/
    ├── images/{train,val,test}/
    ├── labels/{train,val,test}/
    └── data.yaml
"""

from __future__ import annotations

import json
import random
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

# ────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────

RANDOM_SEED = 42

TRAIN_PER_CLASS = 450
VAL_PER_CLASS = 50

# Paths — all relative to the ai-backend directory
BASE_DIR = Path(__file__).resolve().parent.parent  # ai-backend/

SOURCE_DIR = (
    BASE_DIR / "dataset_parasites" / "source_chula"
    / "Chula-ParasiteEgg-11" / "Chula-ParasiteEgg-11" / "Chula-ParasiteEgg-11"
)
SOURCE_IMAGES_DIR = SOURCE_DIR / "data"
SOURCE_LABELS_JSON = SOURCE_DIR / "labels.json"

TEST_SOURCE_DIR = (
    BASE_DIR / "dataset_parasites" / "source_chula"
    / "Chula-ParasiteEgg-11_test" / "test" / "data"
)

OUTPUT_DIR = BASE_DIR / "dataset_parasites" / "yolo_dataset"

# YOLO class mapping — IDs kept identical to COCO source
CLASS_NAMES = [
    "Ascaris_lumbricoides",       # 0
    "Capillaria_philippinensis",  # 1
    "Enterobius_vermicularis",    # 2
    "Fasciolopsis_buski",         # 3
    "Hookworm",                   # 4
    "Hymenolepis_diminuta",       # 5
    "Hymenolepis_nana",           # 6
    "Opisthorchis_viverrine",     # 7
    "Paragonimus_spp",            # 8
    "Taenia_spp",                 # 9
    "Trichuris_trichiura",        # 10
]

# Map from COCO category name → YOLO class ID
# (handles the dataset's naming quirks: "Hookworm egg" → 4, etc.)
COCO_NAME_TO_CLASS_ID = {
    "Ascaris lumbricoides": 0,
    "Capillaria philippinensis": 1,
    "Enterobius vermicularis": 2,
    "Fasciolopsis buski": 3,
    "Hookworm egg": 4,
    "Hymenolepis diminuta": 5,
    "Hymenolepis nana": 6,
    "Opisthorchis viverrine": 7,
    "Paragonimus spp": 8,
    "Taenia spp. egg": 9,
    "Trichuris trichiura": 10,
}

# ────────────────────────────────────────────────────────────────────
# COCO → YOLO conversion helpers
# ────────────────────────────────────────────────────────────────────


def coco_bbox_to_yolo(
    bbox: list[float],
    img_width: int,
    img_height: int,
) -> tuple[float, float, float, float]:
    """
    Convert a single COCO bbox [x, y, w, h] (top-left, absolute pixels)
    to YOLO format [x_center, y_center, w, h] (normalised 0–1).

    Values are clamped to [0.0, 1.0].
    """
    x, y, w, h = bbox

    x_center = (x + w / 2.0) / img_width
    y_center = (y + h / 2.0) / img_height
    w_norm = w / img_width
    h_norm = h / img_height

    # Clamp to valid range
    x_center = max(0.0, min(1.0, x_center))
    y_center = max(0.0, min(1.0, y_center))
    w_norm = max(0.0, min(1.0, w_norm))
    h_norm = max(0.0, min(1.0, h_norm))

    return x_center, y_center, w_norm, h_norm


def determine_class_from_filename(filename: str) -> int | None:
    """
    Infer the YOLO class ID from a training image filename.

    Filenames follow the pattern:  "Hymenolepis nana_0001.jpg"
    We match the prefix (before _NNNN.jpg) against COCO category names.
    """
    # Strip extension
    stem = Path(filename).stem  # e.g. "Hymenolepis nana_0001"

    # Remove trailing _NNNN
    parts = stem.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        class_part = parts[0]  # e.g. "Hymenolepis nana"
    else:
        class_part = stem

    return COCO_NAME_TO_CLASS_ID.get(class_part)


# ────────────────────────────────────────────────────────────────────
# Main pipeline
# ────────────────────────────────────────────────────────────────────


def main() -> None:
    print("=" * 72)
    print("  CHULA-PARASITEEGG-11  ->  YOLO DATASET CONVERTER")
    print("=" * 72)
    t_start = time.time()

    # ──────────── STEP 1: Validate source paths ────────────
    print("\n[1/7] Validating source paths...")

    if not SOURCE_IMAGES_DIR.is_dir():
        print(f"  ERROR: Source images dir not found: {SOURCE_IMAGES_DIR}")
        sys.exit(1)

    # Try labels.json, fall back to "labels" (no extension)
    labels_path = SOURCE_LABELS_JSON
    if not labels_path.is_file():
        labels_path = SOURCE_DIR / "labels"
        if not labels_path.is_file():
            print(f"  ERROR: Labels file not found in {SOURCE_DIR}")
            sys.exit(1)
    print(f"  Images dir : {SOURCE_IMAGES_DIR}")
    print(f"  Labels file: {labels_path}")
    print(f"  Test dir   : {TEST_SOURCE_DIR} (exists={TEST_SOURCE_DIR.is_dir()})")

    # ──────────── STEP 2: Load & parse COCO JSON ────────────
    print("\n[2/7] Loading COCO annotations...")

    with open(labels_path, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    categories = coco_data["categories"]
    images_list = coco_data["images"]
    annotations = coco_data["annotations"]

    print(f"  Categories  : {len(categories)}")
    print(f"  Images      : {len(images_list)}")
    print(f"  Annotations : {len(annotations)}")

    # Build COCO category_id → YOLO class_id map
    coco_cat_to_yolo = {}
    for cat in categories:
        coco_cat_id = cat["id"]
        coco_name = cat["name"]
        yolo_id = COCO_NAME_TO_CLASS_ID.get(coco_name)
        if yolo_id is not None:
            coco_cat_to_yolo[coco_cat_id] = yolo_id
        else:
            print(f"  WARNING: Unknown category '{coco_name}' (id={coco_cat_id})")

    print(f"  Mapped {len(coco_cat_to_yolo)}/{ len(categories)} categories to YOLO IDs")

    # Build image_id → image_info lookup
    image_id_to_info: dict[int, dict] = {}
    for img in images_list:
        image_id_to_info[img["id"]] = img

    # Build image_id → list of YOLO annotation lines
    image_id_to_labels: dict[int, list[str]] = defaultdict(list)
    skipped_annotations = 0
    for ann in annotations:
        cat_id = ann["category_id"]
        yolo_class = coco_cat_to_yolo.get(cat_id)
        if yolo_class is None:
            skipped_annotations += 1
            continue

        img_info = image_id_to_info.get(ann["image_id"])
        if img_info is None:
            skipped_annotations += 1
            continue

        xc, yc, wn, hn = coco_bbox_to_yolo(
            ann["bbox"], img_info["width"], img_info["height"]
        )
        label_line = f"{yolo_class} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}"
        image_id_to_labels[ann["image_id"]].append(label_line)

    if skipped_annotations:
        print(f"  WARNING: Skipped {skipped_annotations} annotations (unknown cat/image)")

    # Count multi-egg images
    multi_egg = sum(1 for v in image_id_to_labels.values() if len(v) > 1)
    print(f"  Images with annotations: {len(image_id_to_labels)}")
    print(f"  Images with multi-eggs : {multi_egg}")

    # ──────────── STEP 3: Group images by class ────────────
    print("\n[3/7] Grouping images by class from filenames...")

    class_to_image_ids: dict[int, list[int]] = defaultdict(list)
    unclassified = []

    for img in images_list:
        cls = determine_class_from_filename(img["file_name"])
        if cls is not None:
            class_to_image_ids[cls].append(img["id"])
        else:
            unclassified.append(img["file_name"])

    if unclassified:
        print(f"  WARNING: {len(unclassified)} images could not be classified:")
        for fn in unclassified[:5]:
            print(f"    - {fn}")

    for cls_id in range(len(CLASS_NAMES)):
        count = len(class_to_image_ids.get(cls_id, []))
        print(f"  Class {cls_id:2d} ({CLASS_NAMES[cls_id]:30s}): {count:5d} images")

    # ──────────── STEP 4: Balanced split ────────────
    print(f"\n[4/7] Splitting: {TRAIN_PER_CLASS}/class train, {VAL_PER_CLASS}/class val (seed={RANDOM_SEED})...")

    random.seed(RANDOM_SEED)

    train_image_ids: list[int] = []
    val_image_ids: list[int] = []

    for cls_id in range(len(CLASS_NAMES)):
        ids = class_to_image_ids.get(cls_id, [])
        if len(ids) < TRAIN_PER_CLASS + VAL_PER_CLASS:
            print(f"  WARNING: Class {cls_id} has only {len(ids)} images "
                  f"(need {TRAIN_PER_CLASS + VAL_PER_CLASS}). Using all available.")
            random.shuffle(ids)
            split_point = int(len(ids) * 0.9)
            train_image_ids.extend(ids[:split_point])
            val_image_ids.extend(ids[split_point:])
        else:
            random.shuffle(ids)
            train_image_ids.extend(ids[:TRAIN_PER_CLASS])
            val_image_ids.extend(ids[TRAIN_PER_CLASS:TRAIN_PER_CLASS + VAL_PER_CLASS])

    print(f"  Train images: {len(train_image_ids)}")
    print(f"  Val images  : {len(val_image_ids)}")

    # ──────────── STEP 5: Create output directories ────────────
    print("\n[5/7] Creating output directory structure...")

    # Clean existing output
    if OUTPUT_DIR.exists():
        print(f"  Removing existing output dir: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)

    for split in ("train", "val", "test"):
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    print(f"  Created: {OUTPUT_DIR}")

    # ──────────── STEP 6: Copy images & write labels ────────────
    print("\n[6/7] Copying images and writing YOLO label files...")

    errors: list[str] = []
    no_annotation_count = {"train": 0, "val": 0}

    # Track per-class annotation counts per split
    class_counts: dict[str, dict[int, int]] = {
        "train": defaultdict(int),
        "val": defaultdict(int),
    }

    def process_split(
        split_name: str,
        image_ids: list[int],
    ) -> int:
        """Copy images and write labels for a split. Returns count of processed files."""
        copied = 0
        for img_id in image_ids:
            img_info = image_id_to_info.get(img_id)
            if img_info is None:
                errors.append(f"Image ID {img_id} not found in COCO data")
                continue

            filename = img_info["file_name"]
            src_path = SOURCE_IMAGES_DIR / filename
            if not src_path.is_file():
                errors.append(f"Missing source file: {src_path}")
                continue

            # Copy image
            dst_image_path = OUTPUT_DIR / "images" / split_name / filename
            shutil.copy2(src_path, dst_image_path)

            # Write label .txt (same name, different extension)
            label_filename = Path(filename).stem + ".txt"
            dst_label_path = OUTPUT_DIR / "labels" / split_name / label_filename

            label_lines = image_id_to_labels.get(img_id, [])
            if not label_lines:
                # Empty label file for images with no annotations
                dst_label_path.write_text("")
                no_annotation_count[split_name] += 1
            else:
                dst_label_path.write_text("\n".join(label_lines) + "\n")
                # Count annotations per class
                for line in label_lines:
                    cls = int(line.split()[0])
                    class_counts[split_name][cls] += 1

            copied += 1

        return copied

    train_copied = process_split("train", train_image_ids)
    val_copied = process_split("val", val_image_ids)

    print(f"  Train: {train_copied} images copied")
    print(f"  Val  : {val_copied} images copied")

    # ──────── Copy test images (no labels available) ────────
    test_copied = 0
    if TEST_SOURCE_DIR.is_dir():
        test_files = sorted(TEST_SOURCE_DIR.glob("*.jpg"))
        print(f"  Test : {len(test_files)} source images found")
        for src in test_files:
            dst = OUTPUT_DIR / "images" / "test" / src.name
            shutil.copy2(src, dst)
            # Write empty label file (no ground truth available)
            label_path = OUTPUT_DIR / "labels" / "test" / (src.stem + ".txt")
            label_path.write_text("")
            test_copied += 1
        print(f"  Test : {test_copied} images copied (no labels -- empty .txt created)")
    else:
        print("  Test : SKIPPED (test source directory not found)")

    # ──────────── STEP 7: Write data.yaml ────────────
    print("\n[7/7] Writing data.yaml...")

    yaml_path = OUTPUT_DIR / "data.yaml"
    yaml_content = f"""# Chula-ParasiteEgg-11 — YOLO Dataset Configuration
# Auto-generated by prepare_parasites_yolo_dataset.py
# {len(CLASS_NAMES)} classes, {train_copied} train, {val_copied} val, {test_copied} test images

path: {OUTPUT_DIR.as_posix()}
train: images/train
val: images/val
test: images/test

nc: {len(CLASS_NAMES)}
names: {CLASS_NAMES}
"""
    yaml_path.write_text(yaml_content, encoding="utf-8")
    print(f"  Written: {yaml_path}")

    # ──────────── Summary Report ────────────
    elapsed = time.time() - t_start

    print("\n" + "=" * 72)
    print("  SUMMARY REPORT")
    print("=" * 72)

    print(f"\n  Output directory: {OUTPUT_DIR}")
    print(f"  Time elapsed    : {elapsed:.1f}s")

    print(f"")
    print(f"  +---------------------------------------------------+")
    print(f"  | Split   | Images | Annotations | No-annot imgs  |")
    print(f"  +---------------------------------------------------+")
    print(f"  | Train   | {train_copied:6d} | {sum(class_counts['train'].values()):11d} | {no_annotation_count['train']:14d} |")
    print(f"  | Val     | {val_copied:6d} | {sum(class_counts['val'].values()):11d} | {no_annotation_count['val']:14d} |")
    print(f"  | Test    | {test_copied:6d} |         N/A |            N/A |")
    print(f"  +---------------------------------------------------+")

    print(f"\n  Annotations per class:")
    print(f"  {'Class':<35s} {'Train':>7s} {'Val':>7s}")
    print(f"  {'-' * 35} {'-' * 7} {'-' * 7}")
    for cls_id, name in enumerate(CLASS_NAMES):
        t_count = class_counts["train"].get(cls_id, 0)
        v_count = class_counts["val"].get(cls_id, 0)
        print(f"  {cls_id:2d}. {name:<31s} {t_count:7d} {v_count:7d}")
    print(f"  {'-' * 35} {'-' * 7} {'-' * 7}")
    print(f"  {'TOTAL':<35s} {sum(class_counts['train'].values()):7d} {sum(class_counts['val'].values()):7d}")

    # Errors
    if errors:
        print(f"\n  [!] ERRORS ({len(errors)}):")
        for err in errors[:20]:
            print(f"    - {err}")
        if len(errors) > 20:
            print(f"    ... and {len(errors) - 20} more")
    else:
        print(f"\n  [OK] No errors encountered")

    # Sample YOLO label content
    print(f"\n  Sample YOLO label (first train file):")
    sample_labels = sorted((OUTPUT_DIR / "labels" / "train").glob("*.txt"))
    for lf in sample_labels[:3]:
        content = lf.read_text().strip()
        if content:
            print(f"    {lf.name}:")
            for line in content.split("\n")[:3]:
                parts = line.split()
                cls_name = CLASS_NAMES[int(parts[0])] if len(parts) >= 5 else "?"
                print(f"      {line}  # {cls_name}")
            break

    print(f"\n  data.yaml path: {yaml_path}")
    print(f"\n{'=' * 72}")
    print("  DATASET PREPARATION COMPLETE")
    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    main()
