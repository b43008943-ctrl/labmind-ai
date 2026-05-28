"""
LabMind AI — Full Pipeline YOLO Detection Diagnostic
=====================================================

Comprehensive diagnostic of the YOLO detection stage across all available
full-field blood smear image sources.

Uses the EXACT same parameters as V1Provider (FROZEN):
  - yolo_conf  = 0.05
  - tile_size  = 640
  - overlap    = 0.25
  - nms_iou    = 0.35
  - border skip = 5px

This is DIAGNOSTIC ONLY — no models or source files are modified.
"""

import json
import os
import random
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import torchvision

# ── Reproducibility ──
random.seed(42)
np.random.seed(42)

# ──────────────────────────────────────────────────────────
#  CONFIGURATION — mirrors V1Provider exactly
# ──────────────────────────────────────────────────────────

YOLO_CONF = 0.05
TILE_SIZE = 640
OVERLAP_RATIO = 0.25
NMS_IOU = 0.35
BORDER_SKIP = 5
MIN_TILE_DIM = 100

YOLO_CLASS_MAP = {0: "plt", 1: "rbc", 2: "wbc", 3: "sickle"}

# ── Paths ──
SCRIPT_DIR = Path(__file__).resolve().parent
YOLO_MODEL_PATH = SCRIPT_DIR / "blood_ai_v2.pt"
REPORTS_DIR = SCRIPT_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Source directories ──
SOURCE_DIRS = {
    "validation_smears": {
        "paths": [
            SCRIPT_DIR / "validation_smears" / "normal",
            SCRIPT_DIR / "validation_smears" / "sickle",
        ],
        "label": "Validation Smears (original test set)",
    },
    "erythrocytesIDB": {
        "paths": [
            SCRIPT_DIR / "dataset_robust" / "raw" / "source_erythrocytesIDB" / "sources",
        ],
        "label": "ErythrocytesIDB — Cuba (sickle patients)",
    },
    "kaggle_positive": {
        "paths": [
            SCRIPT_DIR / "dataset_robust" / "raw" / "source_kaggle_scd" / "Positive" / "Labelled",
            SCRIPT_DIR / "dataset_robust" / "raw" / "source_kaggle_scd" / "Positive" / "Unlabelled",
        ],
        "label": "Kaggle SCD — Positive (Uganda)",
    },
    "kaggle_negative": {
        "paths": [
            SCRIPT_DIR / "dataset_robust" / "raw" / "source_kaggle_scd" / "Negative",
        ],
        "label": "Kaggle SCD — Negative (Uganda)",
    },
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def collect_images(paths: list[Path]) -> list[Path]:
    """Collect all image files from a list of directories."""
    images = []
    for p in paths:
        if not p.exists():
            continue
        for f in sorted(p.iterdir()):
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                images.append(f)
    return images


# ══════════════════════════════════════════════════════════
#  STEP 1 — SCAN AVAILABLE IMAGES
# ══════════════════════════════════════════════════════════

def scan_source(name: str, images: list[Path]) -> dict:
    """Compute image statistics for a source."""
    if not images:
        return {
            "source": name,
            "count": 0,
            "dimensions": None,
            "color_profile": None,
            "note": "No images found",
        }

    widths, heights = [], []
    mean_r, mean_g, mean_b = [], [], []

    for img_path in images:
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        widths.append(w)
        heights.append(h)
        # BGR → RGB means
        mean_b.append(float(img[:, :, 0].mean()))
        mean_g.append(float(img[:, :, 1].mean()))
        mean_r.append(float(img[:, :, 2].mean()))

    if not widths:
        return {"source": name, "count": len(images), "dimensions": None,
                "color_profile": None, "note": "All images unreadable"}

    return {
        "source": name,
        "count": len(images),
        "readable": len(widths),
        "dimensions": {
            "avg_w": round(np.mean(widths), 1),
            "avg_h": round(np.mean(heights), 1),
            "min_w": int(np.min(widths)),
            "min_h": int(np.min(heights)),
            "max_w": int(np.max(widths)),
            "max_h": int(np.max(heights)),
            "avg_megapixels": round(np.mean([w * h for w, h in zip(widths, heights)]) / 1e6, 2),
        },
        "color_profile": {
            "mean_R": round(np.mean(mean_r), 2),
            "mean_G": round(np.mean(mean_g), 2),
            "mean_B": round(np.mean(mean_b), 2),
        },
    }


# ══════════════════════════════════════════════════════════
#  STEP 2/3 — YOLO DETECTION DIAGNOSTIC
# ══════════════════════════════════════════════════════════

def run_yolo_tiling(yolo_model, img: np.ndarray) -> dict:
    """
    Run YOLO tiling + NMS exactly as V1Provider does.

    Returns raw and post-NMS detection data with full statistics.
    """
    h_img, w_img = img.shape[:2]
    tile_size = TILE_SIZE
    overlap = int(tile_size * OVERLAP_RATIO)
    step = tile_size - overlap

    raw_boxes, raw_scores, raw_classes = [], [], []
    tile_count = 0

    for y in range(0, h_img, step):
        for x in range(0, w_img, step):
            y_end = min(y + tile_size, h_img)
            x_end = min(x + tile_size, w_img)
            tile = img[y:y_end, x:x_end]
            if tile.shape[0] < MIN_TILE_DIM or tile.shape[1] < MIN_TILE_DIM:
                continue
            tile_count += 1

            results = yolo_model(tile, conf=YOLO_CONF, imgsz=tile_size, verbose=False)
            for result in results:
                boxes = result.boxes.xyxy.cpu().numpy()
                scores = result.boxes.conf.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy()
                for i, box in enumerate(boxes):
                    tx1, ty1, tx2, ty2 = map(int, box)
                    # Border skip — same as V1Provider line 270
                    if (tx1 <= BORDER_SKIP or ty1 <= BORDER_SKIP or
                            tx2 >= tile.shape[1] - BORDER_SKIP or
                            ty2 >= tile.shape[0] - BORDER_SKIP):
                        continue
                    raw_boxes.append([x + tx1, y + ty1, x + tx2, y + ty2])
                    raw_scores.append(float(scores[i]))
                    raw_classes.append(int(classes[i]))

    # ── NMS (class-aware, same as V1Provider) ──
    nms_boxes, nms_scores, nms_classes = [], [], []
    if raw_boxes:
        gb = torch.tensor(raw_boxes, dtype=torch.float32)
        gs = torch.tensor(raw_scores, dtype=torch.float32)
        gc = torch.tensor(raw_classes, dtype=torch.int64)
        keep = torchvision.ops.batched_nms(gb, gs, gc, NMS_IOU)
        for idx in keep:
            i = idx.item()
            nms_boxes.append(raw_boxes[i])
            nms_scores.append(raw_scores[i])
            nms_classes.append(raw_classes[i])

    # ── Statistics ──
    def box_stats(boxes, scores, classes):
        if not boxes:
            return {
                "count": 0, "avg_conf": 0, "min_conf": 0, "max_conf": 0,
                "avg_box_w": 0, "avg_box_h": 0,
                "min_box_w": 0, "min_box_h": 0,
                "max_box_w": 0, "max_box_h": 0,
                "class_counts": {},
                "conf_buckets": {"high_gt_0.3": 0, "medium_0.1_0.3": 0, "low_lt_0.1": 0},
            }
        ws = [b[2] - b[0] for b in boxes]
        hs = [b[3] - b[1] for b in boxes]
        cc = {}
        for c in classes:
            cn = YOLO_CLASS_MAP.get(c, f"unknown_{c}")
            cc[cn] = cc.get(cn, 0) + 1
        high = sum(1 for s in scores if s > 0.3)
        medium = sum(1 for s in scores if 0.1 <= s <= 0.3)
        low = sum(1 for s in scores if s < 0.1)
        return {
            "count": len(boxes),
            "avg_conf": round(float(np.mean(scores)), 4),
            "min_conf": round(float(np.min(scores)), 4),
            "max_conf": round(float(np.max(scores)), 4),
            "avg_box_w": round(float(np.mean(ws)), 1),
            "avg_box_h": round(float(np.mean(hs)), 1),
            "min_box_w": int(np.min(ws)),
            "min_box_h": int(np.min(hs)),
            "max_box_w": int(np.max(ws)),
            "max_box_h": int(np.max(hs)),
            "class_counts": cc,
            "conf_buckets": {"high_gt_0.3": high, "medium_0.1_0.3": medium, "low_lt_0.1": low},
        }

    return {
        "image_size": {"w": w_img, "h": h_img},
        "tile_count": tile_count,
        "raw": box_stats(raw_boxes, raw_scores, raw_classes),
        "nms": box_stats(nms_boxes, nms_scores, nms_classes),
        "nms_boxes": nms_boxes,
        "nms_scores": nms_scores,
        "nms_classes": nms_classes,
    }


def draw_diagnostic_image(img: np.ndarray, detection_result: dict,
                          image_name: str, source_label: str) -> str:
    """
    Draw ALL YOLO bounding boxes on the image, color-coded by confidence.
      Green  : conf > 0.3
      Yellow : 0.1 <= conf <= 0.3
      Red    : conf < 0.1
    Save to reports/ directory.
    """
    out = img.copy()
    boxes = detection_result["nms_boxes"]
    scores = detection_result["nms_scores"]
    classes = detection_result["nms_classes"]

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box)
        conf = scores[i]
        cls_name = YOLO_CLASS_MAP.get(classes[i], "?")

        if conf > 0.3:
            color = (0, 255, 0)   # Green — high confidence
        elif conf >= 0.1:
            color = (0, 255, 255)  # Yellow — medium
        else:
            color = (0, 0, 255)    # Red — low / suspicious

        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"{cls_name} {conf:.2f}"
        # Small text above box
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        cv2.rectangle(out, (x1, y1 - th - 4), (x1 + tw, y1), color, -1)
        cv2.putText(out, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                    (0, 0, 0), 1, cv2.LINE_AA)

    # ── Header overlay ──
    h_img, w_img = out.shape[:2]
    overlay = out.copy()
    oh, ow = 160, 520
    cv2.rectangle(overlay, (10, 10), (10 + ow, 10 + oh), (0, 0, 0), -1)
    out = cv2.addWeighted(overlay, 0.75, out, 0.25, 0)

    nms = detection_result["nms"]
    raw = detection_result["raw"]
    y_pos = 35
    cv2.putText(out, "YOLO DIAGNOSTIC", (20, y_pos),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
    y_pos += 25
    cv2.putText(out, f"Source: {source_label}", (20, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    y_pos += 22
    cv2.putText(out, f"Image: {image_name}  ({w_img}x{h_img})", (20, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    y_pos += 22
    cv2.putText(out, f"Tiles: {detection_result['tile_count']}  |  "
                     f"Raw dets: {raw['count']}  |  After NMS: {nms['count']}", (20, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    y_pos += 22
    cv2.putText(out, f"Conf: avg={nms['avg_conf']:.3f}  min={nms['min_conf']:.3f}  "
                     f"max={nms['max_conf']:.3f}", (20, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    y_pos += 22
    cv2.putText(out, f"Avg box: {nms['avg_box_w']:.0f}x{nms['avg_box_h']:.0f}px  |  "
                     f"Classes: {nms['class_counts']}", (20, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.40, (200, 200, 200), 1)

    # ── Legend ──
    leg_y = 10 + oh + 15
    cv2.putText(out, "Legend:", (15, leg_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    cv2.rectangle(out, (85, leg_y - 10), (95, leg_y), (0, 255, 0), -1)
    cv2.putText(out, ">0.3", (100, leg_y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
    cv2.rectangle(out, (145, leg_y - 10), (155, leg_y), (0, 255, 255), -1)
    cv2.putText(out, "0.1-0.3", (160, leg_y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
    cv2.rectangle(out, (225, leg_y - 10), (235, leg_y), (0, 0, 255), -1)
    cv2.putText(out, "<0.1", (240, leg_y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

    # ── Save ──
    safe_name = Path(image_name).stem
    out_path = str(REPORTS_DIR / f"diagnose_yolo_{safe_name}.png")
    cv2.imwrite(out_path, out)
    return out_path


def run_diagnostic_on_sample(yolo_model, images: list[Path], n: int,
                             source_key: str, source_label: str) -> list[dict]:
    """Run YOLO diagnostic on n randomly-selected images from a source."""
    if not images:
        print(f"  ⚠  No images found for {source_label}. Skipping.")
        return []

    sample = random.sample(images, min(n, len(images)))
    results = []

    for img_path in sample:
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  ⚠  Cannot read: {img_path}")
            continue

        print(f"  ▶ Processing {img_path.name} ({img.shape[1]}x{img.shape[0]}) ...")
        t0 = time.time()
        det = run_yolo_tiling(yolo_model, img)
        elapsed = time.time() - t0

        # Draw diagnostic image
        diag_path = draw_diagnostic_image(img, det, img_path.name, source_label)

        print(f"    Tiles: {det['tile_count']}")
        print(f"    Raw detections: {det['raw']['count']}")
        print(f"    After NMS: {det['nms']['count']}")
        print(f"    Avg conf: {det['nms']['avg_conf']:.4f}  "
              f"(min={det['nms']['min_conf']:.4f}, max={det['nms']['max_conf']:.4f})")
        print(f"    Avg box: {det['nms']['avg_box_w']:.0f}x{det['nms']['avg_box_h']:.0f}px")
        print(f"    Conf buckets: {det['nms']['conf_buckets']}")
        print(f"    Class counts: {det['nms']['class_counts']}")
        print(f"    Time: {elapsed:.2f}s")
        print(f"    Diagnostic image: {diag_path}")

        # Remove heavy arrays for JSON serialization
        result = {
            "image": img_path.name,
            "image_path": str(img_path),
            "source": source_key,
            "image_size": det["image_size"],
            "tile_count": det["tile_count"],
            "raw_detections": det["raw"]["count"],
            "nms_detections": det["nms"]["count"],
            "nms_stats": {k: v for k, v in det["nms"].items()
                          if k not in ("count",)},
            "raw_stats": {k: v for k, v in det["raw"].items()
                          if k not in ("count",)},
            "elapsed_seconds": round(elapsed, 2),
            "diagnostic_image": diag_path,
        }
        results.append(result)

    return results


# ══════════════════════════════════════════════════════════
#  STEP 4 — COMPARISON TABLE
# ══════════════════════════════════════════════════════════

def build_comparison(all_results: dict) -> dict:
    """Build a comparison table across sources."""
    table = {}
    for source_key, results in all_results.items():
        if not results:
            table[source_key] = {
                "avg_detections": 0, "avg_confidence": 0,
                "avg_box_w": 0, "avg_box_h": 0,
                "avg_image_w": 0, "avg_image_h": 0,
                "sample_count": 0,
            }
            continue

        dets = [r["nms_detections"] for r in results]
        confs = [r["nms_stats"]["avg_conf"] for r in results if r["nms_detections"] > 0]
        bws = [r["nms_stats"]["avg_box_w"] for r in results if r["nms_detections"] > 0]
        bhs = [r["nms_stats"]["avg_box_h"] for r in results if r["nms_detections"] > 0]
        iws = [r["image_size"]["w"] for r in results]
        ihs = [r["image_size"]["h"] for r in results]

        table[source_key] = {
            "sample_count": len(results),
            "avg_detections": round(float(np.mean(dets)), 1) if dets else 0,
            "avg_confidence": round(float(np.mean(confs)), 4) if confs else 0,
            "avg_box_w": round(float(np.mean(bws)), 1) if bws else 0,
            "avg_box_h": round(float(np.mean(bhs)), 1) if bhs else 0,
            "avg_image_w": round(float(np.mean(iws)), 0) if iws else 0,
            "avg_image_h": round(float(np.mean(ihs)), 0) if ihs else 0,
        }
    return table


def print_comparison_table(table: dict):
    """Pretty-print the comparison table."""
    print("\n" + "=" * 100)
    print("  STEP 4 — CROSS-SOURCE COMPARISON")
    print("=" * 100)
    header = (f"{'Source':<22} | {'Samples':>7} | {'Avg Dets':>9} | {'Avg Conf':>9} | "
              f"{'Avg Box (WxH)':>14} | {'Avg Img (WxH)':>16}")
    print(header)
    print("-" * 100)
    for src, data in table.items():
        box_str = f"{data['avg_box_w']:.0f}x{data['avg_box_h']:.0f}"
        img_str = f"{data['avg_image_w']:.0f}x{data['avg_image_h']:.0f}"
        print(f"{src:<22} | {data['sample_count']:>7} | {data['avg_detections']:>9.1f} | "
              f"{data['avg_confidence']:>9.4f} | {box_str:>14} | {img_str:>16}")
    print("=" * 100)


# ══════════════════════════════════════════════════════════
#  STEP 5 — DIAGNOSIS & RECOMMENDATIONS
# ══════════════════════════════════════════════════════════

def diagnose(table: dict, all_results: dict, scan_stats: dict) -> dict:
    """Analyze YOLO behavior and produce actionable diagnosis."""
    findings = []
    recommendations = []

    # ── A) False object detection (boxes on empty space) ──
    low_conf_total = 0
    total_dets = 0
    for results in all_results.values():
        for r in results:
            if r["nms_detections"] > 0:
                low_conf_total += r["nms_stats"]["conf_buckets"]["low_lt_0.1"]
                total_dets += r["nms_detections"]

    if total_dets > 0:
        low_pct = low_conf_total / total_dets * 100
        finding_a = {
            "question": "A) Is YOLO detecting too many false objects (boxes on empty space)?",
            "low_confidence_detections": low_conf_total,
            "total_detections": total_dets,
            "low_confidence_percentage": round(low_pct, 1),
        }
        if low_pct > 30:
            finding_a["verdict"] = "YES — CRITICAL"
            finding_a["detail"] = (
                f"{low_pct:.1f}% of all detections have confidence < 0.1. "
                "The YOLO model is hallucinating objects — most of these are likely "
                "noise, background texture, or staining artifacts being mistaken for cells."
            )
            recommendations.append(
                "RAISE yolo_conf threshold from 0.05 to at least 0.15-0.25 to filter noise."
            )
        elif low_pct > 15:
            finding_a["verdict"] = "MODERATE CONCERN"
            finding_a["detail"] = (
                f"{low_pct:.1f}% of detections have conf < 0.1. Some noise is leaking through."
            )
            recommendations.append(
                "Consider raising yolo_conf from 0.05 to 0.10 to reduce noise."
            )
        else:
            finding_a["verdict"] = "LOW RISK"
            finding_a["detail"] = f"Only {low_pct:.1f}% of detections are very low confidence."
    else:
        finding_a = {
            "question": "A) Is YOLO detecting too many false objects?",
            "verdict": "CANNOT ASSESS",
            "detail": "No detections produced at all.",
        }
    findings.append(finding_a)

    # ── B) Missing real cells ──
    finding_b = {
        "question": "B) Is YOLO missing real cells?",
    }
    # Compare detection density across sources
    for src_key in ["erythrocytesIDB", "kaggle_positive"]:
        data = table.get(src_key, {})
        if data.get("avg_detections", 0) < 10 and data.get("sample_count", 0) > 0:
            finding_b["verdict"] = "YES — LIKELY MISSING CELLS"
            finding_b["detail"] = (
                f"Source '{src_key}' yields only ~{data['avg_detections']:.0f} detections "
                f"on images averaging {data['avg_image_w']:.0f}x{data['avg_image_h']:.0f}px. "
                "A typical blood smear of this size should have 50-300+ red blood cells visible. "
                "The YOLO model is not generalizing to this image domain."
            )
            recommendations.append(
                f"Retrain or fine-tune YOLO on images from {src_key} source. "
                "The current model was likely trained on a different magnification/staining protocol."
            )
            break
    if "verdict" not in finding_b:
        finding_b["verdict"] = "ASSESSMENT BELOW"
        finding_b["detail"] = "Detection counts need to be compared against manual cell counts."
    findings.append(finding_b)

    # ── C) Bounding box size appropriateness ──
    finding_c = {
        "question": "C) Is the bounding box size appropriate for cell crops?",
    }
    box_issues = []
    for src_key, data in table.items():
        if data.get("avg_box_w", 0) > 0:
            avg_area = data["avg_box_w"] * data["avg_box_h"]
            if avg_area < 200:
                box_issues.append(
                    f"{src_key}: avg box {data['avg_box_w']:.0f}x{data['avg_box_h']:.0f} "
                    f"is TINY — too small for meaningful CNN classification (128x128 input)."
                )
            elif avg_area > 40000:
                box_issues.append(
                    f"{src_key}: avg box {data['avg_box_w']:.0f}x{data['avg_box_h']:.0f} "
                    f"is HUGE — likely spanning multiple cells or entire tile regions."
                )

    if box_issues:
        finding_c["verdict"] = "ISSUES DETECTED"
        finding_c["detail"] = " | ".join(box_issues)
        recommendations.append(
            "Review bounding box sizes per source — consider source-specific preprocessing "
            "or rejection of boxes outside expected RBC size range (20-100px per cell)."
        )
    else:
        finding_c["verdict"] = "ACCEPTABLE"
        finding_c["detail"] = "Bounding box sizes are within reasonable range for cell crops."
    findings.append(finding_c)

    # ── D) Confidence threshold analysis ──
    finding_d = {
        "question": "D) Is the confidence threshold (0.05) too low — letting noise through?",
    }
    # Collect ALL conf buckets across all results
    total_high, total_med, total_low = 0, 0, 0
    for results in all_results.values():
        for r in results:
            if r["nms_detections"] > 0:
                total_high += r["nms_stats"]["conf_buckets"]["high_gt_0.3"]
                total_med += r["nms_stats"]["conf_buckets"]["medium_0.1_0.3"]
                total_low += r["nms_stats"]["conf_buckets"]["low_lt_0.1"]

    grand_total = total_high + total_med + total_low
    if grand_total > 0:
        finding_d["confidence_distribution"] = {
            "high_gt_0.3": total_high,
            "high_pct": round(total_high / grand_total * 100, 1),
            "medium_0.1_0.3": total_med,
            "medium_pct": round(total_med / grand_total * 100, 1),
            "low_lt_0.1": total_low,
            "low_pct": round(total_low / grand_total * 100, 1),
        }
        if total_low / grand_total > 0.3:
            finding_d["verdict"] = "YES — THRESHOLD TOO LOW"
            finding_d["detail"] = (
                f"{total_low / grand_total * 100:.1f}% of detections are < 0.1 confidence. "
                "The threshold of 0.05 is letting massive amounts of noise through. "
                "This wastes compute on CNN classification of garbage crops and produces "
                "false positives in the final report."
            )
            recommendations.append(
                "CRITICAL: Raise YOLO confidence threshold from 0.05 to >= 0.15. "
                "Validate on the original test set to ensure recall is maintained."
            )
        elif total_low / grand_total > 0.15:
            finding_d["verdict"] = "BORDERLINE"
            finding_d["detail"] = (
                f"{total_low / grand_total * 100:.1f}% of detections are < 0.1. "
                "Consider raising threshold to 0.10."
            )
        else:
            finding_d["verdict"] = "ACCEPTABLE"
            finding_d["detail"] = "Most detections are reasonably confident."
    else:
        finding_d["verdict"] = "CANNOT ASSESS"
        finding_d["detail"] = "No detections produced."
    findings.append(finding_d)

    # ── E) Tile size appropriateness ──
    finding_e = {
        "question": "E) Are the tile sizes (640x640) appropriate for these image sizes?",
    }
    tile_issues = []
    for src_key, stats_data in scan_stats.items():
        if stats_data.get("dimensions"):
            dims = stats_data["dimensions"]
            avg_w, avg_h = dims["avg_w"], dims["avg_h"]
            # If image is smaller than tile, tiling adds no value
            if avg_w <= TILE_SIZE and avg_h <= TILE_SIZE:
                tile_issues.append(
                    f"{src_key}: avg image {avg_w:.0f}x{avg_h:.0f} fits in a single 640x640 tile. "
                    "Tiling is unnecessary and overlap may cause duplicate detections."
                )
            # If image is very large, many tiles needed
            tiles_x = max(1, int(np.ceil((avg_w - TILE_SIZE) / (TILE_SIZE * (1 - OVERLAP_RATIO)))) + 1)
            tiles_y = max(1, int(np.ceil((avg_h - TILE_SIZE) / (TILE_SIZE * (1 - OVERLAP_RATIO)))) + 1)
            total_tiles = tiles_x * tiles_y
            if total_tiles > 50:
                tile_issues.append(
                    f"{src_key}: avg image {avg_w:.0f}x{avg_h:.0f} requires ~{total_tiles} tiles. "
                    "Very high tile count — consider larger tiles (1280) for high-res images."
                )

    if tile_issues:
        finding_e["verdict"] = "ISSUES DETECTED"
        finding_e["detail"] = " | ".join(tile_issues)
        recommendations.append(
            "Consider adaptive tile sizing based on image resolution."
        )
    else:
        finding_e["verdict"] = "ACCEPTABLE"
        finding_e["detail"] = "640x640 tiling is reasonable for the observed image sizes."
    findings.append(finding_e)

    return {
        "findings": findings,
        "recommendations": recommendations,
    }


def print_diagnosis(diagnosis: dict):
    """Pretty-print the diagnosis."""
    print("\n" + "=" * 100)
    print("  STEP 5 — DIAGNOSIS & RECOMMENDATIONS")
    print("=" * 100)

    for f in diagnosis["findings"]:
        print(f"\n  {f['question']}")
        print(f"  → Verdict: {f.get('verdict', 'N/A')}")
        if f.get("detail"):
            # Word-wrap long details
            detail = f["detail"]
            while len(detail) > 90:
                cut = detail[:90].rfind(" ")
                if cut < 50:
                    cut = 90
                print(f"    {detail[:cut]}")
                detail = detail[cut:].lstrip()
            if detail:
                print(f"    {detail}")
        if f.get("confidence_distribution"):
            cd = f["confidence_distribution"]
            print(f"    High (>0.3): {cd['high_gt_0.3']} ({cd['high_pct']}%)")
            print(f"    Medium (0.1-0.3): {cd['medium_0.1_0.3']} ({cd['medium_pct']}%)")
            print(f"    Low (<0.1): {cd['low_lt_0.1']} ({cd['low_pct']}%)")

    print(f"\n{'─' * 100}")
    print("  RECOMMENDATIONS:")
    for i, rec in enumerate(diagnosis["recommendations"], 1):
        print(f"  {i}. {rec}")

    print("=" * 100)


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    print("=" * 100)
    print("  LabMind AI — Full Pipeline YOLO Detection Diagnostic")
    print(f"  Parameters: conf={YOLO_CONF}, tile={TILE_SIZE}x{TILE_SIZE}, "
          f"overlap={OVERLAP_RATIO}, nms_iou={NMS_IOU}")
    print("=" * 100)

    # ── Load YOLO model ──
    if not YOLO_MODEL_PATH.exists():
        print(f"FATAL: YOLO model not found at {YOLO_MODEL_PATH}")
        sys.exit(1)

    print(f"\nLoading YOLO model from {YOLO_MODEL_PATH} ...")
    from ultralytics import YOLO
    yolo_model = YOLO(str(YOLO_MODEL_PATH))
    print("  ✓ YOLO model loaded.\n")

    # ════════════════════════════════════════════════════════
    #  STEP 1 — SCAN AVAILABLE IMAGES
    # ════════════════════════════════════════════════════════
    print("=" * 100)
    print("  STEP 1 — SCAN AVAILABLE IMAGES")
    print("=" * 100)

    all_images = {}
    scan_stats = {}

    for source_key, source_info in SOURCE_DIRS.items():
        images = collect_images(source_info["paths"])
        all_images[source_key] = images

        print(f"\n  Source: {source_info['label']}")
        for p in source_info["paths"]:
            print(f"    Path: {p}  {'✓ exists' if p.exists() else '✗ NOT FOUND'}")
        print(f"    Total images: {len(images)}")

        if images:
            stats = scan_source(source_key, images)
            scan_stats[source_key] = stats
            if stats.get("dimensions"):
                d = stats["dimensions"]
                print(f"    Dimensions: avg {d['avg_w']:.0f}x{d['avg_h']:.0f}, "
                      f"min {d['min_w']}x{d['min_h']}, max {d['max_w']}x{d['max_h']}")
                print(f"    Megapixels (avg): {d['avg_megapixels']}")
            if stats.get("color_profile"):
                c = stats["color_profile"]
                print(f"    Color profile (mean RGB): R={c['mean_R']:.1f}, "
                      f"G={c['mean_G']:.1f}, B={c['mean_B']:.1f}")
        else:
            scan_stats[source_key] = {"source": source_key, "count": 0,
                                       "note": "No images found / directory missing"}
            print("    ⚠  No images found.")

    # ════════════════════════════════════════════════════════
    #  STEP 2 — YOLO DIAGNOSTIC ON ErythrocytesIDB
    # ════════════════════════════════════════════════════════
    print("\n" + "=" * 100)
    print("  STEP 2 — YOLO DETECTION DIAGNOSTIC ON ErythrocytesIDB (5 images)")
    print("=" * 100)

    all_diagnostic_results = {}
    erythro_results = run_diagnostic_on_sample(
        yolo_model, all_images.get("erythrocytesIDB", []),
        n=5, source_key="erythrocytesIDB",
        source_label="ErythrocytesIDB (Cuba)"
    )
    all_diagnostic_results["erythrocytesIDB"] = erythro_results

    # ════════════════════════════════════════════════════════
    #  STEP 3 — YOLO DIAGNOSTIC ON Kaggle SCD
    # ════════════════════════════════════════════════════════
    print("\n" + "=" * 100)
    print("  STEP 3 — YOLO DETECTION DIAGNOSTIC ON Kaggle SCD")
    print("=" * 100)

    # Kaggle Positive
    print("\n  ── Kaggle Positive (3 images) ──")
    kaggle_pos_results = run_diagnostic_on_sample(
        yolo_model, all_images.get("kaggle_positive", []),
        n=3, source_key="kaggle_positive",
        source_label="Kaggle SCD Positive (Uganda)"
    )
    all_diagnostic_results["kaggle_positive"] = kaggle_pos_results

    # Kaggle Negative
    print("\n  ── Kaggle Negative (2 images) ──")
    kaggle_neg_results = run_diagnostic_on_sample(
        yolo_model, all_images.get("kaggle_negative", []),
        n=2, source_key="kaggle_negative",
        source_label="Kaggle SCD Negative (Uganda)"
    )
    all_diagnostic_results["kaggle_negative"] = kaggle_neg_results

    # Also run on validation_smears for comparison baseline
    print("\n  ── Validation Smears (baseline, all images) ──")
    val_results = run_diagnostic_on_sample(
        yolo_model, all_images.get("validation_smears", []),
        n=min(10, len(all_images.get("validation_smears", []))),
        source_key="validation_smears",
        source_label="Validation Smears (original test set)"
    )
    all_diagnostic_results["validation_smears"] = val_results

    # ════════════════════════════════════════════════════════
    #  STEP 4 — COMPARISON TABLE
    # ════════════════════════════════════════════════════════
    comparison = build_comparison(all_diagnostic_results)
    print_comparison_table(comparison)

    # ════════════════════════════════════════════════════════
    #  STEP 5 — DIAGNOSIS
    # ════════════════════════════════════════════════════════
    diagnosis = diagnose(comparison, all_diagnostic_results, scan_stats)
    print_diagnosis(diagnosis)

    # ════════════════════════════════════════════════════════
    #  SAVE FULL REPORT
    # ════════════════════════════════════════════════════════
    report = {
        "metadata": {
            "script": "diagnose_full_pipeline.py",
            "parameters": {
                "yolo_conf": YOLO_CONF,
                "tile_size": TILE_SIZE,
                "overlap_ratio": OVERLAP_RATIO,
                "nms_iou": NMS_IOU,
                "border_skip": BORDER_SKIP,
            },
            "yolo_model": str(YOLO_MODEL_PATH),
        },
        "step1_scan": scan_stats,
        "step2_erythrocytesIDB": erythro_results,
        "step3_kaggle_positive": kaggle_pos_results,
        "step3_kaggle_negative": kaggle_neg_results,
        "step3_validation_baseline": val_results,
        "step4_comparison": comparison,
        "step5_diagnosis": diagnosis,
    }

    report_path = SCRIPT_DIR / "diagnose_full_pipeline_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  ✓ Full report saved to: {report_path}")

    # Also copy report to reports/ for consistency
    report_copy_path = REPORTS_DIR / "diagnose_full_pipeline_report.json"
    with open(report_copy_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  ✓ Report copy in: {report_copy_path}")

    print(f"\n  ✓ Diagnostic images saved to: {REPORTS_DIR}/")
    print(f"  ✓ Total diagnostic images: "
          f"{sum(len(r) for r in all_diagnostic_results.values())}")
    print("\n" + "=" * 100)
    print("  DIAGNOSTIC COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
