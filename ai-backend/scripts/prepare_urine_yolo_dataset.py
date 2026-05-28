"""
Prepare UMID Urine Microscopic Dataset for YOLO training.

Reads train.csv / val.csv / test.csv from source_umid/, converts bounding-box
and point annotations into YOLO normalized format, copies images into the
standard YOLO directory layout, and generates data.yaml.

YOLO class mapping (user-defined):
    0: rbc
    1: pus  (WBC / pus cells)
    2: ep   (epithelial cells)

Point annotations are expanded into pseudo bounding boxes using empirically
chosen median sizes per class.
"""

import csv
import shutil
import sys
from collections import defaultdict
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────
IMG_W, IMG_H = 1280, 720

# Label → YOLO class id
LABEL_MAP = {
    "rbc": 0, "point-rbc": 0,
    "pus": 1, "point-pus": 1,
    "ep":  2, "point-ep":  2,
}

# Default pseudo-box sizes (px) for point annotations
POINT_BOX_SIZES = {
    "point-rbc": (40, 40),
    "point-pus": (55, 55),
    "point-ep":  (190, 190),
}

SOURCE_DIR = Path(__file__).resolve().parent.parent / "dataset_urine" / "source_umid"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "dataset_urine" / "yolo_dataset"
IMAGES_DIR = SOURCE_DIR / "images"

SPLITS = {
    "train": SOURCE_DIR / "train.csv",
    "val":   SOURCE_DIR / "val.csv",
    "test":  SOURCE_DIR / "test.csv",
}


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def is_point_annotation(label: str) -> bool:
    return label.startswith("point-")


def to_yolo(xmin, ymin, xmax, ymax):
    """Convert absolute pixel coords to YOLO normalised (cx, cy, w, h)."""
    cx = (xmin + xmax) / 2.0 / IMG_W
    cy = (ymin + ymax) / 2.0 / IMG_H
    w  = (xmax - xmin) / IMG_W
    h  = (ymax - ymin) / IMG_H
    # Clamp to [0, 1]
    cx = clamp(cx, 0.0, 1.0)
    cy = clamp(cy, 0.0, 1.0)
    w  = clamp(w,  0.0, 1.0)
    h  = clamp(h,  0.0, 1.0)
    return cx, cy, w, h


def expand_point(px, py, label):
    """Expand a point annotation to a clamped pseudo bounding box."""
    bw, bh = POINT_BOX_SIZES[label]
    half_w, half_h = bw / 2.0, bh / 2.0
    xmin = clamp(px - half_w, 0, IMG_W)
    ymin = clamp(py - half_h, 0, IMG_H)
    xmax = clamp(px + half_w, 0, IMG_W)
    ymax = clamp(py + half_h, 0, IMG_H)
    return xmin, ymin, xmax, ymax


def read_csv(csv_path: Path):
    """
    Read a UMID CSV and return {image_name: [(class_id, cx, cy, w, h), ...]}.
    Also return counters for the summary report.
    """
    annotations = defaultdict(list)
    stats = {
        "bbox": defaultdict(int),
        "point": defaultdict(int),
        "skipped_missed": 0,
        "skipped_unknown": 0,
        "total_rows": 0,
    }

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["total_rows"] += 1
            img_name = row["image"].strip()
            label = row["label"].strip()

            if label == "missedlabel":
                stats["skipped_missed"] += 1
                continue

            if label not in LABEL_MAP:
                stats["skipped_unknown"] += 1
                continue

            class_id = LABEL_MAP[label]
            xmin = float(row["xmin"])
            ymin = float(row["ymin"])
            xmax = float(row["xmax"])
            ymax = float(row["ymax"])

            if is_point_annotation(label):
                # Point: xmin==xmax, ymin==ymax — expand to pseudo-box
                xmin, ymin, xmax, ymax = expand_point(xmin, ymin, label)
                stats["point"][label] += 1
            else:
                stats["bbox"][label] += 1

            cx, cy, w, h = to_yolo(xmin, ymin, xmax, ymax)
            # Skip degenerate boxes (zero-area after clamping at edges)
            if w < 1e-6 or h < 1e-6:
                continue

            annotations[img_name].append((class_id, cx, cy, w, h))

    return annotations, stats


