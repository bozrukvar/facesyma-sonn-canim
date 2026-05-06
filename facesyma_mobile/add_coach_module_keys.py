"""
Inserts 13 new coach module i18n keys after every 'coach.memories_btn' line
in facesyma_mobile/src/utils/i18n.ts.
Safe to run multiple times — skips insertion if keys already present.
"""

import re

FILE = "src/utils/i18n.ts"

# Per-language translations for each of the 13 new keys
# Order matches the 18 lang blocks: tr en de ru ar es ko ja zh hi fr pt bn id ur it vi pl
TRANSLATIONS: dict[str, dict[str, str]] = {
    "coach.mod_activity": {
        "tr": "Etkinlik Tavsiyeleri",
        "en": "Activity Recommendations",
        "de": "Aktivitätsempfehlungen",
        "ru": "Рекомендации по занятиям",
        "ar": "توصيات الأنشطة",
        "es": "Recomendaciones de actividad",
        "ko": "활동 추천",
        "ja": "アクティビティのおすすめ",
        "zh": "活动推荐",
        "hi": "गतिविधि सिफारिशें",
        "fr": "Recommandations d'activités",
        "pt": "Recomendações de atividades",
        "bn": "কার্যকলাপের পরামর্শ",
        "id": "Rekomendasi aktivitas",
        "ur": "سرگرمی کی سفارشات",
        "it": "Consigli sulle attività",
        "vi": "Đề xuất hoạt động",
        "pl": "Zalecenia dotyczące aktywności",
    },
    "coach.mod_sport": {
        "tr": "Spor & Aktivite",
        "en": "Sport & Fitness",
        "de": "Sport & Fitness",
        "ru": "Спорт и фитнес",
        "ar": "الرياضة واللياقة",
        "es": "Deporte y fitness",
        "ko": "스포츠 & 피트니스",
        "ja": "スポーツ＆フィットネス",
        "zh": "运动与健身",
        "hi": "खेल और फिटनेस",
        "fr": "Sport et fitness",
        "pt": "Esporte e fitness",
        "bn": "খেলাধুলা ও ফিটনেস",
        "id": "Olahraga & kebugaran",
        "ur": "کھیل اور فٹنس",
        "it": "Sport e fitness",
        "vi": "Thể thao & thể dục",
        "pl": "Sport i fitness",
    },
    "coach.mod_career_path": {
        "tr": "Kariyer Yolu",
        "en": "Career Path",
        "de": "Karriereweg",
        "ru": "Карьерный путь",
        "ar": "المسار الوظيفي",
        "es": "Camino profesional",
        "ko": "경력 경로",
        "ja": "キャリアパス",
        "zh": "职业道路",
        "hi": "करियर पथ",
        "fr": "Parcours professionnel",
        "pt": "Caminho de carreira",
        "bn": "ক্যারিয়ার পথ",
        "id": "Jalur karir",
        "ur": "کیریئر کا راستہ",
        "it": "Percorso professionale",
        "vi": "Con đường sự nghiệp",
        "pl": "Ścieżka kariery",
    },
    "coach.mod_hr": {
        "tr": "İnsan Kaynakları",
        "en": "Human Resources",
        "de": "Personalwesen",
        "ru": "Кадры",
        "ar": "الموارد البشرية",
        "es": "Recursos humanos",
        "ko": "인사",
        "ja": "人事",
        "zh": "人力资源",
        "hi": "मानव संसाधन",
        "fr": "Ressources humaines",
        "pt": "Recursos humanos",
        "bn": "মানব সম্পদ",
        "id": "Sumber daya manusia",
        "ur": "انسانی وسائل",
        "it": "Risorse umane",
        "vi": "Nguồn nhân lực",
        "pl": "Zasoby ludzkie",
    },
    "coach.mod_emotional": {
        "tr": "Duygusal Rehberlik",
        "en": "Emotional Guidance",
        "de": "Emotionale Führung",
        "ru": "Эмоциональное руководство",
        "ar": "الإرشاد العاطفي",
        "es": "Orientación emocional",
        "ko": "감정 안내",
        "ja": "感情的なガイダンス",
        "zh": "情感指导",
        "hi": "भावनात्मक मार्गदर्शन",
        "fr": "Guidance émotionnelle",
        "pt": "Orientação emocional",
        "bn": "আবেগিক নির্দেশনা",
        "id": "Panduan emosional",
        "ur": "جذباتی رہنمائی",
        "it": "Guida emotiva",
        "vi": "Hướng dẫn cảm xúc",
        "pl": "Wsparcie emocjonalne",
    },
    "coach.mod_meditation": {
        "tr": "Meditasyon & Egzersiz",
        "en": "Meditation & Exercise",
        "de": "Meditation & Übung",
        "ru": "Медитация и упражнения",
        "ar": "التأمل والتمرين",
        "es": "Meditación y ejercicio",
        "ko": "명상 & 운동",
        "ja": "瞑想＆エクササイズ",
        "zh": "冥想与运动",
        "hi": "ध्यान और व्यायाम",
        "fr": "Méditation et exercice",
        "pt": "Meditação e exercício",
        "bn": "ধ্যান ও ব্যায়াম",
        "id": "Meditasi & olahraga",
        "ur": "مراقبہ اور ورزش",
        "it": "Meditazione e esercizio",
        "vi": "Thiền & tập thể dục",
        "pl": "Medytacja i ćwiczenia",
    },
    "coach.mod_book": {
        "tr": "Kitap Tavsiyeleri",
        "en": "Book Recommendations",
        "de": "Buchempfehlungen",
        "ru": "Рекомендации книг",
        "ar": "توصيات الكتب",
        "es": "Recomendaciones de libros",
        "ko": "도서 추천",
        "ja": "本のおすすめ",
        "zh": "书籍推荐",
        "hi": "पुस्तक सिफारिशें",
        "fr": "Recommandations de livres",
        "pt": "Recomendações de livros",
        "bn": "বই পরামর্শ",
        "id": "Rekomendasi buku",
        "ur": "کتاب کی سفارشات",
        "it": "Consigli sui libri",
        "vi": "Đề xuất sách",
        "pl": "Rekomendacje książek",
    },
    "coach.mod_film": {
        "tr": "Film Tavsiyeleri",
        "en": "Film Recommendations",
        "de": "Filmempfehlungen",
        "ru": "Рекомендации фильмов",
        "ar": "توصيات الأفلام",
        "es": "Recomendaciones de películas",
        "ko": "영화 추천",
        "ja": "映画のおすすめ",
        "zh": "电影推荐",
        "hi": "फिल्म सिफारिशें",
        "fr": "Recommandations de films",
        "pt": "Recomendações de filmes",
        "bn": "চলচ্চিত্র পরামর্শ",
        "id": "Rekomendasi film",
        "ur": "فلم کی سفارشات",
        "it": "Consigli sui film",
        "vi": "Đề xuất phim",
        "pl": "Rekomendacje filmów",
    },
    "coach.mod_music": {
        "tr": "Müzik Tavsiyeleri",
        "en": "Music Recommendations",
        "de": "Musikempfehlungen",
        "ru": "Рекомендации музыки",
        "ar": "توصيات الموسيقى",
        "es": "Recomendaciones de música",
        "ko": "음악 추천",
        "ja": "音楽のおすすめ",
        "zh": "音乐推荐",
        "hi": "संगीत सिफारिशें",
        "fr": "Recommandations musicales",
        "pt": "Recomendações musicais",
        "bn": "সঙ্গীত পরামর্শ",
        "id": "Rekomendasi musik",
        "ur": "موسیقی کی سفارشات",
        "it": "Consigli musicali",
        "vi": "Đề xuất âm nhạc",
        "pl": "Rekomendacje muzyczne",
    },
    "coach.mod_podcast": {
        "tr": "Podcast Tavsiyeleri",
        "en": "Podcast Recommendations",
        "de": "Podcast-Empfehlungen",
        "ru": "Рекомендации подкастов",
        "ar": "توصيات البودكاست",
        "es": "Recomendaciones de podcasts",
        "ko": "팟캐스트 추천",
        "ja": "ポッドキャストのおすすめ",
        "zh": "播客推荐",
        "hi": "पॉडकास्ट सिफारिशें",
        "fr": "Recommandations de podcasts",
        "pt": "Recomendações de podcasts",
        "bn": "পডকাস্ট পরামর্শ",
        "id": "Rekomendasi podcast",
        "ur": "پوڈکاسٹ کی سفارشات",
        "it": "Consigli sui podcast",
        "vi": "Đề xuất podcast",
        "pl": "Rekomendacje podcastów",
    },
    "coach.mod_travel": {
        "tr": "Seyahat Tavsiyeleri",
        "en": "Travel Recommendations",
        "de": "Reiseempfehlungen",
        "ru": "Рекомендации путешествий",
        "ar": "توصيات السفر",
        "es": "Recomendaciones de viaje",
        "ko": "여행 추천",
        "ja": "旅行のおすすめ",
        "zh": "旅行推荐",
        "hi": "यात्रा सिफारिशें",
        "fr": "Recommandations de voyage",
        "pt": "Recomendações de viagem",
        "bn": "ভ্রমণ পরামর্শ",
        "id": "Rekomendasi perjalanan",
        "ur": "سفر کی سفارشات",
        "it": "Consigli di viaggio",
        "vi": "Đề xuất du lịch",
        "pl": "Rekomendacje podróży",
    },
    "coach.mod_affirmation": {
        "tr": "Günlük Afirmasyon",
        "en": "Daily Affirmation",
        "de": "Tägliche Affirmation",
        "ru": "Ежедневная аффирмация",
        "ar": "التأكيد اليومي",
        "es": "Afirmación diaria",
        "ko": "일일 확언",
        "ja": "毎日のアファメーション",
        "zh": "每日肯定",
        "hi": "दैनिक पुष्टि",
        "fr": "Affirmation quotidienne",
        "pt": "Afirmação diária",
        "bn": "দৈনিক ইতিবাচক বক্তব্য",
        "id": "Afirmasi harian",
        "ur": "روزانہ تصدیق",
        "it": "Affermazione quotidiana",
        "vi": "Khẳng định hàng ngày",
        "pl": "Codzienne afirmacje",
    },
    "coach.mod_health_advice": {
        "tr": "Sağlık Tavsiyeleri",
        "en": "Health Advice",
        "de": "Gesundheitsratschläge",
        "ru": "Советы по здоровью",
        "ar": "نصائح صحية",
        "es": "Consejos de salud",
        "ko": "건강 조언",
        "ja": "健康アドバイス",
        "zh": "健康建议",
        "hi": "स्वास्थ्य सलाह",
        "fr": "Conseils santé",
        "pt": "Conselhos de saúde",
        "bn": "স্বাস্থ্য পরামর্শ",
        "id": "Saran kesehatan",
        "ur": "صحت کے مشورے",
        "it": "Consigli salutari",
        "vi": "Lời khuyên sức khỏe",
        "pl": "Porady zdrowotne",
    },
}

