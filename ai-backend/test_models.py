"""Test importing all models in sequence."""
import traceback
models = [
    "app.db.models.user",
    "app.db.models.patient",
    "app.db.models.lab_case",
    "app.db.models.case_asset",
    "app.db.models.analysis_run",
    "app.db.models.analysis_result",
    "app.db.models.diagnostic_report",
    "app.db.models.report_review",
    "app.db.models.alert",
    "app.db.models.audit_log",
    "app.db.models.rasha_message",
]

import importlib
for m in models:
    try:
        importlib.import_module(m)
        print(f"OK: {m}")
    except Exception as ex:
        print(f"FAIL: {m} -> {type(ex).__name__}: {ex}")
        traceback.print_exc()
        # Write the error details to file  
        with open("d:/New folder/ai-backend/model_error.txt", "w") as f:
            f.write(f"Module: {m}\n")
            f.write(f"Error: {type(ex).__name__}: {ex}\n\n")
            f.write(traceback.format_exc())
        break
