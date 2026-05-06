"""
assessment_recommendations.py
=============================
Generate personalized recommendations using Ollama LLM (local)

Takes assessment results and generates Turkish recommendations
based on domain scores and overall performance.
Uses local Ollama process via subprocess.
"""

import json
import logging
import subprocess
from functools import lru_cache
from typing import Dict, List

log = logging.getLogger(__name__)

# Ollama model to use (must be installed locally)
OLLAMA_MODEL = "mistral"  # Faster than llama2, good quality for Turkish

_REC_SKIP_MARKERS = (':', '**', '##', 'Assessment', 'Score', 'Domain')

_TEST_NAMES: dict = {
        'tr': {
            'skills': 'Beceri', 'hr': 'İK Yetkinliği', 'personality': 'Kişilik (Big Five)',
            'career': 'Kariyer Yeteneği', 'relationship': 'İlişki Dinamiği', 'vocation': 'Meslek Uyumu (Holland RIASEC)',
            'attachment': 'Bağlanma Stili', 'grit': 'Azim ve Kararlılık', 'growth_mindset': 'Büyüme Zihniyeti',
            'life_satisfaction': 'Yaşam Doyumu', 'self_compassion': 'Öz-Şefkat',
            'body_image': 'Beden İmgesi', 'self_efficacy': 'Öz-Yeterlik', 'stress': 'Algılanan Stres',
        },
        'en': {
            'skills': 'Skills Assessment', 'hr': 'HR Competencies', 'personality': 'Personality (Big Five)',
            'career': 'Career Aptitude', 'relationship': 'Relationship Dynamics', 'vocation': 'Vocational Fit (Holland RIASEC)',
            'attachment': 'Attachment Style', 'grit': 'Grit & Perseverance', 'growth_mindset': 'Growth Mindset',
            'life_satisfaction': 'Life Satisfaction', 'self_compassion': 'Self-Compassion',
            'body_image': 'Body Image', 'self_efficacy': 'Self-Efficacy', 'stress': 'Perceived Stress',
        },
        'de': {
            'skills': 'Fähigkeitentest', 'hr': 'HR-Kompetenzen', 'personality': 'Persönlichkeit (Big Five)',
            'career': 'Karrierefähigkeit', 'relationship': 'Beziehungsdynamik', 'vocation': 'Berufliche Eignung',
            'attachment': 'Bindungsstil', 'grit': 'Beharrlichkeit und Leidenschaft', 'growth_mindset': 'Wachstumsorientierung',
            'life_satisfaction': 'Lebenszufriedenheit', 'self_compassion': 'Selbstmitgefühl',
            'body_image': 'Körperbild', 'self_efficacy': 'Selbstwirksamkeit', 'stress': 'Wahrgenommener Stress',
        },
        'ru': {
            'skills': 'Оценка навыков', 'hr': 'HR компетенции', 'personality': 'Личность (Big Five)',
            'career': 'Карьерный потенциал', 'relationship': 'Динамика отношений', 'vocation': 'Профессиональное соответствие',
            'attachment': 'Стиль привязанности', 'grit': 'Настойчивость и увлечённость', 'growth_mindset': 'Установка на рост',
            'life_satisfaction': 'Удовлетворённость жизнью', 'self_compassion': 'Самосострадание',
            'body_image': 'Образ тела', 'self_efficacy': 'Самоэффективность', 'stress': 'Воспринимаемый стресс',
        },
        'ar': {
            'skills': 'تقييم المهارات', 'hr': 'كفاءات الموارد البشرية', 'personality': 'الشخصية (Big Five)',
            'career': 'القدرة المهنية', 'relationship': 'ديناميكية العلاقات', 'vocation': 'التوافق الوظيفي',
            'attachment': 'نمط التعلق', 'grit': 'المثابرة والشغف', 'growth_mindset': 'عقلية النمو',
            'life_satisfaction': 'الرضا عن الحياة', 'self_compassion': 'الرحمة بالذات',
            'body_image': 'صورة الجسم', 'self_efficacy': 'الكفاءة الذاتية', 'stress': 'الضغط المُدرَك',
        },
        'es': {
            'skills': 'Evaluación de habilidades', 'hr': 'Competencias RR.HH.', 'personality': 'Personalidad (Big Five)',
            'career': 'Aptitud profesional', 'relationship': 'Dinámicas relacionales', 'vocation': 'Ajuste vocacional',
            'attachment': 'Estilo de apego', 'grit': 'Perseverancia y Pasión', 'growth_mindset': 'Mentalidad de Crecimiento',
            'life_satisfaction': 'Satisfacción con la Vida', 'self_compassion': 'Autocompasión',
            'body_image': 'Imagen Corporal', 'self_efficacy': 'Autoeficacia', 'stress': 'Estrés Percibido',
        },
        'ko': {
            'skills': '기술 평가', 'hr': 'HR 역량', 'personality': '성격 (Big Five)',
            'career': '커리어 적성', 'relationship': '관계 역학', 'vocation': '직업 적합성',
            'attachment': '애착 유형', 'grit': '근성과 열정', 'growth_mindset': '성장 마인드셋',
            'life_satisfaction': '삶의 만족도', 'self_compassion': '자기 자비',
            'body_image': '신체 이미지', 'self_efficacy': '자기효능감', 'stress': '지각된 스트레스',
        },
        'ja': {
            'skills': 'スキル評価', 'hr': 'HR能力', 'personality': '性格（Big Five）',
            'career': 'キャリア適性', 'relationship': '関係ダイナミクス', 'vocation': '職業適合性',
            'attachment': '愛着スタイル', 'grit': '粘り強さと情熱', 'growth_mindset': 'グロースマインドセット',
            'life_satisfaction': '生活満足度', 'self_compassion': 'セルフ・コンパッション',
            'body_image': 'ボディイメージ', 'self_efficacy': '自己効力感', 'stress': '知覚されたストレス',
        },
        'zh': {
            'skills': '技能评估', 'hr': '人力资源能力', 'personality': '性格（Big Five）',
            'career': '职业能力', 'relationship': '关系动态', 'vocation': '职业适配度',
            'attachment': '依恋风格', 'grit': '坚毅与激情', 'growth_mindset': '成长型思维',
            'life_satisfaction': '生活满意度', 'self_compassion': '自我同情',
            'body_image': '身体意象', 'self_efficacy': '自我效能', 'stress': '感知压力',
        },
        'hi': {
            'skills': 'कौशल मूल्यांकन', 'hr': 'HR क्षमता', 'personality': 'व्यक्तित्व (Big Five)',
            'career': 'करियर योग्यता', 'relationship': 'संबंध गतिशीलता', 'vocation': 'व्यावसायिक फिट',
            'attachment': 'अटैचमेंट शैली', 'grit': 'दृढ़ता और जुनून', 'growth_mindset': 'विकास मानसिकता',
            'life_satisfaction': 'जीवन संतुष्टि', 'self_compassion': 'आत्म-करुणा',
            'body_image': 'शारीरिक छवि', 'self_efficacy': 'आत्म-प्रभावकारिता', 'stress': 'अनुभवित तनाव',
        },
        'fr': {
            'skills': 'Évaluation des compétences', 'hr': 'Compétences RH', 'personality': 'Personnalité (Big Five)',
            'career': 'Aptitude professionnelle', 'relationship': 'Dynamiques relationnelles', 'vocation': 'Adéquation professionnelle',
            'attachment': 'Style d\'attachement', 'grit': 'Persévérance et Passion', 'growth_mindset': 'État d\'esprit de croissance',
            'life_satisfaction': 'Satisfaction de vie', 'self_compassion': 'Auto-compassion',
            'body_image': 'Image corporelle', 'self_efficacy': 'Auto-efficacité', 'stress': 'Stress perçu',
        },
        'pt': {
            'skills': 'Avaliação de habilidades', 'hr': 'Competências RH', 'personality': 'Personalidade (Big Five)',
            'career': 'Aptidão profissional', 'relationship': 'Dinâmica de relacionamento', 'vocation': 'Adequação profissional',
            'attachment': 'Estilo de apego', 'grit': 'Persistência e Paixão', 'growth_mindset': 'Mentalidade de Crescimento',
            'life_satisfaction': 'Satisfação com a Vida', 'self_compassion': 'Autocompaixão',
            'body_image': 'Imagem Corporal', 'self_efficacy': 'Autoeficácia', 'stress': 'Estresse Percebido',
        },
        'bn': {
            'skills': 'দক্ষতা মূল্যায়ন', 'hr': 'এইচআর দক্ষতা', 'personality': 'ব্যক্তিত্ব (Big Five)',
            'career': 'ক্যারিয়ার যোগ্যতা', 'relationship': 'সম্পর্ক গতিশীলতা', 'vocation': 'পেশাদার ফিট',
            'attachment': 'সংযুক্তি শৈলী', 'grit': 'অধ্যবসায় ও আবেগ', 'growth_mindset': 'বৃদ্ধির মানসিকতা',
            'life_satisfaction': 'জীবন সন্তুষ্টি', 'self_compassion': 'আত্ম-করুণা',
            'body_image': 'শরীরের ছবি', 'self_efficacy': 'আত্ম-কার্যকারিতা', 'stress': 'অনুভূত চাপ',
        },
        'id': {
            'skills': 'Penilaian Keterampilan', 'hr': 'Kompetensi HR', 'personality': 'Kepribadian (Big Five)',
            'career': 'Aptitude Karir', 'relationship': 'Dinamika Hubungan', 'vocation': 'Kesesuaian Vokasional',
            'attachment': 'Gaya Kelekatan', 'grit': 'Ketekunan dan Semangat', 'growth_mindset': 'Pola Pikir Berkembang',
            'life_satisfaction': 'Kepuasan Hidup', 'self_compassion': 'Kasih Sayang Diri',
            'body_image': 'Citra Tubuh', 'self_efficacy': 'Efikasi Diri', 'stress': 'Stres yang Dirasakan',
        },
        'ur': {
            'skills': 'مہارت کی تشخیص', 'hr': 'HR صلاحیتیں', 'personality': 'شخصیت (Big Five)',
            'career': 'کیریئر کی صلاحیت', 'relationship': 'تعلق کی حرکیات', 'vocation': 'پیشہ ورانہ فٹ',
            'attachment': 'لگاؤ کا انداز', 'grit': 'استقامت اور جذبہ', 'growth_mindset': 'ترقی کی ذہنیت',
            'life_satisfaction': 'زندگی کا اطمینان', 'self_compassion': 'خود پر رحم',
            'body_image': 'جسمانی تصویر', 'self_efficacy': 'خود اعتمادی', 'stress': 'محسوس شدہ تناؤ',
        },
        'it': {
            'skills': 'Valutazione delle competenze', 'hr': 'Competenze RH', 'personality': 'Personalità (Big Five)',
            'career': 'Attitudine professionale', 'relationship': 'Dinamiche relazionali', 'vocation': 'Adeguatezza vocazionale',
            'attachment': 'Stile di attaccamento', 'grit': 'Perseveranza e Passione', 'growth_mindset': 'Mentalità di Crescita',
            'life_satisfaction': 'Soddisfazione di Vita', 'self_compassion': 'Autocompassione',
            'body_image': 'Immagine Corporea', 'self_efficacy': 'Autoefficacia', 'stress': 'Stress Percepito',
        },
        'vi': {
            'skills': 'Đánh giá kỹ năng', 'hr': 'Năng lực HR', 'personality': 'Tính cách (Big Five)',
            'career': 'Năng khiếu nghề nghiệp', 'relationship': 'Động lực quan hệ', 'vocation': 'Phù hợp nghề',
            'attachment': 'Phong cách gắn bó', 'grit': 'Kiên trì và Đam mê', 'growth_mindset': 'Tư duy phát triển',
            'life_satisfaction': 'Sự hài lòng cuộc sống', 'self_compassion': 'Lòng tự trắc ẩn',
            'body_image': 'Hình ảnh cơ thể', 'self_efficacy': 'Tự hiệu quả', 'stress': 'Căng thẳng cảm nhận',
        },
        'pl': {
            'skills': 'Ocena umiejętności', 'hr': 'Kompetencje HR', 'personality': 'Osobowość (Big Five)',
            'career': 'Uzdolnienie zawodowe', 'relationship': 'Dynamika relacji', 'vocation': 'Dopasowanie zawodowe',
            'attachment': 'Styl przywiązania', 'grit': 'Wytrwałość i Pasja', 'growth_mindset': 'Nastawienie na Wzrost',
            'life_satisfaction': 'Satysfakcja z Życia', 'self_compassion': 'Samowspółczucie',
            'body_image': 'Obraz Ciała', 'self_efficacy': 'Poczucie Własnej Skuteczności', 'stress': 'Postrzegany Stres',
        },
}

_TEST_CONTEXT: dict = {
    'personality':       'IPIP Big Five personality inventory — measures stable traits: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism.',
    'skills':            'Behavioral competency assessment (STAR format) — measures demonstrated abilities in problem-solving, empathy, organization, learning speed, and decision-making.',
    'hr':                'Workplace behavior style assessment — measures how the person acts in professional settings: leadership, teamwork, communication, stress tolerance, and motivation.',
    'career':            'Career interest inventory (Holland RIASEC role/environment) — measures which career roles and work environments the person aspires to.',
    'vocation':          'Vocational interest inventory (Holland SDS-R) — measures which specific activities the person genuinely enjoys doing.',
    'relationship':      'Relationship dynamics assessment — measures love language preferences, conflict style, intimacy needs, and relationship values.',
    'attachment':        'Adult attachment style (ECR-12, Lafontaine 2016) — measures anxiety (fear of abandonment) and avoidance (discomfort with closeness) dimensions.',
    'grit':              'Grit Scale (Duckworth & Quinn 2009) — measures perseverance of effort and consistency of passion over long-term goals.',
    'growth_mindset':    'Growth Mindset Scale (Dweck 2006) — measures belief that intelligence and abilities can be developed through effort and learning.',
    'life_satisfaction': 'Satisfaction with Life Scale / SWLS (Diener et al. 1985) — a global cognitive judgment of life satisfaction.',
    'self_compassion':   'Self-Compassion Scale Short Form / SCS-SF (Raes et al. 2011) — measures self-kindness, common humanity, and mindfulness toward oneself.',
    'self_efficacy':     'General Self-Efficacy Scale / GSE (Schwarzer & Jerusalem 1995) — measures confidence in one\'s ability to handle challenges.',
    'stress':            'Perceived Stress Scale / PSS-10 (Cohen et al. 1983) — measures the degree to which situations in one\'s life are perceived as stressful in the past month.',
    'body_image':        'Body image assessment (BSQ-8 adaptation, Cooper et al. 1987) — measures appearance evaluation and body satisfaction.',
}

_NARRATIVE_PROMPT = """You are a professional psychologist providing a personalized assessment interpretation.

Test: {test_name}
Scale context: {test_context}
Overall Score: {overall_score:.2f}/5.0

All domain scores:
{domains_text}

Top strengths: {top_domains}
Growth opportunity: {bottom_domains}

Write a personal 3-paragraph psychological profile in {lang_name}. Address the person directly as "you".

Paragraph 1 (2-3 sentences): Overall character profile — what kind of person do these scores suggest? Be specific and warm, not generic.
Paragraph 2 (2-3 sentences): Dive into their top strengths ({top_domains}). What does excelling here mean for how they think, relate, or work?
Paragraph 3 (2-3 sentences): Growth opportunity ({bottom_domains}). Frame it positively — what would developing this area unlock for them? Give one concrete action.

Rules:
- RESPOND ONLY IN {lang_name}. Do not use any other language.
- No bullet points. No headers. Plain flowing prose.
- Separate paragraphs with a blank line.
- Total: 6-9 sentences across 3 paragraphs.
- Be specific to the actual scores, not generic advice."""

_CAREER_NARRATIVE_PROMPT = """You are a career counselor providing a personalized career profile.

Test: {test_name}
Scale context: {test_context}
Overall Score: {overall_score:.2f}/5.0

All domain scores:
{domains_text}

Top strengths: {top_domains}
Lower areas: {bottom_domains}

Write a personal 3-paragraph career profile in {lang_name}. Address the person directly as "you".

Paragraph 1 (2-3 sentences): Career character summary — based on these scores, what kind of work environment, role type, and working style suits this person best?
Paragraph 2 (2-3 sentences): Name 4-6 specific job titles or career paths that align with their top domains ({top_domains}). Be concrete — say actual professions, not broad fields.
Paragraph 3 (2 sentences): One strength to lean into further and one concrete first step they can take this week toward exploring these careers.

Rules:
- RESPOND ONLY IN {lang_name}. Do not use any other language.
- No bullet points. No headers. Plain flowing prose.
- Separate paragraphs with a blank line.
- Total: 6-8 sentences across 3 paragraphs.
- Name real, specific job titles. Do not say "many careers" — say actual roles."""

_LANG_NAMES = {
    'tr': 'Turkish', 'en': 'English', 'de': 'German', 'ru': 'Russian',
    'ar': 'Arabic', 'es': 'Spanish', 'ko': 'Korean', 'ja': 'Japanese',
    'zh': 'Chinese', 'hi': 'Hindi', 'fr': 'French', 'pt': 'Portuguese',
    'bn': 'Bengali', 'id': 'Indonesian', 'ur': 'Urdu', 'it': 'Italian',
    'vi': 'Vietnamese', 'pl': 'Polish',
}

_PROMPTS: dict = {

        'tr': """Sen bir kariyer koçu ve gelişim mentörüsün. Bu değerlendirme sonuçlarına göre kişiselleştirilmiş, motive edici öneriler oluştur.

Değerlendirme Türü: {test_name}
Genel Puan: {overall_score:.2f}/5.0

Alan Puanları:
{domains_text}

3-4 öneri cümlesi oluştur:
1. En yüksek puanlı alanını daha da güçlendir
2. En düşük puanlı alanını geliştirmeye odaklan
3. Güçlü yönlerini kişisel gelişim için kullan
4. Somut ve pratik adımlar ver

Profesyonel ama sıcak bir tonla yaz. Cümle başına en fazla 15 kelime. "• " ile başla. Sadece öneriler, açıklama yok.""",

        'en': """You are a career coach and development mentor. Create personalized, motivating recommendations based on these assessment results.

Assessment Type: {test_name}
Overall Score: {overall_score:.2f}/5.0

Domain Scores:
{domains_text}

Create 3-4 recommendation sentences based on:
1. Strengthen your highest-scoring area
2. Focus on improving your lowest-scoring area
3. Use your strengths for personal development
4. Provide concrete, practical steps

Write in professional but warm tone. Max 15 words per sentence. Start each with "• ". Only recommendations, no explanations.""",

        'de': """Du bist ein Karriereberater und Entwicklungsmentor. Erstelle personalisierte, motivierende Empfehlungen basierend auf diesen Bewertungsergebnissen.

Bewertungstyp: {test_name}
Gesamtpunktzahl: {overall_score:.2f}/5.0

Domain-Werte:
{domains_text}

Erstelle 3-4 Empfehlungssätze basierend auf:
1. Stärke dein höchstbewertetes Gebiet weiter
2. Konzentriere dich auf die Verbesserung deines niedrigsten Bereichs
3. Nutze deine Stärken für deine Entwicklung
4. Gebe konkrete, praktische Schritte

Schreibe in professionellem aber warmem Ton. Max 15 Wörter pro Satz. Beginne mit "• ". Nur Empfehlungen.""",

        'ru': """Вы карьерный консультант и тренер по развитию. Создайте персонализированные, мотивирующие рекомендации на основе этих результатов оценки.

Тип оценки: {test_name}
Общая оценка: {overall_score:.2f}/5.0

Оценки по областям:
{domains_text}

Создайте 3-4 рекомендации на основе:
1. Усилить ваш самый высокий результат
2. Сосредоточиться на улучшении низкого результата
3. Использовать сильные стороны для развития
4. Дать конкретные практические шаги

Пишите в профессиональном, но теплом тоне. Макс 15 слов за предложение. Начните с "• ". Только рекомендации.""",

        'ar': """أنت مستشار مهني ومدرب تطوير. أنشئ توصيات مخصصة وملهمة بناءً على نتائج هذا التقييم.

نوع التقييم: {test_name}
النقاط الإجمالية: {overall_score:.2f}/5.0

درجات المجال:
{domains_text}

إنشاء 3-4 توصيات بناءً على:
1. تقوية أعلى مجال لديك
2. التركيز على تحسين أقل مجال
3. استخدام نقاطك القوية للتطوير
4. تقديم خطوات عملية محددة

اكتب بنبرة احترافية دافئة. أقصى 15 كلمة لكل جملة. ابدأ بـ "• ". التوصيات فقط.""",

        'es': """Eres entrenador de carrera y desarrollo. Crea recomendaciones personalizadas y motivadoras basadas en estos resultados de evaluación.

Tipo de evaluación: {test_name}
Puntuación general: {overall_score:.2f}/5.0

Puntuaciones de dominio:
{domains_text}

Crea 3-4 recomendaciones basadas en:
1. Fortalece tu área mejor puntuada
2. Enfócate en mejorar tu área más baja
3. Usa tus fortalezas para el desarrollo
4. Proporciona pasos prácticos concretos

Escribe en tono cálido y profesional. Máx 15 palabras por oración. Comienza con "• ". Solo recomendaciones.""",

        'ko': """당신은 커리어 코치이자 발전 멘토입니다. 이 평가 결과를 바탕으로 맞춤형, 동기부여 권장사항을 만드세요.

평가 유형: {test_name}
전체 점수: {overall_score:.2f}/5.0

도메인 점수:
{domains_text}

다음을 바탕으로 3-4개의 권장 문장을 만드세요:
1. 가장 높은 점수 영역을 강화
2. 가장 낮은 영역 개선에 집중
3. 강점을 개발에 활용
4. 구체적인 실용적 단계 제공

따뜻하고 전문적인 톤으로 작성하세요. 문장당 최대 15단어. "• "로 시작. 권장사항만 제시하세요.""",

        'ja': """あなたはキャリアコーチと開発メンターです。 これらの評価結果に基づいて、パーソナライズされた、やる気を引き出す推奨事項を作成してください。

評価タイプ: {test_name}
総合スコア: {overall_score:.2f}/5.0

ドメインスコア:
{domains_text}

以下に基づいて3～4つの推奨文を作成してください：
1. 最高スコア領域を強化
2. 最低領域の改善に注力
3. 強みを開発に活用
4. 具体的で実用的なステップを提供

温かくプロフェッショナルなトーンで書いてください。 1文最大15語。 「•」で開始。 推奨事項のみ。""",

        'zh': """你是职业顾问和发展导师。根据这些评估结果创建个性化、激励性的建议。

评估类型: {test_name}
总体分数: {overall_score:.2f}/5.0

域分数：
{domains_text}

根据以下内容创建3-4条建议：
1. 加强您最高评分的领域
2. 专注于改进您最低的领域
3. 利用您的优势进行发展
4. 提供具体实用的步骤

以温暖专业的语气写作。 每句最多15个单词。 以"•"开头。 仅建议。""",

        'hi': """आप एक करियर कोच और विकास सलाहकार हैं। इन मूल्यांकन परिणामों के आधार पर व्यक्तिगत, प्रेरक सिफारिशें बनाएं।

मूल्यांकन प्रकार: {test_name}
समग्र स्कोर: {overall_score:.2f}/5.0

डोमेन स्कोर:
{domains_text}

इसके आधार पर 3-4 सिफारिशें बनाएं:
1. अपने सर्वोच्च स्कोर वाले क्षेत्र को मजबूत करें
2. अपने निम्नतम क्षेत्र में सुधार पर ध्यान दें
3. विकास के लिए अपनी शक्तियों का उपयोग करें
4. ठोस व्यावहारिक कदम प्रदान करें

गर्म व्यावहारिक टोन में लिखें। प्रति वाक्य अधिकतम 15 शब्द। "•" से शुरू करें। केवल सिफारिशें।""",

        'fr': """Vous êtes un coach en carrière et développement. Créez des recommandations personnalisées et motivantes basées sur ces résultats d'évaluation.

Type d'évaluation: {test_name}
Score global: {overall_score:.2f}/5.0

Scores par domaine:
{domains_text}

Créez 3-4 recommandations basées sur:
1. Renforcez votre domaine le mieux noté
2. Concentrez-vous sur l'amélioration de votre domaine le plus faible
3. Utilisez vos forces pour le développement
4. Fournissez des étapes pratiques concrètes

Écrivez dans un ton chaud et professionnel. Max 15 mots par phrase. Commencez par "•". Recommandations uniquement.""",

        'pt': """Você é treinador de carreira e desenvolvimento. Crie recomendações personalizadas e motivadoras baseadas nesses resultados de avaliação.

Tipo de avaliação: {test_name}
Pontuação geral: {overall_score:.2f}/5.0

Pontuações por domínio:
{domains_text}

Crie 3-4 recomendações baseadas em:
1. Fortaleça sua área mais bem pontuada
2. Concentre-se em melhorar sua área mais baixa
3. Use seus pontos fortes para desenvolvimento
4. Forneça etapas práticas concretas

Escreva em tom profissional mas acolhedor. Máx 15 palavras por sentença. Comece com "•". Apenas recomendações.""",

        'bn': """আপনি একজন ক্যারিয়ার কোচ এবং উন্নয়ন পরামর্শদাতা। এই মূল্যায়ন ফলাফলের উপর ভিত্তি করে ব্যক্তিগত, অনুপ্রেরণামূলক সুপারিশ তৈরি করুন।

মূল্যায়ন প্রকার: {test_name}
সামগ্রিক স্কোর: {overall_score:.2f}/5.0

ডোমেইন স্কোর:
{domains_text}

এর উপর ভিত্তি করে 3-4 টি সুপারিশ তৈরি করুন:
1. আপনার সর্বোচ্চ স্কোর এলাকা শক্তিশালী করুন
2. আপনার সর্বনিম্ন এলাকা উন্নত করতে ফোকাস করুন
3. বিকাশের জন্য আপনার শক্তি ব্যবহার করুন
4. নির্দিষ্ট ব্যবহারিক পদক্ষেপ প্রদান করুন

উষ্ণ পেশাদার টোনে লিখুন। প্রতি বাক্যে সর্বাধিক 15 শব্দ। "•" দিয়ে শুরু করুন। শুধুমাত্র সুপারিশ।""",

        'id': """Anda adalah pelatih karir dan mentor pengembangan. Buat rekomendasi yang dipersonalisasi dan memotivasi berdasarkan hasil penilaian ini.

Jenis penilaian: {test_name}
Skor keseluruhan: {overall_score:.2f}/5.0

Skor domain:
{domains_text}

Buat 3-4 rekomendasi berdasarkan:
1. Perkuat area dengan skor tertinggi Anda
2. Fokus pada peningkatan area terendah Anda
3. Gunakan kekuatan Anda untuk pengembangan
4. Berikan langkah-langkah praktis yang konkret

Tulis dalam nada hangat dan profesional. Maks 15 kata per kalimat. Mulai dengan "•". Hanya rekomendasi.""",

        'ur': """آپ ایک کیریئر کوچ اور ترقیاتی مشیر ہیں۔ ان تشخیص کے نتائج کی بنیاد پر ذاتی نوعیت کی، حوصلہ افزا سفارشات بنائیں۔

تشخیص کی قسم: {test_name}
مجموعی اسکور: {overall_score:.2f}/5.0

ڈومین اسکور:
{domains_text}

اس کی بنیاد پر 3-4 سفارشات بنائیں:
1. اپنے سب سے زیادہ اسکور کے شعبے کو مضبوط کریں
2. اپنے سب سے کم شعبے کو بہتر بنانے پر توجہ دیں
3. ترقی کے لیے اپنی طاقتوں کا استعمال کریں
4. ٹھوس عملی اقدامات فراہم کریں

گرم پیشہ ورانہ انداز میں لکھیں۔ فی جملہ زیادہ سے زیادہ 15 الفاظ۔ "•" سے شروع کریں۔ صرف سفارشات۔""",

        'it': """Sei un allenatore di carriera e mentore di sviluppo. Crea raccomandazioni personalizzate e motivanti basate su questi risultati di valutazione.

Tipo di valutazione: {test_name}
Punteggio complessivo: {overall_score:.2f}/5.0

Punteggi per dominio:
{domains_text}

Crea 3-4 raccomandazioni in base a:
1. Rafforza la tua area con il punteggio più alto
2. Concentrati sul miglioramento della tua area più bassa
3. Usa i tuoi punti di forza per lo sviluppo
4. Fornisci passaggi pratici concreti

Scrivi in tono caldo e professionale. Max 15 parole per frase. Inizia con "•". Solo raccomandazioni.""",

        'vi': """Bạn là một huấn luyện viên sự nghiệp và cố vấn phát triển. Tạo các đề xuất được cá nhân hóa và có động lực dựa trên kết quả đánh giá này.

Loại đánh giá: {test_name}
Điểm tổng thể: {overall_score:.2f}/5.0

Điểm theo lĩnh vực:
{domains_text}

Tạo 3-4 đề xuất dựa trên:
1. Tăng cường lĩnh vực điểm cao nhất của bạn
2. Tập trung vào cải thiện lĩnh vực thấp nhất của bạn
3. Sử dụng sức mạnh của bạn để phát triển
4. Cung cấp các bước thực tế cụ thể

Viết bằng giọng ấm áp và chuyên nghiệp. Tối đa 15 từ mỗi câu. Bắt đầu bằng "•". Chỉ các đề xuất.""",

        'pl': """Jesteś trenerem karier i mentorem rozwoju. Utwórz spersonalizowane, motywujące rekomendacje na podstawie tych wyników oceny.

Typ oceny: {test_name}
Wynik ogólny: {overall_score:.2f}/5.0

Wyniki domeny:
{domains_text}

Utwórz 3-4 rekomendacje na podstawie:
1. Wzmocnij swój obszar z najwyższym wynikiem
2. Skup się na poprawie twojego obszaru najniższego
3. Wykorzystaj swoje mocne strony do rozwoju
4. Podaj konkretne praktyczne kroki

Pisz w ciepłym, profesjonalnym tonie. Maks 15 słów na zdanie. Zacznij od "•". Tylko rekomendacje.""",
}


_ATTACHMENT_STYLES: dict = {
    'tr': {
        'secure':   'Güvenli Bağlanma — ilişkilerde rahat, güvenen, dengeli',
        'anxious':  'Kaygılı Bağlanma — terk edilme kaygısı, onay ihtiyacı yüksek',
        'avoidant': 'Kaçıngan Bağlanma — duygusal mesafe, bağımsızlık ön planda',
        'fearful':  'Korkulu Bağlanma — hem yakınlık istiyor hem de korkuyor',
    },
    'en': {
        'secure':   'Secure Attachment — comfortable with intimacy, trusting, balanced',
        'anxious':  'Anxious Attachment — fear of abandonment, high need for reassurance',
        'avoidant': 'Avoidant Attachment — emotional distance, prioritizes independence',
        'fearful':  'Fearful Attachment — desires closeness but fears it simultaneously',
    },
    'de': {
        'secure':   'Sichere Bindung — wohl in Intimität, vertrauend, ausgeglichen',
        'anxious':  'Ängstliche Bindung — Verlassenheitsangst, hohes Bestätigungsbedürfnis',
        'avoidant': 'Vermeidende Bindung — emotionale Distanz, Unabhängigkeit im Vordergrund',
        'fearful':  'Ängstlich-vermeidende Bindung — wünscht Nähe, fürchtet sie zugleich',
    },
    'ru': {
        'secure':   'Надёжная привязанность — комфорт в близости, доверие, уравновешенность',
        'anxious':  'Тревожная привязанность — страх быть брошенным, высокая потребность в заверениях',
        'avoidant': 'Избегающая привязанность — эмоциональная дистанция, приоритет независимости',
        'fearful':  'Тревожно-избегающая привязанность — желает близости, но одновременно боится её',
    },
    'ar': {
        'secure':   'التعلق الآمن — مرتاح في الحميمية، ثقة، متوازن',
        'anxious':  'التعلق القلق — خوف من الهجر، حاجة عالية للطمأنينة',
        'avoidant': 'التعلق المتجنب — مسافة عاطفية، استقلالية في المقدمة',
        'fearful':  'التعلق المخيف — يرغب في القرب لكنه يخشاه في آن واحد',
    },
    'es': {
        'secure':   'Apego Seguro — cómodo con la intimidad, confiado, equilibrado',
        'anxious':  'Apego Ansioso — miedo al abandono, alta necesidad de reafirmación',
        'avoidant': 'Apego Evitativo — distancia emocional, prioriza la independencia',
        'fearful':  'Apego Temeroso — desea cercanía pero la teme simultáneamente',
    },
    'ko': {
        'secure':   '안정 애착 — 친밀감에 편안함, 신뢰, 균형',
        'anxious':  '불안 애착 — 유기 불안, 높은 확인 욕구',
        'avoidant': '회피 애착 — 정서적 거리두기, 독립성 우선',
        'fearful':  '두려움-회피 애착 — 친밀함을 원하지만 동시에 두려워함',
    },
    'ja': {
        'secure':   '安定型愛着 — 親密さに快適、信頼、バランス',
        'anxious':  '不安型愛着 — 見捨てられ不安、承認欲求が高い',
        'avoidant': '回避型愛着 — 感情的距離、独立性重視',
        'fearful':  '恐れ回避型愛着 — 親密さを望むが同時に恐れている',
    },
    'zh': {
        'personality': {
            'openness': {'high': '你的好奇心和想象力很强；新的经历和想法自然会吸引你。', 'moderate': '您平衡好奇心与实用性，在某些领域充满好奇，而在另一些领域则传统。', 'low': '你更喜欢实用、熟悉的东西；一致的惯例和经过验证的方法适合您。'},
            'conscientiousness': {'high': '你遵守纪律、有组织性、可靠；你系统地追求目标。', 'moderate': '您平衡责任和灵活性；建立例行公事将进一步加强这一点。', 'low': '你的风格灵活、随性；养成计划习惯可以提高你的效率。'},
            'extraversion': {'high': '你的社交能量很高；你从人们那里汲取力量，并为周围的人带来能量。', 'moderate': '您平衡与他人相处的时间和独处的时间，在两种环境中都感到舒适。', 'low': '你内向的性格是深入思考和专注工作的天然资产。'},
            'agreeableness': {'high': '你热情、合作的天性会在你们的人际关系中建立信任与和谐。', 'moderate': '你平衡合作与独立、理解与自信。', 'low': '你倾向于独立、批判性思维——这是分析和客观判断的优势。'},
            'neuroticism': {'high': '你的情绪反应可能会很激烈；压力管理和自我调节策略将为您提供支持。', 'moderate': '你会经历一些情绪的起伏；大多数时候你可以再次找到平衡。', 'low': '你的情绪恢复能力很强；你在压力下保持冷静，轻松处理困难。'},
        },
        'skills': {
            'problem_solving': {'high': '您擅长分析复杂问题并生成实用的解决方案。', 'moderate': '你解决问题的方法正在发展；结构化思维技巧可以为您提供支持。', 'low': '学习系统的解决问题的方法将释放你在这方面的潜力。'},
            'empathy': {'high': '您具有理解他人情绪并产生同理心的非凡能力。', 'moderate': '你的同理心能力正在发展；练习积极倾听将加强这一领域。', 'low': '更多地探索他人的观点将使你成为更有效的沟通者。'},
            'organization': {'high': '你的计划和优先顺序很明确；你井井有条的风格可以帮助你脱颖而出。', 'moderate': '你的组织能力合理；使用时间管理工具可以让你变得更强大。', 'low': '养成系统的组织习惯可以显着提高您的工作效率。'},
            'learning_speed': {'high': '您可以快速适应新的知识和技能——这是在不断变化的环境中的一个主要优势。', 'moderate': '你的学习节奏合理；尝试不同的策略可以提高你的效率。', 'low': '结构化的复习和练习策略将支持您在该领域的学习过程。'},
            'decision_making': {'high': '您可以在决策情况下采取果断、快速的步骤。', 'moderate': '您的决策能力正在发展；结构化框架在困难时刻提供帮助。', 'low': '从较小的决定开始是建立决策信心的有效方法。'},
        },
        'hr': {
            'leadership': {'high': '您擅长指导团队、激励他人和发挥领导作用。', 'moderate': '你有领导才能；实践经验将很快培养这些技能。', 'low': '通过实践刻意培养领导技能可以显着提升您的职业生涯。'},
            'team_fit': {'high': '您因和谐的团队合作、协作和乐于助人而脱颖而出。', 'moderate': '你的团队配合度很好；了解不同的工作方式将进一步加强这一点。', 'low': '更积极地参与团队动态将加强您的专业关系。'},
            'communication': {'high': '您擅长清晰、有效和建设性的沟通。', 'moderate': '你的沟通方式正在发展；适应不同的受众会给你带来优势。', 'low': '系统地练习沟通技巧将会在这方面带来快速的进步。'},
            'stress_tolerance': {'high': '你能在压力下保持冷静；专业韧性的基石。', 'moderate': '您的压力应对能力是合理的；恢复力建设技巧会让你变得更加强大。', 'low': '在日常实践的支持下制定压力管理策略可以快速产生结果。'},
            'motivation': {'high': '你的内在动机很高；您以承诺和热情实现您的目标。', 'moderate': '你的动机各不相同；与你的目标保持联系可以成为持续的能量来源。', 'low': '设定有意义的短期目标是重新激发动力的有效方法。'},
        },
        'career': {
            'analytical': {'high': '您对分析思维和以数据为中心的工作环境有着强烈的导向。', 'moderate': '你有分析倾向；结构化的问题解决实践将加强这一领域。', 'low': '发展系统的分析技能将扩大您在这个职业领域的选择。'},
            'creative': {'high': '您可以在富有创意和创新的工作环境中最好地表达自己。', 'moderate': '你有创作倾向；培养这个领域可以增加你的职业成就感。', 'low': '目前，结构性和技术性的职业道路似乎比以创意为中心的角色更加一致。'},
            'social': {'high': '帮助、教导或与人合作会让你充满活力。', 'moderate': '您对涉及社交互动的角色感到满意；更深层次的联系可以增加价值。', 'low': '目前，以社会为中心的职业道路并不是您的强烈兴趣领域。'},
            'entrepreneurial': {'high': '您非常倾向于担任需要领导力、说服力和冒险精神的创业角色。', 'moderate': '您的创业视角正在发展；决策和领导经验将加速这一过程。', 'low': '目前，以专业知识为中心的职业道路似乎比创业角色更加一致。'},
            'managerial': {'high': '您非常适合需要管理、协调和组织的角色。', 'moderate': '您的管理倾向正在发展；承担责任将培育这一领域。', 'low': '现在，以专业知识为中心、管理压力较小的职业道路可能会感觉更舒服。'},
            'technical': {'high': '您对技术和专业领域有浓厚的兴趣和方向。', 'moderate': '您的技术技能正在发展；深度专业化将加强这一领域。', 'low': '目前，以人为本的职业道路似乎比技术专家角色更加一致。'},
        },
        'vocation': {
            'realistic': {'high': '您对实际、动手和技术工作有强烈的倾向。', 'moderate': '您对实践工作具有中等兴趣；尝试这个区域会给你一个更清晰的认识。', 'low': '实践和技术活动目前并不是您的强烈兴趣。'},
            'investigative': {'high': '研究、分析和探索想法自然会吸引你。', 'moderate': '您有研究兴趣；加深该领域的知识将进一步加强它。', 'low': '以研究和分析为重点的活动目前不属于您的优先兴趣。'},
            'artistic': {'high': '您强烈倾向于需要创造性表达、艺术和美学的活动。', 'moderate': '你有艺术倾向；培育这个领域可以提供满足感和真实性。', 'low': '艺术和创意活动目前并不是您的强烈兴趣领域。'},
            'social': {'high': '与人相处、帮助和教导会让你充满活力。', 'moderate': '您对社交活动有中等兴趣；建立有意义的联系会带来满足感。', 'low': '以社交为中心的活动目前不属于您的优先兴趣。'},
            'enterprising': {'high': '在需要领导力、说服力和竞争的活动中，你感觉最强。', 'moderate': '你有进取心；实践责任和决策可以强化这一点。', 'low': '目前，竞争性和以领导力为中心的活动并不是您的强烈兴趣领域。'},
            'conventional': {'high': '您擅长组织、系统且规则一致的工作环境。', 'moderate': '您对组织和结构有中等兴趣；系统的工作实践培养了这一点。', 'low': '结构化和常规活动目前不是您的强烈兴趣领域。'},
        },
        'relationship': {
            'love_language': {'high': '你清楚地表达你的爱的语言，并重视人际关系中的相互理解。', 'moderate': 'You express your love language moderately;在这里更加开放可以丰富你的人际关系。', 'low': '培养情感表达和爱的语言的意识将加深你们的联系。'},
            'conflict_style': {'high': '您擅长以建设性且健康的方式解决冲突。', 'moderate': '你的冲突解决方式正在发展；尝试更具建设性的方法会有所帮助。', 'low': '制定健康的冲突解决策略将显着提高你们的关系质量。'},
            'intimacy_needs': {'high': '您清楚地了解自己对情感亲密和联系的需求。', 'moderate': '您对自己的亲密需求有中等程度的认识；进一步探索这一领域是有价值的。', 'low': '了解您的情感联系和亲密需求将使您的关系更加充实。'},
            'relationship_values': {'high': '对于你想要的人际关系有一个清晰的价值框架。', 'moderate': '你的人际关系价值观正在形成；反思这一点可以帮助您建立更健康的联系。', 'low': '发现并澄清你的个人关系价值观为更深层次的联系奠定了基础。'},
        },
        'attachment': {
            'anxiety': {'high': '对被遗弃的焦虑程度很高；这种意识是发展安全依恋的一个强有力的起点。', 'moderate': '依恋焦虑程度中等；安全关系实践支持这一领域。', 'low': '你的被遗弃焦虑程度较低；你在人际关系中表现出安全和平衡的依恋。'},
            'avoidance': {'high': '回避情感上的亲密是显而易见的；认识到这种模式是迈向更深层次联系的第一步。', 'moderate': '避免亲密接触的程度是中等的；随着自我意识的增强，你可以建立更开放的联系。', 'low': '您对情感亲密的回避程度较低；开放和联系使人在人际关系中感到舒适。'},
        },
        'grit': {
            'perseverance': {'high': '你有能力完成你开始的事情，并克服障碍继续前进。', 'moderate': '你的决心和毅力正在增强；致力于长期目标可以强化这一点。', 'low': '积累短期成功是培养可持续毅力的有效策略。'},
            'passion': {'high': '您对长期目标表现出一贯的热情和兴趣。', 'moderate': '你对目标的热情正在增强；与有意义的目标联系会增强这种能量。', 'low': '发现真正激发你兴趣的兴趣会激发你的热情和动力。'},
        },
        'growth_mindset': {
            'growth_mindset': {'high': '您坚信能力和智力可以通过努力来发展。', 'moderate': '你的成长心态正在发展；将挑战视为学习机会可以培养这一点。', 'low': '能力是固定的这一信念仍在继续；质疑这种心态会加速你的成长。'},
        },
        'life_satisfaction': {
            'life_satisfaction': {'high': '您对自己的生活表示高度满意，并做出总体积极的评价。', 'moderate': '您的生活满意度中等；加强意义与价值的一致性可以增加成就感。', 'low': '生活满意度低；问问自己想要改变什么是一个很好的起点。'},
        },
        'self_compassion': {
            'self_kindness': {'high': '你以慈悲和理解的态度对待自己；心理弹性的强大来源。', 'moderate': '你的自我同情心正在发展；在困难时刻像朋友一样与自己交谈可以培养这一点。', 'low': '内心的刺耳声音很突出；培养自我慈悲的做法将为你提供支持。'},
            'self_judgment': {'high': '存在过度自我批评的倾向；认识到这一点是变革的有力起点。', 'moderate': '自我批评是适度的；对自己更友善有时会带来好处。', 'low': '你对自己表现出平衡和友善的态度；自我评价的健康标志。'},
            'common_humanity': {'high': '你明白你的挣扎是人类共同经历的一部分，这会带来安慰。', 'moderate': '你们的共同人性意识正在发展；记住你并不孤单，这会增强你的力量。', 'low': '当困难出现时，你可能会感到孤立；请记住，这是一种非常常见的经历。'},
            'isolation': {'high': '在困难的时刻，你感到孤立无援；寻求联系和支持有助于平衡这一点。', 'moderate': '孤立感有时会出现；建立联系有助于平衡这一点。', 'low': '面对困难时，您会感到与他人有联系并受到支持；心理健康的重要标志。'},
            'mindfulness': {'high': '你可以用平衡和意识来观察你的情绪；健康的心理姿态。', 'moderate': '你的正念意识正在发展；简单的冥想练习将加强这个领域。', 'low': '有抑制情绪而不是观察情绪的倾向；正念练习可以提供支持。'},
            'overidentification': {'high': '有过度关注负面情绪和想法的倾向；正念练习打破了这个循环。', 'moderate': '有时你可能会过度认同消极的想法；平衡策略有帮助。', 'low': '您与消极想法保持健康的距离；正念意识的有力指标。'},
        },
        'self_efficacy': {
            'self_efficacy': {'high': '您坚信自己有能力完成具有挑战性的任务。', 'moderate': '您的自我效能信念正在发展；积累小成功会增强这种信心。', 'low': '对自己能力缺乏信心；通过小步骤积累成功经验会有所帮助。'},
        },
        'stress': {
            'perceived_stress': {'high': '您最近感到压力很大；压力管理策略现在尤其重要。', 'moderate': '您正承受中等程度的压力；识别和管理压力触发因素会带来好处。', 'low': '您的压力感知水平较低；你应对挑战的能力似乎很强。'},
        },
        'body_image': {
            'appearance_evaluation': {'high': '您对自己的外表总体评价是积极的；健康身体形象的标志。', 'moderate': "对你的外表评价褒贬不一；focusing on your body's functionality broadens perspective.", 'low': '人们倾向于对自己的外表做出负面评价；身体肯定实践在这里提供支持。'},
            'body_satisfaction': {'high': '您对自己的身体总体感到满意；健康自我接纳的标志。', 'moderate': '您的身体满意度中等；专注于身体的优势可以培养这个区域。', 'low': '你对自己的身体感到不满意；自我同情实践和专业支持可能是有益的。'},
        },
    },
    'hi': {
        'secure':   'सुरक्षित जुड़ाव — अंतरंगता में सहज, भरोसेमंद, संतुलित',
        'anxious':  'चिंतित जुड़ाव — छोड़े जाने का डर, आश्वासन की उच्च आवश्यकता',
        'avoidant': 'परिहारी जुड़ाव — भावनात्मक दूरी, स्वतंत्रता को प्राथमिकता',
        'fearful':  'भयभीत जुड़ाव — निकटता चाहता है लेकिन साथ ही डरता भी है',
    },
    'fr': {
        'secure':   "Attachement Sécure — à l'aise avec l'intimité, confiant, équilibré",
        'anxious':  "Attachement Anxieux — peur d'abandon, grand besoin de réassurance",
        'avoidant': "Attachement Évitant — distance émotionnelle, privilégie l'indépendance",
        'fearful':  "Attachement Craintif — désire la proximité mais la craint simultanément",
    },
    'pt': {
        'secure':   'Apego Seguro — confortável com intimidade, confiante, equilibrado',
        'anxious':  'Apego Ansioso — medo de abandono, alta necessidade de reasseguramento',
        'avoidant': 'Apego Evitativo — distância emocional, prioriza independência',
        'fearful':  'Apego Temeroso — deseja proximidade mas a teme simultaneamente',
    },
    'bn': {
        'secure':   'নিরাপদ সংযুক্তি — আন্তরিকতায় স্বাচ্ছন্দ্য, বিশ্বাসযোগ্য, সুষম',
        'anxious':  'উদ্বিগ্ন সংযুক্তি — পরিত্যক্ত হওয়ার ভয়, আশ্বাসের উচ্চ প্রয়োজন',
        'avoidant': 'পরিহারকারী সংযুক্তি — মানসিক দূরত্ব, স্বাধীনতাকে অগ্রাধিকার',
        'fearful':  'ভয়-পরিহারকারী সংযুক্তি — ঘনিষ্ঠতা চায় কিন্তু একসাথে ভয় পায়',
    },
    'id': {
        'secure':   'Kelekatan Aman — nyaman dengan keintiman, percaya, seimbang',
        'anxious':  'Kelekatan Cemas — takut ditinggalkan, butuh kepastian tinggi',
        'avoidant': 'Kelekatan Menghindar — jarak emosional, mengutamakan kemandirian',
        'fearful':  'Kelekatan Takut — menginginkan kedekatan tapi sekaligus takut',
    },
    'ur': {
        'secure':   'محفوظ لگاؤ — قربت میں آرام دہ، بھروسہ مند، متوازن',
        'anxious':  'پریشان لگاؤ — چھوڑے جانے کا خوف، یقین دہانی کی اعلی ضرورت',
        'avoidant': 'گریز کرنے والا لگاؤ — جذباتی فاصلہ، آزادی کو ترجیح',
        'fearful':  'خوفزدہ لگاؤ — قربت چاہتا ہے لیکن بیک وقت ڈرتا بھی ہے',
    },
    'it': {
        'secure':   "Attaccamento Sicuro — a proprio agio con l'intimità, fiducioso, equilibrato",
        'anxious':  "Attaccamento Ansioso — paura dell'abbandono, alto bisogno di rassicurazione",
        'avoidant': "Attaccamento Evitante — distanza emotiva, indipendenza in primo piano",
        'fearful':  "Attaccamento Timoroso — desidera la vicinanza ma la teme allo stesso tempo",
    },
    'vi': {
        'secure':   'Gắn bó An toàn — thoải mái với sự thân mật, tin tưởng, cân bằng',
        'anxious':  'Gắn bó Lo lắng — sợ bị bỏ rơi, nhu cầu cao được trấn an',
        'avoidant': 'Gắn bó Né tránh — khoảng cách cảm xúc, ưu tiên độc lập',
        'fearful':  'Gắn bó Sợ hãi — muốn sự gần gũi nhưng đồng thời sợ hãi',
    },
    'pl': {
        'secure':   'Bezpieczne Przywiązanie — swoboda z intymnością, ufność, równowaga',
        'anxious':  'Lękowe Przywiązanie — strach przed porzuceniem, duże zapotrzebowanie na zapewnienia',
        'avoidant': 'Unikające Przywiązanie — dystans emocjonalny, pierwszeństwo niezależności',
        'fearful':  'Lękowo-unikające Przywiązanie — pragnie bliskości, ale jednocześnie się jej boi',
    },
}


def _classify_attachment(breakdown: Dict) -> str:
    """Classify attachment style from anxiety + avoidance subscale scores."""
    anxiety  = breakdown.get('anxiety',  {}).get('score', 3.0)
    avoidance = breakdown.get('avoidance', {}).get('score', 3.0)
    if anxiety <= 2.5 and avoidance <= 2.5:
        return 'secure'
    elif anxiety > 3.0 and avoidance <= 2.5:
        return 'anxious'
    elif avoidance > 3.0 and anxiety <= 2.5:
        return 'avoidant'
    else:
        return 'fearful'


def _compute_spotlight(breakdown: Dict) -> Dict:
    """Return top 2 strengths and bottom 2 growth areas from breakdown scores."""
    scored = [(d, float(s.get('score', 0))) for d, s in breakdown.items()]
    scored.sort(key=lambda x: x[1], reverse=True)
    strengths    = [{'name': d, 'score': round(s, 2)} for d, s in scored[:2]]
    growth_areas = [{'name': d, 'score': round(s, 2)} for d, s in scored[-2:] if s < 4.0]
    return {'strengths': strengths, 'growth_areas': growth_areas}


def _generate_prompt(test_type: str, breakdown: Dict, overall_score: float, lang: str = 'tr') -> str:
    """Generate narrative prompt for Ollama — single template, 18 language output."""

    lang = lang.split('-')[0].lower() if lang else 'tr'
    lang_name = _LANG_NAMES.get(lang, 'English')

    test_names = _TEST_NAMES.get(lang, _TEST_NAMES['en'])
    test_name = test_names.get(test_type, test_type)

    # Attachment style: two-dimensional classification
    if test_type == 'attachment':
        style_key = _classify_attachment(breakdown)
        styles    = _ATTACHMENT_STYLES.get(lang, _ATTACHMENT_STYLES['en'])
        style_str = styles.get(style_key, style_key)
        anxiety_score   = breakdown.get('anxiety',  {}).get('score', 0)
        avoidance_score = breakdown.get('avoidance', {}).get('score', 0)
        domains_text = (
            f"• anxiety: {anxiety_score:.2f}/5.0\n"
            f"• avoidance: {avoidance_score:.2f}/5.0\n"
            f"• attachment style: {style_str}"
        )
        top_domains    = style_str
        bottom_domains = style_str
    else:
        domains_text = "\n".join([
            f"• {domain}: {scores.get('score', 0):.2f}/5.0 ({scores.get('level', scores.get('level_tr', ''))})"
            for domain, scores in breakdown.items()
        ])
        scored = sorted(breakdown.items(), key=lambda x: x[1].get('score', 0), reverse=True)
        top_domains    = ', '.join(d for d, _ in scored[:2])
        bottom_domains = ', '.join(d for d, _ in scored[-2:])

    test_context = _TEST_CONTEXT.get(test_type, '')

    prompt_template = (
        _CAREER_NARRATIVE_PROMPT
        if test_type in ('career', 'vocation')
        else _NARRATIVE_PROMPT
    )

    return prompt_template.format(
        test_name=test_name,
        test_context=test_context,
        overall_score=overall_score,
        domains_text=domains_text,
        top_domains=top_domains,
        bottom_domains=bottom_domains,
        lang_name=lang_name,
    )


def _call_ollama_local(prompt: str, max_tokens: int = 300) -> str | None:
    """Call Ollama locally via subprocess."""
    _logwarn = log.warning
    try:
        # Use subprocess to call ollama
        process = subprocess.run(
            ['ollama', 'run', OLLAMA_MODEL],
            input=prompt.encode('utf-8'),
            capture_output=True,
            timeout=90,  # Increased timeout for LLM generation
            text=False
        )

        if process.returncode == 0:
            return process.stdout.decode('utf-8', errors='ignore').strip()
        else:
            _logwarn(f'Ollama returned error: {process.stderr.decode("utf-8", errors="ignore")}')
            return None

    except FileNotFoundError:
        _logwarn('Ollama not found in PATH. Install ollama or add to PATH.')
        return None
    except subprocess.TimeoutExpired:
        _logwarn('Ollama subprocess timed out')
        return None
    except Exception as e:
        _logwarn(f'Ollama subprocess error: {e}')
        return None


def _parse_recommendations(text: str) -> List[str]:
    """Parse recommendations from Ollama output."""
    if not text:
        return []

    lines = text.split('\n')
    recommendations = []
    _rappend = recommendations.append

    for line in lines:
        line = line.strip()
        # Look for lines starting with bullet point
        if line.startswith('•'):
            rec = line[1:].strip()
            if rec:  # Only add non-empty recommendations
                _rappend(rec)
        elif line and not any(c in line for c in _REC_SKIP_MARKERS):
            # Also accept other short lines that look like recommendations
            if 10 < len(line) < 150 and line[0].isupper():
                _rappend(line)

    return recommendations[:4]  # Return max 4 recommendations


_DOMAIN_DESCRIPTIONS: dict = {
    'tr': {
        'personality': {
            'openness':          {'high': 'Merak ve hayal gücünüz güçlü; yeni deneyimler ve fikirler sizi doğal olarak çekiyor.', 'moderate': 'Bazı alanlarda meraklı, bazılarında alışılageldik yaklaşımları tercih ediyorsunuz.', 'low': 'Pratik ve tutarlı bir yapınız var; rutin ve alışıldık ortamlarda güvenli hissediyorsunuz.'},
            'conscientiousness': {'high': 'Disiplinli, planlı ve güvenilirsiniz; hedeflerinizi sistematik biçimde takip edersiniz.', 'moderate': 'Sorumluluk ve esneklik arasında denge kuruyorsunuz; rutin oluşturmak sizi daha da güçlendirir.', 'low': 'Esnek ve spontane bir yapınız var; planlama alışkanlıkları geliştirmek verimliliğinizi artırabilir.'},
            'extraversion':      {'high': 'Sosyal enerjiniz yüksek; insanlarla etkileşimden güç alıyor ve çevrenizi canlandırıyorsunuz.', 'moderate': 'Sosyal ve yalnız zamana olan ihtiyacınız arasında denge kurabiliyorsunuz.', 'low': 'İçe dönük yapınız derin düşünce ve odak için doğal bir avantaj sağlıyor.'},
            'agreeableness':     {'high': 'Sıcakkanlı ve iş birliğine açık yapınız çevrenizde güven ve uyum oluşturuyor.', 'moderate': 'İş birliğine yatkınsınız; hem anlayışlı hem bağımsız bir denge sergiliyorsunuz.', 'low': 'Bağımsız ve eleştirel düşünceye yatkınsınız; bu güçlü bir analitik bakış açısı sağlar.'},
            'neuroticism':       {'high': 'Duygusal tepkileriniz güçlü olabiliyor; stres yönetimi ve öz-düzenleme stratejileri size destek olacaktır.', 'moderate': 'Duygusal dalgalanmalar yaşayabiliyorsunuz; çoğu zaman denge noktanızı yeniden bulabiliyorsunuz.', 'low': 'Duygusal dayanıklılığınız güçlü; baskı altında sakin kalıyor ve zorlu durumları kolaylıkla atlatıyorsunuz.'},
        },
        'skills': {
            'problem_solving':  {'high': 'Karmaşık sorunları analiz etme ve pratik çözümler üretme konusunda güçlüsünüz.', 'moderate': 'Problem çözme yaklaşımınız gelişiyor; yapılandırılmış düşünme teknikleri size destek olabilir.', 'low': 'Sistematik problem çözme yöntemleri öğrenmek bu alandaki potansiyelinizi açığa çıkaracak.'},
            'empathy':          {'high': 'Başkalarının duygularını anlama ve empati kurma konusunda etkileyici bir yeteneğiniz var.', 'moderate': 'Empati becerileriniz gelişiyor; aktif dinleme pratiği bu alanı güçlendirir.', 'low': 'Başkalarının bakış açısını daha fazla keşfetmek sizi daha etkili bir iletişimci yapacak.'},
            'organization':     {'high': 'Planlamanız ve önceliklendirmeniz güçlü; düzenli yapınız sizi öne çıkarıyor.', 'moderate': 'Organizasyon beceriniz makul; zaman yönetimi araçları kullanmak sizi daha da güçlendirir.', 'low': 'Sistematik organizasyon alışkanlıkları geliştirmek verimliliğinizi önemli ölçüde artırabilir.'},
            'learning_speed':   {'high': 'Yeni bilgi ve becerilere hızlı adapte oluyorsunuz; bu değişen ortamlarda büyük avantaj.', 'moderate': 'Öğrenme hızınız makul; farklı öğrenme stratejilerini deneyerek etkinliğinizi artırabilirsiniz.', 'low': 'Öğrenme sürecini desteklemek için yapılandırılmış tekrar ve pratik stratejiler faydalı olacak.'},
            'decision_making':  {'high': 'Karar alma süreçlerinde kararlı ve hızlı adımlar atabiliyorsunuz.', 'moderate': 'Karar verme becerileriniz gelişiyor; zor durumlarda yapılandırılmış çerçeveler yardımcı olur.', 'low': 'Karar alma kasını güçlendirmek için küçük kararlardan başlamak etkili bir başlangıç noktasıdır.'},
        },
        'hr': {
            'leadership':       {'high': 'Ekibe yön verme, ilham katma ve liderlik etme konusunda güçlüsünüz.', 'moderate': 'Liderlik yatkınlığınız var; pratik deneyimler bu becerilerinizi hızla geliştirir.', 'low': 'Liderlik becerilerini kasıtlı pratikle geliştirmek kariyer gelişiminize önemli katkı sağlar.'},
            'team_fit':         {'high': 'Ekip içinde uyumlu çalışma, iş birliği ve yardımseverlik konusunda öne çıkıyorsunuz.', 'moderate': 'Ekip uyumunuz iyi; farklı çalışma stillerini anlamak bu alanı daha da güçlendirir.', 'low': 'Ekip dinamiklerine daha aktif katılmak profesyonel ilişkilerinizi güçlendirecektir.'},
            'communication':    {'high': 'Açık, etkili ve yapıcı iletişim kurma konusunda güçlüsünüz.', 'moderate': 'İletişim tarzınız gelişiyor; farklı kitlelere uyarlama becerisi kazanmak size avantaj sağlar.', 'low': 'İletişim becerilerini sistematik pratikle geliştirmek bu alanda hızlı ilerleme sağlar.'},
            'stress_tolerance': {'high': 'Baskı altında sakinliğinizi koruyabiliyorsunuz; bu kariyer dayanıklılığının temel taşı.', 'moderate': 'Stresle başa çıkma kapasiteniz makul; dayanıklılık artırıcı teknikler sizi daha da güçlendirir.', 'low': 'Stres yönetimi stratejileri geliştirmek günlük pratiklerle desteklendiğinde hızlı sonuç verir.'},
            'motivation':       {'high': 'İçsel motivasyonunuz yüksek; hedeflerinize bağlılık ve tutku ile yaklaşıyorsunuz.', 'moderate': 'Motivasyonunuz duruma göre değişiyor; amacınızla bağlantıda kalmak sürekli enerji kaynağı olabilir.', 'low': 'Anlamlı kısa vadeli hedefler belirlemek motivasyonu yeniden ateşlemenin etkili bir yolu.'},
        },
        'career': {
            'analytical':       {'high': 'Analitik düşünce ve veri odaklı çalışma ortamlarında güçlü bir yönelim var.', 'moderate': 'Analitik eğilimleriniz var; yapılandırılmış problem çözme pratiği bu alanı güçlendirir.', 'low': 'Sistematik analiz becerileri geliştirmek bu kariyer alanındaki seçeneklerinizi genişletir.'},
            'creative':         {'high': 'Yaratıcı ve yenilikçi çalışma ortamlarında kendinizi en iyi şekilde ifade ediyorsunuz.', 'moderate': 'Yaratıcı yönleriniz var; bu alanı beslemek kariyer doyumunuzu artırabilir.', 'low': 'Yapısal ve teknik kariyer yolları şu an yaratıcı odaklı rollerden daha uyumlu gözüküyor.'},
            'social':           {'high': 'İnsanlara yardım etmek, eğitmek veya onlarla çalışmak sizi güçlendiriyor.', 'moderate': 'Sosyal etkileşim içeren rollerde rahatsınız; daha derin bağlantılar değer katabilir.', 'low': 'Sosyal odaklı kariyer yolları şu an güçlü bir ilgi alanınız değil.'},
            'entrepreneurial':  {'high': 'Liderlik, ikna ve risk alma gerektiren girişimci rollere güçlü bir yatkınlık var.', 'moderate': 'Girişimci bakış açınız gelişiyor; karar verme ve liderlik deneyimi bu alanı hızla güçlendirir.', 'low': 'Uzmanlık odaklı kariyer yolları girişimci rollerden şu an daha uyumlu gözüküyor.'},
            'managerial':       {'high': 'Yönetim, koordinasyon ve organizasyon gerektiren rollere güçlü bir uyum var.', 'moderate': 'Yönetim eğilimleriniz gelişiyor; sorumluluk alma pratiği bu alanı besler.', 'low': 'Uzmanlık odaklı, yönetim sorumluluğu az olan kariyer yolları şu an daha konforlu gelebilir.'},
            'technical':        {'high': 'Teknik uzmanlık gerektiren alanlarda güçlü bir ilgi ve yönelim var.', 'moderate': 'Teknik becerileriniz gelişiyor; derinlemesine uzmanlaşma bu alanı güçlendirir.', 'low': 'İnsan odaklı kariyer yolları şu an teknik uzmanlık rollerinden daha uyumlu gözüküyor.'},
        },
        'vocation': {
            'realistic':        {'high': 'Pratik, elle yapılan ve teknik işlere güçlü bir yatkınlık var.', 'moderate': 'Uygulamalı çalışmaya orta düzey ilginiz var; bu alanı denemek daha net bir resim çizer.', 'low': 'Pratik ve teknik aktiviteler şu an güçlü ilgi alanlarınız değil.'},
            'investigative':    {'high': 'Araştırma, analiz ve fikir keşfetme aktiviteleri sizi doğal olarak çekiyor.', 'moderate': 'Araştırmacı ilginiz var; bilgi derinleştirmek bu alanı daha da güçlendirir.', 'low': 'Araştırma ve analiz odaklı aktiviteler şu an öncelikli ilgi alanlarınız değil.'},
            'artistic':         {'high': 'Yaratıcı ifade, sanat ve estetik gerektiren aktivitelere güçlü bir eğilim var.', 'moderate': 'Sanatsal yönleriniz var; bu alanı beslemek tatmin ve özgünlük sağlayabilir.', 'low': 'Sanatsal ve yaratıcı aktiviteler şu an güçlü bir ilgi alanınız değil.'},
            'social':           {'high': 'İnsanlarla birlikte olmak, yardım etmek ve öğretmek sizi canlandırıyor.', 'moderate': 'Sosyal aktivitelere orta düzey ilginiz var; anlamlı bağlantılar kurmak tatmin sağlar.', 'low': 'Sosyal odaklı aktiviteler şu an öncelikli ilgi alanlarınız değil.'},
            'enterprising':     {'high': 'Liderlik, ikna ve rekabet gerektiren aktivitelerde kendinizi en güçlü hissediyorsunuz.', 'moderate': 'Girişimci eğilimleriniz var; sorumluluk ve karar alma pratiği bu alanı güçlendirir.', 'low': 'Rekabetçi ve liderlik odaklı aktiviteler şu an güçlü bir ilgi alanınız değil.'},
            'conventional':     {'high': 'Düzenli, sistematik ve kurallara uygun çalışma ortamlarında güçlüsünüz.', 'moderate': 'Organizasyon ve düzene orta düzey ilginiz var; sistemli çalışma pratiği bu alanı besler.', 'low': 'Yapılandırılmış ve konvansiyonel aktiviteler şu an güçlü bir ilgi alanınız değil.'},
        },
        'relationship': {
            'love_language':        {'high': 'Sevgi dilinizi açık biçimde ifade ediyor ve karşılıklı anlayışa değer veriyorsunuz.', 'moderate': 'Sevgi dilinizi orta düzeyde ifade ediyorsunuz; bu alanda daha açık olmak ilişkilerinizi zenginleştirir.', 'low': 'Duygusal ifade ve sevgi dili farkındalığı geliştirmek ilişkilerinizi derinleştirir.'},
            'conflict_style':       {'high': 'Çatışmaları yapıcı ve sağlıklı yollarla çözme konusunda güçlüsünüz.', 'moderate': 'Çatışma çözüm tarzınız gelişiyor; anlaşmazlıklarda daha yapıcı yaklaşımlar deneyebilirsiniz.', 'low': 'Sağlıklı çatışma çözüm stratejileri geliştirmek ilişki kalitenizi önemli ölçüde artırır.'},
            'intimacy_needs':       {'high': 'Duygusal yakınlık ve bağlılık konusundaki ihtiyaçlarınızı net bir şekilde anlıyorsunuz.', 'moderate': 'Samimilik ihtiyaçlarınız hakkında orta düzeyde farkındalığınız var; bu alanı keşfetmek değerli.', 'low': 'Duygusal bağ ve yakınlık ihtiyaçlarınızı anlamak ilişkilerinizi daha tatmin edici kılar.'},
            'relationship_values':  {'high': 'İlişkilerinizde ne istediğinize dair net bir değer çerçeveniz var.', 'moderate': 'İlişki değerleriniz şekilleniyor; bu alanı düşünmek daha sağlıklı bağlar kurmanıza yardımcı olur.', 'low': 'Kişisel ilişki değerlerinizi keşfetmek daha derin bağlar kurmanıza zemin hazırlar.'},
        },
        'attachment': {
            'anxiety':   {'high': 'Terk edilme endişesi yüksek; bu farkındalık güvenli bağlanma geliştirmek için güçlü bir başlangıç.', 'moderate': 'Bağlanma kaygısı orta düzeyde; güvenli ilişki pratikleri bu alanı destekler.', 'low': 'Terk edilme kaygınız düşük; ilişkilerde güvenli ve dengeli bir bağlanma sergiliyorsunuz.'},
            'avoidance': {'high': 'Duygusal yakınlıktan kaçınma belirgin; bu stili tanımak daha derin bağlar için ilk adım.', 'moderate': 'Yakınlıktan kaçınma orta düzeyde; farkındalık arttıkça daha açık bağlantılar kurabilirsiniz.', 'low': 'Duygusal yakınlıktan kaçınma düşük; ilişkilerde açıklık ve bağlılık rahat hissettiriyor.'},
        },
        'grit': {
            'perseverance': {'high': 'Başladığınız şeyleri tamamlama ve zorluklar karşısında devam etme konusunda güçlüsünüz.', 'moderate': 'Kararlılık ve azim gelişiyor; uzun vadeli hedeflere bağlı kalmak bu alanı güçlendirir.', 'low': 'Sürdürülebilir azim geliştirmek için kısa vadeli başarılar biriktirmek etkili bir strateji.'},
            'passion':      {'high': 'Uzun vadeli hedeflerinize karşı tutarlı bir tutku ve ilgi sergiliyorsunuz.', 'moderate': 'Hedefe olan tutkunuz gelişiyor; anlamlı bir amaca bağlanmak bu enerjiyi artırır.', 'low': 'Kendinizi gerçekten ateşleyen ilgi alanlarını keşfetmek tutku ve motivasyonu besler.'},
        },
        'growth_mindset': {
            'growth_mindset': {'high': 'Yetenekler ve zekanın çaba ile geliştirilebileceğine güçlü bir şekilde inanıyorsunuz.', 'moderate': 'Büyüme zihniyetiniz gelişiyor; zorluklara öğrenme fırsatı gözüyle bakmak bu alanı besler.', 'low': 'Yeteneklerin sabit olduğuna dair inanç devam ediyor; bu zihniyeti sorgulamak gelişimi hızlandırır.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {'high': 'Yaşamınızdan yüksek düzeyde tatmin aldığınızı ve olumlu bir genel değerlendirme yaptığınızı gösteriyor.', 'moderate': 'Yaşam doyumunuz orta düzeyde; anlam ve değer uyumunu güçlendirmek doyumu artırır.', 'low': 'Yaşamdan alınan doyum düşük; kendinize hangi alanlarda değişiklik istediğinizi sormak iyi bir başlangıç.'},
        },
        'self_compassion': {
            'self_kindness':       {'high': 'Kendinize şefkatli ve anlayışlı yaklaşıyorsunuz; bu güçlü bir psikolojik dayanıklılık kaynağı.', 'moderate': 'Öz-şefkatiniz gelişiyor; zor anlarda kendinize bir dost gibi konuşmak bu alanı besler.', 'low': 'Kendinize sert bir iç ses ön planda; öz-şefkat pratikleri geliştirmek sizi destekleyecek.'},
            'self_judgment':       {'high': 'Kendinize karşı eleştirel bir tutum belirgin; bunu fark etmek değişim için güçlü bir başlangıç.', 'moderate': 'Öz-eleştiri orta düzeyde; bazen kendinize daha nazik olmak fayda sağlar.', 'low': 'Kendinize karşı dengeli ve nazik bir tutum sergiliyorsunuz; bu sağlıklı bir öz-değerlendirme göstergesi.'},
            'common_humanity':     {'high': 'Zorluklarınızın ortak insanlık deneyiminin parçası olduğunu anlıyor ve bu sizi rahatlatıyor.', 'moderate': 'Ortak insanlık duygunuz gelişiyor; zor anlarda yalnız olmadığınızı hatırlamak güçlendirir.', 'low': 'Zorluklar yaşandığında kendinizi izole hissedebiliyorsunuz; bu çok yaygın bir deneyim olduğunu hatırlayın.'},
            'isolation':           {'high': 'Zor anlarda kendinizi izole ve yalnız hissediyorsunuz; bağlantı ve destek arayışı bu duyguyu dengeler.', 'moderate': 'Zaman zaman izolasyon hissi yaşanabiliyor; bağlantı kurmak bu duyguyu dengeler.', 'low': 'Zorluklar karşısında bağlı ve desteklenmiş hissediyorsunuz; bu psikolojik sağlık için önemli.'},
            'mindfulness':         {'high': 'Duygularınızı dengeyle ve farkındalıkla gözlemleyebiliyorsunuz; bu sağlıklı bir psikolojik tutum.', 'moderate': 'Bilinçli farkındalığınız gelişiyor; basit meditasyon pratikleri bu alanı güçlendirir.', 'low': 'Duyguları gözlemlemek yerine bastırma eğilimi var; farkındalık pratikleri destek sağlayabilir.'},
            'overidentification':  {'high': 'Olumsuz duygu ve düşüncelere aşırı odaklanma eğilimi var; farkındalık pratikleri bu döngüyü kırar.', 'moderate': 'Zaman zaman olumsuz düşüncelerle aşırı özdeşleşebiliyorsunuz; denge stratejileri yardımcı olur.', 'low': 'Olumsuz düşüncelerle sağlıklı bir mesafe koruyabiliyorsunuz; bu güçlü bir bilinçli farkındalık göstergesi.'},
        },
        'self_efficacy': {
            'self_efficacy': {'high': 'Kendinizi zorlayan görevlerin üstesinden gelebileceğinize güçlü bir inancınız var.', 'moderate': 'Öz-yeterlik inancınız gelişiyor; küçük başarılar biriktirmek bu güveni artırır.', 'low': 'Kendi yeteneklerinize olan güven düşük; küçük adımlarla başarı deneyimleri oluşturmak yardımcı olur.'},
        },
        'stress': {
            'perceived_stress': {'high': 'Son dönemde yüksek düzeyde stres algılıyorsunuz; stres yönetimi stratejileri bu dönemde özellikle önemli.', 'moderate': 'Orta düzeyde stres yaşıyorsunuz; stres tetikleyicilerini tanımak ve yönetmek fayda sağlar.', 'low': 'Stres algı düzeyiniz düşük; zorluklarla başa çıkma kapasiteniz güçlü görünüyor.'},
        },
        'body_image': {
            'appearance_evaluation': {'high': 'Görünümünüzü genel olarak olumlu değerlendiriyorsunuz; bu sağlıklı bir beden imgesi işareti.', 'moderate': 'Görünüme ilişkin değerlendirmeleriniz karışık; bedenin işlevselliğine odaklanmak perspektifi genişletir.', 'low': 'Görünümünüzü olumsuz değerlendirme eğilimi var; beden olumlama pratikleri bu alanda destek sağlar.'},
            'body_satisfaction':     {'high': 'Bedeninizden genel olarak memnunsunuz; bu sağlıklı bir öz-kabul göstergesi.', 'moderate': 'Beden memnuniyetiniz orta düzeyde; bedeninizin güçlü yönlerine odaklanmak bu alanı besler.', 'low': 'Bedeninizden memnuniyetsizlik hissediyorsunuz; öz-şefkat pratikleri ve profesyonel destek faydalı olabilir.'},
        },
    },
    'en': {
        'personality': {
            'openness':          {'high': 'Your curiosity and imagination are strong; new experiences and ideas naturally attract you.', 'moderate': 'You balance curiosity with practicality, curious in some areas and conventional in others.', 'low': 'You prefer the practical and familiar; consistent routines and proven approaches feel right for you.'},
            'conscientiousness': {'high': 'You are disciplined, organized, and reliable; you pursue goals systematically.', 'moderate': 'You balance responsibility and flexibility; building routines would strengthen this further.', 'low': 'You have a flexible, spontaneous style; developing planning habits can improve your effectiveness.'},
            'extraversion':      {'high': 'Your social energy is high; you draw strength from people and bring energy to those around you.', 'moderate': 'You balance time with others and time alone, comfortable in both settings.', 'low': 'Your introverted nature is a natural asset for deep thinking and focused work.'},
            'agreeableness':     {'high': 'Your warm, cooperative nature builds trust and harmony in your relationships.', 'moderate': 'You balance cooperativeness and independence, understanding yet self-assertive.', 'low': 'You lean toward independent, critical thinking — a strength for analysis and objective judgment.'},
            'neuroticism':       {'high': 'Your emotional reactions can be intense; stress management and self-regulation strategies will support you.', 'moderate': 'You experience some emotional ups and downs; most of the time you can find your balance again.', 'low': 'Your emotional resilience is strong; you stay calm under pressure and handle difficulties with ease.'},
        },
        'skills': {
            'problem_solving':  {'high': 'You are strong at analyzing complex problems and generating practical solutions.', 'moderate': 'Your problem-solving approach is developing; structured thinking techniques can support you.', 'low': 'Learning systematic problem-solving methods will unlock your potential in this area.'},
            'empathy':          {'high': 'You have a remarkable ability to understand others\' emotions and connect with empathy.', 'moderate': 'Your empathy skills are developing; practicing active listening will strengthen this area.', 'low': 'Exploring others\' perspectives more will make you a more effective communicator.'},
            'organization':     {'high': 'Your planning and prioritization are strong; your organized style helps you stand out.', 'moderate': 'Your organizational skill is reasonable; using time management tools can make you even stronger.', 'low': 'Developing systematic organizational habits can significantly improve your productivity.'},
            'learning_speed':   {'high': 'You adapt quickly to new knowledge and skills — a major advantage in changing environments.', 'moderate': 'Your learning pace is reasonable; experimenting with different strategies can increase your effectiveness.', 'low': 'Structured review and practice strategies will support your learning process in this area.'},
            'decision_making':  {'high': 'You can take decisive, quick steps in decision-making situations.', 'moderate': 'Your decision-making skills are developing; structured frameworks help in difficult moments.', 'low': 'Starting with smaller decisions is an effective way to build your decision-making confidence.'},
        },
        'hr': {
            'leadership':       {'high': 'You are strong at directing teams, inspiring others, and taking the lead.', 'moderate': 'You have leadership aptitude; practical experiences will develop these skills quickly.', 'low': 'Deliberately developing leadership skills through practice can significantly advance your career.'},
            'team_fit':         {'high': 'You stand out for harmonious teamwork, collaboration, and helpfulness.', 'moderate': 'Your team fit is good; understanding different work styles will strengthen this further.', 'low': 'More active participation in team dynamics will strengthen your professional relationships.'},
            'communication':    {'high': 'You are strong at clear, effective, and constructive communication.', 'moderate': 'Your communication style is developing; adapting to different audiences gives you an advantage.', 'low': 'Systematically practicing communication skills will produce rapid progress in this area.'},
            'stress_tolerance': {'high': 'You can maintain your composure under pressure; a cornerstone of professional resilience.', 'moderate': 'Your stress-coping capacity is reasonable; resilience-building techniques will make you even stronger.', 'low': 'Developing stress management strategies, supported by daily practices, produces results quickly.'},
            'motivation':       {'high': 'Your intrinsic motivation is high; you approach your goals with commitment and passion.', 'moderate': 'Your motivation varies; staying connected to your purpose can be a continuous energy source.', 'low': 'Setting meaningful short-term goals is an effective way to reignite your motivation.'},
        },
        'career': {
            'analytical':       {'high': 'You have a strong orientation toward analytical thinking and data-focused work environments.', 'moderate': 'You have analytical tendencies; structured problem-solving practice will strengthen this area.', 'low': 'Developing systematic analytical skills will expand your options in this career area.'},
            'creative':         {'high': 'You express yourself best in creative and innovative work environments.', 'moderate': 'You have creative tendencies; nurturing this area can increase your career fulfillment.', 'low': 'Structural and technical career paths currently seem more aligned than creative-focused roles.'},
            'social':           {'high': 'Helping, teaching, or working with people energizes you.', 'moderate': 'You are comfortable in roles involving social interaction; deeper connections can add value.', 'low': 'Social-focused career paths are not currently a strong interest area for you.'},
            'entrepreneurial':  {'high': 'You have a strong tendency toward entrepreneurial roles requiring leadership, persuasion, and risk-taking.', 'moderate': 'Your entrepreneurial perspective is developing; decision-making and leadership experience will accelerate this.', 'low': 'Expertise-focused career paths currently seem more aligned than entrepreneurial roles.'},
            'managerial':       {'high': 'You are well-suited to roles that require management, coordination, and organization.', 'moderate': 'Your managerial tendencies are developing; taking on responsibility will nurture this area.', 'low': 'Expertise-focused career paths with less managerial pressure may feel more comfortable right now.'},
            'technical':        {'high': 'You have a strong interest and orientation toward technical and specialized fields.', 'moderate': 'Your technical skills are developing; deep specialization will strengthen this area.', 'low': 'People-focused career paths currently seem more aligned than technical specialist roles.'},
        },
        'vocation': {
            'realistic':        {'high': 'You have a strong inclination toward practical, hands-on, and technical work.', 'moderate': 'You have moderate interest in hands-on work; trying this area will give you a clearer picture.', 'low': 'Practical and technical activities are not currently among your strong interests.'},
            'investigative':    {'high': 'Research, analysis, and exploring ideas naturally attract you.', 'moderate': 'You have investigative interest; deepening knowledge in this area will strengthen it further.', 'low': 'Research and analysis-focused activities are not currently among your priority interests.'},
            'artistic':         {'high': 'You have a strong inclination toward activities requiring creative expression, art, and aesthetics.', 'moderate': 'You have artistic tendencies; nurturing this area can provide fulfillment and authenticity.', 'low': 'Artistic and creative activities are not currently a strong interest area for you.'},
            'social':           {'high': 'Being with people, helping, and teaching energizes you.', 'moderate': 'You have moderate interest in social activities; building meaningful connections brings satisfaction.', 'low': 'Social-focused activities are not currently among your priority interests.'},
            'enterprising':     {'high': 'You feel strongest in activities requiring leadership, persuasion, and competition.', 'moderate': 'You have enterprising tendencies; practicing responsibility and decision-making strengthens this.', 'low': 'Competitive and leadership-focused activities are not currently a strong interest area for you.'},
            'conventional':     {'high': 'You are strong in organized, systematic, and rule-consistent work environments.', 'moderate': 'You have moderate interest in organization and structure; systematic work practice nurtures this.', 'low': 'Structured and conventional activities are not currently a strong interest area for you.'},
        },
        'relationship': {
            'love_language':        {'high': 'You clearly express your love language and value mutual understanding in relationships.', 'moderate': 'You express your love language moderately; being more open here can enrich your relationships.', 'low': 'Developing awareness of emotional expression and love languages will deepen your connections.'},
            'conflict_style':       {'high': 'You are strong at resolving conflicts in constructive and healthy ways.', 'moderate': 'Your conflict resolution style is developing; trying more constructive approaches can help.', 'low': 'Developing healthy conflict resolution strategies will significantly improve your relationship quality.'},
            'intimacy_needs':       {'high': 'You clearly understand your needs for emotional closeness and connection.', 'moderate': 'You have moderate awareness of your intimacy needs; exploring this area further is valuable.', 'low': 'Understanding your emotional bonding and intimacy needs will make your relationships more fulfilling.'},
            'relationship_values':  {'high': 'You have a clear value framework for what you want in your relationships.', 'moderate': 'Your relationship values are taking shape; reflecting on this helps you build healthier connections.', 'low': 'Discovering and clarifying your personal relationship values lays the groundwork for deeper bonds.'},
        },
        'attachment': {
            'anxiety':   {'high': 'Anxiety about abandonment is high; this awareness is a strong starting point for developing secure attachment.', 'moderate': 'Attachment anxiety is moderate; secure relationship practices support this area.', 'low': 'Your abandonment anxiety is low; you show secure and balanced attachment in relationships.'},
            'avoidance': {'high': 'Avoidance of emotional closeness is noticeable; recognizing this pattern is the first step toward deeper bonds.', 'moderate': 'Avoidance of closeness is moderate; as self-awareness grows, you can build more open connections.', 'low': 'Your avoidance of emotional closeness is low; openness and connection feel comfortable in relationships.'},
        },
        'grit': {
            'perseverance': {'high': 'You are strong at completing what you start and continuing despite obstacles.', 'moderate': 'Your determination and grit are developing; staying committed to long-term goals strengthens this.', 'low': 'Accumulating short-term successes is an effective strategy for building sustainable perseverance.'},
            'passion':      {'high': 'You show consistent passion and interest toward your long-term goals.', 'moderate': 'Your passion for goals is developing; connecting to a meaningful purpose amplifies this energy.', 'low': 'Discovering interests that genuinely fire you up will fuel your passion and motivation.'},
        },
        'growth_mindset': {
            'growth_mindset': {'high': 'You strongly believe that abilities and intelligence can be developed through effort.', 'moderate': 'Your growth mindset is developing; viewing challenges as learning opportunities nurtures this.', 'low': 'The belief that abilities are fixed continues; questioning this mindset will accelerate your growth.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {'high': 'You report high satisfaction with your life and make an overall positive appraisal.', 'moderate': 'Your life satisfaction is moderate; strengthening meaning-value alignment increases fulfillment.', 'low': 'Life satisfaction is low; asking yourself what you want to change is a good starting point.'},
        },
        'self_compassion': {
            'self_kindness':       {'high': 'You approach yourself with compassion and understanding; a strong source of psychological resilience.', 'moderate': 'Your self-compassion is developing; talking to yourself like a friend in difficult moments nurtures this.', 'low': 'A harsh inner voice is prominent; developing self-compassion practices will support you.'},
            'self_judgment':       {'high': 'A tendency to be overly self-critical is present; recognizing this is a powerful starting point for change.', 'moderate': 'Self-criticism is moderate; being kinder to yourself sometimes brings benefit.', 'low': 'You show a balanced and kind attitude toward yourself; a healthy sign of self-evaluation.'},
            'common_humanity':     {'high': 'You understand that your struggles are part of the shared human experience, which brings comfort.', 'moderate': 'Your sense of common humanity is developing; remembering you are not alone strengthens you.', 'low': 'You may feel isolated when difficulties arise; remember this is a very common experience.'},
            'isolation':           {'high': 'You feel isolated and alone in difficult moments; seeking connection and support helps balance this.', 'moderate': 'Feelings of isolation can arise from time to time; building connections helps balance this.', 'low': 'You feel connected and supported when facing difficulties; an important sign of psychological health.'},
            'mindfulness':         {'high': 'You can observe your emotions with balance and awareness; a healthy psychological stance.', 'moderate': 'Your mindful awareness is developing; simple meditation practices will strengthen this area.', 'low': 'There is a tendency to suppress rather than observe emotions; mindfulness practices can provide support.'},
            'overidentification':  {'high': 'There is a tendency to over-focus on negative emotions and thoughts; mindfulness practices break this cycle.', 'moderate': 'You can sometimes over-identify with negative thoughts; balance strategies help.', 'low': 'You maintain a healthy distance from negative thoughts; a strong indicator of mindful awareness.'},
        },
        'self_efficacy': {
            'self_efficacy': {'high': 'You have a strong belief in your ability to accomplish challenging tasks.', 'moderate': 'Your self-efficacy belief is developing; accumulating small successes increases this confidence.', 'low': 'Confidence in your own abilities is low; building success experiences through small steps helps.'},
        },
        'stress': {
            'perceived_stress': {'high': 'You are perceiving a high level of stress recently; stress management strategies are especially important now.', 'moderate': 'You are experiencing moderate stress; identifying and managing stress triggers brings benefit.', 'low': 'Your stress perception level is low; your capacity to handle challenges appears strong.'},
        },
        'body_image': {
            'appearance_evaluation': {'high': 'You evaluate your appearance generally positively; a sign of healthy body image.', 'moderate': "Your appearance evaluations are mixed; focusing on your body's functionality broadens perspective.", 'low': 'There is a tendency to evaluate your appearance negatively; body affirmation practices provide support here.'},
            'body_satisfaction':     {'high': 'You are generally satisfied with your body; a sign of healthy self-acceptance.', 'moderate': "Your body satisfaction is moderate; focusing on your body's strengths nurtures this area.", 'low': 'You feel dissatisfied with your body; self-compassion practices and professional support may be beneficial.'},
        },
    },
    'de': {
        'personality': {
            'openness': {"high": 'Ihre Neugier und Vorstellungskraft sind stark;Neue Erfahrungen und Ideen ziehen Sie natürlich an.', "moderate": 'Sie bringen Neugier und Praktikabilität in Einklang, sind in manchen Bereichen neugierig und in anderen konventionell.', "low": 'Sie bevorzugen das Praktische und Vertraute;Konsistente Routinen und bewährte Ansätze fühlen sich für Sie richtig an.'},
            'conscientiousness': {"high": 'Sie sind diszipliniert, organisiert und zuverlässig;Sie verfolgen Ziele systematisch.', "moderate": 'Sie bringen Verantwortung und Flexibilität in Einklang;Bauroutinen würden dies noch verstärken.', "low": 'Sie haben einen flexiblen, spontanen Stil;Die Entwicklung von Planungsgewohnheiten kann Ihre Effektivität verbessern.'},
            'extraversion': {"high": 'Ihre soziale Energie ist hoch;Sie schöpfen Kraft aus den Menschen und bringen Energie zu den Menschen um Sie herum.', "moderate": 'Sie balancieren die Zeit mit anderen und die Zeit alleine aus und fühlen sich in beiden Situationen wohl.', "low": 'Ihre introvertierte Art ist eine natürliche Bereicherung für tiefes Denken und konzentriertes Arbeiten.'},
            'agreeableness': {"high": 'Ihre herzliche, kooperative Art schafft Vertrauen und Harmonie in Ihren Beziehungen.', "moderate": 'Sie bringen Kooperationsbereitschaft und Unabhängigkeit in Einklang, sind verständnisvoll und dennoch selbstbewusst.', "low": 'Sie neigen zu unabhängigem, kritischem Denken – eine Stärke für Analyse und objektives Urteil.'},
            'neuroticism': {"high": 'Ihre emotionalen Reaktionen können heftig sein;Stressbewältigungs- und Selbstregulationsstrategien unterstützen Sie dabei.', "moderate": 'Sie erleben einige emotionale Höhen und Tiefen;Meistens gelingt es dir, dein Gleichgewicht wiederzufinden.', "low": 'Ihre emotionale Belastbarkeit ist stark;Sie bleiben unter Druck ruhig und bewältigen Schwierigkeiten mit Leichtigkeit.'},
        },
        'skills': {
            'problem_solving': {"high": 'Sie sind stark darin, komplexe Probleme zu analysieren und praktische Lösungen zu erarbeiten.', "moderate": 'Ihr Problemlösungsansatz entwickelt sich;Techniken des strukturierten Denkens können Sie dabei unterstützen.', "low": 'Das Erlernen systematischer Problemlösungsmethoden wird Ihr Potenzial in diesem Bereich freisetzen.'},
            'empathy': {"high": 'Sie verfügen über eine bemerkenswerte Fähigkeit, die Emotionen anderer zu verstehen und sich mit Empathie zu identifizieren.', "moderate": 'Ihre Empathiefähigkeiten entwickeln sich;Durch aktives Zuhören wird dieser Bereich gestärkt.', "low": 'Wenn Sie die Perspektiven anderer stärker erkunden, werden Sie zu einem effektiveren Kommunikator.'},
            'organization': {"high": 'Ihre Planung und Priorisierung ist stark;Ihr organisierter Stil hilft Ihnen, aufzufallen.', "moderate": 'Ihr organisatorisches Geschick ist angemessen;Der Einsatz von Zeitmanagement-Tools kann Sie noch stärker machen.', "low": 'Die Entwicklung systematischer Organisationsgewohnheiten kann Ihre Produktivität erheblich steigern.'},
            'learning_speed': {"high": 'Sie passen sich schnell an neue Kenntnisse und Fähigkeiten an – ein großer Vorteil in sich verändernden Umgebungen.', "moderate": 'Ihr Lerntempo ist angemessen;Das Experimentieren mit verschiedenen Strategien kann Ihre Effektivität steigern.', "low": 'Strukturierte Wiederholungs- und Übungsstrategien unterstützen Ihren Lernprozess in diesem Bereich.'},
            'decision_making': {"high": 'Sie können in Entscheidungssituationen entscheidende und schnelle Schritte unternehmen.', "moderate": 'Ihre Entscheidungsfähigkeiten entwickeln sich;Strukturierte Rahmenbedingungen helfen in schwierigen Momenten.', "low": 'Mit kleineren Entscheidungen zu beginnen, ist ein effektiver Weg, um Ihr Entscheidungsvertrauen zu stärken.'},
        },
        'hr': {
            'leadership': {"high": 'Sie sind stark darin, Teams zu leiten, andere zu inspirieren und die Führung zu übernehmen.', "moderate": 'Sie verfügen über Führungsqualitäten;Praktische Erfahrungen werden diese Fähigkeiten schnell entwickeln.', "low": 'Die gezielte Entwicklung von Führungsqualitäten durch praktische Übungen kann Ihre Karriere erheblich voranbringen.'},
            'team_fit': {"high": 'Sie zeichnen sich durch harmonische Teamarbeit, Zusammenarbeit und Hilfsbereitschaft aus.', "moderate": 'Ihr Teamfit ist gut;Das Verständnis verschiedener Arbeitsstile wird dies weiter stärken.', "low": 'Eine aktivere Beteiligung an der Teamdynamik stärkt Ihre beruflichen Beziehungen.'},
            'communication': {"high": 'Sie sind stark in der klaren, effektiven und konstruktiven Kommunikation.', "moderate": 'Ihr Kommunikationsstil entwickelt sich;Die Anpassung an unterschiedliche Zielgruppen verschafft Ihnen einen Vorteil.', "low": 'Das systematische Einüben von Kommunikationsfähigkeiten wird in diesem Bereich zu schnellen Fortschritten führen.'},
            'stress_tolerance': {"high": 'Sie können auch unter Druck die Fassung bewahren;ein Eckpfeiler der beruflichen Belastbarkeit.', "moderate": 'Ihre Fähigkeit zur Stressbewältigung ist angemessen;Resilienzaufbauende Techniken werden Sie noch stärker machen.', "low": 'Die Entwicklung von Stressbewältigungsstrategien, unterstützt durch tägliche Übungen, führt schnell zu Ergebnissen.'},
            'motivation': {"high": 'Ihre intrinsische Motivation ist hoch;Du gehst deine Ziele mit Engagement und Leidenschaft an.', "moderate": 'Ihre Motivation ist unterschiedlich;Mit Ihrem Ziel verbunden zu bleiben, kann eine kontinuierliche Energiequelle sein.', "low": 'Das Setzen sinnvoller kurzfristiger Ziele ist eine wirksame Möglichkeit, Ihre Motivation wiederzubeleben.'},
        },
        'career': {
            'analytical': {"high": 'Sie sind stark auf analytisches Denken und datenorientierte Arbeitsumgebungen ausgerichtet.', "moderate": 'Sie haben analytische Tendenzen;Eine strukturierte Problemlösungspraxis wird diesen Bereich stärken.', "low": 'Durch die Entwicklung systematischer Analysefähigkeiten erweitern Sie Ihre Möglichkeiten in diesem Berufsfeld.'},
            'creative': {"high": 'Sie bringen sich am besten in kreativen und innovativen Arbeitsumgebungen zum Ausdruck.', "moderate": 'Sie haben kreative Tendenzen;Die Förderung dieses Bereichs kann Ihre berufliche Erfüllung steigern.', "low": 'Strukturelle und technische Karrierewege scheinen derzeit stärker aufeinander abgestimmt zu sein als kreativ ausgerichtete Rollen.'},
            'social': {"high": 'Menschen zu helfen, zu unterrichten oder mit ihnen zu arbeiten gibt Ihnen neue Energie.', "moderate": 'Sie fühlen sich in Rollen wohl, die soziale Interaktion erfordern;Tiefere Verbindungen können einen Mehrwert schaffen.', "low": 'Sozialorientierte Karrierewege sind für Sie derzeit kein großes Interessengebiet.'},
            'entrepreneurial': {"high": 'Sie neigen stark zu unternehmerischen Rollen, die Führung, Überzeugungskraft und Risikobereitschaft erfordern.', "moderate": 'Ihre unternehmerische Perspektive entwickelt sich;Entscheidungsfindung und Führungserfahrung werden dies beschleunigen.', "low": 'Fachkompetenzorientierte Karrierewege scheinen derzeit stärker aufeinander abgestimmt zu sein als unternehmerische Rollen.'},
            'managerial': {"high": 'Sie eignen sich gut für Rollen, die Führung, Koordination und Organisation erfordern.', "moderate": 'Ihre Führungstendenzen entwickeln sich;Durch die Übernahme von Verantwortung wird dieser Bereich gefördert.', "low": 'Fachwissenorientierte Karrierewege mit weniger Führungsdruck könnten sich derzeit wohler anfühlen.'},
            'technical': {"high": 'Sie haben ein ausgeprägtes Interesse und eine ausgeprägte Orientierung an technischen und speziellen Fachgebieten.', "moderate": 'Ihre technischen Fähigkeiten entwickeln sich;Eine tiefe Spezialisierung wird diesen Bereich stärken.', "low": 'Karrierewege, bei denen der Mensch im Mittelpunkt steht, scheinen derzeit stärker aufeinander abgestimmt zu sein als die Rollen von technischen Spezialisten.'},
        },
        'vocation': {
            'realistic': {"high": 'Sie haben einen ausgeprägten Hang zu praktischer, praktischer und technischer Arbeit.', "moderate": 'Sie haben mäßiges Interesse an praktischer Arbeit;Wenn Sie diesen Bereich ausprobieren, erhalten Sie ein klareres Bild.', "low": 'Praktische und technische Tätigkeiten gehören derzeit nicht zu Ihren starken Interessen.'},
            'investigative': {"high": 'Recherche, Analyse und die Erkundung von Ideen ziehen Sie natürlich an.', "moderate": 'Sie haben Ermittlungsinteresse;Durch die Vertiefung der Kenntnisse in diesem Bereich werden diese weiter gestärkt.', "low": 'Forschungs- und analyseorientierte Tätigkeiten gehören derzeit nicht zu Ihren vorrangigen Interessen.'},
            'artistic': {"high": 'Sie haben eine starke Neigung zu Aktivitäten, die kreativen Ausdruck, Kunst und Ästhetik erfordern.', "moderate": 'Sie haben künstlerische Neigungen;Die Pflege dieses Bereichs kann für Erfüllung und Authentizität sorgen.', "low": 'Künstlerische und kreative Tätigkeiten sind für Sie derzeit kein großes Interessengebiet.'},
            'social': {"high": 'Der Umgang mit Menschen, das Helfen und Lehren gibt Ihnen neue Energie.', "moderate": 'Sie haben ein mäßiges Interesse an sozialen Aktivitäten;Der Aufbau sinnvoller Verbindungen bringt Zufriedenheit.', "low": 'Soziale Aktivitäten gehören derzeit nicht zu Ihren vorrangigen Interessen.'},
            'enterprising': {"high": 'Sie fühlen sich bei Aktivitäten am stärksten, die Führung, Überzeugungskraft und Wettbewerb erfordern.', "moderate": 'Sie haben unternehmungslustige Tendenzen;Das Einüben von Verantwortung und Entscheidungsfindung stärkt dies.', "low": 'Wettbewerbs- und führungsorientierte Tätigkeiten sind für Sie derzeit nicht besonders interessant.'},
            'conventional': {"high": 'Sie sind stark in organisierten, systematischen und regelkonformen Arbeitsumgebungen.', "moderate": 'Sie haben ein mäßiges Interesse an Organisation und Struktur;Eine systematische Arbeitspraxis fördert dies.', "low": 'Strukturierte und konventionelle Tätigkeiten sind für Sie derzeit kein starkes Interessengebiet.'},
        },
        'relationship': {
            'love_language': {"high": 'Sie bringen Ihre Liebessprache deutlich zum Ausdruck und legen Wert auf gegenseitiges Verständnis in Beziehungen.', "moderate": 'Sie drücken Ihre Liebessprache mäßig aus;Hier offener zu sein, kann Ihre Beziehungen bereichern.', "low": 'Die Entwicklung eines Bewusstseins für emotionalen Ausdruck und Liebessprachen wird Ihre Verbindungen vertiefen.'},
            'conflict_style': {"high": 'Sie sind stark darin, Konflikte auf konstruktive und gesunde Weise zu lösen.', "moderate": 'Ihr Konfliktlösungsstil entwickelt sich;Es kann hilfreich sein, konstruktivere Ansätze auszuprobieren.', "low": 'Die Entwicklung gesunder Konfliktlösungsstrategien wird die Qualität Ihrer Beziehung erheblich verbessern.'},
            'intimacy_needs': {"high": 'Sie verstehen Ihr Bedürfnis nach emotionaler Nähe und Verbindung klar.', "moderate": 'Sie sind sich Ihrer Intimitätsbedürfnisse nur mäßig bewusst;Es ist wertvoll, diesen Bereich weiter zu erkunden.', "low": 'Wenn Sie Ihre emotionalen Bindungs- und Intimitätsbedürfnisse verstehen, werden Ihre Beziehungen erfüllender.'},
            'relationship_values': {"high": 'Sie haben einen klaren Werterahmen für das, was Sie in Ihren Beziehungen wollen.', "moderate": 'Ihre Beziehungswerte nehmen Gestalt an;Wenn Sie darüber nachdenken, können Sie gesündere Verbindungen aufbauen.', "low": 'Das Entdecken und Klären Ihrer persönlichen Beziehungswerte legt den Grundstein für tiefere Bindungen.'},
        },
        'attachment': {
            'anxiety': {"high": 'Die Angst vor dem Verlassenwerden ist groß;Dieses Bewusstsein ist ein starker Ausgangspunkt für die Entwicklung einer sicheren Bindung.', "moderate": 'Bindungsangst ist mäßig;Sichere Beziehungspraktiken unterstützen diesen Bereich.', "low": 'Ihre Verlassenheitsangst ist gering;Sie zeigen in Beziehungen eine sichere und ausgeglichene Bindung.'},
            'avoidance': {"high": 'Auffallend ist die Vermeidung emotionaler Nähe;Das Erkennen dieses Musters ist der erste Schritt zu tieferen Bindungen.', "moderate": 'Die Vermeidung von Nähe ist moderat;Wenn das Selbstbewusstsein wächst, können Sie offenere Verbindungen aufbauen.', "low": 'Ihre Vermeidung emotionaler Nähe ist gering;Offenheit und Verbundenheit fühlen sich in Beziehungen wohl.'},
        },
        'grit': {
            'perseverance': {"high": 'Sie sind stark darin, das, was Sie begonnen haben, zu Ende zu bringen und trotz Hindernissen weiterzumachen.', "moderate": 'Ihre Entschlossenheit und Ihr Mut entwickeln sich;Wenn man sich langfristigen Zielen verpflichtet fühlt, wird dies gestärkt.', "low": 'Das Anhäufen kurzfristiger Erfolge ist eine wirksame Strategie zum Aufbau nachhaltiger Ausdauer.'},
            'passion': {"high": 'Sie zeigen beständig Leidenschaft und Interesse für Ihre langfristigen Ziele.', "moderate": 'Ihre Leidenschaft für Ziele entwickelt sich;Die Verbindung zu einem sinnvollen Zweck verstärkt diese Energie.', "low": 'Das Entdecken von Interessen, die Sie wirklich antreiben, wird Ihre Leidenschaft und Motivation ankurbeln.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'Sie glauben fest daran, dass Fähigkeiten und Intelligenz durch Anstrengung entwickelt werden können.', "moderate": 'Ihre Wachstumsmentalität entwickelt sich;Herausforderungen als Lernmöglichkeiten zu betrachten, fördert dies.', "low": 'Der Glaube, dass Fähigkeiten festgelegt sind, bleibt bestehen;Das Hinterfragen dieser Denkweise wird Ihr Wachstum beschleunigen.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'Sie berichten von einer hohen Zufriedenheit mit Ihrem Leben und ziehen eine insgesamt positive Bilanz.', "moderate": 'Ihre Lebenszufriedenheit ist mäßig;Die Stärkung der Sinn-Wert-Ausrichtung erhöht die Erfüllung.', "low": 'Die Lebenszufriedenheit ist gering;Sich selbst zu fragen, was Sie ändern möchten, ist ein guter Ausgangspunkt.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'Sie gehen mit Mitgefühl und Verständnis auf sich selbst zu;eine starke Quelle psychologischer Widerstandsfähigkeit.', "moderate": 'Ihr Selbstmitgefühl entwickelt sich;In schwierigen Momenten mit sich selbst wie mit einem Freund zu sprechen, fördert dies.', "low": 'Eine raue innere Stimme ist vorherrschend;Die Entwicklung von Selbstmitgefühlspraktiken wird Ihnen dabei helfen.'},
            'self_judgment': {"high": 'Es besteht eine Tendenz zu übertriebener Selbstkritik;Dies zu erkennen, ist ein wichtiger Ausgangspunkt für Veränderungen.', "moderate": 'Selbstkritik ist moderat;Freundlicher zu sich selbst zu sein, bringt manchmal Vorteile.', "low": 'Du zeigst eine ausgeglichene und freundliche Einstellung zu dir selbst;ein gesundes Zeichen der Selbsteinschätzung.'},
            'common_humanity': {"high": 'Sie verstehen, dass Ihre Kämpfe Teil der gemeinsamen menschlichen Erfahrung sind, die Trost spendet.', "moderate": 'Ihr Sinn für die gemeinsame Menschlichkeit entwickelt sich;Sich daran zu erinnern, dass du nicht allein bist, stärkt dich.', "low": 'Wenn Schwierigkeiten auftreten, fühlen Sie sich möglicherweise isoliert.Denken Sie daran, dass dies eine sehr häufige Erfahrung ist.'},
            'isolation': {"high": 'In schwierigen Momenten fühlt man sich isoliert und allein;Die Suche nach Kontakt und Unterstützung trägt dazu bei, dies auszugleichen.', "moderate": 'Von Zeit zu Zeit können Gefühle der Isolation aufkommen;Der Aufbau von Verbindungen trägt dazu bei, dies auszugleichen.', "low": 'Sie fühlen sich bei Schwierigkeiten verbunden und unterstützt;ein wichtiges Zeichen psychischer Gesundheit.'},
            'mindfulness': {"high": 'Sie können Ihre Emotionen ausgeglichen und bewusst beobachten;eine gesunde psychologische Haltung.', "moderate": 'Ihr achtsames Bewusstsein entwickelt sich;Einfache Meditationsübungen stärken diesen Bereich.', "low": 'Es besteht die Tendenz, Emotionen eher zu unterdrücken als zu beobachten;Achtsamkeitsübungen können dabei unterstützend wirken.'},
            'overidentification': {"high": 'Es besteht die Tendenz, sich zu sehr auf negative Emotionen und Gedanken zu konzentrieren.Achtsamkeitsübungen durchbrechen diesen Kreislauf.', "moderate": 'Manchmal können Sie sich zu sehr mit negativen Gedanken identifizieren;Balancestrategien helfen.', "low": 'Sie wahren einen gesunden Abstand zu negativen Gedanken;ein starker Indikator für achtsames Bewusstsein.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'Sie sind fest davon überzeugt, dass Sie anspruchsvolle Aufgaben meistern können.', "moderate": 'Ihr Glaube an die Selbstwirksamkeit entwickelt sich;Die Anhäufung kleiner Erfolge steigert dieses Selbstvertrauen.', "low": 'Das Vertrauen in die eigenen Fähigkeiten ist gering;Der Aufbau von Erfolgserlebnissen in kleinen Schritten hilft.'},
        },
        'stress': {
            'perceived_stress': {"high": 'Sie verspüren in letzter Zeit ein hohes Maß an Stress;Stressbewältigungsstrategien sind jetzt besonders wichtig.', "moderate": 'Sie leiden unter mäßigem Stress;Das Erkennen und Bewältigen von Stressauslösern bringt Vorteile.', "low": 'Ihr Stressempfinden ist niedrig;Ihre Fähigkeit, Herausforderungen zu meistern, scheint stark zu sein.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'Sie bewerten Ihr Erscheinungsbild grundsätzlich positiv;ein Zeichen für ein gesundes Körperbild.', "moderate": 'Ihre Beurteilung des Aussehens fällt gemischt aus;Wenn Sie sich auf die Funktionalität Ihres Körpers konzentrieren, erweitert sich die Perspektive.', "low": 'Es besteht die Tendenz, Ihr Aussehen negativ zu bewerten.Körperaffirmationspraktiken bieten hier Unterstützung.'},
            'body_satisfaction': {"high": 'Im Allgemeinen sind Sie mit Ihrem Körper zufrieden;ein Zeichen gesunder Selbstakzeptanz.', "moderate": 'Ihre Körperzufriedenheit ist mäßig;Wenn Sie sich auf die Stärken Ihres Körpers konzentrieren, wird dieser Bereich gefördert.', "low": 'Sie sind mit Ihrem Körper unzufrieden;Selbstmitgefühlspraktiken und professionelle Unterstützung können hilfreich sein.'},
        },
    },
    'ru': {
        'personality': {
            'openness': {"high": 'Ваше любопытство и воображение сильны;вас естественным образом привлекают новые впечатления и идеи.', "moderate": 'Вы балансируете между любопытством и практичностью: в одних областях вы любопытны, а в других — консервативны.', "low": 'Вы предпочитаете практичное и знакомое;Последовательный распорядок дня и проверенные подходы подходят именно вам.'},
            'conscientiousness': {"high": 'Вы дисциплинированы, организованы и надежны;вы систематически преследуете цели.', "moderate": 'Вы балансируете ответственность и гибкость;построение процедур еще больше укрепит это.', "low": 'У вас гибкий, спонтанный стиль;Развитие привычек планирования может повысить вашу эффективность.'},
            'extraversion': {"high": 'Ваша социальная энергия высока;вы черпаете силу из людей и приносите энергию окружающим.', "moderate": 'Вы балансируете время с другими и в одиночестве, чувствуя себя комфортно в обеих ситуациях.', "low": 'Ваша интровертная натура — естественный ресурс для глубокого мышления и целенаправленной работы.'},
            'agreeableness': {"high": 'Ваш теплый, готовый к сотрудничеству характер создает доверие и гармонию в ваших отношениях.', "moderate": 'Вы балансируете между готовностью к сотрудничеству и независимостью, понимающим, но самоуверенным.', "low": 'Вы склонны к независимому, критическому мышлению – силе в анализе и объективном суждении.'},
            'neuroticism': {"high": 'Ваши эмоциональные реакции могут быть сильными;Стратегии управления стрессом и саморегуляции помогут вам.', "moderate": 'Вы испытываете некоторые эмоциональные взлеты и падения;Большую часть времени вы можете снова найти свой баланс.', "low": 'Ваша эмоциональная устойчивость сильна;вы сохраняете спокойствие под давлением и легко справляетесь с трудностями.'},
        },
        'skills': {
            'problem_solving': {"high": 'Вы умеете анализировать сложные проблемы и находить практические решения.', "moderate": 'Ваш подход к решению проблем развивается;методы структурированного мышления могут вам помочь.', "low": 'Изучение систематических методов решения проблем раскроет ваш потенциал в этой области.'},
            'empathy': {"high": 'У вас замечательная способность понимать эмоции других и проявлять сочувствие.', "moderate": 'Ваши навыки эмпатии развиваются;практика активного слушания укрепит эту область.', "low": 'Более детальное изучение точек зрения других сделает вас более эффективным коммуникатором.'},
            'organization': {"high": 'Ваше планирование и расстановка приоритетов сильны;организованный стиль помогает вам выделиться.', "moderate": 'Ваши организаторские способности разумны;Использование инструментов тайм-менеджмента может сделать вас еще сильнее.', "low": 'Развитие систематических организационных привычек может значительно повысить вашу производительность.'},
            'learning_speed': {"high": 'Вы быстро адаптируетесь к новым знаниям и навыкам — главное преимущество в меняющейся среде.', "moderate": 'Ваш темп обучения разумный;экспериментирование с различными стратегиями может повысить вашу эффективность.', "low": 'Стратегии структурированного обзора и практики помогут вашему процессу обучения в этой области.'},
            'decision_making': {"high": 'Вы можете предпринимать решительные и быстрые шаги в ситуациях принятия решений.', "moderate": 'Ваши навыки принятия решений развиваются;структурированные рамки помогают в трудные моменты.', "low": 'Начинать с небольших решений — это эффективный способ обрести уверенность в принятии решений.'},
        },
        'hr': {
            'leadership': {"high": 'Вы умеете руководить командой, вдохновлять других и брать на себя инициативу.', "moderate": 'У вас есть лидерские способности;практический опыт быстро разовьет эти навыки.', "low": 'Целенаправленное развитие лидерских качеств на практике может значительно продвинуть вашу карьеру.'},
            'team_fit': {"high": 'Вы отличаетесь слаженной командной работой, сотрудничеством и готовностью помочь.', "moderate": 'Ваша командная совместимость хорошая;понимание различных стилей работы еще больше укрепит это.', "low": 'Более активное участие в командной динамике укрепит ваши профессиональные отношения.'},
            'communication': {"high": 'Вы сильны в четком, эффективном и конструктивном общении.', "moderate": 'Ваш стиль общения развивается;адаптация к разным аудиториям дает вам преимущество.', "low": 'Систематическая практика коммуникативных навыков приведет к быстрому прогрессу в этой области.'},
            'stress_tolerance': {"high": 'Вы можете сохранять самообладание под давлением;краеугольный камень профессиональной устойчивости.', "moderate": 'Ваша способность справляться со стрессом достаточна;методы повышения устойчивости сделают вас еще сильнее.', "low": 'Разработка стратегий управления стрессом, подкрепленная повседневной практикой, быстро дает результаты.'},
            'motivation': {"high": 'Ваша внутренняя мотивация высока;вы подходите к своим целям целеустремленно и страстно.', "moderate": 'Ваша мотивация варьируется;Оставаясь на связи со своей целью, вы можете стать постоянным источником энергии.', "low": 'Постановка значимых краткосрочных целей — эффективный способ возродить вашу мотивацию.'},
        },
        'career': {
            'analytical': {"high": 'У вас сильная ориентация на аналитическое мышление и рабочую среду, ориентированную на данные.', "moderate": 'У вас есть аналитические наклонности;структурированная практика решения проблем укрепит эту область.', "low": 'Развитие систематических аналитических навыков расширит ваши возможности в этой области карьеры.'},
            'creative': {"high": 'Лучше всего вы проявляете себя в творческой и инновационной рабочей среде.', "moderate": 'У вас есть творческие наклонности;развитие этой области может повысить вашу карьерную реализацию.', "low": 'Структурные и технические карьерные пути в настоящее время кажутся более согласованными, чем должности, ориентированные на творчество.'},
            'social': {"high": 'Помощь, обучение или работа с людьми заряжает вас энергией.', "moderate": 'Вы чувствуете себя комфортно в ролях, связанных с социальным взаимодействием;более глубокие связи могут повысить ценность.', "low": 'Карьера, ориентированная на социальную сферу, в настоящее время не представляет для вас особого интереса.'},
            'entrepreneurial': {"high": 'У вас сильная склонность к предпринимательской деятельности, требующей лидерства, убеждения и принятия риска.', "moderate": 'Ваша предпринимательская перспектива развивается;принятие решений и опыт лидерства ускорят это.', "low": 'Карьерные пути, ориентированные на экспертные знания, в настоящее время кажутся более согласованными, чем предпринимательские роли.'},
            'managerial': {"high": 'Вы хорошо подходите для должностей, требующих управления, координации и организации.', "moderate": 'Ваши управленческие способности развиваются;принятие на себя ответственности будет способствовать развитию этой области.', "low": 'Карьерный путь, ориентированный на экспертные знания и с меньшим управленческим давлением, может показаться более комфортным прямо сейчас.'},
            'technical': {"high": 'У вас сильный интерес и ориентация на технические и специализированные области.', "moderate": 'Ваши технические навыки развиваются;глубокая специализация укрепит эту область.', "low": 'Карьерные пути, ориентированные на людей, в настоящее время кажутся более согласованными, чем должности технических специалистов.'},
        },
        'vocation': {
            'realistic': {"high": 'У вас сильная склонность к практической, практической и технической работе.', "moderate": 'У вас умеренный интерес к практической работе;попробовав эту область, вы получите более четкую картину.', "low": 'Практическая и техническая деятельность в настоящее время не входит в число ваших сильных интересов.'},
            'investigative': {"high": 'Исследования, анализ и изучение идей естественным образом привлекают вас.', "moderate": 'У вас есть исследовательский интерес;углубление знаний в этой области еще больше укрепит ее.', "low": 'Научно-аналитическая деятельность в настоящее время не входит в число ваших приоритетных интересов.'},
            'artistic': {"high": 'У вас сильная склонность к деятельности, требующей творческого самовыражения, искусства и эстетики.', "moderate": 'У вас есть художественные наклонности;развитие этой области может обеспечить удовлетворение и подлинность.', "low": 'Художественная и творческая деятельность в настоящее время не является для вас сферой особого интереса.'},
            'social': {"high": 'Общение с людьми, помощь и обучение заряжают вас энергией.', "moderate": 'У вас умеренный интерес к общественной деятельности;построение значимых связей приносит удовлетворение.', "low": 'Социально-ориентированная деятельность в настоящее время не входит в число ваших приоритетных интересов.'},
            'enterprising': {"high": 'Вы чувствуете себя сильнее всего в деятельности, требующей лидерства, убеждения и конкуренции.', "moderate": 'У вас есть предприимчивые наклонности;практика ответственности и принятия решений усиливает это.', "low": 'Конкурентоспособная и ориентированная на лидерство деятельность в настоящее время не является для вас сферой особого интереса.'},
            'conventional': {"high": 'Вы сильны в организованной, систематической и соответствующей правилам рабочей среде.', "moderate": 'У вас умеренный интерес к организации и структуре;систематическая практика работы способствует этому.', "low": 'Структурированная и традиционная деятельность в настоящее время не представляет для вас особого интереса.'},
        },
        'relationship': {
            'love_language': {"high": 'Вы ясно выражаете свой язык любви и цените взаимопонимание в отношениях.', "moderate": 'Вы умеренно выражаете свой язык любви;если вы будете здесь более открытыми, это может обогатить ваши отношения.', "low": 'Развитие понимания выражения эмоций и языков любви углубит ваши связи.'},
            'conflict_style': {"high": 'Вы умеете разрешать конфликты конструктивным и здоровым способом.', "moderate": 'Ваш стиль разрешения конфликтов развивается;использование более конструктивных подходов может помочь.', "low": 'Разработка здоровых стратегий разрешения конфликтов значительно улучшит качество ваших отношений.'},
            'intimacy_needs': {"high": 'Вы четко понимаете свои потребности в эмоциональной близости и связи.', "moderate": 'Вы умеренно осознаете свои потребности в близости;Дальнейшее изучение этой области имеет ценность.', "low": 'Понимание ваших эмоциональных связей и потребностей в близости сделает ваши отношения более полноценными.'},
            'relationship_values': {"high": 'У вас есть четкая система ценностей того, чего вы хотите в своих отношениях.', "moderate": 'Ценности ваших отношений обретают форму;размышления об этом помогут вам построить более здоровые связи.', "low": 'Выявление и разъяснение ценностей ваших личных отношений закладывает основу для более глубоких связей.'},
        },
        'attachment': {
            'anxiety': {"high": 'Тревога по поводу оставления высока;это осознание является мощной отправной точкой для развития безопасной привязанности.', "moderate": 'Тревога привязанности умеренная;Практика безопасных отношений поддерживает эту область.', "low": 'Ваша тревога покинутости низкая;вы демонстрируете надежную и уравновешенную привязанность в отношениях.'},
            'avoidance': {"high": 'Заметно избегание эмоциональной близости;признание этой закономерности является первым шагом к более глубоким связям.', "moderate": 'Избегание близости умеренное;по мере роста самосознания вы сможете создавать более открытые связи.', "low": 'Ваше избегание эмоциональной близости низкое;открытость и контактность чувствуют себя комфортно в отношениях.'},
        },
        'grit': {
            'perseverance': {"high": 'Вы умеете доводить начатое до конца и продолжать, несмотря на препятствия.', "moderate": 'Ваша решимость и упорство развиваются;приверженность долгосрочным целям усиливает это.', "low": 'Накопление краткосрочных успехов является эффективной стратегией формирования устойчивой настойчивости.'},
            'passion': {"high": 'Вы демонстрируете постоянную страсть и интерес к своим долгосрочным целям.', "moderate": 'Ваша страсть к целям развивается;подключение к значимой цели усиливает эту энергию.', "low": 'Обнаружение интересов, которые действительно вас зажигают, подпитает вашу страсть и мотивацию.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'Вы твердо верите, что способности и интеллект можно развивать, прилагая усилия.', "moderate": 'Ваше мышление роста развивается;рассмотрение проблем как возможностей обучения способствует этому.', "low": 'Вера в то, что способности фиксированы, сохраняется;сомнение в этом образе мышления ускорит ваш рост.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'Вы сообщаете о высоком удовлетворении своей жизнью и в целом оцениваете ее положительно.', "moderate": 'Ваша удовлетворенность жизнью умеренная;усиление выравнивания смысла и ценности увеличивает удовлетворение.', "low": 'Удовлетворенность жизнью низкая;Хорошая отправная точка — спросить себя, что вы хотите изменить.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'Вы подходите к себе с состраданием и пониманием;мощный источник психологической устойчивости.', "moderate": 'Ваше самосострадание развивается;разговор с самим собой как с другом в трудные моменты способствует этому.', "low": 'Заметен резкий внутренний голос;развитие практики самосострадания поддержит вас.'},
            'self_judgment': {"high": 'Присутствует тенденция к чрезмерной самокритичности;признание этого является мощной отправной точкой для перемен.', "moderate": 'Самокритика умеренная;быть добрее к себе иногда приносит пользу.', "low": 'Вы проявляете уравновешенное и доброе отношение к себе;здоровый признак самооценки.'},
            'common_humanity': {"high": 'Вы понимаете, что ваши трудности — это часть общего человеческого опыта, который приносит утешение.', "moderate": 'Ваше чувство человечности развивается;воспоминание о том, что вы не одиноки, укрепляет вас.', "low": 'Вы можете чувствовать себя изолированным, когда возникают трудности;помните, что это очень распространенный опыт.'},
            'isolation': {"high": 'Вы чувствуете себя изолированным и одиноким в трудные минуты;поиск связи и поддержки помогает сбалансировать это.', "moderate": 'Время от времени может возникать чувство изоляции;установление связей помогает сбалансировать это.', "low": 'Вы чувствуете связь и поддержку, когда сталкиваетесь с трудностями;важный признак психологического здоровья.'},
            'mindfulness': {"high": 'Вы можете наблюдать за своими эмоциями сбалансированно и осознанно;здоровая психологическая позиция.', "moderate": 'Ваше осознанное осознание развивается;простые медитативные практики укрепят эту область.', "low": 'Существует тенденция подавлять, а не наблюдать эмоции;Практики осознанности могут оказать поддержку.'},
            'overidentification': {"high": 'Существует тенденция чрезмерного внимания к негативным эмоциям и мыслям;практики осознанности разрывают этот порочный круг.', "moderate": 'Иногда вы можете чрезмерно отождествлять себя с негативными мыслями;стратегии баланса помогают.', "low": 'Вы сохраняете здоровую дистанцию \u200b\u200bот негативных мыслей;сильный показатель внимательного осознания.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'Вы твердо верите в свою способность решать сложные задачи.', "moderate": 'Ваша вера в самоэффективность развивается;накопление небольших успехов увеличивает эту уверенность.', "low": 'Уверенность в собственных силах низкая;помогает добиться успеха с помощью маленьких шагов.'},
        },
        'stress': {
            'perceived_stress': {"high": 'В последнее время вы испытываете высокий уровень стресса;Стратегии управления стрессом особенно важны сейчас.', "moderate": 'Вы испытываете умеренный стресс;выявление и управление триггерами стресса приносит пользу.', "low": 'Ваш уровень восприятия стресса низкий;ваша способность справляться с трудностями кажется сильной.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'Свою внешность вы оцениваете в целом положительно;признак здорового образа тела.', "moderate": 'Ваши оценки внешности неоднозначны;сосредоточение внимания на функциональности вашего тела расширяет перспективу.', "low": 'Есть склонность негативно оценивать свою внешность;Практики утверждения тела оказывают здесь поддержку.'},
            'body_satisfaction': {"high": 'В целом вы удовлетворены своим телом;признак здорового принятия себя.', "moderate": 'Удовлетворенность вашим телом умеренная;Сосредоточение внимания на сильных сторонах вашего тела питает эту область.', "low": 'Вы чувствуете неудовлетворенность своим телом;Практика самосострадания и профессиональная поддержка могут оказаться полезными.'},
        },
    },
    'ar': {
        'personality': {
            'openness': {"high": 'فضولك وخيالك قويان؛التجارب والأفكار الجديدة تجذبك بشكل طبيعي.', "moderate": 'أنت توازن بين الفضول والتطبيق العملي، والفضول في بعض المجالات والتقليدي في مناطق أخرى.', "low": 'أنت تفضل العملي والمألوف؛الإجراءات الروتينية المتسقة والأساليب التي أثبتت جدواها تبدو مناسبة لك.'},
            'conscientiousness': {"high": 'أنت منضبط ومنظم وموثوق؛أنت تسعى لتحقيق الأهداف بشكل منهجي.', "moderate": 'أنت توازن بين المسؤولية والمرونة.إجراءات البناء من شأنها أن تعزز هذا بشكل أكبر.', "low": 'لديك أسلوب مرن وعفوي.تطوير عادات التخطيط يمكن أن يحسن فعاليتك.'},
            'extraversion': {"high": 'طاقتك الاجتماعية عالية؛أنت تستمد القوة من الناس وتجلب الطاقة لمن حولك.', "moderate": 'أنت توازن بين الوقت الذي تقضيه مع الآخرين والوقت الذي تقضيه بمفردك، وتكون مرتاحًا في كلا الوضعين.', "low": 'إن طبيعتك الانطوائية هي رصيد طبيعي للتفكير العميق والعمل المركّز.'},
            'agreeableness': {"high": 'طبيعتك الدافئة والتعاونية تبني الثقة والانسجام في علاقاتك.', "moderate": 'أنت توازن بين التعاون والاستقلالية والتفاهم مع تأكيد الذات.', "low": 'أنت تميل نحو التفكير النقدي المستقل، وهو ما يمثل قوة للتحليل والحكم الموضوعي.'},
            'neuroticism': {"high": 'يمكن أن تكون ردود أفعالك العاطفية شديدة؛إدارة التوتر واستراتيجيات التنظيم الذاتي سوف تدعمك.', "moderate": 'تواجه بعض التقلبات العاطفية.في معظم الأوقات يمكنك العثور على رصيدك مرة أخرى.', "low": 'مرونتك العاطفية قوية؛تحافظ على هدوئك تحت الضغط وتتعامل مع الصعوبات بسهولة.'},
        },
        'skills': {
            'problem_solving': {"high": 'أنت قوي في تحليل المشكلات المعقدة وإيجاد حلول عملية.', "moderate": 'إن أسلوبك في حل المشكلات يتطور؛تقنيات التفكير المنظم يمكن أن تدعمك.', "low": 'إن تعلم أساليب حل المشكلات المنهجية سيطلق العنان لإمكاناتك في هذا المجال.'},
            'empathy': {"high": 'لديك قدرة رائعة على فهم مشاعر الآخرين والتواصل مع التعاطف.', "moderate": 'تتطور مهارات التعاطف لديك؛ممارسة الاستماع النشط سوف تقوي هذا المجال.', "low": 'إن استكشاف وجهات نظر الآخرين بشكل أكبر سيجعلك أكثر فعالية في التواصل.'},
            'organization': {"high": 'تخطيطك وتحديد أولوياتك قويان؛أسلوبك المنظم يساعدك على التميز.', "moderate": 'مهارتك التنظيمية معقولة.استخدام أدوات إدارة الوقت يمكن أن يجعلك أقوى.', "low": 'إن تطوير عادات تنظيمية منهجية يمكن أن يحسن إنتاجيتك بشكل كبير.'},
            'learning_speed': {"high": 'أنت تتكيف بسرعة مع المعرفة والمهارات الجديدة - وهي ميزة كبيرة في البيئات المتغيرة.', "moderate": 'وتيرة التعلم الخاصة بك معقولة.تجربة استراتيجيات مختلفة يمكن أن تزيد من فعاليتك.', "low": 'ستدعم استراتيجيات المراجعة والممارسة المنظمة عملية التعلم الخاصة بك في هذا المجال.'},
            'decision_making': {"high": 'يمكنك اتخاذ خطوات حاسمة وسريعة في مواقف اتخاذ القرار.', "moderate": 'تتطور مهاراتك في اتخاذ القرار؛تساعد الأطر المنظمة في اللحظات الصعبة.', "low": 'يعد البدء بقرارات أصغر طريقة فعالة لبناء ثقتك في اتخاذ القرار.'},
        },
        'hr': {
            'leadership': {"high": 'أنت قوي في توجيه الفرق وإلهام الآخرين وأخذ زمام المبادرة.', "moderate": 'لديك القدرة على القيادة.فالتجارب العملية ستعمل على تطوير هذه المهارات بسرعة.', "low": 'إن التطوير المتعمد لمهارات القيادة من خلال الممارسة يمكن أن يؤدي إلى تحسين حياتك المهنية بشكل كبير.'},
            'team_fit': {"high": 'أنت تتميز بالعمل الجماعي المتناغم والتعاون والمساعدة.', "moderate": 'فريقك لائق بشكل جيد.إن فهم أساليب العمل المختلفة سيعزز هذا الأمر بشكل أكبر.', "low": 'المشاركة الأكثر نشاطًا في ديناميكيات الفريق ستعزز علاقاتك المهنية.'},
            'communication': {"high": 'أنت قوي في التواصل الواضح والفعال والبناء.', "moderate": 'أسلوب الاتصال الخاص بك يتطور.يمنحك التكيف مع الجماهير المختلفة ميزة.', "low": 'سوف تؤدي ممارسة مهارات الاتصال بشكل منهجي إلى تحقيق تقدم سريع في هذا المجال.'},
            'stress_tolerance': {"high": 'يمكنك الحفاظ على رباطة جأشك تحت الضغط؛حجر الزاوية في المرونة المهنية.', "moderate": 'قدرتك على التعامل مع التوتر معقولة؛تقنيات بناء المرونة ستجعلك أقوى.', "low": 'إن تطوير استراتيجيات إدارة التوتر، بدعم من الممارسات اليومية، يؤدي إلى نتائج سريعة.'},
            'motivation': {"high": 'الدافع الجوهري الخاص بك مرتفع.أنت تقترب من أهدافك بالتزام وشغف.', "moderate": 'الدافع الخاص بك يختلف.البقاء على اتصال بهدفك يمكن أن يكون مصدرًا مستمرًا للطاقة.', "low": 'يعد تحديد أهداف ذات معنى على المدى القصير طريقة فعالة لإعادة إشعال حافزك.'},
        },
        'career': {
            'analytical': {"high": 'لديك توجه قوي نحو التفكير التحليلي وبيئات العمل التي تركز على البيانات.', "moderate": 'لديك ميول تحليلية.الممارسة المنظمة لحل المشكلات ستعزز هذا المجال.', "low": 'سيؤدي تطوير المهارات التحليلية المنهجية إلى توسيع خياراتك في هذا المجال الوظيفي.'},
            'creative': {"high": 'أنت تعبر عن نفسك بشكل أفضل في بيئات العمل الإبداعية والمبتكرة.', "moderate": 'لديك ميول إبداعية.رعاية هذا المجال يمكن أن تزيد من تحقيق حياتك المهنية.', "low": 'تبدو المسارات الوظيفية الهيكلية والفنية حاليًا أكثر توافقًا من الأدوار التي تركز على الإبداع.'},
            'social': {"high": 'إن المساعدة أو التدريس أو العمل مع الناس ينشطك.', "moderate": 'أنت مرتاح في الأدوار التي تنطوي على التفاعل الاجتماعي؛يمكن للاتصالات الأعمق أن تضيف قيمة.', "low": 'لا تعد المسارات الوظيفية التي تركز على المجتمع حاليًا مجال اهتمام قوي بالنسبة لك.'},
            'entrepreneurial': {"high": 'لديك ميل قوي نحو الأدوار الريادية التي تتطلب القيادة والإقناع والمخاطرة.', "moderate": 'منظورك الريادي يتطور؛وستعمل عملية صنع القرار والخبرة القيادية على تسريع ذلك.', "low": 'تبدو المسارات الوظيفية التي تركز على الخبرة حاليًا أكثر توافقًا من أدوار ريادة الأعمال.'},
            'managerial': {"high": 'أنت مناسب تمامًا للأدوار التي تتطلب الإدارة والتنسيق والتنظيم.', "moderate": 'ميولك الإدارية تتطور.تحمل المسؤولية سوف يغذي هذا المجال.', "low": 'قد تشعر المسارات الوظيفية التي تركز على الخبرة مع ضغط إداري أقل براحة أكبر في الوقت الحالي.'},
            'technical': {"high": 'لديك اهتمام قوي وتوجه نحو المجالات التقنية والمتخصصة.', "moderate": 'مهاراتك التقنية تتطور.التخصص العميق سوف يعزز هذا المجال.', "low": 'تبدو المسارات الوظيفية التي تركز على الأشخاص حاليًا أكثر توافقًا من الأدوار المتخصصة الفنية.'},
        },
        'vocation': {
            'realistic': {"high": 'لديك ميل قوي نحو العمل العملي والتدريب العملي والتقني.', "moderate": 'لديك اهتمام معتدل بالعمل العملي؛تجربة هذه المنطقة ستعطيك صورة أوضح.', "low": 'الأنشطة العملية والتقنية ليست من بين اهتماماتك القوية حاليًا.'},
            'investigative': {"high": 'البحث والتحليل واستكشاف الأفكار يجذبك بشكل طبيعي.', "moderate": 'لديك اهتمام بالتحقيق؛وتعميق المعرفة في هذا المجال سيعززها أكثر.', "low": 'الأنشطة التي تركز على البحث والتحليل ليست حاليًا من بين اهتماماتك ذات الأولوية.'},
            'artistic': {"high": 'لديك ميل قوي نحو الأنشطة التي تتطلب التعبير الإبداعي والفن والجماليات.', "moderate": 'لديك ميول فنية.رعاية هذه المنطقة يمكن أن توفر الوفاء والأصالة.', "low": 'الأنشطة الفنية والإبداعية ليست في الوقت الحالي مجال اهتمام قوي بالنسبة لك.'},
            'social': {"high": 'إن التواجد مع الناس والمساعدة والتعليم ينشطك.', "moderate": 'لديك اهتمام معتدل بالأنشطة الاجتماعية.بناء اتصالات ذات معنى يجلب الرضا.', "low": 'الأنشطة التي تركز على المجتمع ليست حاليًا من بين اهتماماتك ذات الأولوية.'},
            'enterprising': {"high": 'تشعر أنك أقوى في الأنشطة التي تتطلب القيادة والإقناع والمنافسة.', "moderate": 'لديك ميول جريئة.وممارسة المسؤولية واتخاذ القرار يعزز ذلك.', "low": 'الأنشطة التنافسية والتي تركز على القيادة ليست في الوقت الحالي مجال اهتمام قوي بالنسبة لك.'},
            'conventional': {"high": 'أنت قوي في بيئات العمل المنظمة والمنهجية والمتسقة مع القواعد.', "moderate": 'لديك اهتمام معتدل بالتنظيم والهيكل؛ممارسة العمل المنهجية تغذي هذا.', "low": 'الأنشطة المنظمة والتقليدية ليست في الوقت الحالي مجال اهتمام قوي بالنسبة لك.'},
        },
        'relationship': {
            'love_language': {"high": 'أنت تعبر بوضوح عن لغة حبك وتقدر التفاهم المتبادل في العلاقات.', "moderate": 'أنت تعبر عن لغة حبك باعتدال؛كونك أكثر انفتاحًا هنا يمكن أن يثري علاقاتك.', "low": 'سيؤدي تطوير الوعي بالتعبير العاطفي ولغات الحب إلى تعميق اتصالاتك.'},
            'conflict_style': {"high": 'أنت قوي في حل النزاعات بطرق بناءة وصحية.', "moderate": 'أسلوبك في حل النزاعات يتطور؛تجربة المزيد من الأساليب البناءة يمكن أن تساعد.', "low": 'سيؤدي تطوير استراتيجيات حل النزاعات الصحية إلى تحسين جودة علاقتك بشكل كبير.'},
            'intimacy_needs': {"high": 'أنت تفهم بوضوح احتياجاتك من التقارب العاطفي والتواصل.', "moderate": 'لديك وعي معتدل باحتياجاتك الحميمية؛يعد استكشاف هذه المنطقة بشكل أكبر أمرًا ذا قيمة.', "low": 'إن فهم احتياجاتك العاطفية والحميمية سيجعل علاقاتك أكثر إشباعًا.'},
            'relationship_values': {"high": 'لديك إطار عمل واضح لما تريده في علاقاتك.', "moderate": 'قيم علاقتك تتشكل؛التفكير في هذا يساعدك على بناء اتصالات أكثر صحة.', "low": 'إن اكتشاف قيم علاقتك الشخصية وتوضيحها يضع الأساس لروابط أعمق.'},
        },
        'attachment': {
            'anxiety': {"high": 'القلق بشأن الهجر مرتفع.يعد هذا الوعي نقطة انطلاق قوية لتطوير الارتباط الآمن.', "moderate": 'قلق التعلق معتدل.ممارسات العلاقة الآمنة تدعم هذا المجال.', "low": 'قلقك من الهجر منخفض.تظهر ارتباطًا آمنًا ومتوازنًا في العلاقات.'},
            'avoidance': {"high": 'من الملحوظ تجنب التقارب العاطفي.إن التعرف على هذا النمط هو الخطوة الأولى نحو روابط أعمق.', "moderate": 'تجنب القرب معتدل.مع نمو الوعي الذاتي، يمكنك بناء المزيد من الاتصالات المفتوحة.', "low": 'تجنبك للتقارب العاطفي منخفض؛الانفتاح والاتصال يشعران بالراحة في العلاقات.'},
        },
        'grit': {
            'perseverance': {"high": 'أنت قوي في استكمال ما بدأته والاستمرار فيه رغم العقبات.', "moderate": 'إن تصميمك وإصرارك يتطوران؛إن البقاء ملتزمًا بالأهداف طويلة المدى يعزز ذلك.', "low": 'إن مراكمة النجاحات قصيرة المدى هي استراتيجية فعالة لبناء المثابرة المستدامة.'},
            'passion': {"high": 'تُظهر شغفًا واهتمامًا ثابتين تجاه أهدافك طويلة المدى.', "moderate": 'شغفك بالأهداف يتطور؛الاتصال بهدف هادف يضخم هذه الطاقة.', "low": 'إن اكتشاف الاهتمامات التي تثيرك حقًا سيغذي شغفك وتحفيزك.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'أنت تؤمن بشدة أنه يمكن تطوير القدرات والذكاء من خلال الجهد.', "moderate": 'عقلية النمو لديك تتطور؛إن النظر إلى التحديات باعتبارها فرصًا للتعلم يعزز هذا الأمر.', "low": 'ويستمر الاعتقاد بأن القدرات ثابتة؛إن التشكيك في هذه العقلية سيؤدي إلى تسريع نموك.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'لقد أبلغت عن رضاك \u200b\u200bالشديد عن حياتك وقمت بإجراء تقييم إيجابي شامل.', "moderate": 'رضاك عن الحياة معتدل؛تعزيز التوافق بين المعنى والقيمة يزيد من الإشباع.', "low": 'الرضا عن الحياة منخفض؛إن سؤال نفسك عما تريد تغييره يعد نقطة انطلاق جيدة.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'أنت تقترب من نفسك بالرحمة والتفاهم؛مصدر قوي للمرونة النفسية.', "moderate": 'إن تعاطفك مع نفسك يتطور؛التحدث مع نفسك كصديق في اللحظات الصعبة يغذي هذا.', "low": 'صوت داخلي خشن بارز.تطوير ممارسات التعاطف الذاتي سوف يدعمك.'},
            'self_judgment': {"high": 'هناك ميل إلى الإفراط في النقد الذاتي؛والاعتراف بهذا هو نقطة انطلاق قوية للتغيير.', "moderate": 'النقد الذاتي معتدل.أن تكون لطيفًا مع نفسك يجلب لك أحيانًا فائدة.', "low": 'تظهر موقفًا متوازنًا ولطيفًا تجاه نفسك؛علامة صحية للتقييم الذاتي.'},
            'common_humanity': {"high": 'أنت تدرك أن صراعاتك هي جزء من التجربة الإنسانية المشتركة، والتي تجلب لك الراحة.', "moderate": 'إن إحساسك بالإنسانية المشتركة يتطور؛تذكر أنك لست وحدك يقويك.', "low": 'قد تشعر بالعزلة عند ظهور الصعوبات؛تذكر أن هذه تجربة شائعة جدًا.'},
            'isolation': {"high": 'تشعر بالعزلة والوحدة في اللحظات الصعبة؛البحث عن الاتصال والدعم يساعد في تحقيق التوازن بين ذلك.', "moderate": 'يمكن أن تنشأ مشاعر العزلة من وقت لآخر؛يساعد بناء الاتصالات على تحقيق التوازن في هذا الأمر.', "low": 'تشعر بالارتباط والدعم عند مواجهة الصعوبات؛علامة مهمة على الصحة النفسية.'},
            'mindfulness': {"high": 'يمكنك مراقبة عواطفك بتوازن ووعي؛موقف نفسي سليم .', "moderate": 'إن وعيك الواعي يتطور؛ممارسات التأمل البسيطة ستقوي هذا المجال.', "low": 'هناك ميل إلى قمع المشاعر بدلاً من مراقبتها؛ممارسات اليقظة الذهنية يمكن أن توفر الدعم.'},
            'overidentification': {"high": 'هناك ميل إلى الإفراط في التركيز على المشاعر والأفكار السلبية؛ممارسات اليقظة الذهنية تكسر هذه الدورة.', "moderate": 'يمكنك في بعض الأحيان المبالغة في التماثل مع الأفكار السلبية؛استراتيجيات التوازن تساعد.', "low": 'تحافظ على مسافة صحية من الأفكار السلبية؛مؤشر قوي على الوعي الواعي.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'لديك إيمان قوي بقدرتك على إنجاز المهام الصعبة.', "moderate": 'إن إيمانك بالكفاءة الذاتية يتطور؛وتراكم النجاحات الصغيرة يزيد من هذه الثقة.', "low": 'الثقة في قدراتك الخاصة منخفضة؛بناء تجارب النجاح من خلال خطوات صغيرة يساعد.'},
        },
        'stress': {
            'perceived_stress': {"high": 'أنت تشعر بمستوى عالٍ من التوتر مؤخرًا؛استراتيجيات إدارة التوتر لها أهمية خاصة الآن.', "moderate": 'أنت تعاني من إجهاد معتدل.تحديد وإدارة مسببات التوتر يجلب الفائدة.', "low": 'مستوى إدراكك للتوتر منخفض؛تبدو قدرتك على التعامل مع التحديات قوية.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'تقوم بتقييم مظهرك بشكل إيجابي بشكل عام؛علامة على صورة الجسم السليم.', "moderate": 'تقييمات مظهرك مختلطة.التركيز على وظائف جسمك يوسع المنظور.', "low": 'هناك ميل لتقييم مظهرك بشكل سلبي؛ممارسات تأكيد الجسم توفر الدعم هنا.'},
            'body_satisfaction': {"high": 'أنت راضٍ بشكل عام عن جسمك؛علامة على قبول الذات الصحي.', "moderate": 'رضا جسمك معتدل.التركيز على نقاط القوة في جسمك يغذي هذه المنطقة.', "low": 'تشعر بعدم الرضا عن جسدك؛قد تكون ممارسات التعاطف الذاتي والدعم المهني مفيدة.'},
        },
    },
    'es': {
        'personality': {
            'openness': {"high": 'Tu curiosidad e imaginación son fuertes;Nuevas experiencias e ideas te atraen naturalmente.', "moderate": 'Equilibras la curiosidad con la practicidad, curioso en algunas áreas y convencional en otras.', "low": 'Prefieres lo práctico y familiar;Las rutinas consistentes y los enfoques probados le parecen adecuados.'},
            'conscientiousness': {"high": 'Eres disciplinado, organizado y confiable;persigues objetivos sistemáticamente.', "moderate": 'Equilibra responsabilidad y flexibilidad;La construcción de rutinas fortalecería esto aún más.', "low": 'Tienes un estilo flexible y espontáneo;desarrollar hábitos de planificación puede mejorar su eficacia.'},
            'extraversion': {"high": 'Tu energía social es alta;Obtienes fuerza de las personas y aportas energía a quienes te rodean.', "moderate": 'Equilibras el tiempo con los demás y el tiempo a solas, y te sientes cómodo en ambos entornos.', "low": 'Su naturaleza introvertida es un activo natural para el pensamiento profundo y el trabajo concentrado.'},
            'agreeableness': {"high": 'Su naturaleza cálida y cooperativa genera confianza y armonía en sus relaciones.', "moderate": 'Equilibra la cooperación y la independencia, siendo comprensivo pero asertivo.', "low": 'Se inclina hacia el pensamiento crítico e independiente: una fortaleza para el análisis y el juicio objetivo.'},
            'neuroticism': {"high": 'Tus reacciones emocionales pueden ser intensas;Las estrategias de gestión del estrés y autorregulación le ayudarán.', "moderate": 'Experimentas algunos altibajos emocionales;la mayoría de las veces podrás recuperar el equilibrio.', "low": 'Tu resiliencia emocional es fuerte;Mantienes la calma bajo presión y manejas las dificultades con facilidad.'},
        },
        'skills': {
            'problem_solving': {"high": 'Eres fuerte analizando problemas complejos y generando soluciones prácticas.', "moderate": 'Su enfoque de resolución de problemas se está desarrollando;Las técnicas de pensamiento estructurado pueden ayudarte.', "low": 'Aprender métodos sistemáticos de resolución de problemas desbloqueará su potencial en esta área.'},
            'empathy': {"high": 'Tienes una capacidad notable para comprender las emociones de los demás y conectar con la empatía.', "moderate": 'Tus habilidades de empatía se están desarrollando;practicar la escucha activa fortalecerá esta área.', "low": 'Explorar más las perspectivas de los demás le convertirá en un comunicador más eficaz.'},
            'organization': {"high": 'Su planificación y priorización son sólidas;Tu estilo organizado te ayuda a destacar.', "moderate": 'Su habilidad organizativa es razonable;El uso de herramientas de gestión del tiempo puede hacerte aún más fuerte.', "low": 'Desarrollar hábitos organizacionales sistemáticos puede mejorar significativamente su productividad.'},
            'learning_speed': {"high": 'Se adapta rápidamente a nuevos conocimientos y habilidades, una gran ventaja en entornos cambiantes.', "moderate": 'Su ritmo de aprendizaje es razonable;experimentar con diferentes estrategias puede aumentar su efectividad.', "low": 'Las estrategias estructuradas de revisión y práctica respaldarán su proceso de aprendizaje en esta área.'},
            'decision_making': {"high": 'Puede tomar medidas rápidas y decisivas en situaciones de toma de decisiones.', "moderate": 'Tus habilidades para tomar decisiones se están desarrollando;Los marcos estructurados ayudan en momentos difíciles.', "low": 'Comenzar con decisiones más pequeñas es una forma eficaz de desarrollar su confianza en la toma de decisiones.'},
        },
        'hr': {
            'leadership': {"high": 'Eres fuerte para dirigir equipos, inspirar a otros y tomar la iniciativa.', "moderate": 'Tienes aptitud de liderazgo;Las experiencias prácticas desarrollarán estas habilidades rápidamente.', "low": 'Desarrollar deliberadamente habilidades de liderazgo a través de la práctica puede hacer avanzar significativamente su carrera.'},
            'team_fit': {"high": 'Destacas por el trabajo armonioso en equipo, la colaboración y la amabilidad.', "moderate": 'La forma de tu equipo es buena;comprender diferentes estilos de trabajo fortalecerá esto aún más.', "low": 'Una participación más activa en las dinámicas de equipo fortalecerá tus relaciones profesionales.'},
            'communication': {"high": 'Eres fuerte en la comunicación clara, efectiva y constructiva.', "moderate": 'Su estilo de comunicación se está desarrollando;adaptarse a diferentes públicos te da una ventaja.', "low": 'La práctica sistemática de las habilidades comunicativas producirá un rápido progreso en esta área.'},
            'stress_tolerance': {"high": 'Puedes mantener la compostura bajo presión;una piedra angular de la resiliencia profesional.', "moderate": 'Su capacidad para afrontar el estrés es razonable;Las técnicas de desarrollo de la resiliencia te harán aún más fuerte.', "low": 'Desarrollar estrategias de manejo del estrés, respaldadas por prácticas diarias, produce resultados rápidamente.'},
            'motivation': {"high": 'Tu motivación intrínseca es alta;abordas tus objetivos con compromiso y pasión.', "moderate": 'Tu motivación varía;permanecer conectado con su propósito puede ser una fuente de energía continua.', "low": 'Establecer objetivos significativos a corto plazo es una forma eficaz de reavivar su motivación.'},
        },
        'career': {
            'analytical': {"high": 'Tiene una fuerte orientación hacia el pensamiento analítico y los entornos de trabajo centrados en datos.', "moderate": 'Tienes tendencias analíticas;La práctica estructurada de resolución de problemas fortalecerá esta área.', "low": 'Desarrollar habilidades analíticas sistemáticas ampliará sus opciones en esta área profesional.'},
            'creative': {"high": 'Te expresas mejor en entornos de trabajo creativos e innovadores.', "moderate": 'Tienes tendencias creativas;nutrir esta área puede aumentar su realización profesional.', "low": 'Actualmente, las trayectorias profesionales estructurales y técnicas parecen más alineadas que los roles centrados en la creatividad.'},
            'social': {"high": 'Ayudar, enseñar o trabajar con personas te da energía.', "moderate": 'Se siente cómodo en roles que implican interacción social;conexiones más profundas pueden agregar valor.', "low": 'Las carreras profesionales centradas en lo social no son actualmente un área de gran interés para usted.'},
            'entrepreneurial': {"high": 'Tiene una fuerte tendencia hacia roles empresariales que requieren liderazgo, persuasión y asunción de riesgos.', "moderate": 'Su perspectiva empresarial se está desarrollando;La experiencia en toma de decisiones y liderazgo acelerará esto.', "low": 'Actualmente, las trayectorias profesionales centradas en la experiencia parecen más alineadas que las funciones empresariales.'},
            'managerial': {"high": 'Está bien preparado para roles que requieren gestión, coordinación y organización.', "moderate": 'Sus tendencias gerenciales se están desarrollando;asumir responsabilidades nutrirá esta área.', "low": 'Las trayectorias profesionales centradas en la experiencia y con menos presión gerencial pueden resultar más cómodas en este momento.'},
            'technical': {"high": 'Tienes un fuerte interés y orientación hacia campos técnicos y especializados.', "moderate": 'Tus habilidades técnicas se están desarrollando;Una profunda especialización fortalecerá esta área.', "low": 'Actualmente, las trayectorias profesionales centradas en las personas parecen más alineadas que las funciones de especialistas técnicos.'},
        },
        'vocation': {
            'realistic': {"high": 'Tienes una fuerte inclinación hacia el trabajo práctico, práctico y técnico.', "moderate": 'Tiene un interés moderado en el trabajo práctico;probar esta área le dará una imagen más clara.', "low": 'Las actividades prácticas y técnicas no se encuentran actualmente entre sus fuertes intereses.'},
            'investigative': {"high": 'La investigación, el análisis y la exploración de ideas le atraen naturalmente.', "moderate": 'Tiene interés de investigación;profundizar el conocimiento en esta área la fortalecerá aún más.', "low": 'Las actividades centradas en la investigación y el análisis no se encuentran actualmente entre sus intereses prioritarios.'},
            'artistic': {"high": 'Tienes una fuerte inclinación hacia actividades que requieren expresión creativa, arte y estética.', "moderate": 'Tienes tendencias artísticas;nutrir esta área puede proporcionar plenitud y autenticidad.', "low": 'Las actividades artísticas y creativas no son actualmente un área de gran interés para usted.'},
            'social': {"high": 'Estar con gente, ayudar y enseñar te da energía.', "moderate": 'Tiene un interés moderado en las actividades sociales;construir conexiones significativas trae satisfacción.', "low": 'Las actividades centradas en lo social no se encuentran actualmente entre sus intereses prioritarios.'},
            'enterprising': {"high": 'Se siente más fuerte en actividades que requieren liderazgo, persuasión y competencia.', "moderate": 'Tienes tendencias emprendedoras;practicar la responsabilidad y la toma de decisiones fortalece esto.', "low": 'Las actividades competitivas y centradas en el liderazgo no son actualmente un área de gran interés para usted.'},
            'conventional': {"high": 'Eres fuerte en ambientes de trabajo organizados, sistemáticos y consistentes con reglas.', "moderate": 'Tienes un interés moderado en la organización y la estructura;la práctica sistemática del trabajo fomenta esto.', "low": 'Las actividades estructuradas y convencionales no son actualmente un área de gran interés para usted.'},
        },
        'relationship': {
            'love_language': {"high": 'Expresas claramente tu lenguaje de amor y valoras la comprensión mutua en las relaciones.', "moderate": 'Expresas tu lenguaje de amor moderadamente;ser más abierto aquí puede enriquecer sus relaciones.', "low": 'Desarrollar conciencia de la expresión emocional y los lenguajes del amor profundizará sus conexiones.'},
            'conflict_style': {"high": 'Eres fuerte para resolver conflictos de manera constructiva y saludable.', "moderate": 'Su estilo de resolución de conflictos se está desarrollando;probar enfoques más constructivos puede ayudar.', "low": 'Desarrollar estrategias saludables de resolución de conflictos mejorará significativamente la calidad de su relación.'},
            'intimacy_needs': {"high": 'Entiendes claramente tus necesidades de cercanía y conexión emocional.', "moderate": 'Tienes una conciencia moderada de tus necesidades de intimidad;Es valioso explorar más a fondo esta área.', "low": 'Comprender sus vínculos emocionales y sus necesidades de intimidad hará que sus relaciones sean más satisfactorias.'},
            'relationship_values': {"high": 'Tienes un marco de valores claro para lo que quieres en tus relaciones.', "moderate": 'Los valores de tu relación están tomando forma;Reflexionar sobre esto te ayuda a construir conexiones más saludables.', "low": 'Descubrir y aclarar los valores de sus relaciones personales sienta las bases para vínculos más profundos.'},
        },
        'attachment': {
            'anxiety': {"high": 'La ansiedad por el abandono es alta;Esta conciencia es un sólido punto de partida para desarrollar un apego seguro.', "moderate": 'La ansiedad por apego es moderada;Las prácticas de relaciones seguras respaldan esta área.', "low": 'Tu ansiedad de abandono es baja;Muestras un apego seguro y equilibrado en las relaciones.'},
            'avoidance': {"high": 'Se nota la evitación de la cercanía emocional;Reconocer este patrón es el primer paso hacia vínculos más profundos.', "moderate": 'La evitación de la cercanía es moderada;A medida que crece la autoconciencia, puedes construir conexiones más abiertas.', "low": 'Tu evitación de la cercanía emocional es baja;La apertura y la conexión se sienten cómodos en las relaciones.'},
        },
        'grit': {
            'perseverance': {"high": 'Eres fuerte para completar lo que comienzas y continuar a pesar de los obstáculos.', "moderate": 'Tu determinación y valor se están desarrollando;Mantener el compromiso con objetivos a largo plazo fortalece esto.', "low": 'Acumular éxitos a corto plazo es una estrategia eficaz para construir una perseverancia sostenible.'},
            'passion': {"high": 'Muestra pasión e interés constantes hacia sus objetivos a largo plazo.', "moderate": 'Tu pasión por las metas se está desarrollando;conectarse con un propósito significativo amplifica esta energía.', "low": 'Descubrir intereses que realmente te entusiasmen alimentará tu pasión y motivación.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'Cree firmemente que las habilidades y la inteligencia se pueden desarrollar mediante el esfuerzo.', "moderate": 'Tu mentalidad de crecimiento se está desarrollando;ver los desafíos como oportunidades de aprendizaje fomenta esto.', "low": 'La creencia de que las habilidades son fijas continúa;Cuestionar esta mentalidad acelerará tu crecimiento.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'Usted declara estar muy satisfecho con su vida y hace una evaluación general positiva.', "moderate": 'Su satisfacción con la vida es moderada;fortalecer la alineación significado-valor aumenta la satisfacción.', "low": 'La satisfacción con la vida es baja;Preguntarse qué quiere cambiar es un buen punto de partida.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'Te acercas a ti mismo con compasión y comprensión;una fuerte fuente de resiliencia psicológica.', "moderate": 'Tu autocompasión se está desarrollando;hablar contigo mismo como un amigo en los momentos difíciles fomenta esto.', "low": 'Se destaca una voz interior áspera;Desarrollar prácticas de autocompasión te ayudará.'},
            'self_judgment': {"high": 'Hay una tendencia a ser demasiado autocrítico;Reconocer esto es un poderoso punto de partida para el cambio.', "moderate": 'La autocrítica es moderada;ser más amable contigo mismo a veces trae beneficios.', "low": 'Muestras una actitud equilibrada y amable contigo mismo;una señal saludable de autoevaluación.'},
            'common_humanity': {"high": 'Entiendes que tus luchas son parte de la experiencia humana compartida, lo que trae consuelo.', "moderate": 'Vuestro sentido de humanidad común se está desarrollando;recordar que no estás solo te fortalece.', "low": 'Puede que te sientas aislado cuando surgen dificultades;Recuerde que esta es una experiencia muy común.'},
            'isolation': {"high": 'Te sientes aislado y solo en momentos difíciles;buscar conexión y apoyo ayuda a equilibrar esto.', "moderate": 'De vez en cuando pueden surgir sentimientos de aislamiento;construir conexiones ayuda a equilibrar esto.', "low": 'Te sientes conectado y apoyado ante las dificultades;un signo importante de salud psicológica.'},
            'mindfulness': {"high": 'Puedes observar tus emociones con equilibrio y conciencia;una postura psicológica saludable.', "moderate": 'Tu conciencia consciente se está desarrollando;Prácticas simples de meditación fortalecerán esta área.', "low": 'Existe una tendencia a reprimir las emociones en lugar de observarlas;Las prácticas de atención plena pueden proporcionar apoyo.'},
            'overidentification': {"high": 'Existe una tendencia a centrarse demasiado en las emociones y pensamientos negativos;Las prácticas de atención plena rompen este ciclo.', "moderate": 'A veces puedes identificarte demasiado con pensamientos negativos;Las estrategias de equilibrio ayudan.', "low": 'Mantienes una sana distancia de los pensamientos negativos;un fuerte indicador de conciencia consciente.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'Cree firmemente en su capacidad para realizar tareas desafiantes.', "moderate": 'Su creencia de autoeficacia se está desarrollando;acumular pequeños éxitos aumenta esta confianza.', "low": 'La confianza en las propias capacidades es baja;Construir experiencias de éxito a través de pequeños pasos ayuda.'},
        },
        'stress': {
            'perceived_stress': {"high": 'Estás percibiendo un alto nivel de estrés recientemente;Las estrategias de manejo del estrés son especialmente importantes ahora.', "moderate": 'Está experimentando un estrés moderado;Identificar y controlar los desencadenantes del estrés resulta beneficioso.', "low": 'Tu nivel de percepción del estrés es bajo;su capacidad para manejar desafíos parece fuerte.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'Valoras tu apariencia en general de manera positiva;un signo de imagen corporal saludable.', "moderate": 'Sus evaluaciones de apariencia son mixtas;centrarse en la funcionalidad de su cuerpo amplía la perspectiva.', "low": 'Existe una tendencia a evaluar negativamente su apariencia;Las prácticas de afirmación corporal brindan apoyo aquí.'},
            'body_satisfaction': {"high": 'Generalmente estás satisfecho con tu cuerpo;un signo de sana autoaceptación.', "moderate": 'Tu satisfacción corporal es moderada;centrarse en las fortalezas de su cuerpo nutre esta área.', "low": 'Te sientes insatisfecho con tu cuerpo;Las prácticas de autocompasión y el apoyo profesional pueden ser beneficiosos.'},
        },
    },
    'ko': {
        'personality': {
            'openness': {"high": '당신의 호기심과 상상력은 강합니다.새로운 경험과 아이디어는 자연스럽게 당신을 끌어당깁니다.', "moderate": '당신은 호기심과 실용성의 균형을 맞추며, 일부 분야에서는 호기심이 많고 다른 분야에서는 관습적입니다.', "low": '당신은 실용적이고 친숙한 것을 선호합니다.일관된 루틴과 입증된 접근 방식이 귀하에게 적합하다고 생각됩니다.'},
            'conscientiousness': {"high": '당신은 규율 있고 조직적이며 신뢰할 수 있습니다.당신은 체계적으로 목표를 추구합니다.', "moderate": '책임감과 유연성의 균형을 유지하세요.루틴을 구축하면 이를 더욱 강화할 수 있습니다.', "low": '당신은 유연하고 자발적인 스타일을 가지고 있습니다.계획 습관을 개발하면 효율성이 향상될 수 있습니다.'},
            'extraversion': {"high": '당신의 사회적 에너지는 높습니다.당신은 사람들로부터 힘을 얻고 주변 사람들에게 에너지를 가져옵니다.', "moderate": '다른 사람과의 시간과 혼자 있는 시간의 균형을 유지하며 두 환경 모두에서 편안합니다.', "low": '당신의 내성적인 성격은 깊은 사고와 집중적인 업무를 위한 타고난 자산입니다.'},
            'agreeableness': {"high": '당신의 따뜻하고 협조적인 성격은 관계에서 신뢰와 조화를 구축합니다.', "moderate": '당신은 협력성과 독립성, 이해심과 자기 주장의 균형을 유지합니다.', "low": '당신은 분석과 객관적인 판단의 강점인 독립적이고 비판적인 사고를 지향합니다.'},
            'neuroticism': {"high": '당신의 감정적 반응은 강렬할 수 있습니다.스트레스 관리와 자기 조절 전략이 도움이 될 것입니다.', "moderate": '당신은 감정적 기복을 경험합니다.대부분의 경우 잔액을 다시 찾을 수 있습니다.', "low": '당신의 정서적 회복력은 강합니다.당신은 압박감 속에서도 침착함을 유지하고 어려움을 쉽게 처리합니다.'},
        },
        'skills': {
            'problem_solving': {"high": '당신은 복잡한 문제를 분석하고 실용적인 해결책을 찾는 데 강합니다.', "moderate": '귀하의 문제 해결 접근 방식이 발전하고 있습니다.구조화된 사고 기술이 당신을 지원할 수 있습니다.', "low": '체계적인 문제 해결 방법을 배우면 이 분야에서 잠재력을 발휘할 수 있습니다.'},
            'empathy': {"high": '당신은 다른 사람의 감정을 이해하고 공감하는 놀라운 능력을 가지고 있습니다.', "moderate": '당신의 공감 능력이 발전하고 있습니다.적극적으로 경청하는 연습을 하면 이 영역이 강화됩니다.', "low": '다른 사람의 관점을 더 많이 탐구하면 더 효과적인 의사소통자가 될 수 있습니다.'},
            'organization': {"high": '귀하의 계획과 우선 순위는 강력합니다.당신의 정리된 스타일은 당신을 돋보이게 하는 데 도움이 됩니다.', "moderate": '귀하의 조직 능력은 합리적입니다.시간 관리 도구를 사용하면 더욱 강해질 수 있습니다.', "low": '체계적인 조직 습관을 개발하면 생산성이 크게 향상될 수 있습니다.'},
            'learning_speed': {"high": '새로운 지식과 기술에 빠르게 적응할 수 있으며 이는 변화하는 환경에서 큰 이점이 됩니다.', "moderate": '귀하의 학습 속도는 합리적입니다.다양한 전략을 실험해 보면 효율성이 높아질 수 있습니다.', "low": '구조화된 검토 및 연습 전략은 이 분야의 학습 과정을 지원합니다.'},
            'decision_making': {"high": '의사결정 상황에서 결정적이고 빠른 조치를 취할 수 있습니다.', "moderate": '귀하의 의사결정 능력이 발전하고 있습니다.구조화된 프레임워크는 어려운 순간에 도움이 됩니다.', "low": '작은 결정부터 시작하는 것은 의사결정에 대한 자신감을 키우는 효과적인 방법입니다.'},
        },
        'hr': {
            'leadership': {"high": '당신은 팀을 지휘하고, 다른 사람들에게 영감을 주고, 주도하는 데 강합니다.', "moderate": '당신은 리더십 적성을 갖고 있습니다.실제 경험을 통해 이러한 기술을 빠르게 개발할 수 있습니다.', "low": '연습을 통해 의도적으로 리더십 기술을 개발하면 경력이 크게 발전할 수 있습니다.'},
            'team_fit': {"high": '당신은 조화로운 팀워크, 협력, 도움을 주는 면에서 두각을 나타냅니다.', "moderate": '당신의 팀 핏은 좋습니다.다양한 작업 스타일을 이해하면 이를 더욱 강화할 수 있습니다.', "low": '팀 역학에 더욱 적극적으로 참여하면 전문적인 관계가 강화됩니다.'},
            'communication': {"high": '당신은 명확하고 효과적이며 건설적인 의사소통에 능숙합니다.', "moderate": '귀하의 의사소통 스타일이 발전하고 있습니다.다양한 청중에 적응하면 이점이 있습니다.', "low": '의사소통 기술을 체계적으로 연습하면 이 분야에서 빠른 발전을 이룰 수 있습니다.'},
            'stress_tolerance': {"high": '압박감 속에서도 평정심을 유지할 수 있습니다.직업적 탄력성의 초석.', "moderate": '귀하의 스트레스 대처 능력은 합리적입니다.탄력성을 키우는 기술은 당신을 더욱 강하게 만들 것입니다.', "low": '일상적인 실천을 바탕으로 스트레스 관리 전략을 개발하면 빠르게 결과를 얻을 수 있습니다.'},
            'motivation': {"high": '당신의 내재적 동기는 높습니다.당신은 헌신과 열정으로 목표에 접근합니다.', "moderate": '당신의 동기는 다양합니다.목적에 계속 연결되어 있으면 지속적인 에너지원이 될 수 있습니다.', "low": '의미 있는 단기 목표를 설정하는 것은 동기를 다시 부여하는 효과적인 방법입니다.'},
        },
        'career': {
            'analytical': {"high": '당신은 분석적 사고와 데이터 중심 작업 환경에 대한 강한 지향성을 가지고 있습니다.', "moderate": '당신은 분석적인 경향이 있습니다.구조화된 문제 해결 실천은 이 영역을 강화할 것입니다.', "low": '체계적인 분석 기술을 개발하면 이 직업 분야에서 선택의 폭이 넓어질 것입니다.'},
            'creative': {"high": '창의적이고 혁신적인 작업 환경에서 자신을 가장 잘 표현할 수 있습니다.', "moderate": '당신은 창의적인 경향이 있습니다.이 영역을 육성하면 경력 성취도가 높아질 수 있습니다.', "low": '구조적 및 기술적 경력 경로는 현재 창의적 중심 역할보다 더 일치하는 것처럼 보입니다.'},
            'social': {"high": '사람들을 돕고, 가르치고, 함께 일하는 것은 당신에게 활력을 줍니다.', "moderate": '당신은 사회적 상호 작용과 관련된 역할에 편안함을 느낍니다.더 깊은 연결이 가치를 더할 수 있습니다.', "low": '사회 중심 직업 경로는 현재 귀하에게 큰 관심 분야가 아닙니다.'},
            'entrepreneurial': {"high": '당신은 리더십, 설득, 위험 감수가 필요한 기업가적 역할에 대한 강한 경향이 있습니다.', "moderate": '귀하의 기업가적 관점이 발전하고 있습니다.의사결정과 리더십 경험이 이를 가속화할 것입니다.', "low": '전문 지식 중심의 경력 경로는 현재 기업가 역할보다 더 일치하는 것처럼 보입니다.'},
            'managerial': {"high": '당신은 관리, 조정, 조직이 필요한 역할에 매우 적합합니다.', "moderate": '귀하의 관리 경향이 발전하고 있습니다.책임을 지는 것은 이 영역을 육성할 것입니다.', "low": '관리적 부담이 덜하고 전문 지식 중심의 경력 경로가 지금은 더 편안하게 느껴질 수 있습니다.'},
            'technical': {"high": '당신은 기술 및 전문 분야에 대한 강한 관심과 지향성을 가지고 있습니다.', "moderate": '귀하의 기술 능력이 발전하고 있습니다.심층적인 전문화는 이 영역을 강화할 것입니다.', "low": '사람 중심의 경력 경로는 현재 기술 전문가 역할보다 더 일치하는 것으로 보입니다.'},
        },
        'vocation': {
            'realistic': {"high": '당신은 실용적이고 실무적이며 기술적인 작업에 대한 강한 성향을 가지고 있습니다.', "moderate": '당신은 실습에 적당한 관심을 갖고 있습니다.이 영역을 시도해 보면 더 선명한 그림을 얻을 수 있습니다.', "low": '실용적이고 기술적인 활동은 현재 귀하의 주요 관심사가 아닙니다.'},
            'investigative': {"high": '연구, 분석, 아이디어 탐구는 자연스럽게 당신의 마음을 사로잡습니다.', "moderate": '귀하는 조사에 관심이 있습니다.이 분야에 대한 지식을 심화시키면 더욱 강화될 것입니다.', "low": '연구 및 분석 중심 활동은 현재 귀하의 최우선 관심사가 아닙니다.'},
            'artistic': {"high": '당신은 창의적인 표현, 예술, 미학을 요구하는 활동에 대한 성향이 강합니다.', "moderate": '당신은 예술적 성향을 가지고 있습니다.이 영역을 육성하면 성취감과 진정성을 얻을 수 있습니다.', "low": '예술적이고 창의적인 활동은 현재 귀하에게 큰 관심 분야가 아닙니다.'},
            'social': {"high": '사람들과 함께 있고, 돕고, 가르치는 것은 당신에게 활력을 줍니다.', "moderate": '당신은 사회 활동에 적당한 관심을 갖고 있습니다.의미 있는 관계를 구축하면 만족을 얻게 됩니다.', "low": '사회 중심 활동은 현재 귀하의 우선 관심사가 아닙니다.'},
            'enterprising': {"high": '당신은 리더십, 설득, 경쟁이 필요한 활동에서 가장 강한 느낌을 받습니다.', "moderate": '당신은 진취적인 성향을 가지고 있습니다.책임과 의사결정을 실천하면 이를 강화할 수 있습니다.', "low": '경쟁적이고 리더십에 초점을 맞춘 활동은 현재 귀하의 큰 관심 분야가 아닙니다.'},
            'conventional': {"high": '당신은 조직적이고 체계적이며 규칙을 준수하는 작업 환경에 강합니다.', "moderate": '당신은 조직과 구조에 적당한 관심을 갖고 있습니다.체계적인 업무 관행이 이를 뒷받침합니다.', "low": '체계적이고 전통적인 활동은 현재 귀하의 관심 분야가 아닙니다.'},
        },
        'relationship': {
            'love_language': {"high": '당신은 사랑의 언어를 명확하게 표현하고 관계에서의 상호 이해를 중요하게 생각합니다.', "moderate": '당신은 사랑의 언어를 적당히 표현합니다.여기에서 좀 더 개방적인 태도를 취하면 관계가 더욱 풍요로워질 수 있습니다.', "low": '감정 표현과 사랑의 언어에 대한 인식을 발전시키면 관계가 깊어질 것입니다.'},
            'conflict_style': {"high": '당신은 건설적이고 건전한 방법으로 갈등을 해결하는 데 강합니다.', "moderate": '귀하의 갈등 해결 스타일이 발전하고 있습니다.보다 건설적인 접근 방식을 시도하는 것이 도움이 될 수 있습니다.', "low": '건전한 갈등 해결 전략을 개발하면 관계의 질이 크게 향상됩니다.'},
            'intimacy_needs': {"high": '당신은 정서적 친밀감과 연결에 대한 욕구를 분명히 이해합니다.', "moderate": '당신은 친밀감 요구에 대해 어느 정도 인식하고 있습니다.이 영역을 더 깊이 탐구하는 것은 가치 있는 일입니다.', "low": '감정적 유대감과 친밀감 요구 사항을 이해하면 관계가 더욱 만족스러워질 것입니다.'},
            'relationship_values': {"high": '당신은 관계에서 원하는 것에 대한 명확한 가치 체계를 가지고 있습니다.', "moderate": '귀하의 관계 가치가 구체화되고 있습니다.이를 반영하면 더 건강한 연결을 구축하는 데 도움이 됩니다.', "low": '당신의 개인적인 관계 가치를 발견하고 명확히 하는 것은 더 깊은 유대감을 위한 토대를 마련합니다.'},
        },
        'attachment': {
            'anxiety': {"high": '버림받는 것에 대한 불안감이 높습니다.이러한 인식은 안정 애착을 개발하기 위한 강력한 출발점입니다.', "moderate": '애착 불안은 보통 수준입니다.안전한 관계 관행은 이 영역을 지원합니다.', "low": '당신의 포기 불안은 낮습니다.당신은 관계에서 안전하고 균형 잡힌 애착을 보여줍니다.'},
            'avoidance': {"high": '정서적 친밀감을 피하는 것이 눈에 띕니다.이 패턴을 인식하는 것이 더 깊은 유대를 향한 첫 번째 단계입니다.', "moderate": '친밀감을 피하는 것은 보통 수준입니다.자기 인식이 커짐에 따라 더 많은 열린 관계를 구축할 수 있습니다.', "low": '정서적 친밀감을 피하는 정도가 낮습니다.개방성과 연결성은 관계에서 편안함을 느낍니다.'},
        },
        'grit': {
            'perseverance': {"high": '당신은 시작한 일을 완수하고 장애물에도 불구하고 계속하는 데 강합니다.', "moderate": '당신의 결단력과 투지가 발전하고 있습니다.장기적인 목표에 전념하는 것이 이를 강화합니다.', "low": '단기적인 성공을 축적하는 것은 지속 가능한 인내심을 구축하기 위한 효과적인 전략입니다.'},
            'passion': {"high": '당신은 장기적인 목표에 대해 일관된 열정과 관심을 보입니다.', "moderate": '목표에 대한 당신의 열정이 발전하고 있습니다.의미 있는 목적과 연결되면 이 에너지가 증폭됩니다.', "low": '당신을 진정으로 불타오르게 하는 관심사를 발견하는 것은 당신의 열정과 동기를 불러일으킬 것입니다.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": '당신은 노력을 통해 능력과 지능이 발전할 수 있다고 굳게 믿습니다.', "moderate": '당신의 성장 사고방식이 발전하고 있습니다.도전을 학습 기회로 보는 것이 이를 촉진합니다.', "low": '능력은 고정되어 있다는 믿음은 계속됩니다.이러한 사고방식에 의문을 제기하면 성장이 가속화됩니다.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": '당신은 자신의 삶에 대해 높은 만족도를 보고하고 전반적으로 긍정적인 평가를 내립니다.', "moderate": '당신의 삶의 만족도는 보통입니다.의미-가치 정렬을 강화하면 성취도가 높아집니다.', "low": '삶의 만족도가 낮습니다.무엇을 바꾸고 싶은지 스스로에게 물어보는 것이 좋은 출발점입니다.'},
        },
        'self_compassion': {
            'self_kindness': {"high": '당신은 연민과 이해심을 가지고 자신에게 접근합니다.심리적 회복력의 강력한 원천.', "moderate": '당신의 자기 연민이 발전하고 있습니다.어려운 순간에 친구처럼 자신에게 이야기하는 것은 이것을 키워줍니다.', "low": '거친 내면의 목소리가 두드러진다.자기연민 실천을 개발하는 것이 도움이 될 것입니다.'},
            'self_judgment': {"high": '지나치게 자기 비판적인 경향이 있습니다.이것을 인식하는 것이 변화를 위한 강력한 출발점입니다.', "moderate": '자기비판은 온건하다.자신에게 더 친절하면 때로는 이익이 되기도 합니다.', "low": '당신은 자신에 대해 균형 잡히고 친절한 태도를 보입니다.자기 평가의 건강한 신호.'},
            'common_humanity': {"high": '당신은 당신의 어려움이 위로를 가져오는 공유된 인간 경험의 일부라는 것을 이해합니다.', "moderate": '당신의 공통된 인간성에 대한 감각이 발전하고 있습니다.당신이 혼자가 아니라는 것을 기억하는 것은 당신을 강화시킵니다.', "low": '어려움이 닥치면 고립감을 느낄 수도 있습니다.이것은 매우 일반적인 경험이라는 것을 기억하십시오.'},
            'isolation': {"high": '당신은 어려운 순간에 고립되고 외롭다고 느낍니다.연결과 지원을 구하는 것은 균형을 잡는 데 도움이 됩니다.', "moderate": '고립감은 때때로 발생할 수 있습니다.연결을 구축하면 균형을 맞추는 데 도움이 됩니다.', "low": '어려움에 직면했을 때 연결되어 있고 지지받는 느낌을 받습니다.심리적 건강의 중요한 신호.'},
            'mindfulness': {"high": '균형과 자각을 통해 자신의 감정을 관찰할 수 있습니다.건강한 심리적 자세.', "moderate": '당신의 마음챙김 인식이 발전하고 있습니다.간단한 명상 수련은 이 영역을 강화할 것입니다.', "low": '감정을 관찰하기보다는 억압하는 경향이 있습니다.마음챙김 실천이 도움을 줄 수 있습니다.'},
            'overidentification': {"high": '부정적인 감정과 생각에 지나치게 집중하는 경향이 있습니다.마음챙김 수련은 이 순환을 깨뜨립니다.', "moderate": '당신은 때때로 부정적인 생각을 과도하게 동일시할 수 있습니다.균형 전략이 도움이 됩니다.', "low": '당신은 부정적인 생각으로부터 건전한 거리를 유지합니다.마음챙김 인식의 강력한 지표.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": '당신은 어려운 일을 성취할 수 있는 능력에 대한 강한 믿음을 가지고 있습니다.', "moderate": '당신의 자기효능감에 대한 믿음이 발전하고 있습니다.작은 성공을 쌓으면 이러한 자신감이 높아집니다.', "low": '자신의 능력에 대한 자신감이 낮습니다.작은 단계를 통해 성공 경험을 쌓는 것이 도움이 됩니다.'},
        },
        'stress': {
            'perceived_stress': {"high": '당신은 최근 높은 수준의 스트레스를 받고 있습니다.스트레스 관리 전략은 이제 특히 중요합니다.', "moderate": '당신은 적당한 스트레스를 겪고 있습니다.스트레스 유발 요인을 식별하고 관리하면 이점을 얻을 수 있습니다.', "low": '스트레스 인식 수준이 낮습니다.문제를 처리하는 능력이 강력해 보입니다.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": '당신은 일반적으로 당신의 외모를 긍정적으로 평가합니다.건강한 신체 이미지의 표시.', "moderate": '당신의 외모 평가는 엇갈립니다.신체의 기능에 초점을 맞추면 관점이 넓어집니다.', "low": '당신의 외모를 부정적으로 평가하는 경향이 있습니다.신체 확인 관행은 여기서 지원을 제공합니다.'},
            'body_satisfaction': {"high": '당신은 일반적으로 당신의 몸에 만족합니다.건강한 자기 수용의 표시.', "moderate": '당신의 신체 만족도는 보통입니다.신체의 강점에 집중하면 이 영역이 육성됩니다.', "low": '당신은 당신의 몸에 불만을 느낍니다.자기연민 실천과 전문적인 지원이 도움이 될 수 있습니다.'},
        },
    },
    'ja': {
        'personality': {
            'openness': {"high": 'あなたの好奇心と想像力は強いです。新しい経験やアイデアが自然とあなたを惹きつけます。', "moderate": 'あなたは好奇心と実用性のバランスをとり、ある分野では好奇心旺盛ですが、他の分野では伝統的です。', "low": 'あなたは実用的で親しみやすいものを好みます。一貫したルーチンと実績のあるアプローチがあなたにぴったりだと感じます。'},
            'conscientiousness': {"high": 'あなたは規律があり、組織的で、信頼できます。計画的に目標を追求します。', "moderate": '責任と柔軟性のバランスをとることができます。ルーチンを構築すると、これがさらに強化されるでしょう。', "low": 'あなたは柔軟で自発的なスタイルを持っています。計画を立てる習慣を身につけると、効率が向上します。'},
            'extraversion': {"high": 'あなたの社交的なエネルギーは高いです。あなたは人々から力を引き出し、周りの人たちにエネルギーをもたらします。', "moderate": '他の人と過ごす時間と一人で過ごす時間のバランスをとり、どちらの環境でも快適に過ごせます。', "low": 'あなたの内向的な性質は、深い思考と集中した仕事に適した天性の資産です。'},
            'agreeableness': {"high": 'あなたの温かく協力的な性格は、人間関係に信頼と調和を築きます。', "moderate": '協調性と独立性のバランスが取れており、理解がありながらも自己主張が強いです。', "low": 'あなたは独立した批判的思考、つまり分析と客観的な判断を得意とする傾向にあります。'},
            'neuroticism': {"high": 'あなたの感情的な反応は激しい場合があります。ストレス管理と自己調整戦略があなたをサポートします。', "moderate": 'あなたは感情の浮き沈みを経験します。ほとんどの場合、バランスを取り戻すことができます。', "low": 'あなたの感情的な回復力は強いです。プレッシャーの下でも冷静さを保ち、困難に簡単に対処します。'},
        },
        'skills': {
            'problem_solving': {"high": 'あなたは、複雑な問題を分析し、実用的な解決策を生み出すことに長けています。', "moderate": 'あなたの問題解決アプローチは発展しつつあります。構造化された思考テクニックがあなたをサポートします。', "low": '体系的な問題解決方法を学ぶことで、この分野での可能性が解き放たれます。'},
            'empathy': {"high": 'あなたは他人の感情を理解し、共感を得る驚くべき能力を持っています。', "moderate": 'あなたの共感能力は発達しています。アクティブリスニングを実践すると、この領域が強化されます。', "low": '他の人の視点をもっと探ることで、より効果的なコミュニケーションが可能になります。'},
            'organization': {"high": 'あなたの計画と優先順位はしっかりしています。整理されたスタイルはあなたを目立たせるのに役立ちます。', "moderate": 'あなたの組織力は妥当です。時間管理ツールを使用すると、さらに強くなれます。', "low": '組織的な習慣を体系的に身につけると、生産性が大幅に向上します。'},
            'learning_speed': {"high": '新しい知識やスキルにすぐに適応できるため、環境の変化において大きな利点となります。', "moderate": 'あなたの学習ペースは妥当です。さまざまな戦略を試してみると、効率が向上します。', "low": '構造化された復習と練習戦略が、この分野の学習プロセスをサポートします。'},
            'decision_making': {"high": '意思決定の場面では、決断的かつ迅速な行動を起こすことができます。', "moderate": 'あなたの意思決定スキルは発達しています。構造化されたフレームワークは困難な瞬間に役立ちます。', "low": '小さな決断から始めることは、意思決定に対する自信を高める効果的な方法です。'},
        },
        'hr': {
            'leadership': {"high": 'あなたはチームを指揮し、他の人を鼓舞し、率先して行動するのが得意です。', "moderate": 'あなたにはリーダーシップの適性があります。実践的な経験はこれらのスキルを迅速に開発します。', "low": '実践を通じてリーダーシップ スキルを意図的に開発することで、キャリアを大幅に向上させることができます。'},
            'team_fit': {"high": 'あなたは調和のとれたチームワーク、コラボレーション、親切さで際立っています。', "moderate": 'チームのフィット感は良好です。さまざまな働き方を理解することで、これがさらに強化されます。', "low": 'チームのダイナミクスにもっと積極的に参加すると、職業上の関係が強化されます。'},
            'communication': {"high": 'あなたは、明確で効果的かつ建設的なコミュニケーションが得意です。', "moderate": 'あなたのコミュニケーションスタイルは発展しつつあります。さまざまな聴衆に適応することが有利になります。', "low": 'コミュニケーションスキルを体系的に練習すると、この分野で急速な進歩が得られます。'},
            'stress_tolerance': {"high": 'プレッシャーの下でも平静を保つことができます。プロフェッショナルな回復力の基礎。', "moderate": 'あなたのストレス対処能力は妥当です。回復力を高めるテクニックはあなたをさらに強くします。', "low": '日々の実践に裏付けられたストレス管理戦略を開発すると、すぐに結果が得られます。'},
            'motivation': {"high": 'あなたの内発的動機は高いです。あなたは献身と情熱を持って目標に取り組みます。', "moderate": 'モチベーションはさまざまです。自分の目的とつながり続けることは、継続的なエネルギー源となります。', "low": '意味のある短期目標を設定することは、モチベーションを再燃させる効果的な方法です。'},
        },
        'career': {
            'analytical': {"high": 'あなたは分析的思考とデータ重視の作業環境に対する強い志向を持っています。', "moderate": 'あなたには分析的な傾向があります。構造化された問題解決の実践は、この領域を強化します。', "low": '体系的な分析スキルを開発すると、このキャリア分野での選択肢が広がります。'},
            'creative': {"high": '創造的で革新的な職場環境では、自分自身を最大限に表現できます。', "moderate": 'あなたには創造的な傾向があります。この領域を育成することで、キャリアの充実度を高めることができます。', "low": '現在、構造的および技術的なキャリアパスは、クリエイティブに焦点を当てた役割よりも整合しているように見えます。'},
            'social': {"high": '人々を助けたり、教えたり、協力したりすることは、あなたに活力を与えます。', "moderate": 'あなたは社会的交流を伴う役割に慣れています。より深いつながりは価値を付加することができます。', "low": '社会に焦点を当てたキャリアパスは、現在あなたにとって強い関心のある分野ではありません。'},
            'entrepreneurial': {"high": 'あなたは、リーダーシップ、説得、リスクテイクを必要とする起業家的な役割を担う傾向が強いです。', "moderate": 'あなたの起業家としての視点は発展しています。意思決定とリーダーシップの経験がこれを加速します。', "low": '現在、専門知識に重点を置いたキャリアパスは、起業家としての役割よりも整合性がとれているように見えます。'},
            'managerial': {"high": 'あなたは、管理、調整、組織化を必要とする役割に適しています。', "moderate": 'あなたの管理職の傾向は発展しつつあります。責任を負うことがこの領域を育てることになります。', "low": '管理職のプレッシャーが少なく、専門知識に重点を置いたキャリアパスのほうが、今はより快適に感じられるかもしれません。'},
            'technical': {"high": '技術的・専門的な分野に強い興味と志向を持っている方。', "moderate": 'あなたの技術的スキルは向上しています。深い専門化がこの分野を強化します。', "low": '現在、人材に焦点を当てたキャリアパスは、技術専門家の役割よりも整合性がとれているように見えます。'},
        },
        'vocation': {
            'realistic': {"high": 'あなたは、実践的、実践的、技術的な仕事に強い傾向を持っています。', "moderate": 'あなたは実践的な仕事にある程度の関心を持っています。この領域を試してみると、より鮮明な画像が得られます。', "low": 'あなたは現在、実践的で技術的な活動に強い関心を持っていません。'},
            'investigative': {"high": '研究、分析、アイデアの探求は自然とあなたを惹きつけます。', "moderate": 'あなたは調査に興味があります。この分野の知識を深めることで、さらに強化されます。', "low": '研究と分析に重点を置いた活動は、現在あなたの優先的な関心事ではありません。'},
            'artistic': {"high": 'あなたは、創造的な表現、芸術、美学を必要とする活動に強い傾向を持っています。', "moderate": 'あなたには芸術的な傾向があります。この領域を育成すると、充実感と信頼性が得られます。', "low": '芸術的および創造的な活動は、現在あなたにとって強い関心のある分野ではありません。'},
            'social': {"high": '人々と一緒にいること、助けたり、教えることはあなたに活力を与えます。', "moderate": 'あなたは社会活動に中程度の関心を持っています。有意義なつながりを築くことは満足感をもたらします。', "low": '現在、社会に焦点を当てた活動はあなたの優先的な関心事ではありません。'},
            'enterprising': {"high": 'あなたは、リーダーシップ、説得、競争を必要とする活動に最も強く感じます。', "moderate": 'あなたには進取的な傾向があります。責任と意思決定を実践することでこれが強化されます。', "low": '競争やリーダーシップを重視した活動は、現時点ではあなたにとって強い関心のある分野ではありません。'},
            'conventional': {"high": 'あなたは、組織化され、体系的で、規則に従った作業環境に強みを持ちます。', "moderate": 'あなたは組織や構造にある程度の関心を持っています。体系的な作業習慣がこれを育みます。', "low": '構造化された従来の活動は、現時点ではあなたにとって強い関心のある分野ではありません。'},
        },
        'relationship': {
            'love_language': {"high": 'あなたは愛の言葉を明確に表現し、人間関係における相互理解を大切にします。', "moderate": 'あなたは愛の言葉を適度に表現します。ここでもっとオープンになることで、人間関係が豊かになるでしょう。', "low": '感情表現と愛の言語に対する意識を高めることで、絆が深まります。'},
            'conflict_style': {"high": 'あなたは建設的かつ健全な方法で対立を解決するのが得意です。', "moderate": 'あなたの紛争解決スタイルは発展しつつあります。より建設的なアプローチを試みることが役立つかもしれません。', "low": '健全な対立解決戦略を立てると、人間関係の質が大幅に向上します。'},
            'intimacy_needs': {"high": 'あなたは、感情的な親密さとつながりに対する自分のニーズを明確に理解しています。', "moderate": 'あなたは自分の親密さの必要性を適度に認識しています。この領域をさらに調査することは価値があります。', "low": '自分の感情的な絆と親密さのニーズを理解することで、人間関係がより充実したものになるでしょう。'},
            'relationship_values': {"high": 'あなたは人間関係に何を求めるかについて、明確な価値観の枠組みを持っています。', "moderate": 'Your relationship values are taking shape;これを振り返ることで、より健全なつながりを築くことができます。', "low": '自分の人間関係の価値観を発見し、明確にすることで、より深い絆を築く基礎が築かれます。'},
        },
        'attachment': {
            'anxiety': {"high": '見捨てられることへの不安は大きい。この認識は、安全な愛着を育むための強力な出発点となります。', "moderate": '愛着不安は中程度です。安全な関係の実践がこの分野をサポートします。', "low": 'あなたの見捨てられ不安は低いです。あなたは人間関係において安定したバランスの取れた愛着を示します。'},
            'avoidance': {"high": '感情的な親密さの回避が顕著です。このパターンを認識することが、より深い絆への第一歩です。', "moderate": '親密さの回避は中程度です。自己認識が高まるにつれて、よりオープンなつながりを築くことができます。', "low": '感情的な親密さを避ける傾向が低いです。開放性とつながりが人間関係において快適であると感じます。'},
        },
        'grit': {
            'perseverance': {"high": 'あなたは、始めたことを最後までやり遂げ、障害があっても継続することが得意です。', "moderate": 'あなたの決意と根性は発展しつつあります。長期的な目標に取り組み続けることで、これが強化されます。', "low": '短期的な成功を積み重ねることは、持続可能な忍耐力を構築するための効果的な戦略です。'},
            'passion': {"high": 'あなたは長期的な目標に対して一貫した情熱と関心を示します。', "moderate": '目標に対するあなたの情熱は高まっています。意味のある目的につながると、このエネルギーが増幅されます。', "low": '本当に自分を奮い立たせる興味を見つけると、情熱とモチベーションが高まります。'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'あなたは、能力と知性は努力によって開発できると強く信じています。', "moderate": 'あなたの成長マインドセットは発展しつつあります。課題を学習の機会として捉えることで、これが育まれます。', "low": '能力は固定されているという信念は今も続いています。この考え方に疑問を持つことで、成長が加速します。'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'あなたは自分の人生に対する満足度が高く、全体的に肯定的な評価をしています。', "moderate": 'あなたの人生の満足度は中程度です。意味と価値の一致を強化すると、充実感が高まります。', "low": '人生の満足度は低い。何を変えたいかを自問するのが良い出発点です。'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'あなたは思いやりと理解を持って自分自身に取り組みます。心理的回復力の強力な源。', "moderate": 'あなたのセルフ・コンパッションは発達しつつあります。困難な瞬間に友達のように自分に話しかけることが、これを育みます。', "low": '厳しい内なる声が際立っています。セルフコンパッションの習慣を身につけることがあなたをサポートします。'},
            'self_judgment': {"high": '過度に自己批判的になる傾向が存在します。これが変化への強力な出発点であると認識することです。', "moderate": '自己批判は適度です。自分に優しくすることは、時には利益をもたらすこともあります。', "low": 'あなたは自分自身に対してバランスの取れた優しい態度を示します。自己評価の健全な兆候。'},
            'common_humanity': {"high": 'あなたは、自分の葛藤が人類共通の経験の一部であることを理解しており、それが慰めをもたらします。', "moderate": 'あなたの共通の人間性の感覚は発達しつつあります。あなたは一人ではないということを思い出すと、あなたは強くなります。', "low": '困難が生じると孤独を感じるかもしれません。これは非常に一般的な経験であることを覚えておいてください。'},
            'isolation': {"high": '困難な瞬間に、あなたは孤独を感じ、孤独を感じます。つながりとサポートを求めることは、このバランスをとるのに役立ちます。', "moderate": '孤立感が時々生じることがあります。つながりを築くことは、このバランスをとるのに役立ちます。', "low": '困難に直面したとき、あなたはつながりを感じ、サポートされていると感じます。心理的健康の重要な兆候。'},
            'mindfulness': {"high": 'バランスと意識を持って自分の感情を観察することができます。健全な心理的姿勢。', "moderate": 'あなたのマインドフルな意識は発達しつつあります。簡単な瞑想の実践がこの領域を強化します。', "low": '感情を観察するのではなく、抑制する傾向があります。マインドフルネスの実践はサポートを提供します。'},
            'overidentification': {"high": 'ネガティブな感情や考えに過度に集中する傾向があります。マインドフルネスの実践はこのサイクルを断ち切ります。', "moderate": '時々、ネガティブな考えを過剰に自己同一視してしまうことがあります。バランス戦略が役に立ちます。', "low": 'ネガティブな考えからは適度な距離を保ちます。マインドフルな意識を示す強力な指標です。'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'あなたは、困難な課題を達成できる自分の能力に強い自信を持っています。', "moderate": 'あなたの自己効力感は発展しつつあります。小さな成功を積み重ねることで、この自信が高まります。', "low": '自分の能力に対する自信が低い。小さなステップを通じて成功体験を構築することが役立ちます。'},
        },
        'stress': {
            'perceived_stress': {"high": 'あなたは最近、高いレベルのストレスを感じています。ストレス管理戦略は現在特に重要です。', "moderate": 'あなたは中程度のストレスを感じています。ストレスの引き金を特定して管理することは利益をもたらします。', "low": 'あなたのストレス認識レベルは低いです。あなたの課題に対処する能力は強いようです。'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'あなたは自分の外見を概して肯定的に評価します。健康的なボディイメージの兆候。', "moderate": 'あなたの外見の評価はまちまちです。体の機能に焦点を当てると視野が広がります。', "low": '自分の外見を否定的に評価する傾向があります。身体肯定の実践がここをサポートします。'},
            'body_satisfaction': {"high": 'あなたは一般的に自分の体に満足しています。健全な自己受容のしるし。', "moderate": '体の満足度は中程度です。体の強みに焦点を当てることで、この領域が育まれます。', "low": 'あなたは自分の体に不満を感じています。セルフコンパッションの実践や専門家のサポートが有益な場合があります。'},
        },
    },
    'zh': {
        'personality': {
            'openness': {'high': '你的好奇心和想象力很强；新的经历和想法自然会吸引你。', 'moderate': '您平衡好奇心与实用性，在某些领域充满好奇，而在另一些领域则传统。', 'low': '你更喜欢实用、熟悉的东西；一致的惯例和经过验证的方法适合您。'},
            'conscientiousness': {'high': '你遵守纪律、有组织性、可靠；你系统地追求目标。', 'moderate': '您平衡责任和灵活性；建立例行公事将进一步加强这一点。', 'low': '你的风格灵活、随性；养成计划习惯可以提高你的效率。'},
            'extraversion': {'high': '你的社交能量很高；你从人们那里汲取力量，并为周围的人带来能量。', 'moderate': '您平衡与他人相处的时间和独处的时间，在两种环境中都感到舒适。', 'low': '你内向的性格是深入思考和专注工作的天然资产。'},
            'agreeableness': {'high': '你热情、合作的天性会在你们的人际关系中建立信任与和谐。', 'moderate': '你平衡合作与独立、理解与自信。', 'low': '你倾向于独立、批判性思维——这是分析和客观判断的优势。'},
            'neuroticism': {'high': '你的情绪反应可能会很激烈；压力管理和自我调节策略将为您提供支持。', 'moderate': '你会经历一些情绪的起伏；大多数时候你可以再次找到平衡。', 'low': '你的情绪恢复能力很强；你在压力下保持冷静，轻松处理困难。'},
        },
        'skills': {
            'problem_solving': {'high': '您擅长分析复杂问题并生成实用的解决方案。', 'moderate': '你解决问题的方法正在发展；结构化思维技巧可以为您提供支持。', 'low': '学习系统的解决问题的方法将释放你在这方面的潜力。'},
            'empathy': {'high': '您具有理解他人情绪并产生同理心的非凡能力。', 'moderate': '你的同理心能力正在发展；练习积极倾听将加强这一领域。', 'low': '更多地探索他人的观点将使你成为更有效的沟通者。'},
            'organization': {'high': '你的计划和优先顺序很明确；你井井有条的风格可以帮助你脱颖而出。', 'moderate': '你的组织能力合理；使用时间管理工具可以让你变得更强大。', 'low': '养成系统的组织习惯可以显着提高您的工作效率。'},
            'learning_speed': {'high': '您可以快速适应新的知识和技能——这是在不断变化的环境中的一个主要优势。', 'moderate': '你的学习节奏合理；尝试不同的策略可以提高你的效率。', 'low': '结构化的复习和练习策略将支持您在该领域的学习过程。'},
            'decision_making': {'high': '您可以在决策情况下采取果断、快速的步骤。', 'moderate': '您的决策能力正在发展；结构化框架在困难时刻提供帮助。', 'low': '从较小的决定开始是建立决策信心的有效方法。'},
        },
        'hr': {
            'leadership': {'high': '您擅长指导团队、激励他人和发挥领导作用。', 'moderate': '你有领导才能；实践经验将很快培养这些技能。', 'low': '通过实践刻意培养领导技能可以显着提升您的职业生涯。'},
            'team_fit': {'high': '您因和谐的团队合作、协作和乐于助人而脱颖而出。', 'moderate': '你的团队配合度很好；了解不同的工作方式将进一步加强这一点。', 'low': '更积极地参与团队动态将加强您的专业关系。'},
            'communication': {'high': '您擅长清晰、有效和建设性的沟通。', 'moderate': '你的沟通方式正在发展；适应不同的受众会给你带来优势。', 'low': '系统地练习沟通技巧将会在这方面带来快速的进步。'},
            'stress_tolerance': {'high': '你能在压力下保持冷静；专业韧性的基石。', 'moderate': '您的压力应对能力是合理的；恢复力建设技巧会让你变得更加强大。', 'low': '在日常实践的支持下制定压力管理策略可以快速产生结果。'},
            'motivation': {'high': '你的内在动机很高；您以承诺和热情实现您的目标。', 'moderate': '你的动机各不相同；与你的目标保持联系可以成为持续的能量来源。', 'low': '设定有意义的短期目标是重新激发动力的有效方法。'},
        },
        'career': {
            'analytical': {'high': '您对分析思维和以数据为中心的工作环境有着强烈的导向。', 'moderate': '你有分析倾向；结构化的问题解决实践将加强这一领域。', 'low': '发展系统的分析技能将扩大您在这个职业领域的选择。'},
            'creative': {'high': '您可以在富有创意和创新的工作环境中最好地表达自己。', 'moderate': '你有创作倾向；培养这个领域可以增加你的职业成就感。', 'low': '目前，结构性和技术性的职业道路似乎比以创意为中心的角色更加一致。'},
            'social': {'high': '帮助、教导或与人合作会让你充满活力。', 'moderate': '您对涉及社交互动的角色感到满意；更深层次的联系可以增加价值。', 'low': '目前，以社会为中心的职业道路并不是您的强烈兴趣领域。'},
            'entrepreneurial': {'high': '您非常倾向于担任需要领导力、说服力和冒险精神的创业角色。', 'moderate': '您的创业视角正在发展；决策和领导经验将加速这一过程。', 'low': '目前，以专业知识为中心的职业道路似乎比创业角色更加一致。'},
            'managerial': {'high': '您非常适合需要管理、协调和组织的角色。', 'moderate': '您的管理倾向正在发展；承担责任将培育这一领域。', 'low': '现在，以专业知识为中心、管理压力较小的职业道路可能会感觉更舒服。'},
            'technical': {'high': '您对技术和专业领域有浓厚的兴趣和方向。', 'moderate': '您的技术技能正在发展；深度专业化将加强这一领域。', 'low': '目前，以人为本的职业道路似乎比技术专家角色更加一致。'},
        },
        'vocation': {
            'realistic': {'high': '您对实际、动手和技术工作有强烈的倾向。', 'moderate': '您对实践工作具有中等兴趣；尝试这个区域会给你一个更清晰的认识。', 'low': '实践和技术活动目前并不是您的强烈兴趣。'},
            'investigative': {'high': '研究、分析和探索想法自然会吸引你。', 'moderate': '您有研究兴趣；加深该领域的知识将进一步加强它。', 'low': '以研究和分析为重点的活动目前不属于您的优先兴趣。'},
            'artistic': {'high': '您强烈倾向于需要创造性表达、艺术和美学的活动。', 'moderate': '你有艺术倾向；培育这个领域可以提供满足感和真实性。', 'low': '艺术和创意活动目前并不是您的强烈兴趣领域。'},
            'social': {'high': '与人相处、帮助和教导会让你充满活力。', 'moderate': '您对社交活动有中等兴趣；建立有意义的联系会带来满足感。', 'low': '以社交为中心的活动目前不属于您的优先兴趣。'},
            'enterprising': {'high': '在需要领导力、说服力和竞争的活动中，你感觉最强。', 'moderate': '你有进取心；实践责任和决策可以强化这一点。', 'low': '目前，竞争性和以领导力为中心的活动并不是您的强烈兴趣领域。'},
            'conventional': {'high': '您擅长组织、系统且规则一致的工作环境。', 'moderate': '您对组织和结构有中等兴趣；系统的工作实践培养了这一点。', 'low': '结构化和常规活动目前不是您的强烈兴趣领域。'},
        },
        'relationship': {
            'love_language': {'high': '你清楚地表达你的爱的语言，并重视人际关系中的相互理解。', 'moderate': 'You express your love language moderately;在这里更加开放可以丰富你的人际关系。', 'low': '培养情感表达和爱的语言的意识将加深你们的联系。'},
            'conflict_style': {'high': '您擅长以建设性且健康的方式解决冲突。', 'moderate': '你的冲突解决方式正在发展；尝试更具建设性的方法会有所帮助。', 'low': '制定健康的冲突解决策略将显着提高你们的关系质量。'},
            'intimacy_needs': {'high': '您清楚地了解自己对情感亲密和联系的需求。', 'moderate': '您对自己的亲密需求有中等程度的认识；进一步探索这一领域是有价值的。', 'low': '了解您的情感联系和亲密需求将使您的关系更加充实。'},
            'relationship_values': {'high': '对于你想要的人际关系有一个清晰的价值框架。', 'moderate': '你的人际关系价值观正在形成；反思这一点可以帮助您建立更健康的联系。', 'low': '发现并澄清你的个人关系价值观为更深层次的联系奠定了基础。'},
        },
        'attachment': {
            'anxiety': {'high': '对被遗弃的焦虑程度很高；这种意识是发展安全依恋的一个强有力的起点。', 'moderate': '依恋焦虑程度中等；安全关系实践支持这一领域。', 'low': '你的被遗弃焦虑程度较低；你在人际关系中表现出安全和平衡的依恋。'},
            'avoidance': {'high': '回避情感上的亲密是显而易见的；认识到这种模式是迈向更深层次联系的第一步。', 'moderate': '避免亲密接触的程度是中等的；随着自我意识的增强，你可以建立更开放的联系。', 'low': '您对情感亲密的回避程度较低；开放和联系使人在人际关系中感到舒适。'},
        },
        'grit': {
            'perseverance': {'high': '你有能力完成你开始的事情，并克服障碍继续前进。', 'moderate': '你的决心和毅力正在增强；致力于长期目标可以强化这一点。', 'low': '积累短期成功是培养可持续毅力的有效策略。'},
            'passion': {'high': '您对长期目标表现出一贯的热情和兴趣。', 'moderate': '你对目标的热情正在增强；与有意义的目标联系会增强这种能量。', 'low': '发现真正激发你兴趣的兴趣会激发你的热情和动力。'},
        },
        'growth_mindset': {
            'growth_mindset': {'high': '您坚信能力和智力可以通过努力来发展。', 'moderate': '你的成长心态正在发展；将挑战视为学习机会可以培养这一点。', 'low': '能力是固定的这一信念仍在继续；质疑这种心态会加速你的成长。'},
        },
        'life_satisfaction': {
            'life_satisfaction': {'high': '您对自己的生活表示高度满意，并做出总体积极的评价。', 'moderate': '您的生活满意度中等；加强意义与价值的一致性可以增加成就感。', 'low': '生活满意度低；问问自己想要改变什么是一个很好的起点。'},
        },
        'self_compassion': {
            'self_kindness': {'high': '你以慈悲和理解的态度对待自己；心理弹性的强大来源。', 'moderate': '你的自我同情心正在发展；在困难时刻像朋友一样与自己交谈可以培养这一点。', 'low': '内心的刺耳声音很突出；培养自我慈悲的做法将为你提供支持。'},
            'self_judgment': {'high': '存在过度自我批评的倾向；认识到这一点是变革的有力起点。', 'moderate': '自我批评是适度的；对自己更友善有时会带来好处。', 'low': '你对自己表现出平衡和友善的态度；自我评价的健康标志。'},
            'common_humanity': {'high': '你明白你的挣扎是人类共同经历的一部分，这会带来安慰。', 'moderate': '你们的共同人性意识正在发展；记住你并不孤单，这会增强你的力量。', 'low': '当困难出现时，你可能会感到孤立；请记住，这是一种非常常见的经历。'},
            'isolation': {'high': '在困难的时刻，你感到孤立无援；寻求联系和支持有助于平衡这一点。', 'moderate': '孤立感有时会出现；建立联系有助于平衡这一点。', 'low': '面对困难时，您会感到与他人有联系并受到支持；心理健康的重要标志。'},
            'mindfulness': {'high': '你可以用平衡和意识来观察你的情绪；健康的心理姿态。', 'moderate': '你的正念意识正在发展；简单的冥想练习将加强这个领域。', 'low': '有抑制情绪而不是观察情绪的倾向；正念练习可以提供支持。'},
            'overidentification': {'high': '有过度关注负面情绪和想法的倾向；正念练习打破了这个循环。', 'moderate': '有时你可能会过度认同消极的想法；平衡策略有帮助。', 'low': '您与消极想法保持健康的距离；正念意识的有力指标。'},
        },
        'self_efficacy': {
            'self_efficacy': {'high': '您坚信自己有能力完成具有挑战性的任务。', 'moderate': '您的自我效能信念正在发展；积累小成功会增强这种信心。', 'low': '对自己能力缺乏信心；通过小步骤积累成功经验会有所帮助。'},
        },
        'stress': {
            'perceived_stress': {'high': '您最近感到压力很大；压力管理策略现在尤其重要。', 'moderate': '您正承受中等程度的压力；识别和管理压力触发因素会带来好处。', 'low': '您的压力感知水平较低；你应对挑战的能力似乎很强。'},
        },
        'body_image': {
            'appearance_evaluation': {'high': '您对自己的外表总体评价是积极的；健康身体形象的标志。', 'moderate': "对你的外表评价褒贬不一；focusing on your body's functionality broadens perspective.", 'low': '人们倾向于对自己的外表做出负面评价；身体肯定实践在这里提供支持。'},
            'body_satisfaction': {'high': '您对自己的身体总体感到满意；健康自我接纳的标志。', 'moderate': '您的身体满意度中等；专注于身体的优势可以培养这个区域。', 'low': '你对自己的身体感到不满意；自我同情实践和专业支持可能是有益的。'},
        },
    },
    'hi': {
        'personality': {
            'openness': {"high": 'आपकी जिज्ञासा और कल्पनाशक्ति प्रबल है;नए अनुभव और विचार आपको स्वाभाविक रूप से आकर्षित करते हैं।', "moderate": 'आप जिज्ञासा को व्यावहारिकता, कुछ क्षेत्रों में जिज्ञासु और अन्य में पारंपरिकता के साथ संतुलित करते हैं।', "low": 'आप व्यावहारिक और परिचित को प्राथमिकता देते हैं;लगातार दिनचर्या और सिद्ध दृष्टिकोण आपके लिए सही लगते हैं।'},
            'conscientiousness': {"high": 'आप अनुशासित, संगठित और विश्वसनीय हैं;आप व्यवस्थित रूप से लक्ष्यों का पीछा करते हैं।', "moderate": 'आप जिम्मेदारी और लचीलेपन को संतुलित करते हैं;निर्माण की दिनचर्या इसे और मजबूत करेगी।', "low": 'आपकी शैली लचीली, सहज है;योजना बनाने की आदतें विकसित करने से आपकी प्रभावशीलता में सुधार हो सकता है।'},
            'extraversion': {"high": 'आपकी सामाजिक ऊर्जा उच्च है;आप लोगों से शक्ति प्राप्त करते हैं और अपने आस-पास के लोगों में ऊर्जा लाते हैं।', "moderate": 'आप दूसरों के साथ समय और अकेले समय को संतुलित करते हैं, दोनों स्थितियों में सहज रहते हैं।', "low": 'आपका अंतर्मुखी स्वभाव गहरी सोच और केंद्रित कार्य के लिए एक प्राकृतिक संपत्ति है।'},
            'agreeableness': {"high": 'आपका गर्मजोशी भरा, सहयोगात्मक स्वभाव आपके रिश्तों में विश्वास और सद्भाव पैदा करता है।', "moderate": 'आप सहयोगात्मकता और स्वतंत्रता, समझ और फिर भी आत्म-मुखरता को संतुलित करते हैं।', "low": 'आप स्वतंत्र, आलोचनात्मक सोच की ओर झुकते हैं - विश्लेषण और वस्तुनिष्ठ निर्णय के लिए एक ताकत।'},
            'neuroticism': {"high": 'आपकी भावनात्मक प्रतिक्रियाएँ तीव्र हो सकती हैं;तनाव प्रबंधन और स्व-नियमन रणनीतियाँ आपका समर्थन करेंगी।', "moderate": 'आप कुछ भावनात्मक उतार-चढ़ाव का अनुभव करते हैं;अधिकांश समय आप अपना संतुलन फिर से पा सकते हैं।', "low": 'आपकी भावनात्मक लचीलापन मजबूत है;आप दबाव में शांत रहते हैं और कठिनाइयों को आसानी से संभाल लेते हैं।'},
        },
        'skills': {
            'problem_solving': {"high": 'आप जटिल समस्याओं का विश्लेषण करने और व्यावहारिक समाधान निकालने में मजबूत हैं।', "moderate": 'आपका समस्या-समाधान दृष्टिकोण विकसित हो रहा है;संरचित सोच तकनीकें आपका समर्थन कर सकती हैं।', "low": 'व्यवस्थित समस्या-समाधान के तरीके सीखने से इस क्षेत्र में आपकी क्षमताएं उजागर होंगी।'},
            'empathy': {"high": 'आपमें दूसरों की भावनाओं को समझने और सहानुभूति से जुड़ने की अद्भुत क्षमता है।', "moderate": 'आपकी सहानुभूति कौशल विकसित हो रही है;सक्रिय रूप से सुनने का अभ्यास करने से यह क्षेत्र मजबूत होगा।', "low": 'दूसरों के दृष्टिकोण को और अधिक जानने से आप अधिक प्रभावी संचारक बन जायेंगे।'},
            'organization': {"high": 'आपकी योजना और प्राथमिकताएँ मजबूत हैं;आपकी व्यवस्थित शैली आपको अलग दिखने में मदद करती है।', "moderate": 'आपका संगठनात्मक कौशल उचित है;समय प्रबंधन टूल का उपयोग आपको और भी मजबूत बना सकता है।', "low": 'व्यवस्थित संगठनात्मक आदतें विकसित करने से आपकी उत्पादकता में उल्लेखनीय सुधार हो सकता है।'},
            'learning_speed': {"high": 'आप नए ज्ञान और कौशल को जल्दी से अपना लेते हैं - बदलते परिवेश में यह एक बड़ा फायदा है।', "moderate": 'आपकी सीखने की गति उचित है;विभिन्न रणनीतियों के साथ प्रयोग करने से आपकी प्रभावशीलता बढ़ सकती है।', "low": 'संरचित समीक्षा और अभ्यास रणनीतियाँ इस क्षेत्र में आपकी सीखने की प्रक्रिया का समर्थन करेंगी।'},
            'decision_making': {"high": 'आप निर्णय लेने की स्थितियों में निर्णायक, त्वरित कदम उठा सकते हैं।', "moderate": 'आपके निर्णय लेने के कौशल विकसित हो रहे हैं;संरचित ढाँचे कठिन क्षणों में मदद करते हैं।', "low": 'छोटे निर्णयों से शुरुआत करना आपके निर्णय लेने के आत्मविश्वास को बढ़ाने का एक प्रभावी तरीका है।'},
        },
        'hr': {
            'leadership': {"high": 'आप टीमों को निर्देशित करने, दूसरों को प्रेरित करने और नेतृत्व करने में सशक्त हैं।', "moderate": 'आपमें नेतृत्व की योग्यता है;व्यावहारिक अनुभव इन कौशलों को शीघ्रता से विकसित करेंगे।', "low": 'अभ्यास के माध्यम से जानबूझकर नेतृत्व कौशल विकसित करने से आपका करियर काफी आगे बढ़ सकता है।'},
            'team_fit': {"high": 'आप सामंजस्यपूर्ण टीम वर्क, सहयोग और सहायता के लिए प्रतिष्ठित हैं।', "moderate": 'आपकी टीम की स्थिति अच्छी है;विभिन्न कार्यशैलियों को समझने से यह और मजबूत होगा।', "low": 'टीम की गतिशीलता में अधिक सक्रिय भागीदारी आपके पेशेवर संबंधों को मजबूत करेगी।'},
            'communication': {"high": 'आप स्पष्ट, प्रभावी और रचनात्मक संचार में मजबूत हैं।', "moderate": 'आपकी संचार शैली विकसित हो रही है;अलग-अलग दर्शकों के साथ तालमेल बिठाने से आपको फायदा मिलता है।', "low": 'संचार कौशल का व्यवस्थित अभ्यास करने से इस क्षेत्र में तेजी से प्रगति होगी।'},
            'stress_tolerance': {"high": 'आप दबाव में अपना संयम बनाए रख सकते हैं;पेशेवर लचीलेपन की आधारशिला।', "moderate": 'आपकी तनाव-निपटने की क्षमता उचित है;लचीलापन-निर्माण तकनीकें आपको और भी मजबूत बनाएंगी।', "low": 'दैनिक प्रथाओं द्वारा समर्थित तनाव प्रबंधन रणनीतियों का विकास करने से परिणाम जल्दी मिलते हैं।'},
            'motivation': {"high": 'आपकी आंतरिक प्रेरणा ऊँची है;आप प्रतिबद्धता और जुनून के साथ अपने लक्ष्यों तक पहुंचते हैं।', "moderate": 'आपकी प्रेरणा भिन्न-भिन्न होती है;अपने उद्देश्य से जुड़े रहना एक सतत ऊर्जा स्रोत हो सकता है।', "low": 'सार्थक अल्पकालिक लक्ष्य निर्धारित करना आपकी प्रेरणा को पुनः जागृत करने का एक प्रभावी तरीका है।'},
        },
        'career': {
            'analytical': {"high": 'विश्लेषणात्मक सोच और डेटा-केंद्रित कार्य वातावरण के प्रति आपका रुझान मजबूत है।', "moderate": 'आपमें विश्लेषणात्मक प्रवृत्ति है;संरचित समस्या-समाधान अभ्यास इस क्षेत्र को मजबूत करेगा।', "low": 'व्यवस्थित विश्लेषणात्मक कौशल विकसित करने से इस करियर क्षेत्र में आपके विकल्पों का विस्तार होगा।'},
            'creative': {"high": 'आप रचनात्मक और नवोन्मेषी कार्य वातावरण में खुद को सर्वश्रेष्ठ रूप से अभिव्यक्त करते हैं।', "moderate": 'आपमें रचनात्मक प्रवृत्ति है;इस क्षेत्र का पोषण करने से आपके करियर की पूर्ति बढ़ सकती है।', "low": 'संरचनात्मक और तकनीकी करियर पथ वर्तमान में रचनात्मक-केंद्रित भूमिकाओं की तुलना में अधिक संरेखित प्रतीत होते हैं।'},
            'social': {"high": 'लोगों की मदद करना, पढ़ाना या उनके साथ काम करना आपको ऊर्जावान बनाता है।', "moderate": 'आप सामाजिक संपर्क से जुड़ी भूमिकाओं में सहज हैं;गहरे संबंध मूल्य जोड़ सकते हैं।', "low": 'सामाजिक-केंद्रित करियर पथ वर्तमान में आपके लिए एक मजबूत रुचि वाला क्षेत्र नहीं है।'},
            'entrepreneurial': {"high": 'आपके पास नेतृत्व, अनुनय और जोखिम लेने की आवश्यकता वाली उद्यमशीलता भूमिकाओं की ओर एक मजबूत प्रवृत्ति है।', "moderate": 'आपका उद्यमशीलता परिप्रेक्ष्य विकसित हो रहा है;निर्णय लेने की क्षमता और नेतृत्व का अनुभव इसमें तेजी लाएगा।', "low": 'विशेषज्ञता-केंद्रित करियर पथ वर्तमान में उद्यमशीलता भूमिकाओं की तुलना में अधिक संरेखित प्रतीत होते हैं।'},
            'managerial': {"high": 'आप उन भूमिकाओं के लिए उपयुक्त हैं जिनके लिए प्रबंधन, समन्वय और संगठन की आवश्यकता होती है।', "moderate": 'आपकी प्रबंधकीय प्रवृत्तियाँ विकसित हो रही हैं;जिम्मेदारी लेने से इस क्षेत्र का पोषण होगा।', "low": 'कम प्रबंधकीय दबाव वाले विशेषज्ञता-केंद्रित करियर पथ अभी अधिक आरामदायक महसूस हो सकते हैं।'},
            'technical': {"high": 'तकनीकी और विशिष्ट क्षेत्रों के प्रति आपकी गहरी रुचि और झुकाव है।', "moderate": 'आपके तकनीकी कौशल विकसित हो रहे हैं;गहरी विशेषज्ञता इस क्षेत्र को मजबूत करेगी।', "low": 'जन-केंद्रित करियर पथ वर्तमान में तकनीकी विशेषज्ञ भूमिकाओं की तुलना में अधिक संरेखित प्रतीत होते हैं।'},
        },
        'vocation': {
            'realistic': {"high": 'व्यावहारिक, व्यावहारिक और तकनीकी कार्यों के प्रति आपका रुझान मजबूत है।', "moderate": 'आपको व्यावहारिक कार्य में मध्यम रुचि है;इस क्षेत्र को आज़माने से आपको एक स्पष्ट तस्वीर मिलेगी।', "low": 'व्यावहारिक और तकनीकी गतिविधियाँ वर्तमान में आपके मजबूत हितों में से नहीं हैं।'},
            'investigative': {"high": 'अनुसंधान, विश्लेषण और विचारों की खोज स्वाभाविक रूप से आपको आकर्षित करती है।', "moderate": 'आपकी रुचि खोजपूर्ण है;इस क्षेत्र में ज्ञान को गहरा करने से यह और मजबूत होगा।', "low": 'अनुसंधान और विश्लेषण-केंद्रित गतिविधियाँ वर्तमान में आपकी प्राथमिकता वाली रुचियों में से नहीं हैं।'},
            'artistic': {"high": 'रचनात्मक अभिव्यक्ति, कला और सौंदर्यशास्त्र की आवश्यकता वाली गतिविधियों के प्रति आपका रुझान मजबूत है।', "moderate": 'आपमें कलात्मक प्रवृत्तियाँ हैं;इस क्षेत्र का पोषण पूर्णता और प्रामाणिकता प्रदान कर सकता है।', "low": 'कलात्मक और रचनात्मक गतिविधियाँ वर्तमान में आपके लिए गहरी रुचि का क्षेत्र नहीं हैं।'},
            'social': {"high": 'लोगों के साथ रहना, मदद करना और पढ़ाना आपको ऊर्जावान बनाता है।', "moderate": 'सामाजिक गतिविधियों में आपकी मध्यम रुचि है;सार्थक संबंध बनाने से संतुष्टि मिलती है।', "low": 'सामाजिक-केंद्रित गतिविधियाँ वर्तमान में आपकी प्राथमिकता वाली रुचियों में से नहीं हैं।'},
            'enterprising': {"high": 'आप नेतृत्व, अनुनय और प्रतिस्पर्धा की आवश्यकता वाली गतिविधियों में सबसे मजबूत महसूस करते हैं।', "moderate": 'आपमें उद्यमशीलता की प्रवृत्ति है;जिम्मेदारी का अभ्यास करना और निर्णय लेना इसे मजबूत करता है।', "low": 'प्रतिस्पर्धी और नेतृत्व-केंद्रित गतिविधियाँ वर्तमान में आपके लिए एक मजबूत रुचि वाला क्षेत्र नहीं हैं।'},
            'conventional': {"high": 'आप संगठित, व्यवस्थित और नियम-संगत कार्य वातावरण में मजबूत हैं।', "moderate": 'संगठन और संरचना में आपकी मध्यम रुचि है;व्यवस्थित कार्य अभ्यास इसका पोषण करता है।', "low": 'संरचित और पारंपरिक गतिविधियाँ वर्तमान में आपके लिए एक मजबूत रुचि वाला क्षेत्र नहीं हैं।'},
        },
        'relationship': {
            'love_language': {"high": 'आप अपनी प्रेम भाषा को स्पष्ट रूप से व्यक्त करते हैं और रिश्तों में आपसी समझ को महत्व देते हैं।', "moderate": 'आप अपनी प्रेम भाषा को संयत रूप से व्यक्त करते हैं;यहां अधिक खुला होना आपके रिश्तों को समृद्ध कर सकता है।', "low": 'भावनात्मक अभिव्यक्ति और प्रेम भाषाओं के बारे में जागरूकता विकसित करने से आपके संबंध गहरे होंगे।'},
            'conflict_style': {"high": 'आप रचनात्मक और स्वस्थ तरीकों से संघर्षों को सुलझाने में मजबूत हैं।', "moderate": 'आपकी संघर्ष समाधान शैली विकसित हो रही है;अधिक रचनात्मक दृष्टिकोण आज़माने से मदद मिल सकती है।', "low": 'स्वस्थ संघर्ष समाधान रणनीतियों का विकास करने से आपके रिश्ते की गुणवत्ता में काफी सुधार होगा।'},
            'intimacy_needs': {"high": 'आप भावनात्मक निकटता और जुड़ाव के लिए अपनी आवश्यकताओं को स्पष्ट रूप से समझते हैं।', "moderate": 'आपको अपनी अंतरंगता आवश्यकताओं के बारे में मध्यम जागरूकता है;इस क्षेत्र की और अधिक खोज करना मूल्यवान है।', "low": 'आपके भावनात्मक जुड़ाव और अंतरंगता की ज़रूरतों को समझने से आपके रिश्ते अधिक संतुष्टिदायक बनेंगे।'},
            'relationship_values': {"high": 'आप अपने रिश्तों में क्या चाहते हैं, इसके लिए आपके पास एक स्पष्ट मूल्य ढांचा है।', "moderate": 'आपके रिश्ते के मूल्य आकार ले रहे हैं;इस पर विचार करने से आपको स्वस्थ संबंध बनाने में मदद मिलती है।', "low": 'अपने व्यक्तिगत संबंध मूल्यों की खोज करना और स्पष्ट करना गहरे संबंधों के लिए आधार तैयार करता है।'},
        },
        'attachment': {
            'anxiety': {"high": 'परित्याग के बारे में चिंता अधिक है;यह जागरूकता सुरक्षित लगाव विकसित करने के लिए एक मजबूत प्रारंभिक बिंदु है।', "moderate": 'आसक्ति संबंधी चिंता मध्यम है;सुरक्षित संबंध प्रथाएँ इस क्षेत्र का समर्थन करती हैं।', "low": 'आपकी परित्याग चिंता कम है;आप रिश्तों में सुरक्षित और संतुलित लगाव दिखाते हैं।'},
            'avoidance': {"high": 'भावनात्मक निकटता से बचना ध्यान देने योग्य है;इस पैटर्न को पहचानना गहरे संबंधों की ओर पहला कदम है।', "moderate": 'निकटता से बचना मध्यम है;जैसे-जैसे आत्म-जागरूकता बढ़ती है, आप अधिक खुले संबंध बना सकते हैं।', "low": 'भावनात्मक निकटता से आपका परहेज कम है;रिश्तों में खुलापन और जुड़ाव सहज महसूस कराता है।'},
        },
        'grit': {
            'perseverance': {"high": 'आप जो शुरू करते हैं उसे पूरा करने और बाधाओं के बावजूद जारी रखने में आप मजबूत हैं।', "moderate": 'आपका दृढ़ संकल्प और धैर्य विकसित हो रहा है;दीर्घकालिक लक्ष्यों के प्रति प्रतिबद्ध रहना इसे मजबूत करता है।', "low": 'स्थायी दृढ़ता के निर्माण के लिए अल्पकालिक सफलताओं को संचित करना एक प्रभावी रणनीति है।'},
            'passion': {"high": 'आप अपने दीर्घकालिक लक्ष्यों के प्रति लगातार जुनून और रुचि दिखाते हैं।', "moderate": 'लक्ष्यों के प्रति आपका जुनून विकसित हो रहा है;किसी सार्थक उद्देश्य से जुड़ने से यह ऊर्जा बढ़ती है।', "low": 'ऐसी रुचियों की खोज करना जो वास्तव में आपको उत्साहित करती हैं, आपके जुनून और प्रेरणा को बढ़ावा देंगी।'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'आपका दृढ़ विश्वास है कि प्रयास के माध्यम से क्षमताओं और बुद्धि का विकास किया जा सकता है।', "moderate": 'आपकी विकास मानसिकता विकसित हो रही है;चुनौतियों को सीखने के अवसरों के रूप में देखना इसका पोषण करता है।', "low": 'यह विश्वास जारी है कि योग्यताएँ निश्चित हैं;इस मानसिकता पर सवाल उठाने से आपके विकास में तेजी आएगी।'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'आप अपने जीवन से अत्यधिक संतुष्ट हैं और समग्र रूप से सकारात्मक मूल्यांकन करते हैं।', "moderate": 'आपके जीवन की संतुष्टि मध्यम है;अर्थ-मूल्य संरेखण को मजबूत करने से पूर्ति बढ़ती है।', "low": 'जीवन संतुष्टि कम है;अपने आप से पूछना कि आप क्या बदलना चाहते हैं, एक अच्छा प्रारंभिक बिंदु है।'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'आप करुणा और समझ के साथ अपने आप से संपर्क करते हैं;मनोवैज्ञानिक लचीलेपन का एक मजबूत स्रोत।', "moderate": 'आपकी आत्म-करुणा विकसित हो रही है;कठिन क्षणों में एक मित्र की तरह स्वयं से बात करना इसका पोषण करता है।', "low": 'एक कठोर आंतरिक आवाज प्रमुख है;आत्म-करुणा अभ्यास विकसित करने से आपको सहायता मिलेगी।'},
            'self_judgment': {"high": 'अत्यधिक आत्म-आलोचनात्मक होने की प्रवृत्ति मौजूद है;इसे पहचानना परिवर्तन के लिए एक शक्तिशाली प्रारंभिक बिंदु है।', "moderate": 'आत्म-आलोचना मध्यम है;स्वयं के प्रति दयालु होने से कभी-कभी लाभ मिलता है।', "low": 'आप अपने प्रति संतुलित और दयालु रवैया दिखाते हैं;आत्म-मूल्यांकन का एक स्वस्थ संकेत।'},
            'common_humanity': {"high": 'आप समझते हैं कि आपके संघर्ष साझा मानवीय अनुभव का हिस्सा हैं, जो आराम लाता है।', "moderate": 'आपकी सामान्य मानवता की भावना विकसित हो रही है;यह याद रखना कि आप अकेले नहीं हैं, आपको मजबूत बनाता है।', "low": 'कठिनाइयाँ आने पर आप अलग-थलग महसूस कर सकते हैं;याद रखें यह एक बहुत ही सामान्य अनुभव है.'},
            'isolation': {"high": 'आप कठिन क्षणों में अलग-थलग और अकेला महसूस करते हैं;कनेक्शन और समर्थन मांगने से इसे संतुलित करने में मदद मिलती है।', "moderate": 'अलगाव की भावनाएँ समय-समय पर उत्पन्न हो सकती हैं;कनेक्शन बनाने से इसे संतुलित करने में मदद मिलती है।', "low": 'कठिनाइयों का सामना करते समय आप जुड़ाव और समर्थन महसूस करते हैं;मनोवैज्ञानिक स्वास्थ्य का एक महत्वपूर्ण संकेत.'},
            'mindfulness': {"high": 'आप अपनी भावनाओं को संतुलन और जागरूकता के साथ देख सकते हैं;एक स्वस्थ मनोवैज्ञानिक रुख.', "moderate": 'आपकी सचेत जागरूकता विकसित हो रही है;सरल ध्यान अभ्यास इस क्षेत्र को मजबूत करेगा।', "low": 'भावनाओं का निरीक्षण करने की बजाय दबाने की प्रवृत्ति होती है;माइंडफुलनेस प्रथाएं सहायता प्रदान कर सकती हैं।'},
            'overidentification': {"high": 'नकारात्मक भावनाओं और विचारों पर अत्यधिक ध्यान केंद्रित करने की प्रवृत्ति होती है;माइंडफुलनेस अभ्यास इस चक्र को तोड़ता है।', "moderate": 'आप कभी-कभी नकारात्मक विचारों को जरूरत से ज्यादा पहचान सकते हैं;संतुलन रणनीतियाँ मदद करती हैं।', "low": 'आप नकारात्मक विचारों से स्वस्थ दूरी बनाए रखें;सचेत जागरूकता का एक मजबूत संकेतक।'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'आपको चुनौतीपूर्ण कार्यों को पूरा करने की अपनी क्षमता पर दृढ़ विश्वास है।', "moderate": 'आपका आत्म-प्रभावकारिता विश्वास विकसित हो रहा है;छोटी-छोटी सफलताएँ अर्जित करने से यह आत्मविश्वास बढ़ता है।', "low": 'आपकी अपनी क्षमताओं पर विश्वास कम है;छोटे कदमों के माध्यम से सफलता के अनुभव बनाने से मदद मिलती है।'},
        },
        'stress': {
            'perceived_stress': {"high": 'आप हाल ही में उच्च स्तर का तनाव महसूस कर रहे हैं;तनाव प्रबंधन रणनीतियाँ अब विशेष रूप से महत्वपूर्ण हैं।', "moderate": 'आप मध्यम तनाव का अनुभव कर रहे हैं;तनाव ट्रिगर करने वालों की पहचान करने और उनका प्रबंधन करने से लाभ मिलता है।', "low": 'आपके तनाव बोध का स्तर कम है;चुनौतियों से निपटने की आपकी क्षमता मजबूत दिखाई देती है।'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'आप अपनी उपस्थिति का मूल्यांकन आम तौर पर सकारात्मक रूप से करते हैं;स्वस्थ शरीर की छवि का संकेत.', "moderate": 'आपकी उपस्थिति के मूल्यांकन मिश्रित हैं;आपके शरीर की कार्यक्षमता पर ध्यान केंद्रित करने से दृष्टिकोण व्यापक होता है।', "low": 'आपकी उपस्थिति का नकारात्मक मूल्यांकन करने की प्रवृत्ति है;शरीर पुष्टिकरण प्रथाएँ यहाँ सहायता प्रदान करती हैं।'},
            'body_satisfaction': {"high": 'आप आम तौर पर अपने शरीर से संतुष्ट हैं;स्वस्थ आत्म-स्वीकृति का संकेत.', "moderate": 'आपकी शारीरिक संतुष्टि मध्यम है;आपके शरीर की शक्तियों पर ध्यान केंद्रित करने से इस क्षेत्र का पोषण होता है।', "low": 'आप अपने शरीर से असंतुष्ट महसूस करते हैं;आत्म-करुणा अभ्यास और पेशेवर समर्थन फायदेमंद हो सकते हैं।'},
        },
    },
    'fr': {
        'personality': {
            'openness': {"high": 'Votre curiosité et votre imagination sont fortes ;les nouvelles expériences et idées vous attirent naturellement.', "moderate": 'Vous équilibrez curiosité et praticité, curieux dans certains domaines et conventionnel dans d’autres.', "low": 'Vous préférez le pratique et le familier\xa0;des routines cohérentes et des approches éprouvées vous conviennent.'},
            'conscientiousness': {"high": 'Vous êtes discipliné, organisé et fiable ;vous poursuivez systématiquement des objectifs.', "moderate": 'Vous équilibrez responsabilité et flexibilité ;la création de routines renforcerait encore cela.', "low": 'Vous avez un style flexible et spontané ;développer des habitudes de planification peut améliorer votre efficacité.'},
            'extraversion': {"high": 'Votre énergie sociale est élevée\xa0;vous tirez votre force des gens et apportez de l’énergie à ceux qui vous entourent.', "moderate": "Vous équilibrez le temps avec les autres et le temps seul, à l'aise dans les deux contextes.", "low": 'Votre nature introvertie est un atout naturel pour une réflexion approfondie et un travail ciblé.'},
            'agreeableness': {"high": 'Votre nature chaleureuse et coopérative renforce la confiance et l’harmonie dans vos relations.', "moderate": 'Vous équilibrez coopération et indépendance, compréhension mais affirmation de soi.', "low": 'Vous penchez vers une pensée indépendante et critique – une force pour l’analyse et le jugement objectif.'},
            'neuroticism': {"high": 'Vos réactions émotionnelles peuvent être intenses ;Des stratégies de gestion du stress et d’autorégulation vous soutiendront.', "moderate": 'Vous vivez des hauts et des bas émotionnels\xa0;la plupart du temps, vous pouvez retrouver votre équilibre.', "low": 'Votre résilience émotionnelle est forte\xa0;vous restez calme sous la pression et gérez les difficultés avec aisance.'},
        },
        'skills': {
            'problem_solving': {"high": 'Vous êtes doué pour analyser des problèmes complexes et générer des solutions pratiques.', "moderate": 'Votre approche de résolution de problèmes se développe\xa0;des techniques de pensée structurée peuvent vous aider.', "low": 'L’apprentissage de méthodes systématiques de résolution de problèmes libérera votre potentiel dans ce domaine.'},
            'empathy': {"high": "Vous avez une capacité remarquable à comprendre les émotions des autres et à faire preuve d'empathie.", "moderate": "Vos capacités d'empathie se développent\xa0;pratiquer l’écoute active renforcera ce domaine.", "low": 'Explorer davantage le point de vue des autres fera de vous un communicateur plus efficace.'},
            'organization': {"high": 'Votre planification et vos priorités sont solides\xa0;votre style organisé vous aide à vous démarquer.', "moderate": "Votre sens de l'organisation est raisonnable\xa0;utiliser des outils de gestion du temps peut vous rendre encore plus fort.", "low": 'Développer des habitudes organisationnelles systématiques peut améliorer considérablement votre productivité.'},
            'learning_speed': {"high": 'Vous vous adaptez rapidement aux nouvelles connaissances et compétences – un avantage majeur dans des environnements changeants.', "moderate": "Votre rythme d'apprentissage est raisonnable ;expérimenter différentes stratégies peut augmenter votre efficacité.", "low": 'Des stratégies structurées de révision et de pratique soutiendront votre processus d’apprentissage dans ce domaine.'},
            'decision_making': {"high": 'Vous pouvez prendre des mesures décisives et rapides dans des situations de prise de décision.', "moderate": 'Vos capacités de prise de décision se développent\xa0;des cadres structurés aident dans les moments difficiles.', "low": 'Commencer par des décisions plus modestes est un moyen efficace de renforcer votre confiance en matière de prise de décision.'},
        },
        'hr': {
            'leadership': {"high": 'Vous savez diriger des équipes, inspirer les autres et prendre les devants.', "moderate": 'Vous avez des aptitudes en leadership ;les expériences pratiques développeront ces compétences rapidement.', "low": 'Développer délibérément des compétences en leadership par la pratique peut faire progresser considérablement votre carrière.'},
            'team_fit': {"high": 'Vous vous démarquez par un travail d’équipe harmonieux, une collaboration et une serviabilité.', "moderate": 'La forme de votre équipe est bonne\xa0;comprendre différents styles de travail renforcera encore cela.', "low": 'Une participation plus active à la dynamique d’équipe renforcera vos relations professionnelles.'},
            'communication': {"high": 'Vous êtes doué pour une communication claire, efficace et constructive.', "moderate": 'Votre style de communication se développe ;s’adapter à différents publics vous donne un avantage.', "low": 'La pratique systématique des compétences en communication produira des progrès rapides dans ce domaine.'},
            'stress_tolerance': {"high": 'Vous pouvez garder votre sang-froid sous pression\xa0;une pierre angulaire de la résilience professionnelle.', "moderate": 'Votre capacité à faire face au stress est raisonnable\xa0;les techniques de renforcement de la résilience vous rendront encore plus fort.', "low": 'Développer des stratégies de gestion du stress, soutenues par des pratiques quotidiennes, produit des résultats rapidement.'},
            'motivation': {"high": 'Votre motivation intrinsèque est élevée\xa0;vous abordez vos objectifs avec engagement et passion.', "moderate": 'Votre motivation varie\xa0;rester connecté à votre objectif peut être une source d’énergie continue.', "low": 'Se fixer des objectifs significatifs à court terme est un moyen efficace de raviver votre motivation.'},
        },
        'career': {
            'analytical': {"high": 'Vous avez une forte orientation vers la pensée analytique et les environnements de travail axés sur les données.', "moderate": 'Vous avez des tendances analytiques ;une pratique structurée de résolution de problèmes renforcera ce domaine.', "low": 'Développer des compétences analytiques systématiques élargira vos options dans ce domaine de carrière.'},
            'creative': {"high": 'Vous vous exprimez mieux dans des environnements de travail créatifs et innovants.', "moderate": 'Vous avez des tendances créatives ;nourrir ce domaine peut augmenter votre épanouissement professionnel.', "low": 'Les parcours professionnels structurels et techniques semblent actuellement plus alignés que les rôles axés sur la création.'},
            'social': {"high": 'Aider, enseigner ou travailler avec des gens vous dynamise.', "moderate": "Vous êtes à l'aise dans des rôles impliquant des interactions sociales ;des connexions plus profondes peuvent ajouter de la valeur.", "low": 'Les parcours professionnels à vocation sociale ne constituent pas actuellement un domaine d’intérêt majeur pour vous.'},
            'entrepreneurial': {"high": 'Vous avez une forte tendance aux rôles entrepreneuriaux nécessitant du leadership, de la persuasion et de la prise de risques.', "moderate": 'Votre perspective entrepreneuriale se développe\xa0;l’expérience en matière de prise de décision et de leadership accélérera cela.', "low": 'Les parcours professionnels axés sur l’expertise semblent actuellement plus alignés que les rôles entrepreneuriaux.'},
            'managerial': {"high": 'Vous êtes bien adapté aux rôles qui nécessitent de la gestion, de la coordination et de l’organisation.', "moderate": 'Vos tendances managériales se développent ;assumer des responsabilités nourrira ce domaine.', "low": "Les parcours de carrière axés sur l'expertise avec moins de pression managériale peuvent sembler plus confortables à l'heure actuelle."},
            'technical': {"high": 'Vous avez un fort intérêt et une orientation vers les domaines techniques et spécialisés.', "moderate": 'Vos compétences techniques se développent ;une spécialisation approfondie renforcera ce domaine.', "low": 'Les parcours professionnels axés sur les personnes semblent actuellement plus alignés que les rôles de spécialistes techniques.'},
        },
        'vocation': {
            'realistic': {"high": 'Vous avez une forte inclination pour le travail pratique, pratique et technique.', "moderate": 'Vous avez un intérêt modéré pour le travail pratique ;essayer cette zone vous donnera une image plus claire.', "low": 'Les activités pratiques et techniques ne font pas actuellement partie de vos principaux intérêts.'},
            'investigative': {"high": 'La recherche, l’analyse et l’exploration d’idées vous attirent naturellement.', "moderate": "Vous avez un intérêt pour l'enquête\xa0;l’approfondissement des connaissances dans ce domaine les renforcera encore.", "low": "Les activités axées sur la recherche et l'analyse ne font pas actuellement partie de vos intérêts prioritaires."},
            'artistic': {"high": 'Vous avez un fort penchant pour les activités nécessitant une expression créative, de l’art et de l’esthétique.', "moderate": 'Vous avez des tendances artistiques ;nourrir ce domaine peut apporter épanouissement et authenticité.', "low": 'Les activités artistiques et créatives ne constituent pas actuellement un domaine d’intérêt majeur pour vous.'},
            'social': {"high": 'Être avec les gens, aider et enseigner vous dynamise.', "moderate": 'Vous avez un intérêt modéré pour les activités sociales ;établir des liens significatifs apporte de la satisfaction.', "low": 'Les activités à vocation sociale ne font pas actuellement partie de vos intérêts prioritaires.'},
            'enterprising': {"high": 'Vous vous sentez plus fort dans les activités qui nécessitent du leadership, de la persuasion et de la compétition.', "moderate": 'Vous avez des tendances entreprenantes ;exercer la responsabilité et la prise de décision renforce cela.', "low": 'Les activités compétitives et axées sur le leadership ne constituent pas actuellement un domaine d’intérêt majeur pour vous.'},
            'conventional': {"high": 'Vous êtes fort dans des environnements de travail organisés, systématiques et conformes aux règles.', "moderate": "Vous avez un intérêt modéré pour l'organisation et la structure ;une pratique de travail systématique nourrit cela.", "low": 'Les activités structurées et conventionnelles ne constituent pas actuellement un fort intérêt pour vous.'},
        },
        'relationship': {
            'love_language': {"high": 'Vous exprimez clairement votre langage amoureux et valorisez la compréhension mutuelle dans les relations.', "moderate": 'Vous exprimez votre langage amoureux avec modération ;être plus ouvert ici peut enrichir vos relations.', "low": 'Développer la conscience de l’expression émotionnelle et des langages de l’amour approfondira vos liens.'},
            'conflict_style': {"high": 'Vous êtes doué pour résoudre les conflits de manière constructive et saine.', "moderate": 'Votre style de résolution de conflits se développe\xa0;essayer des approches plus constructives peut aider.', "low": 'Développer des stratégies saines de résolution des conflits améliorera considérablement la qualité de votre relation.'},
            'intimacy_needs': {"high": 'Vous comprenez clairement vos besoins de proximité émotionnelle et de connexion.', "moderate": "Vous avez une conscience modérée de vos besoins en matière d'intimité\xa0;il est utile d’explorer davantage ce domaine.", "low": 'Comprendre vos besoins en matière de liens émotionnels et d’intimité rendra vos relations plus épanouissantes.'},
            'relationship_values': {"high": 'Vous disposez d’un cadre de valeurs clair pour ce que vous souhaitez dans vos relations.', "moderate": 'Vos valeurs relationnelles prennent forme ;réfléchir à cela vous aide à établir des relations plus saines.', "low": 'Découvrir et clarifier vos valeurs relationnelles personnelles jette les bases de liens plus profonds.'},
        },
        'attachment': {
            'anxiety': {"high": 'L’anxiété liée à l’abandon est élevée ;cette prise de conscience est un point de départ solide pour développer un attachement sécurisé.', "moderate": 'L’anxiété d’attachement est modérée ;les pratiques relationnelles sécurisées soutiennent ce domaine.', "low": 'Votre anxiété d’abandon est faible\xa0;vous faites preuve d’un attachement sûr et équilibré dans les relations.'},
            'avoidance': {"high": 'L’évitement de la proximité émotionnelle est perceptible\xa0;reconnaître ce modèle est la première étape vers des liens plus profonds.', "moderate": 'L’évitement de la proximité est modéré\xa0;à mesure que la conscience de soi grandit, vous pouvez établir des connexions plus ouvertes.', "low": "Votre évitement de la proximité émotionnelle est faible\xa0;l'ouverture et la connexion se sentent à l'aise dans les relations."},
        },
        'grit': {
            'perseverance': {"high": 'Vous êtes fort pour terminer ce que vous avez commencé et continuer malgré les obstacles.', "moderate": 'Your determination and grit are developing;rester engagé envers des objectifs à long terme renforce cela.', "low": 'Accumuler les succès à court terme est une stratégie efficace pour bâtir une persévérance durable.'},
            'passion': {"high": 'Vous faites preuve d’une passion et d’un intérêt constants pour vos objectifs à long terme.', "moderate": 'Votre passion pour les objectifs se développe\xa0;se connecter à un objectif significatif amplifie cette énergie.', "low": 'Découvrir des intérêts qui vous passionnent véritablement alimentera votre passion et votre motivation.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'Vous croyez fermement que les capacités et l’intelligence peuvent être développées grâce à l’effort.', "moderate": 'Votre état d’esprit de croissance se développe\xa0;considérer les défis comme des opportunités d’apprentissage nourrit cela.', "low": 'La croyance selon laquelle les capacités sont fixes persiste ;remettre en question cet état d’esprit accélérera votre croissance.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'Vous déclarez être très satisfait de votre vie et faites une évaluation globalement positive.', "moderate": 'Votre satisfaction dans la vie est modérée\xa0;le renforcement de l’alignement sens-valeur augmente l’épanouissement.', "low": 'La satisfaction de vivre est faible\xa0;se demander ce que vous voulez changer est un bon point de départ.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'Vous vous approchez avec compassion et compréhension\xa0;une forte source de résilience psychologique.', "moderate": 'Votre compassion envers vous-même se développe\xa0;se parler comme un ami dans les moments difficiles nourrit cela.', "low": 'Une voix intérieure dure se fait entendre ;développer des pratiques d’auto-compassion vous soutiendra.'},
            'self_judgment': {"high": 'Une tendance à être trop autocritique est présente ;reconnaître qu’il s’agit là d’un puissant point de départ pour le changement.', "moderate": "L'autocritique est modérée ;être plus gentil avec soi-même apporte parfois des avantages.", "low": 'Vous faites preuve d’une attitude équilibrée et bienveillante envers vous-même ;un signe sain d’auto-évaluation.'},
            'common_humanity': {"high": 'Vous comprenez que vos luttes font partie de l’expérience humaine partagée, qui apporte du réconfort.', "moderate": 'Votre sens de l’humanité commune se développe ;se rappeler que vous n’êtes pas seul vous renforce.', "low": "Vous pouvez vous sentir isolé lorsque des difficultés surviennent ;rappelez-vous que c'est une expérience très courante."},
            'isolation': {"high": 'Vous vous sentez isolé et seul dans les moments difficiles\xa0;la recherche de connexion et de soutien aide à équilibrer cela.', "moderate": 'Des sentiments d’isolement peuvent surgir de temps à autre ;l’établissement de liens aide à équilibrer cela.', "low": 'Vous vous sentez connecté et soutenu face aux difficultés ;un signe important de santé psychologique.'},
            'mindfulness': {"high": 'Vous pouvez observer vos émotions avec équilibre et conscience ;une position psychologique saine.', "moderate": 'Votre conscience consciente se développe\xa0;de simples pratiques de méditation renforceront ce domaine.', "low": 'Il existe une tendance à réprimer plutôt qu’à observer les émotions ;les pratiques de pleine conscience peuvent apporter un soutien.'},
            'overidentification': {"high": 'Il existe une tendance à trop se concentrer sur les émotions et les pensées négatives ;les pratiques de pleine conscience brisent ce cycle.', "moderate": 'Vous pouvez parfois vous suridentifier à des pensées négatives\xa0;les stratégies d’équilibre aident.', "low": 'Vous maintenez une distance saine par rapport aux pensées négatives\xa0;un indicateur fort de la pleine conscience.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'Vous croyez fermement en votre capacité à accomplir des tâches difficiles.', "moderate": 'Votre confiance en votre efficacité personnelle se développe\xa0;accumuler de petits succès augmente cette confiance.', "low": 'La confiance en vos propres capacités est faible ;construire des expériences de réussite par petites étapes aide.'},
        },
        'stress': {
            'perceived_stress': {"high": 'Vous ressentez récemment un niveau de stress élevé\xa0;Les stratégies de gestion du stress sont particulièrement importantes à l’heure actuelle.', "moderate": 'Vous vivez un stress modéré\xa0;l’identification et la gestion des déclencheurs de stress sont bénéfiques.', "low": 'Votre niveau de perception du stress est faible\xa0;votre capacité à relever les défis semble forte.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'Vous évaluez votre apparence généralement positivement ;un signe d’une image corporelle saine.', "moderate": 'Vos évaluations d’apparence sont mitigées\xa0;se concentrer sur la fonctionnalité de votre corps élargit la perspective.', "low": 'Il existe une tendance à évaluer votre apparence négativement\xa0;les pratiques d’affirmation corporelle apportent ici un soutien.'},
            'body_satisfaction': {"high": 'Vous êtes généralement satisfait de votre corps ;un signe d’acceptation de soi saine.', "moderate": 'Votre satisfaction corporelle est modérée\xa0;se concentrer sur les points forts de votre corps nourrit ce domaine.', "low": 'Vous vous sentez insatisfait de votre corps\xa0;des pratiques d’auto-compassion et un soutien professionnel peuvent être bénéfiques.'},
        },
    },
    'pt': {
        'personality': {
            'openness': {"high": 'Sua curiosidade e imaginação são fortes;novas experiências e ideias atraem você naturalmente.', "moderate": 'Você equilibra curiosidade com praticidade, curioso em algumas áreas e convencional em outras.', "low": 'Você prefere o prático e familiar;rotinas consistentes e abordagens comprovadas parecem adequadas para você.'},
            'conscientiousness': {"high": 'Você é disciplinado, organizado e confiável;você persegue objetivos sistematicamente.', "moderate": 'Você equilibra responsabilidade e flexibilidade;construir rotinas fortaleceria ainda mais isso.', "low": 'Você tem um estilo flexível e espontâneo;desenvolver hábitos de planejamento pode melhorar sua eficácia.'},
            'extraversion': {"high": 'Sua energia social está alta;você extrai força das pessoas e traz energia para aqueles ao seu redor.', "moderate": 'Você equilibra o tempo com outras pessoas e o tempo sozinho, confortável em ambos os ambientes.', "low": 'Sua natureza introvertida é um recurso natural para pensamentos profundos e trabalho focado.'},
            'agreeableness': {"high": 'Sua natureza calorosa e cooperativa cria confiança e harmonia em seus relacionamentos.', "moderate": 'Você equilibra cooperação e independência, sendo compreensivo, mas auto-afirmativo.', "low": 'Você se inclina para o pensamento crítico e independente – uma força para análise e julgamento objetivo.'},
            'neuroticism': {"high": 'Suas reações emocionais podem ser intensas;estratégias de gerenciamento de estresse e autorregulação irão apoiá-lo.', "moderate": 'Você passa por alguns altos e baixos emocionais;na maioria das vezes você pode encontrar o equilíbrio novamente.', "low": 'Sua resiliência emocional é forte;você permanece calmo sob pressão e lida com as dificuldades com facilidade.'},
        },
        'skills': {
            'problem_solving': {"high": 'Você é forte na análise de problemas complexos e na geração de soluções práticas.', "moderate": 'Sua abordagem de resolução de problemas está se desenvolvendo;técnicas de pensamento estruturado podem apoiá-lo.', "low": 'Aprender métodos sistemáticos de resolução de problemas irá desbloquear seu potencial nesta área.'},
            'empathy': {"high": 'Você tem uma capacidade notável de compreender as emoções dos outros e de se conectar com a empatia.', "moderate": 'Suas habilidades de empatia estão se desenvolvendo;praticar a escuta ativa fortalecerá esta área.', "low": 'Explorar mais as perspectivas dos outros fará de você um comunicador mais eficaz.'},
            'organization': {"high": 'Seu planejamento e priorização são fortes;seu estilo organizado ajuda você a se destacar.', "moderate": 'Sua habilidade organizacional é razoável;usar ferramentas de gerenciamento de tempo pode torná-lo ainda mais forte.', "low": 'O desenvolvimento de hábitos organizacionais sistemáticos pode melhorar significativamente sua produtividade.'},
            'learning_speed': {"high": 'Você se adapta rapidamente a novos conhecimentos e habilidades – uma grande vantagem em ambientes em mudança.', "moderate": 'Seu ritmo de aprendizagem é razoável;experimentar diferentes estratégias pode aumentar sua eficácia.', "low": 'Revisão estruturada e estratégias práticas apoiarão seu processo de aprendizagem nesta área.'},
            'decision_making': {"high": 'Você pode tomar medidas rápidas e decisivas em situações de tomada de decisão.', "moderate": 'Suas habilidades de tomada de decisão estão se desenvolvendo;estruturas estruturadas ajudam em momentos difíceis.', "low": 'Começar com decisões menores é uma maneira eficaz de aumentar sua confiança na tomada de decisões.'},
        },
        'hr': {
            'leadership': {"high": 'Você é forte em dirigir equipes, inspirar outras pessoas e assumir a liderança.', "moderate": 'Você tem aptidão para liderança;experiências práticas desenvolverão essas habilidades rapidamente.', "low": 'O desenvolvimento deliberado de habilidades de liderança por meio da prática pode avançar significativamente em sua carreira.'},
            'team_fit': {"high": 'Você se destaca pelo trabalho em equipe harmonioso, colaboração e ajuda.', "moderate": 'O ajuste da sua equipe é bom;compreender os diferentes estilos de trabalho fortalecerá isso ainda mais.', "low": 'Uma participação mais ativa na dinâmica da equipe fortalecerá seus relacionamentos profissionais.'},
            'communication': {"high": 'Você é forte em comunicação clara, eficaz e construtiva.', "moderate": 'Seu estilo de comunicação está se desenvolvendo;adaptar-se a públicos diferentes oferece uma vantagem.', "low": 'Praticar sistematicamente as habilidades de comunicação produzirá um rápido progresso nesta área.'},
            'stress_tolerance': {"high": 'Você pode manter a compostura sob pressão;uma pedra angular da resiliência profissional.', "moderate": 'Sua capacidade de lidar com o estresse é razoável;técnicas de construção de resiliência o tornarão ainda mais forte.', "low": 'Desenvolver estratégias de gestão do estresse, apoiadas em práticas diárias, produz resultados rapidamente.'},
            'motivation': {"high": 'Sua motivação intrínseca é alta;você aborda seus objetivos com comprometimento e paixão.', "moderate": 'Sua motivação varia;permanecer conectado ao seu propósito pode ser uma fonte contínua de energia.', "low": 'Definir metas significativas de curto prazo é uma forma eficaz de reacender sua motivação.'},
        },
        'career': {
            'analytical': {"high": 'Você tem uma forte orientação para o pensamento analítico e ambientes de trabalho focados em dados.', "moderate": 'Você tem tendências analíticas;a prática estruturada de resolução de problemas fortalecerá esta área.', "low": 'O desenvolvimento de habilidades analíticas sistemáticas expandirá suas opções nesta área de carreira.'},
            'creative': {"high": 'Você se expressa melhor em ambientes de trabalho criativos e inovadores.', "moderate": 'Você tem tendências criativas;nutrir essa área pode aumentar a realização de sua carreira.', "low": 'As carreiras estruturais e técnicas parecem atualmente mais alinhadas do que as funções com foco criativo.'},
            'social': {"high": 'Ajudar, ensinar ou trabalhar com pessoas dá energia a você.', "moderate": 'Você se sente confortável em papéis que envolvem interação social;conexões mais profundas podem agregar valor.', "low": 'As carreiras com foco social não são atualmente uma área de grande interesse para você.'},
            'entrepreneurial': {"high": 'Você tem uma forte tendência para funções empreendedoras que exigem liderança, persuasão e assunção de riscos.', "moderate": 'Sua perspectiva empreendedora está se desenvolvendo;a tomada de decisões e a experiência de liderança irão acelerar isso.', "low": 'Atualmente, as trajetórias de carreira focadas em conhecimentos especializados parecem mais alinhadas do que as funções empreendedoras.'},
            'managerial': {"high": 'Você é adequado para funções que exigem gerenciamento, coordenação e organização.', "moderate": 'Suas tendências gerenciais estão se desenvolvendo;assumir responsabilidades irá nutrir esta área.', "low": 'Planos de carreira focados em experiência e com menos pressão gerencial podem parecer mais confortáveis \u200b\u200bagora.'},
            'technical': {"high": 'Você tem um forte interesse e orientação para áreas técnicas e especializadas.', "moderate": 'Suas habilidades técnicas estão se desenvolvendo;a especialização profunda fortalecerá esta área.', "low": 'Atualmente, as trajetórias de carreira focadas nas pessoas parecem mais alinhadas do que as funções de especialistas técnicos.'},
        },
        'vocation': {
            'realistic': {"high": 'Você tem uma forte inclinação para trabalhos práticos, práticos e técnicos.', "moderate": 'Você tem interesse moderado em trabalho prático;tentar esta área lhe dará uma imagem mais clara.', "low": 'As atividades práticas e técnicas não estão atualmente entre os seus grandes interesses.'},
            'investigative': {"high": 'Pesquisa, análise e exploração de ideias atraem você naturalmente.', "moderate": 'Você tem interesse investigativo;aprofundar o conhecimento nesta área irá fortalecê-lo ainda mais.', "low": 'As atividades focadas em pesquisa e análise não estão atualmente entre os seus interesses prioritários.'},
            'artistic': {"high": 'Você tem uma forte inclinação para atividades que exigem expressão criativa, arte e estética.', "moderate": 'Você tem tendências artísticas;nutrir essa área pode proporcionar realização e autenticidade.', "low": 'As atividades artísticas e criativas não são atualmente uma área de grande interesse para você.'},
            'social': {"high": 'Estar com as pessoas, ajudar e ensinar dá energia a você.', "moderate": 'Você tem interesse moderado em atividades sociais;construir conexões significativas traz satisfação.', "low": 'As atividades com foco social não estão atualmente entre os seus interesses prioritários.'},
            'enterprising': {"high": 'Você se sente mais forte em atividades que exigem liderança, persuasão e competição.', "moderate": 'Você tem tendências empreendedoras;praticar a responsabilidade e a tomada de decisões fortalece isso.', "low": 'Atividades competitivas e focadas em liderança não são atualmente uma área de grande interesse para você.'},
            'conventional': {"high": 'Você é forte em ambientes de trabalho organizados, sistemáticos e consistentes com regras.', "moderate": 'Você tem interesse moderado em organização e estrutura;a prática sistemática de trabalho alimenta isso.', "low": 'As atividades estruturadas e convencionais não são atualmente uma área de grande interesse para você.'},
        },
        'relationship': {
            'love_language': {"high": 'Você expressa claramente sua linguagem de amor e valoriza a compreensão mútua nos relacionamentos.', "moderate": 'Você expressa sua linguagem de amor com moderação;ser mais aberto aqui pode enriquecer seus relacionamentos.', "low": 'Desenvolver a consciência da expressão emocional e das linguagens do amor aprofundará suas conexões.'},
            'conflict_style': {"high": 'Você é forte na resolução de conflitos de maneira construtiva e saudável.', "moderate": 'Seu estilo de resolução de conflitos está se desenvolvendo;tentar abordagens mais construtivas pode ajudar.', "low": 'O desenvolvimento de estratégias saudáveis \u200b\u200bde resolução de conflitos melhorará significativamente a qualidade do seu relacionamento.'},
            'intimacy_needs': {"high": 'Você entende claramente suas necessidades de proximidade e conexão emocional.', "moderate": 'Você tem consciência moderada de suas necessidades de intimidade;explorar mais esta área é valioso.', "low": 'Compreender seu vínculo emocional e necessidades de intimidade tornará seus relacionamentos mais gratificantes.'},
            'relationship_values': {"high": 'Você tem uma estrutura de valores clara para o que deseja em seus relacionamentos.', "moderate": 'Seus valores de relacionamento estão tomando forma;refletir sobre isso ajuda você a construir conexões mais saudáveis.', "low": 'Descobrir e esclarecer os valores do seu relacionamento pessoal estabelece as bases para laços mais profundos.'},
        },
        'attachment': {
            'anxiety': {"high": 'A ansiedade em relação ao abandono é elevada;esta consciência é um forte ponto de partida para o desenvolvimento de um apego seguro.', "moderate": 'A ansiedade de apego é moderada;práticas de relacionamento seguras apoiam esta área.', "low": 'Sua ansiedade de abandono é baixa;você mostra apego seguro e equilibrado nos relacionamentos.'},
            'avoidance': {"high": 'A evitação da proximidade emocional é perceptível;reconhecer esse padrão é o primeiro passo em direção a laços mais profundos.', "moderate": 'A evitação da proximidade é moderada;à medida que a autoconsciência aumenta, você pode construir conexões mais abertas.', "low": 'Sua evitação de proximidade emocional é baixa;abertura e conexão se sentem confortáveis \u200b\u200bnos relacionamentos.'},
        },
        'grit': {
            'perseverance': {"high": 'Você é forte em concluir o que começa e continuar apesar dos obstáculos.', "moderate": 'Sua determinação e coragem estão se desenvolvendo;permanecer comprometido com objetivos de longo prazo fortalece isso.', "low": 'Acumular sucessos de curto prazo é uma estratégia eficaz para construir uma perseverança sustentável.'},
            'passion': {"high": 'Você demonstra paixão e interesse consistentes por seus objetivos de longo prazo.', "moderate": 'Sua paixão por objetivos está se desenvolvendo;conectar-se a um propósito significativo amplifica essa energia.', "low": 'Descobrir interesses que realmente o estimulam alimentará sua paixão e motivação.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'Você acredita firmemente que as habilidades e a inteligência podem ser desenvolvidas através do esforço.', "moderate": 'Sua mentalidade construtiva está se desenvolvendo;encarar os desafios como oportunidades de aprendizagem estimula isso.', "low": 'A crença de que as habilidades são fixas continua;questionar essa mentalidade acelerará seu crescimento.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'Você relata alta satisfação com sua vida e faz uma avaliação geral positiva.', "moderate": 'Sua satisfação com a vida é moderada;fortalecer o alinhamento significado-valor aumenta a realização.', "low": 'A satisfação com a vida é baixa;perguntar a si mesmo o que deseja mudar é um bom ponto de partida.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'Você se aproxima com compaixão e compreensão;uma forte fonte de resiliência psicológica.', "moderate": 'Sua autocompaixão está se desenvolvendo;falar consigo mesmo como um amigo em momentos difíceis alimenta isso.', "low": 'Uma voz interior áspera é proeminente;desenvolver práticas de autocompaixão irá apoiá-lo.'},
            'self_judgment': {"high": 'Existe uma tendência a ser excessivamente autocrítico;reconhecer que isto é um poderoso ponto de partida para a mudança.', "moderate": 'A autocrítica é moderada;ser mais gentil consigo mesmo às vezes traz benefícios.', "low": 'Você mostra uma atitude equilibrada e gentil consigo mesmo;um sinal saudável de autoavaliação.'},
            'common_humanity': {"high": 'Você entende que suas lutas fazem parte da experiência humana compartilhada, que traz conforto.', "moderate": 'O vosso sentido de humanidade comum está a desenvolver-se;lembrar que você não está sozinho te fortalece.', "low": 'Você pode se sentir isolado quando surgem dificuldades;lembre-se de que esta é uma experiência muito comum.'},
            'isolation': {"high": 'Você se sente isolado e sozinho em momentos difíceis;buscar conexão e suporte ajuda a equilibrar isso.', "moderate": 'Podem surgir sentimentos de isolamento de vez em quando;construir conexões ajuda a equilibrar isso.', "low": 'Você se sente conectado e apoiado ao enfrentar dificuldades;um importante sinal de saúde psicológica.'},
            'mindfulness': {"high": 'Você pode observar suas emoções com equilíbrio e consciência;uma postura psicológica saudável.', "moderate": 'Sua consciência plena está se desenvolvendo;práticas simples de meditação fortalecerão esta área.', "low": 'Há uma tendência de suprimir as emoções em vez de observá-las;práticas de mindfulness podem fornecer apoio.'},
            'overidentification': {"high": 'Há uma tendência de focar demais em emoções e pensamentos negativos;as práticas de mindfulness quebram esse ciclo.', "moderate": 'Às vezes você pode se identificar demais com pensamentos negativos;estratégias de equilíbrio ajudam.', "low": 'Você mantém uma distância saudável de pensamentos negativos;um forte indicador de consciência consciente.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'Você acredita fortemente em sua capacidade de realizar tarefas desafiadoras.', "moderate": 'Sua crença de autoeficácia está se desenvolvendo;acumular pequenos sucessos aumenta essa confiança.', "low": 'A confiança nas suas próprias habilidades é baixa;construir experiências de sucesso por meio de pequenos passos ajuda.'},
        },
        'stress': {
            'perceived_stress': {"high": 'Você está percebendo um alto nível de estresse recentemente;estratégias de gerenciamento de estresse são especialmente importantes agora.', "moderate": 'Você está passando por estresse moderado;identificar e gerenciar os gatilhos do estresse traz benefícios.', "low": 'Seu nível de percepção de estresse é baixo;sua capacidade de lidar com desafios parece forte.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'Você avalia sua aparência geralmente de forma positiva;um sinal de imagem corporal saudável.', "moderate": 'Suas avaliações de aparência são confusas;focar na funcionalidade do seu corpo amplia a perspectiva.', "low": 'Há uma tendência de avaliar negativamente sua aparência;as práticas de afirmação corporal fornecem suporte aqui.'},
            'body_satisfaction': {"high": 'Você geralmente está satisfeito com seu corpo;um sinal de autoaceitação saudável.', "moderate": 'A sua satisfação corporal é moderada;focar nos pontos fortes do seu corpo nutre essa área.', "low": 'Você se sente insatisfeito com seu corpo;práticas de autocompaixão e apoio profissional podem ser benéficas.'},
        },
    },
    'bn': {
        'personality': {
            'openness': {"high": 'আপনার কৌতূহল এবং কল্পনা শক্তিশালী;নতুন অভিজ্ঞতা এবং ধারণা স্বাভাবিকভাবেই আপনাকে আকর্ষণ করে।', "moderate": 'আপনি ব্যবহারিকতার সাথে কৌতূহলের ভারসাম্য বজায় রাখেন, কিছু ক্ষেত্রে কৌতূহলী এবং অন্যগুলিতে প্রচলিত।', "low": 'আপনি ব্যবহারিক এবং পরিচিত পছন্দ;সামঞ্জস্যপূর্ণ রুটিন এবং প্রমাণিত পন্থা আপনার জন্য সঠিক মনে হয়।'},
            'conscientiousness': {"high": 'আপনি সুশৃঙ্খল, সংগঠিত এবং নির্ভরযোগ্য;আপনি নিয়মতান্ত্রিকভাবে লক্ষ্যগুলি অনুসরণ করেন।', "moderate": 'আপনি দায়িত্ব এবং নমনীয়তা ভারসাম্য;বিল্ডিং রুটিন এটি আরো শক্তিশালী হবে.', "low": 'আপনি একটি নমনীয়, স্বতঃস্ফূর্ত শৈলী আছে;পরিকল্পনার অভ্যাস বিকাশ আপনার কার্যকারিতা উন্নত করতে পারে।'},
            'extraversion': {"high": 'আপনার সামাজিক শক্তি উচ্চ;আপনি মানুষের কাছ থেকে শক্তি পান এবং আপনার চারপাশের লোকেদের জন্য শক্তি আনেন।', "moderate": 'আপনি অন্যদের সাথে সময় এবং একা সময় ভারসাম্য রাখেন, উভয় সেটিংসেই আরামদায়ক।', "low": 'আপনার অন্তর্মুখী প্রকৃতি গভীর চিন্তা এবং মনোযোগী কাজের জন্য একটি প্রাকৃতিক সম্পদ।'},
            'agreeableness': {"high": 'আপনার উষ্ণ, সহযোগিতামূলক প্রকৃতি আপনার সম্পর্কের মধ্যে বিশ্বাস এবং সাদৃশ্য তৈরি করে।', "moderate": 'আপনি সমবায় এবং স্বাধীনতার মধ্যে ভারসাম্য বজায় রাখেন, বোঝার পরও স্ব-প্রত্যয়ী।', "low": 'আপনি স্বাধীন, সমালোচনামূলক চিন্তাভাবনার দিকে ঝুঁকছেন — বিশ্লেষণ এবং উদ্দেশ্যমূলক বিচারের শক্তি।'},
            'neuroticism': {"high": 'আপনার মানসিক প্রতিক্রিয়া তীব্র হতে পারে;স্ট্রেস ম্যানেজমেন্ট এবং স্ব-নিয়ন্ত্রণ কৌশল আপনাকে সমর্থন করবে।', "moderate": 'আপনি কিছু মানসিক উত্থান-পতন অনুভব করেন;বেশিরভাগ সময় আপনি আবার আপনার ব্যালেন্স খুঁজে পেতে পারেন।', "low": 'আপনার মানসিক স্থিতিস্থাপকতা শক্তিশালী;আপনি চাপের মধ্যে শান্ত থাকুন এবং সহজেই অসুবিধাগুলি পরিচালনা করুন।'},
        },
        'skills': {
            'problem_solving': {"high": 'আপনি জটিল সমস্যা বিশ্লেষণ এবং ব্যবহারিক সমাধান তৈরিতে শক্তিশালী।', "moderate": 'আপনার সমস্যা সমাধানের পদ্ধতির বিকাশ ঘটছে;কাঠামোগত চিন্তা কৌশল আপনাকে সমর্থন করতে পারে।', "low": 'পদ্ধতিগত সমস্যা-সমাধান পদ্ধতি শেখা এই এলাকায় আপনার সম্ভাবনা আনলক করবে।'},
            'empathy': {"high": 'আপনার অন্যদের আবেগ বোঝার এবং সহানুভূতির সাথে সংযোগ করার একটি অসাধারণ ক্ষমতা রয়েছে।', "moderate": 'আপনার সহানুভূতি দক্ষতা বিকাশ করছে;সক্রিয় শ্রবণ অনুশীলন এই এলাকাকে শক্তিশালী করবে।', "low": 'অন্যদের দৃষ্টিভঙ্গি আরও অন্বেষণ করা আপনাকে আরও কার্যকর যোগাযোগকারী করে তুলবে।'},
            'organization': {"high": 'আপনার পরিকল্পনা এবং অগ্রাধিকার শক্তিশালী;আপনার সংগঠিত শৈলী আপনাকে দাঁড়াতে সাহায্য করে।', "moderate": 'আপনার সাংগঠনিক দক্ষতা যুক্তিসঙ্গত;টাইম ম্যানেজমেন্ট টুল ব্যবহার করে আপনাকে আরও শক্তিশালী করে তুলতে পারে।', "low": 'পদ্ধতিগত সাংগঠনিক অভ্যাস বিকাশ আপনার উত্পাদনশীলতা উল্লেখযোগ্যভাবে উন্নত করতে পারে।'},
            'learning_speed': {"high": 'আপনি নতুন জ্ঞান এবং দক্ষতার সাথে দ্রুত খাপ খাইয়ে নিচ্ছেন - পরিবর্তিত পরিবেশে একটি বড় সুবিধা।', "moderate": 'আপনার শেখার গতি যুক্তিসঙ্গত;বিভিন্ন কৌশল নিয়ে পরীক্ষা আপনার কার্যকারিতা বাড়াতে পারে।', "low": 'কাঠামোবদ্ধ পর্যালোচনা এবং অনুশীলন কৌশল এই এলাকায় আপনার শেখার প্রক্রিয়া সমর্থন করবে.'},
            'decision_making': {"high": 'সিদ্ধান্ত নেওয়ার পরিস্থিতিতে আপনি সিদ্ধান্তমূলক, দ্রুত পদক্ষেপ নিতে পারেন।', "moderate": 'আপনার সিদ্ধান্ত গ্রহণের দক্ষতা বিকাশ করছে;কাঠামোবদ্ধ কাঠামো কঠিন মুহূর্তে সাহায্য করে।', "low": 'ছোট সিদ্ধান্ত দিয়ে শুরু করা আপনার সিদ্ধান্ত গ্রহণের আস্থা তৈরি করার একটি কার্যকর উপায়।'},
        },
        'hr': {
            'leadership': {"high": 'আপনি দল পরিচালনায়, অন্যদের অনুপ্রাণিত করতে এবং নেতৃত্ব দেওয়ার ক্ষেত্রে শক্তিশালী।', "moderate": 'আপনার নেতৃত্বের যোগ্যতা আছে;ব্যবহারিক অভিজ্ঞতা দ্রুত এই দক্ষতা বিকাশ করবে।', "low": 'ইচ্ছাকৃতভাবে অনুশীলনের মাধ্যমে নেতৃত্বের দক্ষতা বিকাশ আপনার ক্যারিয়ারকে উল্লেখযোগ্যভাবে এগিয়ে নিতে পারে।'},
            'team_fit': {"high": 'আপনি সুরেলা দলগত কাজ, সহযোগিতা এবং সহায়কতার জন্য আলাদা।', "moderate": 'আপনার দলের ফিট ভাল;বিভিন্ন কাজের শৈলী বোঝা এটিকে আরও শক্তিশালী করবে।', "low": 'দলের গতিশীলতায় আরও সক্রিয় অংশগ্রহণ আপনার পেশাদার সম্পর্ককে শক্তিশালী করবে।'},
            'communication': {"high": 'আপনি স্পষ্ট, কার্যকরী এবং গঠনমূলক যোগাযোগে শক্তিশালী।', "moderate": 'আপনার যোগাযোগ শৈলী উন্নয়নশীল;বিভিন্ন দর্শকদের সাথে মানিয়ে নেওয়া আপনাকে একটি সুবিধা দেয়।', "low": 'পদ্ধতিগতভাবে যোগাযোগ দক্ষতা অনুশীলন এই এলাকায় দ্রুত অগ্রগতি তৈরি করবে।'},
            'stress_tolerance': {"high": 'আপনি চাপের মধ্যে আপনার সংযম বজায় রাখতে পারেন;পেশাদার স্থিতিস্থাপকতার ভিত্তি।', "moderate": 'আপনার চাপ মোকাবেলা করার ক্ষমতা যুক্তিসঙ্গত;স্থিতিস্থাপকতা-নির্মাণের কৌশলগুলি আপনাকে আরও শক্তিশালী করে তুলবে।', "low": 'দৈনন্দিন অনুশীলন দ্বারা সমর্থিত স্ট্রেস ম্যানেজমেন্ট কৌশলগুলি দ্রুত ফলাফল তৈরি করে।'},
            'motivation': {"high": 'আপনার অন্তর্নিহিত প্রেরণা উচ্চ;আপনি প্রতিশ্রুতি এবং আবেগ সঙ্গে আপনার লক্ষ্য যোগাযোগ.', "moderate": 'আপনার প্রেরণা পরিবর্তিত হয়;আপনার উদ্দেশ্যের সাথে সংযুক্ত থাকা একটি অবিচ্ছিন্ন শক্তির উত্স হতে পারে।', "low": 'অর্থপূর্ণ স্বল্পমেয়াদী লক্ষ্য নির্ধারণ করা আপনার অনুপ্রেরণাকে পুনরুজ্জীবিত করার একটি কার্যকর উপায়।'},
        },
        'career': {
            'analytical': {"high": 'বিশ্লেষণাত্মক চিন্তাভাবনা এবং ডেটা-কেন্দ্রিক কাজের পরিবেশের প্রতি আপনার একটি শক্তিশালী অভিযোজন রয়েছে।', "moderate": 'আপনার বিশ্লেষণাত্মক প্রবণতা আছে;কাঠামোগত সমস্যা-সমাধান অনুশীলন এই এলাকাকে শক্তিশালী করবে।', "low": 'পদ্ধতিগত বিশ্লেষণাত্মক দক্ষতার বিকাশ এই কর্মজীবনের ক্ষেত্রে আপনার বিকল্পগুলিকে প্রসারিত করবে।'},
            'creative': {"high": 'আপনি সৃজনশীল এবং উদ্ভাবনী কাজের পরিবেশে নিজেকে সেরাভাবে প্রকাশ করেন।', "moderate": 'আপনার সৃজনশীল প্রবণতা আছে;এই এলাকায় লালনপালন আপনার কর্মজীবন পরিপূর্ণতা বৃদ্ধি করতে পারে.', "low": 'কাঠামোগত এবং প্রযুক্তিগত কর্মজীবনের পথগুলি বর্তমানে সৃজনশীল-কেন্দ্রিক ভূমিকার চেয়ে বেশি সারিবদ্ধ বলে মনে হচ্ছে।'},
            'social': {"high": 'সাহায্য করা, শিক্ষা দেওয়া বা লোকেদের সাথে কাজ করা আপনাকে উজ্জীবিত করে।', "moderate": 'আপনি সামাজিক মিথস্ক্রিয়া জড়িত ভূমিকা আরামদায়ক;গভীর সংযোগ মান যোগ করতে পারেন.', "low": 'সামাজিক-কেন্দ্রিক কর্মজীবনের পথগুলি বর্তমানে আপনার জন্য একটি শক্তিশালী আগ্রহের ক্ষেত্র নয়।'},
            'entrepreneurial': {"high": 'নেতৃত্ব, প্ররোচনা এবং ঝুঁকি গ্রহণের প্রয়োজন উদ্যোক্তা ভূমিকার প্রতি আপনার একটি শক্তিশালী প্রবণতা রয়েছে।', "moderate": 'আপনার উদ্যোক্তা দৃষ্টিভঙ্গি বিকাশ করছে;সিদ্ধান্ত গ্রহণ এবং নেতৃত্বের অভিজ্ঞতা এটিকে ত্বরান্বিত করবে।', "low": 'দক্ষতা-কেন্দ্রিক কর্মজীবনের পথগুলি বর্তমানে উদ্যোক্তা ভূমিকার চেয়ে বেশি সারিবদ্ধ বলে মনে হচ্ছে।'},
            'managerial': {"high": 'পরিচালনা, সমন্বয় এবং সংগঠনের প্রয়োজন হয় এমন ভূমিকার জন্য আপনি উপযুক্ত।', "moderate": 'আপনার ব্যবস্থাপনাগত প্রবণতা বিকাশ করছে;দায়িত্ব গ্রহণ এই এলাকা লালনপালন করা হবে.', "low": 'কম ব্যবস্থাপকীয় চাপ সহ দক্ষতা-কেন্দ্রিক কর্মজীবনের পথগুলি এই মুহূর্তে আরও স্বাচ্ছন্দ্য বোধ করতে পারে।'},
            'technical': {"high": 'প্রযুক্তিগত এবং বিশেষ ক্ষেত্রগুলির প্রতি আপনার একটি শক্তিশালী আগ্রহ এবং অভিযোজন রয়েছে।', "moderate": 'আপনার প্রযুক্তিগত দক্ষতা উন্নয়নশীল;গভীর বিশেষীকরণ এই এলাকাকে শক্তিশালী করবে।', "low": 'মানুষ-কেন্দ্রিক কর্মজীবনের পথগুলি বর্তমানে প্রযুক্তিগত বিশেষজ্ঞের ভূমিকার চেয়ে বেশি সারিবদ্ধ বলে মনে হচ্ছে।'},
        },
        'vocation': {
            'realistic': {"high": 'ব্যবহারিক, হাতে-কলমে এবং প্রযুক্তিগত কাজের প্রতি আপনার প্রবল ঝোঁক রয়েছে।', "moderate": 'হাতে-কলমে কাজের প্রতি আপনার মাঝারি আগ্রহ আছে;এই এলাকায় চেষ্টা করে আপনি একটি পরিষ্কার ছবি দিতে হবে.', "low": 'ব্যবহারিক এবং প্রযুক্তিগত কার্যক্রম বর্তমানে আপনার শক্তিশালী আগ্রহের মধ্যে নেই।'},
            'investigative': {"high": 'গবেষণা, বিশ্লেষণ এবং ধারনা অন্বেষণ স্বাভাবিকভাবেই আপনাকে আকর্ষণ করে।', "moderate": 'আপনার অনুসন্ধানমূলক আগ্রহ আছে;এই এলাকায় জ্ঞানের গভীরতা এটিকে আরও শক্তিশালী করবে।', "low": 'গবেষণা এবং বিশ্লেষণ-কেন্দ্রিক কার্যকলাপ বর্তমানে আপনার অগ্রাধিকার আগ্রহের মধ্যে নেই।'},
            'artistic': {"high": 'সৃজনশীল অভিব্যক্তি, শিল্প এবং নান্দনিকতা প্রয়োজন এমন ক্রিয়াকলাপের প্রতি আপনার একটি শক্তিশালী প্রবণতা রয়েছে।', "moderate": 'আপনার শৈল্পিক প্রবণতা আছে;এই এলাকা লালন পরিপূর্ণতা এবং সত্যতা প্রদান করতে পারেন.', "low": 'শৈল্পিক এবং সৃজনশীল কার্যকলাপ বর্তমানে আপনার জন্য একটি শক্তিশালী আগ্রহের ক্ষেত্র নয়।'},
            'social': {"high": 'মানুষের সাথে থাকা, সাহায্য করা এবং শিক্ষা দেওয়া আপনাকে শক্তি জোগায়।', "moderate": 'সামাজিক কর্মকাণ্ডে আপনার মাঝারি আগ্রহ আছে;অর্থপূর্ণ সংযোগ তৈরি করা সন্তুষ্টি নিয়ে আসে।', "low": 'সামাজিক-কেন্দ্রিক ক্রিয়াকলাপগুলি বর্তমানে আপনার অগ্রাধিকারের আগ্রহের মধ্যে নেই।'},
            'enterprising': {"high": 'নেতৃত্ব, প্ররোচনা এবং প্রতিযোগিতার প্রয়োজন এমন ক্রিয়াকলাপে আপনি শক্তিশালী বোধ করেন।', "moderate": 'আপনার উদ্যোগী প্রবণতা আছে;দায়িত্ব অনুশীলন এবং সিদ্ধান্ত গ্রহণ এটিকে শক্তিশালী করে।', "low": 'প্রতিযোগিতামূলক এবং নেতৃত্ব-কেন্দ্রিক কার্যকলাপ বর্তমানে আপনার জন্য একটি শক্তিশালী আগ্রহের ক্ষেত্র নয়।'},
            'conventional': {"high": 'আপনি সংগঠিত, পদ্ধতিগত, এবং নিয়ম-সামঞ্জস্যপূর্ণ কাজের পরিবেশে শক্তিশালী।', "moderate": 'সংগঠন এবং কাঠামোতে আপনার মাঝারি আগ্রহ আছে;পদ্ধতিগত কাজ অনুশীলন এটি লালনপালন.', "low": 'কাঠামোবদ্ধ এবং প্রচলিত ক্রিয়াকলাপগুলি বর্তমানে আপনার জন্য একটি শক্তিশালী আগ্রহের ক্ষেত্র নয়।'},
        },
        'relationship': {
            'love_language': {"high": 'আপনি স্পষ্টভাবে আপনার ভালবাসার ভাষা প্রকাশ করেন এবং সম্পর্কের মধ্যে পারস্পরিক বোঝাপড়ার মূল্য দেন।', "moderate": 'আপনি আপনার ভালবাসার ভাষা পরিমিতভাবে প্রকাশ করুন;এখানে আরও খোলামেলা হওয়া আপনার সম্পর্ককে সমৃদ্ধ করতে পারে।', "low": 'মানসিক অভিব্যক্তি এবং প্রেমের ভাষা সম্পর্কে সচেতনতা বিকাশ আপনার সংযোগগুলিকে আরও গভীর করবে।'},
            'conflict_style': {"high": 'আপনি গঠনমূলক এবং স্বাস্থ্যকর উপায়ে দ্বন্দ্ব সমাধানে শক্তিশালী।', "moderate": 'আপনার দ্বন্দ্ব সমাধান শৈলী উন্নয়নশীল;আরো গঠনমূলক পদ্ধতির চেষ্টা সাহায্য করতে পারে.', "low": 'স্বাস্থ্যকর দ্বন্দ্ব সমাধানের কৌশলগুলি বিকাশ করা আপনার সম্পর্কের গুণমানকে উল্লেখযোগ্যভাবে উন্নত করবে।'},
            'intimacy_needs': {"high": 'আপনি স্পষ্টভাবে আবেগগত ঘনিষ্ঠতা এবং সংযোগের জন্য আপনার প্রয়োজনীয়তা বুঝতে.', "moderate": 'আপনার ঘনিষ্ঠতার চাহিদা সম্পর্কে আপনার মাঝারি সচেতনতা রয়েছে;আরও এই এলাকা অন্বেষণ মূল্যবান.', "low": 'আপনার মানসিক বন্ধন এবং ঘনিষ্ঠতার চাহিদা বোঝা আপনার সম্পর্ককে আরও পরিপূর্ণ করে তুলবে।'},
            'relationship_values': {"high": 'আপনার সম্পর্কের ক্ষেত্রে আপনি যা চান তার জন্য আপনার কাছে একটি স্পষ্ট মূল্য কাঠামো রয়েছে।', "moderate": 'আপনার সম্পর্কের মানগুলি আকার নিচ্ছে;এর প্রতিফলন আপনাকে স্বাস্থ্যকর সংযোগ তৈরি করতে সহায়তা করে।', "low": 'আপনার ব্যক্তিগত সম্পর্কের মানগুলি আবিষ্কার করা এবং স্পষ্ট করা গভীর বন্ধনের ভিত্তি তৈরি করে।'},
        },
        'attachment': {
            'anxiety': {"high": 'পরিত্যাগ সম্পর্কে উদ্বেগ বেশি;এই সচেতনতা নিরাপদ সংযুক্তি বিকাশের জন্য একটি শক্তিশালী সূচনা বিন্দু।', "moderate": 'সংযুক্তি উদ্বেগ মাঝারি;নিরাপদ সম্পর্ক অনুশীলন এই এলাকায় সমর্থন.', "low": 'আপনার পরিত্যাগ উদ্বেগ কম;আপনি সম্পর্কের মধ্যে নিরাপদ এবং সুষম সংযুক্তি দেখান।'},
            'avoidance': {"high": 'মানসিক ঘনিষ্ঠতা পরিহার লক্ষণীয়;এই প্যাটার্ন স্বীকৃতি গভীর বন্ধন দিকে প্রথম পদক্ষেপ.', "moderate": 'ঘনিষ্ঠতা পরিহার মধ্যম;আত্ম-সচেতনতা বাড়ার সাথে সাথে আপনি আরও উন্মুক্ত সংযোগ তৈরি করতে পারেন।', "low": 'মানসিক ঘনিষ্ঠতা আপনার পরিহার কম;খোলামেলাতা এবং সংযোগ সম্পর্কের মধ্যে স্বাচ্ছন্দ্য বোধ করে।'},
        },
        'grit': {
            'perseverance': {"high": 'আপনি যা শুরু করেছেন এবং বাধা সত্ত্বেও চালিয়ে যাচ্ছেন তা সম্পূর্ণ করতে আপনি শক্তিশালী।', "moderate": 'আপনার সংকল্প এবং দৃঢ়তা বিকাশ করছে;দীর্ঘমেয়াদী লক্ষ্যে প্রতিশ্রুতিবদ্ধ থাকা এটিকে শক্তিশালী করে।', "low": 'টেকসই অধ্যবসায় গড়ে তোলার জন্য স্বল্পমেয়াদী সাফল্য সংগ্রহ করা একটি কার্যকর কৌশল।'},
            'passion': {"high": 'আপনি আপনার দীর্ঘমেয়াদী লক্ষ্যগুলির প্রতি ধারাবাহিক আবেগ এবং আগ্রহ দেখান।', "moderate": 'লক্ষ্যগুলির জন্য আপনার আবেগ বিকাশ করছে;একটি অর্থপূর্ণ উদ্দেশ্যে সংযোগ এই শক্তি প্রসারিত.', "low": 'এমন আগ্রহগুলি আবিষ্কার করা যা সত্যিকার অর্থে আপনাকে জাগিয়ে তোলে আপনার আবেগ এবং অনুপ্রেরণাকে বাড়িয়ে তুলবে।'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'আপনি দৃঢ়ভাবে বিশ্বাস করেন যে প্রচেষ্টার মাধ্যমে ক্ষমতা এবং বুদ্ধি বিকাশ করা যেতে পারে।', "moderate": 'আপনার বৃদ্ধির মানসিকতা বিকাশ করছে;শেখার সুযোগ হিসাবে চ্যালেঞ্জগুলি দেখা এটিকে লালন করে।', "low": 'বিশ্বাস যে ক্ষমতা স্থির আছে;এই মানসিকতাকে প্রশ্ন করা আপনার বৃদ্ধিকে ত্বরান্বিত করবে।'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'আপনি আপনার জীবনের সাথে উচ্চ সন্তুষ্টির রিপোর্ট করেন এবং একটি সামগ্রিক ইতিবাচক মূল্যায়ন করেন।', "moderate": 'আপনার জীবনের সন্তুষ্টি মধ্যম;অর্থ-মূল্যের প্রান্তিককরণকে শক্তিশালী করা পরিপূর্ণতা বাড়ায়।', "low": 'জীবনের তৃপ্তি কম;আপনি কি পরিবর্তন করতে চান তা নিজেকে জিজ্ঞাসা করা একটি ভাল সূচনা পয়েন্ট।'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'আপনি সমবেদনা এবং বোঝার সাথে নিজেকে যোগাযোগ করুন;মনস্তাত্ত্বিক স্থিতিস্থাপকতার একটি শক্তিশালী উত্স।', "moderate": 'আপনার আত্ম-সহানুভূতি বিকাশ করছে;কঠিন মুহুর্তে বন্ধুর মতো নিজের সাথে কথা বলা এটিকে লালন করে।', "low": 'একটি কঠোর ভিতরের কণ্ঠস্বর বিশিষ্ট;আত্ম-সহানুভূতি অনুশীলনের বিকাশ আপনাকে সমর্থন করবে।'},
            'self_judgment': {"high": 'অতিরিক্ত আত্ম-সমালোচনা করার প্রবণতা বিদ্যমান;এই স্বীকৃতি পরিবর্তনের জন্য একটি শক্তিশালী শুরু বিন্দু.', "moderate": 'আত্মসমালোচনা মধ্যপন্থী;নিজের প্রতি সদয় হওয়া কখনও কখনও উপকার নিয়ে আসে।', "low": 'আপনি নিজের প্রতি একটি ভারসাম্যপূর্ণ এবং সদয় মনোভাব দেখান;স্ব-মূল্যায়নের একটি সুস্থ চিহ্ন।'},
            'common_humanity': {"high": 'আপনি বুঝতে পারেন যে আপনার সংগ্রামগুলি ভাগ করা মানুষের অভিজ্ঞতার অংশ, যা সান্ত্বনা নিয়ে আসে।', "moderate": 'আপনার সাধারণ মানবতার বোধের বিকাশ ঘটছে;মনে রাখা আপনি একা নন আপনাকে শক্তিশালী করে।', "low": 'অসুবিধা দেখা দিলে আপনি বিচ্ছিন্ন বোধ করতে পারেন;মনে রাখবেন এটি একটি খুব সাধারণ অভিজ্ঞতা।'},
            'isolation': {"high": 'কঠিন মুহূর্তে আপনি বিচ্ছিন্ন এবং একা বোধ করেন;সংযোগ এবং সমর্থন চাওয়া এই ভারসাম্য সাহায্য.', "moderate": 'বিচ্ছিন্নতার অনুভূতি সময়ে সময়ে উঠতে পারে;বিল্ডিং সংযোগ এটি ভারসাম্য সাহায্য করে।', "low": 'অসুবিধার সম্মুখীন হলে আপনি সংযুক্ত এবং সমর্থন বোধ করেন;মনস্তাত্ত্বিক স্বাস্থ্যের একটি গুরুত্বপূর্ণ চিহ্ন।'},
            'mindfulness': {"high": 'আপনি ভারসাম্য এবং সচেতনতার সাথে আপনার আবেগ পর্যবেক্ষণ করতে পারেন;একটি সুস্থ মনস্তাত্ত্বিক অবস্থান।', "moderate": 'আপনার মননশীল সচেতনতা বিকাশ করছে;সহজ ধ্যান অনুশীলন এই এলাকা শক্তিশালী হবে.', "low": 'আবেগ পর্যবেক্ষণের পরিবর্তে দমন করার প্রবণতা রয়েছে;মননশীলতা অনুশীলন সমর্থন প্রদান করতে পারে.'},
            'overidentification': {"high": 'নেতিবাচক আবেগ এবং চিন্তার উপর অতিরিক্ত ফোকাস করার প্রবণতা রয়েছে;মননশীলতা অনুশীলন এই চক্র ভঙ্গ.', "moderate": 'আপনি কখনও কখনও নেতিবাচক চিন্তা সঙ্গে অতিরিক্ত সনাক্ত করতে পারেন;ভারসাম্য কৌশল সাহায্য।', "low": 'আপনি নেতিবাচক চিন্তা থেকে একটি সুস্থ দূরত্ব বজায় রাখুন;মননশীল সচেতনতার একটি শক্তিশালী সূচক।'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'আপনার চ্যালেঞ্জিং কাজগুলি সম্পাদন করার ক্ষমতার উপর দৃঢ় বিশ্বাস রয়েছে।', "moderate": 'আপনার আত্ম-কার্যকারিতা বিশ্বাস বিকাশ করছে;ছোট সাফল্য সঞ্চয় এই আত্মবিশ্বাস বৃদ্ধি.', "low": 'আপনার নিজের ক্ষমতার উপর আস্থা কম;ছোট পদক্ষেপের মাধ্যমে সাফল্যের অভিজ্ঞতা তৈরি করতে সহায়তা করে।'},
        },
        'stress': {
            'perceived_stress': {"high": 'আপনি সম্প্রতি উচ্চ স্তরের চাপ অনুভব করছেন;স্ট্রেস ম্যানেজমেন্ট কৌশলগুলি এখন বিশেষভাবে গুরুত্বপূর্ণ।', "moderate": 'আপনি মাঝারি চাপ অনুভব করছেন;স্ট্রেস ট্রিগার চিহ্নিত করা এবং পরিচালনা করা সুবিধা নিয়ে আসে।', "low": 'আপনার চাপ উপলব্ধি স্তর কম;আপনার চ্যালেঞ্জ মোকাবেলা করার ক্ষমতা শক্তিশালী বলে মনে হয়।'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'আপনি সাধারণত ইতিবাচকভাবে আপনার চেহারা মূল্যায়ন;সুস্থ শরীরের ইমেজ একটি চিহ্ন।', "moderate": 'আপনার চেহারা মূল্যায়ন মিশ্র হয়;আপনার শরীরের কার্যকারিতা উপর ফোকাস দৃষ্টিকোণ বিস্তৃত.', "low": 'আপনার চেহারা নেতিবাচকভাবে মূল্যায়ন করার একটি প্রবণতা আছে;শরীরের নিশ্চিতকরণ অনুশীলন এখানে সহায়তা প্রদান করে।'},
            'body_satisfaction': {"high": 'আপনি সাধারণত আপনার শরীরের সাথে সন্তুষ্ট;সুস্থ স্ব-গ্রহণযোগ্যতার একটি চিহ্ন।', "moderate": 'আপনার শরীরের তৃপ্তি মাঝারি;আপনার শরীরের শক্তির উপর ফোকাস করা এই অঞ্চলকে লালন করে।', "low": 'আপনি আপনার শরীরের সাথে অসন্তুষ্ট বোধ করেন;স্ব-সহানুভূতি অনুশীলন এবং পেশাদার সমর্থন উপকারী হতে পারে।'},
        },
    },
    'id': {
        'personality': {
            'openness': {"high": 'Keingintahuan dan imajinasi Anda kuat;pengalaman dan ide baru secara alami menarik perhatian Anda.', "moderate": 'Anda menyeimbangkan rasa ingin tahu dengan kepraktisan, rasa ingin tahu di beberapa bidang dan konvensional di bidang lain.', "low": 'Anda lebih menyukai yang praktis dan familiar;rutinitas yang konsisten dan pendekatan yang terbukti terasa tepat untuk Anda.'},
            'conscientiousness': {"high": 'Anda disiplin, terorganisir, dan dapat diandalkan;Anda mengejar tujuan secara sistematis.', "moderate": 'Anda menyeimbangkan tanggung jawab dan fleksibilitas;rutinitas membangun akan semakin memperkuat hal ini.', "low": 'Anda memiliki gaya yang fleksibel dan spontan;mengembangkan kebiasaan perencanaan dapat meningkatkan efektivitas Anda.'},
            'extraversion': {"high": 'Energi sosial Anda tinggi;Anda mendapatkan kekuatan dari orang-orang dan memberikan energi kepada orang-orang di sekitar Anda.', "moderate": 'Anda menyeimbangkan waktu dengan orang lain dan waktu sendirian, merasa nyaman dalam kedua situasi tersebut.', "low": 'Sifat introvert Anda adalah aset alami untuk berpikir mendalam dan bekerja fokus.'},
            'agreeableness': {"high": 'Sifat Anda yang hangat dan kooperatif membangun kepercayaan dan keharmonisan dalam hubungan Anda.', "moderate": 'Anda menyeimbangkan sikap kerja sama dan kemandirian, pengertian namun tegas.', "low": 'Anda condong ke arah pemikiran independen dan kritis – kekuatan untuk analisis dan penilaian obyektif.'},
            'neuroticism': {"high": 'Reaksi emosional Anda bisa sangat kuat;manajemen stres dan strategi pengaturan diri akan mendukung Anda.', "moderate": 'Anda mengalami naik turunnya emosi;sering kali Anda dapat menemukan keseimbangan Anda kembali.', "low": 'Ketahanan emosional Anda kuat;Anda tetap tenang di bawah tekanan dan menangani kesulitan dengan mudah.'},
        },
        'skills': {
            'problem_solving': {"high": 'Anda kuat dalam menganalisis masalah kompleks dan menghasilkan solusi praktis.', "moderate": 'Pendekatan pemecahan masalah Anda berkembang;teknik berpikir terstruktur dapat mendukung Anda.', "low": 'Mempelajari metode pemecahan masalah yang sistematis akan membuka potensi Anda di bidang ini.'},
            'empathy': {"high": 'Anda memiliki kemampuan luar biasa untuk memahami emosi orang lain dan terhubung dengan empati.', "moderate": 'Keterampilan empati Anda berkembang;berlatih mendengarkan secara aktif akan memperkuat area ini.', "low": 'Mengeksplorasi lebih banyak sudut pandang orang lain akan membuat Anda menjadi komunikator yang lebih efektif.'},
            'organization': {"high": 'Perencanaan dan prioritas Anda kuat;gaya terorganisir Anda membantu Anda menonjol.', "moderate": 'Keterampilan organisasi Anda masuk akal;menggunakan alat manajemen waktu dapat membuat Anda semakin kuat.', "low": 'Mengembangkan kebiasaan organisasi yang sistematis dapat meningkatkan produktivitas Anda secara signifikan.'},
            'learning_speed': {"high": 'Anda beradaptasi dengan cepat terhadap pengetahuan dan keterampilan baru — sebuah keuntungan besar dalam perubahan lingkungan.', "moderate": 'Kecepatan belajar Anda masuk akal;bereksperimen dengan strategi yang berbeda dapat meningkatkan efektivitas Anda.', "low": 'Tinjauan terstruktur dan strategi praktik akan mendukung proses pembelajaran Anda di bidang ini.'},
            'decision_making': {"high": 'Anda dapat mengambil langkah cepat dan tegas dalam situasi pengambilan keputusan.', "moderate": 'Keterampilan pengambilan keputusan Anda berkembang;kerangka kerja terstruktur membantu di saat-saat sulit.', "low": 'Memulai dengan keputusan yang lebih kecil adalah cara yang efektif untuk membangun kepercayaan diri Anda dalam mengambil keputusan.'},
        },
        'hr': {
            'leadership': {"high": 'Anda kuat dalam mengarahkan tim, menginspirasi orang lain, dan memimpin.', "moderate": 'Anda memiliki bakat kepemimpinan;pengalaman praktis akan mengembangkan keterampilan ini dengan cepat.', "low": 'Mengembangkan keterampilan kepemimpinan secara sengaja melalui praktik dapat memajukan karier Anda secara signifikan.'},
            'team_fit': {"high": 'Anda menonjol karena kerja tim yang harmonis, kolaborasi, dan suka membantu.', "moderate": 'Kesesuaian tim Anda bagus;memahami gaya kerja yang berbeda akan memperkuat hal ini lebih jauh.', "low": 'Partisipasi yang lebih aktif dalam dinamika tim akan memperkuat hubungan profesional Anda.'},
            'communication': {"high": 'Anda kuat dalam komunikasi yang jelas, efektif, dan konstruktif.', "moderate": 'Gaya komunikasi Anda berkembang;beradaptasi dengan audiens yang berbeda memberi Anda keuntungan.', "low": 'Mempraktikkan keterampilan komunikasi secara sistematis akan menghasilkan kemajuan pesat dalam bidang ini.'},
            'stress_tolerance': {"high": 'Anda dapat menjaga ketenangan Anda di bawah tekanan;landasan ketahanan profesional.', "moderate": 'Kapasitas Anda dalam mengatasi stres masuk akal;teknik membangun ketahanan akan membuat Anda semakin kuat.', "low": 'Mengembangkan strategi manajemen stres, didukung oleh praktik sehari-hari, membuahkan hasil dengan cepat.'},
            'motivation': {"high": 'Motivasi intrinsik Anda tinggi;Anda mendekati tujuan Anda dengan komitmen dan semangat.', "moderate": 'Motivasi Anda bervariasi;tetap terhubung dengan tujuan Anda dapat menjadi sumber energi yang berkelanjutan.', "low": 'Menetapkan tujuan jangka pendek yang bermakna adalah cara efektif untuk menghidupkan kembali motivasi Anda.'},
        },
        'career': {
            'analytical': {"high": 'Anda memiliki orientasi yang kuat terhadap pemikiran analitis dan lingkungan kerja yang berfokus pada data.', "moderate": 'Anda memiliki kecenderungan analitis;praktik pemecahan masalah yang terstruktur akan memperkuat bidang ini.', "low": 'Mengembangkan keterampilan analitis yang sistematis akan memperluas pilihan Anda di bidang karir ini.'},
            'creative': {"high": 'Anda mengekspresikan diri Anda yang terbaik dalam lingkungan kerja yang kreatif dan inovatif.', "moderate": 'Anda memiliki kecenderungan kreatif;memelihara bidang ini dapat meningkatkan kepuasan karier Anda.', "low": 'Jalur karier struktural dan teknis saat ini tampak lebih selaras dibandingkan peran yang berfokus pada kreatif.'},
            'social': {"high": 'Membantu, mengajar, atau bekerja dengan orang lain memberi energi pada Anda.', "moderate": 'Anda merasa nyaman dalam peran yang melibatkan interaksi sosial;koneksi yang lebih dalam dapat menambah nilai.', "low": 'Jalur karier yang berfokus pada sosial saat ini bukan bidang minat yang kuat bagi Anda.'},
            'entrepreneurial': {"high": 'Anda memiliki kecenderungan kuat terhadap peran kewirausahaan yang membutuhkan kepemimpinan, persuasi, dan pengambilan risiko.', "moderate": 'Perspektif kewirausahaan Anda berkembang;pengambilan keputusan dan pengalaman kepemimpinan akan mempercepat hal ini.', "low": 'Jalur karir yang berfokus pada keahlian saat ini tampaknya lebih selaras dibandingkan peran kewirausahaan.'},
            'managerial': {"high": 'Anda sangat cocok untuk peran yang memerlukan manajemen, koordinasi, dan pengorganisasian.', "moderate": 'Kecenderungan manajerial Anda sedang berkembang;mengambil tanggung jawab akan memelihara bidang ini.', "low": 'Jalur karier yang berfokus pada keahlian dengan tekanan manajerial yang lebih sedikit mungkin terasa lebih nyaman saat ini.'},
            'technical': {"high": 'Anda memiliki minat dan orientasi yang kuat terhadap bidang teknis dan khusus.', "moderate": 'Keterampilan teknis Anda berkembang;spesialisasi yang mendalam akan memperkuat bidang ini.', "low": 'Jalur karier yang berfokus pada manusia saat ini tampak lebih selaras dibandingkan peran spesialis teknis.'},
        },
        'vocation': {
            'realistic': {"high": 'Anda memiliki kecenderungan kuat terhadap pekerjaan praktis, langsung, dan teknis.', "moderate": 'Anda memiliki minat yang moderat terhadap pekerjaan langsung;mencoba area ini akan memberi Anda gambaran yang lebih jelas.', "low": 'Kegiatan praktis dan teknis saat ini bukan merupakan minat utama Anda.'},
            'investigative': {"high": 'Meneliti, menganalisis, dan mengeksplorasi ide secara alami menarik perhatian Anda.', "moderate": 'Anda memiliki minat investigasi;memperdalam pengetahuan di bidang ini akan semakin memperkuatnya.', "low": 'Aktivitas yang berfokus pada penelitian dan analisis saat ini bukan merupakan prioritas Anda.'},
            'artistic': {"high": 'Anda memiliki kecenderungan kuat terhadap aktivitas yang membutuhkan ekspresi kreatif, seni, dan estetika.', "moderate": 'Anda memiliki kecenderungan artistik;memelihara area ini dapat memberikan kepuasan dan keaslian.', "low": 'Aktivitas artistik dan kreatif saat ini bukanlah bidang yang Anda minati.'},
            'social': {"high": 'Berada bersama orang lain, membantu, dan mengajar memberi energi pada Anda.', "moderate": 'Anda memiliki minat yang moderat terhadap aktivitas sosial;membangun koneksi yang bermakna membawa kepuasan.', "low": 'Aktivitas yang berfokus pada sosial saat ini bukan merupakan prioritas Anda.'},
            'enterprising': {"high": 'Anda merasa paling kuat dalam aktivitas yang membutuhkan kepemimpinan, persuasi, dan kompetisi.', "moderate": 'Anda memiliki kecenderungan giat;mempraktikkan tanggung jawab dan pengambilan keputusan memperkuat hal ini.', "low": 'Aktivitas yang kompetitif dan berfokus pada kepemimpinan saat ini bukan merupakan bidang minat yang kuat bagi Anda.'},
            'conventional': {"high": 'Anda kuat dalam lingkungan kerja yang terorganisir, sistematis, dan konsisten dengan aturan.', "moderate": 'Anda memiliki minat yang moderat terhadap organisasi dan struktur;praktik kerja yang sistematis memupuk hal ini.', "low": 'Aktivitas terstruktur dan konvensional saat ini bukan merupakan bidang minat yang kuat bagi Anda.'},
        },
        'relationship': {
            'love_language': {"high": 'Anda dengan jelas mengekspresikan bahasa cinta Anda dan menghargai saling pengertian dalam hubungan.', "moderate": 'Anda mengekspresikan bahasa cinta Anda secara moderat;bersikap lebih terbuka di sini dapat memperkaya hubungan Anda.', "low": 'Mengembangkan kesadaran akan ekspresi emosional dan bahasa cinta akan memperdalam hubungan Anda.'},
            'conflict_style': {"high": 'Anda kuat dalam menyelesaikan konflik dengan cara yang konstruktif dan sehat.', "moderate": 'Gaya resolusi konflik Anda sedang berkembang;mencoba pendekatan yang lebih konstruktif dapat membantu.', "low": 'Mengembangkan strategi penyelesaian konflik yang sehat akan meningkatkan kualitas hubungan Anda secara signifikan.'},
            'intimacy_needs': {"high": 'Anda memahami dengan jelas kebutuhan Anda akan kedekatan dan hubungan emosional.', "moderate": 'Anda memiliki kesadaran yang moderat akan kebutuhan keintiman Anda;menjelajahi area ini lebih jauh sangatlah berharga.', "low": 'Memahami kebutuhan ikatan emosional dan keintiman Anda akan membuat hubungan Anda lebih memuaskan.'},
            'relationship_values': {"high": 'Anda memiliki kerangka nilai yang jelas tentang apa yang Anda inginkan dalam hubungan Anda.', "moderate": 'Nilai-nilai hubungan Anda mulai terbentuk;merenungkan hal ini membantu Anda membangun koneksi yang lebih sehat.', "low": 'Menemukan dan memperjelas nilai-nilai hubungan pribadi Anda akan meletakkan dasar bagi ikatan yang lebih dalam.'},
        },
        'attachment': {
            'anxiety': {"high": 'Kecemasan akan pengabaian sangatlah tinggi;kesadaran ini adalah titik awal yang kuat untuk mengembangkan keterikatan aman.', "moderate": 'Kecemasan terhadap keterikatan bersifat sedang;praktik hubungan yang aman mendukung bidang ini.', "low": 'Kecemasan Anda akan pengabaian rendah;Anda menunjukkan keterikatan yang aman dan seimbang dalam hubungan.'},
            'avoidance': {"high": 'Penghindaran kedekatan emosional terlihat jelas;mengenali pola ini adalah langkah pertama menuju ikatan yang lebih dalam.', "moderate": 'Menghindari kedekatan adalah hal yang moderat;seiring tumbuhnya kesadaran diri, Anda dapat membangun koneksi yang lebih terbuka.', "low": 'Penghindaran Anda terhadap kedekatan emosional rendah;keterbukaan dan koneksi merasa nyaman dalam hubungan.'},
        },
        'grit': {
            'perseverance': {"high": 'Anda kuat dalam menyelesaikan apa yang Anda mulai dan melanjutkannya meskipun ada rintangan.', "moderate": 'Tekad dan ketabahan Anda berkembang;tetap berkomitmen pada tujuan jangka panjang memperkuat hal ini.', "low": 'Mengumpulkan keberhasilan jangka pendek adalah strategi efektif untuk membangun ketekunan yang berkelanjutan.'},
            'passion': {"high": 'Anda menunjukkan semangat dan minat yang konsisten terhadap tujuan jangka panjang Anda.', "moderate": 'Semangat Anda terhadap tujuan sedang berkembang;menghubungkan ke tujuan yang bermakna memperkuat energi ini.', "low": 'Menemukan minat yang benar-benar membuat Anda bersemangat akan menambah semangat dan motivasi Anda.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'Anda sangat yakin bahwa kemampuan dan kecerdasan dapat dikembangkan melalui usaha.', "moderate": 'Pola pikir berkembang Anda sedang berkembang;melihat tantangan sebagai kesempatan belajar memupuk hal ini.', "low": 'Keyakinan bahwa kemampuan itu tetap terus berlanjut;mempertanyakan pola pikir ini akan mempercepat pertumbuhan Anda.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'Anda melaporkan kepuasan yang tinggi terhadap hidup Anda dan membuat penilaian positif secara keseluruhan.', "moderate": 'Kepuasan hidup Anda sedang;memperkuat keselarasan makna-nilai meningkatkan pemenuhan.', "low": 'Kepuasan hidup rendah;bertanya pada diri sendiri apa yang ingin Anda ubah adalah titik awal yang baik.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'Anda mendekati diri Anda sendiri dengan kasih sayang dan pengertian;sumber ketahanan psikologis yang kuat.', "moderate": 'Rasa welas asih Anda berkembang;berbicara kepada diri sendiri seperti seorang teman di saat-saat sulit memupuk hal ini.', "low": 'Suara hati yang kasar terdengar jelas;mengembangkan praktik belas kasihan diri akan mendukung Anda.'},
            'self_judgment': {"high": 'Ada kecenderungan untuk terlalu kritis terhadap diri sendiri;menyadari bahwa ini adalah titik awal yang kuat untuk perubahan.', "moderate": 'Kritik terhadap diri sendiri bersifat moderat;bersikap lebih baik pada diri sendiri terkadang membawa manfaat.', "low": 'Anda menunjukkan sikap yang seimbang dan baik terhadap diri sendiri;tanda evaluasi diri yang sehat.'},
            'common_humanity': {"high": 'Anda memahami bahwa perjuangan Anda adalah bagian dari pengalaman bersama manusia, yang membawa kenyamanan.', "moderate": 'Rasa kemanusiaan Anda sedang berkembang;mengingat Anda tidak sendirian menguatkan Anda.', "low": 'Anda mungkin merasa terisolasi ketika kesulitan muncul;ingat ini adalah pengalaman yang sangat umum.'},
            'isolation': {"high": 'Anda merasa terisolasi dan sendirian di saat-saat sulit;mencari koneksi dan dukungan membantu menyeimbangkan hal ini.', "moderate": 'Perasaan terisolasi bisa muncul dari waktu ke waktu;membangun koneksi membantu menyeimbangkan hal ini.', "low": 'Anda merasa terhubung dan didukung ketika menghadapi kesulitan;tanda penting kesehatan psikologis.'},
            'mindfulness': {"high": 'Anda dapat mengamati emosi Anda dengan keseimbangan dan kesadaran;sikap psikologis yang sehat.', "moderate": 'Kesadaran penuh perhatian Anda sedang berkembang;praktik meditasi sederhana akan memperkuat area ini.', "low": 'Ada kecenderungan untuk menekan daripada mengamati emosi;praktik mindfulness dapat memberikan dukungan.'},
            'overidentification': {"high": 'Ada kecenderungan untuk terlalu fokus pada emosi dan pikiran negatif;praktik kesadaran memutus siklus ini.', "moderate": 'Terkadang Anda bisa mengidentifikasi diri Anda secara berlebihan dengan pikiran negatif;strategi keseimbangan membantu.', "low": 'Anda menjaga jarak yang sehat dari pikiran negatif;indikator kuat dari kesadaran penuh.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'Anda memiliki keyakinan kuat pada kemampuan Anda untuk menyelesaikan tugas-tugas yang menantang.', "moderate": 'Keyakinan efikasi diri Anda berkembang;mengumpulkan keberhasilan kecil meningkatkan kepercayaan diri ini.', "low": 'Keyakinan terhadap kemampuan sendiri rendah;membangun pengalaman sukses melalui langkah-langkah kecil membantu.'},
        },
        'stress': {
            'perceived_stress': {"high": 'Anda merasakan tingkat stres yang tinggi akhir-akhir ini;strategi manajemen stres sangat penting saat ini.', "moderate": 'Anda mengalami stres sedang;mengidentifikasi dan mengelola pemicu stres membawa manfaat.', "low": 'Tingkat persepsi stres Anda rendah;kapasitas Anda untuk menangani tantangan tampak kuat.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'Anda menilai penampilan Anda secara umum secara positif;tanda citra tubuh yang sehat.', "moderate": 'Evaluasi penampilan Anda beragam;berfokus pada fungsi tubuh Anda memperluas perspektif.', "low": 'Ada kecenderungan menilai penampilan Anda secara negatif;praktik penegasan tubuh memberikan dukungan di sini.'},
            'body_satisfaction': {"high": 'Anda umumnya puas dengan tubuh Anda;tanda penerimaan diri yang sehat.', "moderate": 'Kepuasan tubuh Anda sedang;berfokus pada kekuatan tubuh Anda akan memupuk area ini.', "low": 'Anda merasa tidak puas dengan tubuh Anda;praktik belas kasihan diri dan dukungan profesional mungkin bermanfaat.'},
        },
    },
    'ur': {
        'personality': {
            'openness': {"high": 'آپ کا تجسس اور تخیل مضبوط ہے۔نئے تجربات اور خیالات قدرتی طور پر آپ کو اپنی طرف متوجہ کرتے ہیں۔', "moderate": 'آپ تجسس کو عملییت کے ساتھ متوازن رکھتے ہیں، کچھ علاقوں میں متجسس اور دوسروں میں روایتی۔', "low": 'آپ عملی اور واقف کو ترجیح دیتے ہیں؛مستقل معمولات اور ثابت شدہ نقطہ نظر آپ کے لیے صحیح محسوس کرتے ہیں۔'},
            'conscientiousness': {"high": 'آپ نظم و ضبط، منظم، اور قابل اعتماد ہیں؛آپ منظم طریقے سے مقاصد کا تعاقب کرتے ہیں۔', "moderate": 'آپ ذمہ داری اور لچک میں توازن رکھتے ہیں۔معمولات کی تعمیر اس کو مزید مضبوط کرے گی۔', "low": 'آپ کے پاس لچکدار، بے ساختہ انداز ہے۔منصوبہ بندی کی عادتیں آپ کی تاثیر کو بہتر بنا سکتی ہیں۔'},
            'extraversion': {"high": 'آپ کی سماجی توانائی زیادہ ہے؛آپ لوگوں سے طاقت حاصل کرتے ہیں اور اپنے آس پاس کے لوگوں میں توانائی لاتے ہیں۔', "moderate": 'آپ دوسروں کے ساتھ وقت اور اکیلے وقت میں توازن رکھتے ہیں، دونوں ترتیبات میں آرام دہ اور پرسکون۔', "low": 'آپ کی انٹروورٹڈ فطرت گہری سوچ اور مرکوز کام کے لیے قدرتی اثاثہ ہے۔'},
            'agreeableness': {"high": 'آپ کی گرمجوشی، تعاون پر مبنی فطرت آپ کے تعلقات میں اعتماد اور ہم آہنگی پیدا کرتی ہے۔', "moderate": 'آپ تعاون اور آزادی میں توازن رکھتے ہیں، لیکن خود پر زور دیتے ہوئے سمجھتے ہیں۔', "low": 'آپ آزاد، تنقیدی سوچ کی طرف جھکاؤ رکھتے ہیں — تجزیہ اور معروضی فیصلے کی طاقت۔'},
            'neuroticism': {"high": 'آپ کے جذباتی ردعمل شدید ہو سکتے ہیں۔تناؤ کا انتظام اور خود کو منظم کرنے کی حکمت عملی آپ کی مدد کریں گی۔', "moderate": 'آپ کو کچھ جذباتی اتار چڑھاؤ کا سامنا کرنا پڑتا ہے۔زیادہ تر وقت آپ اپنا بیلنس دوبارہ تلاش کر سکتے ہیں۔', "low": 'آپ کی جذباتی لچک مضبوط ہے؛آپ دباؤ میں پرسکون رہتے ہیں اور آسانی کے ساتھ مشکلات کو سنبھالتے ہیں۔'},
        },
        'skills': {
            'problem_solving': {"high": 'آپ پیچیدہ مسائل کا تجزیہ کرنے اور عملی حل پیدا کرنے میں مضبوط ہیں۔', "moderate": 'آپ کا مسئلہ حل کرنے کا طریقہ ترقی کر رہا ہے۔ساختی سوچ کی تکنیک آپ کی مدد کر سکتی ہے۔', "low": 'مسئلہ حل کرنے کے منظم طریقے سیکھنا اس علاقے میں آپ کی صلاحیت کو کھول دے گا۔'},
            'empathy': {"high": 'آپ میں دوسروں کے جذبات کو سمجھنے اور ہمدردی سے جڑنے کی قابل ذکر صلاحیت ہے۔', "moderate": 'آپ کی ہمدردی کی صلاحیتیں ترقی کر رہی ہیں۔فعال سننے کی مشق کرنے سے اس علاقے کو تقویت ملے گی۔', "low": 'دوسروں کے نقطہ نظر کو مزید دریافت کرنا آپ کو زیادہ موثر رابطہ کار بنا دے گا۔'},
            'organization': {"high": 'آپ کی منصوبہ بندی اور ترجیح مضبوط ہے۔آپ کا منظم انداز آپ کو نمایاں کرنے میں مدد کرتا ہے۔', "moderate": 'آپ کی تنظیمی مہارت معقول ہے؛ٹائم مینجمنٹ ٹولز کا استعمال آپ کو مزید مضبوط بنا سکتا ہے۔', "low": 'منظم تنظیمی عادات کو فروغ دینا آپ کی پیداواری صلاحیت کو نمایاں طور پر بہتر بنا سکتا ہے۔'},
            'learning_speed': {"high": 'آپ نئے علم اور مہارتوں کے ساتھ تیزی سے ڈھل جاتے ہیں - بدلتے ہوئے ماحول میں ایک بڑا فائدہ۔', "moderate": 'آپ کی سیکھنے کی رفتار معقول ہے۔مختلف حکمت عملیوں کے ساتھ تجربہ کرنا آپ کی تاثیر کو بڑھا سکتا ہے۔', "low": 'تشکیل شدہ جائزہ اور مشق کی حکمت عملی اس علاقے میں آپ کے سیکھنے کے عمل کی حمایت کریں گی۔'},
            'decision_making': {"high": 'آپ فیصلہ سازی کے حالات میں فیصلہ کن، فوری اقدامات کر سکتے ہیں۔', "moderate": 'آپ کی فیصلہ سازی کی صلاحیتیں ترقی کر رہی ہیں۔منظم فریم ورک مشکل لمحات میں مدد کرتے ہیں۔', "low": 'چھوٹے فیصلوں سے شروع کرنا آپ کا فیصلہ سازی کا اعتماد بڑھانے کا ایک مؤثر طریقہ ہے۔'},
        },
        'hr': {
            'leadership': {"high": 'آپ ٹیموں کو ہدایت دینے، دوسروں کو متاثر کرنے اور قیادت کرنے میں مضبوط ہیں۔', "moderate": 'آپ میں قائدانہ صلاحیت ہے؛عملی تجربات ان مہارتوں کو تیزی سے تیار کریں گے۔', "low": 'جان بوجھ کر پریکٹس کے ذریعے قائدانہ صلاحیتوں کو فروغ دینا آپ کے کیریئر کو نمایاں طور پر آگے بڑھا سکتا ہے۔'},
            'team_fit': {"high": 'آپ ہم آہنگ ٹیم ورک، تعاون اور مدد کے لیے نمایاں ہیں۔', "moderate": 'آپ کی ٹیم اچھی ہے؛کام کے مختلف انداز کو سمجھنے سے اس کو مزید تقویت ملے گی۔', "low": 'ٹیم کی حرکیات میں زیادہ فعال شرکت آپ کے پیشہ ورانہ تعلقات کو مضبوط کرے گی۔'},
            'communication': {"high": 'آپ واضح، موثر اور تعمیری مواصلت میں مضبوط ہیں۔', "moderate": 'آپ کا مواصلاتی انداز ترقی کر رہا ہے۔مختلف سامعین کے مطابق ڈھالنا آپ کو ایک فائدہ دیتا ہے۔', "low": 'مواصلاتی مہارتوں کو منظم طریقے سے مشق کرنے سے اس علاقے میں تیزی سے ترقی ہوگی۔'},
            'stress_tolerance': {"high": 'آپ دباؤ میں اپنا سکون برقرار رکھ سکتے ہیں۔پیشہ ورانہ لچک کا سنگ بنیاد۔', "moderate": 'آپ کی کشیدگی سے نمٹنے کی صلاحیت معقول ہے؛لچک پیدا کرنے کی تکنیکیں آپ کو مزید مضبوط بنائیں گی۔', "low": 'تناؤ کے انتظام کی حکمت عملیوں کو تیار کرنا، جو روزمرہ کے طریقوں سے تعاون کرتا ہے، تیزی سے نتائج پیدا کرتا ہے۔'},
            'motivation': {"high": 'آپ کی اندرونی حوصلہ افزائی زیادہ ہے؛آپ عزم اور جذبے کے ساتھ اپنے مقاصد تک پہنچتے ہیں۔', "moderate": 'آپ کی حوصلہ افزائی مختلف ہوتی ہے؛اپنے مقصد سے جڑے رہنا ایک مسلسل توانائی کا ذریعہ ہو سکتا ہے۔', "low": 'معنی خیز قلیل مدتی اہداف کا تعین آپ کی حوصلہ افزائی کا ایک مؤثر طریقہ ہے۔'},
        },
        'career': {
            'analytical': {"high": 'آپ کا تجزیاتی سوچ اور ڈیٹا پر مبنی کام کے ماحول کی طرف مضبوط رجحان ہے۔', "moderate": 'آپ کے تجزیاتی رجحانات ہیں؛تشکیل شدہ مسئلہ حل کرنے کی مشق اس علاقے کو مضبوط کرے گی۔', "low": 'منظم تجزیاتی مہارتوں کو تیار کرنا اس کیریئر کے علاقے میں آپ کے اختیارات کو بڑھا دے گا۔'},
            'creative': {"high": 'آپ تخلیقی اور اختراعی کام کے ماحول میں اپنا بہترین اظہار کرتے ہیں۔', "moderate": 'آپ کے تخلیقی رجحانات ہیں؛اس علاقے کی پرورش آپ کے کیریئر کی تکمیل کو بڑھا سکتی ہے۔', "low": 'ساختی اور تکنیکی کیریئر کے راستے فی الحال تخلیقی توجہ مرکوز کرداروں سے زیادہ منسلک نظر آتے ہیں۔'},
            'social': {"high": 'لوگوں کی مدد کرنا، سکھانا یا ان کے ساتھ کام کرنا آپ کو توانائی بخشتا ہے۔', "moderate": 'آپ سماجی تعامل میں شامل کرداروں میں آرام دہ ہیں۔گہرے کنکشن قدر میں اضافہ کر سکتے ہیں۔', "low": 'سماجی توجہ مرکوز کیریئر کے راستے فی الحال آپ کے لئے ایک مضبوط دلچسپی کا علاقہ نہیں ہے.'},
            'entrepreneurial': {"high": 'آپ کا کاروباری کرداروں کی طرف مضبوط رجحان ہے جس میں قیادت، قائل اور خطرہ مول لینے کی ضرورت ہوتی ہے۔', "moderate": 'آپ کا کاروباری نقطہ نظر ترقی کر رہا ہے؛فیصلہ سازی اور قیادت کا تجربہ اس کو تیز کرے گا۔', "low": 'مہارت پر مبنی کیریئر کے راستے فی الحال کاروباری کرداروں کے مقابلے میں زیادہ منسلک نظر آتے ہیں۔'},
            'managerial': {"high": 'آپ ان کرداروں کے لیے موزوں ہیں جن کے لیے انتظام، ہم آہنگی اور تنظیم کی ضرورت ہوتی ہے۔', "moderate": 'آپ کے انتظامی رجحانات ترقی کر رہے ہیں۔ذمہ داری لینے سے اس علاقے کی پرورش ہوگی۔', "low": 'کم انتظامی دباؤ کے ساتھ مہارت پر مبنی کیریئر کے راستے ابھی زیادہ آرام دہ محسوس کر سکتے ہیں۔'},
            'technical': {"high": 'آپ کی تکنیکی اور خصوصی شعبوں کی طرف گہری دلچسپی اور واقفیت ہے۔', "moderate": 'آپ کی تکنیکی مہارتیں ترقی کر رہی ہیں۔گہری مہارت اس علاقے کو مضبوط کرے گی۔', "low": 'لوگوں پر مرکوز کیریئر کے راستے فی الحال تکنیکی ماہر کے کرداروں کے مقابلے میں زیادہ منسلک نظر آتے ہیں۔'},
        },
        'vocation': {
            'realistic': {"high": 'آپ کا عملی، ہینڈ آن، اور تکنیکی کام کی طرف مضبوط جھکاؤ ہے۔', "moderate": 'آپ کو ہاتھ سے کام کرنے میں اعتدال پسند دلچسپی ہے؛اس علاقے کو آزمانے سے آپ کو ایک واضح تصویر ملے گی۔', "low": 'عملی اور تکنیکی سرگرمیاں فی الحال آپ کی مضبوط دلچسپیوں میں شامل نہیں ہیں۔'},
            'investigative': {"high": 'تحقیق، تجزیہ اور خیالات کی تلاش قدرتی طور پر آپ کو اپنی طرف متوجہ کرتی ہے۔', "moderate": 'آپ کو تفتیشی دلچسپی ہے؛اس علاقے میں علم کو گہرا کرنے سے اسے مزید تقویت ملے گی۔', "low": 'تحقیق اور تجزیہ پر مرکوز سرگرمیاں فی الحال آپ کی ترجیحی دلچسپیوں میں شامل نہیں ہیں۔'},
            'artistic': {"high": 'تخلیقی اظہار، فن اور جمالیات کی ضرورت والی سرگرمیوں کی طرف آپ کا جھکاؤ مضبوط ہے۔', "moderate": 'آپ کے فنکارانہ رجحانات ہیں؛اس علاقے کی پرورش تکمیل اور صداقت فراہم کر سکتی ہے۔', "low": 'فنکارانہ اور تخلیقی سرگرمیاں فی الحال آپ کے لیے ایک مضبوط دلچسپی کا علاقہ نہیں ہے۔'},
            'social': {"high": 'لوگوں کے ساتھ رہنا، مدد کرنا اور سکھانا آپ کو توانائی بخشتا ہے۔', "moderate": 'آپ کو سماجی سرگرمیوں میں اعتدال پسند دلچسپی ہے؛بامعنی روابط استوار کرنے سے اطمینان ہوتا ہے۔', "low": 'سماجی مرکوز سرگرمیاں فی الحال آپ کی ترجیحی دلچسپیوں میں شامل نہیں ہیں۔'},
            'enterprising': {"high": 'آپ ان سرگرمیوں میں مضبوط محسوس کرتے ہیں جن میں قیادت، قائل اور مقابلے کی ضرورت ہوتی ہے۔', "moderate": 'آپ میں کاروباری رجحانات ہیں؛ذمہ داری اور فیصلہ سازی کی مشق اس کو مضبوط کرتی ہے۔', "low": 'مسابقتی اور قیادت پر مرکوز سرگرمیاں فی الحال آپ کے لیے ایک مضبوط دلچسپی کا علاقہ نہیں ہے۔'},
            'conventional': {"high": 'آپ منظم، منظم، اور اصول کے مطابق کام کے ماحول میں مضبوط ہیں۔', "moderate": 'آپ کو تنظیم اور ساخت میں اعتدال پسند دلچسپی ہے؛منظم کام کی مشق اس کی پرورش کرتی ہے۔', "low": 'ساختی اور روایتی سرگرمیاں فی الحال آپ کے لیے ایک مضبوط دلچسپی کا علاقہ نہیں ہے۔'},
        },
        'relationship': {
            'love_language': {"high": 'آپ واضح طور پر اپنی محبت کا اظہار کرتے ہیں اور رشتوں میں باہمی افہام و تفہیم کی قدر کرتے ہیں۔', "moderate": 'آپ اپنی محبت کا اظہار اعتدال سے کرتے ہیں۔یہاں زیادہ کھلا رہنا آپ کے تعلقات کو بہتر بنا سکتا ہے۔', "low": 'جذباتی اظہار اور محبت کی زبانوں کے بارے میں آگاہی پیدا کرنے سے آپ کے روابط مزید گہرے ہوں گے۔'},
            'conflict_style': {"high": 'آپ تعمیری اور صحت مند طریقوں سے تنازعات کو حل کرنے میں مضبوط ہیں۔', "moderate": 'آپ کا تنازعہ حل کرنے کا انداز ترقی کر رہا ہے۔مزید تعمیری طریقوں کی کوشش کرنے سے مدد مل سکتی ہے۔', "low": 'صحت مند تنازعات کے حل کی حکمت عملیوں کو تیار کرنا آپ کے تعلقات کے معیار کو نمایاں طور پر بہتر بنائے گا۔'},
            'intimacy_needs': {"high": 'آپ جذباتی قربت اور تعلق کی اپنی ضروریات کو واضح طور پر سمجھتے ہیں۔', "moderate": 'آپ کو اپنی قربت کی ضروریات کے بارے میں اعتدال پسند آگاہی ہے؛اس علاقے کو مزید دریافت کرنا قابل قدر ہے۔', "low": 'آپ کے جذباتی بندھن اور قربت کی ضروریات کو سمجھنا آپ کے تعلقات کو مزید پورا کرے گا۔'},
            'relationship_values': {"high": 'آپ اپنے تعلقات میں جو چاہتے ہیں اس کے لیے آپ کے پاس واضح قدر کا فریم ورک ہے۔', "moderate": 'آپ کے تعلقات کی قدریں شکل اختیار کر رہی ہیں۔اس پر غور کرنے سے آپ کو صحت مند روابط استوار کرنے میں مدد ملتی ہے۔', "low": 'اپنے ذاتی تعلقات کی اقدار کو دریافت کرنا اور واضح کرنا گہرے بندھنوں کی بنیاد رکھتا ہے۔'},
        },
        'attachment': {
            'anxiety': {"high": 'ترک کرنے کے بارے میں تشویش زیادہ ہے؛یہ آگاہی محفوظ اٹیچمنٹ کو فروغ دینے کے لیے ایک مضبوط نقطہ آغاز ہے۔', "moderate": 'اٹیچمنٹ کی بے چینی اعتدال پسند ہے؛محفوظ تعلقات کے طریقے اس علاقے کی حمایت کرتے ہیں۔', "low": 'آپ کے ترک کرنے کی پریشانی کم ہے۔آپ تعلقات میں محفوظ اور متوازن لگاؤ \u200b\u200bظاہر کرتے ہیں۔'},
            'avoidance': {"high": 'جذباتی قربت سے گریز قابل توجہ ہے؛اس پیٹرن کو پہچاننا گہرے بندھنوں کی طرف پہلا قدم ہے۔', "moderate": 'قربت سے بچنا اعتدال ہے۔جیسے جیسے خود آگاہی بڑھتی ہے، آپ مزید کھلے رابطے بنا سکتے ہیں۔', "low": 'جذباتی قربت سے آپ کا اجتناب کم ہے۔کشادگی اور کنکشن تعلقات میں آرام دہ محسوس کرتے ہیں.'},
        },
        'grit': {
            'perseverance': {"high": 'آپ جو کچھ شروع کرتے ہیں اسے مکمل کرنے اور رکاوٹوں کے باوجود جاری رکھنے میں آپ مضبوط ہیں۔', "moderate": 'آپ کا عزم اور حوصلہ بڑھ رہا ہے۔طویل مدتی اہداف کے لیے پرعزم رہنا اس کو تقویت دیتا ہے۔', "low": 'قلیل مدتی کامیابیوں کو جمع کرنا پائیدار استقامت کی تعمیر کے لیے ایک مؤثر حکمت عملی ہے۔'},
            'passion': {"high": 'آپ اپنے طویل مدتی اہداف کی طرف مستقل جذبہ اور دلچسپی ظاہر کرتے ہیں۔', "moderate": 'اہداف کے لیے آپ کا جذبہ ترقی کر رہا ہے۔ایک بامعنی مقصد سے جڑنا اس توانائی کو بڑھاتا ہے۔', "low": 'ایسی دلچسپیوں کو دریافت کرنا جو آپ کو حقیقی طور پر متحرک کرتے ہیں آپ کے جذبے اور حوصلہ افزائی کو تقویت بخشیں گے۔'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'آپ کو پختہ یقین ہے کہ صلاحیتوں اور ذہانت کو کوشش کے ذریعے تیار کیا جا سکتا ہے۔', "moderate": 'آپ کی ترقی کی ذہنیت ترقی کر رہی ہے؛چیلنجز کو سیکھنے کے مواقع کے طور پر دیکھنا اس کی پرورش کرتا ہے۔', "low": 'یہ یقین کہ صلاحیتیں مستقل ہیں؛اس ذہنیت پر سوال اٹھانا آپ کی ترقی کو تیز کرے گا۔'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'آپ اپنی زندگی سے اعلیٰ اطمینان کی اطلاع دیتے ہیں اور مجموعی طور پر مثبت تشخیص کرتے ہیں۔', "moderate": 'آپ کی زندگی کا اطمینان اعتدال پسند ہے؛معنی قدر کی سیدھ کو مضبوط بنانے سے تکمیل میں اضافہ ہوتا ہے۔', "low": 'زندگی کا اطمینان کم ہے؛اپنے آپ سے پوچھنا کہ آپ کیا تبدیل کرنا چاہتے ہیں ایک اچھا نقطہ آغاز ہے۔'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'آپ ہمدردی اور سمجھ بوجھ کے ساتھ اپنے آپ سے رجوع کرتے ہیں۔نفسیاتی لچک کا ایک مضبوط ذریعہ۔', "moderate": 'آپ کی خود شفقت ترقی کر رہی ہے؛مشکل لمحات میں اپنے آپ سے ایک دوست کی طرح بات کرنا اس کی پرورش کرتا ہے۔', "low": 'ایک سخت اندرونی آواز نمایاں ہے؛خود ہمدردی کے طریقوں کو تیار کرنا آپ کی مدد کرے گا۔'},
            'self_judgment': {"high": 'ضرورت سے زیادہ خود پر تنقید کرنے کا رجحان موجود ہے۔اس کو تسلیم کرنا تبدیلی کا ایک طاقتور نقطہ آغاز ہے۔', "moderate": 'خود تنقید معتدل ہے۔اپنے آپ پر مہربان ہونا کبھی کبھی فائدہ لاتا ہے۔', "low": 'آپ اپنے تئیں متوازن اور مہربان رویہ ظاہر کرتے ہیں۔خود تشخیص کی ایک صحت مند علامت۔'},
            'common_humanity': {"high": 'آپ سمجھتے ہیں کہ آپ کی جدوجہد مشترکہ انسانی تجربے کا حصہ ہے، جس سے سکون ملتا ہے۔', "moderate": 'آپ کا مشترکہ انسانیت کا احساس ترقی کر رہا ہے۔یاد رکھنا کہ آپ اکیلے نہیں ہیں آپ کو مضبوط کرتا ہے۔', "low": 'مشکلات پیدا ہونے پر آپ الگ تھلگ محسوس کر سکتے ہیں۔یاد رکھیں کہ یہ ایک بہت عام تجربہ ہے۔'},
            'isolation': {"high": 'آپ مشکل لمحات میں الگ تھلگ اور تنہا محسوس کرتے ہیں۔کنکشن اور مدد کی تلاش اس کو متوازن کرنے میں مدد کرتی ہے۔', "moderate": 'تنہائی کے احساسات وقتاً فوقتاً پیدا ہو سکتے ہیں۔کنکشن کی تعمیر اس میں توازن میں مدد کرتی ہے۔', "low": 'جب آپ مشکلات کا سامنا کرتے ہیں تو آپ منسلک اور معاون محسوس کرتے ہیں؛نفسیاتی صحت کی ایک اہم علامت۔'},
            'mindfulness': {"high": 'آپ توازن اور آگاہی کے ساتھ اپنے جذبات کا مشاہدہ کر سکتے ہیں۔ایک صحت مند نفسیاتی موقف.', "moderate": 'آپ کی ذہنی بیداری ترقی کر رہی ہے؛سادہ مراقبہ کے طریقوں سے اس علاقے کو تقویت ملے گی۔', "low": 'جذبات کا مشاہدہ کرنے کے بجائے دبانے کا رجحان ہے۔ذہن سازی کے طریقے مدد فراہم کر سکتے ہیں۔'},
            'overidentification': {"high": 'منفی جذبات اور خیالات پر زیادہ توجہ مرکوز کرنے کا رجحان ہے؛ذہن سازی کے عمل اس چکر کو توڑ دیتے ہیں۔', "moderate": 'آپ کبھی کبھی منفی خیالات سے زیادہ شناخت کر سکتے ہیں؛توازن کی حکمت عملی مدد کرتی ہے۔', "low": 'آپ منفی خیالات سے صحت مند فاصلہ برقرار رکھتے ہیں۔ذہنی بیداری کا ایک مضبوط اشارہ۔'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'آپ کو مشکل کاموں کو پورا کرنے کی اپنی صلاحیت پر پختہ یقین ہے۔', "moderate": 'آپ کا خود افادیت کا یقین ترقی کر رہا ہے۔چھوٹی کامیابیاں جمع کرنے سے اس اعتماد میں اضافہ ہوتا ہے۔', "low": 'آپ کی اپنی صلاحیتوں پر اعتماد کم ہے؛چھوٹے قدموں کے ذریعے کامیابی کے تجربات کی تعمیر میں مدد ملتی ہے۔'},
        },
        'stress': {
            'perceived_stress': {"high": 'آپ حال ہی میں اعلی سطح پر تناؤ محسوس کر رہے ہیں۔تناؤ کے انتظام کی حکمت عملی اب خاص طور پر اہم ہیں۔', "moderate": 'آپ اعتدال پسند تناؤ کا سامنا کر رہے ہیں؛تناؤ کے محرکات کی شناخت اور انتظام کرنے سے فائدہ ہوتا ہے۔', "low": 'آپ کے تناؤ کے ادراک کی سطح کم ہے۔چیلنجوں سے نمٹنے کی آپ کی صلاحیت مضبوط دکھائی دیتی ہے۔'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'آپ اپنی ظاہری شکل کا عمومی طور پر مثبت انداز میں جائزہ لیتے ہیں۔صحت مند جسم کی تصویر کی علامت۔', "moderate": 'آپ کے ظہور کے جائزے ملے جلے ہیں۔آپ کے جسم کی فعالیت پر توجہ مرکوز کرنے سے نقطہ نظر وسیع ہوتا ہے۔', "low": 'آپ کی ظاہری شکل کو منفی انداز میں جانچنے کا رجحان ہے۔جسمانی اثبات کے طریقے یہاں مدد فراہم کرتے ہیں۔'},
            'body_satisfaction': {"high": 'آپ عام طور پر اپنے جسم سے مطمئن ہیں؛صحت مند خود قبولیت کی علامت۔', "moderate": 'آپ کے جسم کی اطمینان اعتدال پسند ہے؛آپ کے جسم کی طاقتوں پر توجہ مرکوز کرنے سے اس علاقے کی پرورش ہوتی ہے۔', "low": 'آپ اپنے جسم سے غیر مطمئن محسوس کرتے ہیں؛خود رحمی کے طریقے اور پیشہ ورانہ مدد فائدہ مند ہو سکتی ہے۔'},
        },
    },
    'it': {
        'personality': {
            'openness': {"high": 'La tua curiosità e immaginazione sono forti;nuove esperienze e idee ti attraggono naturalmente.', "moderate": 'Bilancia la curiosità con la praticità, curioso in alcune aree e convenzionale in altre.', "low": 'Preferisci ciò che è pratico e familiare;routine coerenti e approcci comprovati ti sembrano giusti.'},
            'conscientiousness': {"high": 'Sei disciplinato, organizzato e affidabile;persegui gli obiettivi in \u200b\u200bmodo sistematico.', "moderate": 'Bilancia responsabilità e flessibilità;costruire routine lo rafforzerebbe ulteriormente.', "low": 'Hai uno stile flessibile, spontaneo;sviluppare abitudini di pianificazione può migliorare la tua efficacia.'},
            'extraversion': {"high": 'La tua energia sociale è alta;trai forza dalle persone e porti energia a chi ti circonda.', "moderate": 'Bilancia il tempo con gli altri e il tempo da solo, a tuo agio in entrambi i contesti.', "low": 'La tua natura introversa è una risorsa naturale per il pensiero profondo e il lavoro mirato.'},
            'agreeableness': {"high": 'La tua natura calda e cooperativa crea fiducia e armonia nelle tue relazioni.', "moderate": "Bilancia la cooperazione e l'indipendenza, la comprensione ma l'autoaffermazione.", "low": "Ti inclini al pensiero indipendente e critico: un punto di forza per l'analisi e il giudizio obiettivo."},
            'neuroticism': {"high": 'Le tue reazioni emotive possono essere intense;le strategie di gestione dello stress e di autoregolamentazione ti supporteranno.', "moderate": 'Provi alcuni alti e bassi emotivi;la maggior parte delle volte riesci a ritrovare il tuo equilibrio.', "low": 'La tua resilienza emotiva è forte;rimani calmo sotto pressione e gestisci le difficoltà con facilità.'},
        },
        'skills': {
            'problem_solving': {"high": "Sei forte nell'analizzare problemi complessi e nel generare soluzioni pratiche.", "moderate": 'Il tuo approccio alla risoluzione dei problemi si sta sviluppando;le tecniche di pensiero strutturato possono supportarti.', "low": 'L’apprendimento di metodi sistematici di risoluzione dei problemi sbloccherà il tuo potenziale in quest’area.'},
            'empathy': {"high": 'Hai una notevole capacità di comprendere le emozioni degli altri e di connetterti con empatia.', "moderate": "Le tue capacità di empatia si stanno sviluppando;praticare l'ascolto attivo rafforzerà quest'area.", "low": 'Esplorare maggiormente le prospettive degli altri ti renderà un comunicatore più efficace.'},
            'organization': {"high": 'La tua pianificazione e la definizione delle priorità sono forti;il tuo stile organizzato ti aiuta a distinguerti.', "moderate": 'La tua capacità organizzativa è ragionevole;utilizzare gli strumenti di gestione del tempo può renderti ancora più forte.', "low": 'Lo sviluppo di abitudini organizzative sistematiche può migliorare significativamente la produttività.'},
            'learning_speed': {"high": 'Ti adatti rapidamente a nuove conoscenze e competenze: un grande vantaggio in ambienti in evoluzione.', "moderate": 'Il tuo ritmo di apprendimento è ragionevole;sperimentare diverse strategie può aumentare la tua efficacia.', "low": "La revisione strutturata e le strategie pratiche supporteranno il tuo processo di apprendimento in quest'area."},
            'decision_making': {"high": 'Puoi compiere passi decisivi e rapidi nelle situazioni decisionali.', "moderate": 'Le tue capacità decisionali si stanno sviluppando;quadri strutturati aiutano nei momenti difficili.', "low": 'Iniziare con decisioni più piccole è un modo efficace per rafforzare la fiducia nel processo decisionale.'},
        },
        'hr': {
            'leadership': {"high": "Sei forte nel dirigere i team, nell'ispirare gli altri e nel prendere l'iniziativa.", "moderate": 'Hai attitudine alla leadership;le esperienze pratiche svilupperanno rapidamente queste abilità.', "low": 'Sviluppare deliberatamente capacità di leadership attraverso la pratica può far avanzare significativamente la tua carriera.'},
            'team_fit': {"high": 'Ti distingui per il lavoro di squadra armonioso, la collaborazione e la disponibilità.', "moderate": 'La forma della tua squadra è buona;la comprensione dei diversi stili di lavoro rafforzerà ulteriormente questo aspetto.', "low": 'Una partecipazione più attiva alle dinamiche del team rafforzerà le tue relazioni professionali.'},
            'communication': {"high": 'Sei forte nella comunicazione chiara, efficace e costruttiva.', "moderate": 'Il tuo stile di comunicazione si sta sviluppando;adattarsi a pubblici diversi ti dà un vantaggio.', "low": 'La pratica sistematica delle abilità comunicative produrrà rapidi progressi in quest’area.'},
            'stress_tolerance': {"high": 'Puoi mantenere la calma sotto pressione;una pietra miliare della resilienza professionale.', "moderate": 'La tua capacità di affrontare lo stress è ragionevole;le tecniche di costruzione della resilienza ti renderanno ancora più forte.', "low": 'Lo sviluppo di strategie di gestione dello stress, supportate da pratiche quotidiane, produce risultati rapidamente.'},
            'motivation': {"high": 'La tua motivazione intrinseca è alta;ti avvicini ai tuoi obiettivi con impegno e passione.', "moderate": 'La tua motivazione varia;rimanere connessi al proprio scopo può essere una fonte di energia continua.', "low": 'Stabilire obiettivi significativi a breve termine è un modo efficace per riaccendere la motivazione.'},
        },
        'career': {
            'analytical': {"high": 'Hai un forte orientamento verso il pensiero analitico e gli ambienti di lavoro incentrati sui dati.', "moderate": 'Hai tendenze analitiche;la pratica strutturata della risoluzione dei problemi rafforzerà quest’area.', "low": "Lo sviluppo di capacità analitiche sistematiche amplierà le tue opzioni in quest'area di carriera."},
            'creative': {"high": 'Ti esprimi al meglio in ambienti lavorativi creativi e innovativi.', "moderate": 'Hai tendenze creative;coltivare quest’area può aumentare la tua realizzazione professionale.', "low": 'I percorsi di carriera strutturali e tecnici sembrano attualmente più allineati rispetto ai ruoli incentrati sulla creatività.'},
            'social': {"high": 'Aiutare, insegnare o lavorare con le persone ti dà energia.', "moderate": "Ti senti a tuo agio in ruoli che implicano l'interazione sociale;connessioni più profonde possono aggiungere valore.", "low": "I percorsi professionali incentrati sul sociale non sono attualmente un'area di forte interesse per te."},
            'entrepreneurial': {"high": 'Hai una forte tendenza verso ruoli imprenditoriali che richiedono leadership, persuasione e assunzione di rischi.', "moderate": 'La tua prospettiva imprenditoriale si sta sviluppando;il processo decisionale e l’esperienza di leadership accelereranno questo processo.', "low": 'I percorsi di carriera incentrati sulle competenze sembrano attualmente più allineati rispetto ai ruoli imprenditoriali.'},
            'managerial': {"high": 'Sei adatto a ruoli che richiedono gestione, coordinamento e organizzazione.', "moderate": 'Le tue tendenze manageriali si stanno sviluppando;l’assunzione di responsabilità alimenterà questo settore.', "low": 'Percorsi di carriera incentrati sulle competenze con meno pressione manageriale potrebbero sembrare più a loro agio in questo momento.'},
            'technical': {"high": 'Hai un forte interesse e orientamento verso settori tecnici e specialistici.', "moderate": 'Le tue capacità tecniche si stanno sviluppando;una profonda specializzazione rafforzerà quest’area.', "low": 'I percorsi di carriera incentrati sulle persone sembrano attualmente più allineati rispetto ai ruoli di specialisti tecnici.'},
        },
        'vocation': {
            'realistic': {"high": 'Hai una forte inclinazione per il lavoro pratico, pratico e tecnico.', "moderate": "Hai un moderato interesse per il lavoro pratico;provare quest'area ti darà un'immagine più chiara.", "low": 'Le attività pratiche e tecniche non rientrano attualmente tra i tuoi forti interessi.'},
            'investigative': {"high": 'La ricerca, l’analisi e l’esplorazione delle idee ti attraggono naturalmente.', "moderate": 'Hai interesse investigativo;l’approfondimento della conoscenza in questo settore lo rafforzerà ulteriormente.', "low": "Le attività focalizzate sulla ricerca e sull'analisi non rientrano attualmente tra i tuoi interessi prioritari."},
            'artistic': {"high": 'Hai una forte inclinazione verso le attività che richiedono espressione creativa, arte ed estetica.', "moderate": 'Hai tendenze artistiche;coltivare quest’area può fornire appagamento e autenticità.', "low": 'Le attività artistiche e creative non sono attualmente un ambito di forte interesse per te.'},
            'social': {"high": 'Stare con le persone, aiutare e insegnare ti dà energia.', "moderate": 'Hai un moderato interesse per le attività sociali;costruire connessioni significative porta soddisfazione.', "low": 'Le attività incentrate sul sociale non rientrano attualmente tra i tuoi interessi prioritari.'},
            'enterprising': {"high": 'Ti senti più forte nelle attività che richiedono leadership, persuasione e competizione.', "moderate": 'Hai tendenze intraprendenti;praticare la responsabilità e il processo decisionale rafforza questo.', "low": "Le attività competitive e incentrate sulla leadership non sono attualmente un'area di forte interesse per te."},
            'conventional': {"high": 'Sei forte negli ambienti di lavoro organizzati, sistematici e coerenti con le regole.', "moderate": "Hai un moderato interesse per l'organizzazione e la struttura;la pratica di lavoro sistematica favorisce questo.", "low": 'Le attività strutturate e convenzionali non sono attualmente un ambito di forte interesse per te.'},
        },
        'relationship': {
            'love_language': {"high": "Esprimi chiaramente il tuo linguaggio d'amore e apprezzi la comprensione reciproca nelle relazioni.", "moderate": "Esprimi il tuo linguaggio d'amore con moderazione;essere più aperti qui può arricchire le tue relazioni.", "low": 'Sviluppare la consapevolezza dell’espressione emotiva e dei linguaggi dell’amore approfondirà le tue connessioni.'},
            'conflict_style': {"high": 'Sei forte nel risolvere i conflitti in modi costruttivi e sani.', "moderate": 'Il tuo stile di risoluzione dei conflitti si sta sviluppando;provare approcci più costruttivi può aiutare.', "low": 'Lo sviluppo di sane strategie di risoluzione dei conflitti migliorerà significativamente la qualità della tua relazione.'},
            'intimacy_needs': {"high": 'Comprendi chiaramente i tuoi bisogni di vicinanza e connessione emotiva.', "moderate": "Hai una moderata consapevolezza dei tuoi bisogni di intimità;esplorare ulteriormente quest'area è prezioso.", "low": 'Comprendere il tuo legame emotivo e le tue esigenze di intimità renderà le tue relazioni più soddisfacenti.'},
            'relationship_values': {"high": 'Hai un chiaro quadro di valori per ciò che desideri nelle tue relazioni.', "moderate": 'I tuoi valori relazionali stanno prendendo forma;riflettere su questo ti aiuta a costruire connessioni più sane.', "low": 'Scoprire e chiarire i tuoi valori relazionali personali pone le basi per legami più profondi.'},
        },
        'attachment': {
            'anxiety': {"high": 'L’ansia per l’abbandono è elevata;questa consapevolezza è un forte punto di partenza per sviluppare un attaccamento sicuro.', "moderate": "L’ansia da attaccamento è moderata;le pratiche di relazione sicura supportano quest'area.", "low": 'La tua ansia da abbandono è bassa;mostri un attaccamento sicuro ed equilibrato nelle relazioni.'},
            'avoidance': {"high": "L'evitamento della vicinanza emotiva è evidente;Riconoscere questo modello è il primo passo verso legami più profondi.", "moderate": "L'evitamento della vicinanza è moderato;man mano che la consapevolezza di sé cresce, puoi costruire connessioni più aperte.", "low": "Il tuo evitamento della vicinanza emotiva è basso;l'apertura e la connessione si sentono a proprio agio nelle relazioni."},
        },
        'grit': {
            'perseverance': {"high": 'Sei forte nel completare ciò che inizi e nel continuare nonostante gli ostacoli.', "moderate": 'La tua determinazione e grinta si stanno sviluppando;rimanere impegnati verso obiettivi a lungo termine rafforza questo aspetto.', "low": 'Accumulare successi a breve termine è una strategia efficace per costruire una perseveranza sostenibile.'},
            'passion': {"high": 'Mostri passione e interesse costanti verso i tuoi obiettivi a lungo termine.', "moderate": 'La tua passione per gli obiettivi si sta sviluppando;connettersi a uno scopo significativo amplifica questa energia.', "low": 'Scoprire interessi che ti infiammano davvero alimenterà la tua passione e la tua motivazione.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": "Credi fermamente che le capacità e l'intelligenza possano essere sviluppate attraverso lo sforzo.", "moderate": 'La tua mentalità di crescita si sta sviluppando;vedere le sfide come opportunità di apprendimento favorisce tutto questo.', "low": 'La convinzione che le capacità siano fisse continua;mettere in discussione questa mentalità accelererà la tua crescita.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'Riferisci un elevato grado di soddisfazione per la tua vita e fai una valutazione complessivamente positiva.', "moderate": 'La tua soddisfazione di vita è moderata;rafforzare l’allineamento significato-valore aumenta la realizzazione.', "low": 'La soddisfazione della vita è bassa;chiederti cosa vuoi cambiare è un buon punto di partenza.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'Ti avvicini a te stesso con compassione e comprensione;una forte fonte di resilienza psicologica.', "moderate": 'La tua auto-compassione si sta sviluppando;parlare con te stesso come un amico nei momenti difficili alimenta questo.', "low": 'Una dura voce interiore è prominente;lo sviluppo di pratiche di auto-compassione ti supporterà.'},
            'self_judgment': {"high": 'È presente una tendenza ad essere eccessivamente autocritici;riconoscere questo è un potente punto di partenza per il cambiamento.', "moderate": "L'autocritica è moderata;essere gentile con te stesso a volte porta benefici.", "low": 'Mostri un atteggiamento equilibrato e gentile verso te stesso;un sano segno di autovalutazione.'},
            'common_humanity': {"high": "Comprendi che le tue lotte fanno parte dell'esperienza umana condivisa, che porta conforto.", "moderate": 'Il tuo senso di comune umanità si sta sviluppando;Ricordare che non sei solo ti rafforza.', "low": "Potresti sentirti isolato quando sorgono difficoltà;ricorda che questa è un'esperienza molto comune."},
            'isolation': {"high": 'Ti senti isolato e solo nei momenti difficili;cercare connessione e supporto aiuta a bilanciare questo.', "moderate": 'Di tanto in tanto possono sorgere sentimenti di isolamento;costruire connessioni aiuta a bilanciare questo.', "low": 'Ti senti connesso e supportato quando affronti le difficoltà;un segnale importante di salute psicologica.'},
            'mindfulness': {"high": 'Puoi osservare le tue emozioni con equilibrio e consapevolezza;una sana posizione psicologica.', "moderate": "La tua consapevolezza consapevole si sta sviluppando;semplici pratiche di meditazione rafforzeranno quest'area.", "low": "C'è la tendenza a sopprimere piuttosto che osservare le emozioni;le pratiche di consapevolezza possono fornire supporto."},
            'overidentification': {"high": "C'è la tendenza a concentrarsi eccessivamente su emozioni e pensieri negativi;le pratiche di consapevolezza interrompono questo ciclo.", "moderate": 'A volte puoi identificarti eccessivamente con pensieri negativi;le strategie di equilibrio aiutano.', "low": 'Mantieni una sana distanza dai pensieri negativi;un forte indicatore di consapevolezza consapevole.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'Hai una forte fiducia nella tua capacità di portare a termine compiti impegnativi.', "moderate": 'La tua convinzione di autoefficacia si sta sviluppando;accumulare piccoli successi aumenta questa fiducia.', "low": 'La fiducia nelle proprie capacità è bassa;costruire esperienze di successo attraverso piccoli passi aiuta.'},
        },
        'stress': {
            'perceived_stress': {"high": 'Ultimamente stai percependo un elevato livello di stress;le strategie di gestione dello stress sono particolarmente importanti ora.', "moderate": 'Stai vivendo uno stress moderato;identificare e gestire i fattori scatenanti dello stress porta benefici.', "low": 'Il tuo livello di percezione dello stress è basso;la tua capacità di gestire le sfide sembra forte.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": "Valuti il \u200b\u200btuo aspetto generalmente positivamente;un segno di un'immagine corporea sana.", "moderate": "Le tue valutazioni sull'aspetto sono contrastanti;concentrarsi sulla funzionalità del proprio corpo amplia la prospettiva.", "low": "C'è la tendenza a valutare negativamente il tuo aspetto;le pratiche di affermazione del corpo forniscono supporto in questo caso."},
            'body_satisfaction': {"high": 'Generalmente sei soddisfatto del tuo corpo;un segno di sana accettazione di sé.', "moderate": "La soddisfazione del tuo corpo è moderata;concentrarsi sui punti di forza del proprio corpo nutre quest'area.", "low": 'Ti senti insoddisfatto del tuo corpo;pratiche di auto-compassione e supporto professionale possono essere utili.'},
        },
    },
    'vi': {
        'personality': {
            'openness': {"high": 'Sự tò mò và trí tưởng tượng của bạn rất mạnh mẽ;những trải nghiệm và ý tưởng mới sẽ thu hút bạn một cách tự nhiên.', "moderate": 'Bạn cân bằng sự tò mò với tính thực tế, tò mò ở một số lĩnh vực và thông thường ở những lĩnh vực khác.', "low": 'Bạn thích những gì thực tế và quen thuộc;các thói quen nhất quán và các phương pháp đã được chứng minh sẽ phù hợp với bạn.'},
            'conscientiousness': {"high": 'Bạn là người có kỷ luật, có tổ chức và đáng tin cậy;bạn theo đuổi mục tiêu một cách có hệ thống.', "moderate": 'Bạn cân bằng giữa trách nhiệm và tính linh hoạt;xây dựng thói quen sẽ củng cố điều này hơn nữa.', "low": 'Bạn có phong cách linh hoạt, tự phát;phát triển thói quen lập kế hoạch có thể cải thiện hiệu quả của bạn.'},
            'extraversion': {"high": 'Năng lượng xã hội của bạn cao;bạn thu hút sức mạnh từ mọi người và mang lại năng lượng cho những người xung quanh.', "moderate": 'Bạn cân bằng thời gian với người khác và thời gian ở một mình, thoải mái trong cả hai hoàn cảnh.', "low": 'Bản chất hướng nội của bạn là tài sản tự nhiên cho khả năng suy nghĩ sâu sắc và tập trung làm việc.'},
            'agreeableness': {"high": 'Bản chất ấm áp, hợp tác của bạn xây dựng niềm tin và sự hòa hợp trong các mối quan hệ của bạn.', "moderate": 'Bạn cân bằng giữa tính hợp tác và sự độc lập, hiểu biết nhưng vẫn tự quyết.', "low": 'Bạn thiên về tư duy phê phán, độc lập - sức mạnh để phân tích và đánh giá khách quan.'},
            'neuroticism': {"high": 'Phản ứng cảm xúc của bạn có thể rất mãnh liệt;chiến lược quản lý căng thẳng và tự điều chỉnh sẽ hỗ trợ bạn.', "moderate": 'Bạn trải qua một số cảm xúc thăng trầm;hầu hết thời gian bạn có thể tìm lại được số dư của mình.', "low": 'Khả năng phục hồi cảm xúc của bạn rất mạnh mẽ;bạn giữ bình tĩnh trước áp lực và xử lý khó khăn một cách dễ dàng.'},
        },
        'skills': {
            'problem_solving': {"high": 'Bạn giỏi phân tích các vấn đề phức tạp và đưa ra các giải pháp thực tế.', "moderate": 'Phương pháp giải quyết vấn đề của bạn đang phát triển;kỹ thuật tư duy có cấu trúc có thể hỗ trợ bạn.', "low": 'Học các phương pháp giải quyết vấn đề có hệ thống sẽ mở ra tiềm năng của bạn trong lĩnh vực này.'},
            'empathy': {"high": 'Bạn có khả năng vượt trội trong việc hiểu được cảm xúc của người khác và kết nối bằng sự đồng cảm.', "moderate": 'Kỹ năng đồng cảm của bạn đang phát triển;thực hành lắng nghe tích cực sẽ củng cố lĩnh vực này.', "low": 'Khám phá quan điểm của người khác nhiều hơn sẽ giúp bạn trở thành người giao tiếp hiệu quả hơn.'},
            'organization': {"high": 'Việc lập kế hoạch và ưu tiên của bạn rất mạnh mẽ;phong cách ngăn nắp của bạn sẽ giúp bạn nổi bật.', "moderate": 'Kỹ năng tổ chức của bạn là hợp lý;sử dụng các công cụ quản lý thời gian có thể khiến bạn mạnh mẽ hơn nữa.', "low": 'Phát triển thói quen tổ chức có hệ thống có thể cải thiện đáng kể năng suất của bạn.'},
            'learning_speed': {"high": 'Bạn thích ứng nhanh chóng với kiến \u200b\u200bthức và kỹ năng mới - một lợi thế lớn trong môi trường luôn thay đổi.', "moderate": 'Tốc độ học tập của bạn là hợp lý;thử nghiệm các chiến lược khác nhau có thể làm tăng hiệu quả của bạn.', "low": 'Các chiến lược thực hành và đánh giá có cấu trúc sẽ hỗ trợ quá trình học tập của bạn trong lĩnh vực này.'},
            'decision_making': {"high": 'Bạn có thể thực hiện những bước đi quyết đoán, nhanh chóng trong các tình huống đưa ra quyết định.', "moderate": 'Kỹ năng ra quyết định của bạn đang phát triển;khuôn khổ có cấu trúc giúp đỡ trong những thời điểm khó khăn.', "low": 'Bắt đầu với những quyết định nhỏ hơn là một cách hiệu quả để xây dựng sự tự tin khi đưa ra quyết định của bạn.'},
        },
        'hr': {
            'leadership': {"high": 'Bạn có khả năng chỉ đạo nhóm tốt, truyền cảm hứng cho người khác và dẫn đầu.', "moderate": 'Bạn có năng khiếu lãnh đạo;kinh nghiệm thực tế sẽ phát triển những kỹ năng này một cách nhanh chóng.', "low": 'Cố ý phát triển kỹ năng lãnh đạo thông qua thực hành có thể thúc đẩy đáng kể sự nghiệp của bạn.'},
            'team_fit': {"high": 'Bạn nổi bật nhờ khả năng làm việc nhóm hài hòa, hợp tác và sẵn sàng giúp đỡ.', "moderate": 'Đội của bạn phù hợp tốt;hiểu các phong cách làm việc khác nhau sẽ củng cố điều này hơn nữa.', "low": 'Việc tham gia tích cực hơn vào hoạt động nhóm sẽ củng cố các mối quan hệ nghề nghiệp của bạn.'},
            'communication': {"high": 'Bạn có khả năng giao tiếp rõ ràng, hiệu quả và mang tính xây dựng.', "moderate": 'Phong cách giao tiếp của bạn đang phát triển;việc thích ứng với các đối tượng khác nhau mang lại cho bạn một lợi thế.', "low": 'Việc rèn luyện các kỹ năng giao tiếp một cách có hệ thống sẽ tạo ra sự tiến bộ nhanh chóng trong lĩnh vực này.'},
            'stress_tolerance': {"high": 'Bạn có thể giữ bình tĩnh trước áp lực;nền tảng của khả năng phục hồi nghề nghiệp.', "moderate": 'Khả năng đối phó với căng thẳng của bạn ở mức hợp lý;kỹ thuật xây dựng khả năng phục hồi sẽ làm cho bạn mạnh mẽ hơn nữa.', "low": 'Việc phát triển các chiến lược quản lý căng thẳng, được hỗ trợ bằng thực hành hàng ngày, sẽ mang lại kết quả nhanh chóng.'},
            'motivation': {"high": 'Động lực nội tại của bạn cao;bạn tiếp cận mục tiêu của mình bằng sự cam kết và đam mê.', "moderate": 'Động lực của bạn thay đổi;duy trì kết nối với mục đích của bạn có thể là một nguồn năng lượng liên tục.', "low": 'Đặt ra những mục tiêu ngắn hạn có ý nghĩa là một cách hiệu quả để khơi dậy động lực của bạn.'},
        },
        'career': {
            'analytical': {"high": 'Bạn có định hướng mạnh mẽ về tư duy phân tích và môi trường làm việc tập trung vào dữ liệu.', "moderate": 'Bạn có xu hướng phân tích;thực hành giải quyết vấn đề có cấu trúc sẽ củng cố lĩnh vực này.', "low": 'Phát triển kỹ năng phân tích có hệ thống sẽ mở rộng các lựa chọn của bạn trong lĩnh vực nghề nghiệp này.'},
            'creative': {"high": 'Bạn thể hiện bản thân tốt nhất trong môi trường làm việc sáng tạo và đổi mới.', "moderate": 'Bạn có khuynh hướng sáng tạo;nuôi dưỡng lĩnh vực này có thể làm tăng sự thỏa mãn nghề nghiệp của bạn.', "low": 'Con đường sự nghiệp về mặt cấu trúc và kỹ thuật hiện có vẻ phù hợp hơn so với các vai trò tập trung vào sáng tạo.'},
            'social': {"high": 'Giúp đỡ, giảng dạy hoặc làm việc với mọi người sẽ tiếp thêm năng lượng cho bạn.', "moderate": 'Bạn cảm thấy thoải mái với những vai trò liên quan đến tương tác xã hội;kết nối sâu hơn có thể tăng thêm giá trị.', "low": 'Con đường sự nghiệp tập trung vào xã hội hiện không phải là lĩnh vực bạn quan tâm.'},
            'entrepreneurial': {"high": 'Bạn có khuynh hướng mạnh mẽ đối với các vai trò kinh doanh đòi hỏi khả năng lãnh đạo, thuyết phục và chấp nhận rủi ro.', "moderate": 'Quan điểm kinh doanh của bạn đang phát triển;kinh nghiệm ra quyết định và lãnh đạo sẽ đẩy nhanh quá trình này.', "low": 'Con đường sự nghiệp tập trung vào chuyên môn hiện có vẻ phù hợp hơn vai trò kinh doanh.'},
            'managerial': {"high": 'Bạn rất phù hợp với những vai trò đòi hỏi sự quản lý, điều phối và tổ chức.', "moderate": 'Xu hướng quản lý của bạn đang phát triển;đảm nhận trách nhiệm sẽ nuôi dưỡng lĩnh vực này.', "low": 'Con đường sự nghiệp tập trung vào chuyên môn với ít áp lực quản lý hơn có thể khiến bạn cảm thấy thoải mái hơn lúc này.'},
            'technical': {"high": 'Bạn có niềm đam mê và định hướng mạnh mẽ đối với các lĩnh vực kỹ thuật và chuyên ngành.', "moderate": 'Kỹ năng kỹ thuật của bạn đang phát triển;chuyên môn sâu sẽ củng cố lĩnh vực này.', "low": 'Con đường sự nghiệp tập trung vào con người hiện có vẻ phù hợp hơn vai trò chuyên gia kỹ thuật.'},
        },
        'vocation': {
            'realistic': {"high": 'Bạn có thiên hướng mạnh mẽ về công việc thực tế, thực hành và kỹ thuật.', "moderate": 'Bạn có hứng thú vừa phải với công việc thực hành;thử khu vực này sẽ cho bạn một bức tranh rõ ràng hơn.', "low": 'Các hoạt động thực tế và kỹ thuật hiện không phải là mối quan tâm chính của bạn.'},
            'investigative': {"high": 'Nghiên cứu, phân tích và khám phá các ý tưởng sẽ thu hút bạn một cách tự nhiên.', "moderate": 'Bạn có hứng thú điều tra;đào sâu kiến \u200b\u200bthức trong lĩnh vực này sẽ củng cố nó hơn nữa.', "low": 'Các hoạt động tập trung vào nghiên cứu và phân tích hiện không nằm trong mối quan tâm ưu tiên của bạn.'},
            'artistic': {"high": 'Bạn có thiên hướng mạnh mẽ về các hoạt động đòi hỏi sự thể hiện sáng tạo, nghệ thuật và thẩm mỹ.', "moderate": 'Bạn có khuynh hướng nghệ thuật;nuôi dưỡng lĩnh vực này có thể mang lại sự thỏa mãn và tính xác thực.', "low": 'Hoạt động nghệ thuật và sáng tạo hiện không phải là lĩnh vực bạn quan tâm nhiều.'},
            'social': {"high": 'Ở bên mọi người, giúp đỡ và dạy dỗ sẽ tiếp thêm năng lượng cho bạn.', "moderate": 'Bạn có sự quan tâm vừa phải đến các hoạt động xã hội;xây dựng những kết nối có ý nghĩa mang lại sự hài lòng.', "low": 'Các hoạt động tập trung vào xã hội hiện không nằm trong số các mối quan tâm ưu tiên của bạn.'},
            'enterprising': {"high": 'Bạn cảm thấy mạnh mẽ nhất trong những hoạt động đòi hỏi khả năng lãnh đạo, thuyết phục và cạnh tranh.', "moderate": 'Bạn có khuynh hướng dám nghĩ dám làm;thực hành trách nhiệm và ra quyết định củng cố điều này.', "low": 'Các hoạt động cạnh tranh và tập trung vào khả năng lãnh đạo hiện không phải là lĩnh vực bạn quan tâm.'},
            'conventional': {"high": 'Bạn mạnh mẽ trong môi trường làm việc có tổ chức, có hệ thống và tuân thủ các quy tắc.', "moderate": 'Bạn có sự quan tâm vừa phải đến tổ chức và cơ cấu;thực hành làm việc có hệ thống sẽ nuôi dưỡng điều này.', "low": 'Các hoạt động có cấu trúc và thông thường hiện không phải là lĩnh vực được bạn quan tâm nhiều.'},
        },
        'relationship': {
            'love_language': {"high": 'Bạn thể hiện rõ ràng ngôn ngữ tình yêu của mình và coi trọng sự hiểu biết lẫn nhau trong các mối quan hệ.', "moderate": 'Bạn thể hiện ngôn ngữ tình yêu của mình một cách vừa phải;cởi mở hơn ở đây có thể làm phong phú thêm các mối quan hệ của bạn.', "low": 'Phát triển nhận thức về biểu hiện cảm xúc và ngôn ngữ tình yêu sẽ làm sâu sắc thêm mối quan hệ của bạn.'},
            'conflict_style': {"high": 'Bạn rất mạnh mẽ trong việc giải quyết xung đột theo những cách mang tính xây dựng và lành mạnh.', "moderate": 'Phong cách giải quyết xung đột của bạn đang phát triển;thử các cách tiếp cận mang tính xây dựng hơn có thể hữu ích.', "low": 'Phát triển các chiến lược giải quyết xung đột lành mạnh sẽ cải thiện đáng kể chất lượng mối quan hệ của bạn.'},
            'intimacy_needs': {"high": 'Bạn hiểu rõ nhu cầu của mình về sự gần gũi và kết nối tình cảm.', "moderate": 'Bạn có nhận thức vừa phải về nhu cầu thân mật của mình;khám phá khu vực này hơn nữa là có giá trị.', "low": 'Hiểu được nhu cầu gắn kết tình cảm và sự thân mật của bạn sẽ làm cho mối quan hệ của bạn trở nên viên mãn hơn.'},
            'relationship_values': {"high": 'Bạn có một khung giá trị rõ ràng cho những gì bạn muốn trong các mối quan hệ của mình.', "moderate": 'Giá trị mối quan hệ của bạn đang hình thành;suy ngẫm về điều này sẽ giúp bạn xây dựng các kết nối lành mạnh hơn.', "low": 'Việc khám phá và làm rõ các giá trị trong mối quan hệ cá nhân của bạn sẽ đặt nền tảng cho những mối quan hệ sâu sắc hơn.'},
        },
        'attachment': {
            'anxiety': {"high": 'Lo lắng về việc bị bỏ rơi rất cao;nhận thức này là điểm khởi đầu vững chắc để phát triển sự gắn bó an toàn.', "moderate": 'Sự lo lắng về sự gắn bó ở mức vừa phải;thực hành mối quan hệ an toàn hỗ trợ lĩnh vực này.', "low": 'Nỗi lo bị bỏ rơi của bạn ở mức thấp;bạn thể hiện sự gắn bó an toàn và cân bằng trong các mối quan hệ.'},
            'avoidance': {"high": 'Việc tránh né sự gần gũi về mặt tình cảm là điều dễ nhận thấy;nhận ra mô hình này là bước đầu tiên hướng tới những mối liên kết sâu sắc hơn.', "moderate": 'Tránh gần gũi là vừa phải;khi khả năng tự nhận thức tăng lên, bạn có thể xây dựng nhiều kết nối cởi mở hơn.', "low": 'Khả năng tránh gần gũi về mặt tình cảm của bạn ở mức thấp;sự cởi mở và kết nối tạo cảm giác thoải mái trong các mối quan hệ.'},
        },
        'grit': {
            'perseverance': {"high": 'Bạn mạnh mẽ trong việc hoàn thành những gì bạn đã bắt đầu và tiếp tục bất chấp những trở ngại.', "moderate": 'Sự quyết tâm và bền bỉ của bạn đang phát triển;luôn cam kết với các mục tiêu dài hạn sẽ củng cố điều này.', "low": 'Tích lũy những thành công ngắn hạn là một chiến lược hiệu quả để xây dựng tính kiên trì bền vững.'},
            'passion': {"high": 'Bạn thể hiện niềm đam mê và sự quan tâm nhất quán đối với các mục tiêu dài hạn của mình.', "moderate": 'Niềm đam mê mục tiêu của bạn đang phát triển;kết nối với một mục đích có ý nghĩa sẽ khuếch đại năng lượng này.', "low": 'Việc khám phá những sở thích thực sự khiến bạn hứng khởi sẽ tiếp thêm niềm đam mê và động lực cho bạn.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'Bạn tin tưởng mạnh mẽ rằng khả năng và trí thông minh có thể được phát triển thông qua nỗ lực.', "moderate": 'Tư duy phát triển của bạn đang phát triển;xem những thách thức là cơ hội học tập nuôi dưỡng điều này.', "low": 'Niềm tin rằng các khả năng là cố định vẫn tiếp tục;đặt câu hỏi về suy nghĩ này sẽ đẩy nhanh sự phát triển của bạn.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'Bạn báo cáo sự hài lòng cao với cuộc sống của bạn và đưa ra đánh giá tổng thể tích cực.', "moderate": 'Sự hài lòng về cuộc sống của bạn ở mức vừa phải;tăng cường sự liên kết ý nghĩa-giá trị làm tăng sự thỏa mãn.', "low": 'Mức độ hài lòng với cuộc sống ở mức thấp;tự hỏi bản thân xem bạn muốn thay đổi điều gì là một điểm khởi đầu tốt.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'Bạn tiếp cận bản thân bằng lòng trắc ẩn và sự hiểu biết;một nguồn sức mạnh tâm lý mạnh mẽ.', "moderate": 'Lòng từ bi của bạn đang phát triển;nói chuyện với chính mình như một người bạn trong những thời điểm khó khăn sẽ nuôi dưỡng điều này.', "low": 'Một giọng nói nội tâm khắc nghiệt nổi bật;việc phát triển các thực hành lòng từ bi với bản thân sẽ hỗ trợ bạn.'},
            'self_judgment': {"high": 'Có xu hướng tự phê bình quá mức;nhận ra đây là điểm khởi đầu mạnh mẽ cho sự thay đổi.', "moderate": 'Tự phê bình ở mức vừa phải;tử tế hơn với bản thân đôi khi mang lại lợi ích.', "low": 'Bạn thể hiện thái độ cân bằng và tử tế với bản thân;một dấu hiệu lành mạnh của sự tự đánh giá.'},
            'common_humanity': {"high": 'Bạn hiểu rằng những khó khăn của bạn là một phần trải nghiệm chung của con người, điều này mang lại sự thoải mái.', "moderate": 'Ý thức về lòng nhân đạo chung của bạn đang phát triển;việc nhớ rằng bạn không đơn độc sẽ củng cố bạn.', "low": 'Bạn có thể cảm thấy bị cô lập khi gặp khó khăn;hãy nhớ rằng đây là một trải nghiệm rất bình thường.'},
            'isolation': {"high": 'Bạn cảm thấy bị cô lập và đơn độc trong những thời khắc khó khăn;tìm kiếm sự kết nối và hỗ trợ giúp cân bằng điều này.', "moderate": 'Đôi khi cảm giác bị cô lập có thể nảy sinh;xây dựng các kết nối giúp cân bằng điều này.', "low": 'Bạn cảm thấy được kết nối và hỗ trợ khi gặp khó khăn;một dấu hiệu quan trọng của sức khỏe tâm lý.'},
            'mindfulness': {"high": 'Bạn có thể quan sát cảm xúc của mình một cách cân bằng và nhận thức;một thái độ tâm lý lành mạnh.', "moderate": 'Nhận thức chánh niệm của bạn đang phát triển;thực hành thiền đơn giản sẽ củng cố lĩnh vực này.', "low": 'Có xu hướng kìm nén hơn là quan sát cảm xúc;thực hành chánh niệm có thể cung cấp hỗ trợ.'},
            'overidentification': {"high": 'Có xu hướng tập trung quá mức vào những cảm xúc và suy nghĩ tiêu cực;thực hành chánh niệm sẽ phá vỡ chu kỳ này.', "moderate": 'Đôi khi bạn có thể đồng cảm quá mức với những suy nghĩ tiêu cực;chiến lược cân bằng giúp đỡ.', "low": 'Bạn duy trì một khoảng cách lành mạnh với những suy nghĩ tiêu cực;một dấu hiệu mạnh mẽ của nhận thức chánh niệm.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'Bạn có niềm tin mãnh liệt vào khả năng hoàn thành những nhiệm vụ đầy thử thách của mình.', "moderate": 'Niềm tin vào năng lực bản thân của bạn đang phát triển;tích lũy những thành công nhỏ làm tăng sự tự tin này.', "low": 'Sự tự tin vào khả năng của bản thân thấp;xây dựng kinh nghiệm thành công thông qua các bước nhỏ sẽ giúp ích.'},
        },
        'stress': {
            'perceived_stress': {"high": 'Gần đây bạn đang cảm thấy mức độ căng thẳng cao;chiến lược quản lý căng thẳng hiện nay đặc biệt quan trọng.', "moderate": 'Bạn đang gặp căng thẳng vừa phải;xác định và quản lý các tác nhân gây căng thẳng mang lại lợi ích.', "low": 'Mức độ nhận thức căng thẳng của bạn thấp;khả năng xử lý thử thách của bạn có vẻ mạnh mẽ.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'Bạn đánh giá ngoại hình của mình nhìn chung là tích cực;một dấu hiệu của hình ảnh cơ thể khỏe mạnh.', "moderate": 'Đánh giá về ngoại hình của bạn là khác nhau;tập trung vào chức năng của cơ thể bạn sẽ mở rộng tầm nhìn.', "low": 'Có xu hướng đánh giá ngoại hình của bạn một cách tiêu cực;thực hành khẳng định cơ thể cung cấp hỗ trợ ở đây.'},
            'body_satisfaction': {"high": 'Nhìn chung bạn hài lòng với cơ thể của mình;một dấu hiệu của sự chấp nhận bản thân lành mạnh.', "moderate": 'Sự hài lòng về cơ thể của bạn ở mức vừa phải;tập trung vào điểm mạnh của cơ thể bạn sẽ nuôi dưỡng khu vực này.', "low": 'Bạn cảm thấy không hài lòng với cơ thể mình;thực hành lòng từ bi và sự hỗ trợ chuyên nghiệp có thể có lợi.'},
        },
    },
    'pl': {
        'personality': {
            'openness': {"high": 'Twoja ciekawość i wyobraźnia są silne;nowe doświadczenia i pomysły w naturalny sposób Cię przyciągają.', "moderate": 'Łączysz ciekawość z praktycznością, ciekawość w niektórych obszarach i konwencjonalność w innych.', "low": 'Wolisz to, co praktyczne i znane;spójne procedury i sprawdzone podejścia są dla Ciebie odpowiednie.'},
            'conscientiousness': {"high": 'Jesteś zdyscyplinowany, zorganizowany i niezawodny;systematycznie dążysz do celu.', "moderate": 'Równoważysz odpowiedzialność i elastyczność;procedury budowlane jeszcze bardziej to wzmocnią.', "low": 'Masz elastyczny, spontaniczny styl;rozwijanie nawyków planowania może poprawić Twoją efektywność.'},
            'extraversion': {"high": 'Twoja energia społeczna jest wysoka;czerpiesz siłę od ludzi i dajesz energię otaczającym cię osobom.', "moderate": 'Równoważysz czas z innymi i czas sam, wygodnie w obu ustawieniach.', "low": 'Twoja introwertyczna natura jest naturalnym atutem umożliwiającym głębokie myślenie i skupioną pracę.'},
            'agreeableness': {"high": 'Twoja ciepła, współpracująca natura buduje zaufanie i harmonię w twoich relacjach.', "moderate": 'Równoważysz współpracę i niezależność, zrozumienie, a jednocześnie asertywność.', "low": 'Skłaniasz się ku niezależnemu, krytycznemu myśleniu – co jest siłą niezbędną do analizy i obiektywnej oceny.'},
            'neuroticism': {"high": 'Twoje reakcje emocjonalne mogą być intensywne;strategie zarządzania stresem i samoregulacji będą Ci pomocne.', "moderate": 'Doświadczasz emocjonalnych wzlotów i upadków;przez większość czasu możesz ponownie znaleźć równowagę.', "low": 'Twoja odporność emocjonalna jest silna;zachowujesz spokój pod presją i łatwo radzisz sobie z trudnościami.'},
        },
        'skills': {
            'problem_solving': {"high": 'Potrafisz analizować złożone problemy i generować praktyczne rozwiązania.', "moderate": 'Rozwija się Twoje podejście do rozwiązywania problemów;Techniki myślenia strukturalnego mogą Ci pomóc.', "low": 'Nauka systematycznych metod rozwiązywania problemów odblokuje Twój potencjał w tym obszarze.'},
            'empathy': {"high": 'Masz niezwykłą zdolność rozumienia emocji innych i łączenia się z empatią.', "moderate": 'Rozwijają się Twoje umiejętności empatii;ćwiczenie aktywnego słuchania wzmocni ten obszar.', "low": 'Większe poznawanie perspektyw innych sprawi, że będziesz skuteczniejszym komunikatorem.'},
            'organization': {"high": 'Twoje planowanie i ustalanie priorytetów są dobre;Twój zorganizowany styl pomaga Ci się wyróżnić.', "moderate": 'Twoje umiejętności organizacyjne są rozsądne;korzystanie z narzędzi do zarządzania czasem może uczynić Cię jeszcze silniejszym.', "low": 'Rozwijanie systematycznych nawyków organizacyjnych może znacząco poprawić Twoją produktywność.'},
            'learning_speed': {"high": 'Szybko dostosowujesz się do nowej wiedzy i umiejętności – to główna zaleta w zmieniającym się środowisku.', "moderate": 'Twoje tempo nauki jest rozsądne;eksperymentowanie z różnymi strategiami może zwiększyć Twoją skuteczność.', "low": 'Ustrukturyzowane strategie przeglądu i ćwiczeń będą wspierać Twój proces uczenia się w tym obszarze.'},
            'decision_making': {"high": 'W sytuacjach decyzyjnych potrafisz podejmować zdecydowane i szybkie kroki.', "moderate": 'Rozwijają się Twoje umiejętności podejmowania decyzji;strukturyzowane ramy pomagają w trudnych chwilach.', "low": 'Rozpoczęcie od mniejszych decyzji to skuteczny sposób na budowanie pewności siebie przy podejmowaniu decyzji.'},
        },
        'hr': {
            'leadership': {"high": 'Potrafisz kierować zespołami, inspirować innych i przewodzić.', "moderate": 'Masz zdolności przywódcze;praktyczne doświadczenia szybko rozwiną te umiejętności.', "low": 'Celowe rozwijanie umiejętności przywódczych poprzez praktykę może znacząco przyspieszyć Twoją karierę.'},
            'team_fit': {"high": 'Wyróżnia Cię harmonijna praca zespołowa, współpraca i uczynność.', "moderate": 'Twoje dopasowanie do zespołu jest dobre;zrozumienie różnych stylów pracy jeszcze bardziej to wzmocni.', "low": 'Bardziej aktywne uczestnictwo w dynamice zespołu wzmocni Twoje relacje zawodowe.'},
            'communication': {"high": 'Potrafisz jasno, efektywnie i konstruktywnie komunikować się.', "moderate": 'Twój styl komunikacji rozwija się;dostosowywanie się do różnych odbiorców daje przewagę.', "low": 'Systematyczne ćwiczenie umiejętności komunikacyjnych przyniesie szybki postęp w tej dziedzinie.'},
            'stress_tolerance': {"high": 'Potrafisz zachować spokój pod presją;kamień węgielny odporności zawodowej.', "moderate": 'Twoja zdolność radzenia sobie ze stresem jest rozsądna;Techniki budowania odporności sprawią, że będziesz jeszcze silniejszy.', "low": 'Opracowanie strategii zarządzania stresem, wspartych codziennymi praktykami, szybko daje rezultaty.'},
            'motivation': {"high": 'Twoja wewnętrzna motywacja jest wysoka;podchodzisz do swoich celów z zaangażowaniem i pasją.', "moderate": 'Twoja motywacja jest różna;utrzymywanie kontaktu z celem może być ciągłym źródłem energii.', "low": 'Wyznaczanie znaczących celów krótkoterminowych to skuteczny sposób na ponowne wzbudzenie motywacji.'},
        },
        'career': {
            'analytical': {"high": 'Cechuje Cię silna orientacja w kierunku myślenia analitycznego i środowisk pracy skoncentrowanych na danych.', "moderate": 'Masz skłonności analityczne;ustrukturyzowana praktyka rozwiązywania problemów wzmocni ten obszar.', "low": 'Rozwijanie systematycznych umiejętności analitycznych poszerzy Twoje możliwości w tym obszarze kariery.'},
            'creative': {"high": 'Najlepiej wyrażasz siebie w kreatywnym i innowacyjnym środowisku pracy.', "moderate": 'Masz tendencje twórcze;pielęgnowanie tego obszaru może zwiększyć Twoje spełnienie zawodowe.', "low": 'Strukturalne i techniczne ścieżki kariery wydają się obecnie bardziej dopasowane niż role skupione na kreatywności.'},
            'social': {"high": 'Pomaganie, nauczanie lub praca z ludźmi dodaje Ci energii.', "moderate": 'Dobrze czujesz się w rolach wymagających interakcji społecznych;głębsze połączenia mogą dodać wartość.', "low": 'Ścieżki kariery zorientowane na społeczeństwo nie są obecnie Twoim obszarem dużego zainteresowania.'},
            'entrepreneurial': {"high": 'Masz silną tendencję do podejmowania ról przedsiębiorczych wymagających przywództwa, perswazji i podejmowania ryzyka.', "moderate": 'Rozwija się Twoja perspektywa przedsiębiorczości;proces podejmowania decyzji i doświadczenie przywódcze przyspieszą to.', "low": 'Ścieżki kariery zorientowane na wiedzę specjalistyczną wydają się obecnie bardziej wyrównane niż role przedsiębiorcze.'},
            'managerial': {"high": 'Dobrze nadajesz się do ról wymagających zarządzania, koordynacji i organizacji.', "moderate": 'Rozwijają się Twoje tendencje menedżerskie;wzięcie na siebie odpowiedzialności będzie pielęgnować ten obszar.', "low": 'Ścieżki kariery zorientowane na wiedzę specjalistyczną i charakteryzujące się mniejszą presją ze strony kierownictwa mogą być teraz wygodniejsze.'},
            'technical': {"high": 'Masz duże zainteresowanie i orientację w dziedzinach technicznych i specjalistycznych.', "moderate": 'Rozwijają się Twoje umiejętności techniczne;głęboka specjalizacja wzmocni ten obszar.', "low": 'Ścieżki kariery zorientowane na ludzi wydają się obecnie bardziej wyrównane niż stanowiska specjalistów technicznych.'},
        },
        'vocation': {
            'realistic': {"high": 'Masz silną skłonność do pracy praktycznej, praktycznej i technicznej.', "moderate": 'Masz umiarkowane zainteresowanie pracą praktyczną;wypróbowanie tego obszaru da wyraźniejszy obraz.', "low": 'Zajęcia praktyczne i techniczne nie należą obecnie do Twoich głównych zainteresowań.'},
            'investigative': {"high": 'Badania, analizy i odkrywanie pomysłów w naturalny sposób Cię przyciągają.', "moderate": 'Masz zainteresowania dochodzeniowe;pogłębianie wiedzy w tym obszarze jeszcze bardziej ją wzmocni.', "low": 'Działalność o charakterze badawczym i analitycznym nie należy obecnie do Twoich priorytetowych zainteresowań.'},
            'artistic': {"high": 'Masz silną skłonność do działań wymagających ekspresji twórczej, sztuki i estetyki.', "moderate": 'Masz tendencje artystyczne;pielęgnowanie tego obszaru może zapewnić spełnienie i autentyczność.', "low": 'Działalność artystyczna i twórcza nie jest obecnie obszarem Twoich zainteresowań.'},
            'social': {"high": 'Bycie z ludźmi, pomaganie i nauczanie dodaje Ci energii.', "moderate": 'Masz umiarkowane zainteresowanie działalnością społeczną;budowanie znaczących relacji przynosi satysfakcję.', "low": 'Działalność społeczna nie należy obecnie do Twoich priorytetowych zainteresowań.'},
            'enterprising': {"high": 'Najsilniej czujesz się w działaniach wymagających przywództwa, perswazji i rywalizacji.', "moderate": 'Masz skłonności do przedsiębiorczości;praktykowanie odpowiedzialności i podejmowania decyzji wzmacnia to.', "low": 'Działania konkurencyjne i zorientowane na przywództwo nie są obecnie obszarem Twoich zainteresowań.'},
            'conventional': {"high": 'Dobrze radzisz sobie w zorganizowanym, systematycznym i zgodnym z zasadami środowisku pracy.', "moderate": 'Masz umiarkowane zainteresowanie organizacją i strukturą;pielęgnuje to systematyczna praktyka zawodowa.', "low": 'Ustrukturyzowane i konwencjonalne działania nie są obecnie dla Ciebie szczególnie interesującym obszarem.'},
        },
        'relationship': {
            'love_language': {"high": 'Jasno wyrażasz swój język miłości i cenisz wzajemne zrozumienie w związkach.', "moderate": 'Umiarkowanie wyrażasz swój język miłości;bycie bardziej otwartym tutaj może wzbogacić wasze relacje.', "low": 'Rozwijanie świadomości wyrażania emocji i języków miłości pogłębi Twoje połączenia.'},
            'conflict_style': {"high": 'Potrafisz rozwiązywać konflikty w konstruktywny i zdrowy sposób.', "moderate": 'Rozwija się Twój styl rozwiązywania konfliktów;pomocne może być wypróbowanie bardziej konstruktywnego podejścia.', "low": 'Opracowanie zdrowych strategii rozwiązywania konfliktów znacznie poprawi jakość relacji.'},
            'intimacy_needs': {"high": 'Wyraźnie rozumiesz swoje potrzeby emocjonalnej bliskości i połączenia.', "moderate": 'Masz umiarkowaną świadomość swoich potrzeb w zakresie intymności;Dalsze badanie tego obszaru jest cenne.', "low": 'Zrozumienie swoich potrzeb związanych z więzią emocjonalną i intymnością sprawi, że wasze relacje będą bardziej satysfakcjonujące.'},
            'relationship_values': {"high": 'Masz jasne ramy wartości określające, czego chcesz w swoich relacjach.', "moderate": 'Twoje wartości w związku nabierają kształtu;zastanowienie się nad tym pomoże Ci zbudować zdrowsze relacje.', "low": 'Odkrycie i wyjaśnienie wartości swoich osobistych relacji stanowi podstawę głębszych więzi.'},
        },
        'attachment': {
            'anxiety': {"high": 'Niepokój związany z porzuceniem jest wysoki;ta świadomość jest mocnym punktem wyjścia do rozwijania bezpiecznego przywiązania.', "moderate": 'Lęk przed przywiązaniem jest umiarkowany;praktyki bezpiecznych relacji wspierają ten obszar.', "low": 'Twój lęk przed porzuceniem jest niski;okazujesz bezpieczne i zrównoważone przywiązanie w związkach.'},
            'avoidance': {"high": 'Zauważalne jest unikanie bliskości emocjonalnej;rozpoznanie tego wzorca jest pierwszym krokiem w kierunku głębszych więzi.', "moderate": 'Unikanie bliskości jest umiarkowane;w miarę wzrostu samoświadomości możesz budować bardziej otwarte połączenia.', "low": 'Twoje unikanie bliskości emocjonalnej jest niskie;otwartość i łączność sprawiają, że czujesz się komfortowo w związkach.'},
        },
        'grit': {
            'perseverance': {"high": 'Jesteś silny w kończeniu tego, co zacząłeś i kontynuowaniu pomimo przeszkód.', "moderate": 'Twoja determinacja i hart ducha rozwijają się;trzymanie się celów długoterminowych wzmacnia to.', "low": 'Gromadzenie krótkoterminowych sukcesów to skuteczna strategia budowania trwałej wytrwałości.'},
            'passion': {"high": 'Wykazujesz stałą pasję i zainteresowanie długoterminowymi celami.', "moderate": 'Twoja pasja do celów rozwija się;połączenie się ze znaczącym celem wzmacnia tę energię.', "low": 'Odkrywanie zainteresowań, które naprawdę Cię rozpalają, wzmocni Twoją pasję i motywację.'},
        },
        'growth_mindset': {
            'growth_mindset': {"high": 'Mocno wierzysz, że zdolności i inteligencję można rozwijać poprzez wysiłek.', "moderate": 'Rozwija się Twoje nastawienie na rozwój;postrzeganie wyzwań jako możliwości uczenia się, które to wspierają.', "low": 'Nadal utrzymuje się przekonanie, że umiejętności są stałe;kwestionowanie tego sposobu myślenia przyspieszy Twój rozwój.'},
        },
        'life_satisfaction': {
            'life_satisfaction': {"high": 'Zgłaszasz wysoki poziom zadowolenia ze swojego życia i ogólnie oceniasz go pozytywnie.', "moderate": 'Twoje zadowolenie z życia jest umiarkowane;wzmocnienie dopasowania znaczenia do wartości zwiększa spełnienie.', "low": 'Satysfakcja z życia jest niska;Dobrym punktem wyjścia jest zadanie sobie pytania, co chcesz zmienić.'},
        },
        'self_compassion': {
            'self_kindness': {"high": 'Podchodzisz do siebie ze współczuciem i zrozumieniem;silne źródło odporności psychicznej.', "moderate": 'Rozwija się Twoje współczucie dla samego siebie;mówienie do siebie jak do przyjaciela w trudnych chwilach sprzyja temu.', "low": 'Wyraźny jest ostry głos wewnętrzny;rozwinięcie praktyk współczucia wobec siebie będzie dla ciebie wsparciem.'},
            'self_judgment': {"high": 'Występuje tendencja do nadmiernego samokrytycyzmu;Uświadomienie sobie tego jest potężnym punktem wyjścia do zmian.', "moderate": 'Samokrytyka jest umiarkowana;bycie dla siebie milszym czasami przynosi korzyści.', "low": 'Wykazujesz zrównoważone i życzliwe podejście do siebie;zdrowy znak samooceny.'},
            'common_humanity': {"high": 'Rozumiesz, że twoje zmagania są częścią wspólnego ludzkiego doświadczenia, które przynosi pocieszenie.', "moderate": 'Rozwija się twoje poczucie wspólnego człowieczeństwa;świadomość, że nie jesteś sam, wzmacnia cię.', "low": 'Możesz czuć się osamotniony, gdy pojawiają się trudności;pamiętaj, że jest to bardzo częste doświadczenie.'},
            'isolation': {"high": 'Czujesz się odizolowany i samotny w trudnych chwilach;szukanie kontaktu i wsparcia pomaga to zrównoważyć.', "moderate": 'Od czasu do czasu może pojawić się poczucie izolacji;budowanie połączeń pomaga to zrównoważyć.', "low": 'Czujesz więź i wsparcie w obliczu trudności;ważny objaw zdrowia psychicznego.'},
            'mindfulness': {"high": 'Możesz obserwować swoje emocje z zachowaniem równowagi i świadomości;zdrowa postawa psychologiczna.', "moderate": 'Twoja uważna świadomość rozwija się;proste praktyki medytacyjne wzmocnią ten obszar.', "low": 'Istnieje tendencja do raczej tłumienia niż obserwowania emocji;Praktyki uważności mogą zapewnić wsparcie.'},
            'overidentification': {"high": 'Istnieje tendencja do nadmiernego skupiania się na negatywnych emocjach i myślach;praktyki uważności przerywają ten cykl.', "moderate": 'Czasami możesz nadmiernie utożsamiać się z negatywnymi myślami;Strategie równowagi pomagają.', "low": 'Utrzymujesz zdrowy dystans od negatywnych myśli;silny wskaźnik uważnej świadomości.'},
        },
        'self_efficacy': {
            'self_efficacy': {"high": 'Masz silną wiarę w swoją zdolność do wykonywania trudnych zadań.', "moderate": 'Rozwija się Twoja wiara we własną skuteczność;gromadzenie małych sukcesów zwiększa tę pewność.', "low": 'Wiara we własne możliwości jest niska;budowanie doświadczeń sukcesu metodą małych kroków pomaga.'},
        },
        'stress': {
            'perceived_stress': {"high": 'Odczuwasz ostatnio wysoki poziom stresu;strategie radzenia sobie ze stresem są teraz szczególnie ważne.', "moderate": 'Doświadczasz umiarkowanego stresu;identyfikacja czynników wywołujących stres i radzenie sobie z nimi przynosi korzyści.', "low": 'Twój poziom odczuwania stresu jest niski;Twoja zdolność do radzenia sobie z wyzwaniami wydaje się silna.'},
        },
        'body_image': {
            'appearance_evaluation': {"high": 'Oceniasz swój wygląd ogólnie pozytywnie;oznaka zdrowego obrazu ciała.', "moderate": 'Twoje oceny wyglądu są mieszane;skupienie się na funkcjonalności swojego ciała poszerza perspektywę.', "low": 'Istnieje tendencja do negatywnej oceny swojego wyglądu;Praktyki afirmacji ciała zapewniają tutaj wsparcie.'},
            'body_satisfaction': {"high": 'Ogólnie rzecz biorąc, jesteś zadowolony ze swojego ciała;oznaka zdrowej samoakceptacji.', "moderate": 'Twoje zadowolenie z ciała jest umiarkowane;skupienie się na mocnych stronach ciała pielęgnuje ten obszar.', "low": 'Czujesz się niezadowolony ze swojego ciała;praktyki współczucia wobec siebie i profesjonalne wsparcie mogą być korzystne.'},
        },
    },
}


_DOMAIN_DESC_GENERIC: dict = {
    'tr': {'high': 'Bu alanda güçlü bir profil sergiliyorsunuz.', 'moderate': 'Bu alanda gelişmeye devam etmektesiniz.', 'low': 'Bu alan gelişim fırsatı sunuyor.'},
    'en': {'high': 'You show a strong profile in this area.', 'moderate': 'You are continuing to develop in this area.', 'low': 'This area offers a growth opportunity.'},
}


def get_domain_description(test_type: str, domain: str, level: str, lang: str = 'tr') -> str:
    """Return a 1-sentence contextual description for the domain based on its score level."""
    level_lower = level.lower()
    if level_lower in ('very high', 'high'):
        tier = 'high'
    elif level_lower in ('low', 'very low'):
        tier = 'low'
    else:
        tier = 'moderate'

    lang_key = lang if lang in _DOMAIN_DESCRIPTIONS else 'en'
    desc = (_DOMAIN_DESCRIPTIONS
            .get(lang_key, {})
            .get(test_type, {})
            .get(domain, {})
            .get(tier, ''))
    generic = _DOMAIN_DESC_GENERIC.get(lang_key, _DOMAIN_DESC_GENERIC['en'])
    return desc or generic.get(tier, '')


def generate_recommendations(test_type: str, breakdown: Dict, overall_score: float, lang: str = 'tr') -> Dict:
    """
    Generate a personalized narrative + spotlight for assessment results using local Ollama.

    Returns:
        Dict with narrative (str), strengths ([{name,score}]), growth_areas ([{name,score}]),
        recommendations (kept for compat), status
    """
    attachment_style = _classify_attachment(breakdown) if test_type == 'attachment' else None
    spotlight = _compute_spotlight(breakdown)

    try:
        prompt = _generate_prompt(test_type, breakdown, overall_score, lang)
        response_text = _call_ollama_local(prompt)

        if response_text and len(response_text.strip()) > 40:
            result = {
                'status': 'success',
                'narrative': response_text.strip(),
                'strengths': spotlight['strengths'],
                'growth_areas': spotlight['growth_areas'],
                'recommendations': [],
                'recommendations_status': 'success',
            }
        else:
            log.info('Ollama unavailable or empty, using fallback')
            if test_type in ('career', 'vocation'):
                fallback = _career_job_fallback(test_type, breakdown, lang)
            else:
                fallback = get_fallback_recommendations(test_type, lang)
            result = {
                'status': 'fallback',
                'narrative': ' '.join(fallback),
                'strengths': spotlight['strengths'],
                'growth_areas': spotlight['growth_areas'],
                'recommendations': fallback,
                'recommendations_status': 'template',
            }

        if attachment_style:
            result['attachment_style'] = attachment_style
        return result

    except Exception as e:
        log.error(f'Error generating recommendations: {e}')
        if test_type in ('career', 'vocation'):
            fallback = _career_job_fallback(test_type, breakdown, lang)
        else:
            fallback = get_fallback_recommendations(test_type, lang)
        result = {
            'status': 'fallback',
            'narrative': ' '.join(fallback),
            'strengths': spotlight['strengths'],
            'growth_areas': spotlight['growth_areas'],
            'recommendations': fallback,
            'recommendations_status': 'template',
        }
        if attachment_style:
            result['attachment_style'] = attachment_style
        return result


# Fallback recommendations if Ollama unavailable — 18 languages
FALLBACK_RECOMMENDATIONS = {
    'tr': {
        'skills': ["Problem çözme becerinizi pratik projelerle güçlendirin.", "En düşük puanlı alanda çevrenizden destek almaktan çekinmeyin.", "Yeni becerileri öğrenme konusundaki hızınızı koruyun.", "Öğrendiklerinizi başkalarıyla paylaşarak pekiştirin."],
        'hr': ["Ekip çalışmasında örnek olmaya devam edin.", "Leaderboard becerilerini mentoring yoluyla geliştirin.", "Stres yönetimi tekniklerini kişisel rutininize ekleyin.", "Geri bildirime açık olmayı bir alışkanlık haline getirin."],
        'personality': ["Kişiliğinizin güçlü yönlerini hedef belirlemede kullanın.", "Farklı kişilik tiplerini anlamaya çalışarak empati geliştirin.", "İç dengeyi sağlayan faaliyetleri keşfetmeye zaman ayırın.", "Kendini tanıma yolculuğunda sabırlı ve öz-sempatik olun."],
        'career': ["En ilgi duyduğunuz kariyer alanına yönelik projelerde çalışın.", "Zayıf yönlerinizi geliştirmek için eğitim kaynaklarını araştırın.", "Mentorlük ve networking fırsatlarından yararlanın.", "Düzenli olarak kariyer hedeflerinizi gözden geçirin."],
        'relationship': ["İlişkilerinizde açık ve dürüst iletişimi temel alın.", "Duygusal zeka becerilerinizi pratik hayatta uygulamaya çalışın.", "Bağlılık tarzınızı anlamak gelişim için önemlidir.", "Sağlıklı ilişki dinamikleri hakkında bilgi edinmeye yatırım yapın."],
        'vocation': ["En uyumlu meslekler listesini araştırarak deneyim kazanın.", "Çalışma alanlarında gözlemlik veya stajlık fırsatlarını keşfedin.", "Sektör profesyonelleriyle bağlantı kurup deneyim paylaşmalarını dinleyin.", "Mesleki gelişim yolunuzu tarih belirlemeden sabırla ilerleyin."],
        'grit': ["Zorluklarla karşılaştığınızda vazgeçmeden devam etme kasınızı güçlendirin.", "Uzun vadeli hedeflerinize olan bağlılığınızı somut adımlarla pekiştirin.", "İlgi alanlarınızı derinleştirerek tutarlılık ve odak geliştirin.", "Her küçük ilerlemeyi kutlayarak azim motivasyonunuzu canlı tutun."],
        'growth_mindset': ["Başarısızlıkları öğrenme fırsatı olarak yeniden çerçevelendirin.", "Zor görevlerde 'Henüz yapamıyorum' yerine 'Henüz öğrenmiyorum' deyin.", "Çaba ve strateji odaklı geri bildirimlere açık olun.", "Yeteneklerin geliştirilebilir olduğunu hatırlatacak günlük uygulamalar deneyin."],
        'life_satisfaction': ["Hayatınızdaki olumlu yönleri fark etmek için minnet günlüğü tutun.", "Gerçek hedeflerinizle mevcut yaşamınız arasındaki boşluğu kapatacak küçük adımlar atın.", "Değerlerinize uygun aktivitelere daha fazla zaman ayırın.", "Anlamlı ilişkilere ve deneyimlere yatırım yaparak doyum artırın."],
        'self_compassion': ["Kendinize bir arkadaşınıza davrandığınız gibi şefkatle yaklaşın.", "Hatalarınızı insanlığın ortak deneyimi olarak görmeyi pratik edin.", "Zor anlarda kendinizi rahatlatıcı bir ses tonuyla destekleyin.", "Duyguları bastırmak yerine farkındalıkla gözlemlemeyi alışkanlık haline getirin."],
        'body_image': ["Vücudunuzu performansı ve sağlığı açısından değerlendirmeyi deneyin.", "Sosyal medyada gerçekçi olmayan standartlara maruz kalmayı sınırlayın.", "Bedeninizle barışık olmanızı destekleyen hareketlere odaklanın.", "Görünüm yerine güçlü yönlerinize odaklanarak öz-değer geliştirin."],
        'self_efficacy': ["Küçük zorlukları başarıyla aştıkça öz-güveninizi kademeli artırın.", "Geçmişte üstesinden geldiğiniz zorluklara düzenli olarak bakın.", "Kendinize güvendiğiniz bir mentorun veya rol modelinin yaklaşımını benimseyin.", "Belirsiz durumlarda adım adım aksiyon planı yaparak kontrol duygusu geliştirin."],
        'stress': ["Nefes egzersizleri ve kısa meditasyon pratiklerini günlük rutininize ekleyin.", "Stres kaynaklarını belirleyerek hangilerini kontrol edebileceğinize odaklanın.", "Fiziksel aktivite ve kaliteli uyku stres yönetiminin temel taşlarıdır.", "Duygusal destek için güvenilir kişilerle bağlantıda kalmayı ihmal etmeyin."],
    },
    'en': {
        'skills': ["Strengthen problem-solving skills through practical projects.", "Don't hesitate to seek support in your weakest areas.", "Maintain your rapid learning pace for new skills.", "Reinforce what you learn by sharing with others."],
        'hr': ["Continue setting an example in teamwork and collaboration.", "Develop leadership through mentoring and guidance roles.", "Integrate stress management techniques into your routine.", "Make openness to feedback a daily practice."],
        'personality': ["Use your personality strengths for goal-setting and planning.", "Build empathy by understanding different personality types.", "Invest time finding activities that bring inner balance.", "Be patient and self-compassionate in self-discovery."],
        'career': ["Pursue projects in your most interesting career fields.", "Research educational resources for weak career areas.", "Leverage mentoring and networking opportunities.", "Review career goals regularly for alignment."],
        'relationship': ["Base relationships on open and honest communication.", "Apply emotional intelligence skills in everyday interactions.", "Understanding attachment style supports personal growth.", "Invest in learning about healthy relationship dynamics."],
        'vocation': ["Research compatible professions and gain practical experience.", "Explore internship and shadowing opportunities in sectors.", "Network with professionals and learn from their experiences.", "Advance your career path patiently without rushing."],
        'grit': ["Build the habit of persisting through difficulties without giving up.", "Reinforce commitment to long-term goals with concrete milestones.", "Deepen your interests to develop consistency and focus.", "Celebrate every small progress to keep your motivation alive."],
        'growth_mindset': ["Reframe setbacks as learning opportunities rather than failures.", "Replace 'I can't do this' with 'I can't do this yet.'", "Welcome feedback focused on effort and strategy.", "Practice daily reminders that abilities can be developed with work."],
        'life_satisfaction': ["Keep a gratitude journal to notice the positives in your life.", "Take small steps to close the gap between your values and current life.", "Spend more time on activities aligned with your core values.", "Invest in meaningful relationships and experiences to boost fulfillment."],
        'self_compassion': ["Speak to yourself with the same kindness you'd offer a good friend.", "Practice seeing your mistakes as part of the shared human experience.", "In difficult moments, comfort yourself with a supportive inner voice.", "Observe emotions mindfully instead of suppressing them."],
        'body_image': ["Try evaluating your body for its performance and health, not appearance.", "Limit exposure to unrealistic standards on social media.", "Focus on movements and activities that help you feel at home in your body.", "Build self-worth around your strengths, not your appearance."],
        'self_efficacy': ["Gradually increase self-confidence by mastering small challenges first.", "Regularly reflect on past difficulties you have successfully overcome.", "Adopt the approach of a mentor or role model you trust.", "In uncertain situations, build control by making step-by-step action plans."],
        'stress': ["Add breathing exercises and short meditation to your daily routine.", "Identify stress sources and focus on those within your control.", "Physical activity and quality sleep are cornerstones of stress management.", "Stay connected with trusted people for emotional support."],
    },
    'de': {
        'skills': ["Stärke deine Problemlösungsfähigkeiten durch praktische Projekte.", "Zögere nicht, Unterstützung in deinen schwächsten Bereichen zu suchen.", "Behalte dein schnelles Lerntempo bei.", "Verstärke das Gelernte durch Teilen mit anderen."],
        'hr': ["Setze weiterhin ein Vorbild in Teamarbeit.", "Entwickle Führungskompetenzen durch Mentoring.", "Integriere Stressabbau in deine Routine.", "Mache Offenheit für Rückmeldungen zur Gewohnheit."],
        'personality': ["Nutze deine Stärken zur Zielsetzung.", "Entwickle Empathie durch Verständnis anderer Typen.", "Investiere Zeit in ausgleichende Aktivitäten.", "Sei geduldig mit dir selbst beim Selbstverständnis."],
        'career': ["Verfolge Projekte in deinen Interessensfeldern.", "Recherchiere Ressourcen für schwache Bereiche.", "Nutze Mentoring und Networking-Chancen.", "Überprüfe Karriereziele regelmäßig."],
        'relationship': ["Basiere Beziehungen auf offener Kommunikation.", "Wende emotionale Intelligenz im Alltag an.", "Verstehe deinen Bindungsstil.", "Investiere in Wissen über gesunde Beziehungen."],
        'vocation': ["Recherchiere kompatible Berufe und sammle Erfahrung.", "Erkunde Praktikums- und Hospitationschancen.", "Vernetze dich mit Fachleuten.", "Verfolge deinen Karriereweg geduldig."]
    },
    'ru': {
        'skills': ["Укрепляйте навыки решения проблем через практические проекты.", "Не стесняйтесь искать поддержку в слабых областях.", "Сохраняйте быстрый темп обучения.", "Закрепляйте знания, делясь с другими."],
        'hr': ["Продолжайте подавать пример в командной работе.", "Развивайте лидерство через наставничество.", "Интегрируйте техники управления стрессом.", "Сделайте открытость к обратной связи привычкой."],
        'personality': ["Используйте свои сильные стороны для целеполагания.", "Развивайте эмпатию, понимая разные типы.", "Инвестируйте время в уравновешивающую деятельность.", "Будьте терпеливы с собой в самопознании."],
        'career': ["Преследуйте проекты в интересующих областях.", "Исследуйте ресурсы для слабых областей.", "Используйте возможности наставничества и сетевого взаимодействия.", "Регулярно проверяйте карьерные цели."],
        'relationship': ["Базируйте отношения на открытом общении.", "Применяйте эмоциональный интеллект в повседневной жизни.", "Поймите свой стиль привязанности.", "Инвестируйте в знания о здоровых отношениях."],
        'vocation': ["Исследуйте совместимые профессии и получайте опыт.", "Изучайте возможности стажировки и наблюдения.", "Общайтесь с профессионалами.", "Следуйте карьерному пути терпеливо."]
    },
    'ar': {
        'skills': ["قوّ مهارات حل المشاكل من خلال المشاريع العملية.", "لا تتردد في طلب الدعم في المجالات الضعيفة.", "حافظ على وتيرة التعلم السريع.", "عزز ما تتعلمه بمشاركته مع الآخرين."],
        'hr': ["استمر في أن تكون قدوة في العمل الجماعي.", "طور القيادة من خلال الإرشاد.", "ادمج تقنيات إدارة الضغط.", "اجعل الانفتاح على الملاحظات عادة يومية."],
        'personality': ["استخدم نقاط قوتك في تحديد الأهداف.", "طور التعاطف بفهم أنواع مختلفة.", "استثمر الوقت في أنشطة التوازن.", "كن صبوراً مع نفسك في اكتشاف الذات."],
        'career': ["متابعة المشاريع في مجالات اهتمامك.", "ابحث عن الموارد للمجالات الضعيفة.", "استفد من فرص الإرشاد والتواصل.", "راجع أهدافك الوظيفية بانتظام."],
        'relationship': ["أسّس العلاقات على التواصل المفتوح.", "طبّق الذكاء العاطفي في الحياة اليومية.", "افهم أسلوب تعلقك.", "استثمر في معرفة العلاقات الصحية."],
        'vocation': ["استكشف المهن المتوافقة واكتسب الخبرة.", "استكشف فرص التدريب والمراقبة.", "تواصل مع المتخصصين.", "اتبع مسارك الوظيفي بصبر."]
    },
    'es': {
        'skills': ["Fortalece habilidades de resolución mediante proyectos prácticos.", "No dudes en buscar apoyo en áreas débiles.", "Mantén tu ritmo rápido de aprendizaje.", "Refuerza lo aprendido compartiéndolo con otros."],
        'hr': ["Continúa siendo ejemplo en trabajo en equipo.", "Desarrolla liderazgo a través del mentorado.", "Integra técnicas de manejo de estrés.", "Haz de la apertura al feedback una práctica diaria."],
        'personality': ["Usa tus fortalezas para establecer objetivos.", "Desarrolla empatía comprendiendo diferentes tipos.", "Invierte tiempo en actividades equilibradoras.", "Sé paciente contigo en el autoconocimiento."],
        'career': ["Persigue proyectos en tus campos de interés.", "Investiga recursos para áreas débiles.", "Aprovecha oportunidades de mentorado y networking.", "Revisa objetivos de carrera regularmente."],
        'relationship': ["Fundamenta relaciones en comunicación abierta.", "Aplica inteligencia emocional en la vida diaria.", "Comprende tu estilo de apego.", "Invierte en conocimiento de relaciones saludables."],
        'vocation': ["Explora profesiones compatibles y gana experiencia.", "Descubre oportunidades de prácticas y observación.", "Conecta con profesionales de la industria.", "Avanza en tu carrera con paciencia."]
    },
    'ko': {
        'skills': ["실무 프로젝트를 통해 문제 해결 능력을 강화하세요.", "약점 영역에서 도움을 받으세요.", "빠른 학습 속도를 유지하세요.", "배운 내용을 다른 사람과 공유하여 강화하세요."],
        'hr': ["팀 작업에서 모범이 되세요.", "멘토링을 통해 리더십을 개발하세요.", "스트레스 관리 기법을 일상에 통합하세요.", "피드백에 대한 개방성을 습관으로 만드세요."],
        'personality': ["강점을 목표 설정에 사용하세요.", "다양한 유형을 이해하여 공감을 개발하세요.", "균형 잡힌 활동에 시간을 투자하세요.", "자기 발견에 인내심을 가지세요."],
        'career': ["관심 분야의 프로젝트를 추구하세요.", "약한 영역의 자료를 조사하세요.", "멘토링과 네트워킹 기회를 활용하세요.", "경력 목표를 정기적으로 검토하세요."],
        'relationship': ["개방적인 소통을 기반으로 관계를 맺으세요.", "일상에서 감정 지능을 적용하세요.", "당신의 애착 스타일을 이해하세요.", "건강한 관계에 대해 배우세요."],
        'vocation': ["호환되는 직업을 탐색하고 경험을 쌓으세요.", "인턴십과 관찰 기회를 찾으세요.", "전문가와 네트워크하세요.", "경력을 인내심 있게 발전시키세요."]
    },
    'ja': {
        'skills': ["実践的なプロジェクトを通じて問題解決能力を強化してください。", "弱い領域でサポートを受けてください。", "速い学習ペースを維持してください。", "学んだことを他の人と共有して強化してください。"],
        'hr': ["チームワークで模範を示し続けてください。", "メンタリングを通じてリーダーシップを開発してください。", "ストレス管理技術を日常に統合してください。", "フィードバックへのオープン性を習慣にしてください。"],
        'personality': ["強みを目標設定に使用してください。", "異なるタイプを理解して共感を構築してください。", "バランスの取れた活動に時間を投資してください。", "自己発見に忍耐力を持ってください。"],
        'career': ["興味のある分野でプロジェクトを追求してください。", "弱い領域のリソースを調査してください。", "メンタリングとネットワーキングの機会を活用してください。", "キャリア目標を定期的に見直してください。"],
        'relationship': ["オープンなコミュニケーションに基づいて関係を構築してください。", "日常生活で感情知能を適用してください。", "添付スタイルを理解してください。", "健全な関係について学ぶに投資してください。"],
        'vocation': ["互換性のある職業を探索し、経験を積んでください。", "インターンシップと観察の機会を探索してください。", "専門家とネットワークしてください。", "キャリアを辛抱強く進めてください。"]
    },
    'zh': {
        'skills': ["通过实践项目加强问题解决能力。", "不要犹豫在薄弱领域寻求支持。", "保持快速学习速度。", "通过与他人分享来巩固学习。"],
        'hr': ["继续在团队合作中树立榜样。", "通过指导来发展领导能力。", "将压力管理技术融入日常。", "使对反馈的开放成为习惯。"],
        'personality': ["将优势用于目标设定。", "通过理解不同类型来培养同理心。", "投资时间进行平衡活动。", "在自我发现中保持耐心。"],
        'career': ["在你感兴趣的领域追求项目。", "研究薄弱领域的资源。", "利用指导和人脉机会。", "定期审视职业目标。"],
        'relationship': ["以开放沟通为基础建立关系。", "在日常生活中运用情感智慧。", "了解你的依恋风格。", "学习健康关系动态。"],
        'vocation': ["探索兼容的职业并获得经验。", "探索实习和观察机会。", "与专业人士建立联系。", "耐心推进职业发展。"]
    },
    'hi': {
        'skills': ["व्यावहारिक परियोजनाओं के माध्यम से समस्या समाधान कौशल को शक्तिशाली बनाएं।", "कमजोर क्षेत्रों में समर्थन लेने से न डरें।", "तेजी से सीखने की गति बनाए रखें।", "दूसरों के साथ साझा करके सीखे हुए को मजबूत करें।"],
        'hr': ["टीम कार्य में उदाहरण प्रदान करते रहें।", "परामर्श के माध्यम से नेतृत्व विकसित करें।", "तनाव प्रबंधन तकनीकों को दैनिक जीवन में शामिल करें।", "प्रतिक्रिया के लिए खुलापन को आदत बनाएं।"],
        'personality': ["शक्तियों को लक्ष्य निर्धारण में उपयोग करें।", "विभिन्न प्रकारों को समझकर सहानुभूति विकसित करें।", "संतुलन गतिविधियों में समय निवेश करें।", "आत्म-खोज में धैर्य रखें।"],
        'career': ["अपने रुचि के क्षेत्रों में परियोजनाएं खोजें।", "कमजोर क्षेत्रों के लिए संसाधनों का अन्वेषण करें।", "परामर्श और नेटवर्किंग के अवसरों का लाभ उठाएं।", "नियमित रूप से कैरियर लक्ष्यों की समीक्षा करें।"],
        'relationship': ["खुली और ईमानदार संचार पर आधारित संबंध बनाएं।", "दैनिक जीवन में भावनात्मक बुद्धिमत्ता लागू करें।", "अपनी लगाव शैली को समझें।", "स्वस्थ रिश्ते की गतिशीलता सीखें।"],
        'vocation': ["संगत व्यवसायों की खोज करें और अनुभव प्राप्त करें।", "इंटर्नशिप और प्रशिक्षण के अवसरों की खोज करें।", "पेशेवारों के साथ नेटवर्क करें।", "अपने करियर को धैर्यपूर्वक आगे बढ़ाएं।"]
    },
    'fr': {
        'skills': ["Renforcez vos compétences en résolution de problèmes par des projets pratiques.", "N'hésitez pas à chercher du soutien dans vos domaines faibles.", "Maintenez votre rythme d'apprentissage rapide.", "Renforcez ce que vous apprenez en le partageant."],
        'hr': ["Continuez à donner l'exemple dans le travail en équipe.", "Développez le leadership par le mentorat.", "Intégrez les techniques de gestion du stress.", "Faites de l'ouverture au feedback une pratique quotidienne."],
        'personality': ["Utilisez vos forces pour la fixation d'objectifs.", "Développez l'empathie en comprenant différents types.", "Investissez du temps dans des activités d'équilibre.", "Soyez patient avec vous-même dans l'autodécouverte."],
        'career': ["Poursuivez des projets dans vos domaines d'intérêt.", "Recherchez des ressources pour les domaines faibles.", "Tirez parti des occasions de mentorat et de réseautage.", "Réexaminez régulièrement vos objectifs de carrière."],
        'relationship': ["Basez les relations sur une communication ouverte.", "Appliquez l'intelligence émotionnelle dans la vie quotidienne.", "Comprenez votre style d'attachement.", "Investissez dans la connaissance des relations saines."],
        'vocation': ["Explorez les professions compatibles et acquérez de l'expérience.", "Explorez les possibilités de stage et d'observation.", "Établissez un réseau avec des professionnels.", "Avancez dans votre carrière avec patience."]
    },
    'pt': {
        'skills': ["Fortaleça habilidades de resolução por meio de projetos práticos.", "Não hesite em buscar apoio em suas áreas fracas.", "Mantenha seu ritmo rápido de aprendizagem.", "Reforce o que aprende compartilhando com outros."],
        'hr': ["Continue dando exemplo no trabalho em equipe.", "Desenvolva liderança através de mentoria.", "Integre técnicas de gerenciamento de estresse.", "Faça abertura ao feedback uma prática diária."],
        'personality': ["Use seus pontos fortes para estabelecer metas.", "Desenvolva empatia compreendendo diferentes tipos.", "Invista tempo em atividades equilibradoras.", "Seja paciente consigo mesmo no autoconhecimento."],
        'career': ["Busque projetos em seus campos de interesse.", "Pesquise recursos para áreas fracas.", "Aproveite oportunidades de mentoria e networking.", "Revise regularmente seus objetivos de carreira."],
        'relationship': ["Base relacionamentos em comunicação aberta.", "Aplique inteligência emocional na vida cotidiana.", "Compreenda seu estilo de apego.", "Invista em conhecimento sobre relacionamentos saudáveis."],
        'vocation': ["Explore profissões compatíveis e ganhe experiência.", "Explore oportunidades de estágio e observação.", "Faça networking com profissionais.", "Avance em sua carreira com paciência."]
    },
    'bn': {
        'skills': ["ব্যবহারিক প্রকল্পের মাধ্যমে সমস্যা সমাধানের দক্ষতা শক্তিশালী করুন।", "দুর্বল ক্ষেত্রে সহায়তা চাইতে দ্বিধা করবেন না।", "দ্রুত শেখার গতি বজায় রাখুন।", "অন্যদের সাথে ভাগ করে শেখা শক্তিশালী করুন।"],
        'hr': ["দল কাজে উদাহরণ সেট করতে থাকুন।", "পরামর্শের মাধ্যমে নেতৃত্ব উন্নত করুন।", "চাপ ব্যবস্থাপনা কৌশল একীভূত করুন।", "প্রতিক্রিয়ার প্রতি খোলামেলাতা অভ্যাস করুন।"],
        'personality': ["লক্ষ্য নির্ধারণে শক্তি ব্যবহার করুন।", "বিভিন্ন ধরনের বোঝার মাধ্যমে সহানুভূতি গড়ুন।", "ভারসাম্য ক্রিয়াকলাপে সময় বিনিয়োগ করুন।", "আত্মশনাক্তিতে ধৈর্যশীল হন।"],
        'career': ["আপনার আগ্রহের ক্ষেত্রে প্রকল্প অনুসরণ করুন।", "দুর্বল ক্ষেত্রের জন্য সংস্থান গবেষণা করুন।", "পরামর্শ এবং নেটওয়ার্কিং সুযোগ ব্যবহার করুন।", "ক্যারিয়ার লক্ষ্য নিয়মিত পর্যালোচনা করুন।"],
        'relationship': ["খোলা যোগাযোগের ভিত্তিতে সম্পর্ক গড়ুন।", "দৈনন্দিন জীবনে সংবেদনশীল বুদ্ধিমত্তা প্রয়োগ করুন।", "আপনার সংযুক্তি শৈলী বুঝুন।", "সুস্থ সম্পর্ক সম্পর্কে শিখুন।"],
        'vocation': ["সামঞ্জস্যপূর্ণ পেশা অন্বেষণ করুন এবং অভিজ্ঞতা অর্জন করুন।", "ইন্টার্নশিপ এবং পর্যবেক্ষণ সুযোগ অন্বেষণ করুন।", "পেশাদারদের সাথে সংযুক্ত হন।", "আপনার ক্যারিয়ার ধৈর্যের সাথে এগিয়ে যান।"]
    },
    'id': {
        'skills': ["Perkuat keterampilan pemecahan masalah melalui proyek praktis.", "Jangan ragu untuk mencari dukungan di area yang lemah.", "Pertahankan kecepatan pembelajaran yang cepat.", "Perkuat apa yang Anda pelajari dengan berbagi."],
        'hr': ["Terus memberi contoh dalam kerja tim.", "Kembangkan kepemimpinan melalui mentoring.", "Integrasikan teknik manajemen stres.", "Jadikan keterbukaan terhadap umpan balik sebagai kebiasaan."],
        'personality': ["Gunakan kekuatan Anda untuk penetapan tujuan.", "Kembangkan empati dengan memahami tipe yang berbeda.", "Investasikan waktu dalam kegiatan yang seimbang.", "Bersabarlah dengan diri sendiri dalam penemuan diri."],
        'career': ["Kejar proyek di bidang yang Anda minati.", "Teliti sumber daya untuk area yang lemah.", "Manfaatkan peluang mentoring dan jaringan.", "Tinjau tujuan karir secara teratur."],
        'relationship': ["Dasarkan hubungan pada komunikasi terbuka.", "Terapkan kecerdasan emosional dalam kehidupan sehari-hari.", "Pahami gaya lampiran Anda.", "Berinvestasi dalam pengetahuan hubungan yang sehat."],
        'vocation': ["Jelajahi profesi yang kompatibel dan dapatkan pengalaman.", "Jelajahi peluang magang dan observasi.", "Jaringan dengan profesional.", "Majukan karir Anda dengan sabar."]
    },
    'ur': {
        'skills': ["عملی منصوبوں کے ذریعے مسئلہ حل کرنے کی مہارت کو بہتر بنائیں۔", "کمزور علاقوں میں مدد حاصل کرنے میں ہچکچاہٹ نہ کریں۔", "تیزی سے سیکھنے کی رفتار برقرار رکھیں۔", "دوسروں کے ساتھ شیئر کر کے سیکھے ہوئے کو مضبوط کریں۔"],
        'hr': ["ٹیم ورک میں مثال دیتے رہیں۔", "سفارش کاری کے ذریعے قیادت کی ترقی کریں۔", "تناؤ کے انتظام کی تکنیکیں شامل کریں۔", "تنقید کے لیے کھلاپن کو عادت بنائیں۔"],
        'personality': ["مقصد کے تعین میں اپنی طاقتوں کا استعمال کریں۔", "مختلف اقسام کو سمجھ کر ہمدردی بڑھائیں۔", "متوازن سرگرمیوں میں وقت لگائیں۔", "خود شناخت میں صبر سے کام لیں۔"],
        'career': ["اپنے دلچسپی کے شعبوں میں منصوبے تلاش کریں۔", "کمزور علاقوں کے لیے وسائل کی تحقیق کریں۔", "سفارش کاری اور نیٹ ورکنگ کے مواقع سے فائدہ اٹھائیں۔", "باقاعدگی سے کیریئر کے مقاصد کا جائزہ لیں۔"],
        'relationship': ["کھلی رابطے پر پیش آنے والے تعلقات پر بنیاد رکھیں۔", "روز مرہ کی زندگی میں جذباتی ذہانت کا اطلاق کریں۔", "اپنے تعلق کی شوق کو سمجھیں۔", "صحت مند تعلقات کے بارے میں جانیں۔"],
        'vocation': ["موافق پیشے تلاش کریں اور تجربہ حاصل کریں۔", "انٹرن شپ اور مراقبت کے مواقع تلاش کریں۔", "پیشہ ور حضرات سے رابطہ کریں۔", "اپنے کیریئر کو صبر سے آگے بڑھائیں۔"]
    },
    'it': {
        'skills': ["Rafforza le abilità di risoluzione attraverso progetti pratici.", "Non esitare a cercare supporto nelle aree deboli.", "Mantieni il tuo ritmo di apprendimento veloce.", "Rinforza ciò che impari condividendolo con altri."],
        'hr': ["Continua a essere un esempio nel lavoro di squadra.", "Sviluppa la leadership attraverso il mentoring.", "Integra le tecniche di gestione dello stress.", "Rendi l'apertura al feedback un'abitudine quotidiana."],
        'personality': ["Usa i tuoi punti di forza per la definizione degli obiettivi.", "Sviluppa l'empatia comprendendo tipi diversi.", "Investi tempo in attività equilibranti.", "Sii paziente con te stesso nell'autodiscovery."],
        'career': ["Persegui progetti nei tuoi campi di interesse.", "Ricerca risorse per aree deboli.", "Sfrutta le opportunità di mentoring e networking.", "Rivedi regolarmente gli obiettivi di carriera."],
        'relationship': ["Basa le relazioni sulla comunicazione aperta.", "Applica l'intelligenza emotiva nella vita quotidiana.", "Comprendi il tuo stile di attaccamento.", "Investi nella conoscenza dei rapporti sani."],
        'vocation': ["Esplora professioni compatibili e acquisisci esperienza.", "Esplora opportunità di stage e osservazione.", "Fai networking con professionisti.", "Avanza nella tua carriera con pazienza."]
    },
    'vi': {
        'skills': ["Tăng cường kỹ năng giải quyết vấn đề qua các dự án thực tế.", "Đừng ngần ngại tìm kiếm sự hỗ trợ ở những lĩnh vực yếu.", "Duy trì tốc độ học tập nhanh của bạn.", "Củng cố những gì bạn học bằng cách chia sẻ."],
        'hr': ["Tiếp tục làm gương trong làm việc nhóm.", "Phát triển khả năng lãnh đạo thông qua hướng dẫn.", "Tích hợp các kỹ thuật quản lý căng thẳng.", "Hãy coi sự mở cửa với phản hồi là thói quen."],
        'personality': ["Sử dụng sức mạnh của bạn để đặt mục tiêu.", "Phát triển sự thông cảm bằng cách hiểu các loại khác nhau.", "Đầu tư thời gian vào các hoạt động cân bằng.", "Hãy kiên nhẫn với chính mình trong khám phá bản thân."],
        'career': ["Theo đuổi dự án trong các lĩnh vực quan tâm của bạn.", "Tìm kiếm tài nguyên cho những lĩnh vực yếu.", "Tận dụng cơ hội hướng dẫn và mạng lưới.", "Xem xét thường xuyên các mục tiêu sự nghiệp."],
        'relationship': ["Dựa vào giao tiếp cởi mở trong mối quan hệ.", "Áp dụng trí tuệ cảm xúc trong cuộc sống hàng ngày.", "Hiểu phong cách gắn bó của bạn.", "Đầu tư vào kiến thức về các mối quan hệ lành mạnh."],
        'vocation': ["Khám phá các nghề phù hợp và có được kinh nghiệm.", "Khám phá cơ hội thực tập và quan sát.", "Kết nối với các chuyên gia.", "Nâng cao sự nghiệp của bạn một cách kiên nhẫn."]
    },
    'pl': {
        'skills': ["Wzmocnij umiejętności rozwiązywania problemów poprzez projekty praktyczne.", "Nie wahaj się szukać pomocy w słabych obszarach.", "Zachowaj szybkie tempo nauki.", "Wzmocnij to, co się uczysz, dzieląc się z innymi."],
        'hr': ["Nadal dawaj przykład w pracy zespołowej.", "Rozwijaj umiejętności przywódcze poprzez mentoring.", "Integruj techniki zarządzania stresem.", "Uczyń otwartość na informacje zwrotne nawykiem."],
        'personality': ["Używaj swoich mocnych stron do ustalania celów.", "Rozwijaj empatię, rozumiejąc różne typy.", "Inwestuj czas w działania wyrównujące.", "Bądź cierpliwy z sobą w odkrywaniu siebie."],
        'career': ["Realizuj projekty w swoich dziedzinach zainteresowań.", "Badaj zasoby dla słabych obszarów.", "Korzystaj z okazji mentoringu i networkingu.", "Regularnie przeglądaj cele zawodowe."],
        'relationship': ["Opieraj relacje na otwartej komunikacji.", "Stosuj inteligencję emocjonalną w codziennym życiu.", "Rozumiej swój styl przywiązania.", "Inwestuj w wiedzę o zdrowymi relacjach."],
        'vocation': ["Poszukuj zgodnych zawodów i zdobywaj doświadczenie.", "Poszukuj okazji praktyk i obserwacji.", "Nawiąż kontakty z profesjonalistami.", "Zaawansuj swoją karierę z cierpliwością."]
    }
}


# ── Fill missing test-type entries for all 18 languages ──────────────────────
_FALLBACK_SUPPLEMENT: dict = {
    'attachment': {
        'tr': ["Bağlanma stilinizi anlamak ilişki kalitesini artırır.", "Güvenli bağlanma geliştirmek için güvenilir kişilerle bağı derinleştirin.", "Kaygılı bağlanma paternlerini fark ettiğinizde kendinize şefkatle yaklaşın.", "Terapist veya bilinçli pratiklerle bağlanma yaraları üzerinde çalışın."],
        'en': ["Understanding your attachment style can improve relationship quality.", "Deepen bonds with trustworthy people to cultivate secure attachment.", "When you notice anxious patterns, approach yourself with compassion.", "Work on attachment wounds through therapy or mindful practices."],
        'de': ["Ihr Bindungsstil zu verstehen verbessert die Beziehungsqualität.", "Vertiefen Sie Bindungen mit vertrauenswürdigen Menschen.", "Bei ängstlichen Bindungsmustern gehen Sie mitfühlend mit sich um.", "Bearbeiten Sie Bindungswunden durch Therapie oder Achtsamkeitspraxis."],
        'ru': ["Понимание стиля привязанности улучшает качество отношений.", "Углубляйте связи с надёжными людьми для безопасной привязанности.", "Замечая тревожные паттерны, относитесь к себе с состраданием.", "Работайте с ранами привязанности через терапию или осознанность."],
        'ar': ["فهم أسلوب تعلقك يحسن جودة العلاقات.", "عمّق الروابط مع أشخاص موثوقين لتنمية التعلق الآمن.", "حين تلاحظ أنماط التعلق القلق، عامل نفسك برحمة.", "اعمل على جروح التعلق عبر العلاج أو الممارسات الواعية."],
        'es': ["Entender tu estilo de apego mejora la calidad de las relaciones.", "Profundiza vínculos con personas de confianza para cultivar apego seguro.", "Cuando notes patrones de apego ansioso, trátate con compasión.", "Trabaja las heridas de apego mediante terapia o prácticas conscientes."],
        'ko': ["자신의 애착 유형을 이해하면 관계의 질이 향상됩니다.", "안전한 애착을 키우려면 신뢰할 수 있는 사람과의 유대를 깊이 하세요.", "불안한 애착 패턴을 인식할 때 자신에게 연민으로 다가가세요.", "치료나 마음챙김을 통해 애착 상처를 치유하세요."],
        'ja': ["愛着スタイルを理解することで関係の質が向上します。", "安全な愛着を育てるために信頼できる人との絆を深めてください。", "不安な愛着パターンに気づいたら自分に思いやりを持ってください。", "療法やマインドフルネスで愛着の傷に取り組んでください。"],
        'zh': ["了解自己的依恋风格可以改善关系质量。", "与可信赖的人深化联系，培养安全型依恋。", "当注意到焦虑型依恋模式时，以同情心对待自己。", "通过心理治疗或正念练习处理依恋创伤。"],
        'hi': ["अपनी संलग्नता शैली को समझने से संबंध की गुणवत्ता में सुधार होता है।", "सुरक्षित संलग्नता विकसित करने के लिए भरोसेमंद लोगों के साथ बंधन गहरा करें।", "चिंतित पैटर्न देखें तो अपने आप से करुणा के साथ पेश आएं।", "थेरेपी या सचेत प्रथाओं के माध्यम से संलग्नता के घावों पर काम करें।"],
        'fr': ["Comprendre votre style d'attachement améliore la qualité des relations.", "Approfondissez les liens avec des personnes de confiance pour un attachement sécurisé.", "Lorsque vous remarquez des patterns d'attachement anxieux, approchez-vous avec compassion.", "Travaillez sur les blessures d'attachement par la thérapie ou des pratiques conscientes."],
        'pt': ["Entender seu estilo de apego melhora a qualidade dos relacionamentos.", "Aprofunde laços com pessoas confiáveis para cultivar apego seguro.", "Quando notar padrões de apego ansioso, trate-se com compaixão.", "Trabalhe as feridas de apego por meio de terapia ou práticas conscientes."],
        'bn': ["আপনার সংযুক্তি শৈলী বোঝা সম্পর্কের গুণমান উন্নত করে।", "নিরাপদ সংযুক্তি গড়তে বিশ্বস্ত মানুষদের সাথে বন্ধন গভীর করুন।", "উদ্বিগ্ন সংযুক্তি প্যাটার্ন লক্ষ্য করলে সহানুভূতির সাথে নিজের সাথে আচরণ করুন।", "থেরাপি বা সচেতন অনুশীলনের মাধ্যমে সংযুক্তির ক্ষত নিয়ে কাজ করুন।"],
        'id': ["Memahami gaya kelekatan meningkatkan kualitas hubungan.", "Perdalam ikatan dengan orang terpercaya untuk menumbuhkan kelekatan aman.", "Ketika Anda memperhatikan pola kelekatan cemas, dekati diri sendiri dengan welas asih.", "Kerjakan luka kelekatan melalui terapi atau praktik penuh kesadaran."],
        'ur': ["اپنی لگاؤ کی طرز کو سمجھنا رشتوں کی معیار کو بہتر بناتا ہے۔", "محفوظ لگاؤ پروان چڑھانے کے لیے قابلِ اعتماد لوگوں کے ساتھ تعلق گہرا کریں۔", "پریشانی کے لگاؤ کے نمونے دیکھیں تو اپنے آپ سے ہمدردی سے پیش آئیں۔", "تھراپی یا باشعور مشقوں کے ذریعے لگاؤ کے زخموں پر کام کریں۔"],
        'it': ["Capire il tuo stile di attaccamento migliora la qualità delle relazioni.", "Approfondisci i legami con persone fidate per coltivare un attaccamento sicuro.", "Quando noti schemi di attaccamento ansioso, approcciati con compassione.", "Lavora sulle ferite di attaccamento attraverso la terapia o pratiche consapevoli."],
        'vi': ["Hiểu phong cách gắn bó của bạn có thể cải thiện chất lượng các mối quan hệ.", "Làm sâu sắc mối liên kết với những người đáng tin cậy để nuôi dưỡng sự gắn bó an toàn.", "Khi nhận thấy các mẫu gắn bó lo lắng, hãy tiếp cận bản thân với lòng từ bi.", "Giải quyết các vết thương gắn bó qua liệu pháp hoặc thực hành chánh niệm."],
        'pl': ["Zrozumienie stylu przywiązania poprawia jakość relacji.", "Pogłębiaj więzi z zaufanymi osobami, by kultywować bezpieczne przywiązanie.", "Gdy zauważysz lękowe wzorce przywiązania, podejdź do siebie ze współczuciem.", "Pracuj nad ranami przywiązania poprzez terapię lub uważność."],
    },
    'grit': {
        'de': ["Baue die Gewohnheit auf, bei Schwierigkeiten nicht aufzugeben.", "Stärke das Engagement für langfristige Ziele mit konkreten Meilensteinen.", "Vertiefe deine Interessen, um Beständigkeit und Fokus zu entwickeln.", "Feiere jeden kleinen Fortschritt, um deine Motivation aufrechtzuerhalten."],
        'ru': ["Выработайте привычку не сдаваться при трудностях.", "Укрепляйте приверженность долгосрочным целям конкретными вехами.", "Углубляйте интересы для развития последовательности и концентрации.", "Отмечайте каждый маленький прогресс, чтобы поддерживать мотивацию."],
        'ar': ["طوّر عادة الاستمرار في مواجهة الصعوبات دون التخلي.", "عزز الالتزام بالأهداف طويلة المدى بمعالم ملموسة.", "عمّق اهتماماتك لتطوير الاتساق والتركيز.", "احتفل بكل تقدم صغير للحفاظ على تحفيزك."],
        'es': ["Construye el hábito de persistir ante las dificultades sin rendirse.", "Refuerza el compromiso con objetivos a largo plazo con hitos concretos.", "Profundiza en tus intereses para desarrollar consistencia y enfoque.", "Celebra cada pequeño progreso para mantener tu motivación."],
        'ko': ["어려움을 포기하지 않고 계속하는 습관을 만드세요.", "구체적인 이정표로 장기 목표에 대한 헌신을 강화하세요.", "일관성과 집중력을 개발하기 위해 관심사를 심화하세요.", "작은 진전을 축하하여 동기를 유지하세요."],
        'ja': ["困難に諦めず続ける習慣を築いてください。", "具体的なマイルストーンで長期目標へのコミットメントを強化してください。", "一貫性と集中力を育てるために興味を深めてください。", "モチベーションを維持するために小さな進歩を祝ってください。"],
        'zh': ["培养在困难中坚持不放弃的习惯。", "用具体里程碑强化对长期目标的承诺。", "深化你的兴趣以培养一致性和专注力。", "庆祝每一个小进步，保持你的动力。"],
        'hi': ["कठिनाइयों में हार न मानते हुए जारी रखने की आदत बनाएं।", "ठोस मील के पत्थर के साथ दीर्घकालिक लक्ष्यों के प्रति प्रतिबद्धता मजबूत करें।", "निरंतरता और ध्यान विकसित करने के लिए अपनी रुचियों को गहरा करें।", "प्रेरणा बनाए रखने के लिए हर छोटी प्रगति का जश्न मनाएं।"],
        'fr': ["Cultivez l'habitude de persévérer face aux difficultés sans abandonner.", "Renforcez l'engagement envers les objectifs à long terme avec des jalons concrets.", "Approfondissez vos intérêts pour développer cohérence et concentration.", "Célébrez chaque petite avancée pour maintenir votre motivation."],
        'pt': ["Construa o hábito de persistir nas dificuldades sem desistir.", "Reforce o compromisso com objetivos de longo prazo com marcos concretos.", "Aprofunde seus interesses para desenvolver consistência e foco.", "Celebre cada pequeno progresso para manter sua motivação."],
        'bn': ["কঠিনতায় হাল না ছেড়ে অব্যাহত থাকার অভ্যাস গড়ুন।", "সুনির্দিষ্ট মাইলস্টোন দিয়ে দীর্ঘমেয়াদী লক্ষ্যের প্রতি প্রতিশ্রুতি শক্তিশালী করুন।", "ধারাবাহিকতা ও মনোযোগ বিকাশ করতে আগ্রহ গভীর করুন।", "অনুপ্রেরণা জীবিত রাখতে প্রতিটি ছোট অগ্রগতি উদযাপন করুন।"],
        'id': ["Bangun kebiasaan bertahan menghadapi kesulitan tanpa menyerah.", "Perkuat komitmen pada tujuan jangka panjang dengan tonggak konkret.", "Perdalam minat Anda untuk mengembangkan konsistensi dan fokus.", "Rayakan setiap kemajuan kecil untuk menjaga motivasi Anda."],
        'ur': ["مشکلات میں ہار نہ مانتے ہوئے جاری رہنے کی عادت بنائیں۔", "ٹھوس سنگ میل کے ساتھ طویل مدتی اہداف کے لیے عزم کو مضبوط کریں۔", "ہم آہنگی اور توجہ پیدا کرنے کے لیے اپنی دلچسپیوں کو گہرا کریں۔", "تحریک کو زندہ رکھنے کے لیے ہر چھوٹی پیشرفت کا جشن منائیں۔"],
        'it': ["Costruisci l'abitudine di persistere nelle difficoltà senza arrenderti.", "Rafforza l'impegno verso gli obiettivi a lungo termine con traguardi concreti.", "Approfondisci i tuoi interessi per sviluppare coerenza e concentrazione.", "Festeggia ogni piccolo progresso per mantenere la motivazione."],
        'vi': ["Xây dựng thói quen kiên trì vượt qua khó khăn mà không bỏ cuộc.", "Củng cố cam kết với các mục tiêu dài hạn bằng các cột mốc cụ thể.", "Đào sâu sở thích để phát triển sự nhất quán và tập trung.", "Ăn mừng mỗi tiến bộ nhỏ để duy trì động lực."],
        'pl': ["Buduj nawyk wytrwania przez trudności bez poddawania się.", "Wzmacniaj zaangażowanie w długoterminowe cele konkretnymi kamieniami milowymi.", "Pogłębiaj swoje zainteresowania, aby rozwijać spójność i skupienie.", "Świętuj każdy mały postęp, aby utrzymać motywację."],
    },
    'growth_mindset': {
        'de': ["Betrachte Rückschläge als Lernmöglichkeiten, nicht als Misserfolge.", "Ersetze 'Das kann ich nicht' durch 'Das kann ich noch nicht'.", "Begrüße Feedback, das auf Anstrengung und Strategie ausgerichtet ist.", "Übe tägliche Erinnerungen, dass Fähigkeiten durch Arbeit entwickelt werden können."],
        'ru': ["Переосмыслите неудачи как возможности для обучения.", "Замените 'Я не могу' на 'Я ещё не могу'.", "Приветствуйте обратную связь, ориентированную на усилия и стратегию.", "Практикуйте ежедневные напоминания о том, что способности можно развить."],
        'ar': ["أعد صياغة الانتكاسات كفرص تعلم لا كإخفاقات.", "استبدل 'لا أستطيع' بـ 'لا أستطيع بعد'.", "رحّب بالملاحظات المركزة على الجهد والاستراتيجية.", "تدرّب على تذكيرات يومية بأن القدرات تتطور مع العمل."],
        'es': ["Reformula los retrocesos como oportunidades de aprendizaje.", "Reemplaza 'No puedo' por 'Aún no puedo'.", "Recibe con agrado el feedback sobre esfuerzo y estrategia.", "Practica recordatorios diarios de que las habilidades se desarrollan con el trabajo."],
        'ko': ["실패를 학습 기회로 재구성하세요.", "'할 수 없다'를 '아직 못 한다'로 바꾸세요.", "노력과 전략에 중점을 둔 피드백을 환영하세요.", "능력은 노력으로 발전할 수 있다는 것을 매일 상기하는 연습을 하세요."],
        'ja': ["挫折を失敗ではなく学びの機会として捉えてください。", "「できない」を「まだできない」に置き換えてください。", "努力と戦略に焦点を当てたフィードバックを歓迎してください。", "能力は努力で伸ばせるという日々の確認を練習してください。"],
        'zh': ["将挫折视为学习机会而非失败。", "将'我做不到'改为'我还做不到'。", "欢迎关注努力和策略的反馈。", "每天练习提醒自己能力可以通过努力培养。"],
        'hi': ["असफलताओं को सीखने के अवसर के रूप में पुनः संरचित करें।", "'मैं यह नहीं कर सकता' को 'मैं यह अभी तक नहीं कर सका' से बदलें।", "प्रयास और रणनीति पर केंद्रित प्रतिक्रिया का स्वागत करें।", "रोज याद दिलाएं कि क्षमताएं मेहनत से विकसित की जा सकती हैं।"],
        'fr': ["Recadrez les revers comme des opportunités d'apprentissage.", "Remplacez 'Je ne peux pas' par 'Je ne peux pas encore'.", "Accueillez les retours axés sur l'effort et la stratégie.", "Pratiquez des rappels quotidiens que les capacités se développent avec le travail."],
        'pt': ["Reformule retrocessos como oportunidades de aprendizado.", "Substitua 'Não consigo' por 'Ainda não consigo'.", "Receba bem o feedback focado em esforço e estratégia.", "Pratique lembretes diários de que habilidades se desenvolvem com esforço."],
        'bn': ["পিছুটানকে ব্যর্থতা নয়, শেখার সুযোগ হিসেবে দেখুন।", "'পারব না' কে 'এখনও পারিনি' দিয়ে প্রতিস্থাপন করুন।", "প্রচেষ্টা ও কৌশলে মনোযোগী প্রতিক্রিয়াকে স্বাগত জানান।", "প্রতিদিন মনে করিয়ে দিন যে যোগ্যতা পরিশ্রম দিয়ে বিকশিত হয়।"],
        'id': ["Framing ulang kemunduran sebagai peluang belajar bukan kegagalan.", "Ganti 'Saya tidak bisa' dengan 'Saya belum bisa'.", "Sambut umpan balik yang berfokus pada upaya dan strategi.", "Latih pengingat harian bahwa kemampuan dapat dikembangkan dengan kerja keras."],
        'ur': ["ناکامیوں کو بربادی نہیں بلکہ سیکھنے کے مواقع کے طور پر دیکھیں۔", "'میں نہیں کر سکتا' کو 'میں ابھی تک نہیں کر سکتا' سے بدل دیں۔", "کوشش اور حکمت عملی پر مرکوز تاثرات کا خیرمقدم کریں۔", "روزانہ یاد دلائیں کہ صلاحیتیں محنت سے پروان چڑھ سکتی ہیں۔"],
        'it': ["Inquadra i rovesci come opportunità di apprendimento, non fallimenti.", "Sostituisci 'Non posso farlo' con 'Non posso ancora farlo'.", "Dai il benvenuto al feedback focalizzato su sforzo e strategia.", "Pratica promemoria quotidiani che le capacità si sviluppano con il lavoro."],
        'vi': ["Tái định khung những thất bại là cơ hội học hỏi, không phải thất bại.", "Thay 'Tôi không thể' bằng 'Tôi chưa thể'.", "Đón nhận phản hồi tập trung vào nỗ lực và chiến lược.", "Thực hành nhắc nhở hàng ngày rằng khả năng có thể phát triển qua công việc."],
        'pl': ["Przekształć porażki w możliwości uczenia się.", "Zamień 'Nie potrafię' na 'Jeszcze nie potrafię'.", "Przyjmuj z otwartością informacje zwrotne skupione na wysiłku i strategii.", "Ćwicz codzienne przypomnienia, że zdolności rozwijają się dzięki pracy."],
    },
    'life_satisfaction': {
        'de': ["Führe ein Dankbarkeitstagebuch, um Positives wahrzunehmen.", "Mache kleine Schritte, um die Lücke zwischen deinen Werten und deinem Leben zu schließen.", "Verbringe mehr Zeit mit wertorientierten Aktivitäten.", "Investiere in sinnvolle Beziehungen und Erfahrungen."],
        'ru': ["Ведите дневник благодарности для замечания позитивного.", "Делайте маленькие шаги для сближения ценностей и жизни.", "Проводите больше времени в ценностно-совместимых занятиях.", "Инвестируйте в значимые отношения и опыт."],
        'ar': ["احتفظ بيومية الامتنان لتلاحظ الإيجابيات في حياتك.", "اتخذ خطوات صغيرة لسد الفجوة بين قيمك وحياتك.", "أمضِ وقتاً أكثر في أنشطة تتوافق مع قيمك.", "استثمر في علاقات ذات معنى لتعزيز الرضا."],
        'es': ["Lleva un diario de gratitud para notar los aspectos positivos.", "Da pequeños pasos para cerrar la brecha entre tus valores y tu vida.", "Dedica más tiempo a actividades alineadas con tus valores.", "Invierte en relaciones y experiencias significativas."],
        'ko': ["삶의 긍정적인 면을 인식하기 위해 감사 일기를 쓰세요.", "가치관과 현재 삶의 격차를 줄이기 위한 작은 조치를 취하세요.", "핵심 가치에 맞는 활동에 더 많은 시간을 투자하세요.", "의미 있는 관계와 경험에 투자하여 충족감을 높이세요."],
        'ja': ["人生のポジティブな面を見つけるために感謝の日記をつけてください。", "価値観と現在の生活のギャップを縮める小さな一歩を踏み出してください。", "コアバリューに合う活動にもっと時間を使ってください。", "充実感を高めるために意義ある関係や経験に投資してください。"],
        'zh': ["写感恩日记，注意生活中的积极方面。", "采取小步骤缩小你的价值观与现实生活之间的差距。", "将更多时间花在与你核心价值观一致的活动上。", "投资于有意义的关系和经历以增强满足感。"],
        'hi': ["जीवन के सकारात्मक पहलुओं को नोटिस करने के लिए कृतज्ञता पत्रिका रखें।", "अपने मूल्यों और वर्तमान जीवन के बीच की खाई को बंद करने के लिए छोटे कदम उठाएं।", "अपने मूल मूल्यों के अनुरूप गतिविधियों पर अधिक समय बिताएं।", "पूर्णता बढ़ाने के लिए अर्थपूर्ण संबंधों और अनुभवों में निवेश करें।"],
        'fr': ["Tenez un journal de gratitude pour noter les aspects positifs.", "Faites de petits pas pour combler l'écart entre vos valeurs et votre vie.", "Passez plus de temps sur des activités alignées avec vos valeurs.", "Investissez dans des relations et expériences significatives."],
        'pt': ["Mantenha um diário de gratidão para notar os aspectos positivos.", "Dê pequenos passos para fechar a lacuna entre seus valores e sua vida.", "Passe mais tempo em atividades alinhadas com seus valores.", "Invista em relacionamentos e experiências significativas."],
        'bn': ["জীবনের ইতিবাচক দিকগুলো লক্ষ্য করতে কৃতজ্ঞতার জার্নাল রাখুন।", "আপনার মূল্যবোধ ও বর্তমান জীবনের মধ্যে ব্যবধান কমাতে ছোট পদক্ষেপ নিন।", "মূল মূল্যবোধের সাথে সামঞ্জস্যপূর্ণ কার্যক্রমে বেশি সময় ব্যয় করুন।", "পরিপূর্ণতা বাড়াতে অর্থবহ সম্পর্ক ও অভিজ্ঞতায় বিনিয়োগ করুন।"],
        'id': ["Simpan jurnal syukur untuk memperhatikan sisi positif hidup Anda.", "Ambil langkah kecil untuk mempersempit kesenjangan antara nilai dan kehidupan.", "Habiskan lebih banyak waktu untuk kegiatan yang selaras dengan nilai-nilai Anda.", "Investasikan dalam hubungan dan pengalaman bermakna."],
        'ur': ["زندگی کے مثبت پہلوؤں کو نوٹ کرنے کے لیے شکر گزاری کی ڈائری رکھیں۔", "اپنی اقدار اور موجودہ زندگی کے درمیان خلاء کو کم کرنے کے لیے چھوٹے قدم اٹھائیں۔", "اپنی بنیادی اقدار کے مطابق سرگرمیوں پر زیادہ وقت گزاریں۔", "تسکین بڑھانے کے لیے بامعنی رشتوں اور تجربوں میں سرمایہ کاری کریں۔"],
        'it': ["Tieni un diario della gratitudine per notare gli aspetti positivi.", "Fai piccoli passi per colmare il divario tra i tuoi valori e la tua vita.", "Dedica più tempo alle attività in linea con i tuoi valori.", "Investi in relazioni ed esperienze significative."],
        'vi': ["Giữ nhật ký biết ơn để nhận thấy những mặt tích cực trong cuộc sống.", "Thực hiện những bước nhỏ để thu hẹp khoảng cách giữa giá trị và cuộc sống.", "Dành nhiều thời gian hơn cho các hoạt động phù hợp với giá trị cốt lõi.", "Đầu tư vào các mối quan hệ và trải nghiệm có ý nghĩa."],
        'pl': ["Prowadź dziennik wdzięczności, aby zauważać pozytywy.", "Rób małe kroki, by zmniejszyć lukę między wartościami a życiem.", "Poświęcaj więcej czasu działaniom zgodnym z twoimi wartościami.", "Inwestuj w znaczące relacje i doświadczenia."],
    },
    'self_compassion': {
        'de': ["Spreche mit dir mit der gleichen Güte wie mit einem guten Freund.", "Übe, Fehler als Teil menschlicher Erfahrung zu betrachten.", "Tröste dich in schwierigen Momenten mit einer unterstützenden inneren Stimme.", "Beobachte Gefühle achtsam statt sie zu unterdrücken."],
        'ru': ["Разговаривайте с собой с той же добротой, что и с другом.", "Учитесь воспринимать ошибки как часть общего человеческого опыта.", "В трудные моменты поддерживайте себя благосклонным внутренним голосом.", "Наблюдайте за эмоциями осознанно, не подавляя их."],
        'ar': ["تحدث إلى نفسك بنفس اللطف الذي تقدمه لصديق.", "تدرّب على رؤية أخطائك كجزء من التجربة الإنسانية المشتركة.", "في اللحظات الصعبة، وازِ نفسك بصوت داخلي داعم.", "راقب مشاعرك بوعي بدلاً من قمعها."],
        'es': ["Habla contigo mismo con la misma amabilidad que a un buen amigo.", "Practica ver tus errores como parte de la experiencia humana compartida.", "En momentos difíciles, consuélate con una voz interior de apoyo.", "Observa las emociones conscientemente en lugar de suprimirlas."],
        'ko': ["좋은 친구에게 하듯 자신에게 친절하게 말하세요.", "자신의 실수를 공유된 인간 경험의 일부로 보는 연습을 하세요.", "어려운 순간에 지지하는 내면의 목소리로 자신을 위로하세요.", "감정을 억누르지 말고 마음챙김으로 관찰하세요."],
        'ja': ["よい友人に接するように、自分自身に親切に語りかけてください。", "自分のミスを共通の人間経験の一部として見る練習をしてください。", "困難な瞬間、支持的な内なる声で自分を慰めてください。", "感情を抑えるのではなく、マインドフルに観察してください。"],
        'zh': ["用对好朋友的同等善意与自己交谈。", "练习将错误视为共同人类经历的一部分。", "在困难时刻，用支持性的内心声音安慰自己。", "正念地观察情绪而不是压制它们。"],
        'hi': ["अपने आप से उसी दयालुता से बोलें जो आप एक अच्छे मित्र को देंगे।", "अपनी गलतियों को साझा मानव अनुभव का हिस्सा देखने का अभ्यास करें।", "कठिन पलों में एक सहायक आंतरिक आवाज से खुद को सांत्वना दें।", "भावनाओं को दबाने की बजाय सचेतन रूप से देखें।"],
        'fr': ["Parlez-vous avec la même gentillesse que vous offririez à un bon ami.", "Pratiquez voir vos erreurs comme une expérience humaine partagée.", "Dans les moments difficiles, réconfortez-vous avec une voix intérieure bienveillante.", "Observez les émotions avec pleine conscience plutôt que de les réprimer."],
        'pt': ["Fale consigo mesmo com a mesma bondade que ofereceria a um bom amigo.", "Pratique ver seus erros como parte da experiência humana compartilhada.", "Em momentos difíceis, conforte-se com uma voz interior de apoio.", "Observe emoções com atenção plena em vez de suprimi-las."],
        'bn': ["নিজের সাথে একজন ভালো বন্ধুকে যে সদয়তা দেন সেভাবে কথা বলুন।", "নিজের ভুলকে মানবিক অভিজ্ঞতার অংশ হিসেবে দেখার অনুশীলন করুন।", "কঠিন মুহূর্তে সহায়ক আভ্যন্তরীণ কণ্ঠস্বর দিয়ে নিজেকে সান্ত্বনা দিন।", "আবেগ দমন করার পরিবর্তে সচেতনভাবে পর্যবেক্ষণ করুন।"],
        'id': ["Berbicaralah pada diri sendiri dengan kebaikan yang sama seperti untuk teman baik.", "Latih diri melihat kesalahan sebagai bagian dari pengalaman manusia bersama.", "Di saat sulit, hibur diri dengan suara batin yang mendukung.", "Amati emosi dengan penuh kesadaran, bukan menekannya."],
        'ur': ["اپنے آپ سے اسی محبت سے بات کریں جو آپ کسی اچھے دوست کو دیتے ہیں۔", "اپنی غلطیوں کو مشترکہ انسانی تجربے کا حصہ دیکھنے کی مشق کریں۔", "مشکل لمحات میں ایک حمایتی اندرونی آواز سے اپنے آپ کو تسلی دیں۔", "جذبات کو دبانے کی بجائے ذہن سازی سے مشاہدہ کریں۔"],
        'it': ["Parlate con voi stessi con la stessa gentilezza che offrireste a un buon amico.", "Praticate a vedere i vostri errori come parte dell'esperienza umana condivisa.", "Nei momenti difficili, confortatevi con una voce interiore di supporto.", "Osservate le emozioni con consapevolezza invece di sopprimerle."],
        'vi': ["Nói chuyện với bản thân với sự tử tế như bạn dành cho một người bạn tốt.", "Thực hành nhìn nhận sai lầm là một phần của trải nghiệm con người chung.", "Trong những lúc khó khăn, hãy an ủi bản thân bằng giọng nói nội tâm hỗ trợ.", "Quan sát cảm xúc một cách chú tâm thay vì kìm nén chúng."],
        'pl': ["Rozmawiaj z sobą z taką samą życzliwością, jaką oferujesz dobremu przyjacielowi.", "Ćwicz postrzeganie błędów jako część wspólnego ludzkiego doświadczenia.", "W trudnych chwilach pocieszaj się wspierającym wewnętrznym głosem.", "Obserwuj emocje uważnie zamiast je tłumić."],
    },
    'self_efficacy': {
        'de': ["Steigere schrittweise das Selbstvertrauen durch Meistern kleiner Herausforderungen.", "Reflektiere regelmäßig über vergangene Schwierigkeiten, die du überwunden hast.", "Übernehme den Ansatz eines Mentors oder Vorbilds.", "In unsicheren Situationen baue Kontrolle durch Schritt-für-Schritt-Aktionspläne auf."],
        'ru': ["Постепенно повышайте уверенность, преодолевая небольшие вызовы.", "Регулярно размышляйте о прошлых трудностях, которые вы преодолели.", "Перенимайте подход наставника или образца для подражания.", "В неопределённых ситуациях стройте контроль пошаговыми планами."],
        'ar': ["زِد الثقة تدريجيًا بإتقان التحديات الصغيرة أولاً.", "تأمل بانتظام في الصعوبات الماضية التي تغلبت عليها.", "تبنَّ نهج مرشد أو قدوة تثق به.", "في المواقف الغامضة، ابنِ التحكم بخطط عملية خطوة خطوة."],
        'es': ["Aumenta gradualmente la confianza dominando pequeños desafíos primero.", "Reflexiona regularmente sobre dificultades pasadas que hayas superado.", "Adopta el enfoque de un mentor o modelo a seguir.", "En situaciones inciertas, construye control con planes de acción paso a paso."],
        'ko': ["작은 도전을 먼저 극복하여 점진적으로 자신감을 높이세요.", "성공적으로 극복한 과거 어려움을 정기적으로 되돌아보세요.", "신뢰하는 멘토나 롤모델의 접근 방식을 채택하세요.", "불확실한 상황에서는 단계별 행동 계획으로 통제력을 키우세요."],
        'ja': ["小さな課題をマスターすることで徐々に自信を高めてください。", "成功裏に乗り越えた過去の困難を定期的に振り返ってください。", "信頼するメンターやロールモデルのアプローチを採用してください。", "不確かな状況ではステップバイステップの行動計画で制御を築いてください。"],
        'zh': ["通过先掌握小挑战来逐渐建立自信。", "定期回顾你成功克服的过去困难。", "采用你信任的导师或榜样的方法。", "在不确定的情况下，通过制定逐步行动计划来建立控制感。"],
        'hi': ["पहले छोटी चुनौतियों को माहिर करके धीरे-धीरे आत्मविश्वास बढ़ाएं।", "उन पिछली कठिनाइयों पर नियमित रूप से विचार करें जिन्हें आपने सफलतापूर्वक पार किया।", "किसी भरोसेमंद मार्गदर्शक या आदर्श का दृष्टिकोण अपनाएं।", "अनिश्चित परिस्थितियों में चरण-दर-चरण कार्य योजनाएं बनाकर नियंत्रण बनाएं।"],
        'fr': ["Augmentez progressivement la confiance en maîtrisant d'abord de petits défis.", "Réfléchissez régulièrement aux difficultés passées que vous avez surmontées.", "Adoptez l'approche d'un mentor ou d'un modèle de rôle.", "Dans les situations incertaines, construisez le contrôle avec des plans d'action pas à pas."],
        'pt': ["Aumente gradualmente a autoconfiança dominando pequenos desafios primeiro.", "Reflita regularmente sobre dificuldades passadas que você superou.", "Adote a abordagem de um mentor ou modelo a seguir.", "Em situações incertas, construa controle com planos de ação passo a passo."],
        'bn': ["প্রথমে ছোট চ্যালেঞ্জ আয়ত্ত করে ধীরে ধীরে আত্মবিশ্বাস বাড়ান।", "আপনি সফলভাবে অতিক্রম করা অতীত কঠিনতাগুলো নিয়মিত প্রতিফলন করুন।", "আপনার বিশ্বাসের একজন পরামর্শদাতা বা রোল মডেলের পদ্ধতি গ্রহণ করুন।", "অনিশ্চিত পরিস্থিতিতে ধাপে ধাপে কর্ম পরিকল্পনা করে নিয়ন্ত্রণ গড়ুন।"],
        'id': ["Tingkatkan kepercayaan diri secara bertahap dengan menguasai tantangan kecil.", "Renungkan secara rutin kesulitan masa lalu yang berhasil Anda atasi.", "Adopsi pendekatan mentor atau panutan yang Anda percaya.", "Dalam situasi tidak pasti, bangun kontrol dengan rencana aksi bertahap."],
        'ur': ["پہلے چھوٹی مشکلات پر مہارت حاصل کرکے بتدریج خود اعتمادی بڑھائیں۔", "کامیابی سے قابو پائی گئی پچھلی مشکلات پر باقاعدگی سے غور کریں۔", "جس پر اعتماد ہو اس مرشد یا رول ماڈل کا طریقہ اپنائیں۔", "غیر یقینی صورتحال میں قدم بہ قدم عمل کے منصوبے بنا کر کنٹرول قائم کریں۔"],
        'it': ["Aumenta gradualmente la fiducia padroneggiando prima le piccole sfide.", "Rifletti regolarmente sulle difficoltà passate che hai superato con successo.", "Adotta l'approccio di un mentore o modello di riferimento di fiducia.", "Nelle situazioni incerte, costruisci il controllo con piani d'azione passo dopo passo."],
        'vi': ["Tăng dần sự tự tin bằng cách thành thạo những thách thức nhỏ trước.", "Thường xuyên suy ngẫm về những khó khăn quá khứ bạn đã vượt qua thành công.", "Áp dụng cách tiếp cận của người cố vấn hoặc hình mẫu bạn tin tưởng.", "Trong các tình huống không chắc chắn, xây dựng sự kiểm soát bằng các kế hoạch hành động từng bước."],
        'pl': ["Stopniowo zwiększaj pewność siebie, opanowując najpierw małe wyzwania.", "Regularnie zastanawiaj się nad trudnościami z przeszłości, które pokonałeś.", "Przyjmij podejście mentora lub wzoru do naśladowania, któremu ufasz.", "W niepewnych sytuacjach buduj poczucie kontroli przez plany działania krok po kroku."],
    },
    'stress': {
        'de': ["Füge Atemübungen und kurze Meditation in deine tägliche Routine ein.", "Identifiziere Stressquellen und konzentriere dich auf kontrollierbare.", "Körperliche Aktivität und Schlafqualität sind Grundpfeiler des Stressmanagements.", "Bleibe mit vertrauenswürdigen Menschen für emotionale Unterstützung verbunden."],
        'ru': ["Добавьте дыхательные упражнения и медитацию в распорядок дня.", "Определите источники стресса и сосредоточьтесь на контролируемых.", "Физическая активность и качественный сон — основа управления стрессом.", "Поддерживайте связь с близкими для эмоциональной поддержки."],
        'ar': ["أضف تمارين التنفس والتأمل القصير إلى روتينك اليومي.", "حدّد مصادر التوتر وركّز على ما تستطيع التحكم فيه.", "النشاط البدني وجودة النوم أساسان لإدارة التوتر.", "ابقَ على تواصل مع أشخاص موثوقين للدعم العاطفي."],
        'es': ["Añade ejercicios de respiración y meditación corta a tu rutina diaria.", "Identifica fuentes de estrés y enfócate en las controlables.", "La actividad física y el sueño de calidad son pilares del manejo del estrés.", "Mantente conectado con personas de confianza para apoyo emocional."],
        'ko': ["일상에 호흡 운동과 짧은 명상을 추가하세요.", "스트레스 원인을 파악하고 통제 가능한 것에 집중하세요.", "신체 활동과 질 좋은 수면은 스트레스 관리의 기초입니다.", "정서적 지원을 위해 신뢰할 수 있는 사람들과 연결을 유지하세요."],
        'ja': ["日常ルーティンに呼吸エクササイズと短い瞑想を加えてください。", "ストレスの原因を特定し、コントロールできるものに集中してください。", "身体活動と良質な睡眠はストレス管理の礎です。", "感情的サポートのために信頼できる人々とつながってください。"],
        'zh': ["将呼吸练习和短暂冥想加入日常生活。", "识别压力来源，重点关注可控制的方面。", "体力活动和高质量睡眠是压力管理的基础。", "与可信赖的人保持联系以获得情感支持。"],
        'hi': ["दैनिक दिनचर्या में श्वास व्यायाम और छोटे ध्यान को जोड़ें।", "तनाव के स्रोतों की पहचान करें और जो नियंत्रणीय हैं उन पर ध्यान दें।", "शारीरिक गतिविधि और गुणवत्तापूर्ण नींद तनाव प्रबंधन के आधार हैं।", "भावनात्मक समर्थन के लिए विश्वसनीय लोगों से जुड़े रहें।"],
        'fr': ["Ajoutez des exercices de respiration et de courte méditation à votre routine.", "Identifiez les sources de stress et concentrez-vous sur celles que vous pouvez contrôler.", "L'activité physique et un sommeil de qualité sont les piliers de la gestion du stress.", "Restez connecté avec des personnes de confiance pour un soutien émotionnel."],
        'pt': ["Adicione exercícios de respiração e meditação curta à sua rotina.", "Identifique fontes de estresse e concentre-se nas controláveis.", "Atividade física e sono de qualidade são pilares do gerenciamento do estresse.", "Mantenha contato com pessoas de confiança para suporte emocional."],
        'bn': ["দৈনন্দিন রুটিনে শ্বাস ব্যায়াম এবং সংক্ষিপ্ত ধ্যান যোগ করুন।", "চাপের উৎস চিহ্নিত করুন এবং নিয়ন্ত্রণযোগ্য বিষয়গুলোতে মনোযোগ দিন।", "শারীরিক কার্যক্রম এবং মানসম্পন্ন ঘুম চাপ ব্যবস্থাপনার ভিত্তি।", "মানসিক সমর্থনের জন্য বিশ্বস্ত মানুষদের সাথে সংযুক্ত থাকুন।"],
        'id': ["Tambahkan latihan pernapasan dan meditasi singkat ke rutinitas harian.", "Identifikasi sumber stres dan fokus pada yang dapat dikendalikan.", "Aktivitas fisik dan tidur berkualitas adalah pilar manajemen stres.", "Tetap terhubung dengan orang terpercaya untuk dukungan emosional."],
        'ur': ["روزانہ کی روٹین میں سانس کی مشقیں اور مختصر مراقبہ شامل کریں۔", "تناؤ کے ذرائع کی شناخت کریں اور قابلِ کنٹرول پر توجہ دیں۔", "جسمانی سرگرمی اور معیاری نیند تناؤ کے انتظام کی بنیاد ہے۔", "جذباتی مدد کے لیے قابلِ اعتماد لوگوں سے رابطے میں رہیں۔"],
        'it': ["Aggiungi esercizi di respirazione e breve meditazione alla tua routine.", "Identifica le fonti di stress e concentrati su quelle controllabili.", "Attività fisica e sonno di qualità sono pilastri della gestione dello stress.", "Rimani in contatto con persone fidate per supporto emotivo."],
        'vi': ["Thêm bài tập hơi thở và thiền ngắn vào thói quen hàng ngày.", "Xác định nguồn gây căng thẳng và tập trung vào những gì có thể kiểm soát.", "Hoạt động thể chất và giấc ngủ chất lượng là nền tảng quản lý căng thẳng.", "Duy trì kết nối với những người tin cậy để nhận hỗ trợ tinh thần."],
        'pl': ["Dodaj ćwiczenia oddechowe i krótką medytację do swojej rutyny.", "Zidentyfikuj źródła stresu i skup się na tych, które możesz kontrolować.", "Aktywność fizyczna i jakość snu to filary zarządzania stresem.", "Pozostań w kontakcie z zaufanymi osobami po wsparcie emocjonalne."],
    },
    'body_image': {
        'de': ["Bewerte deinen Körper nach Leistung und Gesundheit, nicht Aussehen.", "Begrenze Exposition gegenüber unrealistischen Standards in sozialen Medien.", "Fokussiere auf Bewegungen, die dir helfen, dich in deinem Körper wohlzufühlen.", "Baue deinen Selbstwert auf Stärken, nicht auf Aussehen."],
        'ru': ["Оценивайте своё тело по здоровью и возможностям, а не внешности.", "Ограничьте воздействие нереалистичных стандартов в соцсетях.", "Сосредоточьтесь на движениях, которые помогают чувствовать себя в своём теле.", "Стройте самооценку на сильных сторонах, не внешности."],
        'ar': ["قيّم جسدك على أساس الصحة والأداء لا المظهر.", "قلّل من التعرض لمعايير غير واقعية على وسائل التواصل.", "ركّز على الحركات التي تساعدك على الشعور بالراحة في جسدك.", "ابنِ قيمتك الذاتية على نقاط القوة لا المظهر."],
        'es': ["Evalúa tu cuerpo por su rendimiento y salud, no su apariencia.", "Limita la exposición a estándares poco realistas en redes sociales.", "Enfócate en movimientos que te ayuden a sentirte a gusto en tu cuerpo.", "Construye tu autoestima en tus fortalezas, no en tu apariencia."],
        'ko': ["외모가 아닌 신체의 성능과 건강으로 몸을 평가해보세요.", "소셜 미디어에서 비현실적인 기준에 노출되는 것을 제한하세요.", "자신의 몸에서 편안함을 느끼게 도와주는 움직임에 집중하세요.", "외모가 아닌 강점을 중심으로 자아 가치를 구축하세요."],
        'ja': ["外見ではなく、パフォーマンスと健康で身体を評価してみてください。", "ソーシャルメディアの非現実的な基準への露出を制限してください。", "自分の体に快適さを感じさせる動きや活動に集中してください。", "外見ではなく強みを中心に自己価値を築いてください。"],
        'zh': ["尝试根据身体的表现和健康评价自己，而非外观。", "限制接触社交媒体上不切实际的标准。", "专注于帮助你在自己身体中感到自在的运动和活动。", "基于你的优势而非外貌建立自我价值感。"],
        'hi': ["अपने शरीर को दिखावे नहीं, बल्कि प्रदर्शन और स्वास्थ्य के आधार पर मूल्यांकित करें।", "सोशल मीडिया पर अवास्तविक मानकों के संपर्क को सीमित करें।", "उन गतिविधियों पर ध्यान दें जो आपको अपने शरीर में घर जैसा महसूस कराती हैं।", "दिखावे के बजाय अपनी ताकत के आसपास आत्म-मूल्य बनाएं।"],
        'fr': ["Évaluez votre corps selon sa performance et sa santé, non son apparence.", "Limitez l'exposition aux standards irréalistes sur les réseaux sociaux.", "Concentrez-vous sur les mouvements qui vous aident à vous sentir bien dans votre corps.", "Construisez l'estime de soi autour de vos forces, pas de votre apparence."],
        'pt': ["Tente avaliar seu corpo por seu desempenho e saúde, não aparência.", "Limite a exposição a padrões irrealistas nas redes sociais.", "Foque em movimentos e atividades que ajudam a sentir-se bem em seu corpo.", "Construa autoestima em torno de seus pontos fortes, não aparência."],
        'bn': ["চেহারা নয়, কার্যক্ষমতা ও স্বাস্থ্যের ভিত্তিতে নিজের শরীরকে মূল্যায়ন করুন।", "সোশ্যাল মিডিয়ায় অবাস্তব মানদণ্ডের সংস্পর্শ সীমাবদ্ধ করুন।", "এমন গতিবিধি ও কার্যক্রমে মনোযোগ দিন যা আপনার শরীরে স্বাচ্ছন্দ্য দেয়।", "চেহারার বদলে নিজের শক্তির ভিত্তিতে আত্মবিশ্বাস গড়ুন।"],
        'id': ["Coba nilai tubuhmu berdasarkan kinerja dan kesehatan, bukan penampilan.", "Batasi paparan terhadap standar tidak realistis di media sosial.", "Fokus pada gerakan yang membantu Anda merasa nyaman dalam tubuh Anda.", "Bangun harga diri berdasarkan kekuatan, bukan penampilan."],
        'ur': ["ظاہری شکل نہیں، کارکردگی اور صحت کی بنیاد پر جسم کا جائزہ لیں۔", "سوشل میڈیا پر غیر حقیقی معیارات کی نمائش محدود کریں۔", "ایسی حرکات پر توجہ دیں جو آپ کو اپنے جسم میں گھر جیسا محسوس کرائیں۔", "ظاہری شکل کی بجائے اپنی طاقتوں کی بنیاد پر خود اعتمادی بنائیں۔"],
        'it': ["Prova a valutare il tuo corpo per le sue prestazioni e salute, non l'aspetto.", "Limita l'esposizione a standard irrealistici sui social media.", "Concentrati su movimenti e attività che ti aiutano a sentirti a tuo agio nel corpo.", "Costruisci l'autostima intorno ai tuoi punti di forza, non all'aspetto."],
        'vi': ["Hãy đánh giá cơ thể bạn dựa trên hiệu suất và sức khỏe, không phải ngoại hình.", "Hạn chế tiếp xúc với các tiêu chuẩn không thực tế trên mạng xã hội.", "Tập trung vào các vận động giúp bạn cảm thấy thoải mái trong cơ thể mình.", "Xây dựng giá trị bản thân xung quanh điểm mạnh, không phải ngoại hình."],
        'pl': ["Oceniaj swoje ciało pod kątem wydajności i zdrowia, nie wyglądu.", "Ogranicz ekspozycję na nierealistyczne standardy w mediach społecznościowych.", "Skup się na ruchach, które pomagają ci czuć się dobrze we własnym ciele.", "Buduj poczucie własnej wartości wokół swoich mocnych stron, nie wyglądu."],
    },
}

# Merge supplement into FALLBACK_RECOMMENDATIONS (setdefault = don't overwrite existing entries)
for _sup_test, _sup_langs in _FALLBACK_SUPPLEMENT.items():
    for _sup_lang, _sup_recs in _sup_langs.items():
        FALLBACK_RECOMMENDATIONS.setdefault(_sup_lang, {}).setdefault(_sup_test, _sup_recs)


@lru_cache(maxsize=64)
def get_fallback_recommendations(test_type: str, lang: str = 'tr') -> List[str]:
    """Get fallback recommendations when Ollama is unavailable."""
    return FALLBACK_RECOMMENDATIONS.get(lang, {}).get(test_type, [])


# Career/Vocation domain → specific job titles
_CAREER_JOBS: dict = {
    'analytical': {
        'tr': ['Veri Bilimcisi', 'İstatistikçi', 'Mali Analist', 'İş Zekası Uzmanı', 'Araştırma Analisti'],
        'en': ['Data Scientist', 'Statistician', 'Financial Analyst', 'Business Intelligence Analyst', 'Research Analyst'],
    },
    'creative': {
        'tr': ['UX/UI Tasarımcısı', 'Grafik Tasarımcı', 'İçerik Stratejisti', 'Reklam Yaratıcı Direktörü', 'Ürün Tasarımcısı'],
        'en': ['UX/UI Designer', 'Graphic Designer', 'Content Strategist', 'Creative Director', 'Product Designer'],
    },
    'social': {
        'tr': ['İnsan Kaynakları Uzmanı', 'Psikolog', 'Eğitim Uzmanı', 'Sosyal Hizmet Uzmanı', 'Halkla İlişkiler Müdürü'],
        'en': ['HR Specialist', 'Psychologist', 'Training & Development Specialist', 'Social Worker', 'Public Relations Manager'],
    },
    'entrepreneurial': {
        'tr': ['Girişimci', 'Satış Müdürü', 'İş Geliştirme Uzmanı', 'Startup Kurucu Ortağı', 'Danışman'],
        'en': ['Entrepreneur', 'Sales Manager', 'Business Development Manager', 'Startup Co-founder', 'Management Consultant'],
    },
    'managerial': {
        'tr': ['Proje Yöneticisi', 'Operasyon Müdürü', 'Ürün Müdürü', 'Program Direktörü', 'Genel Müdür'],
        'en': ['Project Manager', 'Operations Manager', 'Product Manager', 'Program Director', 'General Manager'],
    },
    'technical': {
        'tr': ['Yazılım Mühendisi', 'Sistem Mimarı', 'DevOps Mühendisi', 'Siber Güvenlik Uzmanı', 'Makine Öğrenmesi Mühendisi'],
        'en': ['Software Engineer', 'Systems Architect', 'DevOps Engineer', 'Cybersecurity Specialist', 'ML Engineer'],
    },
}

_VOCATION_JOBS: dict = {
    'realistic': {
        'tr': ['İnşaat Mühendisi', 'Makine Teknisyeni', 'Elektrik Mühendisi', 'Pilot', 'Peyzaj Mimarı'],
        'en': ['Civil Engineer', 'Mechanical Technician', 'Electrical Engineer', 'Pilot', 'Landscape Architect'],
    },
    'investigative': {
        'tr': ['Araştırmacı Bilim İnsanı', 'Doktor', 'Çevre Bilimcisi', 'Biyokimyacı', 'Akademisyen'],
        'en': ['Research Scientist', 'Physician', 'Environmental Scientist', 'Biochemist', 'Academic Researcher'],
    },
    'artistic': {
        'tr': ['Oyuncu', 'Müzisyen', 'Yazar', 'Film Yönetmeni', 'Fotoğrafçı'],
        'en': ['Actor', 'Musician', 'Writer', 'Film Director', 'Photographer'],
    },
    'social': {
        'tr': ['Öğretmen', 'Rehber Danışman', 'Hemşire', 'Kariyer Koçu', 'Sosyolog'],
        'en': ['Teacher', 'School Counselor', 'Nurse', 'Career Coach', 'Sociologist'],
    },
    'enterprising': {
        'tr': ['Avukat', 'Siyasetçi', 'Marka Müdürü', 'Yatırım Bankacısı', 'Lobici'],
        'en': ['Lawyer', 'Politician', 'Brand Manager', 'Investment Banker', 'Lobbyist'],
    },
    'conventional': {
        'tr': ['Muhasebeci', 'Finansal Denetçi', 'Veri Yöneticisi', 'Lojistik Uzmanı', 'Aktüer'],
        'en': ['Accountant', 'Financial Auditor', 'Data Administrator', 'Logistics Specialist', 'Actuary'],
    },
}


def _career_job_fallback(test_type: str, breakdown: Dict, lang: str) -> List[str]:
    """Build job-title recommendations from top-scoring career/vocation domains."""
    job_map = _CAREER_JOBS if test_type == 'career' else _VOCATION_JOBS
    use_lang = lang if lang in ('tr', 'en') else 'en'

    scored = sorted(breakdown.items(), key=lambda x: x[1].get('score', 0), reverse=True)
    top_domains = [d for d, _ in scored[:2]]

    job_lines: List[str] = []
    for domain in top_domains:
        entry = job_map.get(domain)
        if not entry:
            continue
        jobs = entry.get(use_lang, entry['en'])
        jobs_str = ', '.join(jobs)
        if use_lang == 'tr':
            job_lines.append(f"{domain.capitalize()} alanındaki güçlü yetkinliklerinizle şu meslekleri değerlendirin: {jobs_str}.")
        else:
            job_lines.append(f"Your strong {domain} profile fits well with: {jobs_str}.")

    if use_lang == 'tr':
        job_lines.append("Bu alanlarda informational interview yaparak gerçek çalışma ortamını keşfedin.")
        job_lines.append("LinkedIn'de bu unvanları taşıyan kişilerin profillerini inceleyerek yol haritanızı netleştirin.")
    else:
        job_lines.append("Conduct informational interviews in these fields to understand the real work environment.")
        job_lines.append("Explore LinkedIn profiles with these job titles to map your own path.")

    return job_lines
