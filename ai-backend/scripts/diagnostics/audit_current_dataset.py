"""
LabMind AI — Dataset Audit Script
===================================
READ-ONLY audit of all training and validation data.
Does NOT modify any files.

Usage:
    python audit_current_dataset.py

Output:
    - Console summary
    - dataset_audit_report.json
"""

import json
import os
import sys
import statistics
from pathlib import Path
from datetime import datetime, timezone

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("[WARN] OpenCV not available — image dimension/quality analysis will use PIL fallback")
    try:
        from PIL import Image as PILImage
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False
        print("[WARN] PIL not available either — image analysis will be limited to file counts/sizes")

# ── Paths ──
BASE = Path(__file__).resolve().parent
DATASET_V1_2CLASS = BASE / "dataset_v1_2class"
VALIDATION_CELLS = BASE / "validation_cells"
VALIDATION_SMEARS = BASE / "validation_smears"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def is_image(p: Path) -> bool:
    return p.suffix.lower() in IMAGE_EXTENSIONS


def get_image_info(path: Path) -> dict:
    """Read image dimensions without modifying anything."""
    info = {
        "filename": path.name,
        "path": str(path),
        "file_size_bytes": path.stat().st_size,
        "file_size_kb": round(path.stat().st_size / 1024, 2),
    }

    if HAS_CV2:
        img = cv2.imread(str(path))
        if img is not None:
            h, w = img.shape[:2]
            channels = img.shape[2] if len(img.shape) == 3 else 1
            info["width"] = w
            info["height"] = h
            info["channels"] = channels
        else:
            info["width"] = None
            info["height"] = None
            info["error"] = "cv2.imread returned None"
    elif HAS_PIL:
        try:
            with PILImage.open(str(path)) as im:
                info["width"], info["height"] = im.size
                info["channels"] = len(im.getbands())
        except Exception as e:
            info["width"] = None
            info["height"] = None
            info["error"] = str(e)
    else:
        info["width"] = None
        info["height"] = None

    return info


def compute_sharpness(path: Path) -> float | None:
    """Compute Laplacian variance as a sharpness measure."""
    if not HAS_CV2:
        return None
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    return float(cv2.Laplacian(img, cv2.CV_64F).var())


def compute_mean_rgb(path: Path) -> dict | None:
    """Compute mean R, G, B values."""
    if not HAS_CV2:
        return None
    img = cv2.imread(str(path))
    if img is None:
        return None
    # OpenCV loads as BGR
    means = cv2.mean(img)[:3]
    return {"B": round(means[0], 2), "G": round(means[1], 2), "R": round(means[2], 2)}


def scan_image_dir(dir_path: Path) -> list[dict]:
    """Scan a directory for images and return info list."""
    if not dir_path.exists():
        return []
    results = []
    for f in sorted(dir_path.iterdir()):
        if f.is_file() and is_image(f):
            results.append(get_image_info(f))
    return results


def summarize_dimensions(images: list[dict]) -> dict:
    """Compute dimension statistics from a list of image info dicts."""
    widths = [i["width"] for i in images if i.get("width") is not None]
    heights = [i["height"] for i in images if i.get("height") is not None]
    sizes_kb = [i["file_size_kb"] for i in images if i.get("file_size_kb") is not None]

    result = {"count": len(images)}

    if widths:
        result["width_min"] = min(widths)
        result["width_max"] = max(widths)
        result["width_mean"] = round(statistics.mean(widths), 1)
        result["width_stdev"] = round(statistics.stdev(widths), 1) if len(widths) > 1 else 0.0

    if heights:
        result["height_min"] = min(heights)
        result["height_max"] = max(heights)
        result["height_mean"] = round(statistics.mean(heights), 1)
        result["height_stdev"] = round(statistics.stdev(heights), 1) if len(heights) > 1 else 0.0

    if sizes_kb:
        result["file_size_kb_min"] = min(sizes_kb)
        result["file_size_kb_max"] = max(sizes_kb)
        result["file_size_kb_mean"] = round(statistics.mean(sizes_kb), 1)

    return result


# ═══════════════════════════════════════════════════════════════
#  SECTION 1: dataset_v1_2class
# ═══════════════════════════════════════════════════════════════