KEYS_ORDER = list(TRANSLATIONS.keys())

# Map lang block identifier to language code used in TRANSLATIONS
# The i18n.ts starts each language block with:  `  tr: {`, `  en: {`, etc.
LANG_BLOCK_RE = re.compile(r"^\s{2}(\w{2}):\s*\{")


def escape_ts(s: str) -> str:
    """Escape single quotes for TypeScript string literals."""
    return s.replace("'", "\\'")


def main() -> None:
    with open(FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Check if already patched (look for first new key)
    first_key = KEYS_ORDER[0]
    if any(f"'{first_key}'" in line for line in lines):
        print(f"Already patched — '{first_key}' found. Skipping.")
        return

    current_lang: str | None = None
    new_lines: list[str] = []
    inserted = 0

    for line in lines:
        new_lines.append(line)

        # Track which language block we're in
        m = LANG_BLOCK_RE.match(line)
        if m:
            current_lang = m.group(1)

        # After the memories_btn line, inject all 13 new keys
        if current_lang and "'coach.memories_btn'" in line:
            # Determine indentation from this line
            indent = len(line) - len(line.lstrip())
            pad = " " * indent

            for key in KEYS_ORDER:
                lang_map = TRANSLATIONS[key]
                value = lang_map.get(current_lang, lang_map["en"])
                new_lines.append(f"{pad}'{key}': '{escape_ts(value)}',\n")
            inserted += 1

    print(f"Inserted 13 keys after {inserted} 'coach.memories_btn' entries.")

    with open(FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("Done.")


if __name__ == "__main__":
    main()
