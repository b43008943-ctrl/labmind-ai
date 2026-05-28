"""
LabMind AI — Detection Recall Audit
Measures cell count at each pipeline stage to identify where cells are being lost.
Also validates single-cell crop quality for each sickle detection.
"""
import json
import os
import sys
import cv2
import numpy as np
import torch
import torchvision

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.providers.ai_provider_v1 import V1Provider, YOLO_CLASS_MAP

def recall_audit(image_path: str, label: str):
    """Count cells at each pipeline stage."""
    provider = V1Provider()
    img = cv2.imread(image_path)
    if img is None:
        print(f"  ERROR: Cannot read {image_path}")
        return
    h_img, w_img = img.shape[:2]

    # Quality check
    quality = provider.quality_check(img)
    if quality["quality_status"] == "rejected":
        print(f"  REJECTED: {quality['rejection_reason']}")
        return

    # Stage 2: YOLO tiling — raw detections
    tile_size = 640
    overlap = int(tile_size * 0.25)
    step = tile_size - overlap
    global_boxes, global_scores, global_classes = [], [], []
    raw_yolo_count = 0
    edge_rejected = 0

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
                    raw_yolo_count += 1
                    tx1, ty1, tx2, ty2 = map(int, box)
                    if tx1 <= 5 or ty1 <= 5 or tx2 >= tile.shape[1] - 5 or ty2 >= tile.shape[0] - 5:
                        edge_rejected += 1
                        continue
                    global_boxes.append([x + tx1, y + ty1, x + tx2, y + ty2])
                    global_scores.append(float(scores[i]))
                    global_classes.append(int(classes[i]))

    after_edge = len(global_boxes)

    # Stage 3: NMS
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

    after_nms = len(valid_boxes)
    nms_removed = after_edge - after_nms

    # Stage 4: Watershed decluster
    rbc_areas, rbc_widths, rbc_heights = [], [], []
    for i, box in enumerate(valid_boxes):
        cn = YOLO_CLASS_MAP.get(valid_classes[i], "unknown")
        if cn in ("rbc", "sickle"):
            w, h = box[2] - box[0], box[3] - box[1]
            rbc_areas.append(w * h)
            rbc_widths.append(w)
            rbc_heights.append(h)
    median_area = float(np.median(rbc_areas)) if rbc_areas else 0
    median_w = float(np.median(rbc_widths)) if rbc_widths else 0
    median_h = float(np.median(rbc_heights)) if rbc_heights else 0

    dec_boxes, dec_classes, dec_scores = [], [], []
    watershed_split = 0
    for i, box in enumerate(valid_boxes):
        cn = YOLO_CLASS_MAP.get(valid_classes[i], "unknown")
        if cn in ("rbc", "sickle") and median_w > 0 and median_h > 0:
            x1, y1, x2, y2 = map(int, box)
            bw, bh = x2 - x1, y2 - y1
            if bw > 1.5 * median_w or bh > 1.5 * median_h:
                subcells = provider._watershed_decluster(img, box, median_area, w_img, h_img)
                watershed_split += 1
                for sc in subcells:
                    dec_boxes.append(sc)
                    dec_classes.append(valid_classes[i])
                    dec_scores.append(valid_scores[i])
                continue
        dec_boxes.append(box)
        dec_classes.append(valid_classes[i])
        dec_scores.append(valid_scores[i])

    after_decluster = len(dec_boxes)

    # Stage 5+6: Classification (count None returns)
    classify_none = 0
    classify_ok = 0
    classify_exc = 0
    sickle_results = []
    detected_cells = []
    for i, box in enumerate(dec_boxes):
        class_id = dec_classes[i]
        class_name = YOLO_CLASS_MAP.get(class_id, "unknown")
        confidence = dec_scores[i]
        if class_name in ("rbc", "sickle"):
            try:
                cell_data = provider._classify_rbc(img, box, class_id, confidence, median_area, w_img, h_img)
                if cell_data:
                    classify_ok += 1
                    detected_cells.append(cell_data)
                    if cell_data["class_name"] == "sickle":
                        sickle_results.append(cell_data)
                else:
                    classify_none += 1
            except Exception as e:
                classify_exc += 1
        else:
            classify_ok += 1
            detected_cells.append({"class_name": class_name, "x1": box[0], "y1": box[1], "x2": box[2], "y2": box[3]})

    # Stage 7: Deduplication
    final_cells = []
    dedup_removed = 0
    for cell in detected_cells:
        cx = (cell["x1"] + cell["x2"]) / 2
        cy = (cell["y1"] + cell["y2"]) / 2
        dup = False
        for fc in final_cells:
            if fc["class_name"] != cell["class_name"]:
                continue
            fcx = (fc["x1"] + fc["x2"]) / 2
            fcy = (fc["y1"] + fc["y2"]) / 2
            if np.sqrt((cx - fcx) ** 2 + (cy - fcy) ** 2) < 15:
                dup = True
                dedup_removed += 1
                break
        if not dup:
            final_cells.append(cell)

    # Count finals
    final_sickle = sum(1 for c in final_cells if c.get("class_name") == "sickle")
    final_rbc = sum(1 for c in final_cells if c.get("class_name") == "rbc")

    print(f"\n  ═══ RECALL AUDIT: {label} ═══")
    print(f"  Stage 2 (YOLO raw):        {raw_yolo_count}")
    print(f"    edge-rejected:           -{edge_rejected}")
    print(f"    after edge filter:       {after_edge}")
    print(f"  Stage 3 (NMS):             {after_nms}  (-{nms_removed} dups)")
    print(f"  Stage 4 (Watershed):       {after_decluster}  ({watershed_split} boxes split)")
    print(f"  Stage 5+6 (Classify):")
    print(f"    returned cell:           {classify_ok}")
    print(f"    returned None:           -{classify_none}")
    print(f"    exceptions:              -{classify_exc}")
    print(f"  Stage 7 (Dedup):           {len(final_cells)}  (-{dedup_removed} dups)")
    print(f"  ── Final counts ──")
    print(f"    rbc:    {final_rbc}")
    print(f"    sickle: {final_sickle}")
    print(f"    total:  {len(final_cells)}")
    print(f"    median_area: {median_area:.0f}")

    # Sickle cell edge analysis for false-positive investigation
    if sickle_results:
        print(f"\n  ── Sickle detection details ──")
        for idx, s in enumerate(sickle_results):
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            w, h = x2 - x1, y2 - y1
            border = (x1 <= 3 or y1 <= 3 or x2 >= w_img - 3 or y2 >= h_img - 3)
            print(f"    [{idx}] box=[{x1},{y1},{x2},{y2}] ({w}x{h}) conf={s.get('confidence',0):.3f} "
                  f"cnn={s.get('cnn_probability',0):.3f} AR={s.get('aspect_ratio',0):.2f} "
                  f"circ={s.get('circularity',0):.2f} sol={s.get('solidity',0):.2f} "
                  f"{'BORDER!' if border else ''}")

    return {
        "raw_yolo": raw_yolo_count, "edge_rejected": edge_rejected,
        "after_nms": after_nms, "after_decluster": after_decluster,
        "classify_ok": classify_ok, "classify_none": classify_none,
        "final": len(final_cells), "dedup_removed": dedup_removed,
        "sickle": final_sickle, "rbc": final_rbc,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("LabMind AI — Detection Recall Audit")
    print("=" * 60)

    tests = []
    # Normal smears
    ndir = os.path.join("validation_smears", "normal")
    if os.path.isdir(ndir):
        for f in sorted(os.listdir(ndir))[:2]:
            tests.append((os.path.join(ndir, f), f"NORMAL_{f}"))
    # Sickle smears
    sdir = os.path.join("validation_smears", "sickle")
    if os.path.isdir(sdir):
        for f in sorted(os.listdir(sdir))[:2]:
            tests.append((os.path.join(sdir, f), f"SICKLE_{f}"))
    # Main test image
    main = os.path.join("test_images", "Sickle_Cell_Blood_Smear.jpg")
    if os.path.isfile(main):
        tests.append((main, "SICKLE_MAIN"))

    for path, lbl in tests:
        recall_audit(path, lbl)
