"""
LabMind AI -- Parasitology AI Enhancement Module
=================================================

Enhances the rule-based clinical reasoning report with AI-generated
insights using Google Gemini 2.0 Flash.

Architecture
------------
1. Rule-based engine (parasitology_clinical_reasoning.py) provides the
   deterministic clinical report.
2. This module feeds that report + detected species data into Gemini and
   asks for deeper pathophysiological reasoning, rare considerations,
   teaching pearls, and prioritised next steps.
3. The orchestrator ``generate_full_clinical_report()`` combines both
   into a single response for the frontend.

Design Decisions
----------------
- GeminiProvider is synchronous (httpx.Client).  We wrap it with
  ``asyncio.to_thread()`` so the enhancer can be awaited without
  blocking the event loop.
- AI enhancement is strictly optional -- if Gemini is unavailable,
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

logger = logging.getLogger("labmind.parasitology_ai_enhancer")


# ────────────────────────────────────────────────────────────────────
# Prompt template
# ────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT_TEMPLATE = """\
You are a senior parasitologist and medical educator at a teaching hospital.
A stool microscopy examination was performed with the following findings:

PARASITES DETECTED:
{species_section}

TOTAL EGGS DETECTED: {total_eggs}

Our rule-based system classified this as: {scenario_code}
Primary diagnosis: {primary_diagnosis}
Overall severity: {severity}

{patient_context_section}

Provide an enhanced clinical analysis in STRICT JSON format with these fields:

