"""
LabMind AI — Augment & Split
==============================
1. Extract individual cells from Kaggle full-field smear images
2. Smart augmentation to reach 500/class minimum
3. Train/val/test split (70/15/15) with augmentation-aware grouping
4. Visual grid + report

Usage:
    python augment_and_split.py
"""

import json
import math
import os
import random
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    print("[ERROR] OpenCV + NumPy required")
    sys.exit(1)

random.seed(42)
np.random.seed(42)

BASE = Path(__file__).resolve().parent
KAGGLE_SCD = BASE / "dataset_robust" / "raw" / "source_kaggle_scd"
DATASET_CLEAN = BASE / "dataset_clean"
SPLITS_DIR = DATASET_CLEAN / "splits"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
TARGET = (128, 128)
JPG_Q = 95

# Extraction params
CONTOUR_AREA_MIN = 500
CONTOUR_AREA_MAX = 10000
PAD_PX = 10
MAX_CELLS_PER_IMAGE_NEG = 50
MAX_CELLS_PER_IMAGE_POS = 30
NORMAL_CAP = 600
SICKLE_CAP = 400

# Augmentation
SICKLE_TARGET = 500
MIN_RATIO = 1.0
MAX_RATIO = 1.5


def is_img(p): return p.is_file() and p.suffix.lower() in IMAGE_EXTS

def count_cls(cls):
    d = DATASET_CLEAN / cls
    return sum(1 for f in d.iterdir() if is_img(f)) if d.exists() else 0


# ═══════════════════════════════════════════════════════════════
#  STEP 1 — Extract cells from Kaggle full-field images
# ═══════════════════════════════════════════════════════════════

def extract_cells_from_smear(img_path, out_dir, prefix, max_per_img, current_count, cap):
    """Extract individual cell crops from a full-field blood smear image."""
    img = cv2.imread(str(img_path))
    if img is None:
        return 0

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Adaptive thresholding works better on stained smear images
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Morphological cleanup
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    extracted = 0
    stem = img_path.stem

    for i, cnt in enumerate(contours):
        if current_count + extracted >= cap:
            break
        if extracted >= max_per_img:
            break

        area = cv2.contourArea(cnt)
        if area < CONTOUR_AREA_MIN or area > CONTOUR_AREA_MAX:
            continue

        x, y, cw, ch = cv2.boundingRect(cnt)

        # Skip very elongated contours that are likely artifacts
        ar = max(cw, ch) / (min(cw, ch) + 1e-5)
        if ar > 5.0:
            continue

        # Add padding
        x1 = max(0, x - PAD_PX)
        y1 = max(0, y - PAD_PX)
        x2 = min(w, x + cw + PAD_PX)
        y2 = min(h, y + ch + PAD_PX)

        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        # Resize to 128×128
        interp = cv2.INTER_AREA if crop.shape[1] > TARGET[0] else cv2.INTER_CUBIC
        resized = cv2.resize(crop, TARGET, interpolation=interp)

        out_name = f"{prefix}{stem}_{i:03d}.jpg"
        out_path = out_dir / out_name
        cv2.imwrite(str(out_path), resized, [cv2.IMWRITE_JPEG_QUALITY, JPG_Q])
        extracted += 1

    return extracted


