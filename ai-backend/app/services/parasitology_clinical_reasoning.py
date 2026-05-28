"""
LabMind AI — Parasitology Clinical Reasoning Engine
====================================================

Rule-based clinical reasoning module that analyzes detected parasitic
egg species and generates comprehensive diagnostic reports.

This module is **pure Python** — no external API calls, no ML models.
It encodes established parasitology clinical guidelines into a
deterministic decision engine.

Scenarios
---------
1. NEGATIVE               – No parasitic eggs detected
2. SINGLE_SPECIES_MILD    – One species, mild severity
3. SINGLE_SPECIES_MODERATE – One species, moderate severity
4. SINGLE_SPECIES_SEVERE  – One species, severe severity
5. MULTI_SPECIES          – Two or more different species detected
6. HEAVY_INFECTION        – Any species with 5+ eggs in one field

Clinical References
-------------------
- Chula-ParasiteEgg-11 dataset (Chulalongkorn University)
- WHO Guidelines for Soil-Transmitted Helminthiases, 2023.
- Garcia LS. Diagnostic Medical Parasitology, 6th ed.
- Ash LR, Orihel TC. Atlas of Human Parasitology, 5th ed.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("labmind.parasitology_reasoning")


# ────────────────────────────────────────────────────────────────────
# Severity colour mapping (for frontend UI badges)
# ────────────────────────────────────────────────────────────────────

_SEVERITY_COLORS: dict[str, str] = {
    "mild":               "#22c55e",   # Green-500
    "mild_to_moderate":   "#84cc16",   # Lime-500
    "moderate":           "#f59e0b",   # Amber-500
    "moderate_to_severe": "#f97316",   # Orange-500
    "severe":             "#ef4444",   # Red-500
}


def get_severity_color(severity: str) -> str:
    """
    Return a hex colour string for a given severity level.

    Parameters
    ----------
    severity : str
        One of ``"mild"``, ``"mild_to_moderate"``, ``"moderate"``,
        ``"moderate_to_severe"``, ``"severe"``.

    Returns
    -------
    str
        Hex colour code (e.g. ``"#22c55e"``).  Falls back to grey
        (``"#6b7280"``) for unknown values.
    """
    return _SEVERITY_COLORS.get(severity, "#6b7280")


# ────────────────────────────────────────────────────────────────────
# Complete clinical profiles for all 11 parasite species
# ────────────────────────────────────────────────────────────────────

PARASITE_PROFILES: dict[str, dict[str, Any]] = {

    "Ascaris_lumbricoides": {
        "common_name": "Roundworm",
        "disease": "Ascariasis",
        "severity": "moderate",
        "transmission": "Fecal-oral route, contaminated soil/food",
        "symptoms": [
            "Abdominal pain",
            "Nausea/vomiting",
            "Intestinal obstruction (heavy infection)",
            "Loeffler syndrome (pulmonary phase)",
            "Malnutrition in children",
        ],
        "complications": [
            "Intestinal obstruction",
            "Biliary obstruction",
            "Appendicitis",
            "Pancreatitis",
        ],
        "treatment": [
            "Albendazole 400mg single dose",
            "Mebendazole 500mg single dose",
            "Ivermectin 200 mcg/kg single dose",
        ],
        "recommended_tests": [
            "Complete Blood Count (eosinophilia)",
            "Stool examination x3",
            "Abdominal X-ray if obstruction suspected",
        ],
        "red_flags": [
            "Signs of intestinal obstruction (severe pain, vomiting, distension)",
            "Worm migration (coughing up worms, worm in vomit)",
        ],
        "educational_note": (
            "Ascaris is the most common helminth worldwide. Eggs are "
            "resistant to environmental conditions and can survive in soil "
            "for years. Fertilized eggs are oval with thick mammillated "
            "shell, while unfertilized eggs are elongated and irregular."
        ),
    },

    "Hookworm": {
        "common_name": "Hookworm",
        "disease": "Hookworm infection (Ancylostomiasis/Necatoriasis)",
        "severity": "moderate_to_severe",
        "transmission": "Larvae penetrate skin (walking barefoot on contaminated soil)",
        "symptoms": [
            "Iron deficiency anemia (chronic blood loss)",
            "Fatigue and weakness",
            "Ground itch (skin penetration site)",
            "Abdominal pain",
            "Protein malnutrition",
            "Growth retardation in children",
        ],
        "complications": [
            "Severe iron deficiency anemia",
            "Heart failure (severe chronic anemia)",
            "Growth retardation",
            "Cognitive impairment in children",
        ],
        "treatment": [
            "Albendazole 400mg single dose",
            "Mebendazole 500mg single dose",
            "Iron supplementation for anemia",
            "Nutritional support",
        ],
        "recommended_tests": [
            "CBC with differential (microcytic anemia, eosinophilia)",
            "Serum iron and ferritin (low)",
            "Stool examination x3",
            "Quantitative egg count (Kato-Katz)",
        ],
        "red_flags": [
            "Hemoglobin < 7 g/dL (severe anemia)",
            "Signs of heart failure",
            "Severe malnutrition",
        ],
        "educational_note": (
            "Hookworm is a leading cause of iron deficiency anemia "
            "worldwide. The thin-shelled oval egg with clear space between "
            "shell and developing morula is diagnostic. Two species infect "
            "humans: Ancylostoma duodenale and Necator americanus."
        ),
    },

    "Trichuris_trichiura": {
        "common_name": "Whipworm",
        "disease": "Trichuriasis",
        "severity": "mild_to_moderate",
        "transmission": "Fecal-oral route, ingestion of embryonated eggs",
        "symptoms": [
            "Often asymptomatic (light infection)",
            "Abdominal pain",
            "Diarrhea (mucoid/bloody in heavy infection)",
            "Rectal prolapse (heavy infection in children)",
            "Iron deficiency anemia",
        ],
        "complications": [
            "Rectal prolapse",
            "Chronic dysentery",
            "Growth retardation",
            "Anemia",
        ],
        "treatment": [
            "Albendazole 400mg daily x3 days",
            "Mebendazole 500mg single dose or 100mg BID x3 days",
            "Ivermectin (alternative)",
        ],
        "recommended_tests": [
            "Stool examination x3",
            "CBC (eosinophilia, anemia)",
            "Colonoscopy if rectal prolapse",
        ],
        "red_flags": [
            "Rectal prolapse",
            "Severe bloody diarrhea",
            "Significant anemia",
        ],
        "educational_note": (
            "The barrel-shaped egg with bipolar mucous plugs is "
            "pathognomonic. Light infections are usually asymptomatic. "
            "The adult worm threads its thin anterior end into the "
            "colonic mucosa."
        ),
    },

    "Enterobius_vermicularis": {
        "common_name": "Pinworm",
        "disease": "Enterobiasis",
        "severity": "mild",
        "transmission": "Fecal-oral, autoinfection, airborne eggs",
        "symptoms": [
            "Perianal itching (worse at night)",
            "Restless sleep",
            "Irritability",
            "Rarely: vulvovaginitis in girls",
        ],
        "complications": [
            "Secondary bacterial infection from scratching",
            "Vulvovaginitis",
            "Rarely: appendicitis",
        ],
        "treatment": [
            "Mebendazole 100mg single dose, repeat in 2 weeks",
            "Albendazole 400mg single dose, repeat in 2 weeks",
            "Pyrantel pamoate 11mg/kg",
            "Treat entire household",
        ],
        "recommended_tests": [
            "Scotch tape test (perianal swab — morning before bathing)",
            "NOT routine stool exam (eggs rarely found in stool)",
        ],
        "red_flags": [
            "Severe secondary infection",
            "Ectopic migration",
        ],
        "educational_note": (
            "Most common helminth in developed countries. The asymmetric "
            "egg with one flattened side is characteristic. Scotch tape "
            "test is the gold standard, not stool exam. Finding eggs in "
            "stool is uncommon but possible."
        ),
    },

    "Taenia_spp": {
        "common_name": "Tapeworm",
        "disease": "Taeniasis",
        "severity": "moderate",
        "transmission": "Ingestion of undercooked beef (T. saginata) or pork (T. solium)",
        "symptoms": [
            "Often asymptomatic",
            "Abdominal discomfort",
            "Passage of proglottids in stool",
            "Nausea",
            "Weight loss",
        ],
        "complications": [
            "Cysticercosis (T. solium only — SERIOUS)",
            "Neurocysticercosis (seizures, brain cysts)",
            "Intestinal obstruction (rare)",
        ],
        "treatment": [
            "Praziquantel 10mg/kg single dose",
            "Niclosamide 2g single dose",
            "If T. solium: evaluate for cysticercosis",
        ],
        "recommended_tests": [
            "Stool exam for eggs and proglottids",
            "Species identification (proglottid morphology)",
            "If T. solium: brain MRI/CT to rule out neurocysticercosis",
            "Serology for cysticercosis",
        ],
        "red_flags": [
            "Seizures (suspect neurocysticercosis)",
            "Visual disturbances",
            "Signs of increased intracranial pressure",
            "T. solium identification requires cysticercosis workup",
        ],
        "educational_note": (
            "Taenia eggs cannot differentiate T. solium from T. saginata "
            "microscopically — they look identical. Species identification "
            "requires examining proglottids. T. solium is dangerous because "
            "of cysticercosis risk. The round egg with thick radially "
            "striated shell (embryophore) is diagnostic."
        ),
    },

    "Hymenolepis_nana": {
        "common_name": "Dwarf tapeworm",
        "disease": "Hymenolepiasis",
        "severity": "mild",
        "transmission": "Fecal-oral, autoinfection possible (no intermediate host needed)",
        "symptoms": [
            "Usually asymptomatic",
            "Abdominal pain (heavy infection)",
            "Diarrhea",
            "Anorexia",
        ],
        "complications": [
            "Heavy autoinfection in immunocompromised",
        ],
        "treatment": [
            "Praziquantel 25mg/kg single dose",
            "Niclosamide (alternative)",
        ],
        "recommended_tests": [
            "Stool examination x3",
            "CBC (mild eosinophilia)",
        ],
        "red_flags": [
            "Immunocompromised patient (risk of heavy autoinfection)",
        ],
        "educational_note": (
            "Most common tapeworm in humans worldwide. Unique among "
            "tapeworms — can complete entire life cycle in one host "
            "(autoinfection). Small round egg (30-47 um) with thin "
            "shell and polar filaments between inner and outer membranes."
        ),
    },

    "Hymenolepis_diminuta": {
        "common_name": "Rat tapeworm",
        "disease": "Hymenolepiasis",
        "severity": "mild",
        "transmission": "Accidental ingestion of infected insects (grain beetles, fleas)",
        "symptoms": [
            "Usually asymptomatic",
            "Mild GI symptoms",
            "Abdominal pain",
        ],
        "complications": [
            "None significant",
        ],
        "treatment": [
            "Praziquantel 25mg/kg single dose",
            "Niclosamide (alternative)",
        ],
        "recommended_tests": [
            "Stool examination",
            "Species differentiation from H. nana",
        ],
        "red_flags": [],
        "educational_note": (
            "Primarily a parasite of rodents, humans are accidental "
            "hosts. Larger egg than H. nana (60-80 um), round with "
            "thick shell, NO polar filaments (key differentiator from "
            "H. nana)."
        ),
    },

    "Fasciolopsis_buski": {
        "common_name": "Giant intestinal fluke",
        "disease": "Fasciolopsiasis",
        "severity": "moderate",
        "transmission": "Ingestion of metacercariae on aquatic plants (water caltrop, water chestnut)",
        "symptoms": [
            "Abdominal pain",
            "Diarrhea",
            "Nausea/vomiting",
            "Edema (face, abdominal wall)",
            "Intestinal obstruction (heavy infection)",
        ],
        "complications": [
            "Intestinal obstruction",
            "Malabsorption",
            "Anasarca (severe edema)",
        ],
        "treatment": [
            "Praziquantel 25mg/kg TID x1 day",
            "Niclosamide (alternative)",
        ],
        "recommended_tests": [
            "Stool examination for eggs",
            "CBC (eosinophilia)",
            "Serum albumin (low in severe cases)",
        ],
        "red_flags": [
            "Severe edema",
            "Signs of intestinal obstruction",
            "Malnutrition",
        ],
        "educational_note": (
            "Largest intestinal fluke of humans. The large unembryonated "
            "egg (130-140 x 80-85 um) with a small operculum is "
            "diagnostic. Cannot be differentiated from Fasciola hepatica "
            "eggs by microscopy alone."
        ),
    },

    "Opisthorchis_viverrine": {
        "common_name": "Liver fluke",
        "disease": "Opisthorchiasis",
        "severity": "moderate_to_severe",
        "transmission": "Ingestion of raw/undercooked freshwater fish",
        "symptoms": [
            "Often asymptomatic initially",
            "Right upper quadrant pain",
            "Jaundice",
            "Hepatomegaly",
            "Cholangitis",
        ],
        "complications": [
            "Cholangiocarcinoma (bile duct cancer — SERIOUS)",
            "Recurrent cholangitis",
            "Biliary obstruction",
            "Liver abscess",
        ],
        "treatment": [
            "Praziquantel 25mg/kg TID x1-2 days",
            "Follow-up imaging",
        ],
        "recommended_tests": [
            "Stool examination x3",
            "Liver function tests (elevated ALP, GGT)",
            "Abdominal ultrasound",
            "MRCP if biliary symptoms",
            "Tumor markers (CA 19-9) for cholangiocarcinoma screening",
        ],
        "red_flags": [
            "Jaundice",
            "Persistent right upper quadrant pain",
            "Weight loss (suspect cholangiocarcinoma)",
            "Fever with jaundice (cholangitis)",
        ],
        "educational_note": (
            "Chronic infection is a WHO-recognized risk factor for "
            "cholangiocarcinoma. The small egg (22-32 um) with operculum "
            "and posterior knob is diagnostic. Endemic in Southeast Asia "
            "where raw fish dishes are common."
        ),
    },

    "Paragonimus_spp": {
        "common_name": "Lung fluke",
        "disease": "Paragonimiasis",
        "severity": "severe",
        "transmission": "Ingestion of raw/undercooked freshwater crabs or crayfish",
        "symptoms": [
            "Chronic cough",
            "Hemoptysis (blood-tinged sputum)",
            "Chest pain",
            "Pleural effusion",
            "Can mimic tuberculosis",
        ],
        "complications": [
            "Cerebral paragonimiasis (brain involvement — seizures)",
            "Pleural effusion",
            "Pneumothorax",
            "Misdiagnosis as TB",
        ],
        "treatment": [
            "Praziquantel 25mg/kg TID x3 days",
            "Triclabendazole (alternative)",
        ],
        "recommended_tests": [
            "Sputum examination for eggs",
            "Stool examination",
            "Chest X-ray (infiltrates, pleural effusion, ring shadows)",
            "CT chest",
            "Brain CT/MRI if neurological symptoms",
            "Serology",
        ],
        "red_flags": [
            "Hemoptysis (can be severe)",
            "Seizures (cerebral involvement)",
            "Being treated for TB with no improvement (consider paragonimiasis)",
        ],
        "educational_note": (
            "Often misdiagnosed as tuberculosis due to similar symptoms "
            "(chronic cough, hemoptysis). The large oval egg (77-80 um) "
            "with thick shell and operculum is found in sputum or stool. "
            "Eggs in stool result from swallowed sputum."
        ),
    },

    "Capillaria_philippinensis": {
        "common_name": "Capillaria",
        "disease": "Intestinal Capillariasis",
        "severity": "moderate",
        "transmission": "Ingestion of raw/undercooked freshwater fish",
        "symptoms": [
            "Chronic watery diarrhea",
            "Abdominal pain",
            "Borborygmi (gurgling sounds)",
            "Progressive weight loss",
            "Protein-losing enteropathy",
        ],
        "complications": [
            "Severe malabsorption",
            "Cachexia",
            "Death if untreated (up to 10% mortality)",
        ],
        "treatment": [
            "Mebendazole 200mg BID x20 days",
            "Albendazole 400mg daily x10 days",
        ],
        "recommended_tests": [
            "Serial stool examinations (eggs, larvae, adults)",
            "Serum albumin (low)",
            "Electrolytes",
            "Small bowel biopsy if needed",
        ],
        "red_flags": [
            "Severe weight loss",
            "Refractory diarrhea",
            "Hypoalbuminemia",
        ],
        "educational_note": (
            "Unique among helminths — can cause autoinfection in the "
            "intestine, leading to heavy worm burden. The peanut-shaped "
            "egg with striated shell and flattened bipolar plugs resembles "
            "Trichuris but is smaller (36-45 x 20-22 um)."
        ),
    },
}


# Severity rank for comparison
_SEVERITY_RANK: dict[str, int] = {
    "mild": 1,
    "mild_to_moderate": 2,
    "moderate": 3,
    "moderate_to_severe": 4,
    "severe": 5,
}


def _get_highest_severity(species_list: list[str]) -> str:
    """Return the highest severity among a list of species names."""
    max_rank = 0
    max_sev = "mild"
    for sp in species_list:
        profile = PARASITE_PROFILES.get(sp, {})
        sev = profile.get("severity", "mild")
        rank = _SEVERITY_RANK.get(sev, 1)
        if rank > max_rank:
            max_rank = rank
            max_sev = sev
    return max_sev


def _has_heavy_infection(parasite_counts: dict[str, int]) -> bool:
    """Return True if any species has 5+ eggs in one field."""
    return any(count >= 5 for count in parasite_counts.values())


def _deduplicate_list(items: list[str]) -> list[str]:
    """Deduplicate a list while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ────────────────────────────────────────────────────────────────────
