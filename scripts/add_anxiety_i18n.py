"""Add financial_anxiety i18n keys to all 18 language blocks."""
path = 'c:/Users/asus.LAPTOP-V8BS7MTO/Desktop/facesyma-sonn-canim/facesyma_mobile/src/utils/i18n.ts'

with open(path, encoding='utf-8') as f:
    content = f.read()

inserts = [
    ("    'finance.domain_goals': 'Hedef Planlama',",
     "    'finance.domain_anxiety': 'Finansal Kaygı',\n"
     "    'finance.profile_anxious': 'Finansal Kaygılı',\n"
     "    'finance.advice_budget_anxious': 'Gelir ve giderlerini kağıda dök — bilinç, kaygıyı azaltır.',\n"
     "    'finance.advice_saving_anxious': 'Küçük ve otomatik bir tasarruf talimatı başlat. Küçük adımlar güven inşa eder.',\n"
     "    'finance.advice_invest_anxious': 'Düşük riskli araçlarla (mevduat, devlet tahvili) başla; bilgi arttıkça adım genişler.',"),
    ("    'finance.domain_goals': 'Goal Planning',",
     "    'finance.domain_anxiety': 'Financial Anxiety',\n"
     "    'finance.profile_anxious': 'Financially Anxious',\n"
     "    'finance.advice_budget_anxious': 'Write down your income and expenses — awareness reduces anxiety.',\n"
     "    'finance.advice_saving_anxious': 'Start small automated savings. Small steps build confidence.',\n"
     "    'finance.advice_invest_anxious': 'Begin with low-risk instruments (deposits, government bonds); grow as your knowledge grows.',"),
    ("    'finance.domain_goals': 'Zielplanung',",
     "    'finance.domain_anxiety': 'Finanzielle Angst',\n"
     "    'finance.profile_anxious': 'Finanziell Ängstlich',\n"
     "    'finance.advice_budget_anxious': 'Schreib Einnahmen und Ausgaben auf — Bewusstsein reduziert Angst.',\n"
     "    'finance.advice_saving_anxious': 'Starte kleine automatische Sparpläne. Kleine Schritte bauen Vertrauen auf.',\n"
     "    'finance.advice_invest_anxious': 'Beginne mit risikoarmen Anlagen (Einlagen, Staatsanleihen); erweitere schrittweise.',"),
    ("    'finance.domain_goals': 'Планирование целей',",
     "    'finance.domain_anxiety': 'Финансовая тревога',\n"
     "    'finance.profile_anxious': 'Финансово тревожный',\n"
     "    'finance.advice_budget_anxious': 'Запиши доходы и расходы — осознанность снижает тревогу.',\n"
     "    'finance.advice_saving_anxious': 'Начни с небольших автоматических сбережений. Маленькие шаги укрепляют уверенность.',\n"
     "    'finance.advice_invest_anxious': 'Начни с малорискованных инструментов (депозиты, гособлигации); расширяй по мере знаний.',"),
    ("    'finance.domain_goals': 'تخطيط الأهداف',",
     "    'finance.domain_anxiety': 'القلق المالي',\n"
     "    'finance.profile_anxious': 'قلق مالي',\n"
     "    'finance.advice_budget_anxious': 'دوّن دخلك ونفقاتك — الوعي يقلل القلق.',\n"
     "    'finance.advice_saving_anxious': 'ابدأ بادخار تلقائي صغير. الخطوات الصغيرة تبني الثقة.',\n"
     "    'finance.advice_invest_anxious': 'ابدأ بأدوات منخفضة المخاطر (ودائع، سندات حكومية)؛ وسّع مع زيادة معرفتك.',"),
    ("    'finance.domain_goals': 'Planificación de Metas',",
     "    'finance.domain_anxiety': 'Ansiedad Financiera',\n"
     "    'finance.profile_anxious': 'Financieramente Ansioso',\n"
     "    'finance.advice_budget_anxious': 'Escribe tus ingresos y gastos — la conciencia reduce la ansiedad.',\n"
     "    'finance.advice_saving_anxious': 'Inicia un ahorro automático pequeño. Los pequeños pasos construyen confianza.',\n"
     "    'finance.advice_invest_anxious': 'Empieza con instrumentos de bajo riesgo (depósitos, bonos del estado); amplía según tu conocimiento.',"),
    ("    'finance.domain_goals': '목표 계획',",
     "    'finance.domain_anxiety': '재정 불안',\n"
     "    'finance.profile_anxious': '재정적으로 불안한',\n"
     "    'finance.advice_budget_anxious': '수입과 지출을 적어보세요 — 인식이 불안을 줄입니다.',\n"
     "    'finance.advice_saving_anxious': '소액 자동 저축을 시작하세요. 작은 걸음이 자신감을 쌓습니다.',\n"
     "    'finance.advice_invest_anxious': '저위험 상품(예금, 국채)으로 시작해 지식이 늘면 넓혀가세요.',"),
    ("    'finance.domain_goals': '目標計画',",
     "    'finance.domain_anxiety': '財務不安',\n"
     "    'finance.profile_anxious': '財務的に不安',\n"
     "    'finance.advice_budget_anxious': '収入と支出を書き出しましょう — 意識が不安を和らげます。',\n"
     "    'finance.advice_saving_anxious': '小さな自動積立を始めましょう。小さな一歩が自信を築きます。',\n"
     "    'finance.advice_invest_anxious': '低リスクの商品（預金、国債）から始め、知識が増えたら広げましょう。',"),
    ("    'finance.domain_goals': '目标规划',",
     "    'finance.domain_anxiety': '财务焦虑',\n"
     "    'finance.profile_anxious': '财务焦虑型',\n"
     "    'finance.advice_budget_anxious': '把收入和支出写下来——意识能减轻焦虑。',\n"
     "    'finance.advice_saving_anxious': '开始小额自动储蓄。小步骤建立信心。',\n"
     "    'finance.advice_invest_anxious': '从低风险工具（存款、国债）开始；随着知识增长扩大投资。',"),
    ("    'finance.domain_goals': 'लक्ष्य नियोजन',",
     "    'finance.domain_anxiety': 'वित्तीय चिंता',\n"
     "    'finance.profile_anxious': 'वित्तीय रूप से चिंतित',\n"
     "    'finance.advice_budget_anxious': 'अपनी आय और खर्च लिखें — जागरूकता चिंता कम करती है।',\n"
     "    'finance.advice_saving_anxious': 'छोटी स्वचालित बचत शुरू करें। छोटे कदम आत्मविश्वास बनाते हैं।',\n"
     "    'finance.advice_invest_anxious': 'कम जोखिम वाले साधनों (जमा, सरकारी बॉन्ड) से शुरू करें; ज्ञान बढ़ने पर विस्तार करें।',"),
    ("    'finance.domain_goals': 'Planification des Objectifs',",
     "    'finance.domain_anxiety': 'Anxiété Financière',\n"
     "    'finance.profile_anxious': 'Financièrement Anxieux',\n"
     "    'finance.advice_budget_anxious': \"Notez vos revenus et dépenses — la conscience réduit l'anxiété.\",\n"
     "    'finance.advice_saving_anxious': 'Lancez une petite épargne automatique. Les petits pas renforcent la confiance.',\n"
     "    'finance.advice_invest_anxious': \"Commencez par des instruments à faible risque (dépôts, obligations d'État); élargissez avec la connaissance.\","),
    ("    'finance.domain_goals': 'Planejamento de Metas',",
     "    'finance.domain_anxiety': 'Ansiedade Financeira',\n"
     "    'finance.profile_anxious': 'Financeiramente Ansioso',\n"
     "    'finance.advice_budget_anxious': 'Anote suas receitas e despesas — a consciência reduz a ansiedade.',\n"
     "    'finance.advice_saving_anxious': 'Inicie uma poupança automática pequena. Pequenos passos constroem confiança.',\n"
     "    'finance.advice_invest_anxious': 'Comece com instrumentos de baixo risco (depósitos, títulos governamentais); amplie com o conhecimento.',"),
    ("    'finance.domain_goals': 'লক্ষ্য পরিকল্পনা',",
     "    'finance.domain_anxiety': 'আর্থিক উদ্বেগ',\n"
     "    'finance.profile_anxious': 'আর্থিকভাবে উদ্বিগ্ন',\n"
     "    'finance.advice_budget_anxious': 'আয় ও ব্যয় লিখুন — সচেতনতা উদ্বেগ কমায়।',\n"
     "    'finance.advice_saving_anxious': 'ছোট স্বয়ংক্রিয় সঞ্চয় শুরু করুন। ছোট পদক্ষেপ আত্মবিশ্বাস তৈরি করে।',\n"
     "    'finance.advice_invest_anxious': 'কম ঝুঁকির মাধ্যম (আমানত, সরকারি বন্ড) দিয়ে শুরু করুন; জ্ঞান বাড়লে প্রসারিত করুন।',"),
    ("    'finance.domain_goals': 'Perencanaan Tujuan',",
     "    'finance.domain_anxiety': 'Kecemasan Finansial',\n"
     "    'finance.profile_anxious': 'Cemas Secara Finansial',\n"
     "    'finance.advice_budget_anxious': 'Catat pendapatan dan pengeluaran Anda — kesadaran mengurangi kecemasan.',\n"
     "    'finance.advice_saving_anxious': 'Mulailah tabungan otomatis kecil. Langkah kecil membangun kepercayaan diri.',\n"
     "    'finance.advice_invest_anxious': 'Mulai dengan instrumen berisiko rendah (deposito, obligasi pemerintah); perluas seiring pengetahuan.',"),
    ("    'finance.domain_goals': 'ہدف کی منصوبہ بندی',",
     "    'finance.domain_anxiety': 'مالی پریشانی',\n"
     "    'finance.profile_anxious': 'مالی طور پر پریشان',\n"
     "    'finance.advice_budget_anxious': 'آمدنی اور اخراجات لکھیں — آگاہی پریشانی کم کرتی ہے۔',\n"
     "    'finance.advice_saving_anxious': 'چھوٹی خودکار بچت شروع کریں۔ چھوٹے قدم اعتماد بناتے ہیں۔',\n"
     "    'finance.advice_invest_anxious': 'کم خطرے والے آلات (ڈپازٹ، سرکاری بانڈ) سے شروع کریں؛ علم بڑھنے پر پھیلائیں۔',"),
    ("    'finance.domain_goals': 'Pianificazione degli Obiettivi',",
     "    'finance.domain_anxiety': 'Ansia Finanziaria',\n"
     "    'finance.profile_anxious': 'Finanziariamente Ansioso',\n"
     "    'finance.advice_budget_anxious': \"Annota entrate e uscite — la consapevolezza riduce l'ansia.\",\n"
     "    'finance.advice_saving_anxious': 'Avvia un piccolo risparmio automatico. I piccoli passi costruiscono fiducia.',\n"
     "    'finance.advice_invest_anxious': 'Inizia con strumenti a basso rischio (depositi, titoli di stato); espandi con la conoscenza.',"),
    ("    'finance.domain_goals': 'Lap ke hoach Muc tieu',",
     "    'finance.domain_anxiety': 'Lo Lắng Tài Chính',\n"
     "    'finance.profile_anxious': 'Lo Lắng Về Tài Chính',\n"
     "    'finance.advice_budget_anxious': 'Ghi lại thu nhập và chi tiêu — nhận thức giúp giảm lo lắng.',\n"
     "    'finance.advice_saving_anxious': 'Bắt đầu tiết kiệm tự động nhỏ. Những bước nhỏ xây dựng sự tự tin.',\n"
     "    'finance.advice_invest_anxious': 'Bắt đầu với công cụ rủi ro thấp (tiền gửi, trái phiếu chính phủ); mở rộng khi kiến thức tăng.',"),
    ("    'finance.domain_goals': 'Planowanie Celow',",
     "    'finance.domain_anxiety': 'Lęk Finansowy',\n"
     "    'finance.profile_anxious': 'Finansowo Niespokojny',\n"
     "    'finance.advice_budget_anxious': 'Zapisz dochody i wydatki — świadomość zmniejsza lęk.',\n"
     "    'finance.advice_saving_anxious': 'Uruchom małe automatyczne oszczędności. Małe kroki budują pewność siebie.',\n"
     "    'finance.advice_invest_anxious': 'Zacznij od niskoryzykownych instrumentów (depozyty, obligacje rządowe); rozszerzaj wraz z wiedzą.',"),
]

count = 0
for anchor, insertion in inserts:
    if anchor in content:
        content = content.replace(anchor, anchor + '\n' + insertion, 1)
        count += 1
    else:
        print('NOT FOUND:', anchor[:60])

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Done: {count}/18 languages updated')
