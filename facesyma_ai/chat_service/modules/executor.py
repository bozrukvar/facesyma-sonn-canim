"""
facesyma_ai/chat_service/modules/executor.py
=============================================
Module execution engine - calls external services and formats results.
"""

import logging
import requests
from typing import Optional, Dict, Any
from .registry import get_registry

# ---------------------------------------------------------------------------
# Navigation action config — maps module → screen + 18-lang label
# ---------------------------------------------------------------------------
_MODULE_SCREENS: dict[str, str] = {
    "similarity":        "Similarity",
    "astrology":         "Astrology",
    "diet":              "Diet",
    "twins":             "Twins",
    "gamification":      "Gamification",
    "leaderboard":       "Leaderboard",
    "missions":          "Missions",
    "challenges":        "Challenges",
    "daily":             "Daily",
    "art_match":         "ArtMatch",
    "communities":       "Communities",
    "fashion":           "Fashion",
    "assessment_history":"AssessmentHistory",
    "coach_hub":         "CoachHub",
    "badges":            "Badges",
    "coin_wallet":       "CoinWallet",
}

_MODULE_LABELS: dict[str, dict[str, str]] = {
    "similarity": {
        "tr": "🎭 Benzerlerimi Gör", "en": "🎭 See My Matches",
        "de": "🎭 Meine Ähnlichkeiten", "ru": "🎭 Мои совпадения",
        "ar": "🎭 عرض تطابقاتي",       "es": "🎭 Ver coincidencias",
        "ko": "🎭 내 매칭 보기",          "ja": "🎭 類似を見る",
        "zh": "🎭 查看匹配",             "hi": "🎭 मिलान देखें",
        "fr": "🎭 Voir correspondances","pt": "🎭 Ver correspondências",
        "bn": "🎭 মিল দেখুন",           "id": "🎭 Lihat kecocokan",
        "ur": "🎭 مطابقت دیکھیں",       "it": "🎭 Vedi corrispondenze",
        "vi": "🎭 Xem kết quả",         "pl": "🎭 Zobacz dopasowania",
    },
    "astrology": {
        "tr": "⭐ Astroloji Haritamı Gör","en": "⭐ See My Astrology Chart",
        "de": "⭐ Meine Astrologie-Karte","ru": "⭐ Астрологическая карта",
        "ar": "⭐ خريطتي الفلكية",        "es": "⭐ Ver carta astrológica",
        "ko": "⭐ 내 점성술 차트",           "ja": "⭐ 占星術チャートを見る",
        "zh": "⭐ 查看占星图",              "hi": "⭐ ज्योतिष चार्ट देखें",
        "fr": "⭐ Voir ma carte",          "pt": "⭐ Ver meu mapa astrológico",
        "bn": "⭐ জ্যোতিষ চার্ট দেখুন",    "id": "⭐ Lihat bagan astrologi",
        "ur": "⭐ نجومی نقشہ دیکھیں",       "it": "⭐ Vedi la mia mappa",
        "vi": "⭐ Xem biểu đồ chiêu tinh", "pl": "⭐ Zobacz mapę astrologiczną",
    },
    "diet": {
        "tr": "🥗 Beslenme Planımı Gör", "en": "🥗 See My Diet Plan",
        "de": "🥗 Mein Ernährungsplan",  "ru": "🥗 Мой план питания",
        "ar": "🥗 خطة نظامي الغذائي",    "es": "🥗 Ver mi plan de dieta",
        "ko": "🥗 식단 계획 보기",          "ja": "🥗 食事プランを見る",
        "zh": "🥗 查看饮食计划",            "hi": "🥗 आहार योजना देखें",
        "fr": "🥗 Voir mon plan diète",   "pt": "🥗 Ver plano de dieta",
        "bn": "🥗 খাদ্য পরিকল্পনা দেখুন",  "id": "🥗 Lihat rencana diet",
        "ur": "🥗 خوراک کا منصوبہ دیکھیں", "it": "🥗 Vedi il mio piano dieta",
        "vi": "🥗 Xem kế hoạch ăn uống",  "pl": "🥗 Zobacz plan diety",
    },
    "twins": {
        "tr": "👥 Yüz İkizimi Bul", "en": "👥 Find My Face Twin",
        "de": "👥 Mein Gesichtszwilling", "ru": "👥 Найти двойника",
        "ar": "👥 ابحث عن توأمي", "es": "👥 Encontrar mi gemelo",
        "ko": "👥 얼굴 쌍둥이 찾기", "ja": "👥 顔の双子を見つける",
        "zh": "👥 找面孔双胞胎", "hi": "👥 चेहरा जुड़वां खोजें",
        "fr": "👥 Trouver mon jumeau", "pt": "👥 Encontrar meu gêmeo",
        "bn": "👥 মুখের যমজ খুঁজুন", "id": "👥 Temukan kembaran wajah",
        "ur": "👥 چہرے کا جڑواں تلاش کریں", "it": "👥 Trova il mio gemello",
        "vi": "👥 Tìm khuôn mặt song sinh", "pl": "👥 Znajdź mojego bliźniaka",
    },
    "gamification": {
        "tr": "🏆 Oyun Merkezim",          "en": "🏆 My Game Center",
        "de": "🏆 Mein Spielzentrum",       "ru": "🏆 Мой игровой центр",
        "ar": "🏆 مركز الألعاب",             "es": "🏆 Mi centro de juegos",
        "ko": "🏆 게임 센터",                 "ja": "🏆 ゲームセンター",
        "zh": "🏆 游戏中心",                  "hi": "🏆 गेम सेंटर",
        "fr": "🏆 Mon centre de jeux",       "pt": "🏆 Meu centro de jogos",
        "bn": "🏆 গেম সেন্টার",              "id": "🏆 Pusat permainan",
        "ur": "🏆 گیم سینٹر",               "it": "🏆 Il mio centro giochi",
        "vi": "🏆 Trung tâm trò chơi",       "pl": "🏆 Moje centrum gier",
    },
    "missions": {
        "tr": "🎯 Görevlerime Git",          "en": "🎯 Go to My Missions",
        "de": "🎯 Meine Missionen",          "ru": "🎯 Мои миссии",
        "ar": "🎯 مهامي",                    "es": "🎯 Mis misiones",
        "ko": "🎯 내 미션 보기",               "ja": "🎯 ミッションへ",
        "zh": "🎯 我的任务",                   "hi": "🎯 मेरे मिशन",
        "fr": "🎯 Mes missions",             "pt": "🎯 Minhas missões",
        "bn": "🎯 আমার মিশন",                "id": "🎯 Misi saya",
        "ur": "🎯 میری مہمات",               "it": "🎯 Le mie missioni",
        "vi": "🎯 Nhiệm vụ của tôi",          "pl": "🎯 Moje misje",
    },
    "challenges": {
        "tr": "⚔️ Zorluklara Git",           "en": "⚔️ Go to Challenges",
        "de": "⚔️ Meine Herausforderungen",  "ru": "⚔️ Мои вызовы",
        "ar": "⚔️ تحدياتي",                  "es": "⚔️ Mis desafíos",
        "ko": "⚔️ 챌린지 보기",               "ja": "⚔️ チャレンジへ",
        "zh": "⚔️ 我的挑战",                  "hi": "⚔️ मेरी चुनौतियाँ",
        "fr": "⚔️ Mes défis",               "pt": "⚔️ Meus desafios",
        "bn": "⚔️ আমার চ্যালেঞ্জ",           "id": "⚔️ Tantangan saya",
        "ur": "⚔️ میرے چیلنج",              "it": "⚔️ Le mie sfide",
        "vi": "⚔️ Thách thức của tôi",        "pl": "⚔️ Moje wyzwania",
    },
    "leaderboard": {
        "tr": "📊 Sıralamaya Git",           "en": "📊 Go to Leaderboard",
        "de": "📊 Zur Rangliste",            "ru": "📊 Таблица лидеров",
        "ar": "📊 لوحة المتصدرين",           "es": "📊 Ver clasificación",
        "ko": "📊 리더보드 보기",              "ja": "📊 ランキングへ",
        "zh": "📊 查看排行榜",                "hi": "📊 लीडरबोर्ड देखें",
        "fr": "📊 Voir le classement",       "pt": "📊 Ver classificação",
        "bn": "📊 লিডারবোর্ড দেখুন",         "id": "📊 Lihat papan peringkat",
        "ur": "📊 لیڈربورڈ دیکھیں",          "it": "📊 Classifica",
        "vi": "📊 Bảng xếp hạng",            "pl": "📊 Tabela wyników",
    },
    "daily": {
        "tr": "🌟 Günlük İçeriğime Git",     "en": "🌟 Go to Daily Content",
        "de": "🌟 Tägliche Inhalte",         "ru": "🌟 Ежедневный контент",
        "ar": "🌟 المحتوى اليومي",           "es": "🌟 Contenido diario",
        "ko": "🌟 오늘의 콘텐츠",              "ja": "🌟 デイリーコンテンツ",
        "zh": "🌟 每日内容",                  "hi": "🌟 दैनिक सामग्री",
        "fr": "🌟 Contenu quotidien",        "pt": "🌟 Conteúdo diário",
        "bn": "🌟 দৈনিক বিষয়বস্তু",          "id": "🌟 Konten harian",
        "ur": "🌟 روزانہ مواد",              "it": "🌟 Contenuto giornaliero",
        "vi": "🌟 Nội dung hàng ngày",        "pl": "🌟 Codzienna zawartość",
    },
    "art_match": {
        "tr": "🎨 Sanat Eşimi Bul",          "en": "🎨 Find My Art Match",
        "de": "🎨 Mein Kunst-Match",         "ru": "🎨 Мое произведение искусства",
        "ar": "🎨 تطابقي الفني",             "es": "🎨 Mi obra de arte",
        "ko": "🎨 내 예술 매칭",              "ja": "🎨 アートマッチ",
        "zh": "🎨 我的艺术匹配",              "hi": "🎨 मेरा कला मिलान",
        "fr": "🎨 Mon œuvre d'art",          "pt": "🎨 Minha obra de arte",
        "bn": "🎨 আমার শিল্প মিল",           "id": "🎨 Kecocokan seni saya",
        "ur": "🎨 میری فنی مطابقت",          "it": "🎨 La mia opera d'arte",
        "vi": "🎨 Tác phẩm nghệ thuật của tôi","pl": "🎨 Moje dopasowanie artystyczne",
    },
    "communities": {
        "tr": "👥 Topluluklara Git",          "en": "👥 Go to Communities",
        "de": "👥 Zu den Gemeinschaften",    "ru": "👥 Сообщества",
        "ar": "👥 المجتمعات",                "es": "👥 Comunidades",
        "ko": "👥 커뮤니티 보기",              "ja": "👥 コミュニティへ",
        "zh": "👥 社区",                     "hi": "👥 समुदाय",
        "fr": "👥 Communautés",             "pt": "👥 Comunidades",
        "bn": "👥 কমিউনিটিতে যান",           "id": "👥 Komunitas",
        "ur": "👥 کمیونٹیز",                "it": "👥 Comunità",
        "vi": "👥 Cộng đồng",                "pl": "👥 Społeczności",
    },
    "fashion": {
        "tr": "👗 Moda Önerilerime Git",      "en": "👗 Go to Fashion",
        "de": "👗 Mode-Empfehlungen",        "ru": "👗 Модные рекомендации",
        "ar": "👗 توصيات الموضة",            "es": "👗 Recomendaciones de moda",
        "ko": "👗 패션 추천 보기",             "ja": "👗 ファッションへ",
        "zh": "👗 时尚推荐",                  "hi": "👗 फैशन अनुशंसाएं",
        "fr": "👗 Recommandations mode",     "pt": "👗 Recomendações de moda",
        "bn": "👗 ফ্যাশন পরামর্শ",           "id": "👗 Rekomendasi fashion",
        "ur": "👗 فیشن تجاویز",              "it": "👗 Consigli di moda",
        "vi": "👗 Gợi ý thời trang",          "pl": "👗 Rekomendacje mody",
    },
    "assessment_history": {
        "tr": "📋 Test Geçmişime Git",        "en": "📋 Go to Test History",
        "de": "📋 Testverlauf",              "ru": "📋 История тестов",
        "ar": "📋 سجل الاختبارات",           "es": "📋 Historial de tests",
        "ko": "📋 테스트 기록 보기",           "ja": "📋 テスト履歴へ",
        "zh": "📋 测试历史",                  "hi": "📋 परीक्षण इतिहास",
        "fr": "📋 Historique des tests",     "pt": "📋 Histórico de testes",
        "bn": "📋 পরীক্ষার ইতিহাস",          "id": "📋 Riwayat tes",
        "ur": "📋 ٹیسٹ کی تاریخ",            "it": "📋 Cronologia dei test",
        "vi": "📋 Lịch sử bài kiểm tra",      "pl": "📋 Historia testów",
    },
    "coach_hub": {
        "tr": "🧭 Koç Merkezine Git",         "en": "🧭 Go to Coach Hub",
        "de": "🧭 Zum Coach-Hub",            "ru": "🧭 Центр коуча",
        "ar": "🧭 مركز المدرب",              "es": "🧭 Centro de coaching",
        "ko": "🧭 코치 허브 보기",             "ja": "🧭 コーチハブへ",
        "zh": "🧭 教练中心",                  "hi": "🧭 कोच हब",
        "fr": "🧭 Centre de coaching",       "pt": "🧭 Hub de coaching",
        "bn": "🧭 কোচ হাব",                  "id": "🧭 Pusat pelatihan",
        "ur": "🧭 کوچ مرکز",                "it": "🧭 Hub di coaching",
        "vi": "🧭 Trung tâm huấn luyện",      "pl": "🧭 Centrum coachingu",
    },
    "badges": {
        "tr": "🏅 Rozetlerime Git",           "en": "🏅 Go to My Badges",
        "de": "🏅 Meine Abzeichen",          "ru": "🏅 Мои значки",
        "ar": "🏅 شاراتي",                   "es": "🏅 Mis insignias",
        "ko": "🏅 내 배지 보기",               "ja": "🏅 バッジへ",
        "zh": "🏅 我的徽章",                  "hi": "🏅 मेरे बैज",
        "fr": "🏅 Mes badges",              "pt": "🏅 Meus emblemas",
        "bn": "🏅 আমার ব্যাজ",               "id": "🏅 Lencana saya",
        "ur": "🏅 میرے بیجز",               "it": "🏅 I miei badge",
        "vi": "🏅 Huy hiệu của tôi",          "pl": "🏅 Moje odznaki",
    },
    "coin_wallet": {
        "tr": "💰 Coin Cüzdanıma Git",        "en": "💰 Go to Coin Wallet",
        "de": "💰 Mein Münzgeldbeutel",      "ru": "💰 Монетный кошелёк",
        "ar": "💰 محفظة العملات",             "es": "💰 Monedero de monedas",
        "ko": "💰 코인 지갑 보기",             "ja": "💰 コインウォレット",
        "zh": "💰 硬币钱包",                  "hi": "💰 कॉइन वॉलेट",
        "fr": "💰 Portefeuille de pièces",   "pt": "💰 Carteira de moedas",
        "bn": "💰 কয়েন ওয়ালেট",             "id": "💰 Dompet koin",
        "ur": "💰 کوائن والٹ",               "it": "💰 Portafoglio monete",
        "vi": "💰 Ví xu",                    "pl": "💰 Portfel monet",
    },
}


