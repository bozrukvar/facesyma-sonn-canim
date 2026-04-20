# JSON Merge Reference Examples - Conversation Starters & Module-Specific

## Overview
This document shows how to structure the merged JSON files after translation. Provides concrete examples of the final format for both conversation_starters.json and module_specific_questions.json with all 18 languages (Turkish, English + 16 new languages).

---

## 1. CONVERSATION STARTERS - Merged JSON Example

After translating all 108 conversation starter questions to 16 languages, the structure will be:

```json
{
  "metadata": {
    "description": "Deep psychological and philosophical conversation starters for personality discovery (18 languages)",
    "version": "3.0",
    "total_questions_per_language": 108,
    "languages": ["tr", "en", "ar", "pt", "it", "de", "es", "ja", "ko", "ru", "fr", "zh", "hi", "bn", "id", "ur", "vi", "pl"],
    "categories": [
      "self_discovery",
      "hidden_traits",
      "relationships",
      "purpose",
      "authenticity",
      "shadows",
      "potential",
      "connections",
      "transformation",
      "legacy"
    ],
    "generated_at": "2026-04-19",
    "languages_added_20260419": ["ar", "pt", "it", "de", "es", "ja", "ko", "ru", "fr", "zh", "hi", "bn", "id", "ur", "vi", "pl"]
  },
  "questions_by_category": {
    "self_discovery": {
      "description": "Kendini bulma, tanıma, keşfetme | Finding yourself, getting to know yourself",
      "questions_tr": [
        "Gel, kendini bul.",
        "Sandığın kadar mısın, başka mı?",
        "... (all 12 Turkish questions)"
      ],
      "questions_en": [
        "Come, find yourself.",
        "Are you as you think you are, or something else?",
        "... (all 12 English questions)"
      ],
      "questions_ar": [
        "تعال، اكتشف نفسك.",
        "هل أنت كما تعتقد أنك، أم شيء آخر؟",
        "... (all 12 Arabic questions)"
      ],
      "questions_pt": [
        "Vem, encontra a ti mesmo.",
        "Você é como pensa que é, ou algo diferente?",
        "... (all 12 Portuguese questions)"
      ],
      "questions_it": [
        "Vieni, trova te stesso.",
        "Sei come pensi di essere, o qualcosa di diverso?",
        "... (all 12 Italian questions)"
      ],
      "questions_de": [
        "Komm, finde dich selbst.",
        "Bist du wie du denkst, dass du bist, oder etwas anderes?",
        "... (all 12 German questions)"
      ],
      "questions_es": [
        "Ven, encuéntrate a ti mismo.",
        "¿Eres como crees que eres, o algo diferente?",
        "... (all 12 Spanish questions)"
      ],
      "questions_ja": [
        "さあ、自分を見つけてください。",
        "あなたは、自分だと思っている通りの人ですか、それとも別の何かですか？",
        "... (all 12 Japanese questions)"
      ],
      "questions_ko": [
        "와서, 자신을 찾으세요.",
        "당신은 자신이라고 생각하는 대로입니까, 아니면 다른 무언가입니까?",
        "... (all 12 Korean questions)"
      ],
      "questions_ru": [
        "Приди, найди себя.",
        "Вы такие, как вы думаете, или что-то другое?",
        "... (all 12 Russian questions)"
      ],
      "questions_fr": [
        "Viens, trouve-toi.",
        "Êtes-vous comme vous le pensez, ou quelque chose d'autre?",
        "... (all 12 French questions)"
      ],
      "questions_zh": [
        "来吧，找到你自己。",
        "你是你认为的那样，还是别的什么？",
        "... (all 12 Chinese questions)"
      ],
      "questions_hi": [
        "आओ, अपने आप को खोजो।",
        "क्या आप वैसे हैं जैसा आप सोचते हैं, या कुछ और?",
        "... (all 12 Hindi questions)"
      ],
      "questions_bn": [
        "এসো, নিজেকে খুঁজে নাও।",
        "আপনি যেভাবে ভাবেন সেভাবে আছেন, নাকি অন্য কিছু?",
        "... (all 12 Bengali questions)"
      ],
      "questions_id": [
        "Datanglah, temukan diri Anda.",
        "Apakah Anda seperti yang Anda pikir, atau sesuatu yang lain?",
        "... (all 12 Indonesian questions)"
      ],
      "questions_ur": [
        "آؤ، اپنے آپ کو تلاش کرو۔",
        "کیا آپ وہی ہیں جیسا آپ سوچتے ہیں، یا کچھ اور؟",
        "... (all 12 Urdu questions)"
      ],
      "questions_vi": [
        "Hãy đến, tìm thấy chính mình.",
        "Bạn có phải như bạn nghĩ không, hay là điều gì đó khác?",
        "... (all 12 Vietnamese questions)"
      ],
      "questions_pl": [
        "Chodź, znajdź siebie.",
        "Czy jesteś taki, jak myślisz, że jesteś, czy czymś innym?",
        "... (all 12 Polish questions)"
      ]
    },
    "hidden_traits": {
      "description": "Gizli yönler, saklı güçler, fark edilmeyen özellikler | Hidden sides, buried strengths",
      "questions_tr": [
        "Fark etmediğin nefesini duymak ister misin?",
        "... (all 14 Turkish questions)"
      ],
      "questions_en": [
        "Do you want to hear the breath you don't notice?",
        "... (all 14 English questions)"
      ],
      "questions_ar": [
        "هل تود أن تسمع النفس الذي لا تلاحظه؟",
        "... (all 14 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "relationships": {
      "description": "İlişkiler, bağlantılar, kişiler arası dinamikler | Connections, relationships, interpersonal dynamics",
      "questions_tr": [
        "Sana en çok benzeyen yabancıyı tanımak ister misin?",
        "... (all 14 Turkish questions)"
      ],
      "questions_en": [
        "Do you want to get to know the stranger who resembles you the most?",
        "... (all 14 English questions)"
      ],
      "questions_ar": [
        "هل تود التعرف على الغريب الذي يشبهك أكثر من غيره؟",
        "... (all 14 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "purpose": {
      "description": "Amaç, anlam, yaşam yönü | Life purpose, meaning, direction",
      "questions_tr": [
        "Seni senle buluşturmak ister misin?",
        "... (all 12 Turkish questions)"
      ],
      "questions_en": [
        "Do you want to bring you together with yourself?",
        "... (all 12 English questions)"
      ],
      "questions_ar": [
        "هل تود أن تجمع نفسك بنفسك؟",
        "... (all 12 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "authenticity": {
      "description": "Gerçeklik, dürüstlük, kimlik | Truthfulness, honesty, identity",
      "questions_tr": [
        "Ne kadarın oyuncu, ne kadarın gerçek?",
        "... (all 12 Turkish questions)"
      ],
      "questions_en": [
        "How much of you is an actor, how much is real?",
        "... (all 12 English questions)"
      ],
      "questions_ar": [
        "كم منك ممثل، كم حقيقي؟",
        "... (all 12 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "shadows": {
      "description": "Gölgeler, çelişkiler, karanlık taraflar | Shadow self, contradictions, dark sides",
      "questions_tr": [
        "Kendi içinde ne kadar karanlık var?",
        "... (all 12 Turkish questions)"
      ],
      "questions_en": [
        "How much darkness exists within you?",
        "... (all 12 English questions)"
      ],
      "questions_ar": [
        "كم من الظلام موجود بداخلك؟",
        "... (all 12 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "potential": {
      "description": "Potansiyel, büyüme, gelişim | Potential, growth, development",
      "questions_tr": [
        "Hangi versiyonun olabilirdin?",
        "... (all 12 Turkish questions)"
      ],
      "questions_en": [
        "Which version of yourself could you have been?",
        "... (all 12 English questions)"
      ],
      "questions_ar": [
        "أي نسخة منك كان يمكن أن تكون؟",
        "... (all 12 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "connections": {
      "description": "Bağlantılar, karşılıklılık, empati | Bonds, reciprocity, empathy",
      "questions_tr": [
        "Hangi insandan en çok öğrendin?",
        "... (all 14 Turkish questions)"
      ],
      "questions_en": [
        "From which person have you learned the most?",
        "... (all 14 English questions)"
      ],
      "questions_ar": [
        "من أي شخص تعلمت أكثر؟",
        "... (all 14 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "transformation": {
      "description": "Değişim, dönüşüm, evrim | Change, transformation, evolution",
      "questions_tr": [
        "Hangi olaydan sonra harita değişti?",
        "... (all 12 Turkish questions)"
      ],
      "questions_en": [
        "After which event did your map change?",
        "... (all 12 English questions)"
      ],
      "questions_ar": [
        "بعد أي حدث تغيرت خريطتك؟",
        "... (all 12 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "legacy": {
      "description": "Miras, kalıcılık, etki | Legacy, permanence, impact",
      "questions_tr": [
        "Hangisini geride bırakmak istersen?",
        "... (all 12 Turkish questions)"
      ],
      "questions_en": [
        "What do you want to leave behind?",
        "... (all 12 English questions)"
      ],
      "questions_ar": [
        "ماذا تريد أن تتركه وراءك؟",
        "... (all 12 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    }
  },
  "usage": {
    "description": "Bu soruları RAG sistemi ile kullanma",
    "languages_supported": ["tr", "en", "ar", "pt", "it", "de", "es", "ja", "ko", "ru", "fr", "zh", "hi", "bn", "id", "ur", "vi", "pl"],
    "methods": [
      "1. Chat endpoint: /chat/message'e soru gönder (lang: 'tr', 'en', 'ar', 'pt', etc.)",
      "2. Suggestion API: GET /chat/suggestions?category=self_discovery&lang=ar (all languages supported)",
      "3. Batch test: test_rag_simple.py ile CHROMA_PATH env var set et"
    ],
    "expected_behavior": "RAG retriever, sorudan ilgili sıfat karakteristikleri bulup LLM'e context olarak injekte eder. Cevap daha derinlemesine ve ilişkili olur.",
    "language_notes": {
      "rtl_languages": ["ar", "ur"],
      "asian_languages": ["ja", "ko", "zh", "hi", "bn", "vi"],
      "formal_register": ["de", "fr", "it", "pl", "ru"],
      "philosophical_depth": "All languages selected for existing introspective and philosophical traditions"
    }
  }
}
```