def step1_extract_kaggle():
    print("\n" + "=" * 70)
    print("  STEP 1: Extract cells from Kaggle full-field smears")
    print("=" * 70)

    total_neg = 0
    total_pos = 0

    # Look for Kaggle images — handle various folder structures
    # Structure: source_kaggle_scd/Positive/Labelled/*.jpg and Unlabelled/*.jpg
    # No Negative folder exists in this dataset

    pos_dirs = []
    neg_dirs = []

    # Check for Negative folder
    neg_path = KAGGLE_SCD / "Negative"
    if neg_path.exists():
        neg_dirs.append(neg_path)
        # Also check subdirectories
        for sub in neg_path.iterdir():
            if sub.is_dir():
                neg_dirs.append(sub)

    # Check for Positive folder
    pos_path = KAGGLE_SCD / "Positive"
    if pos_path.exists():
        # Check for images directly
        if any(is_img(f) for f in pos_path.iterdir() if f.is_file()):
            pos_dirs.append(pos_path)
        # Check subdirectories (Labelled, Unlabelled)
        for sub in pos_path.iterdir():
            if sub.is_dir():
                pos_dirs.append(sub)

    # Extract from Negative (normal) smears
    if neg_dirs:
        current_normal = count_cls("normal")
        print(f"\n  Negative dirs found: {[d.name for d in neg_dirs]}")
        print(f"  Current normal count: {current_normal}, cap: {NORMAL_CAP}")

        for d in neg_dirs:
            imgs = sorted([f for f in d.iterdir() if is_img(f)])
            for img_path in imgs:
                if count_cls("normal") >= NORMAL_CAP:
                    break
                n = extract_cells_from_smear(
                    img_path, DATASET_CLEAN / "normal",
                    "kaggle_neg_", MAX_CELLS_PER_IMAGE_NEG,
                    count_cls("normal"), NORMAL_CAP)
                total_neg += n
            if count_cls("normal") >= NORMAL_CAP:
                break

        print(f"  Extracted {total_neg} normal cells from Negative smears")
    else:
        print(f"\n  No Negative/ folder found — skipping normal extraction from Kaggle")

    # Extract from Positive (sickle) smears
    if pos_dirs:
        current_sickle = count_cls("sickle")
        print(f"\n  Positive dirs found: {[d.name for d in pos_dirs]}")
        print(f"  Current sickle count: {current_sickle}, cap: {SICKLE_CAP}")

        for d in pos_dirs:
            imgs = sorted([f for f in d.iterdir() if is_img(f)])
            print(f"    Scanning {d.name}/: {len(imgs)} images")
            for j, img_path in enumerate(imgs):
                if count_cls("sickle") >= SICKLE_CAP:
                    break
                n = extract_cells_from_smear(
                    img_path, DATASET_CLEAN / "sickle",
                    "kaggle_pos_", MAX_CELLS_PER_IMAGE_POS,
                    count_cls("sickle"), SICKLE_CAP)
                total_pos += n
                if (j + 1) % 50 == 0:
                    print(f"      [{j+1}/{len(imgs)}] sickle count: {count_cls('sickle')}")
            if count_cls("sickle") >= SICKLE_CAP:
                break

        print(f"  Extracted {total_pos} cells from Positive smears → sickle/")
    else:
        print(f"\n  No Positive/ folder found — skipping sickle extraction from Kaggle")

    final_normal = count_cls("normal")
    final_sickle = count_cls("sickle")
    print(f"\n  After extraction:")
    print(f"    normal:  {final_normal}")
    print(f"    sickle:  {final_sickle}")

    return total_neg, total_pos


# ═══════════════════════════════════════════════════════════════
#  STEP 2 — Smart augmentation
# ═══════════════════════════════════════════════════════════════

def augment_image(img, aug_type):
    """Apply a single augmentation and return the result."""
    if aug_type == "r90":
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif aug_type == "r180":
        return cv2.rotate(img, cv2.ROTATE_180)
    elif aug_type == "r270":
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif aug_type == "hflip":
        return cv2.flip(img, 1)
    elif aug_type == "bright":
        return cv2.convertScaleAbs(img, alpha=1.0, beta=38)  # +15%
    elif aug_type == "dark":
        return cv2.convertScaleAbs(img, alpha=0.85, beta=0)  # -15%
    elif aug_type == "blur":
        return cv2.GaussianBlur(img, (3, 3), 0)
    elif aug_type == "hue":
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0].astype(int) + 10) % 180
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return img


AUG_TYPES = ["r90", "r180", "r270", "hflip", "bright", "dark", "blur", "hue"]

# Priority order for source prefixes (augment least-represented first)
PREFIX_PRIORITY = ["orig_", "erydb_c_", "erydb_e_", "kaggle_neg_", "kaggle_pos_"]