def build_module_action(
    module_name: str,
    result_data: dict,
    params: dict,
    lang: str,
) -> dict | None:
    """Return a navigate action dict if the module supports it, else None."""
    screen = _MODULE_SCREENS.get(module_name)
    if not screen:
        return None

    labels = _MODULE_LABELS.get(module_name, {})
    label  = labels.get(lang) or labels.get("en", f"→ {screen}")

    # Build screen-specific params
    nav_params: dict = {}
    if module_name == "similarity":
        nav_params = {"sifatlar": params.get("sifatlar", []), "lang": lang}
    elif module_name == "fashion":
        nav_params = {"analysisResult": result_data, "lang": lang}

    return {"screen": screen, "params": nav_params, "label": label}

log = logging.getLogger(__name__)


def execute_module(
    module_name: str,
    params: Dict[str, Any],
    lang: str = "en",
    token: Optional[str] = None,
) -> Dict:
    """Execute a module by calling its endpoint.

    Args:
        module_name: Name of module (e.g., "astrology", "test_personality")
        params: Parameters to pass to the module (e.g., {"birth_date": "1990-05-15"})
        lang: Language code
        token: JWT token for auth (optional)

    Returns:
        {
            "status": "success" | "pending" | "error",
            "module": module_name,
            "result": {...},  # Formatted result
            "error": None or error message
        }
    """
    registry = get_registry()
    module = registry.get(module_name)

    if not module:
        return {
            "status": "error",
            "module": module_name,
            "result": None,
            "error": f"Module not found: {module_name}",
        }

    try:
        _lerr = log.error
        _mget = module.get
        endpoint = _mget("endpoint")
        method = _mget("method", "POST")

        # Build request headers
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = token

        # Test modules require special handling (2-step: start + submit)
        if module_name.startswith("test_"):
            return _execute_test_module(module_name, params, lang, headers)

        # Navigate-only modules — no HTTP call, just return action
        if method == "NAVIGATE":
            formatted = {"type": "navigate_only", "screen": _MODULE_SCREENS.get(module_name, "")}
            return {
                "status": "success",
                "module": module_name,
                "result": formatted,
                "action": build_module_action(module_name, formatted, params, lang),
                "error": None,
            }

        # Single-step modules
        payload = _build_payload(module, params, lang)

        log.info(f"Executing module '{module_name}' at {endpoint} with params {params}")

        if method == "POST":
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        else:
            response = requests.get(endpoint, params=payload, headers=headers, timeout=30)

        response.raise_for_status()
        result_data = response.json()

        formatted = format_module_result(module_name, result_data, lang)
        return {
            "status": "success",
            "module": module_name,
            "result": formatted,
            "action": build_module_action(module_name, formatted, params, lang),
            "error": None,
        }

    except requests.RequestException as e:
        _lerr(f"Module execution failed: {e}")
        return {
            "status": "error",
            "module": module_name,
            "result": None,
            "error": "Module request failed.",
        }
    except Exception as e:
        _lerr(f"Unexpected error executing module: {e}")
        return {
            "status": "error",
            "module": module_name,
            "result": None,
            "error": "Unexpected error.",
        }