def main():
    print("=" * 65)
    print("  UMID Urine -> YOLO Dataset Preparation")
    print("=" * 65)

    # Verify source exists
    if not IMAGES_DIR.exists():
        print(f"ERROR: Image directory not found: {IMAGES_DIR}")
        sys.exit(1)

    available_images = {p.name for p in IMAGES_DIR.glob("*.jpg")}
    print(f"Source images found: {len(available_images)}")

    # Create output structure
    for split in SPLITS:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    all_stats = {}
    sample_label_lines = None
    missing_images = []

    for split_name, csv_path in SPLITS.items():
        print(f"\n-- Processing split: {split_name} ({csv_path.name}) --")
        if not csv_path.exists():
            print(f"  WARNING: CSV not found, skipping: {csv_path}")
            continue

        annotations, stats = read_csv(csv_path)
        all_stats[split_name] = stats

        images_copied = 0
        labels_written = 0

        for img_name, annots in sorted(annotations.items()):
            # Verify image exists
            src_img = IMAGES_DIR / img_name
            if not src_img.exists():
                missing_images.append((split_name, img_name))
                continue

            # Copy image
            dst_img = OUTPUT_DIR / "images" / split_name / img_name
            if not dst_img.exists():
                shutil.copy2(src_img, dst_img)
            images_copied += 1

            # Write label file
            label_file = OUTPUT_DIR / "labels" / split_name / (Path(img_name).stem + ".txt")
            with open(label_file, "w", encoding="utf-8") as lf:
                for cls_id, cx, cy, w, h in annots:
                    lf.write(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
            labels_written += 1

            # Capture sample for report
            if sample_label_lines is None and annots:
                sample_label_lines = (
                    img_name,
                    [f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}" for c, x, y, w, h in annots[:3]],
                )

        # Handle images that appear in no annotations (create empty label files)
        # — not needed here since we iterate from annotations

        print(f"  Images copied : {images_copied}")
        print(f"  Labels written: {labels_written}")

    # ── Generate data.yaml ─────────────────────────────────────────────────
    yaml_path = OUTPUT_DIR / "data.yaml"
    yaml_content = (
        f"path: {OUTPUT_DIR.as_posix()}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"test: images/test\n"
        f"nc: 3\n"
        f"names: ['rbc', 'pus', 'ep']\n"
    )
    yaml_path.write_text(yaml_content, encoding="utf-8")
    print(f"\nGenerated {yaml_path}")

    # ── Summary Report ─────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  SUMMARY REPORT")
    print("=" * 65)

    class_names = {0: "rbc", 1: "pus", 2: "ep"}

    for split_name in ["train", "val", "test"]:
        if split_name not in all_stats:
            continue
        s = all_stats[split_name]
        print(f"\n  [{split_name.upper()}]")
        print(f"    Total CSV rows     : {s['total_rows']}")
        print(f"    Skipped (missed)   : {s['skipped_missed']}")
        print(f"    Skipped (unknown)  : {s['skipped_unknown']}")
        print(f"    Bounding-box annots:")
        for label, count in sorted(s["bbox"].items()):
            print(f"      {label:>10}: {count}")
        print(f"    Point->box annots :")
        for label, count in sorted(s["point"].items()):
            print(f"      {label:>10}: {count}")

    if missing_images:
        print(f"\n  WARNING: Missing images ({len(missing_images)}):")
        for split, name in missing_images[:10]:
            print(f"    [{split}] {name}")
        if len(missing_images) > 10:
            print(f"    ... and {len(missing_images) - 10} more")

    if sample_label_lines:
        img_name, lines = sample_label_lines
        print(f"\n  Sample label ({img_name}):")
        for line in lines:
            print(f"    {line}")

    # Count output files
    for split_name in ["train", "val", "test"]:
        img_count = len(list((OUTPUT_DIR / "images" / split_name).glob("*.jpg")))
        lbl_count = len(list((OUTPUT_DIR / "labels" / split_name).glob("*.txt")))
        print(f"\n  Output [{split_name}]: {img_count} images, {lbl_count} label files")

    print("\n" + "=" * 65)
    print("  DONE — Dataset ready at:", OUTPUT_DIR)
    print("=" * 65)


if __name__ == "__main__":
    main()
