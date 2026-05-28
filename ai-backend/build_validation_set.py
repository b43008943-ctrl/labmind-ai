"""
LabMind — Cell-Level Validation Set Builder (Step 2)
Curates 200 labeled crops from existing sources into validation_cells/.

NO code changes. NO threshold changes. Read-only curation + copy.

Sources:
  1. debug_crops/ — CNN crops (_2_cnn_crop.jpg) with pipeline labels from metadata
  2. dataset_v1_2class/val/ — pre-labeled normal/sickle
  3. cropped_cells/rbc/ — pipeline-cropped normal RBCs
  4. new_cropped_cells/ — mixed pool (for artifact candidates)

Priority: problematic smears (normal_04, sickle_05, weak sickle fields)
"""
import json
import os
import random
import shutil
import cv2
import numpy as np
from datetime import datetime, timezone

random.seed(42)

OUT_DIR = "validation_cells"
NORMAL_DIR = os.path.join(OUT_DIR, "normal")
SICKLE_DIR = os.path.join(OUT_DIR, "sickle")
ARTIFACT_DIR = os.path.join(OUT_DIR, "artifact")

TARGET_NORMAL = 80
TARGET_SICKLE = 80
TARGET_ARTIFACT = 40

VALID_EXTS = ('.jpg', '.jpeg', '.png')


def is_valid_image(path, min_px=10):
    """Check if file is a readable image with minimum dimensions."""
    img = cv2.imread(path)
    if img is None:
        return False
    h, w = img.shape[:2]
    return h >= min_px and w >= min_px


def compute_crop_quality(path):
    """Compute basic quality metrics for a crop."""
    img = cv2.imread(path)
    if img is None:
        return {}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    return {"height": h, "width": w, "blur_score": round(blur, 1)}


def collect_debug_crops():
    """Collect CNN crops from debug_crops/ with their pipeline labels."""
    debug_dir = "debug_crops"
    if not os.path.isdir(debug_dir):
        return [], []

    normal_crops = []
    sickle_crops = []

    # CNN crops are named: {smear}_{label}_{idx}_2_cnn_crop.jpg
    for f in os.listdir(debug_dir):
        if not f.endswith("_2_cnn_crop.jpg"):
            continue
        path = os.path.join(debug_dir, f)
        if not is_valid_image(path):
            continue

        # Parse source smear and pipeline label from filename
        # Format: {source}_{smear}_{label}_{idx}_2_cnn_crop.jpg
        # e.g., "sickle_sickle_01.jpg_sickle_5_2_cnn_crop.jpg"
        # e.g., "normal_normal_01.jpg_normal_0_2_cnn_crop.jpg"
        parts = f.replace("_2_cnn_crop.jpg", "")

        # Infer source smear
        if "normal_01" in f:
            source = "normal_01"
        elif "normal_02" in f:
            source = "normal_02"
        elif "sickle_01" in f:
            source = "sickle_01"
        elif "sickle_02" in f:
            source = "sickle_02"
        elif "Sickle_Cell_Blood_Smear" in f:
            source = "Sickle_Cell_Blood_Smear"
        else:
            source = "unknown"

        # Infer pipeline label from the label part before the index
        # The label is embedded in the filename pattern
        if "_sickle_" in parts.split(source)[-1] if source in parts else "":
            pipeline_label = "sickle"
        elif "_normal_" in parts.split(source)[-1] if source in parts else "":
            pipeline_label = "normal"
        else:
            # Safer parsing: check for _sickle_ or _normal_ after the smear name
            after_smear = f.split(".jpg_")[-1] if ".jpg_" in f else f
            if after_smear.startswith("sickle_"):
                pipeline_label = "sickle"
            elif after_smear.startswith("normal_"):
                pipeline_label = "normal"
            else:
                pipeline_label = "unknown"

        entry = {
            "path": path,
            "filename": f,
            "pipeline_label": pipeline_label,
            "source_smear": source,
            "source_type": "debug_crops",
        }

        if pipeline_label == "normal":
            normal_crops.append(entry)
        elif pipeline_label == "sickle":
            sickle_crops.append(entry)

    return normal_crops, sickle_crops