def _execute_test_module(module_name: str, params: Dict, lang: str, headers: Dict) -> Dict:
    """Execute test modules which require two steps: start + submit.

    For now, just start the test and return pending status.
    The test questions will be presented to the user for answering.

    Args:
        module_name: e.g., "test_personality"
        params: Parameters for test
        lang: Language code
        headers: Request headers

    Returns:
        {"status": "pending", "module": module_name, "session_id": "...", "questions": [...]}
    """
    # Extract test_type from module name (e.g., "test_personality" -> "personality")
    test_type = module_name.replace("test_", "")

    endpoint = "http://test:8004/test/start"
    payload = {"test_type": test_type, "lang": lang}

    try:
        log.info(f"Starting test: {test_type}")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        _rget2 = result.get

        return {
            "status": "pending",
            "module": module_name,
            "test_type": test_type,
            "session_id": _rget2("session_id"),
            "questions": _rget2("questions", []),
            "error": None,
        }

    except requests.RequestException as e:
        log.error(f"Test module start failed: {e}")
        return {
            "status": "error",
            "module": module_name,
            "result": None,
            "error": "Failed to start test.",
        }


def _build_payload(module: Dict, params: Dict, lang: str) -> Dict:
    """Build request payload for module based on its type."""
    payload = {"lang": lang}
    _mname = module["name"]

    # Astrology
    if _mname == "astrology":
        if "birth_date" in params:
            payload["birth_date"] = params["birth_date"]
        if "birth_time" in params:
            payload["birth_time"] = params["birth_time"]

    # Coaching
    elif _mname == "coaching":
        # Coaching expects analysis_result
        payload["analysis_result"] = params.get("analysis_result", {})

    # Goals
    elif _mname == "goals":
        if "title" in params:
            payload["title"] = params["title"]
        if "description" in params:
            payload["description"] = params["description"]

    # Similarity
    elif _mname == "similarity":
        payload["sifatlar"] = params.get("sifatlar", [])

    # Add any custom params
    payload.update({k: v for k, v in params.items() if k != "sifatlar" or _mname == "similarity"})

    return payload


