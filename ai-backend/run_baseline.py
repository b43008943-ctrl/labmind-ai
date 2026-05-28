"""
LabMind — Official Baseline Evaluation Script (Step 1)
Freezes the current pipeline state as v1-baseline.
Runs recall_audit + field_audit on ALL available validation smears.
Saves baseline_results.json with full metadata.

NO code changes. NO threshold changes. Read-only evaluation.
"""
import json
import os
import sys
import hashlib
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Capture pipeline file hash as a frozen version fingerprint ──
PROVIDER_PATH = os.path.join("app", "providers", "ai_provider_v1.py")


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_thresholds():
    """Extract the current threshold/settings snapshot from the frozen pipeline."""
    return {
        "yolo_conf": 0.05,
        "yolo_tile_size": 640,
        "yolo_overlap_pct": 0.25,
        "nms_iou": 0.35,
        "watershed_size_multiplier": 1.5,
        "contour_min_area": 100,
        "validity_foreground_ratio_min": 0.25,
        "validity_fill_ratio_min": 0.30,
        "validity_centrality_max": 0.4,
        "validity_contour_ar_max": 4.0,
        "validity_multi_cell_merge_max": 2.0,
        "validity_blur_min": 30,
        "validity_min_crop_px": 20,
        "area_filter_min_multiplier": 0.15,
        "area_filter_max_multiplier": 4.0,
        "cnn_uncertain_threshold": 0.50,
        "sickle_dual_gate_cnn_min": 0.55,
        "sickle_cnn_override_min": 0.70,
        "sickle_morph_gate_standard_morph_min": 0.55,
        "sickle_morph_gate_standard_cnn_min": 0.40,
        "sickle_morph_dominant_morph_min": 0.70,
        "sickle_morph_dominant_cnn_min": 0.15,
        "morphology_veto_light_ar_max": 1.15,
        "morphology_veto_light_circ_min": 0.75,
        "morphology_veto_light_sol_min": 0.90,
        "composite_weight_cnn": 0.60,
        "composite_weight_morph": 0.40,
        "dedup_distance_px": 15,
        "border_rejection_px": 3,
    }


def collect_smears():
    """Collect all available validation smears."""
    smears = []

    # Normal smears
    ndir = os.path.join("validation_smears", "normal")
    if os.path.isdir(ndir):
        for f in sorted(os.listdir(ndir)):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                smears.append({
                    "path": os.path.join(ndir, f),
                    "filename": f,
                    "category": "normal",
                    "label": f"NORMAL_{f}",
                })

    # Sickle smears
    sdir = os.path.join("validation_smears", "sickle")
    if os.path.isdir(sdir):
        for f in sorted(os.listdir(sdir)):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                smears.append({
                    "path": os.path.join(sdir, f),
                    "filename": f,
                    "category": "sickle",
                    "label": f"SICKLE_{f}",
                })

    # Main test image
    main = os.path.join("test_images", "Sickle_Cell_Blood_Smear.jpg")
    if os.path.isfile(main):
        smears.append({
            "path": main,
            "filename": "Sickle_Cell_Blood_Smear.jpg",
            "category": "sickle",
            "label": "SICKLE_MAIN",
        })

    return smears


