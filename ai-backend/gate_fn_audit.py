"""
LabMind — Gate-by-Gate FN Audit (Step 3)
Measures each validity gate's FN contribution on the 80 sickle validation crops.

For each gate, replicates the exact contour analysis from _classify_rbc and
checks whether that gate alone would reject the crop (force Normal or return None).

NO permanent code changes. Read-only measurement.
"""
import json
import os
import sys
import cv2
import numpy as np
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SICKLE_DIR = os.path.join("validation_cells", "sickle")
LABELS_PATH = os.path.join("validation_cells", "labels.json")
VALID_EXTS = ('.jpg', '.jpeg', '.png')


def analyze_crop(path):
    """
    Replicate the contour analysis from _classify_rbc on a standalone crop.
    Returns all gate-relevant metrics.
    
    For a standalone crop, we treat the whole image as the ROI.
    The "original YOLO box" is the full crop, and contour refinement
    happens within it — same as the pipeline does.
    """
    img = cv2.imread(path)
    if img is None:
        return None
    
    h_img, w_img = img.shape[:2]
    
    # For a standalone crop, the "YOLO box" IS the full crop
    orig_x1, orig_y1 = 0, 0
    orig_x2, orig_y2 = w_img, h_img
    orig_area = max(w_img * h_img, 1)
    
    # ── Contour analysis (same as _classify_rbc) ──
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        # No contour: use full crop as fallback (same as pipeline)
        contour_area = orig_area
        cx, cy, cw, ch = 0, 0, w_img, h_img
        x1, y1, x2, y2 = 0, 0, w_img, h_img
    else:
        # Select contour nearest to center (same as pipeline)
        yolo_cx_local = w_img / 2.0
        yolo_cy_local = h_img / 2.0
        min_area_threshold = 100
        
        best_contour = None
        best_dist = float('inf')
        for cnt in contours:
            cnt_area = cv2.contourArea(cnt)
            if cnt_area < min_area_threshold:
                continue
            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cnt_cx = M["m10"] / M["m00"]
            cnt_cy = M["m01"] / M["m00"]
            dist = np.sqrt((cnt_cx - yolo_cx_local) ** 2 + (cnt_cy - yolo_cy_local) ** 2)
            if dist < best_dist:
                best_dist = dist
                best_contour = cnt
        
        if best_contour is None:
            best_contour = max(contours, key=cv2.contourArea)
        
        contour_area = cv2.contourArea(best_contour)
        cx, cy, cw, ch = cv2.boundingRect(best_contour)
        x1, y1 = cx, cy
        x2, y2 = x1 + cw, y1 + ch
    
    crop_area = max((x2 - x1) * (y2 - y1), 1)
    refined_area = crop_area
    
    # ── Compute all gate metrics ──
    
    # Gate 1: Foreground ratio
    foreground_ratio = contour_area / max(crop_area, 1)
    
    # Gate 2: Fill ratio  
    contour_rect_area = max(cw * ch, 1)
    fill_ratio = contour_area / contour_rect_area
    
    # Gate 3: Centrality (contour center vs crop center)
    orig_cx_val = w_img / 2.0
    orig_cy_val = h_img / 2.0
    contour_cx = (x1 + x2) / 2.0
    contour_cy = (y1 + y2) / 2.0
    orig_w = max(w_img, 1)
    orig_h = max(h_img, 1)
    dx = abs(contour_cx - orig_cx_val) / orig_w
    dy = abs(contour_cy - orig_cy_val) / orig_h
    
    # Gate 4: Contour aspect ratio
    contour_ar = max(cw, ch) / (min(cw, ch) + 1e-5)
    
    # Gate 5: Multi-cell merge (refined vs original area)
    merge_ratio = refined_area / max(orig_area, 1)
    
    # Gate 6: Blur score
    cell_crop = img[y1:y2, x1:x2] if (y2 > y1 and x2 > x1) else img
    if cell_crop.size > 0:
        gray_crop = cv2.cvtColor(cell_crop, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray_crop, cv2.CV_64F).var()
    else:
        blur_score = 0.0
    
    # Gate 7: Min crop size
    crop_w = x2 - x1
    crop_h = y2 - y1
    
    # Gate 8: Area filter (needs median_area context)
    # We compute the crop area but the threshold depends on runtime median_area
    # From baseline: median_area ranges from 156 to 9619 across smears
    # We'll test with multiple representative medians
    cell_area_px = crop_area
    
    return {
        "width": w_img,
        "height": h_img,
        "contour_area": float(contour_area),
        "crop_area": float(crop_area),
        "foreground_ratio": round(float(foreground_ratio), 4),
        "fill_ratio": round(float(fill_ratio), 4),
        "centrality_dx": round(float(dx), 4),
        "centrality_dy": round(float(dy), 4),
        "contour_ar": round(float(contour_ar), 4),
        "merge_ratio": round(float(merge_ratio), 4),
        "blur_score": round(float(blur_score), 1),
        "crop_w": int(crop_w),
        "crop_h": int(crop_h),
        "cell_area_px": int(cell_area_px),
        # Gate trigger flags (would this gate reject this crop?)
        "gate_foreground": foreground_ratio < 0.25,
        "gate_fill": fill_ratio < 0.30,
        "gate_centrality": dx > 0.4 or dy > 0.4,
        "gate_contour_ar": contour_ar > 4.0,
        "gate_merge": merge_ratio > 2.0,
        "gate_blur": blur_score < 30,
        "gate_min_size": crop_w < 20 or crop_h < 20,
        # Area filter: test with representative medians from baseline
        "gate_area_median156": cell_area_px < 156 * 0.15 or cell_area_px > 156 * 4.0,
        "gate_area_median824": cell_area_px < 824 * 0.15 or cell_area_px > 824 * 4.0,
        "gate_area_median1480": cell_area_px < 1480 * 0.15 or cell_area_px > 1480 * 4.0,
        "gate_area_median2346": cell_area_px < 2346 * 0.15 or cell_area_px > 2346 * 4.0,
        "gate_area_median4290": cell_area_px < 4290 * 0.15 or cell_area_px > 4290 * 4.0,
        "gate_area_median9619": cell_area_px < 9619 * 0.15 or cell_area_px > 9619 * 4.0,
    }


