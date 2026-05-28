"""
Verify Step 5 field-level interpreter on all 11 validation smears.
Reports screening_result, evidence_strength, and summary for each.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.providers.ai_provider_v1 import V1Provider

SMEAR_DIRS = {
    "normal": os.path.join("validation_smears", "normal"),
    "sickle": os.path.join("validation_smears", "sickle"),
}
VALID_EXTS = ('.jpg', '.jpeg', '.png')


def main():
    provider = V1Provider()
    results = []

    for category, dir_path in SMEAR_DIRS.items():
        smears = sorted([f for f in os.listdir(dir_path) if f.lower().endswith(VALID_EXTS)])
        for smear_file in smears:
            smear_path = os.path.join(dir_path, smear_file)
            smear_name = smear_file.replace(".jpg.jpg", "").replace(".jpg", "")
            print(f"  Processing: {smear_file} ...", end=" ")

            try:
                result = provider.analyze(smear_path)
                fi = result.get("field_interpretation", {})

                entry = {
                    "smear": smear_name,
                    "category": category,
                    "screening_result": fi.get("screening_result", "N/A"),
                    "confidence": fi.get("confidence", 0),
                    "evidence_strength": fi.get("evidence_strength", "N/A"),
                    "sickle_count": fi.get("sickle_count", 0),
                    "total_rbc": fi.get("total_rbc_counted", 0),
                    "sickle_pct": fi.get("sickle_percentage", 0),
                    "summary": fi.get("summary", "N/A"),
                }
                results.append(entry)
                print(f"{fi.get('screening_result', 'N/A')} "
                      f"(sickle={fi.get('sickle_count',0)}, "
                      f"pct={fi.get('sickle_percentage',0):.1f}%, "
                      f"evidence={fi.get('evidence_strength','N/A')})")
            except Exception as e:
                print(f"ERROR: {e}")
                results.append({
                    "smear": smear_name, "category": category,
                    "screening_result": "ERROR", "error": str(e),
                })

    # Save
    out_path = "field_interpretation_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print()
    print("=" * 80)
    print(f"  {'Smear':<25} {'Category':<8} {'Result':<25} {'Sickle':<8} {'Pct':<8} {'Evidence'}")
    print("-" * 80)
    for r in results:
        print(f"  {r['smear']:<25} {r['category']:<8} {r['screening_result']:<25} "
              f"{r.get('sickle_count','?'):<8} {r.get('sickle_pct',0):<8.1f} "
              f"{r.get('evidence_strength','?')}")
    print("=" * 80)

    # Acceptance checks
    normal_positive = [r for r in results if r["category"] == "normal" and r["screening_result"] == "SICKLE_SCREEN_POSITIVE"]
    sickle_positive = [r for r in results if r["category"] == "sickle" and r["screening_result"] == "SICKLE_SCREEN_POSITIVE"]

    print()
    print(f"  Normal fields called SICKLE_SCREEN_POSITIVE: {len(normal_positive)}")
    print(f"  Sickle fields called SICKLE_SCREEN_POSITIVE: {len(sickle_positive)}/6")
    print()
    print(f"  Acceptance: Zero normal POSITIVE = {'PASS' if len(normal_positive) == 0 else 'FAIL'}")
    print(f"  Acceptance: >=5/6 sickle POSITIVE = {'PASS' if len(sickle_positive) >= 5 else 'FAIL'}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    main()
