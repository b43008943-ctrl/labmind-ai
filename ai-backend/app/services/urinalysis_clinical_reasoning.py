"""
LabMind AI — Urinalysis Clinical Reasoning Engine
==================================================

Rule-based clinical reasoning module that analyzes urine sediment cell
counts and generates comprehensive diagnostic reports.

This module is **pure Python** — no external API calls, no ML models.
It encodes established clinical guidelines for urine microscopy
interpretation into a deterministic decision tree.

Scenarios
---------
1. NORMAL_SAMPLE          – All counts within normal reference ranges
2. ISOLATED_HEMATURIA     – Significant RBC elevation, WBC/EP normal
3. MILD_HEMATURIA         – Borderline RBC elevation (3-5/HPF)
4. CLASSIC_UTI            – WBC markedly elevated, RBC normal
5. HEMORRHAGIC_UTI        – Both WBC and RBC significantly elevated
6. MILD_PYURIA            – Slight WBC elevation (6-10/HPF)
7. SAMPLE_CONTAMINATION   – Excessive epithelial cells (>15)
8. COMPLEX_INFLAMMATION   – Multi-lineage elevation (RBC + WBC + EP)

Clinical References
-------------------
- Simerville JA, et al. "Urinalysis: A Comprehensive Review."
  Am Fam Physician. 2005;71(6):1153-1162.
- European Association of Urology (EAU) Guidelines on Urological
  Infections, 2023.
- Brunzel NA. Fundamentals of Urine and Body Fluid Analysis, 4th ed.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("labmind.urine_reasoning")


# ────────────────────────────────────────────────────────────────────
# Severity colour mapping (for frontend UI badges)
# ────────────────────────────────────────────────────────────────────

_SEVERITY_COLORS: dict[str, str] = {
    "normal": "#22c55e",    # Tailwind green-500
    "mild": "#f59e0b",      # Tailwind amber-500
    "abnormal": "#ef4444",  # Tailwind red-500
    "critical": "#dc2626",  # Tailwind red-600
}


def get_severity_color(severity: str) -> str:
    """
    Return a hex colour string for a given severity level.

    Parameters
    ----------
    severity : str
        One of ``"normal"``, ``"mild"``, ``"abnormal"``, ``"critical"``.

    Returns
    -------
    str
        Hex colour code (e.g. ``"#22c55e"``).  Falls back to grey
        (``"#6b7280"``) for unknown values.
    """
    return _SEVERITY_COLORS.get(severity, "#6b7280")


# ────────────────────────────────────────────────────────────────────
# Scenario builders
# ────────────────────────────────────────────────────────────────────

def _scenario_normal(rbc: int, pus: int, ep: int) -> dict[str, Any]:
    """SCENARIO 1 — Normal urine sediment."""
    return {
        "scenario_code": "NORMAL_SAMPLE",
        "severity": "normal",
        "primary_diagnosis": {
            "english": "Normal Urine Sediment",
            "arabic": "رواسب بولية طبيعية",
        },
        "differential_diagnosis": [
            {
                "condition": "No pathological finding",
                "arabic": "لا يوجد مرض",
                "likelihood": "confirmed",
            },
        ],
        "ruled_out": [
            {
                "condition": "Urinary Tract Infection",
                "reason": f"WBC count within normal limits ({pus}/HPF ≤ 5)",
                "arabic_reason": "عدد الخلايا البيضاء طبيعي",
            },
            {
                "condition": "Hematuria",
                "reason": f"RBC count within normal limits ({rbc}/HPF ≤ 2)",
                "arabic_reason": "عدد كريات الدم الحمراء طبيعي",
            },
            {
                "condition": "Sample contamination",
                "reason": f"Epithelial cell count normal ({ep}/HPF ≤ 5)",
                "arabic_reason": "عدد الخلايا الظهارية طبيعي",
            },
        ],
        "recommended_investigations": [
            {
                "test": "Routine follow-up urinalysis if clinically indicated",
                "arabic": "إعادة الفحص روتينياً عند الحاجة السريرية",
                "priority": "low",
            },
        ],
        "red_flags": [],
        "educational_note": {
            "english": (
                "All cell counts are within normal reference ranges. "
                "Normal urine may contain up to 2 RBCs/HPF, 5 WBCs/HPF, "
                "and a few epithelial cells. No further workup is required "
                "in the absence of clinical symptoms."
            ),
            "arabic": (
                "جميع أعداد الخلايا ضمن المعدل الطبيعي. "
                "البول الطبيعي قد يحتوي على ما يصل إلى ٢ كريات حمراء "
                "و٥ خلايا بيضاء وعدد قليل من الخلايا الظهارية لكل حقل مجهري. "
                "لا حاجة لفحوصات إضافية بغياب الأعراض السريرية."
            ),
        },
        "summary_for_clinician": (
            f"Normal urine sediment: {rbc} RBCs, {pus} WBCs, "
            f"{ep} epithelial cells per HPF. "
            "No pathological findings. Routine follow-up only."
        ),
    }


def _scenario_isolated_hematuria(rbc: int, pus: int, ep: int) -> dict[str, Any]:
    """SCENARIO 2 — Significant isolated hematuria (RBC > 5, WBC/EP normal)."""
    return {
        "scenario_code": "ISOLATED_HEMATURIA",
        "severity": "abnormal",
        "primary_diagnosis": {
            "english": "Significant Hematuria",
            "arabic": "بيلة دموية شديدة",
        },
        "differential_diagnosis": [
            {
                "condition": "Renal / ureteric stones (nephrolithiasis)",
                "arabic": "حصى كلوية أو حالبية",
                "likelihood": "most_likely",
            },
            {
                "condition": "Glomerulonephritis",
                "arabic": "التهاب كبيبات الكلى",
                "likelihood": "possible",
            },
            {
                "condition": "Urinary tract trauma",
                "arabic": "إصابة المسالك البولية",
                "likelihood": "possible",
            },
            {
                "condition": "Bladder or renal malignancy",
                "arabic": "أورام المثانة أو الكلى",
                "likelihood": "rare_but_important",
            },
            {
                "condition": "Vigorous exercise-induced hematuria",
                "arabic": "بيلة دموية ناتجة عن رياضة عنيفة",
                "likelihood": "benign",
            },
        ],
        "ruled_out": [
            {
                "condition": "Urinary Tract Infection",
                "reason": f"No pyuria detected (WBC = {pus}/HPF, within normal)",
                "arabic_reason": "غياب الصديد — لا يوجد التهاب",
            },
            {
                "condition": "Sample contamination",
                "reason": f"Clean sample (epithelial = {ep}/HPF)",
                "arabic_reason": "عينة نظيفة — الخلايا الظهارية طبيعية",
            },
        ],
        "recommended_investigations": [
            {
                "test": "Repeat urinalysis in 24-48 hours",
                "arabic": "إعادة فحص البول خلال ٢٤-٤٨ ساعة",
                "priority": "high",
            },
            {
                "test": "Urine culture and sensitivity",
                "arabic": "زراعة البول وحساسية المضادات",
                "priority": "high",
            },
            {
                "test": "Renal and bladder ultrasound",
                "arabic": "تصوير بالموجات فوق الصوتية للكلى والمثانة",
                "priority": "high",
            },
            {
                "test": "Serum creatinine, BUN, and electrolytes",
                "arabic": "كرياتينين ويوريا وأملاح الدم",
                "priority": "medium",
            },
            {
                "test": "CT KUB (non-contrast) if nephrolithiasis suspected",
                "arabic": "أشعة مقطعية بدون صبغة عند الشك بحصى",
                "priority": "conditional",
            },
            {
                "test": "Urine cytology if malignancy suspected (age > 40)",
                "arabic": "فحص خلايا البول عند الشك بورم (العمر > ٤٠)",
                "priority": "conditional",
            },
        ],
        "red_flags": [
            {
                "flag": "Severe flank or costovertebral angle pain",
                "arabic": "ألم شديد في الخاصرة أو زاوية الظهر",
                "action": "Immediate imaging to rule out obstructing stone",
            },
            {
                "flag": "Fever accompanying hematuria",
                "arabic": "حمى مصاحبة للنزيف البولي",
                "action": "Suspect complicated pyelonephritis — start empiric antibiotics",
            },
            {
                "flag": "Gross (macroscopic) hematuria",
                "arabic": "دم ظاهر للعين المجردة في البول",
                "action": "Urgent urology referral",
            },
            {
                "flag": "History of anticoagulant use",
                "arabic": "استخدام مضادات التخثر",
                "action": "Check coagulation profile (PT/INR)",
            },
        ],
        "educational_note": {
            "english": (
                "Hematuria without pyuria typically suggests a mechanical "
                "(nephrolithiasis, trauma) or vascular/glomerular cause rather "
                "than infection. The absence of WBC elevation is a key "
                "diagnostic clue that steers workup toward imaging and renal "
                "function tests rather than urine culture alone. In patients "
                "over 40, painless hematuria must be evaluated for malignancy."
            ),
            "arabic": (
                "وجود نزيف بولي بدون صديد يشير عادةً إلى سبب ميكانيكي "
                "(حصى أو إصابة) أو وعائي/كبيبي وليس عدوى. "
                "غياب ارتفاع الخلايا البيضاء دليل تشخيصي مهم يوجّه "
                "الفحوصات نحو التصوير ووظائف الكلى بدلاً من زراعة البول فقط. "
                "في المرضى فوق سن ٤٠، يجب استبعاد الأورام الخبيثة."
            ),
        },
        "summary_for_clinician": (
            f"{rbc} RBCs/HPF detected with no pyuria (WBC = {pus}) and "
            f"no epithelial contamination (EP = {ep}). "
            "Pattern consistent with non-inflammatory hematuria. "
            "Recommend renal imaging to rule out nephrolithiasis or "
            "structural lesion."
        ),
    }


def _scenario_mild_hematuria(rbc: int, pus: int, ep: int) -> dict[str, Any]:
    """SCENARIO 3 — Mild / borderline hematuria (RBC 3-5/HPF)."""
    return {
        "scenario_code": "MILD_HEMATURIA",
        "severity": "mild",
        "primary_diagnosis": {
            "english": "Mild Hematuria (Borderline)",
            "arabic": "بيلة دموية خفيفة (حدّية)",
        },
        "differential_diagnosis": [
            {
                "condition": "Early / small renal stone",
                "arabic": "حصاة كلوية صغيرة أو مبكرة",
                "likelihood": "possible",
            },
            {
                "condition": "Exercise-induced hematuria",
                "arabic": "بيلة دموية ناتجة عن الرياضة",
                "likelihood": "possible",
            },
            {
                "condition": "Menstrual contamination (females)",
                "arabic": "تلوث العينة بدم الحيض (إناث)",
                "likelihood": "possible",
            },
            {
                "condition": "Mild glomerular leak",
                "arabic": "تسرب كبيبي خفيف",
                "likelihood": "less_likely",
            },
            {
                "condition": "Benign / idiopathic cause",
                "arabic": "سبب حميد أو غير معروف",
                "likelihood": "benign",
            },
        ],
        "ruled_out": [
            {
                "condition": "Urinary Tract Infection",
                "reason": f"WBC within normal range ({pus}/HPF)",
                "arabic_reason": "خلايا الدم البيضاء طبيعية — لا التهاب",
            },
            {
                "condition": "Sample contamination",
                "reason": f"Epithelial cells within normal range ({ep}/HPF)",
                "arabic_reason": "الخلايا الظهارية طبيعية",
            },
        ],
        "recommended_investigations": [
            {
                "test": "Repeat urinalysis in 1-2 weeks",
                "arabic": "إعادة فحص البول خلال ١-٢ أسابيع",
                "priority": "medium",
            },
            {
                "test": "Urine dipstick for blood confirmation",
                "arabic": "شريط كيميائي لتأكيد وجود الدم",
                "priority": "medium",
            },
            {
                "test": "Blood pressure measurement",
                "arabic": "قياس ضغط الدم",
                "priority": "medium",
            },
            {
                "test": "Serum creatinine if persistent",
                "arabic": "كرياتينين الدم في حال الاستمرار",
                "priority": "low",
            },
        ],
        "red_flags": [
            {
                "flag": "Persistent hematuria on repeat testing",
                "arabic": "استمرار الدم في البول عند إعادة الفحص",
                "action": "Escalate to full hematuria workup (imaging + cystoscopy)",
            },
            {
                "flag": "New-onset hypertension",
                "arabic": "ارتفاع ضغط الدم لأول مرة",
                "action": "Evaluate for glomerular disease",
            },
        ],
        "educational_note": {
            "english": (
                "Mild hematuria (3-5 RBCs/HPF) is common and often benign, "
                "especially in young patients after vigorous exercise or in "
                "females during menstruation. However, persistent microscopic "
                "hematuria warrants at least a repeat urinalysis. If it "
                "persists across 2-3 specimens, full evaluation including "
                "imaging is recommended."
            ),
            "arabic": (
                "البيلة الدموية الخفيفة (٣-٥ كريات حمراء/حقل) شائعة وغالباً "
                "حميدة، خاصةً عند الشباب بعد الرياضة أو عند الإناث أثناء "
                "الدورة الشهرية. لكن استمرارها يستدعي إعادة الفحص، وإذا "
                "تكرر في ٢-٣ عينات فيُوصى بالتقييم الكامل شاملاً التصوير."
            ),
        },
        "summary_for_clinician": (
            f"Borderline hematuria: {rbc} RBCs/HPF (reference: 0-2). "
            f"WBC = {pus}, EP = {ep} — both normal. "
            "Often benign; recommend repeat urinalysis in 1-2 weeks. "
            "If persistent, consider imaging workup."
        ),
    }


def _scenario_classic_uti(rbc: int, pus: int, ep: int) -> dict[str, Any]:
    """SCENARIO 4 — Classic UTI pattern (significant pyuria, RBC normal)."""
    return {
        "scenario_code": "CLASSIC_UTI",
        "severity": "abnormal",
        "primary_diagnosis": {
            "english": "Significant Pyuria — Urinary Tract Infection",
            "arabic": "صديد شديد — التهاب المسالك البولية",
        },
        "differential_diagnosis": [
            {
                "condition": "Acute bacterial cystitis",
                "arabic": "التهاب المثانة البكتيري الحاد",
                "likelihood": "most_likely",
            },
            {
                "condition": "Acute pyelonephritis",
                "arabic": "التهاب الكلى والحوض الحاد",
                "likelihood": "possible",
            },
            {
                "condition": "Urethritis (gonococcal / non-gonococcal)",
                "arabic": "التهاب الإحليل (سيلاني / غير سيلاني)",
                "likelihood": "possible",
            },
            {
                "condition": "Interstitial cystitis",
                "arabic": "التهاب المثانة الخلالي",
                "likelihood": "less_likely",
            },
            {
                "condition": "Renal tuberculosis (sterile pyuria)",
                "arabic": "سلّ كلوي (صديد بدون بكتيريا)",
                "likelihood": "rare_but_important",
            },
        ],
        "ruled_out": [
            {
                "condition": "Hematuria / bleeding source",
                "reason": f"RBC count within normal limits ({rbc}/HPF ≤ 2)",
                "arabic_reason": "كريات الدم الحمراء طبيعية — لا نزيف",
            },
        ],
        "recommended_investigations": [
            {
                "test": "Urine culture and antibiotic sensitivity (MANDATORY)",
                "arabic": "زراعة البول وحساسية المضادات الحيوية (إلزامي)",
                "priority": "high",
            },
            {
                "test": "Urine dipstick: nitrite and leukocyte esterase",
                "arabic": "شريط كيميائي: نيترايت واسترايز الكريات البيض",
                "priority": "high",
            },
            {
                "test": "CBC with differential",
                "arabic": "صورة دم كاملة مع التفريقية",
                "priority": "medium",
            },
            {
                "test": "Serum creatinine",
                "arabic": "كرياتينين الدم",
                "priority": "medium",
            },
            {
                "test": "Renal ultrasound if recurrent UTI or pyelonephritis suspected",
                "arabic": "تصوير الكلى بالموجات فوق الصوتية عند تكرر الالتهاب",
                "priority": "conditional",
            },
        ],
        "red_flags": [
            {
                "flag": "High fever (> 38.5°C) with rigors",
                "arabic": "حمى عالية (> ٣٨.٥°م) مع رعشة",
                "action": "Suspect pyelonephritis — admit for IV antibiotics if severe",
            },
            {
                "flag": "Flank pain or costovertebral tenderness",
                "arabic": "ألم في الخاصرة أو إيلام في زاوية الظهر",
                "action": "Distinguish upper from lower UTI — imaging may be needed",
            },
            {
                "flag": "Recurrent UTIs (≥ 3 per year)",
                "arabic": "التهابات متكررة (≥ ٣ سنوياً)",
                "action": "Evaluate for anatomical abnormalities or vesicoureteral reflux",
            },
            {
                "flag": "UTI in males or children",
                "arabic": "التهاب مسالك عند الذكور أو الأطفال",
                "action": "Always requires full workup — atypical population",
            },
        ],
        "educational_note": {
            "english": (
                "A classic UTI pattern shows significant pyuria (> 10 WBC/HPF) "
                "without hematuria. Urine culture is the gold standard for "
                "confirming the diagnosis and guiding antibiotic therapy. "
                "Empiric treatment may be started while awaiting culture "
                "results in symptomatic patients. Sterile pyuria (elevated "
                "WBC with negative culture) should raise suspicion for TB, "
                "interstitial nephritis, or partially treated infection."
            ),
            "arabic": (
                "النمط الكلاسيكي لالتهاب المسالك يُظهر صديداً شديداً "
                "(> ١٠ خلايا بيضاء/حقل) بدون نزيف. زراعة البول هي المعيار "
                "الذهبي لتأكيد التشخيص وتوجيه العلاج بالمضادات الحيوية. "
                "يمكن بدء العلاج التجريبي أثناء انتظار نتائج الزراعة. "
                "الصديد العقيم (خلايا بيضاء مع زراعة سلبية) يستدعي الشك "
                "بالسلّ أو التهاب الكلى الخلالي."
            ),
        },
        "summary_for_clinician": (
            f"Significant pyuria: {pus} WBCs/HPF (reference: 0-5). "
            f"RBC = {rbc} (normal), EP = {ep}. "
            "Classic UTI pattern. Urine culture mandatory. "
            "Consider empiric antibiotics if symptomatic."
        ),
    }


def _scenario_hemorrhagic_uti(rbc: int, pus: int, ep: int) -> dict[str, Any]:
    """SCENARIO 5 — Hemorrhagic UTI (both WBC and RBC significantly elevated)."""
    return {
        "scenario_code": "HEMORRHAGIC_UTI",
        "severity": "critical",
        "primary_diagnosis": {
            "english": "Hemorrhagic Urinary Tract Infection",
            "arabic": "التهاب مسالك بولية نزفي",
        },
        "differential_diagnosis": [
            {
                "condition": "Hemorrhagic cystitis",
                "arabic": "التهاب مثانة نزفي",
                "likelihood": "most_likely",
            },
            {
                "condition": "Complicated pyelonephritis with bleeding",
                "arabic": "التهاب كلوي معقّد مع نزيف",
                "likelihood": "possible",
            },
            {
                "condition": "Infected kidney stone (pyonephrosis)",
                "arabic": "حصاة كلوية ملتهبة (تقيّح الكلى)",
                "likelihood": "possible",
            },
            {
                "condition": "Urethritis with mucosal erosion",
                "arabic": "التهاب إحليل مع تآكل مخاطي",
                "likelihood": "possible",
            },
            {
                "condition": "Schistosomiasis (endemic areas)",
                "arabic": "بلهارسيا (المناطق الموبوءة)",
                "likelihood": "rare_but_important",
            },
            {
                "condition": "Bladder tumor with secondary infection",
                "arabic": "ورم مثانة مع التهاب ثانوي",
                "likelihood": "rare_but_important",
            },
        ],
        "ruled_out": [],
        "recommended_investigations": [
            {
                "test": "Urine culture and sensitivity (URGENT)",
                "arabic": "زراعة البول وحساسية المضادات (عاجل)",
                "priority": "high",
            },
            {
                "test": "CBC with differential + CRP",
                "arabic": "صورة دم كاملة + بروتين التفاعلي سي",
                "priority": "high",
            },
            {
                "test": "Renal function tests (creatinine, BUN)",
                "arabic": "وظائف الكلى (كرياتينين، يوريا)",
                "priority": "high",
            },
            {
                "test": "Blood culture if febrile",
                "arabic": "زراعة الدم إذا وجدت حمى",
                "priority": "high",
            },
            {
                "test": "Renal and bladder ultrasound",
                "arabic": "تصوير الكلى والمثانة بالموجات فوق الصوتية",
                "priority": "high",
            },
            {
                "test": "CT KUB if stone suspected",
                "arabic": "أشعة مقطعية عند الشك بحصى",
                "priority": "conditional",
            },
            {
                "test": "Cystoscopy if recurrent or age > 40",
                "arabic": "منظار مثانة إذا متكرر أو العمر > ٤٠",
                "priority": "conditional",
            },
        ],
        "red_flags": [
            {
                "flag": "High fever with rigors and flank pain",
                "arabic": "حمى عالية مع رعشة وألم في الخاصرة",
                "action": "Suspect urosepsis — immediate blood cultures and IV antibiotics",
            },
            {
                "flag": "Gross hematuria with clot retention",
                "arabic": "دم ظاهر مع احتباس جلطات",
                "action": "Urology emergency — may need bladder irrigation",
            },
            {
                "flag": "Oliguria or rising creatinine",
                "arabic": "قلة البول أو ارتفاع الكرياتينين",
                "action": "Suspect obstructive uropathy — urgent imaging",
            },
            {
                "flag": "Immunocompromised patient",
                "arabic": "مريض منقوص المناعة",
                "action": "Low threshold for admission and broad-spectrum antibiotics",
            },
        ],
        "educational_note": {
            "english": (
                "Concurrent elevation of both WBC and RBC indicates an "
                "infectious process with mucosal damage or bleeding. This "
                "is more concerning than isolated pyuria or hematuria. "
                "Hemorrhagic cystitis can be caused by bacterial infection "
                "(most commonly E. coli), viral agents (adenovirus, BK virus "
                "in transplant patients), or chemical irritants (e.g. "
                "cyclophosphamide). Always rule out an infected obstructing "
                "stone, which is a urological emergency."
            ),
            "arabic": (
                "ارتفاع الخلايا البيضاء والحمراء معاً يشير إلى عملية "
                "التهابية مع تلف مخاطي أو نزيف. هذا أكثر خطورة من الصديد "
                "أو النزيف المنفرد. التهاب المثانة النزفي قد يكون بسبب "
                "عدوى بكتيرية (غالباً إي كولاي) أو فيروسية أو مهيجات "
                "كيميائية. يجب دائماً استبعاد حصاة سادّة ملتهبة — وهي حالة "
                "طوارئ بولية."
            ),
        },
        "summary_for_clinician": (
            f"Hemorrhagic UTI pattern: {pus} WBCs/HPF and {rbc} RBCs/HPF — "
            f"both significantly elevated. EP = {ep}. "
            "Indicates infection with mucosal damage. "
            "Urgent culture, CBC, and imaging recommended. "
            "Consider empiric broad-spectrum antibiotics."
        ),
    }


def _scenario_mild_pyuria(rbc: int, pus: int, ep: int) -> dict[str, Any]:
    """SCENARIO 6 — Mild pyuria (WBC 6-10/HPF)."""
    return {
        "scenario_code": "MILD_PYURIA",
        "severity": "mild",
        "primary_diagnosis": {
            "english": "Mild Pyuria — Early or Resolving Infection",
            "arabic": "صديد خفيف — التهاب مبكر أو في طور الشفاء",
        },
        "differential_diagnosis": [
            {
                "condition": "Early / uncomplicated UTI",
                "arabic": "التهاب مسالك بولية مبكر أو بسيط",
                "likelihood": "most_likely",
            },
            {
                "condition": "Resolving UTI (post-treatment)",
                "arabic": "التهاب في طور الشفاء بعد العلاج",
                "likelihood": "possible",
            },
            {
                "condition": "Non-specific urethritis",
                "arabic": "التهاب إحليل غير نوعي",
                "likelihood": "possible",
            },
            {
                "condition": "Asymptomatic bacteriuria",
                "arabic": "بيلة جرثومية بدون أعراض",
                "likelihood": "possible",
            },
            {
                "condition": "Sample contamination (vaginal discharge)",
                "arabic": "تلوث العينة (إفرازات مهبلية)",
                "likelihood": "possible",
            },
        ],
        "ruled_out": [
            {
                "condition": "Hematuria",
                "reason": f"RBC count within normal limits ({rbc}/HPF ≤ 2)",
                "arabic_reason": "كريات الدم الحمراء طبيعية",
            },
        ],
        "recommended_investigations": [
            {
                "test": "Urine culture and sensitivity",
                "arabic": "زراعة البول وحساسية المضادات",
                "priority": "high",
            },
            {
                "test": "Repeat urinalysis in 3-5 days if asymptomatic",
                "arabic": "إعادة الفحص خلال ٣-٥ أيام إذا بدون أعراض",
                "priority": "medium",
            },
            {
                "test": "Urine dipstick: nitrite and leukocyte esterase",
                "arabic": "شريط كيميائي: نيترايت واسترايز الكريات البيض",
                "priority": "medium",
            },
            {
                "test": "STI screening if urethritis suspected",
                "arabic": "فحص الأمراض المنقولة جنسياً عند الشك بالتهاب الإحليل",
                "priority": "conditional",
            },
        ],
        "red_flags": [
            {
                "flag": "Progression to significant pyuria on repeat testing",
                "arabic": "تطور إلى صديد شديد عند إعادة الفحص",
                "action": "Treat as confirmed UTI — start antibiotics",
            },
            {
                "flag": "Dysuria, frequency, or suprapubic pain",
                "arabic": "ألم أثناء التبول أو تكرار البول أو ألم فوق العانة",
                "action": "Clinical UTI — treat empirically pending culture",
            },
        ],
        "educational_note": {
            "english": (
                "Mild pyuria (6-10 WBCs/HPF) is a grey zone. It can "
                "represent early infection, resolving infection, or even "
                "contamination. Clinical correlation is essential — "
                "symptomatic patients should be treated, while asymptomatic "
                "patients may be observed with repeat urinalysis. Note that "
                "asymptomatic bacteriuria should NOT be treated in "
                "non-pregnant adults (it increases antibiotic resistance "
                "without clinical benefit)."
            ),
            "arabic": (
                "الصديد الخفيف (٦-١٠ خلايا بيضاء/حقل) منطقة رمادية. قد يمثل "
                "التهاباً مبكراً أو في طور الشفاء أو حتى تلوثاً للعينة. "
                "الارتباط السريري ضروري — المرضى ذوو الأعراض يُعالجون، بينما "
                "يمكن مراقبة المرضى بدون أعراض مع إعادة الفحص. البيلة "
                "الجرثومية بدون أعراض لا تُعالج عند البالغين غير الحوامل."
            ),
        },
        "summary_for_clinician": (
            f"Mild pyuria: {pus} WBCs/HPF (reference: 0-5). "
            f"RBC = {rbc} (normal), EP = {ep}. "
            "May represent early UTI or contamination. "
            "Culture recommended; correlate with clinical symptoms."
        ),
    }


def _scenario_contamination(rbc: int, pus: int, ep: int) -> dict[str, Any]:
    """SCENARIO 7 — Sample contamination (epithelial > 15)."""
    return {
        "scenario_code": "SAMPLE_CONTAMINATION",
        "severity": "mild",
        "primary_diagnosis": {
            "english": "Probable Sample Contamination",
            "arabic": "تلوث محتمل للعينة",
        },
        "differential_diagnosis": [
            {
                "condition": "Improper sample collection (no clean-catch)",
                "arabic": "جمع عينة غير صحيح (بدون تقنية النقطة الوسطى)",
                "likelihood": "most_likely",
            },
            {
                "condition": "Vaginal discharge contamination (females)",
                "arabic": "تلوث بالإفرازات المهبلية (إناث)",
                "likelihood": "possible",
            },
            {
                "condition": "Preputial contamination (uncircumcised males)",
                "arabic": "تلوث من القلفة (ذكور غير مختونين)",
                "likelihood": "possible",
            },
        ],
        "ruled_out": [],
        "recommended_investigations": [
            {
                "test": "Recollect urine with proper clean-catch midstream technique",
                "arabic": "إعادة جمع العينة بتقنية النقطة الوسطى الصحيحة",
                "priority": "high",
            },
            {
                "test": "Instruct patient on proper collection procedure",
                "arabic": "توجيه المريض لطريقة الجمع الصحيحة",
                "priority": "high",
            },
            {
                "test": "Catheterized specimen if unable to collect properly",
                "arabic": "عينة بالقسطرة إذا تعذر الجمع بشكل صحيح",
                "priority": "conditional",
            },
        ],
        "red_flags": [
            {
                "flag": "Symptoms present despite contaminated specimen",
                "arabic": "أعراض موجودة رغم تلوث العينة",
                "action": "Do not dismiss symptoms — recollect and re-evaluate",
            },
        ],
        "educational_note": {
            "english": (
                "A high squamous epithelial cell count (> 15/HPF) strongly "
                "suggests that the urine specimen is contaminated with skin "
                "or vaginal flora, making other findings unreliable. Any WBC "
                "or bacterial counts in such a specimen cannot be trusted "
                "for diagnosis. The recommended approach is to recollect "
                "using the clean-catch midstream technique: cleanse the "
                "periurethral area, void the first portion, then collect "
                "the midstream into a sterile container."
            ),
            "arabic": (
                "ارتفاع الخلايا الظهارية الحرشفية (> ١٥/حقل) يشير بقوة إلى "
                "تلوث العينة بالفلورا الجلدية أو المهبلية، مما يجعل النتائج "
                "الأخرى غير موثوقة. لا يمكن الاعتماد على أعداد الخلايا "
                "البيضاء أو البكتيريا في مثل هذه العينة. الأسلوب الموصى "
                "به هو إعادة الجمع بتقنية النقطة الوسطى: تنظيف منطقة "
                "الإحليل، التبول قليلاً ثم جمع العينة الوسطى في وعاء معقم."
            ),
        },
        "summary_for_clinician": (
            f"Specimen likely contaminated: {ep} epithelial cells/HPF "
            f"(reference: < 5). RBC = {rbc}, WBC = {pus} — "
            "interpret with caution. Recommend recollection using "
            "proper clean-catch midstream technique before clinical "
            "decisions are made."
        ),
    }


def _scenario_complex_inflammation(rbc: int, pus: int, ep: int) -> dict[str, Any]:
    """SCENARIO 8 — Complex inflammation (multi-lineage elevation)."""
    return {
        "scenario_code": "COMPLEX_INFLAMMATION",
        "severity": "critical",
        "primary_diagnosis": {
            "english": "Complex Urinary Tract Inflammation",
            "arabic": "التهاب مسالك بولية معقّد",
        },
        "differential_diagnosis": [
            {
                "condition": "Complicated pyelonephritis",
                "arabic": "التهاب كلى وحوض معقّد",
                "likelihood": "most_likely",
            },
            {
                "condition": "Hemorrhagic pyelonephritis with tissue damage",
                "arabic": "التهاب كلوي نزفي مع تلف أنسجة",
                "likelihood": "possible",
            },
            {
                "condition": "Renal abscess or pyonephrosis",
                "arabic": "خراج كلوي أو تقيّح الكلى",
                "likelihood": "possible",
            },
            {
                "condition": "Invasive bladder pathology (carcinoma + infection)",
                "arabic": "مرض مثانة غازي (ورم + التهاب)",
                "likelihood": "rare_but_important",
            },
            {
                "condition": "Renal papillary necrosis (diabetes, sickle cell)",
                "arabic": "نخر الحليمات الكلوية (سكري، أنيميا منجلية)",
                "likelihood": "rare_but_important",
            },
            {
                "condition": "Early urosepsis",
                "arabic": "تعفن بولي مبكر",
                "likelihood": "rare_but_important",
            },
        ],
        "ruled_out": [],
        "recommended_investigations": [
            {
                "test": "Urine culture and sensitivity (URGENT)",
                "arabic": "زراعة البول وحساسية المضادات (عاجل)",
                "priority": "high",
            },
            {
                "test": "Blood culture × 2 sets",
                "arabic": "زراعة الدم — ٢ عينتين",
                "priority": "high",
            },
            {
                "test": "CBC, CRP, procalcitonin",
                "arabic": "صورة دم كاملة وبروتين التفاعلي سي وبروكالسيتونين",
                "priority": "high",
            },
            {
                "test": "Renal function tests + electrolytes",
                "arabic": "وظائف الكلى + أملاح الدم",
                "priority": "high",
            },
            {
                "test": "CT abdomen/pelvis with contrast",
                "arabic": "أشعة مقطعية بالصبغة للبطن والحوض",
                "priority": "high",
            },
            {
                "test": "Lactate level if sepsis suspected",
                "arabic": "مستوى اللاكتات عند الشك بتعفن",
                "priority": "conditional",
            },
            {
                "test": "Cystoscopy after acute phase resolves",
                "arabic": "منظار المثانة بعد حل المرحلة الحادة",
                "priority": "conditional",
            },
        ],
        "red_flags": [
            {
                "flag": "Septic picture (fever, tachycardia, hypotension)",
                "arabic": "صورة تعفنية (حمى، تسارع نبض، هبوط ضغط)",
                "action": "Activate sepsis protocol — IV fluids, broad-spectrum antibiotics, ICU consult",
            },
            {
                "flag": "Acute kidney injury (rising creatinine, oliguria)",
                "arabic": "إصابة كلوية حادة (ارتفاع كرياتينين، قلة بول)",
                "action": "Urgent nephrology consultation",
            },
            {
                "flag": "Altered consciousness or confusion",
                "arabic": "تغيّر مستوى الوعي أو تشوّش",
                "action": "Suspect severe sepsis — escalate care immediately",
            },
            {
                "flag": "Immunosuppressed or diabetic patient",
                "arabic": "مريض منقوص المناعة أو مريض سكري",
                "action": "High risk for atypical organisms — consider antifungal coverage",
            },
        ],
        "educational_note": {
            "english": (
                "Simultaneous elevation of RBC, WBC, and epithelial cells "
                "indicates a severe, multi-component urinary tract process. "
                "This pattern may be seen in complicated pyelonephritis with "
                "tissue destruction, where the inflammatory exudate contains "
                "all cell types. The elevated epithelial component may "
                "indicate renal tubular/transitional cell shedding rather "
                "than simple contamination. This is a potentially serious "
                "finding that warrants urgent evaluation and often empiric "
                "parenteral antibiotics."
            ),
            "arabic": (
                "ارتفاع كريات الدم الحمراء والبيضاء والخلايا الظهارية معاً "
                "يشير إلى عملية مرضية شديدة ومتعددة المكونات في المسالك "
                "البولية. قد يُشاهد هذا النمط في التهاب الكلى المعقّد مع "
                "تلف الأنسجة. ارتفاع الخلايا الظهارية قد يمثل تساقط خلايا "
                "الأنابيب الكلوية أو الخلايا الانتقالية وليس مجرد تلوث. "
                "هذا اكتشاف خطير يستدعي تقييماً عاجلاً ومضادات حيوية وريدية."
            ),
        },
        "summary_for_clinician": (
            f"Complex inflammation: {rbc} RBCs, {pus} WBCs, "
            f"{ep} epithelial cells/HPF — all elevated. "
            "Multi-lineage elevation suggests complicated UTI with tissue "
            "damage or severe inflammatory process. Urgent culture, blood "
            "work, and imaging recommended. Consider empiric parenteral "
            "antibiotics pending results."
        ),
    }


# ────────────────────────────────────────────────────────────────────
# Main entry point
# ────────────────────────────────────────────────────────────────────

def generate_clinical_report(
    cell_counts: dict[str, int],
    detections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Generate a comprehensive clinical reasoning report from urine
    sediment cell counts.

    This function classifies the observation into one of 8 clinical
    scenarios and returns a structured report with diagnosis,
    differential diagnosis, ruled-out conditions, recommended
    investigations, red flags, and educational notes — all bilingual
    (English + Arabic).

    Parameters
    ----------
    cell_counts : dict[str, int]
        Cell counts per high-power field.  Expected keys:
        ``"rbc"`` (red blood cells), ``"pus"`` (WBC / pus cells),
        ``"ep"`` (epithelial cells).
    detections : list[dict] | None
        Optional list of individual detection objects from the YOLO
        model.  Reserved for future use (e.g. morphology-based
        reasoning).  Currently unused.

    Returns
    -------
    dict[str, Any]
        Comprehensive clinical report dictionary.  See module docstring
        or individual scenario builders for the full schema.

    Examples
    --------
    >>> report = generate_clinical_report({"rbc": 7, "pus": 0, "ep": 1})
    >>> report["scenario_code"]
    'ISOLATED_HEMATURIA'
    """
    rbc = cell_counts.get("rbc", 0)
    pus = cell_counts.get("pus", 0)
    ep = cell_counts.get("ep", 0)

    # ── Scenario classification (order matters — most specific first) ──

    # SCENARIO 7: Sample contamination overrides everything
    if ep > 15:
        scenario = "SAMPLE_CONTAMINATION"
        report = _scenario_contamination(rbc, pus, ep)

    # SCENARIO 8: Complex inflammation (everything elevated)
    elif rbc > 5 and pus > 10 and ep > 5:
        scenario = "COMPLEX_INFLAMMATION"
        report = _scenario_complex_inflammation(rbc, pus, ep)

    # SCENARIO 5: Hemorrhagic UTI (both high)
    elif pus > 10 and rbc > 5:
        scenario = "HEMORRHAGIC_UTI"
        report = _scenario_hemorrhagic_uti(rbc, pus, ep)

    # SCENARIO 4: Classic UTI (WBC very high, RBC normal)
    elif pus > 10 and rbc <= 2:
        scenario = "CLASSIC_UTI"
        report = _scenario_classic_uti(rbc, pus, ep)

    # SCENARIO 2: Isolated significant hematuria
    elif rbc > 5 and pus <= 5 and ep <= 5:
        scenario = "ISOLATED_HEMATURIA"
        report = _scenario_isolated_hematuria(rbc, pus, ep)

    # SCENARIO 6: Mild pyuria
    elif 6 <= pus <= 10 and rbc <= 2:
        scenario = "MILD_PYURIA"
        report = _scenario_mild_pyuria(rbc, pus, ep)

    # SCENARIO 3: Mild hematuria
    elif 3 <= rbc <= 5 and pus <= 5 and ep <= 5:
        scenario = "MILD_HEMATURIA"
        report = _scenario_mild_hematuria(rbc, pus, ep)

    # SCENARIO 1: Normal (default fallback)
    else:
        scenario = "NORMAL_SAMPLE"
        report = _scenario_normal(rbc, pus, ep)

    logger.info(
        "Clinical reasoning matched scenario: %s  "
        "(rbc=%d, pus=%d, ep=%d)",
        scenario, rbc, pus, ep,
    )

    # Attach input data for traceability
    report["input_cell_counts"] = {"rbc": rbc, "pus": pus, "ep": ep}
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

    test_cases: list[tuple[str, dict[str, int]]] = [
        ("NORMAL_SAMPLE",        {"rbc": 1, "pus": 3, "ep": 2}),
        ("ISOLATED_HEMATURIA",   {"rbc": 12, "pus": 1, "ep": 0}),
        ("MILD_HEMATURIA",       {"rbc": 4, "pus": 2, "ep": 1}),
        ("CLASSIC_UTI",          {"rbc": 0, "pus": 18, "ep": 3}),
        ("HEMORRHAGIC_UTI",      {"rbc": 8, "pus": 15, "ep": 2}),
        ("MILD_PYURIA",          {"rbc": 1, "pus": 8, "ep": 3}),
        ("SAMPLE_CONTAMINATION", {"rbc": 2, "pus": 4, "ep": 22}),
        ("COMPLEX_INFLAMMATION", {"rbc": 9, "pus": 14, "ep": 8}),
    ]

    all_passed = True
    print("=" * 72)
    print("  URINALYSIS CLINICAL REASONING ENGINE -- SELF-TEST")
    print("=" * 72)

    for expected_scenario, counts in test_cases:
        report = generate_clinical_report(counts)
        matched = report["scenario_code"]
        status = "[PASS]" if matched == expected_scenario else "[FAIL]"
        if matched != expected_scenario:
            all_passed = False

        print(f"\n{status}  Input: {counts}")
        print(f"  Expected : {expected_scenario}")
        print(f"  Matched  : {matched}")
        print(f"  Severity : {report['severity']}  ({report['severity_color']})")
        print(f"  Diagnosis: {report['primary_diagnosis']['english']}")
        print(f"  Diff-Dx  : {len(report['differential_diagnosis'])} conditions")
        print(f"  Ruled Out: {len(report['ruled_out'])} conditions")
        print(f"  Tests    : {len(report['recommended_investigations'])} recommended")
        print(f"  Red Flags: {len(report['red_flags'])} flags")
        print(f"  Clinician: {report['summary_for_clinician'][:100]}...")

    print("\n" + "=" * 72)
    if all_passed:
        print("  ALL 8 SCENARIOS PASSED")
    else:
        print("  SOME SCENARIOS FAILED -- check output above")
    print("=" * 72)
