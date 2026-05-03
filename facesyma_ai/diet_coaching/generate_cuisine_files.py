"""
generate_cuisine_files.py
=========================
Bootstrap cuisine-specific meal files from existing language-base files.

Usage:
    python generate_cuisine_files.py

Creates meals_{cuisine_key}.json files for cuisine groups that don't have their
own file yet. Each file starts as a copy of the appropriate language base with
updated metadata. Cuisine content should be manually curated afterwards.

Missing cuisines after running this script:
  - meals_ar_gulf.json  (from meals_ar.json)  → Gulf Arab (SA, AE, KW, QA)
  - meals_ar_levant.json (from meals_ar.json) → Levant (LB, SY, JO, IQ, PS)
  - meals_ar_maghreb.json (from meals_ar.json) → North Africa (MA, DZ, TN, LY)
  - meals_MX.json       (from meals_es.json)  → Mexican
  - meals_AR.json       (from meals_es.json)  → Argentinian
  - meals_es_latam.json (from meals_es.json)  → Latin American
  - meals_BR.json       (from meals_pt.json)  → Brazilian
  - meals_US.json       (from meals_en.json)  → American
  - meals_GB.json       (from meals_en.json)  → British
  - meals_AU.json       (from meals_en.json)  → Australian
  - meals_CA.json       (from meals_en.json)  → Canadian
  - meals_BE.json       (from meals_fr.json)  → Belgian
  - meals_CH.json       (from meals_fr.json)  → Swiss
  - meals_TW.json       (from meals_zh.json)  → Taiwanese
  - meals_MY.json       (from meals_id.json)  → Malaysian
  - meals_PH.json       (from meals_en.json)  → Filipino
  - meals_NL.json       (from meals_de.json)  → Dutch
  - meals_nordic.json   (from meals_de.json)  → Nordic
  - meals_GR.json       (from meals_tr.json)  → Greek
  - meals_IL.json       (from meals_he.json)  → Israeli
  - meals_IR.json       (from meals_tr.json)  → Iranian
  - meals_ZA.json       (from meals_en.json)  → South African
  - meals_KE.json       (from meals_en.json)  → East African (Kenya)
  - meals_ET.json       (from meals_en.json)  → Ethiopian
  - meals_NG.json       (from meals_en.json)  → West African (Nigeria)
"""

import json
import copy
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# cuisine_key → (source_file, country_display, country_code, language_code)
CUISINE_BOOTSTRAP: dict = {
    "ar_gulf":   ("meals_ar.json",  "Gulf Arabia",    "SA",    "ar"),
    "ar_levant": ("meals_ar.json",  "Levant",         "LB",    "ar"),
    "ar_maghreb":("meals_ar.json",  "North Africa",   "MA",    "ar"),
    "MX":        ("meals_es.json",  "Mexico",         "MX",    "es"),
    "AR":        ("meals_es.json",  "Argentina",      "AR",    "es"),
    "es_latam":  ("meals_es.json",  "Latin America",  "CO",    "es"),
    "BR":        ("meals_pt.json",  "Brazil",         "BR",    "pt"),
    "US":        ("meals_en.json",  "United States",  "US",    "en"),
    "GB":        ("meals_en.json",  "United Kingdom", "GB",    "en"),
    "AU":        ("meals_en.json",  "Australia",      "AU",    "en"),
    "CA":        ("meals_en.json",  "Canada",         "CA",    "en"),
    "BE":        ("meals_fr.json",  "Belgium",        "BE",    "fr"),
    "CH":        ("meals_fr.json",  "Switzerland",    "CH",    "fr"),
    "TW":        ("meals_zh-hans.json", "Taiwan",      "TW",    "zh"),
    "MY":        ("meals_tl.json",  "Malaysia",       "MY",    "id"),
    "PH":        ("meals_en.json",  "Philippines",    "PH",    "en"),
    "NL":        ("meals_de.json",  "Netherlands",    "NL",    "de"),
    "nordic":    ("meals_de.json",  "Scandinavia",    "SE",    "no"),
    "GR":        ("meals_tr.json",  "Greece",         "GR",    "el"),
    "IL":        ("meals_he.json",  "Israel",         "IL",    "he"),
    "IR":        ("meals_tr.json",  "Iran",           "IR",    "fa"),
    "ZA":        ("meals_en.json",  "South Africa",   "ZA",    "en"),
    "KE":        ("meals_en.json",  "Kenya",          "KE",    "sw"),
    "ET":        ("meals_en.json",  "Ethiopia",       "ET",    "am"),
    "NG":        ("meals_en.json",  "Nigeria",        "NG",    "en"),
}


def _remap_ids(meals_by_type: dict, prefix: str) -> dict:
    """Re-prefix all meal IDs so they don't clash with the source cuisine."""
    result = copy.deepcopy(meals_by_type)
    for meal_type, meals in result.items():
        for i, meal in enumerate(meals, 1):
            old_id = meal.get("id", "")
            # Replace source prefix (e.g. tr_, es_) with new prefix
            new_id = re.sub(r'^[a-z]+_', f"{prefix.lower()}_", old_id)
            if new_id == old_id:
                # Fallback: just prepend prefix
                new_id = f"{prefix.lower()}_{meal_type}_{i:03d}"
            meal["id"] = new_id
    return result


def generate(cuisine_key: str, overwrite: bool = False) -> bool:
    source_file, country_display, country_code, language_code = CUISINE_BOOTSTRAP[cuisine_key]

    dest_path = DATA_DIR / f"meals_{cuisine_key}.json"
    if dest_path.exists() and not overwrite:
        print(f"  SKIP  {dest_path.name} (already exists)")
        return False

    source_path = DATA_DIR / source_file
    if not source_path.exists():
        print(f"  ERROR {cuisine_key}: source {source_file} not found")
        return False

    with open(source_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Update metadata
    data["country"]       = country_display
    data["country_code"]  = country_code
    data["language_code"] = language_code

    # Remap IDs to avoid collisions
    data["meals"] = _remap_ids(data["meals"], cuisine_key.replace("-", "_"))

    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    meal_count = sum(len(v) for v in data["meals"].values())
    print(f"  OK    {dest_path.name}  ({meal_count} meals from {source_file})")
    return True


def main():
    print(f"Cuisine bootstrap — data dir: {DATA_DIR}\n")
    created = 0
    skipped = 0
    for cuisine_key in CUISINE_BOOTSTRAP:
        ok = generate(cuisine_key, overwrite=False)
        if ok:
            created += 1
        else:
            skipped += 1
    print(f"\nDone: {created} created, {skipped} skipped")
    print("\nNOTE: Generated files are copies of their language base.")
    print("Manually curate meal content to reflect each cuisine's actual dishes.")


if __name__ == "__main__":
    main()
