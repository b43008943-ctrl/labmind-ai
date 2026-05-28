"""
LabMind — Large-Scale FP/FN Validation Script
Tests the active V1Provider's CNN + morphology dual-gate on 50 labeled cell crops.

Review set:
  - 20 confirmed NORMAL  (from dataset_v1_2class/val/normal/)
  - 20 confirmed SICKLE  (from dataset_v1_2class/val/sickle/)
  - 10 BORDERLINE/ARTIFACT (from new_raw_images/ — unlabeled, varied quality)
"""
import os, sys, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import warnings
warnings.filterwarnings("ignore")

import cv2
import numpy as np
import torch
from torchvision import transforms

from app.providers.ai_provider_v1 import V1Provider, CellClassifierCNN


def classify_single_crop(crop_path, provider):
    """
    Classify a single cell crop using the same CNN + morphology dual-gate
    that _classify_rbc uses inside the active V1 pipeline.
    Returns a dict with label, confidence, and morphology features.
    """
    img = cv2.imread(crop_path)
    if img is None:
        return {"error": "unreadable", "label": "error"}

    h, w = img.shape[:2]

    # ── Blur filter (same as _classify_rbc) ──
    gray_crop = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray_crop, cv2.CV_64F).var()
    if blur_score < 100:
        return {
            "label": "Normal", "confidence": 0.5,
            "sickle_prob": 0.0, "blur_score": round(blur_score, 1),
            "rejected_reason": "blur",
            "aspect_ratio": 0, "circularity": 0, "solidity": 0,
        }

    # ── Min crop size ──
    if w < 20 or h < 20:
        return {
            "label": "reject", "confidence": 0,
            "sickle_prob": 0.0, "blur_score": round(blur_score, 1),
            "rejected_reason": "too_small",
            "aspect_ratio": 0, "circularity": 0, "solidity": 0,
        }

    # ── CNN inference ──
    tensor = provider._transform(img).unsqueeze(0).to(provider._device)
    with torch.no_grad():
        logits = provider._cnn_model(tensor)
        probs = torch.softmax(logits, dim=1)[0]

    cnn_probs = {}
    for cls_idx, cls_name in provider._cnn_class_map.items():
        cnn_probs[cls_name] = round(probs[cls_idx].item(), 4)

    sickle_idx = {v: k for k, v in provider._cnn_class_map.items()}.get("sickle")
    sickle_prob = probs[sickle_idx].item() if sickle_idx is not None else 0

    top_idx = probs.argmax().item()
    top_prob = probs[top_idx].item()
    cnn_label = provider._cnn_class_map.get(top_idx, "unknown")
    if top_prob < 0.5:
        cnn_label = "uncertain"

    # ── Morphology ──
    morphology_abnormal = False
    circularity = aspect_ratio = solidity = 0.0

    blurred = cv2.GaussianBlur(gray_crop, (5, 5), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(blurred)
    norm = cv2.normalize(clahe, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    at = cv2.adaptiveThreshold(norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 15, 2)
    k_large = np.ones((5, 5), np.uint8)
    at = cv2.morphologyEx(at, cv2.MORPH_CLOSE, k_large, iterations=2)
    k_small = np.ones((3, 3), np.uint8)
    at = cv2.dilate(at, k_small, iterations=1)
    at = cv2.erode(at, k_small, iterations=1)

    ct, _ = cv2.findContours(at, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if ct:
        mc2 = max(ct, key=cv2.contourArea)
        m_area = cv2.contourArea(mc2)
        if m_area >= 30:
            perim = cv2.arcLength(mc2, True)
            circularity = (4 * np.pi * m_area) / (perim ** 2) if perim > 0 else 1.0
            rect = cv2.minAreaRect(mc2)
            rw, rh = rect[1]
            aspect_ratio = max(rw, rh) / (min(rw, rh) + 1e-5)
            hull = cv2.convexHull(mc2)
            hull_area = cv2.contourArea(hull)
            solidity = m_area / float(hull_area) if hull_area > 0 else 0.0

            if circularity > 0.78 or aspect_ratio < 1.40:
                morphology_abnormal = False
            elif 1.40 <= aspect_ratio < 2.0 and solidity > 0.92:
                morphology_abnormal = False
            else:
                morphology_abnormal = True

    # ── Dual-gate decision (same as V1Provider) ──
    if cnn_label == "sickle" and sickle_prob >= 0.75 and morphology_abnormal:
        final_label = "Sickle"
        final_conf = round(sickle_prob, 4)
    elif cnn_label == "sickle":
        # CNN says sickle but insufficient evidence → downgrade
        final_label = "Normal"
        final_conf = round(1.0 - sickle_prob, 4)
    else:
        final_label = "Normal"
        final_conf = round(1.0 - sickle_prob, 4)

    return {
        "label": final_label,
        "confidence": final_conf,
        "sickle_prob": round(sickle_prob, 4),
        "cnn_label": cnn_label,
        "blur_score": round(blur_score, 1),
        "aspect_ratio": round(aspect_ratio, 3),
        "circularity": round(circularity, 3),
        "solidity": round(solidity, 3),
        "morphology_abnormal": morphology_abnormal,
        "rejected_reason": None,
    }


def main():
    random.seed(42)

    # ── Build review set ──
    normal_dir = "dataset_v1_2class/val/normal"
    sickle_dir = "dataset_v1_2class/val/sickle"
    borderline_dir = "new_raw_images"

    normal_files = sorted(os.listdir(normal_dir))
    sickle_files = sorted(os.listdir(sickle_dir))
    border_files = sorted(os.listdir(borderline_dir))

    # Select 20 normal, 20 sickle, 10 borderline
    random.shuffle(normal_files)
    random.shuffle(sickle_files)
    random.shuffle(border_files)

    normal_set = [(os.path.join(normal_dir, f), "normal", f) for f in normal_files[:20]]
    sickle_set = [(os.path.join(sickle_dir, f), "sickle", f) for f in sickle_files[:20]]
    border_set = [(os.path.join(borderline_dir, f), "borderline", f) for f in border_files[:10]]

    print("=" * 78)
    print("  LabMind FP/FN Validation — V1 Dual-Gate (CNN ≥0.75 + Morphology)")
    print("=" * 78)

    # Load provider
    provider = V1Provider()
    print(f"  Classifier: {provider._classifier_mode}, {provider._cnn_num_classes}-class")
    print(f"  Review set: {len(normal_set)} normal + {len(sickle_set)} sickle + {len(border_set)} borderline")
    print()

    all_results = []

    for group_name, group_set in [("NORMAL", normal_set), ("SICKLE", sickle_set), ("BORDERLINE", border_set)]:
        print(f"  ── {group_name} ({'ground truth' if group_name != 'BORDERLINE' else 'unlabeled'}) ──")
        print(f"  {'File':<22} {'Pred':>7} {'Conf':>6} {'CNN_S':>6} {'Blur':>7} {'AR':>5} {'Circ':>5} {'Sol':>5} {'Morph':>5} {'Note'}")
        print(f"  {'-'*22} {'-'*7} {'-'*6} {'-'*6} {'-'*7} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*10}")

        for path, expected, fname in group_set:
            r = classify_single_crop(path, provider)
            r["file"] = fname
            r["expected"] = expected

            note = ""
            if r.get("rejected_reason"):
                note = f"[{r['rejected_reason']}]"
            elif expected == "normal" and r["label"] == "Sickle":
                note = "** FP **"
            elif expected == "sickle" and r["label"] == "Normal":
                note = "** FN **"
            elif expected == "sickle" and r["label"] == "Sickle":
                note = "TP"
            elif expected == "normal" and r["label"] == "Normal":
                note = "TN"

            r["note"] = note
            all_results.append(r)

            morph = "Y" if r.get("morphology_abnormal") else "N"
            print(f"  {fname:<22} {r['label']:>7} {r['confidence']:>5.3f} {r['sickle_prob']:>5.3f}"
                  f" {r['blur_score']:>7.1f} {r['aspect_ratio']:>5.2f} {r['circularity']:>5.3f}"
                  f" {r['solidity']:>5.3f} {morph:>5} {note}")
        print()

    # ── Summary ──
    normal_results = [r for r in all_results if r["expected"] == "normal"]
    sickle_results = [r for r in all_results if r["expected"] == "sickle"]
    border_results = [r for r in all_results if r["expected"] == "borderline"]

    fp = sum(1 for r in normal_results if r["label"] == "Sickle")
    fn = sum(1 for r in sickle_results if r["label"] == "Normal")
    tp = sum(1 for r in sickle_results if r["label"] == "Sickle")
    tn = sum(1 for r in normal_results if r["label"] == "Normal")

    blur_rejected = sum(1 for r in all_results if r.get("rejected_reason") == "blur")
    size_rejected = sum(1 for r in all_results if r.get("rejected_reason") == "too_small")

    sickle_confs = [r["sickle_prob"] for r in all_results if r["label"] == "Sickle"]
    avg_sickle_conf = sum(sickle_confs) / len(sickle_confs) if sickle_confs else 0

    border_sickle = sum(1 for r in border_results if r["label"] == "Sickle")

    print("=" * 78)
    print("  VALIDATION SUMMARY")
    print("=" * 78)
    print()
    print(f"  Confirmed NORMAL samples:    {len(normal_results)} tested")
    print(f"    True Negatives (TN):       {tn}")
    print(f"    False Positives (FP):      {fp}   {'⚠️ CONCERN' if fp > 0 else '✅'}")
    print()
    print(f"  Confirmed SICKLE samples:    {len(sickle_results)} tested")
    print(f"    True Positives (TP):       {tp}")
    print(f"    False Negatives (FN):      {fn}   {'⚠️ CONCERN' if fn > len(sickle_results) * 0.5 else '✅' if fn < len(sickle_results) * 0.3 else '⚠️'}")
    print()
    print(f"  BORDERLINE samples:          {len(border_results)} tested")
    print(f"    Classified as Sickle:      {border_sickle}")
    print(f"    Classified as Normal:      {len(border_results) - border_sickle}")
    print()
    print(f"  Quality rejections:")
    print(f"    Blur rejected:             {blur_rejected}")
    print(f"    Size rejected:             {size_rejected}")
    print()
    print(f"  Avg sickle confidence (TP):  {avg_sickle_conf:.3f}")
    print()

    if len(normal_results) > 0:
        fp_rate = fp / len(normal_results) * 100
        print(f"  FP rate (normal→sickle):     {fp}/{len(normal_results)} = {fp_rate:.1f}%")
    if len(sickle_results) > 0:
        fn_rate = fn / len(sickle_results) * 100
        sensitivity = tp / len(sickle_results) * 100
        print(f"  FN rate (sickle→normal):     {fn}/{len(sickle_results)} = {fn_rate:.1f}%")
        print(f"  Sensitivity (recall):        {tp}/{len(sickle_results)} = {sensitivity:.1f}%")
    if len(normal_results) > 0:
        specificity = tn / len(normal_results) * 100
        print(f"  Specificity:                 {tn}/{len(normal_results)} = {specificity:.1f}%")

    print()
    print("=" * 78)

    # Save JSON
    with open("validation_results_large.json", "w") as f:
        json.dump({
            "summary": {
                "normal_tested": len(normal_results), "sickle_tested": len(sickle_results),
                "borderline_tested": len(border_results),
                "TP": tp, "TN": tn, "FP": fp, "FN": fn,
                "blur_rejected": blur_rejected, "size_rejected": size_rejected,
                "avg_sickle_confidence": round(avg_sickle_conf, 4),
                "borderline_sickle": border_sickle,
            },
            "results": all_results,
        }, f, indent=2, default=str)
    print("  Full results → validation_results_large.json")


if __name__ == "__main__":
    main()