def audit_dataset_v1_2class() -> dict:
    print("\n" + "=" * 70)
    print("  SECTION 1: dataset_v1_2class/")
    print("=" * 70)

    report = {"exists": DATASET_V1_2CLASS.exists()}
    if not report["exists"]:
        print("  ⚠ Directory NOT FOUND — skipping")
        return report

    splits = {}
    for split_name in ["train", "val"]:
        split_dir = DATASET_V1_2CLASS / split_name
        split_data = {}
        for class_name in ["normal", "sickle"]:
            class_dir = split_dir / class_name
            images = scan_image_dir(class_dir)
            summary = summarize_dimensions(images)
            split_data[class_name] = {
                "count": len(images),
                "dimensions": summary,
                "images": images,
            }
            print(f"\n  {split_name}/{class_name}: {len(images)} images")
            if summary.get("width_min"):
                print(f"    Dimensions: {summary['width_min']}×{summary['height_min']} to "
                      f"{summary['width_max']}×{summary['height_max']}")
                print(f"    Mean: {summary['width_mean']}×{summary['height_mean']} "
                      f"(±{summary.get('width_stdev', 0)}, ±{summary.get('height_stdev', 0)})")
            if summary.get("file_size_kb_min"):
                print(f"    File size: {summary['file_size_kb_min']} KB to {summary['file_size_kb_max']} KB "
                      f"(mean: {summary['file_size_kb_mean']} KB)")
        splits[split_name] = split_data

    # Totals
    total_normal = sum(splits[s].get("normal", {}).get("count", 0) for s in splits)
    total_sickle = sum(splits[s].get("sickle", {}).get("count", 0) for s in splits)
    total = total_normal + total_sickle
    ratio = round(total_normal / total_sickle, 2) if total_sickle > 0 else float("inf")

    print(f"\n  ── TOTALS ──")
    print(f"  Normal: {total_normal}  |  Sickle: {total_sickle}  |  Total: {total}")
    print(f"  Balance ratio (normal:sickle): {ratio}:1")
    if ratio > 2.0 or ratio < 0.5:
        print(f"  ⚠ IMBALANCED — ratio exceeds 2:1")
    else:
        print(f"  ✓ Reasonably balanced")

    report["splits"] = {
        split_name: {
            cls: {"count": data["count"], "dimensions": data["dimensions"]}
            for cls, data in split_data.items()
        }
        for split_name, split_data in splits.items()
    }
    report["totals"] = {
        "normal": total_normal,
        "sickle": total_sickle,
        "total": total,
        "balance_ratio": ratio,
        "is_balanced": 0.5 <= ratio <= 2.0,
    }

    return report


# ═══════════════════════════════════════════════════════════════
#  SECTION 2: validation_cells
# ═══════════════════════════════════════════════════════════════

def audit_validation_cells() -> dict:
    print("\n" + "=" * 70)
    print("  SECTION 2: validation_cells/")
    print("=" * 70)

    report = {"exists": VALIDATION_CELLS.exists()}
    if not report["exists"]:
        print("  ⚠ Directory NOT FOUND — skipping")
        return report

    # Active crops
    active = {}
    for class_name in ["normal", "sickle", "artifact"]:
        class_dir = VALIDATION_CELLS / class_name
        images = scan_image_dir(class_dir)
        summary = summarize_dimensions(images)
        active[class_name] = {"count": len(images), "dimensions": summary}
        print(f"\n  Active {class_name}: {len(images)} crops")
        if summary.get("width_min"):
            print(f"    Dimensions: {summary['width_min']}×{summary['height_min']} to "
                  f"{summary['width_max']}×{summary['height_max']}")

    # Raw crops
    raw = {}
    for class_name in ["normal", "sickle", "artifact"]:
        class_dir = VALIDATION_CELLS / "raw" / class_name
        images = scan_image_dir(class_dir)
        raw[class_name] = {"count": len(images)}
        if images:
            print(f"  Raw {class_name}: {len(images)} crops")

    # Rejected crops
    rejected = {}
    for class_name in ["normal", "sickle", "artifact"]:
        class_dir = VALIDATION_CELLS / "_rejected" / class_name
        images = scan_image_dir(class_dir)
        rejected[class_name] = {"count": len(images)}
        if images:
            print(f"  Rejected {class_name}: {len(images)} crops")

    total_rejected = sum(v["count"] for v in rejected.values())
    print(f"\n  Total rejected: {total_rejected}")

    # Original backup
    backup = {}
    for class_name in ["normal", "sickle", "artifact"]:
        class_dir = VALIDATION_CELLS / "_original_backup" / class_name
        images = scan_image_dir(class_dir)
        backup[class_name] = {"count": len(images)}
        if images:
            print(f"  Backup {class_name}: {len(images)} crops")

    total_backup = sum(v["count"] for v in backup.values())
    print(f"  Total in _original_backup: {total_backup}")

    # Clean
    clean_dir = VALIDATION_CELLS / "_clean"
    clean_images = scan_image_dir(clean_dir) if clean_dir.exists() else []
    print(f"  _clean: {len(clean_images)} images")

    # crop_log.json
    crop_log_path = VALIDATION_CELLS / "crop_log.json"
    crop_log_entries = 0
    if crop_log_path.exists():
        try:
            with open(crop_log_path) as f:
                crop_log_entries = len(json.load(f))
        except Exception:
            pass
    print(f"  crop_log.json: {crop_log_entries} entries")

    report["active"] = active
    report["raw"] = raw
    report["rejected"] = rejected
    report["rejected_total"] = total_rejected
    report["original_backup"] = backup
    report["original_backup_total"] = total_backup
    report["clean_count"] = len(clean_images)
    report["crop_log_entries"] = crop_log_entries

    return report


