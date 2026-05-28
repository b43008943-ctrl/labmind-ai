"""
Step 2b: Validation Cells Quality Repair
Audits every crop in validation_cells/ using objective quality criteria.
Outputs a quality report and rebuilds the clean set.
"""
import json
import os
import shutil
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path("validation_cells")
CLASSES = ["normal", "sickle", "artifact"]

# ── Quality thresholds ──
MIN_SIZE_PX = 20          # minimum width AND height
MAX_SIZE_PX = 200         # maximum width OR height (likely multi-cell or bad crop)
MIN_BLUR_SCORE = 30.0     # Laplacian variance — below = too blurry
MIN_FOREGROUND_RATIO = 0.15  # cell pixels vs background
MAX_EDGE_TOUCH_RATIO = 0.25  # fraction of border pixels that are non-background
MIN_CIRCULARITY = 0.0     # not used as hard reject, but flagged
MAX_ASPECT_RATIO = 4.0    # extremely elongated = likely multi-cell or artifact
MIN_CELL_AREA_RATIO = 0.10   # contour area vs crop area — too small = off-center/partial

def analyze_crop(img_path):
    """Analyze a single crop and return quality metrics + pass/reject."""
    img = cv2.imread(str(img_path))
    if img is None:
        return {"status": "reject", "reason": "unreadable_file", "metrics": {}}

    h, w = img.shape[:2]
    area = h * w

    metrics = {"width": w, "height": h, "area": area}
    reasons = []

    # ── Size check ──
    if w < MIN_SIZE_PX or h < MIN_SIZE_PX:
        reasons.append("too_small")
    if w > MAX_SIZE_PX or h > MAX_SIZE_PX:
        reasons.append("too_large")

    # ── Aspect ratio ──
    ar = max(w, h) / max(min(w, h), 1)
    metrics["aspect_ratio"] = round(ar, 2)
    if ar > MAX_ASPECT_RATIO:
        reasons.append("extreme_aspect_ratio")

    # ── Blur score ──
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    metrics["blur_score"] = round(blur, 1)
    if blur < MIN_BLUR_SCORE:
        reasons.append("too_blurry")

    # ── Foreground ratio (Otsu threshold) ──
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    fg_pixels = np.count_nonzero(thresh)
    fg_ratio = fg_pixels / area if area > 0 else 0
    metrics["foreground_ratio"] = round(fg_ratio, 3)
    if fg_ratio < MIN_FOREGROUND_RATIO:
        reasons.append("background_heavy")

    # ── Edge touching check ──
    # Check if significant foreground touches the border
    border_mask = np.zeros_like(thresh)
    border_mask[0, :] = thresh[0, :]
    border_mask[-1, :] = thresh[-1, :]
    border_mask[:, 0] = thresh[:, 0]
    border_mask[:, -1] = thresh[:, -1]
    border_fg = np.count_nonzero(border_mask)
    perimeter = 2 * (w + h)
    edge_ratio = border_fg / perimeter if perimeter > 0 else 0
    metrics["edge_touch_ratio"] = round(edge_ratio, 3)
    if edge_ratio > MAX_EDGE_TOUCH_RATIO:
        reasons.append("edge_touching")

    # ── Centering check (centroid distance from center) ──
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest)
        cell_area_ratio = contour_area / area if area > 0 else 0
        metrics["cell_area_ratio"] = round(cell_area_ratio, 3)

        if cell_area_ratio < MIN_CELL_AREA_RATIO:
            reasons.append("partial_or_offcenter")

        M = cv2.moments(largest)
        if M["m00"] > 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            center_dist = np.sqrt((cx - w/2)**2 + (cy - h/2)**2)
            max_dist = np.sqrt((w/2)**2 + (h/2)**2)
            centrality = center_dist / max_dist if max_dist > 0 else 0
            metrics["centrality"] = round(centrality, 3)
            if centrality > 0.45:
                reasons.append("off_center")

        # ── Multi-cell check (multiple large contours) ──
        large_contours = [c for c in contours if cv2.contourArea(c) > area * 0.1]
        metrics["num_large_contours"] = len(large_contours)
        if len(large_contours) > 2:
            reasons.append("multi_cell")
    else:
        metrics["cell_area_ratio"] = 0
        metrics["centrality"] = 1.0
        metrics["num_large_contours"] = 0
        reasons.append("no_cell_detected")

    status = "reject" if reasons else "pass"
    return {
        "status": status,
        "reason": "|".join(reasons) if reasons else "clean",
        "metrics": metrics,
    }