def step2_augment():
    print("\n" + "=" * 70)
    print("  STEP 2: Smart data augmentation")
    print("=" * 70)

    sickle_before = count_cls("sickle")
    normal_before = count_cls("normal")
    print(f"\n  Before augmentation:")
    print(f"    normal:  {normal_before}")
    print(f"    sickle:  {sickle_before}")

    sickle_aug_count = 0
    normal_aug_count = 0

    # ── Augment sickle to reach target ──
    if sickle_before < SICKLE_TARGET:
        needed = SICKLE_TARGET - sickle_before
        print(f"\n  Sickle needs {needed} more to reach {SICKLE_TARGET}")

        sickle_dir = DATASET_CLEAN / "sickle"
        # Get existing non-augmented files, sorted by prefix priority
        existing = [f for f in sickle_dir.iterdir() if is_img(f)]
        # Exclude already-augmented files
        base_files = [f for f in existing if not any(
            f.stem.endswith(f"_{a}") for a in AUG_TYPES)]

        # Sort by prefix priority
        def prefix_order(f):
            for i, p in enumerate(PREFIX_PRIORITY):
                if f.name.startswith(p):
                    return i
            return len(PREFIX_PRIORITY)

        base_files.sort(key=prefix_order)

        aug_idx = 0
        for base_file in base_files:
            if sickle_aug_count >= needed:
                break
            img = cv2.imread(str(base_file))
            if img is None:
                continue

            for aug_type in AUG_TYPES:
                if sickle_aug_count >= needed:
                    break
                aug_img = augment_image(img, aug_type)
                out_name = f"{base_file.stem}_{aug_type}.jpg"
                out_path = sickle_dir / out_name
                if not out_path.exists():
                    cv2.imwrite(str(out_path), aug_img, [cv2.IMWRITE_JPEG_QUALITY, JPG_Q])
                    sickle_aug_count += 1

        print(f"  Generated {sickle_aug_count} sickle augmentations")
    else:
        print(f"\n  Sickle already at {sickle_before} >= {SICKLE_TARGET}, no augmentation needed")

    # ── Check if normal needs augmentation for balance ──
    final_sickle = count_cls("sickle")
    final_normal = count_cls("normal")
    ratio = final_normal / final_sickle if final_sickle > 0 else float("inf")

    if ratio > MAX_RATIO:
        print(f"\n  Normal:Sickle ratio = {ratio:.2f} > {MAX_RATIO}")
        print(f"  No normal augmentation needed — ratio is within range")
    elif ratio < MIN_RATIO:
        # Need to augment normal
        target_normal = int(final_sickle * MAX_RATIO)
        needed = target_normal - final_normal
        print(f"\n  Normal:Sickle ratio = {ratio:.2f} < {MIN_RATIO}")
        print(f"  Augmenting normal to {target_normal} (need {needed} more)")

        normal_dir = DATASET_CLEAN / "normal"
        base_files = [f for f in normal_dir.iterdir() if is_img(f)
                      and not any(f.stem.endswith(f"_{a}") for a in AUG_TYPES)]
        base_files.sort(key=prefix_order)

        for base_file in base_files:
            if normal_aug_count >= needed:
                break
            img = cv2.imread(str(base_file))
            if img is None:
                continue
            for aug_type in AUG_TYPES:
                if normal_aug_count >= needed:
                    break
                aug_img = augment_image(img, aug_type)
                out_name = f"{base_file.stem}_{aug_type}.jpg"
                out_path = normal_dir / out_name
                if not out_path.exists():
                    cv2.imwrite(str(out_path), aug_img, [cv2.IMWRITE_JPEG_QUALITY, JPG_Q])
                    normal_aug_count += 1

        print(f"  Generated {normal_aug_count} normal augmentations")

    final_normal = count_cls("normal")
    final_sickle = count_cls("sickle")
    print(f"\n  After augmentation:")
    print(f"    normal:  {final_normal}")
    print(f"    sickle:  {final_sickle}")
    print(f"    ratio:   {final_normal/final_sickle:.2f}:1" if final_sickle > 0 else "    ratio: N/A")

    return sickle_aug_count, normal_aug_count, normal_before, sickle_before


# ═══════════════════════════════════════════════════════════════
#  STEP 3 — Train/Val/Test split
# ═══════════════════════════════════════════════════════════════

def get_base_stem(filename):
    """Get the original base stem (before augmentation suffix).
    e.g. 'orig_cell_001_r90' → 'orig_cell_001'
    """
    stem = Path(filename).stem
    for aug in AUG_TYPES:
        if stem.endswith(f"_{aug}"):
            return stem[:-(len(aug) + 1)]
    return stem


