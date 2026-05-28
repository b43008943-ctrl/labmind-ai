"""
LabMind AI — Regression Test for Robust CNN Model
=================================================
Runs the V1Provider pipeline on the 11 validation smears using the newly trained 
`cell_classifier_2class_robust_best.pth` and compares against `baseline_results.json`.
"""

import json
import logging
from pathlib import Path
import torch

from app.providers.ai_provider_v1 import V1Provider, CellClassifierCNN

# Supress noisy logs during pipeline
logging.getLogger("labmind.v1provider").setLevel(logging.WARNING)

BASE_DIR = Path(__file__).resolve().parent
BASELINE_PATH = BASE_DIR / "baseline_results.json"
NEW_WEIGHTS_PATH = BASE_DIR / "cell_classifier_2class_robust_best.pth"
VALIDATION_DIR = BASE_DIR / "validation_smears"
OUTPUT_PATH = BASE_DIR / "regression_test_robust.json"

def load_baseline():
    """Extracts Old metrics from the baseline JSON."""
    if not BASELINE_PATH.exists():
        raise FileNotFoundError(f"Missing {BASELINE_PATH.name}")

    with open(BASELINE_PATH, "r") as f:
        data = json.load(f)
    
    baseline = {}
    for sm_type, key in [("normal", "normal_smears"), ("sickle", "sickle_smears")]:
        smears = data.get("cell_level_metrics", {}).get(key, {}).get("per_smear_sickle", [])
        for entry in smears:
            fname = entry["label"]
            sickle = entry["sickle"]
            total = entry["total"]
            pct = (sickle / total * 100) if total > 0 else 0.0
            
            # Derive standard screening result based on the baseline counts using standard logic
            res = V1Provider._interpret_field(sickle, total, pct)
            
            baseline[fname] = {
                "category": sm_type,
                "sickle_count": sickle,
                "sickle_percentage": round(pct, 2),
                "screening_result": res["screening_result"]
            }
    
    return baseline

def get_status(category, old_sickle, new_sickle):
    if old_sickle == new_sickle:
        return "SAME"
    if category == "normal":
        return "BETTER" if new_sickle < old_sickle else "WORSE"
    else:  # sickle
        return "BETTER" if new_sickle > old_sickle else "WORSE"


def main():
    print("LabMind AI — Robust Model Regression Tester")
    print("=" * 80)
    
    # ── 1. Load Baseline ──
    print("Loading baseline results...")
    baseline = load_baseline()
    print(f"Loaded {len(baseline)} validation images from baseline.")

    # ── 2. Initialize and Monkey-patch V1Provider ──
    print(f"Loading new CNN weights: {NEW_WEIGHTS_PATH.name}...")
    provider = V1Provider()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    new_cnn = CellClassifierCNN(num_classes=2).to(device)
    new_cnn.load_state_dict(torch.load(str(NEW_WEIGHTS_PATH), map_location=device, weights_only=True))
    new_cnn.eval()
    
    # Temporary override mapping
    V1Provider._cnn_model = new_cnn
    V1Provider._classifier_mode = "robust_tester"
    print("Monkey-patch successful. Running inference...")
    
    # ── 3. Run Pipeline ──
    results = {}
    validation_files = list(VALIDATION_DIR.rglob("*.jpg")) + list(VALIDATION_DIR.rglob("*.jpg.jpg"))
    # ensure uniqueness since *.jpg matches .jpg.jpg as well
    unique_files = {f.name: f for f in validation_files}
    
    # Run only on files that exist in the baseline
    files_to_run = [f for name, f in unique_files.items() if name in baseline]
    
    total_images = len(files_to_run)
    current = 0
    for file_path in files_to_run:
        current += 1
        name = file_path.name
        print(f"  [{current}/{total_images}] Testing {name} ...", end="", flush=True)
        
        # Run inference using the overridden CNN
        res = provider.analyze(str(file_path))
        
        results[name] = {
            "total_cells": res["total_cells"],
            "sickle_count": res["sickle_count"],
            "normal_count": res["normal_count"],
            "sickle_percentage": res["sickle_percentage"],
            "screening_result": res["field_interpretation"]["screening_result"]
        }
        print(" done.")

    # ── 4. Compare Results ──
    print("\n" + "=" * 95)
    print(f"{'Image':<25s} | {'OLD sickle':<10s} | {'NEW sickle':<10s} | {'OLD %':<7s} | {'NEW %':<7s} | {'OLD result':<12s} | {'NEW result':<12s} | {'Status':<10s}")
    print("-" * 95)
    
    summary = {
        "normal_improved": 0,
        "normal_worse": 0,
        "sickle_improved": 0,
        "sickle_worse": 0,
    }
    
    for name in baseline.keys():
        if name not in results:
            continue
        
        old = baseline[name]
        new = results[name]
        
        status = get_status(old['category'], old['sickle_count'], new['sickle_count'])
        
        if status == "BETTER":
            if old['category'] == "normal": summary["normal_improved"] += 1
            else: summary["sickle_improved"] += 1
        elif status == "WORSE":
            if old['category'] == "normal": summary["normal_worse"] += 1
            else: summary["sickle_worse"] += 1
            
        print(f"{name:<25s} | {old['sickle_count']:<10d} | {new['sickle_count']:<10d} | "
              f"{old['sickle_percentage'] :>5.1f}% | {new['sickle_percentage'] :>5.1f}% | "
              f"{old['screening_result'][:12]:<12s} | {new['screening_result'][:12]:<12s} | "
              f"{status:<10s}")

    # ── 5. Verdict ──
    print("\n" + "=" * 80)
    print("REGRESSION VERDICT")
    print(f"Normal smears: {summary['normal_improved']} improved, {summary['normal_worse']} got worse.")
    print(f"Sickle smears: {summary['sickle_improved']} improved, {summary['sickle_worse']} got worse.")
    
    normal_04_fp_fixed = False
    sickle_05_fn_fixed = False
    
    if "normal_04.jpg.jpg" in results:
        old_val = baseline["normal_04.jpg.jpg"]["sickle_count"]
        new_val = results["normal_04.jpg.jpg"]["sickle_count"]
        normal_04_fp_fixed = new_val < old_val
        print(f"- normal_04 FP decreased: {normal_04_fp_fixed} (was {old_val}, now {new_val})")
        
    if "sickle_05.jpg.jpg" in results:
        old_val = baseline["sickle_05.jpg.jpg"]["sickle_count"]
        new_val = results["sickle_05.jpg.jpg"]["sickle_count"]
        sickle_05_fn_fixed = new_val > old_val
        print(f"- sickle_05 detection improved: {sickle_05_fn_fixed} (was {old_val}, now {new_val})")

    pass_verdict = (summary["normal_worse"] == 0 and summary["sickle_worse"] == 0) or \
                   ((summary["normal_improved"] + summary["sickle_improved"]) > (summary["normal_worse"] + summary["sickle_worse"]))
    overall = "PASS" if pass_verdict else "FAIL"
    print(f"OVERALL: {overall}")
    
    # ── 6. Save JSON ──
    output_data = {
        "verdict": overall,
        "summary": summary,
        "comparison": {
            name: {
                "old": baseline[name],
                "new": results.get(name, None),
                "status": get_status(baseline[name]["category"], baseline[name]["sickle_count"], results.get(name, {"sickle_count": -1})["sickle_count"])
            }
            for name in baseline
            if name in results
        }
    }
    
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nSaved full results to {OUTPUT_PATH.name}")

if __name__ == "__main__":
    main()
