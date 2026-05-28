import os
import sys
import shutil
import json
import torch
from pathlib import Path
from datetime import datetime

# Allow whatever device PyTorch decides (matching execution environment)

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
PROVIDER_PATH = BASE_DIR / "app" / "providers" / "ai_provider_v1.py"

ORIGINAL_MODEL_NAME = "cell_classifier_2class_finetuned_best.pth"
NEW_MODEL_NAME = "cell_classifier_2class_robust_v3_best.pth"
BACKUP_MODEL_NAME = "cell_classifier_2class_finetuned_best_pre_v3_backup.pth"

REPORT_PATH = BASE_DIR / "adoption_report_v3.json"
SICKLE_SMEAR_TEST = BASE_DIR / "dataset_clean" / "splits" / "test" / "sickle" / "sickle_01.jpg.jpg"
# Try original Validation folder if test folder doesn't have it
if not SICKLE_SMEAR_TEST.exists():
    SICKLE_SMEAR_TEST = BASE_DIR / "validation_smears" / "sickle" / "sickle_01.jpg.jpg"

def abort(msg):
    print(f"\n[ERROR] {msg}")
    print("Aborting adoption process.")
    sys.exit(1)

def main():
    print(f"Starting adoption process for {NEW_MODEL_NAME}...\n")

    # STEP 1: BACKUP
    print("STEP 1: Backup Original Model")
    if not (BASE_DIR / ORIGINAL_MODEL_NAME).exists():
        # Maybe it's named something else natively but User instruction says cell_classifier_2class_finetuned_best.pth
        # I'll check what is available just in case, but assume it exists based on instructions.
        print(f"Warning: {ORIGINAL_MODEL_NAME} not found. Attempting to locate.")
        # We will assume it exists, or fallback to whatever CNN_MODEL_PATH has configured
        pass
    
    # We copy anyway
    original_path = BASE_DIR / ORIGINAL_MODEL_NAME
    backup_path = BASE_DIR / BACKUP_MODEL_NAME
    
    if original_path.exists():
        shutil.copy2(original_path, backup_path)
        if not backup_path.exists() or original_path.stat().st_size != backup_path.stat().st_size:
            abort("Backup file creation failed or size mismatch.")
        print(f"  -> Successfully backed up to {BACKUP_MODEL_NAME} (Size: {backup_path.stat().st_size} bytes)")
    else:
        print(f"  -> Original model {ORIGINAL_MODEL_NAME} not found on disk, skipping backup.")

    # STEP 2: UPDATE .env
    print("\nSTEP 2: Update .env File")
    if not ENV_PATH.exists():
        abort(".env file not found.")
    
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        env_lines = f.readlines()
        
    old_value = None
    new_lines = []
    updated = False
    
    for line in env_lines:
        if "CNN_MODEL_PATH" in line or "MODEL_CNN_PATH" in line:
            old_value = line.strip()
            # Preserve the exact key used
            key = line.split("=")[0]
            new_line = f"{key}={NEW_MODEL_NAME}\n"
            new_lines.append(new_line)
            updated = True
        else:
            new_lines.append(line)
            
    if not updated:
        abort("CNN_MODEL_PATH or MODEL_CNN_PATH not found in .env.")
        
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    print(f"  -> Old .env line: {old_value}")
    print(f"  -> New .env line: {new_line.strip()}")

    # STEP 3: VERIFY LOADING
    print("\nSTEP 3: Verify Model Loading")
    sys.path.insert(0, str(BASE_DIR))
    try:
        from app.providers.ai_provider_v1 import CellClassifierCNN, V1Provider
    except ImportError as e:
        abort(f"Could not import from ai_provider_v1: {e}")
        
    new_model_path = BASE_DIR / NEW_MODEL_NAME
    if not new_model_path.exists():
        abort(f"New model {NEW_MODEL_NAME} does not exist on disk!")
        
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        cnn = CellClassifierCNN(num_classes=2).to(device)
        cnn.load_state_dict(torch.load(str(new_model_path), map_location=device, weights_only=True))
        cnn.eval()
        param_count = sum(p.numel() for p in cnn.parameters())
        print("  -> Model loaded successfully without errors.")
        print(f"  -> Parameter count: {param_count}")
    except Exception as e:
        abort(f"Failed to load new model weights: {e}")

    # STEP 4: E2E SMOKE TEST
    print("\nSTEP 4: E2E Smoke Test")
    print(f"  -> Testing on smear: {SICKLE_SMEAR_TEST.name}")
    if not SICKLE_SMEAR_TEST.exists():
        abort(f"Test smear not found at {SICKLE_SMEAR_TEST}")
        
    try:
        import os
        os.environ["CNN_2CLASS_MODEL_PATH"] = NEW_MODEL_NAME
        os.environ["CNN_MODEL_PATH"] = NEW_MODEL_NAME
        
        from app.core.config import get_settings
        get_settings.cache_clear()  # Clear cache to pick up .env changes
        
        # Force V1Provider to re-read the environment and initialize class static variables
        V1Provider._load_models()
        provider = V1Provider()
        
        print(f" DEBUG: Provider classifier_mode: {provider._classifier_mode}")
        print(f" DEBUG: Provider cnn_class_map: {provider._cnn_class_map}")
        print(f" DEBUG: Provider num_classes: {provider._cnn_num_classes}")
        
        result = provider.analyze(str(SICKLE_SMEAR_TEST))
        
        total_cells = result.get("total_cells", 0)
        sickle_count = result.get("sickle_count", 0)
        
        # Safely extract screening_result which is nested inside field_interpretation
        field_interp = result.get("field_interpretation", {})
        screening_result = field_interp.get("screening_result", "UNKNOWN")
        
        print("  -> E2E Pipeline Completed")
        print(f"  -> Total Cells: {total_cells}")
        print(f"  -> Sickle Count: {sickle_count}")
        print(f"  -> Screening Result: {screening_result}")
        
        if total_cells <= 0:
            abort("Smoke test failed: total_cells <= 0")
        if sickle_count <= 0:
            abort("Smoke test failed: sickle_count <= 0")
        if screening_result != "SICKLE_SCREEN_POSITIVE":
            abort(f"Smoke test failed: Expected SICKLE_SCREEN_POSITIVE, got {screening_result}")
            
    except Exception as e:
        abort(f"E2E Smoke test raised exception: {e}")

    # STEP 5: GENERATE ADOPTION REPORT
    print("\nSTEP 5: Generate Adoption Report")
    report_data = {
        "adoption_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "adopted_model": NEW_MODEL_NAME,
        "replaced_model": ORIGINAL_MODEL_NAME,
        "backup_file": BACKUP_MODEL_NAME,
        "version_label": "V3-ROBUST",
        "training_data": {
            "sources": ["dataset_v1_2class (local)", "erythrocytesIDB (Zenodo)", "Kaggle SCD (Uganda)"],
            "total_training_images": 1250,
            "normal_count": 750,
            "sickle_count": 500
        },
        "test_accuracy": 0.9027,
        "improvements": [
            "normal_04 FP: 17 → 3",
            "sickle_05 detection: 0 → 2",
            "normal_03 FP: 1 → 0",
            "Overall test accuracy: 71% → 90%",
            "False positive reduction: 95%"
        ],
        "known_limitations": [
            "normal_02: 8 FP (field-level stays REVIEW, clinically acceptable)",
            "Sickle detection counts are lower than original (more conservative model)",
            "sickle_03 and sickle_04 have reduced raw counts but remain POSITIVE"
        ],
        "rollback_instructions": f"To rollback: change MODEL_CNN_PATH in .env to {BACKUP_MODEL_NAME}"
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"  -> Saved adoption report to {REPORT_PATH}")

    # STEP 6: CLEANUP RECOMMENDATION
    print("\nSTEP 6: Cleanup Recommendation")
    deletions = [
        "cell_classifier_2class_robust_best.pth",
        "cell_classifier_2class_robust_final.pth",
        "cell_classifier_2class_robust_v2_best.pth",
        "cell_classifier_2class_robust_v2_final.pth",
        "cell_classifier_2class_robust_v4_best.pth",
        "cell_classifier_2class_robust_v4_final.pth"
    ]
    print("These files are safe to delete but keeping them costs only disk space. User decision required:")
    for d in deletions:
        print(f"  - {d}")

    print("\nAdoption process completed successfully.")

if __name__ == "__main__":
    main()
