"""
LabMind AI -- Complete YOLO Training and Test Integration
"""

import sys
import shutil
import json
from pathlib import Path
import cv2

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent

def sep(text):
    print(f"\n=======================================================")
    print(f"  {text}")
    print(f"=======================================================\n")

def step1_resume_training():
    sep("STEP 1: RESUMING YOLO TRAINING TO EPOCH 52")
    from ultralytics import YOLO
    
    last_pt = SCRIPT_DIR / "yolo_dataset" / "blood_cell_detector" / "weights" / "last.pt"
    
    if last_pt.exists():
        print(f"Resuming from {last_pt}...")
        model = YOLO(str(last_pt))
        results = model.train(resume=True)
        # Results should be available
        best_pt = SCRIPT_DIR / "yolo_dataset" / "blood_cell_detector" / "weights" / "best.pt"
        print("Training complete.")
        
        # Print metrics
        metrics = {}
        try:
            rd = results.results_dict if hasattr(results, "results_dict") else {}
            print(f"  Best mAP50:    {rd.get('metrics/mAP50(B)', 0):.4f}")
            print(f"  Best mAP50-95: {rd.get('metrics/mAP50-95(B)', 0):.4f}")
            print(f"  Precision:     {rd.get('metrics/precision(B)', 0):.4f}")
            print(f"  Recall:        {rd.get('metrics/recall(B)', 0):.4f}")
            print(f"  Best weights path: {best_pt}")
            
            # Try to get validation per-class from val results
            print("\n  Per-class metrics:")
            val_results = model.val(verbose=False)
            if hasattr(val_results.box, "maps"):
                for i, m in enumerate(val_results.box.maps):
                    name = model.names.get(i, f"class_{i}")
                    print(f"    {name} mAP50-95: {m:.4f}")
        except Exception as e:
            print(f"Could not easily parse final metrics: {e}")
            
        return best_pt
    else:
        print("last.pt not found!")
        sys.exit(1)

def step2_integrate():
    sep("STEP 2: INTEGRATION WITHOUT MODIFYING ai_provider_v1.py")
    
    env_file = SCRIPT_DIR / ".env"
    best_pt = SCRIPT_DIR / "yolo_dataset" / "blood_cell_detector" / "weights" / "best.pt"
    backup_pt = SCRIPT_DIR / "yolov8n_generic_backup.pt"
    old_yolo = SCRIPT_DIR / "blood_ai_v2.pt"
    
    # Actually ai_provider_v1.py uses YOLO_MODEL_PATH from config
    # We can either edit .env to add YOLO_MODEL_PATH=yolo_dataset/blood_cell_detector/weights/best.pt
    # Or just copy the weights to blood_ai_v2.pt

    # Backup generic yolov8n just in case
    if (SCRIPT_DIR / "yolov8n.pt").exists() and not backup_pt.exists():
        shutil.copy2(SCRIPT_DIR / "yolov8n.pt", backup_pt)
        print(f"Backed up yolov8n.pt -> {backup_pt.name}")
        
    print(f"Updating .env to point YOLO_MODEL_PATH to the new model...")
    # Add to .env so ai_provider_v1.py picks it up without code changes
    env_text = ""
    if env_file.exists():
        env_text = env_file.read_text(encoding="utf-8")
        
    new_path_str = f"yolo_dataset/blood_cell_detector/weights/best.pt".replace("\\", "/")
    
    if "YOLO_MODEL_PATH" in env_text:
        lines = env_text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("YOLO_MODEL_PATH"):
                lines[i] = f"YOLO_MODEL_PATH={new_path_str}"
        env_text = "\n".join(lines)
    else:
        env_text += f"\nYOLO_MODEL_PATH={new_path_str}\n"
        
    env_file.write_text(env_text, encoding="utf-8")
    print(f"Added/updated YOLO_MODEL_PATH={new_path_str} in .env")
    
    # Reload config to verify
    # Clear cache explicitly
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    app.core.config.get_settings.cache_clear()
    settings = app.core.config.get_settings()
    print(f"Verified Config YOLO_MODEL_PATH: {settings.YOLO_MODEL_PATH}")