# Scenario builders
# ────────────────────────────────────────────────────────────────────

def _build_parasite_entry(species: str, count: int) -> dict[str, Any]:
    """Build a complete parasite entry from the profile database."""
    profile = PARASITE_PROFILES.get(species, {})
    return {
        "species": species,
        "common_name": profile.get("common_name", species),
        "egg_count": count,
        "disease": profile.get("disease", "Unknown"),
        "severity": profile.get("severity", "unknown"),
        "transmission": profile.get("transmission", "Unknown"),
        "symptoms": profile.get("symptoms", []),
        "complications": profile.get("complications", []),
        "treatment": profile.get("treatment", []),
        "recommended_tests": profile.get("recommended_tests", []),
        "red_flags": profile.get("red_flags", []),
        "educational_note": profile.get("educational_note", ""),
    }


def _scenario_negative() -> dict[str, Any]:
    """SCENARIO 1 — No parasitic eggs detected."""
    return {
        "scenario_code": "NEGATIVE",
        "severity": "normal",
        "primary_diagnosis": "No parasitic eggs detected",
        "parasites_found": [],
        "overall_assessment": (
            "No parasitic eggs detected in this microscopic field. "
            "A negative result in one field does not rule out infection. "
            "If clinical suspicion remains, repeat stool examination on "
            "3 different days using concentration techniques is recommended."
        ),
        "combined_recommended_tests": [
            "Repeat stool examination x3 on different days",
            "Concentration techniques (formalin-ethyl acetate sedimentation)",
            "Kato-Katz quantitative method if available",
            "Consider serological tests if clinical suspicion is high",
        ],
        "combined_red_flags": [
            "Persistent GI symptoms despite negative stool exam — consider empiric treatment or advanced diagnostics",
            "Eosinophilia on CBC with negative stool — consider tissue-invasive helminths",
        ],
        "combined_treatment": [],
        "educational_summary": (
            "A single negative stool examination has limited sensitivity. "
            "Many parasites shed eggs intermittently, so serial examinations "
            "on 3 different days significantly improve detection rates. "
            "Concentration techniques (sedimentation or flotation) increase "
            "sensitivity for light infections."
        ),
        "summary_for_clinician": (
            "No parasitic eggs identified in this field. If clinical "
            "suspicion persists, repeat stool examination x3 on different "
            "days with concentration techniques is recommended."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


def _scenario_single_species(
    species: str,
    count: int,
    severity_category: str,
) -> dict[str, Any]:
    """SCENARIOS 2/3/4 — Single species detection."""
    profile = PARASITE_PROFILES.get(species, {})
    entry = _build_parasite_entry(species, count)
    common = profile.get("common_name", species)
    disease = profile.get("disease", "Unknown")
    sev = profile.get("severity", "unknown")

    scenario_map = {
        "mild": "SINGLE_SPECIES_MILD",
        "mild_to_moderate": "SINGLE_SPECIES_MODERATE",
        "moderate": "SINGLE_SPECIES_MODERATE",
        "moderate_to_severe": "SINGLE_SPECIES_SEVERE",
        "severe": "SINGLE_SPECIES_SEVERE",
    }
    scenario_code = scenario_map.get(severity_category, "SINGLE_SPECIES_MODERATE")

    # Build overall assessment message
    assessment_parts = [
        f"{common} ({species.replace('_', ' ')}) eggs detected "
        f"({count} egg{'s' if count != 1 else ''} in this field).",
        f"Diagnosis: {disease}.",
        f"Severity: {sev.replace('_', ' ')}.",
    ]
    if profile.get("transmission"):
        assessment_parts.append(f"Transmission: {profile['transmission']}.")

    return {
        "scenario_code": scenario_code,
        "severity": sev,
        "primary_diagnosis": disease,
        "parasites_found": [entry],
        "overall_assessment": " ".join(assessment_parts),
        "combined_recommended_tests": profile.get("recommended_tests", []),
        "combined_red_flags": profile.get("red_flags", []),
        "combined_treatment": profile.get("treatment", []),
        "educational_summary": profile.get("educational_note", ""),
        "summary_for_clinician": (
            f"{common} eggs identified ({count} egg{'s' if count != 1 else ''}/field). "
            f"Consistent with {disease}. "
            f"Recommend: {', '.join(profile.get('treatment', ['Antiparasitic treatment'])[:2])}. "
            f"Additional tests: {', '.join(profile.get('recommended_tests', [])[:3])}."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


def _scenario_multi_species(
    species_detected: list[str],
    parasite_counts: dict[str, int],
) -> dict[str, Any]:
    """SCENARIO 5 — Multiple species detected (co-infection)."""
    entries = []
    all_tests: list[str] = []
    all_flags: list[str] = []
    all_treatment: list[str] = []
    disease_names: list[str] = []

    for sp in species_detected:
        count = parasite_counts.get(sp, 0)
        if count == 0:
            continue
        entry = _build_parasite_entry(sp, count)
        entries.append(entry)

        profile = PARASITE_PROFILES.get(sp, {})
        all_tests.extend(profile.get("recommended_tests", []))
        all_flags.extend(profile.get("red_flags", []))
        all_treatment.extend(profile.get("treatment", []))
        disease_names.append(profile.get("disease", sp))

    overall_severity = _get_highest_severity(species_detected)

    # Build summary line
    species_summary = ", ".join(
        f"{PARASITE_PROFILES.get(sp, {}).get('common_name', sp)} ({parasite_counts.get(sp, 0)})"
        for sp in species_detected if parasite_counts.get(sp, 0) > 0
    )

    return {
        "scenario_code": "MULTI_SPECIES",
        "severity": overall_severity,
        "primary_diagnosis": f"Multi-parasitic co-infection: {', '.join(disease_names)}",
        "parasites_found": entries,
        "overall_assessment": (
            f"Co-infection with multiple parasitic species detected: "
            f"{species_summary}. "
            "Co-infection with multiple parasites suggests heavy "
            "environmental contamination or exposure to multiple "
            "transmission routes. Each species requires targeted "
            "treatment. Overall severity is determined by the most "
            "pathogenic species identified."
        ),
        "combined_recommended_tests": _deduplicate_list(all_tests),
        "combined_red_flags": _deduplicate_list(all_flags),
        "combined_treatment": _deduplicate_list(all_treatment),
        "educational_summary": (
            "Finding multiple parasite species in a single stool sample "
            "indicates polyparasitism, which is common in endemic areas "
            "with poor sanitation. Each species may require different "
            "treatment regimens. Comprehensive deworming programs often "
            "use broad-spectrum anthelmintics like Albendazole or "
            "Mebendazole combined with Praziquantel to cover both "
            "nematodes and cestodes/trematodes."
        ),
        "summary_for_clinician": (
            f"Multi-species parasitic co-infection: {species_summary}. "
            f"Overall severity: {overall_severity.replace('_', ' ')}. "
            "Consider combined antiparasitic therapy and comprehensive "
            "workup for all identified species."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


def _scenario_heavy_infection(
    species_detected: list[str],
    parasite_counts: dict[str, int],
) -> dict[str, Any]:
    """SCENARIO 6 — Heavy infection (5+ eggs of any species in one field)."""
    entries = []
    all_tests: list[str] = []
    all_flags: list[str] = []
    all_treatment: list[str] = []
    heavy_species: list[str] = []

    for sp in species_detected:
        count = parasite_counts.get(sp, 0)
        if count == 0:
            continue
        entry = _build_parasite_entry(sp, count)
        entries.append(entry)

        profile = PARASITE_PROFILES.get(sp, {})
        all_tests.extend(profile.get("recommended_tests", []))
        all_flags.extend(profile.get("red_flags", []))
        all_treatment.extend(profile.get("treatment", []))

        if count >= 5:
            heavy_species.append(sp)

    overall_severity = _get_highest_severity(species_detected)
    # Heavy infection bumps severity up if not already severe
    if _SEVERITY_RANK.get(overall_severity, 1) < _SEVERITY_RANK["moderate_to_severe"]:
        overall_severity = "moderate_to_severe"

    heavy_names = ", ".join(
        f"{PARASITE_PROFILES.get(sp, {}).get('common_name', sp)} "
        f"({parasite_counts.get(sp, 0)} eggs)"
        for sp in heavy_species
    )

    # Add heavy-infection-specific flags
    all_flags.insert(0, "HIGH EGG BURDEN — suggests heavy worm load, higher risk of complications")
    all_tests.insert(0, "Quantitative egg count (Kato-Katz) to assess infection intensity")

    return {
        "scenario_code": "HEAVY_INFECTION",
        "severity": overall_severity,
        "primary_diagnosis": f"Heavy parasitic infection — {heavy_names}",
        "parasites_found": entries,
        "overall_assessment": (
            f"HEAVY INFECTION DETECTED. High egg burden observed: "
            f"{heavy_names}. "
            "Finding 5 or more eggs in a single microscopic field "
            "indicates a heavy worm burden, which is associated with "
            "increased risk of complications. Prompt treatment is "
            "recommended. Consider quantitative egg count (Kato-Katz) "
            "to formally classify infection intensity."
        ),
        "combined_recommended_tests": _deduplicate_list(all_tests),
        "combined_red_flags": _deduplicate_list(all_flags),
        "combined_treatment": _deduplicate_list(all_treatment),
        "educational_summary": (
            "Intensity of helminth infections is classified by egg "
            "counts per gram of stool (EPG). For example, WHO classifies "
            "Ascaris: light (<5000 EPG), moderate (5000-49999), heavy "
            "(≥50000). High egg counts in a single microscopic field "
            "suggest heavy infection requiring prompt treatment and "
            "nutritional assessment, especially in children."
        ),
        "summary_for_clinician": (
            f"Heavy parasitic infection with high egg burden: "
            f"{heavy_names}. Severity: {overall_severity.replace('_', ' ')}. "
            "Prompt anthelmintic treatment strongly recommended. "
            "Assess for complications (anemia, malnutrition, obstruction). "
            "Kato-Katz quantitative egg count advised."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


# ────────────────────────────────────────────────────────────────────
# Main entry point
# ────────────────────────────────────────────────────────────────────

def generate_clinical_report(
    species_detected: list[str],
    parasite_counts: dict[str, int],
    species_info: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Generate a comprehensive clinical reasoning report from parasitology
    detection results.

    This function classifies the observation into one of 6 clinical
    scenarios and returns a structured report with diagnosis, parasites
    found (with full clinical profiles), recommended tests, treatment,
    red flags, and educational notes.

    Parameters
    ----------
    species_detected : list[str]
        List of species names detected (e.g. ``["Hookworm", "Ascaris_lumbricoides"]``).
    parasite_counts : dict[str, int]
        Mapping of species name to egg count (e.g. ``{"Hookworm": 2}``).
    species_info : list[dict] | None
        Optional species info list from the AI provider. Reserved for
        future use (e.g. confidence-weighted reasoning). Currently unused.

    Returns
    -------
    dict[str, Any]
        Comprehensive clinical report dictionary.

    Examples
    --------
    >>> report = generate_clinical_report(["Hookworm"], {"Hookworm": 2})
    >>> report["scenario_code"]
    'SINGLE_SPECIES_MODERATE'
    """
    # Filter to only species with count > 0
    active_species = [sp for sp in species_detected if parasite_counts.get(sp, 0) > 0]
    active_counts = {sp: parasite_counts[sp] for sp in active_species}
    num_species = len(active_species)

    # ── Scenario classification ──────────────────────────────────

    if num_species == 0:
        # SCENARIO 1: NEGATIVE
        scenario = "NEGATIVE"
        report = _scenario_negative()

    elif _has_heavy_infection(active_counts):
        # SCENARIO 6: HEAVY_INFECTION (checked before multi-species
        # since heavy infection takes priority)
        scenario = "HEAVY_INFECTION"
        report = _scenario_heavy_infection(active_species, active_counts)

    elif num_species >= 2:
        # SCENARIO 5: MULTI_SPECIES
        scenario = "MULTI_SPECIES"
        report = _scenario_multi_species(active_species, active_counts)

    else:
        # SCENARIOS 2/3/4: SINGLE_SPECIES (mild/moderate/severe)
        sp = active_species[0]
        count = active_counts[sp]
        profile = PARASITE_PROFILES.get(sp, {})
        sev = profile.get("severity", "moderate")

        if sev in ("mild",):
            severity_category = "mild"
        elif sev in ("severe",):
            severity_category = "severe"
        else:
            severity_category = sev  # moderate, mild_to_moderate, moderate_to_severe

        scenario = f"SINGLE_SPECIES_{severity_category.upper()}"
        report = _scenario_single_species(sp, count, severity_category)

    logger.info(
        "Parasitology reasoning matched scenario: %s  (species=%s, counts=%s)",
        scenario, active_species, active_counts,
    )

    # Attach input data for traceability
    report["input_species_detected"] = active_species
    report["input_parasite_counts"] = active_counts
    report["severity_color"] = get_severity_color(report.get("severity", "mild"))

    return report


# ────────────────────────────────────────────────────────────────────
# Self-test block
# ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
    )

    test_cases: list[tuple[str, list[str], dict[str, int]]] = [
        # (expected_scenario_prefix, species_detected, parasite_counts)
        ("NEGATIVE",                 [],                                  {}),
        ("SINGLE_SPECIES",           ["Hookworm"],                        {"Hookworm": 2}),
        ("MULTI_SPECIES",            ["Hookworm", "Ascaris_lumbricoides"], {"Hookworm": 2, "Ascaris_lumbricoides": 1}),
        ("HEAVY_INFECTION",          ["Taenia_spp"],                      {"Taenia_spp": 6}),
    ]

    all_passed = True
    print("=" * 72)
    print("  PARASITOLOGY CLINICAL REASONING ENGINE -- SELF-TEST")
    print("=" * 72)

    for expected_prefix, species, counts in test_cases:
        report = generate_clinical_report(species, counts)
        matched = report["scenario_code"]
        ok = matched.startswith(expected_prefix)
        status = "[PASS]" if ok else "[FAIL]"
        if not ok:
            all_passed = False

        print(f"\n{status}  Input: species={species}, counts={counts}")
        print(f"  Expected : starts with '{expected_prefix}'")
        print(f"  Matched  : {matched}")
        print(f"  Severity : {report.get('severity', '?')}  ({report.get('severity_color', '?')})")
        print(f"  Diagnosis: {report['primary_diagnosis']}")
        print(f"  Parasites: {len(report['parasites_found'])} species")
        print(f"  Tests    : {len(report['combined_recommended_tests'])} recommended")
        print(f"  Red Flags: {len(report['combined_red_flags'])} flags")
        print(f"  Treatment: {len(report['combined_treatment'])} options")
        if report.get("summary_for_clinician"):
            print(f"  Clinician: {report['summary_for_clinician'][:100]}...")

    print("\n" + "=" * 72)
    if all_passed:
        print("  ALL 4 SCENARIOS PASSED")
    else:
        print("  SOME SCENARIOS FAILED -- check output above")
    print("=" * 72)
