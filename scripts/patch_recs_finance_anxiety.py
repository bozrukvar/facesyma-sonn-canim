"""
Patch assessment_recommendations.py:
 1. Add 'finance_anxiety' to every language block in _TEST_NAMES
 2. Add 'finance_anxiety' to _TEST_CONTEXT
 3. Add 'finance_anxiety' to _FALLBACK_SUPPLEMENT

Run: python scripts/patch_recs_finance_anxiety.py
"""
import re, pathlib

path = pathlib.Path(__file__).parent.parent / 'facesyma_backend/analysis_api/assessment_recommendations.py'
content = path.read_text(encoding='utf-8')

# ── 1. _TEST_NAMES — add after each 'finance': '...' entry ──────────────────

# Each language block ends with:   'finance': '<name>',  \n        },
# We'll insert 'finance_anxiety': '<name>' right after each 'finance' entry.

names = {
    'tr': 'Finansal Kaygı Profili',
    'en': 'Financial Anxiety Profile',
    'de': 'Finanzielle Angst Profil',
    'ru': 'Профиль финансовой тревоги',
    'ar': 'ملف القلق المالي',
    'es': 'Perfil de Ansiedad Financiera',
    'ko': '재무 불안 프로필',
    'ja': '財務不安プロフィール',
    'zh': '财务焦虑档案',
    'hi': 'वित्तीय चिंता प्रोफाइल',
    'fr': 'Profil d\'Anxiété Financière',
    'pt': 'Perfil de Ansiedade Financeira',
    'bn': 'আর্থিক উদ্বেগ প্রোফাইল',
    'id': 'Profil Kecemasan Finansial',
    'ur': 'مالی پریشانی پروفائل',
    'it': 'Profilo Ansia Finanziaria',
    'vi': 'Hồ sơ Lo lắng Tài chính',
    'pl': 'Profil Lęku Finansowego',
}

replaced = 0
for lang, name in names.items():
    # Match the 'finance': '<anything>', inside the language block
    # The pattern must be unique per language block — we'll use the surrounding context
    # Each lang block has: 'finance': '<val>', \n        },
    # We insert before the closing },
    pattern = rf"('finance': '[^']+',)\n        \}},"
    # This is too generic (would match all). Instead, find each exact 'finance': 'val' for this lang block.
    # Better approach: find the exact string for each language and add after it.
    finance_val = None
    # We need to find the finance entry in each lang block.
    # Each lang block is like:
    #   'tr': {
    #       ... 'finance': 'Finansal Zeka & Davranış Profili',
    #   },
    # We can find unique anchors per language block.

# ── Better approach: string replacement per unique anchor ───────────────────

# Each language's last entry in _TEST_NAMES is 'finance': '<val>', followed by \n        },
# We'll replace that pattern uniquely per language by using the known finance values.

lang_finance_values = {
    'tr': "'finance': 'Finansal Zeka & Davranış Profili',",
    'en': "'finance': 'Financial Intelligence & Behavior Profile',",
    'de': "'finance': 'Finanzielle Intelligenz & Verhaltensprofil',",
    'ru': "'finance': 'Финансовый интеллект и профиль поведения',",
    'ar': "'finance': 'الذكاء المالي وملف السلوك',",
    'es': "'finance': 'Inteligencia Financiera y Perfil de Comportamiento',",
    'ko': "'finance': '재무 지능 및 행동 프로필',",
    'ja': "'finance': '財務知能と行動プロフィール',",
    'zh': "'finance': '财务智能与行为档案',",
    'hi': "'finance': 'वित्तीय बुद्धिमत्ता और व्यवहार प्रोफाइल',",
    'fr': "'finance': 'Intelligence Financière & Profil Comportemental',",  # may differ
    'pt': "'finance': 'Inteligência Financeira e Perfil Comportamental',",
    'bn': "'finance': 'আর্থিক বুদ্ধিমত্তা ও আচরণ প্রোফাইল',",
    'id': "'finance': 'Kecerdasan Finansial & Profil Perilaku',",
    'ur': "'finance': 'مالیاتی ذہانت اور رویے کا پروفائل',",
    'it': "'finance': 'Intelligenza Finanziaria e Profilo Comportamentale',",
    'vi': "'finance': 'Trí tuệ Tài chính & Hồ sơ Hành vi',",
    'pl': "'finance': 'Inteligencja Finansowa i Profil Zachowania',",
}

# Find the actual values by regex
actual_values = {}
for m in re.finditer(r"'finance': '([^']+)',", content):
    val = m.group(1)
    actual_values[val] = m.start()

# Build replacement: for each lang, append finance_anxiety after finance entry
for lang, fa_name in names.items():
    old_val = lang_finance_values[lang]
    if old_val not in content:
        # Try to find actual finance value for this lang by proximity
        # Fall back: skip and report
        print(f'WARNING: could not find anchor for lang={lang}: {old_val[:60]}')
        continue
    new_val = old_val + f"\n            'finance_anxiety': '{fa_name}',"
    if f"'finance_anxiety': '{fa_name}'," in content:
        print(f'  {lang}: already present, skipping')
        continue
    # Only replace first occurrence (there should be only one per lang)
    content = content.replace(old_val, new_val, 1)
    replaced += 1
    print(f'  {lang}: inserted finance_anxiety name')

