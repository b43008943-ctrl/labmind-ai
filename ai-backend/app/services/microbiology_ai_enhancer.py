"""
LabMind AI -- Microbiology AI Enhancement Module
=================================================

Enhances the rule-based clinical reasoning report with AI-generated
insights using Google Gemini 2.0 Flash.

Architecture mirrors parasitology_ai_enhancer.py:
1. Rule-based engine provides deterministic clinical report
2. This module feeds that report into Gemini for deeper insights
3. Orchestrator combines both into a single response
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("labmind.microbiology_ai_enhancer")

_SYSTEM_PROMPT_TEMPLATE = """\
You are a senior clinical microbiologist and medical educator at a teaching hospital.
A Gram-stained microscopy specimen was examined with the following findings:

BACTERIA DETECTED:
{bacteria_section}

TOTAL ORGANISMS: {total_bacteria}

GRAM SUMMARY:
{gram_summary_section}

Our rule-based system classified this as: {scenario_code}
Primary diagnosis: {primary_diagnosis}
Overall severity: {severity}

{patient_context_section}

Provide an enhanced clinical analysis in STRICT JSON format with these fields:

{{
  "pathophysiology": "2-3 sentences explaining the pathogenic mechanism of the detected bacteria",
  "clinical_correlation": [
    "Point 1: specific clinical question to ask (recent hospitalization, catheter, travel)",
    "Point 2: physical exam finding to look for",
    "Point 3: specific lab correlation (WBC, CRP, procalcitonin)"
  ],
  "rare_considerations": [
    {{
      "condition": "Name of rare complication or differential",
      "why_consider": "Brief reason based on detected morphotype",
      "clinical_clue": "What would suggest this"
    }}
  ],
  "teaching_pearls": [
    "Insight 1 about Gram stain interpretation and bacterial morphology",
    "Insight 2 about antimicrobial resistance patterns",
    "Insight 3 about empiric therapy and de-escalation principles"
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
    bacteria_counts: dict[str, int],
    rule_based_report: dict[str, Any],
    patient_context: dict[str, Any] | None = None,
) -> str:
    """Build the Gemini system prompt from detection data and scenario."""
    if bacteria_counts:
        _FRIENDLY = {
            "G-_Bacillus": "Gram-negative bacilli", "G+_Coccus": "Gram-positive cocci",
            "G-_Coccus": "Gram-negative cocci", "G+_Bacillus": "Gram-positive bacilli",
        }
        lines = [f"- {_FRIENDLY.get(k, k)}: {v} organism(s)" for k, v in bacteria_counts.items() if v > 0]
        bacteria_section = "\n".join(lines)
    else:
        bacteria_section = "- None detected (NEGATIVE result)"

    # Gram summary
    gram_data = rule_based_report.get("gram_summary", {})
    if gram_data:
        gram_lines = [f"- Gram-positive: {gram_data.get('gram_positive', 0)}", f"- Gram-negative: {gram_data.get('gram_negative', 0)}", f"- Cocci: {gram_data.get('cocci', 0)}", f"- Bacilli: {gram_data.get('bacilli', 0)}"]
        gram_summary_section = "\n".join(gram_lines)
    else:
        gram_summary_section = "- No summary available"

    if patient_context:
        ctx_lines = ["PATIENT CONTEXT:"]
        for key in ("age", "sex", "symptoms", "history", "specimen_source"):
            if key in patient_context:
                val = patient_context[key]
                if isinstance(val, list):
                    val = ", ".join(val)
                ctx_lines.append(f"- {key.replace('_', ' ').title()}: {val}")
        patient_section = "\n".join(ctx_lines)
    else:
        patient_section = "No additional patient context provided."

    total = sum(bacteria_counts.values()) if bacteria_counts else 0

    return _SYSTEM_PROMPT_TEMPLATE.format(
        bacteria_section=bacteria_section,
        total_bacteria=total,
        gram_summary_section=gram_summary_section,
        scenario_code=rule_based_report.get("scenario_code", "UNKNOWN"),
        primary_diagnosis=rule_based_report.get("primary_diagnosis", "Unknown"),
        severity=rule_based_report.get("severity", "unknown"),
        patient_context_section=patient_section,
    )


def _parse_ai_response(raw_text: str) -> dict[str, Any]:
    """Parse AI response text into Python dict."""
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return json.loads(text.strip())


def _call_gemini_sync(prompt: str) -> dict[str, Any]:
    """Synchronous Gemini API call via existing GeminiProvider."""
    from app.providers.gemini_provider import GeminiProvider
    provider = GeminiProvider()
    return provider.chat(
        user_message="Analyze the microbiology Gram stain findings described in the system instructions and return your enhanced clinical analysis as JSON.",
        system_instruction=prompt,
    )


_AI_TIMEOUT_SECONDS = 10.0
_MAX_RETRIES = 2


async def enhance_report_with_ai(
    bacteria_counts: dict[str, int],
    rule_based_report: dict[str, Any],
    patient_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Enhance rule-based report with Gemini AI insights."""
    prompt = _build_prompt(bacteria_counts, rule_based_report, patient_context)
    timestamp = datetime.now(timezone.utc).isoformat()
    last_error = ""

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            logger.info("Gemini AI enhancement attempt %d/%d for scenario %s", attempt, _MAX_RETRIES, rule_based_report.get("scenario_code", "UNKNOWN"))
            raw_result = await asyncio.wait_for(asyncio.to_thread(_call_gemini_sync, prompt), timeout=_AI_TIMEOUT_SECONDS)
            reply_text = raw_result.get("reply", "")
            tokens_used = raw_result.get("tokens_used")

            if not reply_text or reply_text.startswith("Gemini"):
                last_error = f"Gemini returned error: {reply_text}"
                logger.warning("Attempt %d: %s", attempt, last_error)
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(1.0)
                continue

            ai_data = _parse_ai_response(reply_text)
            logger.info("AI enhancement succeeded (attempt %d, %s tokens)", attempt, tokens_used or "unknown")
            return {
                "rule_based": rule_based_report, "ai_enhanced": ai_data,
                "combined": True, "ai_model": "gemini-2.0-flash",
                "ai_tokens_used": tokens_used, "timestamp": timestamp,
            }
        except asyncio.TimeoutError:
            last_error = f"Gemini API timed out after {_AI_TIMEOUT_SECONDS}s"
            logger.warning("Attempt %d: %s", attempt, last_error)
        except json.JSONDecodeError as exc:
            last_error = f"Failed to parse AI response as JSON: {exc}"
            logger.warning("Attempt %d: %s", attempt, last_error)
        except Exception as exc:
            last_error = f"Unexpected error: {exc}"
            logger.error("Attempt %d: %s", attempt, last_error, exc_info=True)

        if attempt < _MAX_RETRIES:
            await asyncio.sleep(1.0)

    logger.error("AI enhancement failed after %d attempts. Last error: %s", _MAX_RETRIES, last_error)
    return {"rule_based": rule_based_report, "ai_enhanced": None, "combined": False, "ai_error": last_error, "timestamp": timestamp}


async def generate_full_clinical_report(
    bacteria_counts: dict[str, int],
    bacteria_info: list[dict[str, Any]] | None = None,
    patient_context: dict[str, Any] | None = None,
    use_ai: bool = True,
) -> dict[str, Any]:
    """Full clinical reasoning pipeline: rule-based + optional AI enhancement."""
    from app.services.microbiology_clinical_reasoning import generate_clinical_report

    logger.info("Generating full microbiology clinical report (counts=%s, ai=%s)", bacteria_counts, use_ai)
    rule_based = generate_clinical_report(bacteria_counts, bacteria_info)

    if not use_ai:
        return {
            "rule_based": rule_based, "ai_enhanced": None, "combined": False,
            "ai_skipped": True, "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return await enhance_report_with_ai(bacteria_counts, rule_based, patient_context)


# ────────────────────────────────────────────────────────────────────
# Self-test
# ────────────────────────────────────────────────────────────────────

async def _run_tests() -> None:
    """Run self-tests for the AI enhancement pipeline."""
    import os
    separator = "=" * 72

    print(separator)
    print("  MICROBIOLOGY AI ENHANCER -- SELF-TEST")
    print(separator)

    print("\n[TEST 1] Rule-based only (use_ai=False)")
    print("-" * 40)
    result_1 = await generate_full_clinical_report({"G+_Coccus": 10}, use_ai=False)
    assert result_1["ai_enhanced"] is None
    assert result_1["ai_skipped"] is True
    print(f"  Scenario   : {result_1['rule_based']['scenario_code']}")
    print(f"  Diagnosis  : {result_1['rule_based']['primary_diagnosis']}")
    print("  [PASS] Rule-based only works correctly")

    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    if not has_key:
        try:
            from app.core.config import get_settings
            has_key = bool(get_settings().GEMINI_API_KEY)
        except Exception:
            pass

    if has_key:
        print(f"\n[TEST 2] AI Enhancement (Gemini API key detected)")
        print("-" * 40)
        result_2 = await generate_full_clinical_report({"G+_Coccus": 8, "G-_Bacillus": 3}, use_ai=True)
        print(f"  Scenario   : {result_2['rule_based']['scenario_code']}")
        print(f"  AI combined: {result_2['combined']}")
        if result_2["combined"]:
            ai = result_2["ai_enhanced"]
            print(f"  Confidence : {ai.get('confidence_level', 'N/A')}")
            print("  [PASS] AI enhancement succeeded")
        else:
            print(f"  AI error   : {result_2.get('ai_error', 'Unknown')}")
            print("  [WARN] AI enhancement failed (non-fatal)")
    else:
        print(f"\n[TEST 2] SKIPPED -- No GEMINI_API_KEY found")

    print(f"\n{separator}")
    print("  SELF-TEST COMPLETE")
    print(separator)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(name)s  %(levelname)s  %(message)s")
    asyncio.run(_run_tests())