# ═══════════════════════════════════════════════════════════════
#  SECTION 3: validation_smears
# ═══════════════════════════════════════════════════════════════

def audit_validation_smears() -> dict:
    print("\n" + "=" * 70)
    print("  SECTION 3: validation_smears/")
    print("=" * 70)

    report = {"exists": VALIDATION_SMEARS.exists()}
    if not report["exists"]:
        print("  ⚠ Directory NOT FOUND — skipping")
        return report

    categories = {}
    for subdir_name in ["normal", "sickle", "borderline"]:
        subdir = VALIDATION_SMEARS / subdir_name
        if not subdir.exists():
            categories[subdir_name] = {"count": 0, "smears": []}
            continue

        smears = []
        for f in sorted(subdir.iterdir()):
            if f.is_file() and is_image(f):
                info = get_image_info(f)
                info["sharpness_laplacian_var"] = compute_sharpness(f)
                info["mean_rgb"] = compute_mean_rgb(f)
                smears.append(info)

        categories[subdir_name] = {
            "count": len(smears),
            "dimensions": summarize_dimensions(smears),
            "smears": smears,
        }

        print(f"\n  {subdir_name}/: {len(smears)} smears")
        for s in smears:
            dims = f"{s.get('width', '?')}×{s.get('height', '?')}"
            sharp = s.get("sharpness_laplacian_var")
            sharp_str = f"sharpness={sharp:.1f}" if sharp is not None else "sharpness=N/A"
            rgb = s.get("mean_rgb")
            rgb_str = f"RGB=({rgb['R']:.0f},{rgb['G']:.0f},{rgb['B']:.0f})" if rgb else "RGB=N/A"
            print(f"    {s['filename']:40s}  {dims:12s}  {s['file_size_kb']:8.1f} KB  {sharp_str:20s}  {rgb_str}")

    total_smears = sum(c["count"] for c in categories.values())
    print(f"\n  Total validation smears: {total_smears}")

    report["categories"] = {
        cat: {"count": data["count"], "dimensions": data.get("dimensions", {}),
              "smears": [{k: v for k, v in s.items() if k != "path"} for s in data["smears"]]}
        for cat, data in categories.items()
    }
    report["total"] = total_smears

    return report


# ═══════════════════════════════════════════════════════════════
#  SECTION 4: Final Summary
# ═══════════════════════════════════════════════════════════════

