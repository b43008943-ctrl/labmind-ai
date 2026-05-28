"""
LabMind AI — Diagnostic Script for normal_02 Regression
=======================================================
Investigates why the new robust CNN model classifies validation_smears/normal/normal_02.jpg.jpg 
as SICKLE_SCREEN_POSITIVE with 40 false positives.

Steps:
1. Runs both old and new models on normal_02.
2. Compares cell-level CNN and morphology scores.
3. Generates statistical breakdown and histogram.
4. Generates visual grid (diagnose_normal02_grid.png).
5. Checks dataset_clean/splits/train/ for contamination.
"""

import os
import json
import logging
from pathlib import Path

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch

from app.providers.ai_provider_v1 import V1Provider, CellClassifierCNN

logging.getLogger("labmind.v1provider").setLevel(logging.WARNING)

BASE_DIR = Path(__file__).resolve().parent
TARGET_FILE = BASE_DIR / "validation_smears" / "normal" / "normal_02.jpg.jpg"
SICKLE_REF = BASE_DIR / "validation_smears" / "sickle" / "sickle_01.jpg.jpg"

OLD_WEIGHTS = BASE_DIR / "cell_classifier_2class_finetuned_best.pth"
NEW_WEIGHTS = BASE_DIR / "cell_classifier_2class_robust_best.pth"

OUTPUT_REPORT = BASE_DIR / "diagnose_normal02_report.json"
OUTPUT_GRID = BASE_DIR / "diagnose_normal02_grid.png"

def run_model(weights_path, image_path):
    print(f"  [>] Running V1Provider on {image_path.name} with {weights_path.name[:15]}...")
    provider = V1Provider()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    cnn = CellClassifierCNN(num_classes=2).to(device)
    cnn.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
    cnn.eval()
    
    V1Provider._cnn_model = cnn
    V1Provider._classifier_mode = "diagnosis"
    
    res = provider.analyze(str(image_path))
    return res

def check_contamination():
    print(f"  [>] Checking dataset_clean/splits/train/ for 'normal_02'...")
    train_dir = BASE_DIR / "dataset_clean" / "splits" / "train"
    matches = []
    if train_dir.exists():
        for f in train_dir.rglob("*.png"):
            if "normal_02" in f.name:
                matches.append(str(f.relative_to(BASE_DIR)))
        for f in train_dir.rglob("*.jpg"):
            if "normal_02" in f.name:
                matches.append(str(f.relative_to(BASE_DIR)))
    return matches

