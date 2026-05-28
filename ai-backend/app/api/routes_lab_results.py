"""
LabMind AI — Lab Results Analyzer API
Accepts a photo of a paper lab report, sends it to Gemini Vision,
and returns structured analysis with clinical interpretations.
"""

import base64
import json as _json

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.db.models.user import User

router = APIRouter(prefix="/api/lab-results", tags=["Lab Results Analyzer"])

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_TIMEOUT = 45.0  # longer timeout for vision tasks
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ANALYSIS_PROMPT = """You are a clinical laboratory specialist and medical educator.

A user has uploaded a photo of a medical laboratory report. Analyze the image and extract ALL test results visible.

For EACH test result found, provide:
1. test_name: The name of the test (e.g., "Hemoglobin", "WBC Count", "Glucose")
2. value: The numeric value shown (as a number or string if non-numeric)
3. unit: The unit of measurement
4. reference_range: The normal reference range for this test
5. status: "normal", "high", or "low"
6. interpretation: A brief explanation of what this value means clinically
7. advice: Medical advice or recommendation based on this value

Also provide:
- report_type: e.g. "CBC", "Metabolic Panel", "Urinalysis", "Lipid Panel", etc.
- patient_info: any visible patient info (keep anonymized — no full names)
- overall_summary: A paragraph summarizing the overall health picture
- urgent_findings: List of any critical/urgent values needing immediate attention (empty list if none)
- recommendations: List of general health recommendations
- disclaimer: "This analysis is for educational purposes only. Please consult your healthcare provider for medical advice."

Respond ONLY with valid JSON (no markdown code blocks). Use this structure:
{
  "report_type": "CBC",
  "patient_info": "...",
  "results": [
    {
      "test_name": "Hemoglobin",
      "value": 14.5,
      "unit": "g/dL",
      "reference_range": "13.5-17.5 g/dL",
      "status": "normal",
      "interpretation": "...",
      "advice": "..."
    }
  ],
  "overall_summary": "...",
  "urgent_findings": [],
  "recommendations": ["..."],
  "disclaimer": "This analysis is for educational purposes only. Please consult your healthcare provider for medical advice."
}"""


@router.post("/analyze")
async def analyze_lab_results(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Analyze a photo of a paper lab report using Gemini Vision."""

    settings = get_settings()
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="AI service is not configured.")

    # Validate file type
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted (JPG, PNG).")

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit.")

    # Encode to base64
    b64_data = base64.b64encode(file_bytes).decode("utf-8")

    # Build Gemini multimodal request
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"inlineData": {"mimeType": content_type, "data": b64_data}},
                    {"text": ANALYSIS_PROMPT},
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 4096,
        },
    }

    url = f"{GEMINI_BASE_URL}/models/gemini-2.0-flash:generateContent?key={api_key}"

    try:
        async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timed out. Please try again.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"AI service error ({e.response.status_code}).")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connection error: {str(e)}")

    # Extract reply text
    candidates = data.get("candidates", [])
    if not candidates:
        raise HTTPException(status_code=502, detail="AI returned no response. Try a clearer photo.")

    parts = candidates[0].get("content", {}).get("parts", [])
    reply_text = parts[0].get("text", "") if parts else ""

    if not reply_text.strip():
        raise HTTPException(
            status_code=502,
            detail="Unable to read the lab report. Please ensure the image is clear and well-lit.",
        )

    # Parse JSON from reply
    cleaned = reply_text.replace("```json", "").replace("```", "").strip()
    try:
        result = _json.loads(cleaned)
    except _json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail="AI response was not in the expected format. Please try again with a clearer image.",
        )

    return {"success": True, "data": result}
