"""Add assessment.finance_anxiety + assessment.finance_anxiety_desc to all 18 language blocks."""
import pathlib

path = pathlib.Path(__file__).parent.parent / 'facesyma_mobile/src/utils/i18n.ts'
content = path.read_text(encoding='utf-8')

# Each entry: (anchor string, text to insert AFTER anchor)
# Anchor = 'assessment.finance_desc': '<value>', in each language block
inserts = [
    (
        "    'assessment.finance_desc': 'Para yönetimi ve finansal davranış analizi',",
        "    'assessment.finance_anxiety': 'Finansal Kaygı Profili',\n"
        "    'assessment.finance_anxiety_desc': 'Finansal kaygı, kaçınma ve utanç ölçümü',"
    ),
    (
        "    'assessment.finance_desc': 'Money management and financial behavior analysis',",
        "    'assessment.finance_anxiety': 'Financial Anxiety Profile',\n"
        "    'assessment.finance_anxiety_desc': 'Measures financial worry, avoidance, and shame',"
    ),
    (
        "    'assessment.finance_desc': 'Geldmanagement und Finanzverhalten',",
        "    'assessment.finance_anxiety': 'Finanzielle Angst Profil',\n"
        "    'assessment.finance_anxiety_desc': 'Misst finanzielle Sorgen, Vermeidung und Scham',"
    ),
    (
        "    'assessment.finance_desc': 'Управление деньгами и анализ финансового поведения',",
        "    'assessment.finance_anxiety': 'Профиль финансовой тревоги',\n"
        "    'assessment.finance_anxiety_desc': 'Измеряет финансовую тревогу, избегание и стыд',"
    ),
    (
        "    'assessment.finance_desc': 'تحليل إدارة المال والسلوك المالي',",
        "    'assessment.finance_anxiety': 'ملف القلق المالي',\n"
        "    'assessment.finance_anxiety_desc': 'يقيس القلق المالي والتجنب والخجل',"
    ),
    (
        "    'assessment.finance_desc': 'Análisis del comportamiento financiero y gestión del dinero',",
        "    'assessment.finance_anxiety': 'Perfil de Ansiedad Financiera',\n"
        "    'assessment.finance_anxiety_desc': 'Mide la preocupación, evitación y vergüenza financiera',"
    ),
    (
        "    'assessment.finance_desc': '돈 관리 및 재무 행동 분석',",
        "    'assessment.finance_anxiety': '재무 불안 프로필',\n"
        "    'assessment.finance_anxiety_desc': '재무 걱정, 회피 및 수치심 측정',"
    ),
    (
        "    'assessment.finance_desc': 'お金の管理と財務行動分析',",
        "    'assessment.finance_anxiety': '財務不安プロフィール',\n"
        "    'assessment.finance_anxiety_desc': '財務上の心配、回避、羞恥心を測定',"
    ),
    (
        "    'assessment.finance_desc': '金钱管理与财务行为分析',",
        "    'assessment.finance_anxiety': '财务焦虑档案',\n"
        "    'assessment.finance_anxiety_desc': '测量财务担忧、回避和羞耻感',"
    ),
    (
        "    'assessment.finance_desc': 'धन प्रबंधन और वित्तीय व्यवहार विश्लेषण',",
        "    'assessment.finance_anxiety': 'वित्तीय चिंता प्रोफाइल',\n"
        "    'assessment.finance_anxiety_desc': 'वित्तीय चिंता, परिहार और शर्म मापता है',"
    ),
    (
        "    'assessment.finance_desc': 'Gestion de l\\'argent et analyse du comportement financier',",
        "    'assessment.finance_anxiety': \"Profil d'Anxiété Financière\",\n"
        "    'assessment.finance_anxiety_desc': \"Mesure l'inquiétude, l'évitement et la honte financière\","
    ),
    (
        "    'assessment.finance_desc': 'Gestao do dinheiro e analise do comportamento financeiro',",
        "    'assessment.finance_anxiety': 'Perfil de Ansiedade Financeira',\n"
        "    'assessment.finance_anxiety_desc': 'Mede preocupação, evitação e vergonha financeira',"
    ),
    (
        "    'assessment.finance_desc': 'অর্থ ব্যবস্থাপনা ও আর্থিক আচরণ বিশ্লেষণ',",
        "    'assessment.finance_anxiety': 'আর্থিক উদ্বেগ প্রোফাইল',\n"
        "    'assessment.finance_anxiety_desc': 'আর্থিক উদ্বেগ, পরিহার এবং লজ্জা পরিমাপ করে',"
    ),
    (
        "    'assessment.finance_desc': 'Manajemen uang dan analisis perilaku keuangan',",
        "    'assessment.finance_anxiety': 'Profil Kecemasan Finansial',\n"
        "    'assessment.finance_anxiety_desc': 'Mengukur kekhawatiran, penghindaran, dan rasa malu finansial',"
    ),
    (
        "    'assessment.finance_desc': 'رقم کا انتظام اور مالی رویے کا تجزیہ',",
        "    'assessment.finance_anxiety': 'مالی پریشانی پروفائل',\n"
        "    'assessment.finance_anxiety_desc': 'مالی فکر، گریز اور شرم کی پیمائش کرتا ہے',"
    ),
    (
        "    'assessment.finance_desc': 'Gestione del denaro e analisi del comportamento finanziario',",
        "    'assessment.finance_anxiety': 'Profilo Ansia Finanziaria',\n"
        "    'assessment.finance_anxiety_desc': 'Misura preoccupazione, evitamento e vergogna finanziaria',"
    ),
    (
        "    'assessment.finance_desc': 'Quan ly tien bac va phan tich hanh vi tai chinh',",
        "    'assessment.finance_anxiety': 'Ho so Lo lang Tai chinh',\n"
        "    'assessment.finance_anxiety_desc': 'Do luong lo lang, tranh ne va xau ho tai chinh',"
    ),
    (
        "    'assessment.finance_desc': 'Zarzadzanie pieniezmi i analiza zachowan finansowych',",
        "    'assessment.finance_anxiety': 'Profil Leku Finansowego',\n"
        "    'assessment.finance_anxiety_desc': 'Mierzy niepokój finansowy, unikanie i wstyd',"
    ),
]

count = 0
for anchor, insertion in inserts:
    if 'assessment.finance_anxiety' in content and insertion.split('\n')[0] in content:
        # already inserted for this language
        continue
    if anchor in content:
        content = content.replace(anchor, anchor + '\n' + insertion, 1)
        count += 1
    else:
        print('NOT FOUND:', anchor[:70])

path.write_text(content, encoding='utf-8')
print(f'Done: {count}/18 languages updated')