print(f'_TEST_NAMES: {replaced} languages patched')

# ── 2. _TEST_CONTEXT ─────────────────────────────────────────────────────────

context_anchor = "    'finance':           'Financial psychology & behavior assessment — measures savings behavior, risk tolerance, financial discipline, spending impulsivity, and long-term goal planning. Identifies profile: Saver, Risk-Taker, Balanced, or Impulsive Spender.',"
context_insert = "    'finance_anxiety':    'Financial anxiety assessment — measures anxiety-related worry (rumination, catastrophizing), avoidance behaviors (avoiding account checks, procrastinating bills), and financial shame. Identifies severity of financial anxiety.',"

if "'finance_anxiety':" in content and "Financial anxiety assessment" in content:
    print('_TEST_CONTEXT: finance_anxiety already present, skipping')
elif context_anchor in content:
    content = content.replace(context_anchor, context_anchor + '\n' + context_insert, 1)
    print('_TEST_CONTEXT: finance_anxiety inserted')
else:
    print(f'WARNING: _TEST_CONTEXT anchor not found:\n  {context_anchor[:80]}')

# ── 3. _FALLBACK_SUPPLEMENT ───────────────────────────────────────────────────

fallback_anchor = "    'finance': {\n        'tr': ["

fallback_new = """    'finance_anxiety': {
        'tr': ["Finansal kaygı, para ile ilişkinizi doğrudan etkiler — farkındalık ilk adımdır.", "Hesap ve faturaları düzenli kontrol etme alışkanlığı kaygıyı zamanla azaltır.", "Küçük bir acil durum fonu oluşturmak, belirsizlikten kaynaklanan kaygıyı önemli ölçüde düşürür.", "Geçmiş finansal hatalar için kendinizi affetmek, ilerlemenin önünü açar."],
        'en': ["Financial anxiety directly affects your relationship with money — awareness is the first step.", "Regularly checking accounts and bills gradually reduces anxiety over time.", "Building even a small emergency fund significantly reduces uncertainty-driven worry.", "Forgiving yourself for past financial mistakes opens the path forward."],
        'de': ["Finanzielle Angst beeinflusst direkt Ihre Beziehung zum Geld — Bewusstsein ist der erste Schritt.", "Das regelmäßige Überprüfen von Konten und Rechnungen reduziert die Angst schrittweise.", "Ein kleiner Notfallfonds reduziert unsicherheitsbedingte Sorgen erheblich.", "Sich selbst für vergangene Fehler zu verzeihen, öffnet den Weg nach vorne."],
        'ru': ["Финансовая тревога напрямую влияет на ваши отношения с деньгами — осознание — первый шаг.", "Регулярная проверка счетов и платежей постепенно снижает тревогу.", "Даже небольшой резервный фонд значительно уменьшает тревогу из-за неопределённости.", "Простить себя за прошлые финансовые ошибки открывает путь вперёд."],
        'ar': ["القلق المالي يؤثر مباشرة على علاقتك بالمال — الوعي هو الخطوة الأولى.", "المراجعة المنتظمة للحسابات والفواتير تقلل القلق تدريجياً.", "حتى صندوق طوارئ صغير يقلل بشكل ملحوظ من القلق الناجم عن عدم اليقين.", "مغفرة نفسك على الأخطاء المالية الماضية تفتح الطريق للأمام."],
        'es': ["La ansiedad financiera afecta directamente tu relación con el dinero — la conciencia es el primer paso.", "Revisar regularmente cuentas y facturas reduce la ansiedad con el tiempo.", "Incluso un pequeño fondo de emergencia reduce significativamente la preocupación por la incertidumbre.", "Perdonarte por errores financieros pasados abre el camino hacia adelante."],
        'ko': ["재정적 불안은 돈과의 관계에 직접적으로 영향을 미칩니다 — 인식이 첫 번째 단계입니다.", "계좌와 청구서를 정기적으로 확인하는 것이 시간이 지나면서 불안을 줄입니다.", "작은 비상 자금도 불확실성으로 인한 걱정을 크게 줄입니다.", "과거의 재정적 실수에 대해 스스로를 용서하는 것이 앞으로 나아가는 길을 엽니다."],
        'ja': ["財務不安はお金との関係に直接影響します — 意識することが最初のステップです。", "口座や請求書を定期的にチェックすることで不安が徐々に軽減されます。", "小さな緊急資金でも不確実性による心配を大幅に減らせます。", "過去の財務上のミスを自分に許すことが前進の道を開きます。"],
        'zh': ["财务焦虑直接影响您与金钱的关系——意识是第一步。", "定期检查账户和账单会随着时间的推移逐渐减轻焦虑。", "即使是小型应急基金也能显著减少因不确定性引发的担忧。", "原谅自己过去的财务错误，为未来打开道路。"],
        'hi': ["वित्तीय चिंता सीधे आपके पैसे के साथ संबंध को प्रभावित करती है — जागरूकता पहला कदम है।", "नियमित रूप से खाते और बिल जांचने से समय के साथ चिंता कम होती है।", "एक छोटा आपातकालीन फंड भी अनिश्चितता से उत्पन्न चिंता को काफी कम करता है।", "पिछली वित्तीय गलतियों के लिए खुद को माफ करना आगे बढ़ने का रास्ता खोलता है।"],
        'fr': ["L'anxiété financière affecte directement votre relation avec l'argent — la prise de conscience est la première étape.", "Vérifier régulièrement les comptes et les factures réduit progressivement l'anxiété.", "Même un petit fonds d'urgence réduit considérablement les inquiétudes liées à l'incertitude.", "Se pardonner pour les erreurs financières passées ouvre la voie à l'avenir."],
        'pt': ["A ansiedade financeira afeta diretamente sua relação com o dinheiro — a conscientização é o primeiro passo.", "Verificar regularmente contas e faturas reduz gradualmente a ansiedade.", "Mesmo um pequeno fundo de emergência reduz significativamente a preocupação com a incerteza.", "Perdoar-se pelos erros financeiros do passado abre o caminho para o futuro."],
        'bn': ["আর্থিক উদ্বেগ সরাসরি অর্থের সাথে আপনার সম্পর্ককে প্রভাবিত করে — সচেতনতাই প্রথম পদক্ষেপ।", "নিয়মিত অ্যাকাউন্ট ও বিল চেক করা সময়ের সাথে উদ্বেগ কমায়।", "একটি ছোট জরুরি তহবিলও অনিশ্চয়তাজনিত উদ্বেগ উল্লেখযোগ্যভাবে কমায়।", "অতীতের আর্থিক ভুলের জন্য নিজেকে ক্ষমা করা এগিয়ে যাওয়ার পথ খুলে দেয়।"],
        'id': ["Kecemasan finansial secara langsung memengaruhi hubungan Anda dengan uang — kesadaran adalah langkah pertama.", "Memeriksa rekening dan tagihan secara teratur secara bertahap mengurangi kecemasan.", "Bahkan dana darurat kecil pun mengurangi kekhawatiran akibat ketidakpastian secara signifikan.", "Memaafkan diri sendiri atas kesalahan keuangan masa lalu membuka jalan ke depan."],
        'ur': ["مالی پریشانی آپ کے پیسے سے تعلق پر براہ راست اثر ڈالتی ہے — آگاہی پہلا قدم ہے۔", "باقاعدگی سے اکاؤنٹس اور بل چیک کرنا وقت کے ساتھ پریشانی کم کرتا ہے۔", "ایک چھوٹا ہنگامی فنڈ بھی غیر یقینی صورتحال سے پیدا ہونے والی فکر کو نمایاں طور پر کم کرتا ہے۔", "ماضی کی مالی غلطیوں کے لیے خود کو معاف کرنا آگے بڑھنے کا راستہ کھولتا ہے۔"],
        'it': ["L'ansia finanziaria influenza direttamente il tuo rapporto con il denaro — la consapevolezza è il primo passo.", "Controllare regolarmente conti e bollette riduce gradualmente l'ansia.", "Anche un piccolo fondo di emergenza riduce significativamente le preoccupazioni legate all'incertezza.", "Perdonarsi per gli errori finanziari passati apre la strada al futuro."],
        'vi': ["Lo lắng tài chính ảnh hưởng trực tiếp đến mối quan hệ của bạn với tiền bạc — nhận thức là bước đầu tiên.", "Kiểm tra tài khoản và hóa đơn thường xuyên dần dần giảm lo lắng theo thời gian.", "Ngay cả một quỹ khẩn cấp nhỏ cũng giảm đáng kể lo lắng do sự không chắc chắn.", "Tha thứ cho bản thân vì những sai lầm tài chính trong quá khứ mở ra con đường tiến về phía trước."],
        'pl': ["Lęk finansowy bezpośrednio wpływa na twój stosunek do pieniędzy — świadomość jest pierwszym krokiem.", "Regularne sprawdzanie kont i rachunków stopniowo zmniejsza lęk.", "Nawet mały fundusz awaryjny znacznie redukuje niepokój wynikający z niepewności.", "Wybaczenie sobie przeszłych błędów finansowych otwiera drogę naprzód."],
    },\n"""

if "'finance_anxiety':" in content and "Financial anxiety directly affects" in content:
    print('_FALLBACK_SUPPLEMENT: finance_anxiety already present, skipping')
elif fallback_anchor in content:
    content = content.replace(fallback_anchor, fallback_new + '    ' + "'finance': {\n        'tr': [", 1)
    print('_FALLBACK_SUPPLEMENT: finance_anxiety inserted')
else:
    print(f'WARNING: _FALLBACK_SUPPLEMENT anchor not found')

path.write_text(content, encoding='utf-8')
print('Done.')
