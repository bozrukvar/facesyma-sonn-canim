"""
add_face_enriched_i18n.py
=========================
Adds assessment.face_enriched_label key to all 18 language blocks in i18n.ts.
Inserted after the 'assessment.finance' key in each language block.
"""

from pathlib import Path

I18N_FILE = Path(__file__).parent.parent / "facesyma_mobile" / "src" / "utils" / "i18n.ts"

TRANSLATIONS: dict = {
    "tr": "Yüz Analizi ile Kişiselleştirildi",
    "en": "Personalized with Face Analysis",
    "de": "Mit Gesichtsanalyse personalisiert",
    "ru": "Персонализировано с анализом лица",
    "ar": "مخصص بتحليل الوجه",
    "es": "Personalizado con análisis facial",
    "ko": "얼굴 분석으로 개인화됨",
    "ja": "顔分析でパーソナライズ済み",
    "zh": "通过面部分析个性化",
    "hi": "चेहरे के विश्लेषण से व्यक्तिगत",
    "fr": "Personnalisé avec l'analyse faciale",
    "pt": "Personalizado com análise facial",
    "bn": "মুখ বিশ্লেষণ দিয়ে ব্যক্তিগতকৃত",
    "id": "Dipersonalisasi dengan analisis wajah",
    "ur": "چہرے کے تجزیے سے ذاتی",
    "it": "Personalizzato con analisi facciale",
    "vi": "Được cá nhân hóa với phân tích khuôn mặt",
    "pl": "Spersonalizowane z analizą twarzy",
}

ANCHOR = "'assessment.finance'"


def run():
    content = I18N_FILE.read_text(encoding="utf-8")
    lines = content.split("\n")
    updated = 0

    for lang, val in TRANSLATIONS.items():
        lang_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{lang}:") and "{" in line:
                lang_idx = i
                break

        if lang_idx is None:
            print(f"  ✗ '{lang}' bloku bulunamadi")
            continue

        anchor_idx = None
        for i in range(lang_idx, min(lang_idx + 5000, len(lines))):
            if ANCHOR in lines[i]:
                anchor_idx = i
                break

        if anchor_idx is None:
            print(f"  ✗ '{lang}' icin anchor bulunamadi")
            continue

        block_text = "\n".join(lines[lang_idx:min(anchor_idx + 20, len(lines))])
        if "'assessment.face_enriched_label'" in block_text:
            print(f"  - '{lang}': zaten mevcut")
            continue

        safe_val = val.replace("'", "\\'")
        new_line = f"    'assessment.face_enriched_label': '{safe_val}',"
        insert_pos = anchor_idx + 1
        lines = lines[:insert_pos] + [new_line] + lines[insert_pos:]
        updated += 1
        print(f"  ✓ '{lang}': face_enriched_label eklendi")

    I18N_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nTamamlandi: {updated} dile face_enriched_label eklendi.")


if __name__ == "__main__":
    run()