def step3_split():
    print("\n" + "=" * 70)
    print("  STEP 3: Train/Val/Test split (70/15/15)")
    print("=" * 70)

    # Create split directories
    for split in ["train", "val", "test"]:
        for cls in ["normal", "sickle"]:
            (SPLITS_DIR / split / cls).mkdir(parents=True, exist_ok=True)

    split_counts = defaultdict(lambda: defaultdict(int))

    for cls in ["normal", "sickle"]:
        src_dir = DATASET_CLEAN / cls
        all_files = sorted([f for f in src_dir.iterdir() if is_img(f)])

        # Group files by base stem (augmented versions stay together)
        groups = defaultdict(list)
        for f in all_files:
            base = get_base_stem(f.name)
            groups[base].append(f)

        # Shuffle groups deterministically
        group_keys = sorted(groups.keys())
        random.shuffle(group_keys)

        n_groups = len(group_keys)
        train_end = int(n_groups * 0.70)
        val_end = int(n_groups * 0.85)

        for i, key in enumerate(group_keys):
            if i < train_end:
                split = "train"
            elif i < val_end:
                split = "val"
            else:
                split = "test"

            for f in groups[key]:
                dst = SPLITS_DIR / split / cls / f.name
                shutil.copy2(str(f), str(dst))
                split_counts[split][cls] += 1

        print(f"  {cls}: {n_groups} base groups → "
              f"train={split_counts['train'][cls]}, "
              f"val={split_counts['val'][cls]}, "
              f"test={split_counts['test'][cls]}")

    return dict(split_counts)


# ═══════════════════════════════════════════════════════════════
#  STEP 4 — Final report
# ═══════════════════════════════════════════════════════════════

