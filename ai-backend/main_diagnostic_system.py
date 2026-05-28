"""
RETIRED — CLI Diagnostic System

This file previously contained a standalone CLI batch processor for blood smear
analysis. It has been retired as part of the Hematology V1 Rebuild (Phase 1).

The diagnostic engine is now accessed exclusively via:
  V1Provider (app/providers/ai_provider_v1.py) → called by Celery worker

If you need to run the CLI pipeline for testing, restore from version control.
"""

# This file is intentionally empty. Do not add new code here.