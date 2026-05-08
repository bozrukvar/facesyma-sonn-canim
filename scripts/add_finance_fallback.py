"""
add_finance_fallback.py
=======================
Adds 'finance' fallback recommendation entries to all 18 language blocks
in FALLBACK_RECOMMENDATIONS inside assessment_recommendations.py.

Inserts after the last existing test key ('stress' if present, else last key)
in each language block.
"""

from pathlib import Path
import re

TARGET = (
    Path(__file__).parent.parent
    / "facesyma_backend"
    / "analysis_api"
    / "assessment_recommendations.py"
)

FINANCE_FALLBACKS = {
    "tr": [
        "Finansal alışkanlıklarınızı fark etmek, değişimin ilk adımıdır.",
        "Tasarruf ve harcama dengenizi değerlendirerek önceliklerinizi netleştirin.",
        "Küçük, tutarlı finansal adımlar zamanla büyük fark yaratır.",
        "Finansal hedeflerinizi yazılı hale getirip düzenli gözden geçirin.",
    ],
    "en": [
        "Recognizing your financial habits is the first step toward change.",
        "Evaluate your savings and spending balance to clarify your priorities.",
        "Small, consistent financial steps make a big difference over time.",
        "Write down your financial goals and review them regularly.",
    ],
    "de": [
        "Ihre Finanzgewohnheiten zu erkennen ist der erste Schritt zur Veränderung.",
        "Bewerten Sie Ihre Spar- und Ausgabenbalance, um Prioritäten zu klären.",
        "Kleine, konsequente finanzielle Schritte machen im Laufe der Zeit einen großen Unterschied.",
        "Schreiben Sie Ihre finanziellen Ziele auf und überprüfen Sie sie regelmäßig.",
    ],
    "ru": [
        "Осознание своих финансовых привычек — первый шаг к переменам.",
        "Оцените баланс накоплений и расходов, чтобы определить приоритеты.",
        "Небольшие, последовательные финансовые шаги со временем дают большой результат.",
        "Запишите свои финансовые цели и регулярно пересматривайте их.",
    ],
    "ar": [
        "إدراك عاداتك المالية هو الخطوة الأولى نحو التغيير.",
        "قيّم توازن مدخراتك ونفقاتك لتوضيح أولوياتك.",
        "الخطوات المالية الصغيرة والمتسقة تحدث فرقاً كبيراً بمرور الوقت.",
        "اكتب أهدافك المالية وراجعها بانتظام.",
    ],
    "es": [
        "Reconocer tus hábitos financieros es el primer paso hacia el cambio.",
        "Evalúa tu balance entre ahorro y gasto para aclarar tus prioridades.",
        "Los pequeños pasos financieros consistentes marcan una gran diferencia con el tiempo.",
        "Escribe tus metas financieras y revísalas con regularidad.",
    ],
    "ko": [
        "재무 습관을 인식하는 것이 변화의 첫 번째 단계입니다.",
        "저축과 지출 균형을 평가하여 우선순위를 명확히 하세요.",
        "작고 꾸준한 재무적 단계가 시간이 지나면 큰 차이를 만듭니다.",
        "재무 목표를 적어두고 정기적으로 검토하세요.",
    ],
    "ja": [
        "財務習慣を認識することが変化への第一歩です。",
        "貯蓄と支出のバランスを評価し、優先事項を明確にしましょう。",
        "小さく一貫した財務的な行動が、長期的に大きな違いを生みます。",
        "財務目標を書き留め、定期的に見直しましょう。",
    ],
    "zh": [
        "认识自己的财务习惯是改变的第一步。",
        "评估储蓄与支出的平衡，明确您的优先事项。",
        "小而持续的财务行动随着时间推移会产生巨大变化。",
        "写下您的财务目标并定期回顾。",
    ],
    "hi": [
        "अपनी वित्तीय आदतों को पहचानना बदलाव की पहली कदम है।",
        "अपनी बचत और खर्च के संतुलन का मूल्यांकन करके प्राथमिकताएं स्पष्ट करें।",
        "छोटे, लगातार वित्तीय कदम समय के साथ बड़ा अंतर लाते हैं।",
        "अपने वित्तीय लक्ष्य लिखें और नियमित रूप से समीक्षा करें।",
    ],
    "fr": [
        "Reconnaitre vos habitudes financieres est la premiere etape du changement.",
        "Evaluez votre equilibre entre epargne et depenses pour clarifier vos priorites.",
        "De petits pas financiers constants font une grande difference avec le temps.",
        "Notez vos objectifs financiers et revisez-les regulierement.",
    ],
    "pt": [
        "Reconhecer seus habitos financeiros e o primeiro passo para a mudanca.",
        "Avalie seu equilibrio entre poupanca e gastos para esclarecer suas prioridades.",
        "Pequenos passos financeiros consistentes fazem grande diferenca ao longo do tempo.",
        "Escreva seus objetivos financeiros e revise-os regularmente.",
    ],
    "bn": [
        "আপনার আর্থিক অভ্যাস সম্পর্কে সচেতন হওয়াই পরিবর্তনের প্রথম পদক্ষেপ।",
        "সঞ্চয় ও ব্যয়ের ভারসাম্য মূল্যায়ন করে অগ্রাধিকার নির্ধারণ করুন।",
        "ছোট, ধারাবাহিক আর্থিক পদক্ষেপ সময়ের সাথে বড় পার্থক্য তৈরি করে।",
        "আপনার আর্থিক লক্ষ্য লিখে রাখুন এবং নিয়মিত পর্যালোচনা করুন।",
    ],
    "id": [
        "Mengenali kebiasaan finansial Anda adalah langkah pertama menuju perubahan.",
        "Evaluasi keseimbangan tabungan dan pengeluaran untuk memperjelas prioritas Anda.",
        "Langkah finansial kecil yang konsisten membuat perbedaan besar seiring waktu.",
        "Tuliskan tujuan finansial Anda dan tinjau secara berkala.",
    ],
    "ur": [
        "اپنی مالی عادات کو پہچاننا تبدیلی کی طرف پہلا قدم ہے۔",
        "بچت اور اخراجات کا توازن جانچ کر اپنی ترجیحات واضح کریں۔",
        "چھوٹے، مسلسل مالی اقدامات وقت کے ساتھ بڑا فرق پیدا کرتے ہیں۔",
        "اپنے مالی اہداف لکھیں اور انہیں باقاعدگی سے دیکھیں۔",
    ],
    "it": [
        "Riconoscere le proprie abitudini finanziarie e il primo passo verso il cambiamento.",
        "Valuta il tuo equilibrio tra risparmio e spesa per chiarire le tue priorita.",
        "Piccoli passi finanziari costanti fanno una grande differenza nel tempo.",
        "Scrivi i tuoi obiettivi finanziari e rivedili regolarmente.",
    ],
    "vi": [
        "Nhận ra thoi quen tai chinh cua ban la buoc dau tien de thay doi.",
        "Danh gia can bang tiet kiem va chi tieu de lam ro cac uu tien.",
        "Nhung buoc tai chinh nho, nhat quan tao ra su khac biet lon theo thoi gian.",
        "Viet ra cac muc tieu tai chinh va xem lai thuong xuyen.",
    ],
    "pl": [
        "Rozpoznanie swoich nawykow finansowych to pierwszy krok do zmiany.",
        "Ocen rownowaге miedzy oszczednoscia a wydatkami, aby wyklarowac priorytety.",
        "Male, konsekwentne kroki finansowe z czasem robi wielka roznice.",
        "Zapisz swoje cele finansowe i regularnie je przeglad.",
    ],
}


