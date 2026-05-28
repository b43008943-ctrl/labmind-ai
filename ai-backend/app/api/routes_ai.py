"""
LabMind AI — AI Proxy API Routes (Rasha, Quiz, Summarize)
All Gemini API calls are proxied through these endpoints.
The API key NEVER reaches the frontend.

Sprint 5: Added input validation and length limits.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_client_ip, get_current_user
from app.db.database import get_db
from app.db.models.user import User
from app.providers.gemini_provider import GeminiProvider
from app.schemas.rasha import (
    RashaMessageItem,
    RashaRequest,
    RashaResponse,
    RashaSessionResponse,
)
from app.services.rasha_service import RashaService

router = APIRouter(prefix="/api/ai", tags=["AI Proxy"])


@router.post("/ask-rasha", response_model=RashaResponse)
def ask_rasha(
    body: RashaRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip = get_client_ip(request)
    service = RashaService(db)
    return service.chat(body, user_id=current_user.id, ip=ip)


@router.get("/sessions", response_model=list[RashaSessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RashaService(db)
    return service.list_sessions(current_user.id)


@router.get("/sessions/{session_id}/messages", response_model=list[RashaMessageItem])
def get_session_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RashaService(db)
    return service.get_messages(session_id, current_user.id)


class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    num_questions: int = Field(default=5, ge=1, le=20)


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=15000)


@router.post("/generate-quiz")
def generate_quiz(
    body: QuizRequest,
    current_user: User = Depends(get_current_user),
):
    gemini = GeminiProvider()
    return gemini.generate_quiz(body.topic, body.num_questions)


@router.post("/summarize")
def summarize_text(
    body: SummarizeRequest,
    current_user: User = Depends(get_current_user),
):
    gemini = GeminiProvider()
    return gemini.summarize(body.text)


# ─────────────────────────────────────────────────────────────
# NEW: Migrated from frontend geminiApi.js (API key security)
# ─────────────────────────────────────────────────────────────

class VideoScriptRequest(BaseModel):
    file_text: str = Field(..., min_length=1, max_length=50000)


class SmartQuizRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000)


class HoloImageRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=500)


@router.post("/generate-video-script")
def generate_video_script(
    body: VideoScriptRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate an Arabic educational summary from uploaded research text."""
    gemini = GeminiProvider()
    result = gemini.generate_video_script(body.file_text)
    if result.get("error"):
        return {"success": False, "content": None, "error": result["error"]}
    return {"success": True, "content": result["reply"]}


@router.post("/generate-smart-quiz")
def generate_smart_quiz(
    body: SmartQuizRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate 3 Arabic MCQ questions from input text."""
    gemini = GeminiProvider()
    result = gemini.generate_smart_quiz(body.text)
    if result.get("error"):
        return {"success": False, "data": None, "error": result["error"]}

    # Parse the JSON array from the reply, stripping markdown if present
    import json as _json
    raw = result["reply"].replace("```json", "").replace("```", "").strip()
    try:
        quiz_data = _json.loads(raw)
    except _json.JSONDecodeError:
        return {"success": False, "data": None, "error": "Failed to parse quiz JSON from AI response."}

    return {"success": True, "data": quiz_data}


@router.post("/generate-holo-image")
def generate_holo_image(
    body: HoloImageRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a holographic image via Imagen or Pollinations fallback."""
    gemini = GeminiProvider()
    result = gemini.generate_holo_image(body.prompt)
    return {"success": True, "url": result["image_url"], "source": result["source"]}