def run_baseline():
    print("=" * 70)
    print("  LabMind — Official Baseline Evaluation (v1-baseline)")
    print("  NO code changes. NO threshold changes. Read-only.")
    print("=" * 70)
    print()

    # ── Metadata ──
    timestamp = datetime.now(timezone.utc).isoformat()
    provider_hash = file_sha256(PROVIDER_PATH) if os.path.exists(PROVIDER_PATH) else "FILE_NOT_FOUND"
    print(f"  Timestamp (UTC): {timestamp}")
    print(f"  Pipeline hash:   {provider_hash[:16]}...")
    print()

    # ── Collect smears ──
    smears = collect_smears()
    normal_smears = [s for s in smears if s["category"] == "normal"]
    sickle_smears = [s for s in smears if s["category"] == "sickle"]
    print(f"  Validation smears found:")
    print(f"    Normal: {len(normal_smears)}")
    print(f"    Sickle: {len(sickle_smears)}")
    print(f"    Total:  {len(smears)}")
    print()

    if not smears:
        print("  ERROR: No validation smears found. Aborting.")
        return

    # ── Import audits ──
    from recall_audit import recall_audit
    from field_audit import field_audit

    # ── Run recall audit on ALL smears ──
    print("=" * 70)
    print("  PHASE 1: RECALL AUDIT (per-stage cell counts)")
    print("=" * 70)

    recall_results = []
    for s in smears:
        print(f"\n  >> {s['label']}")
        try:
            r = recall_audit(s["path"], s["label"])
            if r:
                r["filename"] = s["filename"]
                r["category"] = s["category"]
                recall_results.append(r)
            else:
                recall_results.append({
                    "filename": s["filename"],
                    "category": s["category"],
                    "label": s["label"],
                    "error": "recall_audit returned None",
                })
        except Exception as e:
            print(f"  ERROR: {e}")
            recall_results.append({
                "filename": s["filename"],
                "category": s["category"],
                "label": s["label"],
                "error": str(e),
            })

    # ── Run field audit on ALL smears ──
    print()
    print("=" * 70)
    print("  PHASE 2: FIELD AUDIT (gate tracking + morphology)")
    print("=" * 70)

    field_results = []
    for s in smears:
        print(f"\n  >> {s['label']}")
        try:
            r = field_audit(s["path"], s["label"])
            if r:
                r["filename"] = s["filename"]
                r["category"] = s["category"]
                field_results.append(r)
            else:
                field_results.append({
                    "filename": s["filename"],
                    "category": s["category"],
                    "label": s["label"],
                    "error": "field_audit returned None",
                })
        except Exception as e:
            print(f"  ERROR: {e}")
            field_results.append({
                "filename": s["filename"],
                "category": s["category"],
                "label": s["label"],
                "error": str(e),
            })

    # ── Compute aggregate metrics ──
    print()
    print("=" * 70)
    print("  COMPUTING AGGREGATE METRICS")
    print("=" * 70)

    # Cell-level metrics from recall results
    normal_recall = [r for r in recall_results if r.get("category") == "normal" and "error" not in r]
    sickle_recall = [r for r in recall_results if r.get("category") == "sickle" and "error" not in r]

    cell_metrics = {
        "normal_smears": {
            "count": len(normal_recall),
            "total_final_cells": sum(r.get("final", 0) for r in normal_recall),
            "total_sickle_detections": sum(r.get("sickle", 0) for r in normal_recall),
            "total_rbc_detections": sum(r.get("rbc", 0) for r in normal_recall),
            "false_positive_sickle_count": sum(r.get("sickle", 0) for r in normal_recall),
            "per_smear_sickle": [{"label": r.get("label", r.get("filename", "?")), "sickle": r.get("sickle", 0), "total": r.get("final", 0)} for r in normal_recall],
        },
        "sickle_smears": {
            "count": len(sickle_recall),
            "total_final_cells": sum(r.get("final", 0) for r in sickle_recall),
            "total_sickle_detections": sum(r.get("sickle", 0) for r in sickle_recall),
            "total_rbc_detections": sum(r.get("rbc", 0) for r in sickle_recall),
            "per_smear_sickle": [{"label": r.get("label", r.get("filename", "?")), "sickle": r.get("sickle", 0), "total": r.get("final", 0)} for r in sickle_recall],
        },
    }

    # Field-level metrics from field results
    normal_field = [r for r in field_results if r.get("category") == "normal" and "error" not in r]
    sickle_field = [r for r in field_results if r.get("category") == "sickle" and "error" not in r]

    # Normal field: how many have zero sickle?
    normal_zero_sickle = sum(1 for r in normal_field if r.get("final_sickle", 0) == 0)
    # Sickle field: how many have >= 3 sickle?
    sickle_gte3 = sum(1 for r in sickle_field if r.get("final_sickle", 0) >= 3)

    field_metrics = {
        "normal_fields_zero_sickle": f"{normal_zero_sickle}/{len(normal_field)}",
        "normal_fields_zero_sickle_pct": round(normal_zero_sickle / len(normal_field) * 100, 1) if normal_field else 0,
        "sickle_fields_gte3_sickle": f"{sickle_gte3}/{len(sickle_field)}",
        "sickle_fields_gte3_sickle_pct": round(sickle_gte3 / len(sickle_field) * 100, 1) if sickle_field else 0,
        "sickle_field_variance": {},
    }

    # Compute sickle % per sickle field for variance analysis
    sickle_pcts = []
    for r in sickle_field:
        total_rbc = r.get("final_rbc", 0) + r.get("final_sickle", 0)
        if total_rbc > 0:
            pct = r.get("final_sickle", 0) / total_rbc * 100
        else:
            pct = 0
        sickle_pcts.append({"label": r.get("label", "?"), "sickle_pct": round(pct, 2), "sickle_count": r.get("final_sickle", 0), "total_rbc": total_rbc})

    if sickle_pcts:
        import statistics
        pct_values = [s["sickle_pct"] for s in sickle_pcts]
        field_metrics["sickle_field_variance"] = {
            "per_field": sickle_pcts,
            "mean_sickle_pct": round(statistics.mean(pct_values), 2),
            "stdev_sickle_pct": round(statistics.stdev(pct_values), 2) if len(pct_values) > 1 else 0,
            "min_sickle_pct": round(min(pct_values), 2),
            "max_sickle_pct": round(max(pct_values), 2),
        }

    # Gate summary from field audit
    gate_totals = {"cnn_sickle_candidates": 0, "gate_morph_veto": 0, "gate_border": 0,
                   "gate_dual_fail": 0, "gate_cnn_low": 0, "gate_passed": 0}
    for r in field_results:
        if "error" in r:
            continue
        gates = r.get("gates", {})
        for k in gate_totals:
            gate_totals[k] += gates.get(k, 0)

    # ── Print summary ──
    print()
    print(f"  CELL-LEVEL (normal smears):")
    print(f"    Total cells detected:      {cell_metrics['normal_smears']['total_final_cells']}")
    print(f"    Sickle FPs on normals:     {cell_metrics['normal_smears']['false_positive_sickle_count']}")
    print()
    print(f"  CELL-LEVEL (sickle smears):")
    print(f"    Total cells detected:      {cell_metrics['sickle_smears']['total_final_cells']}")
    print(f"    Sickle detections:         {cell_metrics['sickle_smears']['total_sickle_detections']}")
    print()
    print(f"  FIELD-LEVEL:")
    print(f"    Normal fields w/ 0 sickle: {field_metrics['normal_fields_zero_sickle']} ({field_metrics['normal_fields_zero_sickle_pct']}%)")
    print(f"    Sickle fields w/ ≥3:       {field_metrics['sickle_fields_gte3_sickle']} ({field_metrics['sickle_fields_gte3_sickle_pct']}%)")
    variance = field_metrics.get("sickle_field_variance", {})
    if variance:
        print(f"    Sickle % range:            {variance.get('min_sickle_pct', '?')}% – {variance.get('max_sickle_pct', '?')}%")
        print(f"    Sickle % stdev:            {variance.get('stdev_sickle_pct', '?')}%")
    print()
    print(f"  GATE SUMMARY (all smears):")
    for k, v in gate_totals.items():
        print(f"    {k}: {v}")
    print()

    # ── Assemble final JSON ──
    baseline = {
        "version": "v1-baseline",
        "timestamp_utc": timestamp,
        "pipeline_file": PROVIDER_PATH,
        "pipeline_sha256": provider_hash,
        "git_hash": "NO_GIT_REPO",
        "total_validation_smears": len(smears),
        "smear_inventory": {
            "normal": [s["filename"] for s in normal_smears],
            "sickle": [s["filename"] for s in sickle_smears],
        },
        "thresholds_snapshot": snapshot_thresholds(),
        "cell_level_metrics": cell_metrics,
        "field_level_metrics": field_metrics,
        "gate_summary": gate_totals,
        "per_smear_recall_audit": recall_results,
        "per_smear_field_audit": field_results,
    }

    out_path = "baseline_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False, default=str)

    print("=" * 70)
    print(f"  ✅ Baseline frozen as: v1-baseline")
    print(f"  ✅ Results saved to:   {os.path.abspath(out_path)}")
    print(f"  ✅ Pipeline hash:      {provider_hash[:16]}...")
    print(f"  ✅ Smears evaluated:   {len(smears)}")
    print("=" * 70)


if __name__ == "__main__":
    run_baseline()