def collect_dataset_val():
    """Collect pre-labeled crops from dataset_v1_2class/val/."""
    normal_crops = []
    sickle_crops = []

    normal_dir = os.path.join("dataset_v1_2class", "val", "normal")
    sickle_dir = os.path.join("dataset_v1_2class", "val", "sickle")

    if os.path.isdir(normal_dir):
        for f in sorted(os.listdir(normal_dir)):
            if f.lower().endswith(VALID_EXTS):
                path = os.path.join(normal_dir, f)
                if is_valid_image(path):
                    normal_crops.append({
                        "path": path,
                        "filename": f,
                        "pipeline_label": "normal",
                        "source_smear": "dataset_v1_2class_val",
                        "source_type": "dataset_v1_2class",
                    })

    if os.path.isdir(sickle_dir):
        for f in sorted(os.listdir(sickle_dir)):
            if f.lower().endswith(VALID_EXTS):
                path = os.path.join(sickle_dir, f)
                if is_valid_image(path):
                    sickle_crops.append({
                        "path": path,
                        "filename": f,
                        "pipeline_label": "sickle",
                        "source_smear": "dataset_v1_2class_val",
                        "source_type": "dataset_v1_2class",
                    })

    return normal_crops, sickle_crops


def collect_cropped_rbc():
    """Collect normal RBC crops from cropped_cells/rbc/."""
    crops = []
    rbc_dir = os.path.join("cropped_cells", "rbc")
    if os.path.isdir(rbc_dir):
        for f in sorted(os.listdir(rbc_dir)):
            if f.lower().endswith(VALID_EXTS):
                path = os.path.join(rbc_dir, f)
                if is_valid_image(path):
                    crops.append({
                        "path": path,
                        "filename": f,
                        "pipeline_label": "normal",
                        "source_smear": "cropped_cells_rbc",
                        "source_type": "cropped_cells",
                    })
    return crops


def collect_artifact_candidates():
    """
    Collect artifact candidates: crops that are likely not valid single cells.
    Sources:
      - new_cropped_cells/ — mixed pool, pick small/blurry/odd ones
      - debug_crops/ — context/contour images (not cell crops)
    """
    candidates = []

    # From new_cropped_cells: pick a random sample, then filter for artifact-like
    ncdir = "new_cropped_cells"
    if os.path.isdir(ncdir):
        all_files = [f for f in os.listdir(ncdir) if f.lower().endswith(VALID_EXTS)]
        random.shuffle(all_files)

        for f in all_files[:300]:  # check 300 candidates
            path = os.path.join(ncdir, f)
            img = cv2.imread(path)
            if img is None:
                continue
            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Artifact criteria: very blurry, very small, very large, or odd aspect ratio
            ar = max(w, h) / (min(w, h) + 1e-5)
            is_artifact = (
                blur < 50             # very blurry
                or (w < 25 or h < 25)  # tiny fragment
                or ar > 3.0            # extreme aspect ratio (scratch/artifact)
                or (w > 200 and h > 200)  # too large (multi-cell clump)
            )

            if is_artifact:
                candidates.append({
                    "path": path,
                    "filename": f,
                    "pipeline_label": "artifact",
                    "source_smear": "new_cropped_cells",
                    "source_type": "new_cropped_cells",
                    "artifact_reason": (
                        "blurry" if blur < 50 else
                        "tiny" if (w < 25 or h < 25) else
                        "extreme_ar" if ar > 3.0 else
                        "multi_cell_clump"
                    ),
                    "blur_score": round(blur, 1),
                    "dimensions": f"{w}x{h}",
                })

            if len(candidates) >= 60:  # collect more than needed, then select
                break

    # Also pick some non-artifact crops from new_cropped_cells as "good artifact" examples
    # (normal-looking but from unlabeled pool → borderline/ambiguous)
    if os.path.isdir(ncdir) and len(candidates) < 60:
        all_files2 = [f for f in os.listdir(ncdir) if f.lower().endswith(VALID_EXTS)]
        random.shuffle(all_files2)
        for f in all_files2[:200]:
            path = os.path.join(ncdir, f)
            if any(c["path"] == path for c in candidates):
                continue
            img = cv2.imread(path)
            if img is None:
                continue
            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            # Moderate blur zone: not clearly good, not clearly bad
            if 30 < blur < 80:
                candidates.append({
                    "path": path,
                    "filename": f,
                    "pipeline_label": "artifact",
                    "source_smear": "new_cropped_cells",
                    "source_type": "new_cropped_cells",
                    "artifact_reason": "borderline_quality",
                    "blur_score": round(blur, 1),
                    "dimensions": f"{w}x{h}",
                })
            if len(candidates) >= 60:
                break

    return candidates


