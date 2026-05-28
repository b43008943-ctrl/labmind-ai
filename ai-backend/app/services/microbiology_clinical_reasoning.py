"""
LabMind AI — Microbiology Clinical Reasoning Engine
====================================================

Rule-based clinical reasoning module that analyzes Gram stain findings
and generates comprehensive diagnostic reports.

Scenarios
---------
1. NO_BACTERIA               — No bacteria detected
2. GRAM_POSITIVE_COCCI_DOMINANT — G+ Cocci dominant
3. GRAM_NEGATIVE_BACILLI_DOMINANT — G- Bacilli dominant
4. GRAM_NEGATIVE_COCCI        — G- Cocci detected (Neisseria)
5. MIXED_FLORA                — Multiple types detected
6. GRAM_POSITIVE_BACILLI_DOMINANT — G+ Bacilli dominant
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("labmind.microbiology_reasoning")

_SEVERITY_COLORS: dict[str, str] = {
    "normal":    "#22c55e",
    "low":       "#84cc16",
    "moderate":  "#f59e0b",
    "high":      "#f97316",
    "critical":  "#ef4444",
}


def get_severity_color(severity: str) -> str:
    """Return hex colour for a given severity level."""
    return _SEVERITY_COLORS.get(severity, "#6b7280")


# ────────────────────────────────────────────────────────────────────
# Scenario builders
# ────────────────────────────────────────────────────────────────────

def _scenario_no_bacteria() -> dict[str, Any]:
    """SCENARIO 1 — No bacteria detected."""
    return {
        "scenario_code": "NO_BACTERIA",
        "severity": "normal",
        "primary_diagnosis": "No bacteria detected on Gram stain",
        "differential_diagnosis": [
            "Viral infection (no bacteria expected)",
            "Fungal infection (requires special stains)",
            "Atypical organisms (Mycoplasma, Chlamydia — not visible on Gram stain)",
            "Early or pre-treatment specimen",
        ],
        "ruled_out": [
            "Acute bacterial infection with high organism load",
        ],
        "recommended_investigations": [
            "Culture and sensitivity testing (48-72h incubation)",
            "Consider PCR/molecular testing for atypical pathogens",
            "Repeat Gram stain from a new specimen if clinical suspicion persists",
            "Special stains (acid-fast, Giemsa) if indicated",
        ],
        "red_flags": [
            "Persistent clinical signs of infection despite negative Gram stain",
            "Immunocompromised patient — consider empiric coverage",
        ],
        "educational_note": (
            "A negative Gram stain does not rule out infection. Some organisms "
            "(Mycoplasma, Chlamydia, Mycobacteria) are not visible on standard "
            "Gram stain. Culture remains the gold standard for definitive "
            "identification. The sensitivity of Gram stain is approximately "
            "60-90% depending on specimen quality and organism load."
        ),
        "treatment_considerations": [],
        "overall_assessment": (
            "No bacteria identified on this Gram-stained field. If clinical "
            "suspicion remains, culture and advanced molecular testing are recommended."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


def _scenario_gp_cocci_dominant(bacteria_counts: dict[str, int]) -> dict[str, Any]:
    """SCENARIO 2 — Gram-positive cocci dominant."""
    count = bacteria_counts.get("G+_Coccus", 0)
    return {
        "scenario_code": "GRAM_POSITIVE_COCCI_DOMINANT",
        "severity": "high",
        "primary_diagnosis": f"Gram-positive cocci detected ({count} organisms)",
        "differential_diagnosis": [
            {"organism": "Staphylococcus aureus", "arrangement": "Clusters (grape-like)", "diseases": "Skin/soft tissue infections, bacteremia, endocarditis, osteomyelitis"},
            {"organism": "Streptococcus pneumoniae", "arrangement": "Diplococci (lancet-shaped)", "diseases": "Pneumonia, meningitis, otitis media"},
            {"organism": "Streptococcus pyogenes (Group A)", "arrangement": "Chains", "diseases": "Pharyngitis, cellulitis, necrotizing fasciitis"},
            {"organism": "Enterococcus spp.", "arrangement": "Pairs/short chains", "diseases": "UTI, endocarditis, intra-abdominal infections"},
        ],
        "ruled_out": [
            "Gram-negative infection as primary pathogen",
            "Mycobacterial infection (acid-fast stain needed)",
        ],
        "recommended_investigations": [
            "Blood/wound/urine culture and sensitivity",
            "Coagulase test (S. aureus vs CoNS)",
            "Catalase test (Staphylococcus vs Streptococcus)",
            "Optochin sensitivity (S. pneumoniae)",
            "MRSA screening (mecA gene / cefoxitin disk)",
            "Complete blood count with differential",
        ],
        "red_flags": [
            "Fever with hemodynamic instability — suspect sepsis",
            "New heart murmur — evaluate for endocarditis (echocardiography)",
            "Rapid progression of skin lesion — consider necrotizing fasciitis",
            "Clusters in blood culture — high suspicion for S. aureus bacteremia",
        ],
        "educational_note": (
            "Gram-positive cocci are the most common bacteria seen on Gram stain. "
            "Arrangement is key: clusters suggest Staphylococcus, chains suggest "
            "Streptococcus, and diplococci suggest Pneumococcus. The catalase test "
            "differentiates Staphylococcus (positive) from Streptococcus (negative). "
            "The coagulase test further separates S. aureus (positive) from "
            "coagulase-negative staphylococci."
        ),
        "treatment_considerations": [
            "Empiric: Vancomycin (covers MRSA) pending culture results",
            "If MSSA confirmed: Oxacillin/Nafcillin (drug of choice)",
            "If Streptococcus: Penicillin/Ampicillin",
            "If Enterococcus: Ampicillin + Gentamicin (synergy)",
        ],
        "overall_assessment": (
            f"Gram-positive cocci detected ({count} organisms). Arrangement pattern "
            "is critical for preliminary identification. Culture and sensitivity "
            "testing recommended for definitive diagnosis and targeted therapy."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


def _scenario_gn_bacilli_dominant(bacteria_counts: dict[str, int]) -> dict[str, Any]:
    """SCENARIO 3 — Gram-negative bacilli dominant."""
    count = bacteria_counts.get("G-_Bacillus", 0)
    return {
        "scenario_code": "GRAM_NEGATIVE_BACILLI_DOMINANT",
        "severity": "high",
        "primary_diagnosis": f"Gram-negative bacilli detected ({count} organisms)",
        "differential_diagnosis": [
            {"organism": "Escherichia coli", "source": "Urinary tract, intra-abdominal", "diseases": "UTI, sepsis, meningitis (neonatal)"},
            {"organism": "Klebsiella pneumoniae", "source": "Respiratory, urinary", "diseases": "Pneumonia (currant jelly sputum), UTI, liver abscess"},
            {"organism": "Pseudomonas aeruginosa", "source": "Hospital-acquired", "diseases": "Ventilator-associated pneumonia, burn infections, chronic lung infections"},
            {"organism": "Proteus mirabilis", "source": "Urinary tract", "diseases": "Complicated UTI, struvite kidney stones"},
            {"organism": "Enterobacter spp.", "source": "Hospital-acquired", "diseases": "Nosocomial infections, inducible AmpC resistance"},
        ],
        "ruled_out": [
            "Gram-positive infection as primary cause",
            "Anaerobic infection (requires anaerobic culture)",
        ],
        "recommended_investigations": [
            "Culture and sensitivity (blood, urine, sputum as appropriate)",
            "ESBL screening (double-disk synergy test)",
            "Carbapenemase testing if MDR suspected",
            "Complete blood count with differential (leukocytosis)",
            "Procalcitonin and CRP for sepsis evaluation",
            "Lactate level if sepsis suspected",
        ],
        "red_flags": [
            "Signs of sepsis (fever, tachycardia, hypotension, altered mental status)",
            "Multi-drug resistant organism suspected (hospital-acquired)",
            "Gram-negative bacteremia — risk of endotoxic shock",
            "Immunocompromised patient — aggressive empiric therapy needed",
        ],
        "educational_note": (
            "Gram-negative bacilli stain pink/red due to their thin peptidoglycan "
            "layer and outer membrane containing lipopolysaccharide (LPS/endotoxin). "
            "LPS is a potent trigger of the inflammatory cascade and can cause "
            "septic shock. Antibiotic resistance is a major concern — ESBL-producing "
            "and carbapenem-resistant Enterobacteriaceae (CRE) are critical threats. "
            "Always obtain cultures before starting antibiotics."
        ),
        "treatment_considerations": [
            "Empiric: 3rd-gen Cephalosporin (Ceftriaxone) or Fluoroquinolone",
            "If ESBL suspected: Carbapenem (Meropenem, Imipenem)",
            "If Pseudomonas: Piperacillin-Tazobactam or Cefepime",
            "If CRE: Colistin, Ceftazidime-Avibactam (last resort agents)",
        ],
        "overall_assessment": (
            f"Gram-negative bacilli detected ({count} organisms). These are "
            "commonly associated with Enterobacteriaceae. Culture with "
            "susceptibility testing is essential due to rising antimicrobial resistance."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


def _scenario_gn_cocci(bacteria_counts: dict[str, int]) -> dict[str, Any]:
    """SCENARIO 4 — Gram-negative cocci detected (always clinically significant)."""
    count = bacteria_counts.get("G-_Coccus", 0)
    return {
        "scenario_code": "GRAM_NEGATIVE_COCCI",
        "severity": "critical",
        "primary_diagnosis": f"Gram-negative cocci detected ({count} organisms) — ALWAYS CLINICALLY SIGNIFICANT",
        "differential_diagnosis": [
            {"organism": "Neisseria meningitidis", "arrangement": "Intracellular diplococci (kidney-shaped)", "diseases": "Bacterial meningitis, meningococcemia, Waterhouse-Friderichsen syndrome"},
            {"organism": "Neisseria gonorrhoeae", "arrangement": "Intracellular diplococci", "diseases": "Gonorrhea, pelvic inflammatory disease, disseminated gonococcal infection"},
            {"organism": "Moraxella catarrhalis", "arrangement": "Diplococci", "diseases": "Otitis media, sinusitis, COPD exacerbation"},
        ],
        "ruled_out": [
            "Normal flora (Gram-negative cocci in clinical specimens are rarely contaminants)",
        ],
        "recommended_investigations": [
            "Culture on chocolate agar (CO2 enriched environment)",
            "Oxidase test (Neisseria is oxidase-positive)",
            "PCR/NAAT for Neisseria gonorrhoeae (gold standard for STI screening)",
            "Blood cultures if meningococcemia suspected",
            "CSF analysis if meningitis suspected (Gram stain, culture, protein, glucose)",
            "Lumbar puncture if meningeal signs present",
        ],
        "red_flags": [
            "Fever + neck stiffness + photophobia — SUSPECT MENINGITIS (medical emergency)",
            "Petechial/purpuric rash — meningococcemia (life-threatening)",
            "Altered consciousness — urgent neurological assessment needed",
            "Close contacts need chemoprophylaxis (Rifampin, Ciprofloxacin, or Ceftriaxone)",
        ],
        "educational_note": (
            "Gram-negative diplococci are one of the most clinically significant "
            "findings on Gram stain. Neisseria species are oxidase-positive, "
            "fastidious organisms requiring chocolate agar and CO2 for growth. "
            "N. meningitidis causes bacterial meningitis with high mortality — "
            "immediate empiric antibiotics are critical before culture results. "
            "N. gonorrhoeae is a major STI pathogen with increasing antibiotic "
            "resistance. NAAT is now preferred over culture for gonorrhea diagnosis."
        ),
        "treatment_considerations": [
            "N. meningitidis: Ceftriaxone 2g IV q12h (empiric) — DO NOT DELAY",
            "N. gonorrhoeae: Ceftriaxone 500mg IM single dose + Azithromycin 1g PO",
            "Moraxella: Amoxicillin-Clavulanate or Fluoroquinolone",
            "Chemoprophylaxis for close contacts of meningococcal disease",
        ],
        "overall_assessment": (
            f"Gram-negative cocci detected ({count} organisms). This finding "
            "is ALWAYS clinically significant and warrants immediate attention. "
            "If intracellular diplococci in CSF — treat as meningococcal meningitis "
            "until proven otherwise."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


def _scenario_mixed_flora(bacteria_counts: dict[str, int], species_detected: list[str]) -> dict[str, Any]:
    """SCENARIO 5 — Mixed flora (multiple types detected)."""
    _FRIENDLY = {
        "G-_Bacillus": "Gram-negative bacilli", "G+_Coccus": "Gram-positive cocci",
        "G-_Coccus": "Gram-negative cocci", "G+_Bacillus": "Gram-positive bacilli",
    }
    summary_parts = [f"{_FRIENDLY.get(sp, sp)} ({bacteria_counts.get(sp, 0)})" for sp in species_detected]
    summary = ", ".join(summary_parts)
    total = sum(bacteria_counts.values())

    return {
        "scenario_code": "MIXED_FLORA",
        "severity": "high",
        "primary_diagnosis": f"Mixed bacterial flora detected ({total} total organisms): {summary}",
        "differential_diagnosis": [
            "Polymicrobial infection (intra-abdominal abscess, aspiration pneumonia, wound infection)",
            "Normal flora contamination (oral, skin, vaginal specimens)",
            "Specimen collection contamination — re-collection may be needed",
            "Complicated infection with multiple pathogens",
        ],
        "ruled_out": [
            "Single-organism infection (multiple morphotypes present)",
        ],
        "recommended_investigations": [
            "Culture and sensitivity for each morphotype identified",
            "Anaerobic culture (mixed flora often includes anaerobes)",
            "Assess specimen quality (epithelial cells, WBCs, Q-score for sputum)",
            "Blood cultures x2 sets from separate sites",
            "CT/imaging if deep-seated abscess suspected",
        ],
        "red_flags": [
            "Foul-smelling discharge — suspect anaerobic involvement",
            "Gas in tissues on imaging — necrotizing infection/gas gangrene",
            "Rapidly spreading cellulitis — surgical emergency (necrotizing fasciitis)",
            "Aspiration history — polymicrobial aspiration pneumonia",
        ],
        "educational_note": (
            "Mixed flora on Gram stain can represent true polymicrobial infection "
            "or specimen contamination. Clinical context is key: mixed flora from "
            "a sterile site (blood, CSF) is almost always significant, while mixed "
            "flora from non-sterile sites (sputum, wound swabs) may represent normal "
            "flora. Sputum quality can be assessed using the Q-score: >25 PMNs and "
            "<10 epithelial cells per low-power field indicates a good-quality specimen."
        ),
        "treatment_considerations": [
            "Broad-spectrum empiric therapy (Piperacillin-Tazobactam or Carbapenem + Vancomycin)",
            "Add Metronidazole if anaerobic coverage needed",
            "Narrow therapy once culture and sensitivity results available",
            "Surgical consultation for source control if abscess suspected",
        ],
        "overall_assessment": (
            f"Mixed bacterial flora detected: {summary}. Clinical context and "
            "specimen quality must be considered. Culture with sensitivity testing "
            "is essential for targeted therapy."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


def _scenario_gp_bacilli_dominant(bacteria_counts: dict[str, int]) -> dict[str, Any]:
    """SCENARIO 6 — Gram-positive bacilli dominant."""
    count = bacteria_counts.get("G+_Bacillus", 0)
    return {
        "scenario_code": "GRAM_POSITIVE_BACILLI_DOMINANT",
        "severity": "moderate",
        "primary_diagnosis": f"Gram-positive bacilli detected ({count} organisms)",
        "differential_diagnosis": [
            {"organism": "Bacillus anthracis", "feature": "Large boxcar-shaped rods", "diseases": "Cutaneous/inhalation/GI anthrax (bioterrorism agent)"},
            {"organism": "Clostridium perfringens", "feature": "Large rods, no spores in tissue", "diseases": "Gas gangrene, food poisoning"},
            {"organism": "Clostridium difficile", "feature": "Spore-forming rod", "diseases": "Antibiotic-associated colitis, pseudomembranous colitis"},
            {"organism": "Corynebacterium diphtheriae", "feature": "Club-shaped, Chinese-letter arrangement", "diseases": "Diphtheria (pharyngeal membrane)"},
            {"organism": "Listeria monocytogenes", "feature": "Short rods, tumbling motility", "diseases": "Meningitis (neonates, elderly, immunocompromised)"},
        ],
        "ruled_out": [
            "Gram-negative infection as primary pathogen",
            "Normal skin flora (diphtheroids) — correlate clinically",
        ],
        "recommended_investigations": [
            "Culture on blood agar and selective media",
            "Spore stain (modified Ziehl-Neelsen)",
            "Anaerobic culture (Clostridium species)",
            "Toxin assay if C. difficile suspected",
            "Motility testing at 25°C (Listeria — tumbling motility)",
            "Complete blood count with differential",
        ],
        "red_flags": [
            "Large boxcar-shaped rods in blood — consider Bacillus anthracis (NOTIFY PUBLIC HEALTH)",
            "Crepitus in wound — suspect gas gangrene (surgical emergency)",
            "Recent antibiotic use + diarrhea — C. difficile infection",
            "Neonatal meningitis — consider Listeria (Ampicillin coverage needed)",
        ],
        "educational_note": (
            "Gram-positive bacilli are a diverse group ranging from harmless "
            "diphtheroids (Corynebacterium spp. — common skin flora) to dangerous "
            "pathogens like Bacillus anthracis and Clostridium species. Clinical "
            "context is critical: GPB from a wound with crepitus suggests gas "
            "gangrene, while GPB from a blood culture in a neonate may indicate "
            "Listeria. Spore formation is a key feature of Bacillus and Clostridium."
        ),
        "treatment_considerations": [
            "Bacillus anthracis: Ciprofloxacin or Doxycycline (empiric) + antitoxin",
            "Clostridium perfringens: Penicillin + Clindamycin + surgical debridement",
            "C. difficile: Vancomycin PO or Fidaxomicin (stop offending antibiotic)",
            "Listeria: Ampicillin + Gentamicin (neonates and immunocompromised)",
        ],
        "overall_assessment": (
            f"Gram-positive bacilli detected ({count} organisms). The clinical "
            "significance depends heavily on specimen source and clinical context. "
            "Culture and further testing are needed to differentiate pathogens from "
            "normal flora contaminants."
        ),
        "disclaimer": "AI-assisted analysis for educational purposes only.",
    }


# ────────────────────────────────────────────────────────────────────
# Main entry point
# ────────────────────────────────────────────────────────────────────

def generate_clinical_report(
    bacteria_counts: dict[str, int],
    bacteria_info: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Generate a comprehensive clinical reasoning report from Gram stain findings.

    Parameters
    ----------
    bacteria_counts : dict[str, int]
        Mapping of bacterial type to count.
    bacteria_info : list[dict] | None
        Optional bacteria info from the AI provider.

    Returns
    -------
    dict[str, Any]
        Comprehensive clinical report dictionary.
    """
    active = {k: v for k, v in bacteria_counts.items() if v > 0}
    species_detected = sorted(active.keys())
    total = sum(active.values())

    if total == 0:
        report = _scenario_no_bacteria()
    elif "G-_Coccus" in active and active.get("G-_Coccus", 0) > 0:
        # G- Cocci always takes priority (Neisseria is always significant)
        report = _scenario_gn_cocci(active)
    elif len(species_detected) >= 2:
        report = _scenario_mixed_flora(active, species_detected)
    elif "G+_Coccus" in active:
        report = _scenario_gp_cocci_dominant(active)
    elif "G-_Bacillus" in active:
        report = _scenario_gn_bacilli_dominant(active)
    elif "G+_Bacillus" in active:
        report = _scenario_gp_bacilli_dominant(active)
    else:
        report = _scenario_no_bacteria()

    logger.info(
        "Microbiology reasoning matched scenario: %s (counts=%s)",
        report.get("scenario_code"), active,
    )

    report["input_bacteria_counts"] = active
    report["input_species_detected"] = species_detected
    report["severity_color"] = get_severity_color(report.get("severity", "normal"))

    return report


