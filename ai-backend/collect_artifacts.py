"""
LabMind — Artifact Crop Collector (supplement to build_validation_set.py)
Generates 40 artifact-class crops from available sources.

Artifact sources:
  1. YOLO crops from debug_crops/ that are very small, blurry, or extreme AR
  2. cropped_cells/rbc/ — find edge-case crops (clumps, blurry, partial)
  3. Synthetic: crop random regions from validation_smears (non-cell regions)

NO code changes. Copy-only.
"""
import json
import os
import random
import shutil
import cv2
import numpy as np

random.seed(42)

ARTIFACT_DIR = os.path.join("validation_cells", "artifact")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

VALID_EXTS = ('.jpg', '.jpeg', '.png')
artifacts = []


def compute_metrics(path):
    img = cv2.imread(path)
    if img is None:
        return None
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    ar = max(w, h) / (min(w, h) + 1e-5)
    return {"h": h, "w": w, "blur": blur, "ar": ar}


print("=" * 60)
print("  Artifact Crop Collector")
print("=" * 60)

# ── Source 1: YOLO crops from debug_crops/ (raw, pre-refinement) ──
# These are noisier than CNN crops — good artifact source
yolo_crops = []
for f in os.listdir("debug_crops"):
    if "_1_yolo_crop" in f and f.lower().endswith(VALID_EXTS):
        path = os.path.join("debug_crops", f)
        m = compute_metrics(path)
        if m:
            yolo_crops.append({"path": path, "filename": f, "metrics": m})

# Sort by "artifact-ness": prioritize blurry, tiny, extreme AR
yolo_crops.sort(key=lambda x: x["metrics"]["blur"])  # lowest blur first (most blurry)
print(f"  YOLO crops (debug_crops): {len(yolo_crops)}")

# Take the blurriest / smallest YOLO crops
yc_count = 0
for entry in yolo_crops:
    if yc_count >= 15:
        break
    m = entry["metrics"]
    # Accept if blurry or very small or extreme AR
    if m["blur"] < 200 or m["w"] < 30 or m["h"] < 30 or m["ar"] > 2.5:
        artifacts.append({
            "path": entry["path"],
            "filename": entry["filename"],
            "source_smear": "debug_crops_yolo",
            "source_type": "debug_crops",
            "artifact_reason": f"yolo_raw blur={m['blur']:.0f} ar={m['ar']:.1f} {m['w']}x{m['h']}",
        })
        yc_count += 1

print(f"  Selected from YOLO crops: {yc_count}")

# ── Source 2: cropped_cells/rbc — find edge-case crops ──
rbc_crops = []
rbc_dir = os.path.join("cropped_cells", "rbc")
if os.path.isdir(rbc_dir):
    for f in os.listdir(rbc_dir):
        if f.lower().endswith(VALID_EXTS):
            path = os.path.join(rbc_dir, f)
            m = compute_metrics(path)
            if m:
                rbc_crops.append({"path": path, "filename": f, "metrics": m})

# Sort by artifact-ness: blurriest first
rbc_crops.sort(key=lambda x: x["metrics"]["blur"])
print(f"  RBC crops (cropped_cells): {len(rbc_crops)}")

rc_count = 0
for entry in rbc_crops:
    if rc_count >= 10:
        break
    m = entry["metrics"]
    if m["blur"] < 300 or m["ar"] > 2.0 or m["w"] < 25 or m["h"] < 25:
        artifacts.append({
            "path": entry["path"],
            "filename": entry["filename"],
            "source_smear": "cropped_cells_rbc",
            "source_type": "cropped_cells",
            "artifact_reason": f"rbc_edge_case blur={m['blur']:.0f} ar={m['ar']:.1f} {m['w']}x{m['h']}",
        })
        rc_count += 1

print(f"  Selected from RBC crops: {rc_count}")