def print_final_summary(ds_report: dict, vc_report: dict, vs_report: dict):
    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)

    # Training data totals
    totals = ds_report.get("totals", {})
    total_normal = totals.get("normal", 0)
    total_sickle = totals.get("sickle", 0)
    total_training = totals.get("total", 0)
    ratio = totals.get("balance_ratio", 0)
    is_balanced = totals.get("is_balanced", False)

    print(f"\n  Training Images (dataset_v1_2class/):")
    print(f"    Normal: {total_normal}")
    print(f"    Sickle: {total_sickle}")
    print(f"    Total:  {total_training}")
    print(f"    Balance ratio: {ratio}:1 {'✓ balanced' if is_balanced else '⚠ IMBALANCED'}")

    # Dimensions
    for split_name in ["train", "val"]:
        split = ds_report.get("splits", {}).get(split_name, {})
        for cls in ["normal", "sickle"]:
            dims = split.get(cls, {}).get("dimensions", {})
            if dims.get("width_min"):
                print(f"    {split_name}/{cls}: {dims['width_min']}×{dims['height_min']} to "
                      f"{dims['width_max']}×{dims['height_max']}")

    # Validation cells
    vc_active_total = sum(
        vc_report.get("active", {}).get(cls, {}).get("count", 0)
        for cls in ["normal", "sickle", "artifact"]
    )
    print(f"\n  Validation Cells (validation_cells/):")
    for cls in ["normal", "sickle", "artifact"]:
        cnt = vc_report.get("active", {}).get(cls, {}).get("count", 0)
        print(f"    Active {cls}: {cnt}")
    print(f"    Total active: {vc_active_total}")
    print(f"    Rejected: {vc_report.get('rejected_total', 0)}")
    print(f"    Original backup: {vc_report.get('original_backup_total', 0)}")

    # Validation smears
    vs_total = vs_report.get("total", 0)
    print(f"\n  Validation Smears (validation_smears/):")
    for cat in ["normal", "sickle", "borderline"]:
        cnt = vs_report.get("categories", {}).get(cat, {}).get("count", 0)
        print(f"    {cat}: {cnt}")
    print(f"    Total: {vs_total}")

    # Sufficiency assessment
    RECOMMENDED_MIN_PER_CLASS = 500
    print(f"\n  ── SUFFICIENCY ASSESSMENT ──")
    print(f"  Recommended minimum per class: {RECOMMENDED_MIN_PER_CLASS} images")
    print(f"  (For medical imaging CNNs, 1000–5000+ per class with augmentation is standard)")
    print(f"")

    if total_training == 0:
        print(f"  ⚠ NO TRAINING DATA FOUND")
    else:
        min_class = min(total_normal, total_sickle)
        if min_class < RECOMMENDED_MIN_PER_CLASS:
            deficit = RECOMMENDED_MIN_PER_CLASS - min_class
            print(f"  ⚠ INSUFFICIENT: smallest class has {min_class} images")
            print(f"    Need at least {deficit} more images in the smaller class")
            print(f"    This explains why the model fails on new/external images —")
            print(f"    it has memorized the limited training set rather than learning")
            print(f"    generalizable cell morphology features.")
        else:
            print(f"  ✓ Minimum threshold met ({min_class} >= {RECOMMENDED_MIN_PER_CLASS})")
            print(f"    However, for clinical robustness, 1000+ per class is recommended.")

    if vs_total < 30:
        print(f"\n  ⚠ VALIDATION SET TOO SMALL: {vs_total} smears (recommend 30+ minimum)")

    return {
        "training_normal": total_normal,
        "training_sickle": total_sickle,
        "training_total": total_training,
        "balance_ratio": ratio,
        "is_balanced": is_balanced,
        "validation_cells_active": vc_active_total,
        "validation_cells_rejected": vc_report.get("rejected_total", 0),
        "validation_smears_total": vs_total,
        "recommended_min_per_class": RECOMMENDED_MIN_PER_CLASS,
        "is_sufficient": min(total_normal, total_sickle) >= RECOMMENDED_MIN_PER_CLASS if total_training > 0 else False,
    }


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 70)
    print("  LabMind AI — Dataset Audit Report")
    print(f"  Generated: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Base directory: {BASE}")
    print("═" * 70)

    ds_report = audit_dataset_v1_2class()
    vc_report = audit_validation_cells()
    vs_report = audit_validation_smears()
    summary = print_final_summary(ds_report, vc_report, vs_report)

    # Save full report
    full_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_directory": str(BASE),
        "dataset_v1_2class": ds_report,
        "validation_cells": vc_report,
        "validation_smears": vs_report,
        "summary": summary,
    }

    # Remove raw image lists from JSON to keep it manageable
    # (keep only counts and dimensions)
    output_path = BASE / "dataset_audit_report.json"
    with open(output_path, "w") as f:
        json.dump(full_report, f, indent=2, default=str)

    print(f"\n  ✓ Full report saved to: {output_path}")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    main()