# ────────────────────────────────────────────────────────────────────
# Self-test block
# ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(name)s  %(levelname)s  %(message)s")

    test_cases = [
        ("NO_BACTERIA", {}),
        ("GRAM_POSITIVE_COCCI_DOMINANT", {"G+_Coccus": 15}),
        ("GRAM_NEGATIVE_BACILLI_DOMINANT", {"G-_Bacillus": 8}),
        ("GRAM_NEGATIVE_COCCI", {"G-_Coccus": 3}),
        ("MIXED_FLORA", {"G+_Coccus": 5, "G-_Bacillus": 3}),
        ("GRAM_POSITIVE_BACILLI_DOMINANT", {"G+_Bacillus": 6}),
    ]

    all_passed = True
    print("=" * 72)
    print("  MICROBIOLOGY CLINICAL REASONING ENGINE -- SELF-TEST")
    print("=" * 72)

    for expected, counts in test_cases:
        report = generate_clinical_report(counts)
        matched = report["scenario_code"]
        ok = matched == expected
        status_str = "[PASS]" if ok else "[FAIL]"
        if not ok:
            all_passed = False

        print(f"\n{status_str}  Input: counts={counts}")
        print(f"  Expected : {expected}")
        print(f"  Matched  : {matched}")
        print(f"  Severity : {report.get('severity', '?')}  ({report.get('severity_color', '?')})")
        print(f"  Diagnosis: {report['primary_diagnosis']}")
        print(f"  Tests    : {len(report.get('recommended_investigations', []))} recommended")
        print(f"  Red Flags: {len(report.get('red_flags', []))} flags")

    print("\n" + "=" * 72)
    print("  ALL 6 SCENARIOS PASSED" if all_passed else "  SOME SCENARIOS FAILED")
    print("=" * 72)