---

## 2. MODULE-SPECIFIC QUESTIONS - Merged JSON Example

After translating all 130 module-specific questions to 16 languages:

```json
{
  "metadata": {
    "description": "Module-specific conversation starters for personality discovery across 13 life domains (18 languages)",
    "version": "2.0",
    "total_modules": 13,
    "questions_per_module": 10,
    "total_questions_per_language": 130,
    "languages": ["tr", "en", "ar", "pt", "it", "de", "es", "ja", "ko", "ru", "fr", "zh", "hi", "bn", "id", "ur", "vi", "pl"],
    "modules": [
      "career",
      "music",
      "leadership",
      "sports",
      "art",
      "education",
      "health",
      "relationships",
      "finance",
      "travel",
      "creativity",
      "spirituality",
      "growth"
    ],
    "generated_at": "2026-04-19",
    "languages_added_20260419": ["ar", "pt", "it", "de", "es", "ja", "ko", "ru", "fr", "zh", "hi", "bn", "id", "ur", "vi", "pl"]
  },
  "modules": {
    "career": {
      "name_tr": "Kariyer",
      "name_en": "Career",
      "name_ar": "الحياة المهنية",
      "name_pt": "Carreira",
      "name_it": "Carriera",
      "name_de": "Karriere",
      "name_es": "Carrera",
      "name_ja": "キャリア",
      "name_ko": "경력",
      "name_ru": "Карьера",
      "name_fr": "Carrière",
      "name_zh": "职业生涯",
      "name_hi": "करियर",
      "name_bn": "ক্যারিয়ার",
      "name_id": "Karir",
      "name_ur": "کیریئر",
      "name_vi": "Sự nghiệp",
      "name_pl": "Kariera",
      "description": "İş hayatı, başarı, profesyonel gelişim | Work life, success, professional development",
      "questions_tr": [
        "Hangi işte kendini bulursun?",
        "Hangi meslekte tatmin olursun?",
        "... (all 10 Turkish questions)"
      ],
      "questions_en": [
        "In which profession do you find yourself?",
        "What kind of job truly satisfies you?",
        "... (all 10 English questions)"
      ],
      "questions_ar": [
        "في أي مهنة تجد نفسك؟",
        "ما نوع الوظيفة التي ترضيك حقًا؟",
        "... (all 10 Arabic questions)"
      ],
      "questions_pt": [
        "Em qual profissão você se encontra?",
        "Que tipo de trabalho realmente o satisfaz?",
        "... (all 10 Portuguese questions)"
      ],
      "questions_it": [
        "In quale professione ti trovi?",
        "Quale tipo di lavoro ti soddisfa veramente?",
        "... (all 10 Italian questions)"
      ],
      "questions_de": [
        "In welchem Beruf findest du dich?",
        "Welche Art von Arbeit erfüllt dich wirklich?",
        "... (all 10 German questions)"
      ],
      "questions_es": [
        "¿En cuál profesión te encuentras?",
        "¿Qué tipo de trabajo te satisface realmente?",
        "... (all 10 Spanish questions)"
      ],
      "questions_ja": [
        "どの職業であなた自身を見つけますか？",
        "どのような仕事があなたを本当に満足させますか？",
        "... (all 10 Japanese questions)"
      ],
      "questions_ko": [
        "어떤 직업에서 자신을 찾습니까?",
        "어떤 일이 당신을 진정으로 만족시킵니까?",
        "... (all 10 Korean questions)"
      ],
      "questions_ru": [
        "В какой профессии вы находите себя?",
        "Какой вид работы вас действительно удовлетворяет?",
        "... (all 10 Russian questions)"
      ],
      "questions_fr": [
        "Dans quelle profession vous trouvez-vous?",
        "Quel type de travail vous satisfait vraiment?",
        "... (all 10 French questions)"
      ],
      "questions_zh": [
        "在哪个职业中，你找到了自己？",
        "什么样的工作真正让你满意？",
        "... (all 10 Chinese questions)"
      ],
      "questions_hi": [
        "किस पेशे में आप अपने आप को पाते हैं?",
        "कौन सी नौकरी आपको वास्तव में संतुष्ट करती है?",
        "... (all 10 Hindi questions)"
      ],
      "questions_bn": [
        "কোন পেশায় আপনি নিজেকে খুঁজে পান?",
        "কোন ধরনের কাজ আপনাকে সত্যিকারভাবে সন্তুষ্ট করে?",
        "... (all 10 Bengali questions)"
      ],
      "questions_id": [
        "Dalam profesi apa Anda menemukan diri Anda?",
        "Jenis pekerjaan apa yang benar-benar memuaskan Anda?",
        "... (all 10 Indonesian questions)"
      ],
      "questions_ur": [
        "کس پیشے میں آپ اپنے آپ کو تلاش کرتے ہیں؟",
        "کون سی نوکری آپ کو حقیقی طور پر مطمئن کرتی ہے؟",
        "... (all 10 Urdu questions)"
      ],
      "questions_vi": [
        "Trong ngành nghề nào bạn tìm thấy chính mình?",
        "Loại công việc nào thực sự làm bạn hài lòng?",
        "... (all 10 Vietnamese questions)"
      ],
      "questions_pl": [
        "W jakim zawodzie znajdujesz siebie?",
        "Jaki rodzaj pracy naprawdę cię zadowala?",
        "... (all 10 Polish questions)"
      ]
    },
    "music": {
      "name_tr": "Müzik",
      "name_en": "Music",
      "name_ar": "الموسيقى",
      "name_pt": "Música",
      "name_it": "Musica",
      "name_de": "Musik",
      "name_es": "Música",
      "name_ja": "音楽",
      "name_ko": "음악",
      "name_ru": "Музыка",
      "name_fr": "Musique",
      "name_zh": "音乐",
      "name_hi": "संगीत",
      "name_bn": "সংগীত",
      "name_id": "Musik",
      "name_ur": "موسیقی",
      "name_vi": "Âm nhạc",
      "name_pl": "Muzyka",
      "description": "Müzik zevki, ritim, sesli ifade | Musical taste, rhythm, sonic expression",
      "questions_tr": [
        "Hangi müzik seni kim yapar?",
        "... (all 10 Turkish questions)"
      ],
      "questions_en": [
        "Which music makes you who you are?",
        "... (all 10 English questions)"
      ],
      "questions_ar": [
        "أي موسيقى تجعلك من أنت؟",
        "... (all 10 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "leadership": {
      "name_tr": "Liderlik",
      "name_en": "Leadership",
      "name_ar": "القيادة",
      "name_pt": "Liderança",
      "... (continue translations)",
      "questions_tr": [
        "Kimi yönetirken en iyi halisin?",
        "... (all 10 Turkish questions)"
      ],
      "questions_en": [
        "When managing people, when are you at your best?",
        "... (all 10 English questions)"
      ],
      "questions_ar": [
        "عند إدارة الناس، متى تكون في أفضل حالاتك؟",
        "... (all 10 Arabic questions)"
      ],
      "... (continue for all 16 new languages)"
    },
    "... (continue for remaining 10 modules: sports, art, education, health, relationships, finance, travel, creativity, spirituality, growth)"
  },
  "usage": {
    "integration": "Combine with general 108-question conversation starters for comprehensive personality analysis across 13 life domains",
    "total_questions_available": "108 (conversation starters) + 130 (module-specific) = 238 questions per language (4,284 total across 18 languages)",
    "example_flow": "1. User question → 2. RAG retrieves context in specified language → 3. LLM generates response with module-specific insights",
    "language_switching": "Use lang parameter in API calls: /chat/message?lang=ar, /chat/message?lang=ja, etc.",
    "all_supported_languages": ["tr", "en", "ar", "pt", "it", "de", "es", "ja", "ko", "ru", "fr", "zh", "hi", "bn", "id", "ur", "vi", "pl"]
  }
}
```

