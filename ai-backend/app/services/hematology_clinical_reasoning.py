"""
LabMind AI — Hematology Clinical Reasoning Engine
==================================================

Rule-based clinical reasoning module that analyzes sickle cell detection
results and generates comprehensive diagnostic reports.

This module is **pure Python** — no external API calls, no ML models.
It encodes established hematology clinical guidelines into a
deterministic decision engine.

Scenarios
---------
1. NORMAL_SCREENING      – No sickle morphology / < 1% sickle
2. BORDERLINE            – 1-5% sickle (artifact or very mild trait)
3. SICKLE_TRAIT_SUSPECTED – 5-20% sickle (HbAS likely)
4. SICKLE_DISEASE_SUSPECTED – 20-50% sickle (HbSS/compound)
5. SICKLE_CRISIS_SUSPECTED – >50% sickle (active crisis)

Clinical References
-------------------
- Ware RE et al. Sickle cell disease. Lancet, 2017.
- NHLBI Evidence-Based Management of SCD, 2014.
- ASH Clinical Practice Guidelines on SCD, 2020.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("labmind.hematology_reasoning")


# ────────────────────────────────────────────────────────────────────
# Severity colour mapping (for frontend UI badges)
# ────────────────────────────────────────────────────────────────────

_SEVERITY_COLORS: dict[str, str] = {
    "normal":   "#22c55e",   # Green-500
    "mild":     "#84cc16",   # Lime-500
    "moderate": "#f59e0b",   # Amber-500
    "abnormal": "#f97316",   # Orange-500
    "critical": "#ef4444",   # Red-500
}


def get_severity_color(severity: str) -> str:
    """Return a hex colour string for a given severity level."""
    return _SEVERITY_COLORS.get(severity, "#6b7280")


# ────────────────────────────────────────────────────────────────────
# Scenario builders
# ────────────────────────────────────────────────────────────────────

def _scenario_normal(
    sickle_count: int,
    total_cells: int,
    sickle_pct: float,
) -> dict[str, Any]:
    """SCENARIO 1 — Normal screening result."""
    return {
        "scenario_code": "NORMAL_SCREENING",
        "severity": "normal",
        "primary_diagnosis": "Normal Blood Smear Morphology",
        "differential_diagnosis": [
            {
                "condition": "Normal hemoglobin profile",
                "likelihood": "most_likely",
                "reasoning": "No sickle morphology detected; RBC shape appears normal.",
            },
        ],
        "ruled_out": [
            "Sickle cell disease (HbSS)",
            "Sickle cell trait with significant sickling",
            "Active vaso-occlusive crisis",
        ],
        "recommended_investigations": [
            {
                "test": "No further testing required for sickle cell if clinically well",
                "priority": "routine",
            },
            {
                "test": "Consider hemoglobin electrophoresis if clinical suspicion remains",
                "priority": "conditional",
            },
        ],
        "red_flags": [],
        "treatment": [],
        "educational_note": (
            "A negative peripheral blood smear screening does not completely "
            "rule out sickle cell trait (HbAS), as trait carriers typically "
            "have normal-appearing RBCs under normal oxygen conditions. "
            "Hemoglobin electrophoresis or HPLC is the gold standard for "
            "definitive diagnosis of hemoglobinopathies."
        ),
        "summary_for_clinician": (
            f"Normal morphology screening. {total_cells} cells analyzed, "
            f"{sickle_count} sickle-like cells ({sickle_pct:.1f}%). "
            "No evidence of significant sickling. Consider hemoglobin "
            "electrophoresis only if clinical suspicion persists."
        ),
    }


def _scenario_borderline(
    sickle_count: int,
    total_cells: int,
    sickle_pct: float,
) -> dict[str, Any]:
    """SCENARIO 2 — Borderline result (1-5%)."""
    return {
        "scenario_code": "BORDERLINE",
        "severity": "mild",
        "primary_diagnosis": "Borderline Sickle Morphology — Likely Artifact",
        "differential_diagnosis": [
            {
                "condition": "Processing artifact or crenation",
                "likelihood": "most_likely",
                "reasoning": "Very low sickle percentage often represents drying or processing artifacts.",
            },
            {
                "condition": "Sickle cell trait (HbAS) — mild expression",
                "likelihood": "possible",
                "reasoning": "Rare sickling may occur in trait carriers under stress or dehydration.",
            },
            {
                "condition": "HbSC disease — mild phenotype",
                "likelihood": "rare_but_important",
                "reasoning": "Compound heterozygotes may show minimal sickling on routine smear.",
            },
        ],
        "ruled_out": [
            "Active sickle crisis",
            "Homozygous sickle cell disease (HbSS) with high sickling",
        ],
        "recommended_investigations": [
            {
                "test": "Repeat peripheral blood smear with fresh sample",
                "priority": "high",
            },
            {
                "test": "Hemoglobin electrophoresis",
                "priority": "high",
            },
            {
                "test": "CBC with differential and reticulocyte count",
                "priority": "medium",
            },
            {
                "test": "Solubility test (Sickledex)",
                "priority": "medium",
            },
        ],
        "red_flags": [
            "Any unexplained pain crisis episodes",
            "Family history of sickle cell disease",
            "History of splenic sequestration",
        ],
        "treatment": [
            "No treatment indicated at this stage",
            "Genetic counseling referral if confirmed trait carrier",
        ],
        "educational_note": (
            "Borderline sickle morphology (1-5%) is frequently caused by "
            "slide preparation artifacts (crenated cells, echinocytes) "
            "rather than true sickling. Acanthocytes and poikilocytes can "
            "mimic sickle shape. Fresh sample preparation and confirmatory "
            "testing are essential before any clinical conclusion."
        ),
        "summary_for_clinician": (
            f"Borderline sickle morphology. {sickle_count} sickle-like cells "
            f"out of {total_cells} ({sickle_pct:.1f}%). Likely artifact but "
            "cannot rule out mild trait expression. Recommend fresh smear "
            "and hemoglobin electrophoresis for confirmation."
        ),
    }


def _scenario_sickle_trait(
    sickle_count: int,
    total_cells: int,
    sickle_pct: float,
) -> dict[str, Any]:
    """SCENARIO 3 — Sickle cell trait suspected (5-20%)."""
    return {
        "scenario_code": "SICKLE_TRAIT_SUSPECTED",
        "severity": "moderate",
        "primary_diagnosis": "Sickle Cell Trait Suspected (HbAS)",
        "differential_diagnosis": [
            {
                "condition": "Sickle cell trait (HbAS)",
                "likelihood": "most_likely",
                "reasoning": (
                    f"Moderate sickle percentage ({sickle_pct:.1f}%) is consistent "
                    "with heterozygous carrier state."
                ),
            },
            {
                "condition": "HbSC disease",
                "likelihood": "possible",
                "reasoning": "Compound heterozygote HbSC can present with moderate sickling.",
            },
            {
                "condition": "HbS-beta thalassemia",
                "likelihood": "possible",
                "reasoning": "Beta-thalassemia coinheritance may show moderate sickle morphology.",
            },
            {
                "condition": "Other hemoglobinopathy (HbSD, HbSE, HbSO-Arab)",
                "likelihood": "rare_but_important",
                "reasoning": "Rare compound heterozygotes can present similarly.",
            },
        ],
        "ruled_out": [
            "Normal hemoglobin profile (HbAA)",
        ],
        "recommended_investigations": [
            {
                "test": "Hemoglobin electrophoresis (GOLD STANDARD)",
                "priority": "high",
            },
            {
                "test": "HPLC (High-Performance Liquid Chromatography)",
                "priority": "high",
            },
            {
                "test": "CBC with differential and reticulocyte count",
                "priority": "high",
            },
            {
                "test": "Peripheral blood smear review by hematologist",
                "priority": "high",
            },
            {
                "test": "Solubility test (Sickledex)",
                "priority": "medium",
            },
            {
                "test": "Iron studies (rule out concurrent iron deficiency)",
                "priority": "medium",
            },
        ],
        "red_flags": [
            "Unexplained splenic infarction (trait complications at altitude/dehydration)",
            "Exertional rhabdomyolysis",
            "Hematuria (renal medullary complications of trait)",
            "Family planning — partner screening recommended",
        ],
        "treatment": [
            "No treatment for sickle trait; usually benign carrier state",
            "Genetic counseling strongly recommended",
            "Avoidance of extreme dehydration and high altitude without acclimatization",
            "Pre-surgical notification to anesthesiologist",
        ],
        "educational_note": (
            "Sickle cell trait (HbAS) affects approximately 8% of African "
            "Americans and is generally benign. However, it is not entirely "
            "without risk — rare complications include splenic infarction at "
            "high altitude, exertional rhabdomyolysis, hematuria from renal "
            "papillary necrosis, and exercise-related sudden death. Peripheral "
            "smear showing 5-20% sickle cells suggests heterozygous state, "
            "but electrophoresis showing ~35-45% HbS with >50% HbA confirms."
        ),
        "summary_for_clinician": (
            f"Sickle cell trait suspected. {sickle_count} sickle cells "
            f"of {total_cells} analyzed ({sickle_pct:.1f}%). Pattern "
            "consistent with heterozygous HbAS carrier. Hemoglobin "
            "electrophoresis required for confirmation. Genetic counseling "
            "recommended."
        ),
    }


def _scenario_sickle_disease(
    sickle_count: int,
    total_cells: int,
    sickle_pct: float,
) -> dict[str, Any]:
    """SCENARIO 4 — Sickle cell disease suspected (20-50%)."""
    return {
        "scenario_code": "SICKLE_DISEASE_SUSPECTED",
        "severity": "abnormal",
        "primary_diagnosis": "Sickle Cell Disease Suspected (HbSS/Compound Heterozygote)",
        "differential_diagnosis": [
            {
                "condition": "Homozygous sickle cell disease (HbSS)",
                "likelihood": "most_likely",
                "reasoning": (
                    f"High sickle percentage ({sickle_pct:.1f}%) with {sickle_count} "
                    "sickle cells strongly suggests HbSS disease."
                ),
            },
            {
                "condition": "HbSC disease",
                "likelihood": "possible",
                "reasoning": "Compound heterozygote with significant clinical manifestations.",
            },
            {
                "condition": "HbS-beta-zero thalassemia",
                "likelihood": "possible",
                "reasoning": "Clinically indistinguishable from HbSS without electrophoresis.",
            },
            {
                "condition": "HbS-beta-plus thalassemia",
                "likelihood": "possible",
                "reasoning": "Milder variant but can show significant sickling.",
            },
        ],
        "ruled_out": [
            "Normal hemoglobin profile (HbAA)",
            "Simple sickle cell trait without disease",
        ],
        "recommended_investigations": [
            {
                "test": "URGENT: Hemoglobin electrophoresis",
                "priority": "high",
            },
            {
                "test": "HPLC for hemoglobin quantification",
                "priority": "high",
            },
            {
                "test": "CBC with differential, reticulocyte count",
                "priority": "high",
            },
            {
                "test": "Peripheral blood smear — manual review by hematologist",
                "priority": "high",
            },
            {
                "test": "LDH, bilirubin, haptoglobin (hemolysis markers)",
                "priority": "high",
            },
            {
                "test": "Renal function tests and urinalysis",
                "priority": "medium",
            },
            {
                "test": "Transcranial Doppler ultrasound (stroke risk, if pediatric)",
                "priority": "conditional",
            },
            {
                "test": "Genetic testing for HBB gene mutations",
                "priority": "conditional",
            },
        ],
        "red_flags": [
            "Acute chest syndrome (chest pain, fever, new infiltrate)",
            "Severe pain crisis not responding to standard analgesia",
            "Stroke symptoms (weakness, speech difficulty, confusion)",
            "Priapism lasting > 4 hours",
            "Acute splenic sequestration (rapid splenic enlargement, dropping Hb)",
            "Aplastic crisis (reticulocyte count drop, worsening anemia)",
        ],
        "treatment": [
            "Refer to hematology for disease management plan",
            "Hydroxyurea therapy consideration (increases HbF)",
            "Folic acid supplementation (1mg daily)",
            "Pneumococcal vaccination and penicillin prophylaxis",
            "Pain management protocol for vaso-occlusive crises",
            "Transfusion therapy for severe anemia or stroke prevention",
            "Consider L-glutamine for crisis reduction",
        ],
        "educational_note": (
            "Sickle cell disease (HbSS) is characterized by chronic "
            "hemolytic anemia, vaso-occlusive crises, and progressive organ "
            "damage. The sickle-shaped RBCs result from polymerization of "
            "deoxygenated HbS, causing rigidity and membrane damage. On "
            "peripheral smear, classic irreversibly sickled cells (ISCs) "
            "have pointed ends, while reversibly sickled cells show "
            "variable distortion. Target cells, Howell-Jolly bodies, and "
            "nucleated RBCs may also be present."
        ),
        "summary_for_clinician": (
            f"Sickle cell disease suspected. {sickle_count} sickle cells "
            f"of {total_cells} analyzed ({sickle_pct:.1f}%). High sickle "
            "burden consistent with HbSS or compound heterozygote. "
            "URGENT hemoglobin electrophoresis and hematology referral "
            "recommended. Assess for organ damage and crisis risk."
        ),
    }


def _scenario_sickle_crisis(
    sickle_count: int,
    total_cells: int,
    sickle_pct: float,
) -> dict[str, Any]:
    """SCENARIO 5 — Sickle crisis suspected (>50%)."""
    return {
        "scenario_code": "SICKLE_CRISIS_SUSPECTED",
        "severity": "critical",
        "primary_diagnosis": "Active Sickling Crisis Suspected",
        "differential_diagnosis": [
            {
                "condition": "Vaso-occlusive crisis (acute)",
                "likelihood": "most_likely",
                "reasoning": (
                    f"Extremely high sickle percentage ({sickle_pct:.1f}%) with "
                    f"{sickle_count} sickle cells indicates massive RBC sickling."
                ),
            },
            {
                "condition": "Acute chest syndrome",
                "likelihood": "possible",
                "reasoning": "High sickling burden is a risk factor for ACS.",
            },
            {
                "condition": "Splenic sequestration crisis",
                "likelihood": "possible",
                "reasoning": "Massive sickling can trigger splenic trapping.",
            },
            {
                "condition": "Aplastic crisis (parvovirus B19)",
                "likelihood": "rare_but_important",
                "reasoning": "Preceded by reticulocyte drop with worsening anemia.",
            },
        ],
        "ruled_out": [
            "Normal hemoglobin profile",
            "Sickle cell trait without crisis",
        ],
        "recommended_investigations": [
            {
                "test": "STAT: CBC, reticulocyte count, type and crossmatch",
                "priority": "high",
            },
            {
                "test": "STAT: LDH, bilirubin, haptoglobin",
                "priority": "high",
            },
            {
                "test": "Blood gas analysis (assess oxygenation)",
                "priority": "high",
            },
            {
                "test": "Chest X-ray (rule out acute chest syndrome)",
                "priority": "high",
            },
            {
                "test": "Blood cultures if febrile",
                "priority": "high",
            },
            {
                "test": "Renal and hepatic function panel",
                "priority": "high",
            },
            {
                "test": "Hemoglobin electrophoresis (if not already confirmed)",
                "priority": "medium",
            },
            {
                "test": "CT head if neurological symptoms",
                "priority": "conditional",
            },
        ],
        "red_flags": [
            "CRITICAL: Oxygen saturation < 95% — immediate supplemental O2",
            "CRITICAL: Hemoglobin < 6 g/dL — consider emergency transfusion",
            "Fever > 38.5°C — presume infection, broad-spectrum antibiotics",
            "Neurological deficit — STAT CT/MRI, suspect stroke",
            "Priapism > 4 hours — urological emergency",
            "Severe abdominal pain with splenic enlargement — sequestration crisis",
            "Respiratory distress — suspect acute chest syndrome, STAT CXR",
        ],
        "treatment": [
            "IMMEDIATE: IV fluid hydration (avoid overhydration)",
            "IMMEDIATE: Supplemental oxygen to maintain SpO2 > 95%",
            "Aggressive pain management (IV opioids per protocol, avoid meperidine)",
            "Exchange transfusion for severe crisis, ACS, or stroke",
            "Simple transfusion if Hb critically low",
            "Empiric antibiotics if febrile (ceftriaxone + azithromycin)",
            "Incentive spirometry to prevent ACS",
            "Hematology STAT consultation",
        ],
        "educational_note": (
            "A sickle percentage >50% on peripheral smear represents "
            "massive intravascular sickling and is a hematological emergency. "
            "This degree of sickling causes widespread vaso-occlusion, "
            "leading to tissue ischemia and organ damage. The red cell "
            "membrane becomes permanently damaged, leading to chronic "
            "hemolysis. Irreversibly sickled cells (ISCs) persist even "
            "when reoxygenated. Management priorities are hydration, "
            "oxygenation, pain control, and consideration of exchange "
            "transfusion to rapidly reduce HbS levels below 30%."
        ),
        "summary_for_clinician": (
            f"CRITICAL: Active sickling crisis suspected. {sickle_count} "
            f"sickle cells of {total_cells} analyzed ({sickle_pct:.1f}%). "
            "Massive RBC sickling detected. Immediate clinical assessment "
            "required. Initiate IV hydration, supplemental O2, pain control. "
            "Consider exchange transfusion. STAT hematology consultation."
        ),
    }


# ────────────────────────────────────────────────────────────────────
# Main entry point
# ────────────────────────────────────────────────────────────────────

def generate_clinical_report(
    cell_counts: dict[str, Any],
    detections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Generate a comprehensive clinical reasoning report from hematology
    sickle cell detection results.

    Parameters
    ----------
    cell_counts : dict
        Detection result summary. Expected keys:
        - ``total_cells`` (int): total cells detected
        - ``sickle_count`` (int): cells classified as sickle
        - ``normal_count`` (int): cells classified as normal RBC
        - ``sickle_percentage`` (float): sickle / total RBC * 100
        - ``screening_result`` (str): NEGATIVE, REVIEW, SICKLE_SCREEN_POSITIVE
    detections : list[dict] | None
        Optional list of individual cell detection objects. Reserved
        for future morphology-level reasoning.

    Returns
    -------
    dict[str, Any]
        Comprehensive clinical report dictionary.

    Examples
    --------
    >>> report = generate_clinical_report({
    ...     "total_cells": 150, "sickle_count": 12,
    ...     "normal_count": 138, "sickle_percentage": 8.0,
    ...     "screening_result": "SICKLE_SCREEN_POSITIVE"
    ... })
    >>> report["scenario_code"]
    'SICKLE_TRAIT_SUSPECTED'
    """
    total_cells = cell_counts.get("total_cells", 0)
    sickle_count = cell_counts.get("sickle_count", 0)
    normal_count = cell_counts.get("normal_count", 0)
    sickle_pct = cell_counts.get("sickle_percentage", 0.0)
    screening = cell_counts.get("screening_result", "NEGATIVE")

    # ── Scenario classification (by sickle percentage) ──

    if sickle_pct > 50:
        scenario = "SICKLE_CRISIS_SUSPECTED"
        report = _scenario_sickle_crisis(sickle_count, total_cells, sickle_pct)

    elif sickle_pct >= 20:
        scenario = "SICKLE_DISEASE_SUSPECTED"
        report = _scenario_sickle_disease(sickle_count, total_cells, sickle_pct)

    elif sickle_pct >= 5:
        scenario = "SICKLE_TRAIT_SUSPECTED"
        report = _scenario_sickle_trait(sickle_count, total_cells, sickle_pct)

    elif sickle_pct >= 1:
        scenario = "BORDERLINE"
        report = _scenario_borderline(sickle_count, total_cells, sickle_pct)

    else:
        scenario = "NORMAL_SCREENING"
        report = _scenario_normal(sickle_count, total_cells, sickle_pct)

    logger.info(
        "Hematology reasoning matched scenario: %s  "
        "(sickle=%d, total=%d, pct=%.1f%%)",
        scenario, sickle_count, total_cells, sickle_pct,
    )

    # Attach input data for traceability
    report["input_cell_counts"] = {
        "total_cells": total_cells,
        "sickle_count": sickle_count,
        "normal_count": normal_count,
        "sickle_percentage": round(sickle_pct, 2),
        "screening_result": screening,
    }
    report["severity_color"] = get_severity_color(report["severity"])

    return report


