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
            'career': 'Kariyer Yeteneği', 'relationship': 'İlişki Dinamiği', 'vocation': 'Meslek Uyumu (Holland RIASEC)'
        },
        'en': {
            'skills': 'Skills Assessment', 'hr': 'HR Competencies', 'personality': 'Personality (Big Five)',
            'career': 'Career Aptitude', 'relationship': 'Relationship Dynamics', 'vocation': 'Vocational Fit (Holland RIASEC)'
        },
        'de': {
            'skills': 'Fähigkeitentest', 'hr': 'HR-Kompetenzen', 'personality': 'Persönlichkeit (Big Five)',
            'career': 'Karrierefähigkeit', 'relationship': 'Beziehungsdynamik', 'vocation': 'Berufliche Eignung'
        },
        'ru': {
            'skills': 'Оценка навыков', 'hr': 'HR компетенции', 'personality': 'Личность (Big Five)',
            'career': 'Карьерный потенциал', 'relationship': 'Динамика отношений', 'vocation': 'Профессиональное соответствие'
        },
        'ar': {
            'skills': 'تقييم المهارات', 'hr': 'كفاءات الموارد البشرية', 'personality': 'الشخصية (Big Five)',
            'career': 'القدرة المهنية', 'relationship': 'ديناميكية العلاقات', 'vocation': 'التوافق الوظيفي'
        },
        'es': {
            'skills': 'Evaluación de habilidades', 'hr': 'Competencias RR.HH.', 'personality': 'Personalidad (Big Five)',
            'career': 'Aptitud profesional', 'relationship': 'Dinámicas relacionales', 'vocation': 'Ajuste vocacional'
        },
        'ko': {
            'skills': '기술 평가', 'hr': 'HR 역량', 'personality': '성격 (Big Five)',
            'career': '커리어 적성', 'relationship': '관계 역학', 'vocation': '직업 적합성'
        },
        'ja': {
            'skills': 'スキル評価', 'hr': 'HR能力', 'personality': '性格（Big Five）',
            'career': 'キャリア適性', 'relationship': '関係ダイナミクス', 'vocation': '職業適合性'
        },
        'zh': {
            'skills': '技能评估', 'hr': '人力资源能力', 'personality': '性格（Big Five）',
            'career': '职业能力', 'relationship': '关系动态', 'vocation': '职业适配度'
        },
        'hi': {
            'skills': 'कौशल मूल्यांकन', 'hr': 'HR क्षमता', 'personality': 'व्यक्तित्व (Big Five)',
            'career': 'करियर योग्यता', 'relationship': 'संबंध गतिशीलता', 'vocation': 'व्यावसायिक फिट'
        },
        'fr': {
            'skills': 'Évaluation des compétences', 'hr': 'Compétences RH', 'personality': 'Personnalité (Big Five)',
            'career': 'Aptitude professionnelle', 'relationship': 'Dynamiques relationnelles', 'vocation': 'Adéquation professionnelle'
        },
        'pt': {
            'skills': 'Avaliação de habilidades', 'hr': 'Competências RH', 'personality': 'Personalidade (Big Five)',
            'career': 'Aptidão profissional', 'relationship': 'Dinâmica de relacionamento', 'vocation': 'Adequação profissional'
        },
        'bn': {
            'skills': 'দক্ষতা মূল্যায়ন', 'hr': 'এইচআর দক্ষতা', 'personality': 'ব্যক্তিত্ব (Big Five)',
            'career': 'ক্যারিয়ার যোগ্যতা', 'relationship': 'সম্পর্ক গতিশীলতা', 'vocation': 'পেশাদার ফিট'
        },
        'id': {
            'skills': 'Penilaian Keterampilan', 'hr': 'Kompetensi HR', 'personality': 'Kepribadian (Big Five)',
            'career': 'Aptitude Karir', 'relationship': 'Dinamika Hubungan', 'vocation': 'Kesesuaian Vokasional'
        },
        'ur': {
            'skills': 'مہارت کی تشخیص', 'hr': 'HR صلاحیتیں', 'personality': 'شخصیت (Big Five)',
            'career': 'کیریئر کی صلاحیت', 'relationship': 'تعلق کی حرکیات', 'vocation': 'پیشہ ورانہ فٹ'
        },
        'it': {
            'skills': 'Valutazione delle competenze', 'hr': 'Competenze RH', 'personality': 'Personalità (Big Five)',
            'career': 'Attitudine professionale', 'relationship': 'Dinamiche relazionali', 'vocation': 'Adeguatezza vocazionale'
        },
        'vi': {
            'skills': 'Đánh giá kỹ năng', 'hr': 'Năng lực HR', 'personality': 'Tính cách (Big Five)',
            'career': 'Năng khiếu nghề nghiệp', 'relationship': 'Động lực quan hệ', 'vocation': 'Phù hợp nghề'
        },
        'pl': {
            'skills': 'Ocena umiejętności', 'hr': 'Kompetencje HR', 'personality': 'Osobowość (Big Five)',
            'career': 'Uzdolnienie zawodowe', 'relationship': 'Dynamika relacji', 'vocation': 'Dopasowanie zawodowe'
        },
}

