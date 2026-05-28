"""
RETIRED — Legacy Blood Smear Analysis Endpoint

This file previously contained a standalone FastAPI app with a synchronous
/api/analyze-blood-smear endpoint. It has been retired as part of the
Hematology V1 Rebuild (Phase 1).

The official analysis path is now:
  Frontend → POST /api/analyses/trigger → AnalysisService → Celery → V1Provider

If you need to run the legacy pipeline for testing, restore from version control.
"""

# This file is intentionally empty. Do not add new code here.
# The production entry point is: app.main:app
