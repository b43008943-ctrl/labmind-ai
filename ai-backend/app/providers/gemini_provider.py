"""
LabMind AI — Gemini API Provider
Server-side proxy to Google Gemini. The API key NEVER leaves this backend.

Production hardening:
- Shared httpx.Client with connection pooling (lifecycle managed per-provider instance)
- Request timeout of 30s
- Input length limits enforced at the route level
"""

import httpx

from app.core.config import get_settings


GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_TIMEOUT = 30.0  # seconds


class GeminiProvider:
    """Handles all outbound calls to Google Gemini API."""

    # Class-level shared client — connection pooling across calls
    _client: httpx.Client | None = None

    def __init__(self):
        self.api_key = get_settings().GEMINI_API_KEY
        if GeminiProvider._client is None:
            GeminiProvider._client = httpx.Client(timeout=GEMINI_TIMEOUT)

    def chat(
        self,
        user_message: str,
        system_instruction: str | None = None,
        history: list[dict] | None = None,
    ) -> dict:
        """
        Send a chat message to Gemini and return the response.
        Returns {"reply": str, "tokens_used": int | None}
        """
        if not self.api_key:
            return {
                "reply": "Gemini API key is not configured on the server.",
                "tokens_used": None,
            }

        # Build chat history contents
        contents = []
        if history:
            for msg in history:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        contents.append({"role": "user", "parts": [{"text": user_message}]})

        body: dict = {"contents": contents}

        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        body["generationConfig"] = {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }

        url = (
            f"{GEMINI_BASE_URL}/models/gemini-2.0-flash:generateContent"
            f"?key={self.api_key}"
        )

        try:
            resp = self._client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()

            # Extract text from response
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                reply_text = parts[0].get("text", "") if parts else ""
            else:
                reply_text = "No response generated."

            # Extract token usage
            usage = data.get("usageMetadata", {})
            tokens = usage.get("totalTokenCount")

            return {"reply": reply_text, "tokens_used": tokens}

        except httpx.TimeoutException:
            return {
                "reply": "The AI service timed out. Please try again.",
                "tokens_used": None,
            }
        except httpx.HTTPStatusError as e:
            return {
                "reply": f"Gemini API error: {e.response.status_code}",
                "tokens_used": None,
            }
        except Exception as e:
            return {
                "reply": f"Gemini connection error: {str(e)}",
                "tokens_used": None,
            }

    def generate_quiz(self, topic: str, num_questions: int = 5) -> dict:
        """Generate a quiz via Gemini."""
        prompt = (
            f"Generate a medical quiz with {num_questions} multiple-choice questions "
            f"about: {topic}. "
            f"Return valid JSON with this structure: "
            f'{{"questions": [{{"question": "...", "options": ["A","B","C","D"], "correct": "A", "explanation": "..."}}]}}'
        )
        return self.chat(
            user_message=prompt,
            system_instruction="You are a medical education AI. Return only valid JSON, no markdown.",
        )

    def summarize(self, text: str) -> dict:
        """Summarize a document or text passage."""
        prompt = f"Summarize the following medical/scientific text in 3-5 concise bullet points:\n\n{text}"
        return self.chat(
            user_message=prompt,
            system_instruction="You are a medical summarization assistant. Be precise and clinical.",
        )

    # ────────────────────────────────────────────────────────
    # NEW: Migrated from frontend geminiApi.js (security fix)
    # ────────────────────────────────────────────────────────

    def generate_video_script(self, file_text: str) -> dict:
        """
        Generate an Arabic educational summary from uploaded research text.
        Mirrors the old frontend generateAiVideo() prompt exactly.
        Returns {"reply": str, "tokens_used": int | None}
        """
        prompt = (
            "Summarize the following educational text directly and simply in Arabic. "
            "DO NOT add any titles, headers, intro text, metadata, or formatting. "
            "Just output the pure Arabic text.\n\n"
            "RESEARCH CONTENT:\n\"\"\"\n"
            f"{file_text[:30000]}\n\"\"\""
        )

        body: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,
            },
        }

        url = (
            f"{GEMINI_BASE_URL}/models/gemini-2.0-flash:generateContent"
            f"?key={self.api_key}"
        )

        try:
            resp = self._client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()

            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                reply_text = parts[0].get("text", "") if parts else ""
            else:
                reply_text = ""

            tokens = data.get("usageMetadata", {}).get("totalTokenCount")
            return {"reply": reply_text, "tokens_used": tokens}

        except httpx.TimeoutException:
            return {"reply": "", "tokens_used": None, "error": "The AI service timed out."}
        except httpx.HTTPStatusError as e:
            return {"reply": "", "tokens_used": None, "error": f"API Error ({e.response.status_code})"}
        except Exception as e:
            return {"reply": "", "tokens_used": None, "error": str(e)}

    def generate_smart_quiz(self, text: str) -> dict:
        """
        Generate 3 Arabic multiple-choice questions from input text.
        Mirrors the old frontend generateSmartQuiz() prompt exactly.
        Returns {"reply": str, "tokens_used": int | None}
        — reply contains a raw JSON array string for the frontend to parse.
        """
        prompt = (
            "Based on the following text, generate 3 multiple-choice questions in Arabic. "
            "Return ONLY a valid JSON array of objects. Do not use markdown code blocks like ```json. "
            "Format:\n"
            "[\n"
            '  {\n'
            '    "question": "Question text here?",\n'
            '    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],\n'
            '    "correctAnswer": "Exact text of the correct option"\n'
            '  }\n'
            "]\n"
            f"Text: {text}"
        )

        body: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            },
        }

        url = (
            f"{GEMINI_BASE_URL}/models/gemini-2.0-flash:generateContent"
            f"?key={self.api_key}"
        )

        try:
            resp = self._client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()

            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                reply_text = parts[0].get("text", "") if parts else ""
            else:
                reply_text = ""

            tokens = data.get("usageMetadata", {}).get("totalTokenCount")
            return {"reply": reply_text, "tokens_used": tokens}

        except httpx.TimeoutException:
            return {"reply": "", "tokens_used": None, "error": "The AI service timed out."}
        except httpx.HTTPStatusError as e:
            return {"reply": "", "tokens_used": None, "error": f"API Error ({e.response.status_code})"}
        except Exception as e:
            return {"reply": "", "tokens_used": None, "error": str(e)}

    def generate_holo_image(self, prompt: str) -> dict:
        """
        Generate a holographic image via Google Imagen, with Pollinations.ai fallback.
        Mirrors the old frontend generateHoloImage() logic exactly.
        Returns {"image_url": str, "source": "imagen" | "pollinations"}
        """
        if not self.api_key:
            # Skip Imagen, go straight to fallback
            from urllib.parse import quote
            fallback_url = (
                f"https://image.pollinations.ai/prompt/"
                f"{quote(prompt, safe='')}?nologo=true&width=600&height=800"
            )
            return {"image_url": fallback_url, "source": "pollinations"}

        # Try Google Imagen first
        imagen_url = (
            f"{GEMINI_BASE_URL}/models/imagen-3.0-generate-001:predict"
            f"?key={self.api_key}"
        )
        try:
            resp = self._client.post(
                imagen_url,
                json={
                    "instances": [{"prompt": prompt}],
                    "parameters": {"sampleCount": 1, "aspectRatio": "3:4"},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                b64 = (data.get("predictions") or [{}])[0].get("bytesBase64Encoded")
                if b64:
                    return {
                        "image_url": f"data:image/png;base64,{b64}",
                        "source": "imagen",
                    }
        except Exception:
            pass  # Fall through to Pollinations

        # Fallback: Pollinations.ai (unauthenticated, instant URL)
        from urllib.parse import quote
        fallback_url = (
            f"https://image.pollinations.ai/prompt/"
            f"{quote(prompt, safe='')}?nologo=true&width=600&height=800"
        )
        return {"image_url": fallback_url, "source": "pollinations"}

    @staticmethod
    def _url_encode(text: str) -> str:
        from urllib.parse import quote
        return quote(text, safe="")
