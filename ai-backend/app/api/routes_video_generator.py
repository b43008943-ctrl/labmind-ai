"""
LabMind AI — Video Generator API
Accepts study material (file or text), sends to Gemini,
returns a structured slideshow with scenes, narration, and quizzes.
"""

import io
import json as _json

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.db.models.user import User

router = APIRouter(prefix="/api/video-generator", tags=["Video Generator"])

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_TIMEOUT = 45.0
MAX_TEXT_LEN = 5000

SLIDESHOW_PROMPT = """You are a medical education content creator specializing in creating engaging visual learning experiences for medical laboratory students.

Convert the following study material into an ANIMATED EDUCATIONAL SLIDESHOW with 5-8 scenes.

For EACH scene, provide:
1. scene_number: (1, 2, 3...)
2. title: Short catchy title (5-8 words)
3. narration: The explanation text (2-3 sentences, simple language, engaging)
4. visual_description: Describe what should be shown visually
5. icon: Choose from: ["dna", "cell", "bacteria", "virus", "blood", "microscope", "petri_dish", "syringe", "pill", "heart", "lungs", "kidney", "liver", "brain", "bone", "muscle", "eye", "flask", "test_tube", "thermometer", "stethoscope", "chromosome", "antibody", "parasite", "fungus", "worm"]
6. color_theme: A hex color matching the scene mood
7. key_facts: 2-3 bullet point facts
8. quiz_question: One quiz question with 4 options and correct answer index (0-3)

Also provide:
- presentation_title: Overall title
- total_duration_estimate: Estimated reading time in seconds
- summary: 2 sentence summary

Respond ONLY with valid JSON (no markdown code blocks):
{
  "presentation_title": "...",
  "total_duration_estimate": 120,
  "summary": "...",
  "scenes": [
    {
      "scene_number": 1,
      "title": "...",
      "narration": "...",
      "visual_description": "...",
      "icon": "parasite",
      "color_theme": "#FF9800",
      "key_facts": ["...", "..."],
      "quiz_question": {
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "correct": 0
      }
    }
  ]
}

STUDY MATERIAL:
\"\"\"
{content}
\"\"\""""


def _extract_text_from_pdf(data: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        return "\n".join(pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {e}")


def _extract_text_from_docx(data: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read DOCX: {e}")


@router.post("/generate")
async def generate_slideshow(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    topic_hint: str | None = Form(None),
    current_user: User = Depends(get_current_user),
):
    """Generate an educational slideshow from uploaded study material or text."""

    settings = get_settings()
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="AI service is not configured.")

    # ── Extract content ──
    content = ""

    if file and file.filename:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        name_lower = file.filename.lower()
        if name_lower.endswith(".pdf"):
            content = _extract_text_from_pdf(file_bytes)
        elif name_lower.endswith(".docx"):
            content = _extract_text_from_docx(file_bytes)
        elif name_lower.endswith(".txt"):
            content = file_bytes.decode("utf-8", errors="replace")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, or TXT.")
    elif text and text.strip():
        content = text.strip()
    else:
        raise HTTPException(status_code=400, detail="No content provided. Upload a file or enter text.")

    if len(content.strip()) < 20:
        raise HTTPException(status_code=400, detail="Content is too short to generate a slideshow.")

    # Truncate to limit
    content = content[:MAX_TEXT_LEN]

    # Prepend topic hint if provided
    if topic_hint and topic_hint.strip():
        content = f"Topic: {topic_hint.strip()}\n\n{content}"

    # ── Call Gemini ──
    prompt = SLIDESHOW_PROMPT.replace("{content}", content)

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
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

    # ── Parse response ──
    candidates = data.get("candidates", [])
    if not candidates:
        raise HTTPException(status_code=502, detail="AI returned no response.")

    parts = candidates[0].get("content", {}).get("parts", [])
    reply_text = parts[0].get("text", "") if parts else ""

    cleaned = reply_text.replace("```json", "").replace("```", "").strip()
    try:
        result = _json.loads(cleaned)
    except _json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="AI response was not in the expected format. Please try again.")

    return {"success": True, "data": result}