# ── Source 3: Random crops from validation smears (non-cell background) ──
smear_dirs = [
    ("validation_smears/normal", "normal"),
    ("validation_smears/sickle", "sickle"),
]
bg_count = 0
for sdir, stype in smear_dirs:
    if not os.path.isdir(sdir):
        continue
    for f in sorted(os.listdir(sdir)):
        if not f.lower().endswith(VALID_EXTS):
            continue
        if bg_count >= 15:
            break
        path = os.path.join(sdir, f)
        img = cv2.imread(path)
        if img is None:
            continue
        h_img, w_img = img.shape[:2]

        # Extract random small patches from background-heavy regions
        # Take patches from corners/edges (more likely background)
        for attempt in range(5):
            if bg_count >= 15:
                break
            cx = random.randint(0, max(0, w_img - 50))
            cy = random.randint(0, max(0, h_img - 50))
            patch_w = random.randint(20, 60)
            patch_h = random.randint(20, 60)
            patch = img[cy:min(cy+patch_h, h_img), cx:min(cx+patch_w, w_img)]
            if patch.size == 0:
                continue

            # Check if patch is mostly uniform (background) or very busy (clump)
            gray_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
            std = float(np.std(gray_patch))
            blur = cv2.Laplacian(gray_patch, cv2.CV_64F).var()

            # Accept if it looks like background (low std) or busy noise (very high std)
            if std < 20 or std > 80 or blur < 100:
                patch_name = f"bg_{stype}_{f.split('.')[0]}_{attempt}.jpg"
                patch_path = os.path.join(ARTIFACT_DIR, f"artifact_{len(artifacts):04d}.jpg")
                cv2.imwrite(patch_path, patch)

                artifacts.append({
                    "path": patch_path,
                    "filename": f"artifact_{len(artifacts):04d}.jpg",
                    "source_smear": f"{stype}_{f}",
                    "source_type": "validation_smears_patch",
                    "artifact_reason": f"background_patch std={std:.0f} blur={blur:.0f} {patch.shape[1]}x{patch.shape[0]}",
                    "already_copied": True,
                })
                bg_count += 1

print(f"  Selected background patches: {bg_count}")

# ── Copy all artifacts ──
labels = []
idx = 0
for entry in artifacts:
    if idx >= 40:
        break

    if entry.get("already_copied"):
        # Already saved to artifact dir (background patches)
        fname = f"artifact_{idx:04d}.jpg"
        old_path = entry["path"]
        new_path = os.path.join(ARTIFACT_DIR, fname)
        if old_path != new_path:
            if os.path.exists(old_path):
                shutil.move(old_path, new_path)
    else:
        fname = f"artifact_{idx:04d}.jpg"
        dst = os.path.join(ARTIFACT_DIR, fname)
        shutil.copy2(entry["path"], dst)

    labels.append({
        "filename": fname,
        "class": "artifact",
        "source_smear": entry.get("source_smear", "unknown"),
        "source_type": entry.get("source_type", "unknown"),
        "original_filename": entry.get("filename", ""),
        "notes": entry.get("artifact_reason", ""),
    })
    idx += 1

print(f"\n  Total artifacts copied: {idx}")

# ── Update labels.json ──
labels_path = os.path.join("validation_cells", "labels.json")
if os.path.exists(labels_path):
    with open(labels_path, "r") as f:
        existing = json.load(f)
else:
    existing = {"labels": [], "counts": {}}

# Remove any old artifact entries
existing["labels"] = [l for l in existing["labels"] if l.get("class") != "artifact"]
existing["labels"].extend(labels)
existing["counts"]["artifact"] = idx
existing["total_crops"] = sum(existing["counts"].values())

# Update source distribution
source_dist = {}
smear_dist = {}
for l in existing["labels"]:
    st = l.get("source_type", "unknown")
    source_dist[st] = source_dist.get(st, 0) + 1
    sm = l.get("source_smear", "unknown")
    smear_dist[sm] = smear_dist.get(sm, 0) + 1
existing["source_distribution"] = source_dist
existing["smear_distribution"] = smear_dist

with open(labels_path, "w", encoding="utf-8") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

print(f"\n  Updated labels.json: {labels_path}")
print(f"  Total crops now: {existing['total_crops']}")
print(f"  Counts: {existing['counts']}")
print("=" * 60)
