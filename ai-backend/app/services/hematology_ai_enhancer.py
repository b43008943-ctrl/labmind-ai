"""
LabMind AI — Hematology AI Enhancement Module
==============================================

Enhances the rule-based clinical reasoning report with AI-generated
insights using Google Gemini 2.0 Flash.

Architecture
------------
1. Rule-based engine (hematology_clinical_reasoning.py) provides the
   deterministic clinical report.
2. This module feeds that report + sickle cell detection data into
   Gemini and asks for deeper pathophysiological reasoning, rare
   considerations, teaching pearls, and prioritised next steps.
3. The orchestrator ``generate_full_clinical_report()`` combines both
   into a single response for the frontend.

Design Decisions
----------------
- GeminiProvider is synchronous (httpx.Client).  We wrap it with
  ``asyncio.to_thread()`` so the enhancer can be awaited without
  blocking the event loop.
- AI enhancement is strictly optional — if Gemini is unavailable,
  misconfigured, or returns garbage, the rule-based report is returned
  intact with an error note.
- Retry logic: up to 2 attempts with 1-second backoff.
- Hard timeout: 10 seconds per attempt via ``asyncio.wait_for()``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("labmind.hematology_ai_enhancer")


# ────────────────────────────────────────────────────────────────────
# Prompt template
# ────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT_TEMPLATE = """\
You are a senior hematologist and medical educator at a teaching hospital.
A peripheral blood smear analysis was performed with AI-assisted sickle cell
screening. Here are the findings:

CELL COUNTS:
- Total cells detected: {total_cells}
- Normal RBCs: {normal_count}
- Sickle cells: {sickle_count}
- Sickle percentage: {sickle_pct:.1f}%
- Screening result: {screening_result}

Our rule-based system classified this as: {scenario_code}
Primary diagnosis: {primary_diagnosis}
Overall severity: {severity}

{patient_context_section}

Provide an enhanced clinical analysis in STRICT JSON format with these fields:

{{
  "pathophysiology": "2-3 sentences explaining the underlying pathophysiology of sickle cell disease relevant to these findings (HbS polymerization, sickling cascade, vaso-occlusion)",
  "clinical_correlation": [
    "Point 1: specific clinical question to ask patient (pain episodes, family history, medications)",
    "Point 2: physical exam finding to look for (pallor, jaundice, splenomegaly)",
    "Point 3: specific lab correlation (Hb electrophoresis pattern, reticulocyte count)"
  ],
  "rare_considerations": [
    {{
      "condition": "Name of rare complication or differential",
      "why_consider": "Brief reason based on the sickle cell findings",
      "clinical_clue": "What would suggest this"
    }}
  ],
  "teaching_pearls": [
    "Educational insight 1 about sickle cell morphology identification on peripheral smear",
    "Educational insight 2 about hemoglobin electrophoresis interpretation",
    "Educational insight 3 about management and emerging therapies (gene therapy, voxelotor, crizanlizumab)"
  ],
  "next_steps_priority": [
    {{
      "action": "Specific next step",
      "urgency": "immediate|urgent|routine",
      "rationale": "Why this step"
    }}
  ],
  "confidence_level": "high|moderate|low",
  "ai_summary": "One-paragraph clinical summary suitable for a medical chart"
}}