_PROMPTS: dict = {
        'tr': """Sen bir kariyer danışmanı ve gelişim koçusun. Aşağıdaki assessment sonuçlarına bakarak kişiye özelleştirilmiş, motive edici ve pratik tavsiye cümleleri oluştur.

Assessment Türü: {test_name}
Genel Skor: {overall_score:.2f}/5.0

Domain Puanları:
{domains_text}

Lütfen şu kriterlere göre 3-4 tavsiye cümle oluştur:
1. En yüksek puanlı alanı güçlendirmeye devam et
2. En düşük puanlı alana odaklan ve geliştir
3. Kişinin güçlü yanlarını kendi gelişimi için kullan
4. Hayata uygulayabileceği somut, pratik adımlar ver

Cümleleri Türkçe, profesyonel ancak sıcak bir tonla yaz. Her cümle max 15 kelime olsun. Başına "• " işareti koy. Sadece cümleleri yaz.""",

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


def _generate_prompt(test_type: str, breakdown: Dict, overall_score: float, lang: str = 'tr') -> str:
    """Generate prompt for Ollama — 18 language support"""

    lang = lang.split('-')[0].lower() if lang else 'tr'

    test_names = _TEST_NAMES.get(lang, _TEST_NAMES['en'])
    test_name = test_names.get(test_type, test_type)

    # Get domains text - use 'level' for all langs, fallback to 'level_tr' if exists
    domains_text = "\n".join([
        f"• {domain}: {(_sg := scores.get)('score', 0):.2f}/5.0 ({_sg('level', _sg('level_tr', ''))})"
        for domain, scores in breakdown.items()
    ])

    prompt_template = _PROMPTS.get(lang, _PROMPTS['en'])
    return prompt_template.format(test_name=test_name, overall_score=overall_score, domains_text=domains_text)


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


def generate_recommendations(test_type: str, breakdown: Dict, overall_score: float, lang: str = 'tr') -> Dict:
    """
    Generate personalized recommendations for assessment results using local Ollama.

    Args:
        test_type: Type of assessment (skills, hr, personality, career, relationship, vocation)
        breakdown: Domain scores breakdown
        overall_score: Overall assessment score
        lang: Language for recommendations (tr, en)

    Returns:
        Dict with recommendations or fallback if Ollama unavailable
    """
    try:
        # Generate prompt
        prompt = _generate_prompt(test_type, breakdown, overall_score, lang)

        # Call Ollama locally
        response_text = _call_ollama_local(prompt)

        if not response_text:
            log.info('Ollama unavailable, using fallback recommendations')
            fallback = get_fallback_recommendations(test_type, lang)
            return {
                'status': 'fallback',
                'recommendations': fallback,
                'count': len(fallback),
                'note': 'Ollama not available, using template recommendations'
            }

        # Parse recommendations
        recommendations = _parse_recommendations(response_text)

        if recommendations:
            return {
                'status': 'success',
                'recommendations': recommendations,
                'count': len(recommendations)
            }
        else:
            # If parsing failed, use fallback
            fallback = get_fallback_recommendations(test_type, lang)
            return {
                'status': 'fallback',
                'recommendations': fallback,
                'count': len(fallback),
                'note': 'Ollama response parsing failed, using template'
            }

    except Exception as e:
        log.error(f'Error generating recommendations: {e}')
        fallback = get_fallback_recommendations(test_type, lang)
        return {
            'status': 'fallback',
            'recommendations': fallback,
            'count': len(fallback),
            'error': 'Recommendation generation failed.'
        }


# Fallback recommendations if Ollama unavailable — 18 languages
FALLBACK_RECOMMENDATIONS = {
    'tr': {
        'skills': ["Problem çözme becerinizi pratik projelerle güçlendirin.", "En düşük puanlı alanda çevrenizden destek almaktan çekinmeyin.", "Yeni becerileri öğrenme konusundaki hızınızı koruyun.", "Öğrendiklerinizi başkalarıyla paylaşarak pekiştirin."],
        'hr': ["Ekip çalışmasında örnek olmaya devam edin.", "Leaderboard becerilerini mentoring yoluyla geliştirin.", "Stres yönetimi tekniklerini kişisel rutininize ekleyin.", "Geri bildirime açık olmayı bir alışkanlık haline getirin."],
        'personality': ["Kişiliğinizin güçlü yönlerini hedef belirlemede kullanın.", "Farklı kişilik tiplerini anlamaya çalışarak empati geliştirin.", "İç dengeyi sağlayan faaliyetleri keşfetmeye zaman ayırın.", "Kendini tanıma yolculuğunda sabırlı ve öz-sempatik olun."],
        'career': ["En ilgi duyduğunuz kariyer alanına yönelik projelerde çalışın.", "Zayıf yönlerinizi geliştirmek için eğitim kaynaklarını araştırın.", "Mentorlük ve networking fırsatlarından yararlanın.", "Düzenli olarak kariyer hedeflerinizi gözden geçirin."],
        'relationship': ["İlişkilerinizde açık ve dürüst iletişimi temel alın.", "Duygusal zeka becerilerinizi pratik hayatta uygulamaya çalışın.", "Bağlılık tarzınızı anlamak gelişim için önemlidir.", "Sağlıklı ilişki dinamikleri hakkında bilgi edinmeye yatırım yapın."],
        'vocation': ["En uyumlu meslekler listesini araştırarak deneyim kazanın.", "Çalışma alanlarında gözlemlik veya stajlık fırsatlarını keşfedin.", "Sektör profesyonelleriyle bağlantı kurup deneyim paylaşmalarını dinleyin.", "Mesleki gelişim yolunuzu tarih belirlemeden sabırla ilerleyin."]
    },
    'en': {
        'skills': ["Strengthen problem-solving skills through practical projects.", "Don't hesitate to seek support in your weakest areas.", "Maintain your rapid learning pace for new skills.", "Reinforce what you learn by sharing with others."],
        'hr': ["Continue setting an example in teamwork and collaboration.", "Develop leadership through mentoring and guidance roles.", "Integrate stress management techniques into your routine.", "Make openness to feedback a daily practice."],
        'personality': ["Use your personality strengths for goal-setting and planning.", "Build empathy by understanding different personality types.", "Invest time finding activities that bring inner balance.", "Be patient and self-compassionate in self-discovery."],
        'career': ["Pursue projects in your most interesting career fields.", "Research educational resources for weak career areas.", "Leverage mentoring and networking opportunities.", "Review career goals regularly for alignment."],
        'relationship': ["Base relationships on open and honest communication.", "Apply emotional intelligence skills in everyday interactions.", "Understanding attachment style supports personal growth.", "Invest in learning about healthy relationship dynamics."],
        'vocation': ["Research compatible professions and gain practical experience.", "Explore internship and shadowing opportunities in sectors.", "Network with professionals and learn from their experiences.", "Advance your career path patiently without rushing."]
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


@lru_cache(maxsize=64)
def get_fallback_recommendations(test_type: str, lang: str = 'tr') -> List[str]:
    """Get fallback recommendations when Ollama is unavailable."""
    return FALLBACK_RECOMMENDATIONS.get(lang, {}).get(test_type, [])
