"""
LabMind AI — Cell-Level Crop Debug Audit
Saves debug artifacts for every sickle prediction + sample normal predictions.
Outputs: crop images, metadata JSON, and a visual composite per detection.
"""
import json
import os
import sys
import cv2
import numpy as np

# Ensure we can import the app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.providers.ai_provider_v1 import V1Provider, YOLO_CLASS_MAP

DEBUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_crops")
os.makedirs(DEBUG_DIR, exist_ok=True)


def run_audit(image_path: str, label: str):
    """Run the pipeline on one image and save debug crops for sickle detections."""
    provider = V1Provider()
    img = cv2.imread(image_path)
    if img is None:
        print(f"  ERROR: Cannot read {image_path}")
        return

    h_img, w_img = img.shape[:2]
    print(f"  Image: {image_path} ({w_img}x{h_img})")

    # Run quality check
    quality = provider.quality_check(img)
    if quality["quality_status"] == "rejected":
        print(f"  REJECTED: {quality['rejection_reason']}")
        return

    # ── Run YOLO tiling (replicate analyze() stages 2-4) ──
    tile_size = 640
    overlap = int(tile_size * 0.25)
    step = tile_size - overlap
    global_boxes, global_scores, global_classes = [], [], []

    for y in range(0, h_img, step):
        for x in range(0, w_img, step):
            y_end = min(y + tile_size, h_img)
            x_end = min(x + tile_size, w_img)
            tile = img[y:y_end, x:x_end]
            if tile.shape[0] < 100 or tile.shape[1] < 100:
                continue
            results = provider._yolo_model(tile, conf=0.05, imgsz=tile_size, verbose=False)
            for result in results:
                boxes = result.boxes.xyxy.cpu().numpy()
                scores = result.boxes.conf.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy()
                for i, box in enumerate(boxes):
                    tx1, ty1, tx2, ty2 = map(int, box)
                    if tx1 <= 5 or ty1 <= 5 or tx2 >= tile.shape[1] - 5 or ty2 >= tile.shape[0] - 5:
                        continue
                    global_boxes.append([x + tx1, y + ty1, x + tx2, y + ty2])
                    global_scores.append(float(scores[i]))
                    global_classes.append(int(classes[i]))

    import torch, torchvision
    valid_boxes, valid_classes, valid_scores = [], [], []
    if global_boxes:
        gb = torch.tensor(global_boxes, dtype=torch.float32)
        gs = torch.tensor(global_scores, dtype=torch.float32)
        gc = torch.tensor(global_classes, dtype=torch.int64)
        keep = torchvision.ops.batched_nms(gb, gs, gc, 0.35)
        for idx in keep:
            i = idx.item()
            valid_boxes.append(global_boxes[i])
            valid_classes.append(global_classes[i])
            valid_scores.append(global_scores[i])

    print(f"  YOLO detections after NMS: {len(valid_boxes)}")

    # Compute median for RBC
    rbc_areas = []
    for i, box in enumerate(valid_boxes):
        cn = YOLO_CLASS_MAP.get(valid_classes[i], "unknown")
        if cn in ("rbc", "sickle"):
            w, h = box[2] - box[0], box[3] - box[1]
            rbc_areas.append(w * h)
    median_area = float(np.median(rbc_areas)) if rbc_areas else 0

    # ── For each RBC/sickle detection, do debug crop analysis ──
    audit_results = []
    sickle_idx = 0
    normal_saved = 0

    for i, box in enumerate(valid_boxes):
        class_name = YOLO_CLASS_MAP.get(valid_classes[i], "unknown")
        if class_name not in ("rbc", "sickle"):
            continue

        cell_data = provider._classify_rbc(img, box, valid_classes[i], valid_scores[i], median_area, w_img, h_img)
        if cell_data is None:
            continue

        is_sickle_pred = cell_data["class_name"] == "sickle"

        # Save debug crops for: ALL sickle predictions + first 5 normal predictions
        if is_sickle_pred or (not is_sickle_pred and normal_saved < 5):
            prefix = f"{label}_sickle_{sickle_idx}" if is_sickle_pred else f"{label}_normal_{normal_saved}"

            # 1. Save the YOLO original box region
            ox1, oy1, ox2, oy2 = map(int, box)
            yolo_crop = img[max(0,oy1):min(h_img,oy2), max(0,ox1):min(w_img,ox2)]
            cv2.imwrite(os.path.join(DEBUG_DIR, f"{prefix}_1_yolo_crop.jpg"), yolo_crop)

            # 2. Save the contour-refined crop (what CNN actually sees)
            cx1, cy1, cx2, cy2 = cell_data["x1"], cell_data["y1"], cell_data["x2"], cell_data["y2"]
            cnn_crop = img[max(0,cy1):min(h_img,cy2), max(0,cx1):min(w_img,cx2)]
            cv2.imwrite(os.path.join(DEBUG_DIR, f"{prefix}_2_cnn_crop.jpg"), cnn_crop)

            # 3. Save the padded ROI with contour overlay
            pad = 15
            rx1, ry1 = max(0, ox1 - pad), max(0, oy1 - pad)
            rx2, ry2 = min(w_img, ox2 + pad), min(h_img, oy2 + pad)
            roi_debug = img[ry1:ry2, rx1:rx2].copy()
            # Draw original YOLO box (blue)
            cv2.rectangle(roi_debug, (ox1-rx1, oy1-ry1), (ox2-rx1, oy2-ry1), (255, 0, 0), 2)
            # Draw contour-refined box (green)
            cv2.rectangle(roi_debug, (cx1-rx1, cy1-ry1), (cx2-rx1, cy2-ry1), (0, 255, 0), 2)
            # Do Otsu to show contour
            gray_roi = cv2.cvtColor(img[ry1:ry2, rx1:rx2], cv2.COLOR_BGR2GRAY)
            _, thresh_roi = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours_roi, _ = cv2.findContours(thresh_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(roi_debug, contours_roi, -1, (0, 255, 255), 1)
            cv2.imwrite(os.path.join(DEBUG_DIR, f"{prefix}_3_roi_contours.jpg"), roi_debug)

            # 4. Save annotated full image region (wider context)
            context_pad = 60
            ctx1, cty1 = max(0, ox1 - context_pad), max(0, oy1 - context_pad)
            ctx2, cty2 = min(w_img, ox2 + context_pad), min(h_img, oy2 + context_pad)
            context = img[cty1:cty2, ctx1:ctx2].copy()
            cv2.rectangle(context, (ox1-ctx1, oy1-cty1), (ox2-ctx1, oy2-cty1), (255, 0, 0), 2)
            cv2.rectangle(context, (cx1-ctx1, cy1-cty1), (cx2-ctx1, cy2-cty1), (0, 0, 255) if is_sickle_pred else (0, 255, 0), 3)
            cv2.imwrite(os.path.join(DEBUG_DIR, f"{prefix}_4_context.jpg"), context)

            # 5. Metadata
            meta = {
                "label_type": label,
                "prediction": cell_data["label"],
                "confidence": cell_data["confidence"],
                "cnn_probability": cell_data["cnn_probability"],
                "cnn_class_probabilities": cell_data["cnn_class_probabilities"],
                "yolo_box": [ox1, oy1, ox2, oy2],
                "refined_box": [cx1, cy1, cx2, cy2],
                "yolo_confidence": round(valid_scores[i], 4),
                "circularity": cell_data["circularity"],
                "aspect_ratio": cell_data["aspect_ratio"],
                "solidity": cell_data["solidity"],
                "box_shift_x": abs((cx1+cx2)/2 - (ox1+ox2)/2),
                "box_shift_y": abs((cy1+cy2)/2 - (oy1+oy2)/2),
            }
            with open(os.path.join(DEBUG_DIR, f"{prefix}_meta.json"), "w") as f:
                json.dump(meta, f, indent=2)

            audit_results.append(meta)

            if is_sickle_pred:
                sickle_idx += 1
            else:
                normal_saved += 1

    print(f"  Sickle predictions: {sickle_idx}")
    print(f"  Normal samples saved: {normal_saved}")
    print(f"  Debug crops saved to: {DEBUG_DIR}")
    return audit_results


if __name__ == "__main__":
    print("=" * 60)
    print("LabMind AI — Cell-Level Crop Debug Audit")
    print("=" * 60)

    # Test with available images
    test_pairs = []

    # Sickle smears
    sickle_dir = os.path.join("validation_smears", "sickle")
    if os.path.isdir(sickle_dir):
        for f in sorted(os.listdir(sickle_dir))[:2]:
            test_pairs.append((os.path.join(sickle_dir, f), "sickle"))

    sickle_test = os.path.join("test_images", "Sickle_Cell_Blood_Smear.jpg")
    if os.path.isfile(sickle_test):
        test_pairs.append((sickle_test, "sickle_main"))

    # Normal smears
    normal_dir = os.path.join("validation_smears", "normal")
    if os.path.isdir(normal_dir):
        for f in sorted(os.listdir(normal_dir))[:2]:
            test_pairs.append((os.path.join(normal_dir, f), "normal"))

    all_results = {}
    for path, lbl in test_pairs:
        print(f"\n--- Auditing: {lbl} ({os.path.basename(path)}) ---")
        results = run_audit(path, f"{lbl}_{os.path.splitext(os.path.basename(path))[0]}")
        if results:
            all_results[f"{lbl}_{os.path.basename(path)}"] = results

    # Summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    for key, results in all_results.items():
        sickle_preds = [r for r in results if r["prediction"] == "Sickle"]
        normal_preds = [r for r in results if r["prediction"] == "Normal"]
        print(f"  {key}")
        print(f"    Sickle predictions: {len(sickle_preds)}")
        if sickle_preds:
            for sp in sickle_preds:
                shift = max(sp["box_shift_x"], sp["box_shift_y"])
                print(f"      conf={sp['confidence']:.3f}  shift={shift:.0f}px  AR={sp['aspect_ratio']:.2f}  circ={sp['circularity']:.2f}  sol={sp['solidity']:.2f}")
        print(f"    Normal samples: {len(normal_preds)}")