Return ONLY the JSON object, no markdown, no extra text.\
"""


def _build_prompt(
    cell_counts: dict[str, Any],
    rule_based_report: dict[str, Any],
    patient_context: dict[str, Any] | None = None,
) -> str:
    """Build the Gemini system prompt from cell counts and scenario."""
    # Patient context section
    if patient_context:
        ctx_lines = ["PATIENT CONTEXT:"]
        if "age" in patient_context:
            ctx_lines.append(f"- Age: {patient_context['age']}")
        if "sex" in patient_context:
            ctx_lines.append(f"- Sex: {patient_context['sex']}")
        if "symptoms" in patient_context:
            symptoms_str = ", ".join(patient_context["symptoms"])
            ctx_lines.append(f"- Presenting symptoms: {symptoms_str}")
        if "history" in patient_context:
            ctx_lines.append(f"- Relevant history: {patient_context['history']}")
        if "ethnicity" in patient_context:
            ctx_lines.append(f"- Ethnicity: {patient_context['ethnicity']}")
        patient_section = "\n".join(ctx_lines)
    else:
        patient_section = "No additional patient context provided."

    return _SYSTEM_PROMPT_TEMPLATE.format(
        total_cells=cell_counts.get("total_cells", 0),
        normal_count=cell_counts.get("normal_count", 0),
        sickle_count=cell_counts.get("sickle_count", 0),
        sickle_pct=cell_counts.get("sickle_percentage", 0.0),
        screening_result=cell_counts.get("screening_result", "UNKNOWN"),
        scenario_code=rule_based_report.get("scenario_code", "UNKNOWN"),
        primary_diagnosis=rule_based_report.get("primary_diagnosis", "Unknown"),
        severity=rule_based_report.get("severity", "unknown"),
        patient_context_section=patient_section,
    )


def _parse_ai_response(raw_text: str) -> dict[str, Any]:
    """Parse the AI response text into a Python dict."""
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()
    return json.loads(text)


def _call_gemini_sync(prompt: str) -> dict[str, Any]:
    """Synchronous Gemini API call using the existing GeminiProvider."""
    from app.providers.gemini_provider import GeminiProvider

    provider = GeminiProvider()
    return provider.chat(
        user_message="Analyze the hematology findings described in the system instructions and return your enhanced clinical analysis as JSON.",
        system_instruction=prompt,
    )


# ────────────────────────────────────────────────────────────────────
# Main AI enhancement function
# ────────────────────────────────────────────────────────────────────

_AI_TIMEOUT_SECONDS = 10.0
_MAX_RETRIES = 2


async def enhance_report_with_ai(
    cell_counts: dict[str, Any],
    rule_based_report: dict[str, Any],
    patient_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Enhance a rule-based clinical report with AI-generated insights.

    Parameters
    ----------
    cell_counts : dict
        Detection result summary with total_cells, sickle_count, etc.
    rule_based_report : dict
        Output from ``generate_clinical_report()``.
    patient_context : dict | None
        Optional patient info.

    Returns
    -------
    dict
        Combined report with rule_based, ai_enhanced, combined flag.
    """
    prompt = _build_prompt(cell_counts, rule_based_report, patient_context)
    timestamp = datetime.now(timezone.utc).isoformat()
    last_error: str = ""

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            logger.info(
                "Gemini AI enhancement attempt %d/%d for scenario %s",
                attempt, _MAX_RETRIES,
                rule_based_report.get("scenario_code", "UNKNOWN"),
            )

            raw_result = await asyncio.wait_for(
                asyncio.to_thread(_call_gemini_sync, prompt),
                timeout=_AI_TIMEOUT_SECONDS,
            )

            reply_text = raw_result.get("reply", "")
            tokens_used = raw_result.get("tokens_used")

            if not reply_text or reply_text.startswith("Gemini"):
                last_error = f"Gemini returned error: {reply_text}"
                logger.warning("Attempt %d: %s", attempt, last_error)
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(1.0)
                continue

            ai_data = _parse_ai_response(reply_text)

            logger.info(
                "AI enhancement succeeded (attempt %d, %s tokens)",
                attempt, tokens_used or "unknown",
            )

            return {
                "rule_based": rule_based_report,
                "ai_enhanced": ai_data,
                "combined": True,
                "ai_model": "gemini-2.0-flash",
                "ai_tokens_used": tokens_used,
                "timestamp": timestamp,
            }

        except asyncio.TimeoutError:
            last_error = f"Gemini API timed out after {_AI_TIMEOUT_SECONDS}s"
            logger.warning("Attempt %d: %s", attempt, last_error)

        except json.JSONDecodeError as exc:
            last_error = f"Failed to parse AI response as JSON: {exc}"
            logger.warning("Attempt %d: %s", attempt, last_error)

        except Exception as exc:
            last_error = f"Unexpected error during AI enhancement: {exc}"
            logger.error("Attempt %d: %s", attempt, last_error, exc_info=True)

        if attempt < _MAX_RETRIES:
            await asyncio.sleep(1.0)

    logger.error(
        "AI enhancement failed after %d attempts. Last error: %s",
        _MAX_RETRIES, last_error,
    )
    return {
        "rule_based": rule_based_report,
        "ai_enhanced": None,
        "combined": False,
        "ai_error": last_error,
        "timestamp": timestamp,
    }


# ────────────────────────────────────────────────────────────────────
# Orchestrator: full pipeline
# ────────────────────────────────────────────────────────────────────

async def generate_full_clinical_report(
    cell_counts: dict[str, Any],
    detections: list[dict[str, Any]] | None = None,
    patient_context: dict[str, Any] | None = None,
    use_ai: bool = True,
) -> dict[str, Any]:
    """
    Full clinical reasoning pipeline: rule-based + optional AI.

    Parameters
    ----------
    cell_counts : dict
        Detection summary (total_cells, sickle_count, sickle_percentage, etc.).
    detections : list[dict] | None
        Optional individual cell detections.
    patient_context : dict | None
        Optional patient demographics.
    use_ai : bool
        If True, enhance with Gemini. If False, return rule-based only.

    Returns
    -------
    dict
        Combined clinical report.
    """
    from app.services.hematology_clinical_reasoning import generate_clinical_report

    logger.info(
        "Generating full hematology clinical report (counts=%s, ai=%s)",
        cell_counts, use_ai,
    )

    # Step 1: Rule-based analysis (always runs)
    rule_based = generate_clinical_report(cell_counts, detections)

    # Step 2: AI enhancement (optional)
    if not use_ai:
        return {
            "rule_based": rule_based,
            "ai_enhanced": None,
            "combined": False,
            "ai_skipped": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    result = await enhance_report_with_ai(
        cell_counts, rule_based, patient_context,
    )
    return result