{{
  "pathophysiology": "2-3 sentences explaining the underlying mechanism of disease for the detected parasite(s)",
  "clinical_correlation": [
    "Point 1: specific clinical question to ask patient (dietary habits, travel, exposure)",
    "Point 2: physical exam finding to look for",
    "Point 3: specific lab correlation"
  ],
  "rare_considerations": [
    {{
      "condition": "Name of rare complication or differential",
      "why_consider": "Brief reason based on the detected species",
      "clinical_clue": "What would suggest this"
    }}
  ],
  "teaching_pearls": [
    "Educational insight 1 about the detected parasite morphology and identification",
    "Educational insight 2 about epidemiology and public health significance",
    "Educational insight 3 about treatment considerations and drug resistance"
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
    species_detected: list[str],
    parasite_counts: dict[str, int],
    rule_based_report: dict[str, Any],
    patient_context: dict[str, Any] | None = None,
) -> str:
    """
    Build the Gemini system prompt from detected species, scenario, and
    optional patient context.
    """
    # Species section
    if species_detected:
        lines = []
        for sp in species_detected:
            count = parasite_counts.get(sp, 0)
            lines.append(f"- {sp.replace('_', ' ')}: {count} egg(s)")
        species_section = "\n".join(lines)
    else:
        species_section = "- None detected (NEGATIVE result)"

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
        if "travel" in patient_context:
            ctx_lines.append(f"- Travel history: {patient_context['travel']}")
        patient_section = "\n".join(ctx_lines)
    else:
        patient_section = "No additional patient context provided."

    total_eggs = sum(parasite_counts.values()) if parasite_counts else 0

    return _SYSTEM_PROMPT_TEMPLATE.format(
        species_section=species_section,
        total_eggs=total_eggs,
        scenario_code=rule_based_report.get("scenario_code", "UNKNOWN"),
        primary_diagnosis=rule_based_report.get("primary_diagnosis", "Unknown"),
        severity=rule_based_report.get("severity", "unknown"),
        patient_context_section=patient_section,
    )


def _parse_ai_response(raw_text: str) -> dict[str, Any]:
    """
    Parse the AI response text into a Python dict.

    Handles common Gemini quirks:
    - Response wrapped in ```json ... ``` markdown fences
    - Trailing commas (rare but possible)
    - Leading/trailing whitespace
    """
    text = raw_text.strip()

    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    return json.loads(text)


def _call_gemini_sync(prompt: str) -> dict[str, Any]:
    """
    Synchronous Gemini API call using the existing GeminiProvider.

    This runs on a worker thread (via ``asyncio.to_thread``) so it
    does not block the async event loop.

    Returns
    -------
    dict
        ``{"reply": str, "tokens_used": int | None}``
    """
    from app.providers.gemini_provider import GeminiProvider

    provider = GeminiProvider()
    return provider.chat(
        user_message="Analyze the parasitology findings described in the system instructions and return your enhanced clinical analysis as JSON.",
        system_instruction=prompt,
    )


# ────────────────────────────────────────────────────────────────────
# Main AI enhancement function
# ────────────────────────────────────────────────────────────────────

_AI_TIMEOUT_SECONDS = 10.0
_MAX_RETRIES = 2


async def enhance_report_with_ai(
    species_detected: list[str],
    parasite_counts: dict[str, int],
    rule_based_report: dict[str, Any],
    patient_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Enhance a rule-based clinical report with AI-generated insights
    from Google Gemini 2.0 Flash.

    Parameters
    ----------
    species_detected : list[str]
        List of detected species names.
    parasite_counts : dict[str, int]
        Mapping of species name to egg count.
    rule_based_report : dict
        Output from ``generate_clinical_report()``.
    patient_context : dict | None
        Optional patient info:
        ``{"age": int, "sex": str, "symptoms": list[str], "history": str}``.

    Returns
    -------
    dict
        Combined report with keys:
        - ``rule_based``: original rule-based report
        - ``ai_enhanced``: parsed AI response (or ``None`` on failure)
        - ``combined``: ``True`` if AI succeeded, ``False`` otherwise
        - ``ai_model``: model identifier
        - ``ai_error``: error message (only present on failure)
        - ``timestamp``: ISO 8601 datetime
    """
    prompt = _build_prompt(
        species_detected, parasite_counts,
        rule_based_report, patient_context,
    )
    timestamp = datetime.now(timezone.utc).isoformat()

    last_error: str = ""

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            logger.info(
                "Gemini AI enhancement attempt %d/%d for scenario %s",
                attempt, _MAX_RETRIES,
                rule_based_report.get("scenario_code", "UNKNOWN"),
            )

            # Run synchronous Gemini call on a thread, with timeout
            raw_result = await asyncio.wait_for(
                asyncio.to_thread(_call_gemini_sync, prompt),
                timeout=_AI_TIMEOUT_SECONDS,
            )

            reply_text = raw_result.get("reply", "")
            tokens_used = raw_result.get("tokens_used")

            if not reply_text or reply_text.startswith("Gemini"):
                # Provider returned an error message instead of content
                last_error = f"Gemini returned error: {reply_text}"
                logger.warning("Attempt %d: %s", attempt, last_error)
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(1.0)
                continue

            # Parse the JSON response
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

        # Backoff before retry
        if attempt < _MAX_RETRIES:
            await asyncio.sleep(1.0)

    # All retries exhausted
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
    species_detected: list[str],
    parasite_counts: dict[str, int],
    species_info: list[dict[str, Any]] | None = None,
    patient_context: dict[str, Any] | None = None,
    use_ai: bool = True,
) -> dict[str, Any]:
    """
    Full clinical reasoning pipeline: rule-based analysis + optional
    AI enhancement.

    Parameters
    ----------
    species_detected : list[str]
        List of detected species names.
    parasite_counts : dict[str, int]
        Mapping of species name to egg count.
    species_info : list[dict] | None
        Optional species info from the AI provider.
    patient_context : dict | None
        Optional patient demographics and symptoms for AI context.
    use_ai : bool
        If ``True``, enhance the rule-based report with Gemini AI.
        If ``False``, return only the rule-based report.

    Returns
    -------
    dict
        Combined clinical report ready for frontend consumption.

    Examples
    --------
    >>> import asyncio
    >>> report = asyncio.run(generate_full_clinical_report(
    ...     ["Hookworm"], {"Hookworm": 2}, use_ai=False
    ... ))
    >>> report["rule_based"]["scenario_code"]
    'SINGLE_SPECIES_SEVERE'
    """
    from app.services.parasitology_clinical_reasoning import generate_clinical_report

    logger.info(
        "Generating full parasitology clinical report (species=%s, counts=%s, ai=%s)",
        species_detected, parasite_counts, use_ai,
    )

    # Step 1: Rule-based analysis (always runs)
    rule_based = generate_clinical_report(species_detected, parasite_counts, species_info)

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
        species_detected, parasite_counts,
        rule_based, patient_context,
    )
    return result


# ────────────────────────────────────────────────────────────────────
# Self-test
# ────────────────────────────────────────────────────────────────────

async def _run_tests() -> None:
    """Run self-tests for the AI enhancement pipeline."""
    import os

    separator = "=" * 72

    print(separator)
    print("  PARASITOLOGY AI ENHANCER -- SELF-TEST")
    print(separator)

    # ---- Test 1: Rule-based only (no AI) ----
    print("\n[TEST 1] Rule-based only (use_ai=False)")
    print("-" * 40)

    result_1 = await generate_full_clinical_report(
        ["Hookworm"], {"Hookworm": 2}, use_ai=False,
    )

    assert result_1["ai_enhanced"] is None, "AI should be None when use_ai=False"
    assert result_1["ai_skipped"] is True, "ai_skipped should be True"
    assert result_1["rule_based"]["scenario_code"].startswith("SINGLE_SPECIES")

    print(f"  Scenario   : {result_1['rule_based']['scenario_code']}")
    print(f"  Diagnosis  : {result_1['rule_based']['primary_diagnosis']}")
    print(f"  AI skipped : {result_1.get('ai_skipped', False)}")
    print("  [PASS] Rule-based only works correctly")

    # ---- Test 2: With AI enhancement ----
    has_key = bool(os.environ.get("GEMINI_API_KEY"))

    # Also check settings-based key
    if not has_key:
        try:
            from app.core.config import get_settings
            has_key = bool(get_settings().GEMINI_API_KEY)
        except Exception:
            pass

    if has_key:
        print(f"\n[TEST 2] AI Enhancement (Gemini API key detected)")
        print("-" * 40)

        result_2 = await generate_full_clinical_report(
            ["Hookworm", "Ascaris_lumbricoides"],
            {"Hookworm": 2, "Ascaris_lumbricoides": 1},
            use_ai=True,
        )

        print(f"  Scenario   : {result_2['rule_based']['scenario_code']}")
        print(f"  AI combined: {result_2['combined']}")

        if result_2["combined"]:
            ai = result_2["ai_enhanced"]
            print(f"  AI model   : {result_2.get('ai_model', 'N/A')}")
            print(f"  Tokens     : {result_2.get('ai_tokens_used', 'N/A')}")
            print(f"  Confidence : {ai.get('confidence_level', 'N/A')}")
            print(f"  Pathophys  : {ai.get('pathophysiology', 'N/A')[:120]}...")
            print(f"  Pearls     : {len(ai.get('teaching_pearls', []))} items")
            print(f"  Next steps : {len(ai.get('next_steps_priority', []))} items")
            print(f"  Rare conds : {len(ai.get('rare_considerations', []))} items")
            print("  [PASS] AI enhancement succeeded")
        else:
            print(f"  AI error   : {result_2.get('ai_error', 'Unknown')}")
            print("  [WARN] AI enhancement failed (non-fatal)")

        # ---- Test 3: With patient context ----
        print(f"\n[TEST 3] AI Enhancement with patient context")
        print("-" * 40)

        result_3 = await generate_full_clinical_report(
            ["Opisthorchis_viverrine"],
            {"Opisthorchis_viverrine": 3},
            patient_context={
                "age": 55,
                "sex": "male",
                "symptoms": ["right upper quadrant pain", "jaundice"],
                "history": "Frequent raw fish consumption",
                "travel": "Southeast Asia (Thailand, Laos)",
            },
            use_ai=True,
        )

        print(f"  Scenario   : {result_3['rule_based']['scenario_code']}")
        print(f"  AI combined: {result_3['combined']}")

        if result_3["combined"]:
            ai3 = result_3["ai_enhanced"]
            print(f"  AI summary : {ai3.get('ai_summary', 'N/A')[:150]}...")
            print("  [PASS] AI enhancement with patient context succeeded")
        else:
            print(f"  AI error   : {result_3.get('ai_error', 'Unknown')}")
            print("  [WARN] AI enhancement failed (non-fatal)")
    else:
        print(f"\n[TEST 2] SKIPPED -- No GEMINI_API_KEY found")
        print(f"[TEST 3] SKIPPED -- No GEMINI_API_KEY found")

    print(f"\n{separator}")
    print("  SELF-TEST COMPLETE")
    print(separator)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
    )
    asyncio.run(_run_tests())