def step4_report(neg_extracted, pos_extracted, sickle_aug, normal_aug,
                 normal_before, sickle_before, split_counts):
    print("\n" + "=" * 70)
    print("  STEP 4: Final Report")
    print("=" * 70)

    normal_after = count_cls("normal")
    sickle_after = count_cls("sickle")

    print(f"\n  EXTRACTION RESULTS:")
    print(f"    Cells from Kaggle Negative: {neg_extracted}")
    print(f"    Cells from Kaggle Positive: {pos_extracted}")

    print(f"\n  AUGMENTATION RESULTS:")
    print(f"    Sickle before: {sickle_before} → after: {sickle_after} (+{sickle_aug} augmented)")
    print(f"    Normal before: {normal_before} → after: {normal_after} (+{normal_aug} augmented)")

    print(f"\n  FINAL SPLIT:")
    print(f"  {'Split':<10s}{'Normal':>8s}{'Sickle':>8s}{'Total':>8s}")
    print(f"  {'─' * 34}")
    grand_n, grand_s = 0, 0
    for split in ["train", "val", "test"]:
        n = split_counts.get(split, {}).get("normal", 0)
        s = split_counts.get(split, {}).get("sickle", 0)
        grand_n += n
        grand_s += s
        print(f"  {split:<10s}{n:>8d}{s:>8d}{n+s:>8d}")
    print(f"  {'─' * 34}")
    print(f"  {'TOTAL':<10s}{grand_n:>8d}{grand_s:>8d}{grand_n+grand_s:>8d}")

    ratio = round(grand_n / grand_s, 2) if grand_s > 0 else 0
    sufficient = normal_after >= 500 and sickle_after >= 500
    print(f"\n  Balance ratio: {ratio}:1")
    print(f"  Sufficient (500/class): {'YES ✓' if sufficient else 'NO ⚠'}")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "extraction": {
            "kaggle_negative_cells": neg_extracted,
            "kaggle_positive_cells": pos_extracted,
        },
        "augmentation": {
            "sickle_before": sickle_before, "sickle_after": sickle_after,
            "sickle_augmented": sickle_aug,
            "normal_before": normal_before, "normal_after": normal_after,
            "normal_augmented": normal_aug,
        },
        "splits": {
            split: dict(split_counts.get(split, {}))
            for split in ["train", "val", "test"]
        },
        "totals": {
            "normal": grand_n, "sickle": grand_s,
            "total": grand_n + grand_s, "balance_ratio": ratio,
            "sufficient": sufficient,
        },
    }

    rp = DATASET_CLEAN / "augment_and_split_report.json"
    with open(rp, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  ✓ Report: {rp}")
    return report


# ═══════════════════════════════════════════════════════════════
#  STEP 5 — Visual grid
# ═══════════════════════════════════════════════════════════════

def step5_grid():
    print("\n" + "=" * 70)
    print("  STEP 5: Visual grid")
    print("=" * 70)

    CELL = 128
    COLS = 8
    PAD = 4
    TITLE_H = 22
    LABEL_H = 18

    row_h = TITLE_H + CELL + LABEL_H + PAD
    # Row 1: train normal, Row 2: train sickle, Row 3: augmentation demo (4 sets of 2)
    total_h = PAD + 3 * row_h
    total_w = PAD + COLS * (CELL + PAD)

    canvas = np.ones((total_h, total_w, 3), dtype=np.uint8) * 30

    def draw_cell(canvas, img_path, x, y):
        img = cv2.imread(str(img_path))
        if img is not None:
            r = cv2.resize(img, (CELL, CELL), interpolation=cv2.INTER_AREA)
            canvas[y:y + CELL, x:x + CELL] = r

    y = PAD

    # Row 1: random train normal
    cv2.putText(canvas, "train/normal (random mix)", (PAD + 4, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
    y += TITLE_H
    train_n = SPLITS_DIR / "train" / "normal"
    if train_n.exists():
        files = [f for f in train_n.iterdir() if is_img(f)]
        sample = random.sample(files, min(COLS, len(files)))
        for col, f in enumerate(sample):
            x = PAD + col * (CELL + PAD)
            draw_cell(canvas, f, x, y)
            cv2.putText(canvas, f.stem[:18], (x + 2, y + CELL + 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.24, (150, 150, 150), 1, cv2.LINE_AA)
    y += CELL + LABEL_H + PAD

    # Row 2: random train sickle
    cv2.putText(canvas, "train/sickle (random mix)", (PAD + 4, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
    y += TITLE_H
    train_s = SPLITS_DIR / "train" / "sickle"
    if train_s.exists():
        files = [f for f in train_s.iterdir() if is_img(f)]
        sample = random.sample(files, min(COLS, len(files)))
        for col, f in enumerate(sample):
            x = PAD + col * (CELL + PAD)
            draw_cell(canvas, f, x, y)
            cv2.putText(canvas, f.stem[:18], (x + 2, y + CELL + 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.24, (150, 150, 150), 1, cv2.LINE_AA)
    y += CELL + LABEL_H + PAD

    # Row 3: augmentation demo (original → r90 → hflip → bright)
    cv2.putText(canvas, "Augmentation demo: original | r90 | hflip | bright (x2 sets)", (PAD + 4, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 200, 255), 1, cv2.LINE_AA)
    y += TITLE_H
    sickle_dir = DATASET_CLEAN / "sickle"
    if sickle_dir.exists():
        base_files = [f for f in sickle_dir.iterdir() if is_img(f)
                      and not any(f.stem.endswith(f"_{a}") for a in AUG_TYPES)]
        demo_files = random.sample(base_files, min(2, len(base_files)))
        col = 0
        for df in demo_files:
            img = cv2.imread(str(df))
            if img is None:
                continue
            demos = [
                ("orig", img),
                ("r90", augment_image(img, "r90")),
                ("hflip", augment_image(img, "hflip")),
                ("bright", augment_image(img, "bright")),
            ]
            for label, aug_img in demos:
                if col >= COLS:
                    break
                x = PAD + col * (CELL + PAD)
                r = cv2.resize(aug_img, (CELL, CELL), interpolation=cv2.INTER_AREA)
                canvas[y:y + CELL, x:x + CELL] = r
                cv2.putText(canvas, label, (x + 2, y + CELL + 13),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.30, (0, 200, 255), 1, cv2.LINE_AA)
                col += 1

    grid_path = DATASET_CLEAN / "final_dataset_grid.png"
    cv2.imwrite(str(grid_path), canvas, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    print(f"  ✓ Grid: {grid_path}")


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 70)
    print("  LabMind AI — Augment & Split")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("═" * 70)

    # Step 1
    neg_ex, pos_ex = step1_extract_kaggle()

    # Step 2
    sickle_aug, normal_aug, normal_before, sickle_before = step2_augment()

    # Step 3
    split_counts = step3_split()

    # Step 4
    step4_report(neg_ex, pos_ex, sickle_aug, normal_aug,
                 normal_before, sickle_before, split_counts)

    # Step 5
    try:
        step5_grid()
    except Exception as e:
        print(f"  ⚠ Grid error: {e}")

    print("\n" + "═" * 70)
    print("  DONE — dataset_clean/splits/ is ready for training")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    main()