def run():
    content = TARGET.read_text(encoding="utf-8")
    updated = 0

    for lang, recs in FINANCE_FALLBACKS.items():
        # Check if already present
        pattern = rf"'{lang}':\s*{{[^}}]*'finance'"
        if re.search(pattern, content, re.DOTALL):
            print(f"  - '{lang}': zaten mevcut")
            continue

        # Build the finance line to insert
        items = ", ".join(f'"{r}"' for r in recs)
        finance_line = f"        'finance': [{items}],"

        # Find the lang block opening: '    'tr': {'  inside FALLBACK_RECOMMENDATIONS
        # We look for the pattern and find the closing brace of that block
        # Strategy: find '    '{lang}': {' and then find a line that is just '    },'
        lang_block_re = re.compile(
            rf"(    '{re.escape(lang)}':\s*\{{.*?)(    \}},?\n)",
            re.DOTALL,
        )
        m = lang_block_re.search(content)
        if not m:
            print(f"  ✗ '{lang}' blogu bulunamadi")
            continue

        # Insert before the closing brace of the lang block
        insert_at = m.start(2)  # position of the closing '    },'
        content = content[:insert_at] + finance_line + "\n" + content[insert_at:]
        updated += 1
        print(f"  ✓ '{lang}': finance fallback eklendi")

    TARGET.write_text(content, encoding="utf-8")
    print(f"\nTamamlandi: {updated} dile finance fallback eklendi.")


if __name__ == "__main__":
    run()