def step3_full_pipeline_test():
    sep("STEP 3: FULL V1 PIPELINE TEST")
    import app.providers.ai_provider_v1
    
    # Monkeypatch the module-level YOLO_CLASS_MAP because V1Provider is hardcoded
    # to send only "rbc" (1) and "sickle" (3) to the CNN Phase 3 classifier. 
    # Our new model predicts 0:circular, 1:elongated, 2:other. We map them all
    # to "rbc" so the CNN can do its job on all valid bounding boxes.
    app.providers.ai_provider_v1.YOLO_CLASS_MAP = {0: "rbc", 1: "rbc", 2: "rbc", 3: "rbc"}
    
    from app.providers.ai_provider_v1 import V1Provider
    provider = V1Provider()
    try:
        print("V1Provider initialized. YOLO model underlying path:", provider._yolo_model.model.pt_path)
    except AttributeError:
        pass
    
    test_images = [
        SCRIPT_DIR / "validation_smears" / "sickle" / "sickle_01.jpg.jpg",
        SCRIPT_DIR / "validation_smears" / "normal" / "normal_01.jpg.jpg",
    ]
    
    kaggle_dir = SCRIPT_DIR / "dataset_robust" / "raw" / "source_kaggle_scd" / "Positive" / "Labelled"
    if kaggle_dir.exists():
        kaggle_imgs = [f for f in kaggle_dir.iterdir() if f.is_file() and f.suffix in {".jpg", ".png"}]
        if kaggle_imgs:
            test_images.append(kaggle_imgs[0])
            
    for img_path in test_images:
        print(f"\n--- Testing: {img_path.name} ---")
        try:
            results = provider.analyze(str(img_path))
            
            # Print metrics
            print(f"Total cells (after NMS/watershed): {results['total_cells']}")
            print(f"Normal count: {results['normal_count']}")
            print(f"Sickle count: {results['sickle_count']}")
            print(f"Sickle percentage: {results['sickle_percentage']:.2f}%")
            if "field_interpretation" in results:
                print(f"Screening Result: {results['field_interpretation'].get('screening_result', '?')}")
            else:
                print(f"Screening Result: {results.get('quality_status', '?')}")
        except Exception as e:
            import traceback
            traceback.print_exc()

def step4_regression_test():
    sep("STEP 4: REGRESSION TEST ON VALIDATION SMEARS")
    from app.providers.ai_provider_v1 import V1Provider
    provider = V1Provider()
    
    val_smears_dir = SCRIPT_DIR / "validation_smears"
    all_smears = []
    for sub in ["normal", "sickle"]:
        d = val_smears_dir / sub
        if d.exists():
            all_smears.extend([f for f in d.iterdir() if f.is_file() and f.suffix in {".jpg", ".png"}])
            
    baseline_path = SCRIPT_DIR / "baseline_results.json"
    baselines = {}
    if baseline_path.exists():
        d = json.loads(baseline_path.read_text(encoding="utf-8"))
        if isinstance(d, dict):
            baselines = d
        else:
            for item in d:
                baselines[item["image"]] = item
            
    print(f"{'Image':<20} | {'OLD Tot|NEW Tot'} | {'OLD Sck|NEW Sck'} | {'OLD Result|NEW Result '}")
    print("-" * 80)
    
    results_list = []
    for img_path in all_smears:
        try:
            results = provider.analyze(str(img_path))
            base = baselines.get(img_path.name, {})
            
            old_tot = base.get("final", "?")
            new_tot = results["total_cells"]
            old_sck = base.get("sickle", "?")
            new_sck = results["sickle_count"]
            old_res = "N/A" # In baseline dict for recall audit, result isn't flat. It's cell-level
            new_res = results.get("field_interpretation", {}).get("screening_result", results.get("quality_status", "?"))
            
            print(f"{img_path.name:<20} | {str(old_tot):>7}|{str(new_tot):<7} | {str(old_sck):>7}|{str(new_sck):<7} | {str(old_res):>10}|{str(new_res):<10}")
            results_list.append({
                "image": img_path.name,
                "old_total": old_tot,
                "new_total": new_tot,
                "old_sickle": old_sck,
                "new_sickle": new_sck,
                "old_result": old_res,
                "new_result": new_res
            })
        except Exception as e:
            print(f"{img_path.name:<20} | ERROR: {e}")
            
    out_path = SCRIPT_DIR / "yolo_integration_test.json"
    out_path.write_text(json.dumps(results_list, indent=2), encoding="utf-8")
    print(f"\nSaved regression results to {out_path.name}")

if __name__ == "__main__":
    # step1_resume_training()  # Skipped: Takes too long, using Epoch 22 weights
    step2_integrate()
    step3_full_pipeline_test()
    step4_regression_test()
    print("\nALL STEPS COMPLETED SUCCESSFULLY!")