# ────────────────────────────────────────────────────────────────────
# Self-test block
# ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
    )

    test_cases: list[tuple[str, dict[str, Any]]] = [
        ("NORMAL_SCREENING",          {"total_cells": 200, "sickle_count": 0,  "normal_count": 200, "sickle_percentage": 0.0,  "screening_result": "NEGATIVE"}),
        ("BORDERLINE",                {"total_cells": 180, "sickle_count": 4,  "normal_count": 176, "sickle_percentage": 2.2,  "screening_result": "REVIEW"}),
        ("SICKLE_TRAIT_SUSPECTED",    {"total_cells": 150, "sickle_count": 12, "normal_count": 138, "sickle_percentage": 8.0,  "screening_result": "SICKLE_SCREEN_POSITIVE"}),
        ("SICKLE_DISEASE_SUSPECTED",  {"total_cells": 120, "sickle_count": 36, "normal_count": 84,  "sickle_percentage": 30.0, "screening_result": "SICKLE_SCREEN_POSITIVE"}),
        ("SICKLE_CRISIS_SUSPECTED",   {"total_cells": 100, "sickle_count": 60, "normal_count": 40,  "sickle_percentage": 60.0, "screening_result": "SICKLE_SCREEN_POSITIVE"}),
    ]

    all_passed = True
    print("=" * 72)
    print("  HEMATOLOGY CLINICAL REASONING ENGINE -- SELF-TEST")
    print("=" * 72)

    for expected_scenario, counts in test_cases:
        report = generate_clinical_report(counts)
        matched = report["scenario_code"]
        status = "[PASS]" if matched == expected_scenario else "[FAIL]"
        if matched != expected_scenario:
            all_passed = False

        print(f"\n{status}  Input: sickle_pct={counts['sickle_percentage']}%")
        print(f"  Expected : {expected_scenario}")
        print(f"  Matched  : {matched}")
        print(f"  Severity : {report['severity']}  ({report['severity_color']})")
        print(f"  Diagnosis: {report['primary_diagnosis']}")
        print(f"  Diff-Dx  : {len(report['differential_diagnosis'])} conditions")
        print(f"  Ruled Out: {len(report['ruled_out'])} conditions")
        print(f"  Tests    : {len(report['recommended_investigations'])} recommended")
        print(f"  Red Flags: {len(report['red_flags'])} flags")
        print(f"  Clinician: {report['summary_for_clinician'][:100]}...")

    print("\n" + "=" * 72)
    if all_passed:
        print("  ALL 5 SCENARIOS PASSED")
    else:
        print("  SOME SCENARIOS FAILED -- check output above")
    print("=" * 72)