def main():
    # Load existing labels
    labels_path = BASE_DIR / "labels.json"
    with open(labels_path) as f:
        labels_data = json.load(f)
    
    label_map = {l["filename"]: l for l in labels_data["labels"]}

    # Audit results
    audit_results = []
    class_stats = {}

    for cls in CLASSES:
        cls_dir = BASE_DIR / cls
        if not cls_dir.exists():
            continue

        files = sorted([f for f in os.listdir(cls_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        passed = 0
        rejected = 0

        for fname in files:
            fpath = cls_dir / fname
            result = analyze_crop(fpath)
            
            label_info = label_map.get(fname, {})
            
            entry = {
                "filename": fname,
                "class": cls,
                "status": result["status"],
                "reason": result["reason"],
                "source_smear": label_info.get("source_smear", "unknown"),
                "source_type": label_info.get("source_type", "unknown"),
                **result["metrics"],
            }
            audit_results.append(entry)

            if result["status"] == "pass":
                passed += 1
            else:
                rejected += 1
                
        class_stats[cls] = {"total": len(files), "passed": passed, "rejected": rejected}

    # Print summary
    print("=" * 80)
    print("  VALIDATION CELLS QUALITY AUDIT")
    print("=" * 80)
    
    for cls in CLASSES:
        s = class_stats.get(cls, {})
        print(f"\n  {cls.upper()}: {s.get('total',0)} total → {s.get('passed',0)} passed, {s.get('rejected',0)} rejected")
    
    # Rejection reason breakdown
    print("\n  REJECTION REASONS:")
    reason_counts = {}
    for r in audit_results:
        if r["status"] == "reject":
            for reason in r["reason"].split("|"):
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {count}")

    # Show rejected files
    print("\n  REJECTED CROPS:")
    for r in audit_results:
        if r["status"] == "reject":
            print(f"    [{r['class']}] {r['filename']} → {r['reason']} "
                  f"(size={r.get('width','?')}x{r.get('height','?')}, "
                  f"blur={r.get('blur_score','?')}, "
                  f"fg={r.get('foreground_ratio','?')}, "
                  f"edge={r.get('edge_touch_ratio','?')}, "
                  f"cell_area={r.get('cell_area_ratio','?')})")

    # ── Rebuild clean set ──
    clean_dir = BASE_DIR / "_clean"
    rejected_dir = BASE_DIR / "_rejected"
    
    for cls in CLASSES:
        (clean_dir / cls).mkdir(parents=True, exist_ok=True)
        (rejected_dir / cls).mkdir(parents=True, exist_ok=True)

    clean_labels = []
    rejected_labels = []
    clean_counts = {"normal": 0, "sickle": 0, "artifact": 0}
    rejected_counts = {"normal": 0, "sickle": 0, "artifact": 0}

    for r in audit_results:
        cls = r["class"]
        src = BASE_DIR / cls / r["filename"]
        
        if r["status"] == "pass":
            dst = clean_dir / cls / r["filename"]
            shutil.copy2(str(src), str(dst))
            clean_labels.append({
                "filename": r["filename"],
                "class": cls,
                "source_smear": r.get("source_smear", "unknown"),
                "source_type": r.get("source_type", "unknown"),
                "quality_status": "pass",
                "blur_score": r.get("blur_score"),
                "dimensions": f"{r.get('width','?')}x{r.get('height','?')}",
                "foreground_ratio": r.get("foreground_ratio"),
                "centrality": r.get("centrality"),
            })
            clean_counts[cls] += 1
        else:
            dst = rejected_dir / cls / r["filename"]
            shutil.copy2(str(src), str(dst))
            rejected_labels.append({
                "filename": r["filename"],
                "class": cls,
                "source_smear": r.get("source_smear", "unknown"),
                "rejection_reason": r["reason"],
                "blur_score": r.get("blur_score"),
                "dimensions": f"{r.get('width','?')}x{r.get('height','?')}",
            })
            rejected_counts[cls] += 1

    # Save clean labels
    clean_labels_data = {
        "version": "v1-quality-repair",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "total_crops": sum(clean_counts.values()),
        "counts": clean_counts,
        "rejection_criteria": {
            "min_size_px": MIN_SIZE_PX,
            "max_size_px": MAX_SIZE_PX,
            "min_blur_score": MIN_BLUR_SCORE,
            "min_foreground_ratio": MIN_FOREGROUND_RATIO,
            "max_edge_touch_ratio": MAX_EDGE_TOUCH_RATIO,
            "max_aspect_ratio": MAX_ASPECT_RATIO,
            "min_cell_area_ratio": MIN_CELL_AREA_RATIO,
            "max_centrality": 0.45,
        },
        "labels": clean_labels,
    }
    
    clean_labels_path = clean_dir / "labels.json"
    with open(clean_labels_path, "w") as f:
        json.dump(clean_labels_data, f, indent=2, default=str)

    # Save rejected labels
    rejected_labels_data = {
        "version": "v1-quality-repair-rejected",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "total_rejected": sum(rejected_counts.values()),
        "counts": rejected_counts,
        "labels": rejected_labels,
    }
    
    rejected_labels_path = rejected_dir / "labels.json"
    with open(rejected_labels_path, "w") as f:
        json.dump(rejected_labels_data, f, indent=2, default=str)

    # Save full audit
    audit_path = BASE_DIR / "quality_audit.json"
    with open(audit_path, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_counts": {cls: class_stats[cls]["total"] for cls in CLASSES},
            "clean_counts": clean_counts,
            "rejected_counts": rejected_counts,
            "reason_breakdown": reason_counts,
            "audit_details": audit_results,
        }, f, indent=2, default=str)

    print("\n" + "=" * 80)
    print("  REBUILD RESULTS")
    print("=" * 80)
    print(f"\n  CLEAN SET (saved to {clean_dir}):")
    for cls in CLASSES:
        print(f"    {cls}: {clean_counts[cls]}")
    print(f"    TOTAL: {sum(clean_counts.values())}")
    
    print(f"\n  REJECTED (saved to {rejected_dir}):")
    for cls in CLASSES:
        print(f"    {cls}: {rejected_counts[cls]}")
    print(f"    TOTAL: {sum(rejected_counts.values())}")

    print(f"\n  Files created:")
    print(f"    {clean_labels_path}")
    print(f"    {rejected_labels_path}")
    print(f"    {audit_path}")
    print()


if __name__ == "__main__":
    main()