---

## 3. Database Schema Update

When merging into database (CHROMA_PATH), ensure:

```python
# Each document structure for RAG vectorization
document_structure = {
    "id": "conversation_starters_self_discovery_1",
    "category": "self_discovery",
    "language": "ar",  # Track language
    "question": "تعال، اكتشف نفسك.",
    "english_reference": "Come, find yourself.",
    "module": None,  # For conversation starters
    "metadata": {
        "type": "conversation_starter",
        "category": "self_discovery",
        "language_code": "ar",
        "psychological_theme": "self_discovery"
    }
}

# For module-specific questions
document_structure = {
    "id": "module_specific_career_1",
    "module": "career",
    "language": "ar",
    "question": "في أي مهنة تجد نفسك؟",
    "english_reference": "In which profession do you find yourself?",
    "category": None,  # For module-specific
    "metadata": {
        "type": "module_specific",
        "module": "career",
        "language_code": "ar",
        "life_domain": "career"
    }
}
```

---

## 4. API Endpoint Examples

Once merged, API calls will support language parameter:

```bash
# Get conversation starter suggestions in Arabic
curl -X GET "http://localhost:5000/chat/suggestions?category=self_discovery&lang=ar" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get module-specific suggestions in Japanese
curl -X GET "http://localhost:5000/chat/suggestions?module=career&lang=ja" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Chat with language parameter
curl -X POST "http://localhost:5000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "من أنا حقاً؟",
    "lang": "ar",
    "conversation_id": "abc123"
  }'

# List all supported languages
curl -X GET "http://localhost:5000/chat/languages" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 5. Migration Checklist

Before deploying merged translations:

- [ ] All 108 conversation starter questions translated to 16 languages
- [ ] All 130 module-specific questions translated to 16 languages
- [ ] JSON metadata updated with all 18 language codes
- [ ] Module/category names translated to all 16 languages
- [ ] UTF-8 encoding verified for all special characters
- [ ] RTL languages (Arabic, Urdu) rendering tested
- [ ] Diacritical marks and tone marks validated
- [ ] RAG vector database updated with all language variants
- [ ] Language parameter added to API endpoints
- [ ] Chat interface language switching tested
- [ ] Native speaker quality review completed
- [ ] Documentation updated with new language support
- [ ] User-facing language selection UI implemented
- [ ] Performance tested with multi-language retrieval
- [ ] Fallback to English implemented if language unavailable

---

## 6. Quick Format Validation

JSON structure validation:

```python
# Validation checklist
def validate_merged_translation():
    expected_languages = 18
    expected_conversation_starters = 108
    expected_module_questions = 130
    expected_modules = 13
    expected_categories = 10
    
    assert len(data['metadata']['languages']) == expected_languages
    
    # Check conversation starters
    for category in data['questions_by_category']:
        for lang in data['metadata']['languages']:
            key = f'questions_{lang}'
            assert key in data['questions_by_category'][category]
            assert len(data['questions_by_category'][category][key]) == \
                   len(data['questions_by_category'][category]['questions_en'])
    
    # Check module-specific
    for module in data['modules']:
        for lang in data['metadata']['languages']:
            key = f'questions_{lang}'
            assert key in data['modules'][module]
            assert len(data['modules'][module][key]) == expected_module_questions
    
    print("✓ All validation checks passed!")
```

---

## Summary

**File Structure After Merge:**
- conversation_starters.json: 18 languages × 108 questions = 1,944 total questions
- module_specific_questions.json: 18 languages × 130 questions = 2,340 total questions
- **Grand Total**: 4,284 personality discovery questions in 18 languages

**Estimated File Sizes:**
- conversation_starters.json: ~800-900 KB
- module_specific_questions.json: ~950-1050 KB

**Implementation Timeline:**
- Full translation: 2-4 weeks (depending on available translators)
- Quality review: 1 week
- System integration & testing: 1 week
- Deployment: 1-2 days

---

**Ready to merge translations into production JSON files!**