def main():
    print("\n" + "=" * 80)
    print("Normal_02 FP Diagnostic Analysis")
    print("=" * 80)
    
    # Run Old
    res_old = run_model(OLD_WEIGHTS, TARGET_FILE)
    cells_old = res_old["cell_details"]
    
    # Run New
    res_new = run_model(NEW_WEIGHTS, TARGET_FILE)
    cells_new = res_new["cell_details"]
    
    # Run New on Sickle_01 (for true positive visual comparison)
    res_new_sickle = run_model(NEW_WEIGHTS, SICKLE_REF)
    cells_new_sickle = res_new_sickle["cell_details"]

    # ── Metric Comparison ──
    def extract_stats(cells):
        sick_scores = [c.get("cnn_scores", {}).get("sickle", 0) for c in cells if "cnn_scores" in c]
        sick_cells = [c for c in cells if c.get("class_name") == "sickle"]
        sick_sick_scores = [c.get("cnn_scores", {}).get("sickle", 0) for c in sick_cells]
        
        return {
            "total": len(cells),
            "normal": sum(1 for c in cells if c.get("class_name") != "sickle"),
            "sickle": len(sick_cells),
            "avg_all": round(sum(sick_scores) / len(sick_scores), 4) if sick_scores else 0,
            "avg_sickle": round(sum(sick_sick_scores) / len(sick_sick_scores), 4) if sick_sick_scores else 0,
            "max": round(max(sick_scores), 4) if sick_scores else 0,
            "min_sickle": round(min(sick_sick_scores), 4) if sick_sick_scores else 0,
        }
        
    stats_old = extract_stats(cells_old)
    stats_new = extract_stats(cells_new)
    
    print("\n" + "-" * 70)
    print(f"{'Metric':<35s} | {'Old Model':<15s} | {'New Model':<15s}")
    print("-" * 70)
    print(f"{'Total cells detected':<35s} | {stats_old['total']:<15d} | {stats_new['total']:<15d}")
    print(f"{'Classified as normal':<35s} | {stats_old['normal']:<15d} | {stats_new['normal']:<15d}")
    print(f"{'Classified as sickle':<35s} | {stats_old['sickle']:<15d} | {stats_new['sickle']:<15d}")
    print(f"{'Avg cnn_sick score (all cells)':<35s} | {stats_old['avg_all']:<15.4f} | {stats_new['avg_all']:<15.4f}")
    print(f"{'Avg cnn_sick score (sickle)':<35s} | {stats_old['avg_sickle']:<15.4f} | {stats_new['avg_sickle']:<15.4f}")
    print(f"{'Max cnn_sick score':<35s} | {stats_old['max']:<15.4f} | {stats_new['max']:<15.4f}")
    print(f"{'Min cnn_sick score (sickle)':<35s} | {stats_old['min_sickle']:<15.4f} | {stats_new['min_sickle']:<15.4f}")

    # ── Analyze the 40 FP cells ──
    fp_cells = [c for c in cells_new if c.get("class_name") == "sickle"]
    # Sort them by their position mapping (using x1+y1 as a proxy block) or just take them
    
    fp_scores = [c.get("cnn_scores", {}).get("sickle", 0) for c in fp_cells]
    bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    hist = np.histogram(fp_scores, bins=bins)[0]
    
    print("\n" + "-" * 70)
    print("FALSE POSITIVE DISTRIBUTION (cnn_sick score)")
    print(f"  0.5-0.6: {hist[0]} cells")
    print(f"  0.6-0.7: {hist[1]} cells")
    print(f"  0.7-0.8: {hist[2]} cells")
    print(f"  0.8-0.9: {hist[3]} cells")
    print(f"  0.9-1.0: {hist[4]} cells")
    
    avg_ar = np.mean([c.get("morphology", {}).get("ar", 1.0) for c in fp_cells]) if fp_cells else 1.0
    avg_circ = np.mean([c.get("morphology", {}).get("circ", 1.0) for c in fp_cells]) if fp_cells else 1.0
    avg_sol = np.mean([c.get("morphology", {}).get("sol", 1.0) for c in fp_cells]) if fp_cells else 1.0
    
    print("\nFALSE POSITIVE MORPHOLOGY (Averages)")
    print(f"  Aspect Ratio: {avg_ar:.2f}")
    print(f"  Circularity:  {avg_circ:.2f}")
    print(f"  Solidity:     {avg_sol:.2f}")
    
    routes = {}
    for c in fp_cells:
        r = c.get("classify_route", "unknown")
        routes[r] = routes.get(r, 0) + 1
    print(f"  Gate mechanisms: {routes}")

    # ── Check Contamination ──
    contamination = check_contamination()
    print("\n" + "-" * 70)
    print(f"CONTAMINATION CHECK: {len(contamination)} suspicious files found in train split.")
    if contamination:
        for f in contamination[:5]:
            print(f"  - {f}")
        if len(contamination) > 5: print(f"  ... and {len(contamination)-5} more")

    # ── Recommendation ──
    print("\n" + "-" * 70)
    print("RECOMMENDATION:")
    rec = "Z"
    if contamination:
        rec = "C) Training data contamination found → rebuild dataset without contaminated samples"
    elif avg_ar < 1.15 and avg_circ > 0.7:
        rec = "B) The false positives are clearly round normal cells → systematic bias → check training data limits"
    else:
        rec = "A) False positives look like morphological confusion → need hard negative mining (more normal_02-like crops)"
    print(rec)
    print("-" * 70)

    # ── Visual Grid ──
    print("Generating visual grid...")
    img = cv2.imread(str(TARGET_FILE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    img_sickle = cv2.imread(str(SICKLE_REF))
    img_sickle = cv2.cvtColor(img_sickle, cv2.COLOR_BGR2RGB)
    
    # 1. 10 normal cells correctly classified by OLD
    normal_old = [c for c in cells_old if c.get("class_name") == "rbc"][:10]
    
    # Match the SAME cells in the NEW output by bounding box overlap
    def find_matching_cell(c_old, cells_list):
        cx = (c_old["x1"] + c_old["x2"]) / 2
        cy = (c_old["y1"] + c_old["y2"]) / 2
        for c_new in cells_list:
            if c_new["x1"] <= cx <= c_new["x2"] and c_new["y1"] <= cy <= c_new["y2"]:
                return c_new
        return None

    matched_new = [find_matching_cell(c, cells_new) for c in normal_old]
    matched_new = [c for c in matched_new if c is not None]
    
    tp_cells = [c for c in cells_new_sickle if c.get("class_name") == "sickle"][:10]

    def crop_cell(image, c, padding=10):
        h, w = image.shape[:2]
        x1 = max(0, c["x1"] - padding)
        y1 = max(0, c["y1"] - padding)
        x2 = min(w, c["x2"] + padding)
        y2 = min(h, c["y2"] + padding)
        return image[y1:y2, x1:x2]

    # Plot
    fig, axes = plt.subplots(4, 10, figsize=(20, 9))
    fig.subplots_adjust(wspace=0.1, hspace=0.3)
    fig.suptitle("normal_02.jpg false positive regression", fontsize=16)

    # Row 1: Normal cells (OLD model score)
    for i in range(10):
        ax = axes[0, i]
        ax.axis('off')
        if i < len(normal_old):
            c = normal_old[i]
            crop = crop_cell(img, c)
            ax.imshow(crop)
            score = c.get("cnn_scores", {}).get("sickle", 0)
            ax.set_title(f"OLD sick={score:.2f}", fontsize=8, color="green" if score < 0.5 else "red")
            
    # Row 2: Same cells (NEW model score)
    for i in range(10):
        ax = axes[1, i]
        ax.axis('off')
        if i < len(matched_new):
            c = matched_new[i]
            crop = crop_cell(img, c)
            ax.imshow(crop)
            score = c.get("cnn_scores", {}).get("sickle", 0)
            ax.set_title(f"NEW sick={score:.2f}", fontsize=8, color="green" if score < 0.5 else "red")

    # Row 3: FP cells from NEW model
    for i in range(10):
        ax = axes[2, i]
        ax.axis('off')
        if i < len(fp_cells):
            c = fp_cells[i]
            crop = crop_cell(img, c)
            ax.imshow(crop)
            score = c.get("cnn_scores", {}).get("sickle", 0)
            ax.set_title(f"FP sick={score:.2f}", fontsize=8, color="red")
            
    # Row 4: TP cells from SICKLE_01
    for i in range(10):
        ax = axes[3, i]
        ax.axis('off')
        if i < len(tp_cells):
            c = tp_cells[i]
            crop = crop_cell(img_sickle, c)
            ax.imshow(crop)
            score = c.get("cnn_scores", {}).get("sickle", 0)
            ax.set_title(f"TP sick={score:.2f}", fontsize=8, color="red")
            
    axes[0,0].set_ylabel("OLD normal", visible=True)
    axes[1,0].set_ylabel("NEW same", visible=True)
    axes[2,0].set_ylabel("NEW FP", visible=True)
    axes[3,0].set_ylabel("NEW TP", visible=True)
    
    plt.savefig(str(OUTPUT_GRID), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved visual grid to {OUTPUT_GRID.name}")

    report = {
        "stats_old": stats_old,
        "stats_new": stats_new,
        "false_positives": {
            "count": len(fp_cells),
            "score_histogram": {
                "0.5_0.6": int(hist[0]),
                "0.6_0.7": int(hist[1]),
                "0.7_0.8": int(hist[2]),
                "0.8_0.9": int(hist[3]),
                "0.9_1.0": int(hist[4]),
            },
            "avg_ar": float(avg_ar),
            "avg_circ": float(avg_circ),
            "avg_sol": float(avg_sol),
            "gates_passed": routes
        },
        "contamination_found": len(contamination),
        "recommendation": rec
    }
    with open(OUTPUT_REPORT, "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()