def main():
    print("=" * 70)
    print("  LabMind — Gate-by-Gate FN Audit (Step 3)")
    print("  Testing each validity gate on 80 sickle validation crops")
    print("  NO code changes. Read-only measurement.")
    print("=" * 70)
    print()
    
    # Load sickle crops
    sickle_files = sorted([
        f for f in os.listdir(SICKLE_DIR)
        if f.lower().endswith(VALID_EXTS)
    ])
    print(f"  Sickle crops found: {len(sickle_files)}")
    
    # Load labels for metadata
    with open(LABELS_PATH, "r") as f:
        labels_data = json.load(f)
    labels_lookup = {l["filename"]: l for l in labels_data.get("labels", [])}
    
    # Analyze each crop
    results = []
    for fname in sickle_files:
        path = os.path.join(SICKLE_DIR, fname)
        metrics = analyze_crop(path)
        if metrics is None:
            print(f"  WARNING: Could not analyze {fname}")
            continue
        
        label_info = labels_lookup.get(fname, {})
        metrics["filename"] = fname
        metrics["source_smear"] = label_info.get("source_smear", "unknown")
        metrics["source_type"] = label_info.get("source_type", "unknown")
        results.append(metrics)
    
    print(f"  Successfully analyzed: {len(results)}")
    print()
    
    # ── Gate-by-gate FN analysis ──
    gates = [
        {
            "name": "foreground_ratio < 0.25",
            "key": "gate_foreground",
            "pipeline_effect": "force_normal",
            "description": "Rejects crops where contour fills <25% of crop area",
        },
        {
            "name": "fill_ratio < 0.30",
            "key": "gate_fill",
            "pipeline_effect": "force_normal",
            "description": "Rejects crops where contour fills <30% of its bounding rect",
        },
        {
            "name": "centrality > 0.4",
            "key": "gate_centrality",
            "pipeline_effect": "force_normal",
            "description": "Rejects crops where contour center drifts >40% from YOLO box center",
        },
        {
            "name": "contour_ar > 4.0",
            "key": "gate_contour_ar",
            "pipeline_effect": "force_normal",
            "description": "Rejects crops with extreme contour aspect ratio (scratches/artifacts)",
        },
        {
            "name": "multi_cell_merge > 2.0",
            "key": "gate_merge",
            "pipeline_effect": "force_normal",
            "description": "Rejects crops where refined area is >2x the original YOLO box",
        },
        {
            "name": "blur_score < 30",
            "key": "gate_blur",
            "pipeline_effect": "force_normal",
            "description": "Rejects crops with Laplacian variance <30 (blurry/low contrast)",
        },
        {
            "name": "min_crop_size < 20",
            "key": "gate_min_size",
            "pipeline_effect": "return_none",
            "description": "Rejects crops where width or height is <20px",
        },
    ]
    
    # Area filter analysis with representative medians
    area_medians = {
        "median_156 (normal_05)": "gate_area_median156",
        "median_824 (normal_01)": "gate_area_median824",
        "median_1480 (normal_04)": "gate_area_median1480",
        "median_2346 (sickle_01)": "gate_area_median2346",
        "median_4290 (sickle_04)": "gate_area_median4290",
        "median_9619 (sickle_03)": "gate_area_median9619",
    }
    
    total = len(results)
    gate_audit = []
    
    print("  ═══ GATE FN AUDIT RESULTS ═══")
    print()
    
    for gate in gates:
        triggered = [r for r in results if r.get(gate["key"], False)]
        count = len(triggered)
        pct = round(count / total * 100, 1) if total > 0 else 0
        examples = triggered[:5]
        
        # Assess gate
        if count == 0:
            assessment = "SAFE — never fires on sickle crops"
        elif pct <= 3:
            assessment = "SAFE — minimal FN contribution"
        elif pct <= 10:
            assessment = "REVIEW — moderate FN contribution, may be too strict"
        else:
            assessment = "DANGEROUS — major FN source, needs loosening or removal"
        
        entry = {
            "gate_name": gate["name"],
            "description": gate["description"],
            "pipeline_effect": gate["pipeline_effect"],
            "sickle_crops_rejected": count,
            "fn_contribution_pct": pct,
            "total_sickle_crops": total,
            "assessment": assessment,
            "example_crops": [
                {
                    "filename": e["filename"],
                    "source_smear": e["source_smear"],
                    "metric_value": round(e.get(gate["key"].replace("gate_", ""), 0), 4)
                        if isinstance(e.get(gate["key"].replace("gate_", ""), 0), (int, float))
                        else str(e.get(gate["key"].replace("gate_", ""), "")),
                }
                for e in examples
            ],
            "rejected_filenames": [e["filename"] for e in triggered],
        }
        
        # Add specific metric values for rejected crops
        if gate["key"] == "gate_foreground":
            entry["rejected_values"] = [{"file": r["filename"], "foreground_ratio": r["foreground_ratio"]} for r in triggered]
        elif gate["key"] == "gate_fill":
            entry["rejected_values"] = [{"file": r["filename"], "fill_ratio": r["fill_ratio"]} for r in triggered]
        elif gate["key"] == "gate_centrality":
            entry["rejected_values"] = [{"file": r["filename"], "dx": r["centrality_dx"], "dy": r["centrality_dy"]} for r in triggered]
        elif gate["key"] == "gate_contour_ar":
            entry["rejected_values"] = [{"file": r["filename"], "contour_ar": r["contour_ar"]} for r in triggered]
        elif gate["key"] == "gate_merge":
            entry["rejected_values"] = [{"file": r["filename"], "merge_ratio": r["merge_ratio"]} for r in triggered]
        elif gate["key"] == "gate_blur":
            entry["rejected_values"] = [{"file": r["filename"], "blur_score": r["blur_score"]} for r in triggered]
        elif gate["key"] == "gate_min_size":
            entry["rejected_values"] = [{"file": r["filename"], "w": r["crop_w"], "h": r["crop_h"]} for r in triggered]
        
        gate_audit.append(entry)
        
        # Print summary
        marker = "⚠️" if pct > 3 else "✅"
        print(f"  {marker} {gate['name']}")
        print(f"     Rejected: {count}/{total} ({pct}%)")
        print(f"     Assessment: {assessment}")
        if examples:
            for ex in examples[:3]:
                print(f"     Example: {ex['filename']} (from {ex['source_smear']})")
        print()
    
    # ── Area filter (context-dependent) ──
    print(f"  ── Area Filter (context-dependent) ──")
    print(f"  The area filter depends on per-smear median_area.")
    print(f"  Testing with representative medians from baseline:")
    print()
    
    area_audit = {}
    for label, key in area_medians.items():
        triggered = [r for r in results if r.get(key, False)]
        count = len(triggered)
        pct = round(count / total * 100, 1) if total > 0 else 0
        
        if count == 0:
            assessment = "SAFE"
        elif pct <= 3:
            assessment = "SAFE"
        elif pct <= 10:
            assessment = "REVIEW"
        else:
            assessment = "DANGEROUS"
        
        area_audit[label] = {
            "rejected": count,
            "pct": pct,
            "assessment": assessment,
            "example_files": [r["filename"] for r in triggered[:3]],
            "rejected_areas": [{"file": r["filename"], "cell_area_px": r["cell_area_px"]} for r in triggered],
        }
        
        marker = "⚠️" if pct > 3 else "✅"
        print(f"  {marker} area_filter @ {label}: {count}/{total} ({pct}%) — {assessment}")
    
    gate_audit.append({
        "gate_name": "area_filter (0.15–4.0 × median)",
        "description": "Rejects crops outside 0.15x–4.0x median RBC area. Context-dependent.",
        "pipeline_effect": "return_none",
        "per_median_results": area_audit,
        "assessment": "Context-dependent — varies by smear. See per_median_results.",
    })
    
    print()
    
    # ── Find the biggest FN source ──
    ranked = sorted(
        [g for g in gate_audit if "sickle_crops_rejected" in g],
        key=lambda g: g.get("sickle_crops_rejected", 0),
        reverse=True
    )
    
    biggest = ranked[0] if ranked else None
    
    print("  ═══ RANKED BY FN CONTRIBUTION ═══")
    print()
    for g in ranked:
        count = g.get("sickle_crops_rejected", 0)
        pct = g.get("fn_contribution_pct", 0)
        print(f"  {count:3d} ({pct:5.1f}%)  {g['gate_name']}")
    print()
    
    if biggest:
        print(f"  🔴 BIGGEST FN SOURCE: {biggest['gate_name']}")
        print(f"     Rejects {biggest['sickle_crops_rejected']}/{total} sickle crops ({biggest['fn_contribution_pct']}%)")
    print()
    
    # ── Save JSON ──
    output = {
        "version": "v1-baseline",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_sickle_crops": total,
        "gate_audit": gate_audit,
        "biggest_fn_gate": biggest["gate_name"] if biggest else None,
        "per_crop_metrics": results,
    }
    
    out_path = "gate_fn_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print("=" * 70)
    print(f"  ✅ Gate FN audit complete")
    print(f"  ✅ Results saved to: {os.path.abspath(out_path)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