def format_module_result(module_name: str, result: Dict, lang: str = "en") -> Dict:
    """Format module result for presentation to user.

    Args:
        module_name: Name of the executed module
        result: Raw result from the module
        lang: Language code

    Returns:
        Formatted result suitable for AI presentation
    """
    _rget = result.get
    # Face Analysis result formatting — preserve full rich structure
    if module_name == "face_analysis":
        return {
            "type": "face_analysis",
            "character_summary": _rget("character_summary", ""),
            "key_attributes": _rget("key_attributes", {}),
            "attribute_descriptions": _rget("attribute_descriptions", {}),
            "measurements": _rget("measurements", {}),
        }

    # Astrology result formatting
    elif module_name == "astrology":
        return {
            "type": "astrology",
            "zodiac_sign": _rget("zodiac_sign"),
            "element": _rget("element"),
            "quality": _rget("quality"),
            "summary": _rget("summary", ""),
            "recommendations": _rget("recommendations", []),
        }

    # Test results formatting
    elif module_name.startswith("test_"):
        test_type = module_name.replace("test_", "")
        return {
            "type": "test_result",
            "test_type": test_type,
            "domain_scores": _rget("domain_scores", {}),
            "ai_interpretation": _rget("ai_interpretation", ""),
            "recommendations": _extract_recommendations(_rget("ai_interpretation", "")),
        }

    # Coaching result formatting
    elif module_name == "coaching":
        return {
            "type": "coaching",
            "dominant_attributes": _rget("dominant_sifatlar", []),
            "modules": _rget("coach_modules", {}),
            "suggestions": _extract_coaching_suggestions(result),
        }

    # Goals result formatting
    elif module_name == "goals":
        return {
            "type": "goal",
            "goal_id": _rget("_id"),
            "title": _rget("title"),
            "description": _rget("description"),
            "status": _rget("status", "active"),
        }

    # Similarity result
    elif module_name == "similarity":
        data = _rget("data", result)
        return {
            "type":            "similarity",
            "celebrity":       data.get("celebrity", {}),
            "animal":          data.get("animal", {}),
            "plant":           data.get("plant", {}),
            "object":          data.get("object", {}),
            "blend":           data.get("blend", ""),
            "primary_cluster": data.get("primary_cluster", ""),
        }

    # Default: return as-is
    return {
        "type": "generic",
        "data": result,
    }


def _extract_recommendations(interpretation: str) -> list:
    """Extract recommendations from AI interpretation text."""
    # Simple extraction: split by periods and take meaningful lines
    lines = interpretation.split(".")
    recommendations = [
        _s for line in lines for _s in (line.strip(),) if _s and len(_s) > 10
    ]
    return recommendations[:3]  # Top 3 recommendations


def _extract_coaching_suggestions(result: Dict) -> list:
    """Extract coaching suggestions from result."""
    suggestions = []
    modules = _rget("coach_modules", {})

    for module_name, module_data in modules.items():
        if isinstance(module_data, list) and module_data:
            # Get first item's description
            first_item = module_data[0]
            if isinstance(first_item, dict) and "data" in first_item:
                suggestions.append(f"{module_name}: {first_item['data'][:100]}...")

    return suggestions[:3]  # Top 3 suggestions