def prioritize_problematic(crops, source_priorities):
    """
    Re-order crops to prioritize those from problematic smears.
    Returns the same list but with priority crops first.
    """
    priority = []
    rest = []
    for c in crops:
        smear = c.get("source_smear", "")
        if any(p in smear for p in source_priorities):
            priority.append(c)
        else:
            rest.append(c)
    random.shuffle(priority)
    random.shuffle(rest)
    return priority + rest


def build_validation_set():
    print("=" * 70)
    print("  LabMind — Cell-Level Validation Set Builder")
    print("  NO code changes. Curate + copy only.")
    print("=" * 70)
    print()

    # Create output dirs
    for d in [NORMAL_DIR, SICKLE_DIR, ARTIFACT_DIR]:
        os.makedirs(d, exist_ok=True)

    # ── Collect from all sources ──
    print("  Collecting crops from sources...")

    # Source 1: debug_crops
    dc_normal, dc_sickle = collect_debug_crops()
    print(f"    debug_crops:       {len(dc_normal)} normal, {len(dc_sickle)} sickle")

    # Source 2: dataset_v1_2class/val
    dv_normal, dv_sickle = collect_dataset_val()
    print(f"    dataset_v1_2class: {len(dv_normal)} normal, {len(dv_sickle)} sickle")

    # Source 3: cropped_cells/rbc
    cr_normal = collect_cropped_rbc()
    print(f"    cropped_cells/rbc: {len(cr_normal)} normal")

    # Source 4: artifact candidates
    artifacts = collect_artifact_candidates()
    print(f"    artifact cands:    {len(artifacts)}")
    print()

    # ── Merge and prioritize ──
    # Normal: prioritize debug_crops from normal_04 (FP-prone smear)
    all_normal = dc_normal + dv_normal + cr_normal
    all_normal = prioritize_problematic(all_normal, ["normal_04", "normal_01", "normal_03"])

    # Sickle: prioritize debug_crops from sickle_05 and weak sickle smears
    all_sickle = dc_sickle + dv_sickle
    all_sickle = prioritize_problematic(all_sickle, ["sickle_05", "sickle_03", "Sickle_Cell_Blood_Smear"])

    # Artifact: already collected with priority on bad-quality crops
    random.shuffle(artifacts)

    print(f"  Total pool: {len(all_normal)} normal, {len(all_sickle)} sickle, {len(artifacts)} artifact")
    print()

    # ── Select and copy ──
    labels = []
    used_hashes = set()  # deduplicate by content hash

    def copy_crop(entry, target_dir, class_label, idx):
        """Copy a crop to the target directory with a standardized name."""
        src = entry["path"]
        # Quick dedup: use file size as a rough hash
        fsize = os.path.getsize(src)
        key = f"{fsize}_{entry['filename']}"
        if key in used_hashes:
            return False
        used_hashes.add(key)

        ext = os.path.splitext(src)[1].lower()
        new_name = f"{class_label}_{idx:04d}{ext}"
        dst = os.path.join(target_dir, new_name)
        shutil.copy2(src, dst)

        quality = compute_crop_quality(dst)

        label_entry = {
            "filename": new_name,
            "class": class_label,
            "source_smear": entry.get("source_smear", "unknown"),
            "source_type": entry.get("source_type", "unknown"),
            "original_filename": entry["filename"],
            "notes": "",
        }

        # Add artifact-specific notes
        if class_label == "artifact" and "artifact_reason" in entry:
            label_entry["notes"] = entry["artifact_reason"]
            if "blur_score" in entry:
                label_entry["notes"] += f" (blur={entry['blur_score']})"
            if "dimensions" in entry:
                label_entry["notes"] += f" dims={entry['dimensions']}"

        # Add priority notes
        if entry.get("source_smear") in ("normal_04",):
            label_entry["notes"] = (label_entry["notes"] + " FP-prone_smear").strip()
        if entry.get("source_smear") in ("sickle_05", "sickle_03"):
            label_entry["notes"] = (label_entry["notes"] + " weak_sickle_smear").strip()

        if quality:
            label_entry["blur_score"] = quality.get("blur_score", 0)
            label_entry["dimensions"] = f"{quality.get('width', 0)}x{quality.get('height', 0)}"

        labels.append(label_entry)
        return True

    # Copy normals
    print(f"  Copying {TARGET_NORMAL} normal crops...")
    normal_copied = 0
    for entry in all_normal:
        if normal_copied >= TARGET_NORMAL:
            break
        if copy_crop(entry, NORMAL_DIR, "normal", normal_copied):
            normal_copied += 1

    # Copy sickle
    print(f"  Copying {TARGET_SICKLE} sickle crops...")
    sickle_copied = 0
    for entry in all_sickle:
        if sickle_copied >= TARGET_SICKLE:
            break
        if copy_crop(entry, SICKLE_DIR, "sickle", sickle_copied):
            sickle_copied += 1

    # Copy artifact
    print(f"  Copying {TARGET_ARTIFACT} artifact crops...")
    artifact_copied = 0
    for entry in artifacts:
        if artifact_copied >= TARGET_ARTIFACT:
            break
        if copy_crop(entry, ARTIFACT_DIR, "artifact", artifact_copied):
            artifact_copied += 1

    print()

    # ── Count source distribution ──
    source_dist = {}
    smear_dist = {}
    for l in labels:
        st = l["source_type"]
        source_dist[st] = source_dist.get(st, 0) + 1
        sm = l["source_smear"]
        smear_dist[sm] = smear_dist.get(sm, 0) + 1

    # ── Save labels.json ──
    labels_path = os.path.join(OUT_DIR, "labels.json")
    output = {
        "version": "v1-baseline",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "total_crops": len(labels),
        "counts": {
            "normal": normal_copied,
            "sickle": sickle_copied,
            "artifact": artifact_copied,
        },
        "source_distribution": source_dist,
        "smear_distribution": smear_dist,
        "labels": labels,
    }

    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── Summary ──
    print("=" * 70)
    print("  VALIDATION SET CREATED")
    print("=" * 70)
    print(f"  Normal:   {normal_copied}/{TARGET_NORMAL}")
    print(f"  Sickle:   {sickle_copied}/{TARGET_SICKLE}")
    print(f"  Artifact: {artifact_copied}/{TARGET_ARTIFACT}")
    print(f"  Total:    {len(labels)}")
    print()
    print(f"  Source distribution:")
    for k, v in sorted(source_dist.items()):
        print(f"    {k}: {v}")
    print()
    print(f"  Smear distribution:")
    for k, v in sorted(smear_dist.items()):
        print(f"    {k}: {v}")
    print()
    print(f"  labels.json → {os.path.abspath(labels_path)}")
    print(f"  Directory   → {os.path.abspath(OUT_DIR)}")
    print("=" * 70)


if __name__ == "__main__":
    build_validation_set()
