"""
add_finance_disclaimer_i18n.py
==============================
Adds finance.disclaimer key to all 18 languages in i18n.ts.
Inserted after the 'finance.advice_invest_balanced' key in each language block.
"""

from pathlib import Path

I18N_FILE = Path(__file__).parent.parent / "facesyma_mobile" / "src" / "utils" / "i18n.ts"

DISCLAIMER: dict = {
    "tr": "Bu içerik yalnızca psikolojik farkındalık amaçlıdır. Yatırım tavsiyesi değildir. Finansal kararlarınız için lisanslı bir uzman danışın.",
    "en": "This content is for psychological awareness only. Not investment advice. Consult a licensed professional for financial decisions.",
    "de": "Dieser Inhalt dient nur der psychologischen Bewusstseinsbildung. Keine Anlageberatung. Konsultieren Sie für Finanzentscheidungen einen zugelassenen Fachmann.",
    "ru": "Этот контент предназначен только для психологического осознания. Не является инвестиционным советом. Для финансовых решений обратитесь к лицензированному специалисту.",
    "ar": "هذا المحتوى للتوعية النفسية فقط. ليس نصيحة استثمارية. استشر متخصصاً مرخصاً للقرارات المالية.",
    "es": "Este contenido es solo para concienciación psicológica. No es asesoramiento de inversión. Consulte a un profesional autorizado para decisiones financieras.",
    "ko": "이 콘텐츠는 심리적 인식 목적으로만 제공됩니다. 투자 조언이 아닙니다. 재무 결정을 위해 전문가와 상담하세요.",
    "ja": "このコンテンツは心理的認識を目的としたものです。投資アドバイスではありません。金融上の判断については、資格のある専門家にご相談ください。",
    "zh": "本内容仅用于心理意识。非投资建议。财务决策请咨询持牌专业人士。",
    "hi": "यह सामग्री केवल मनोवैज्ञानिक जागरूकता के लिए है। यह निवेश सलाह नहीं है। वित्तीय निर्णयों के लिए लाइसेंस प्राप्त पेशेवर से परामर्श करें।",
    "fr": "Ce contenu est uniquement a des fins de sensibilisation psychologique. Pas un conseil en investissement. Consultez un professionnel agree pour les decisions financieres.",
    "pt": "Este conteudo e apenas para conscientizacao psicologica. Nao e conselho de investimento. Consulte um profissional licenciado para decisoes financeiras.",
    "bn": "এই বিষয়বস্তু শুধুমাত্র মনোবৈজ্ঞানিক সচেতনতার জন্য। বিনিয়োগ পরামর্শ নয়। আর্থিক সিদ্ধান্তের জন্য লাইসেন্সপ্রাপ্ত পেশাদারের পরামর্শ নিন।",
    "id": "Konten ini hanya untuk kesadaran psikologis. Bukan saran investasi. Konsultasikan dengan profesional berlisensi untuk keputusan keuangan.",
    "ur": "یہ مواد صرف نفسیاتی بیداری کے لیے ہے۔ سرمایہ کاری کا مشورہ نہیں ہے۔ مالی فیصلوں کے لیے لائسنس یافتہ پیشہ ور سے مشورہ کریں۔",
    "it": "Questo contenuto e solo per la consapevolezza psicologica. Non e una consulenza sugli investimenti. Consulta un professionista autorizzato per le decisioni finanziarie.",
    "vi": "Noi dung nay chi danh cho nhan thuc tam ly. Khong phai tu van dau tu. Tham khao chuyen gia co phep cho quyet dinh tai chinh.",
    "pl": "Ta tresc sluzy wylacznie swiadomosci psychologicznej. Nie jest porada inwestycyjna. Skonsultuj sie z licencjonowanym specjalista w sprawach finansowych.",
}

ANCHOR = "'finance.advice_invest_balanced'"


def run():
    content = I18N_FILE.read_text(encoding="utf-8")
    lines = content.split("\n")
    updated = 0

    for lang, val in DISCLAIMER.items():
        lang_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{lang}:") and "{" in line:
                lang_idx = i
                break

        if lang_idx is None:
            print(f"  ✗ '{lang}' bloku bulunamadi")
            continue

        anchor_idx = None
        for i in range(lang_idx, min(lang_idx + 4000, len(lines))):
            if ANCHOR in lines[i]:
                anchor_idx = i
                break

        if anchor_idx is None:
            print(f"  ✗ '{lang}' icin anchor bulunamadi")
            continue

        block_text = "\n".join(lines[lang_idx:min(anchor_idx + 50, len(lines))])
        if "'finance.disclaimer'" in block_text:
            print(f"  - '{lang}': zaten mevcut")
            continue

        safe_val = val.replace("'", "\\'")
        new_line = f"    'finance.disclaimer': '{safe_val}',"
        insert_pos = anchor_idx + 1
        lines = lines[:insert_pos] + [new_line] + lines[insert_pos:]
        updated += 1
        print(f"  ✓ '{lang}': disclaimer eklendi")

    I18N_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nTamamlandi: {updated} dile disclaimer eklendi.")


if __name__ == "__main__":
    run()
