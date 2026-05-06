"""
facesyma_ai/chat_service/memory_manager.py
==========================================
Faz 4 — Uzun Vadeli Hafıza

Kullanıcı mesajlarından rule-based + AI insight çıkarır ve MongoDB
`ai_user_memory` koleksiyonuna kaydeder.  Sonraki konuşmalarda
bu hafıza sistem promptuna enjekte edilir.

Public API:
  extract_and_save(user_id, user_message, conversation_id, lang, db)
  extract_and_save_summary(user_id, messages, conversation_id, lang, db)
  get_memory_prompt_section(user_id, lang, db) → str
  get_memories(user_id, db) → list
  delete_memory(user_id, memory_id, db) → bool
"""

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone

log = logging.getLogger(__name__)

MAX_MEMORIES    = 40   # per user (expanded for summaries)
MAX_MEM_LEN     = 160  # chars per memory item
MIN_MSGS_SUMMARY = 4   # min user messages to trigger AI summary

# ── Groq lazy client (avoids circular import from main.py) ───────────────────
_groq_client = None

def _get_groq():
    global _groq_client
    if _groq_client is None:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
        except Exception as e:
            log.warning(f"Groq init failed in memory_manager: {e}")
    return _groq_client

# ── Dil etiketleri ────────────────────────────────────────────────────────────
_SECTION_LABELS = {
    "tr": "## Önceki Konuşmalardan Hatırladıklarım",
    "en": "## What I Remember From Previous Chats",
    "de": "## Was ich aus früheren Gesprächen erinnere",
    "ru": "## Что я помню из прошлых разговоров",
    "ar": "## ما أتذكره من المحادثات السابقة",
    "es": "## Lo que recuerdo de conversaciones anteriores",
    "ko": "## 이전 대화에서 기억하는 것",
    "ja": "## 以前の会話から覚えていること",
    "zh": "## 我从以前对话中记住的",
    "fr": "## Ce que je me souviens des conversations précédentes",
    "pt": "## O que lembro das conversas anteriores",
    "hi": "## पिछली बातचीत से मुझे जो याद है",
    "id": "## Yang Saya Ingat dari Percakapan Sebelumnya",
    "it": "## Quello che ricordo dalle conversazioni precedenti",
    "pl": "## Co pamiętam z poprzednich rozmów",
    "bn": "## আগের কথোপকথন থেকে যা মনে আছে",
    "ur": "## پچھلی گفتگو سے جو مجھے یاد ہے",
    "vi": "## Những Gì Tôi Nhớ Từ Các Cuộc Trò Chuyện Trước",
}

# ── Pattern maps per language ────────────────────────────────────────────────
# Each entry: (category, compiled_regex)
# category: goal | preference | emotion | concern | insight

def _pat(s: str) -> re.Pattern:
    return re.compile(s, re.IGNORECASE)

_PATTERNS_TR = [
    ("goal",       _pat(r"\b(hedefim|hayalim|olmak istiyorum|yapmak istiyorum|planım|niyetim)\b")),
    ("goal",       _pat(r"\bdeğiştirmek istiyorum\b")),
    ("preference", _pat(r"\b(seviyorum|severim|hoşlanıyorum|tercih ederim|beğeniyorum)\b")),
    ("preference", _pat(r"\b(sever[im]+)\b")),
    ("emotion",    _pat(r"\b(mutluyum|mutsuzum|heyecanlıyım|kızgınım|üzgünüm|bunaldım|yoruldum|motivasyonum yok)\b")),
    ("emotion",    _pat(r"\bhissediyorum\b")),
    ("concern",    _pat(r"\b(endişeleniyorum|kaygılıyım|korkuyorum|tedirginim)\b")),
    ("insight",    _pat(r"\b(içe dönüğüm|dışa dönüğüm|lider değilim|sosyal değilim|analitik biriyim|yaratıcı biriyim)\b")),
]

_PATTERNS_EN = [
    ("goal",       _pat(r"\b(my goal|my dream|i want to|i plan to|i'm planning|i aim to|i hope to)\b")),
    ("preference", _pat(r"\b(i love|i like|i enjoy|i prefer|i'm into|i'm a fan of)\b")),
    ("emotion",    _pat(r"\b(i feel|i'm feeling|i'm (happy|sad|excited|anxious|stressed|burnt out|motivated|lost))\b")),
    ("concern",    _pat(r"\b(i'm worried|i'm concerned|i'm scared|i'm anxious about)\b")),
    ("insight",    _pat(r"\b(i'm (introverted|extroverted|analytical|creative|a leader|not good at|terrible at))\b")),
]

# ── Latin-script languages (de, es, fr, pt, it, pl, id, vi) ──────────────────
_PATTERNS_DE = [
    ("goal",       _pat(r"\b(mein ziel|mein traum|ich möchte|ich will|ich plane|ich hoffe)\b")),
    ("preference", _pat(r"\b(ich liebe|ich mag|ich genieße|ich bevorzuge)\b")),
    ("emotion",    _pat(r"\bich fühle\b|\bbin (glücklich|traurig|gestresst|ängstlich|ausgebrannt|motiviert)\b")),
    ("concern",    _pat(r"\b(ich mache mir sorgen|ich bin besorgt|ich habe angst)\b")),
    ("insight",    _pat(r"\bich bin (introvertiert|extrovertiert|analytisch|kreativ)\b")),
]

_PATTERNS_ES = [
    ("goal",       _pat(r"\b(mi objetivo|mi sueño|quiero|planeo|tengo pensado|espero)\b")),
    ("preference", _pat(r"\b(me gusta|me encanta|prefiero|disfruto|adoro)\b")),
    ("emotion",    _pat(r"\bme siento\b|\bestoy (feliz|triste|ansioso|estresado|agotado|emocionado|motivado)\b")),
    ("concern",    _pat(r"\b(me preocupa|estoy preocupado|tengo miedo)\b")),
    ("insight",    _pat(r"\bsoy (introvertido|extrovertido|analítico|creativo)\b")),
]

_PATTERNS_FR = [
    ("goal",       _pat(r"\b(mon objectif|mon rêve|je veux|je prévois|j'espère|je compte)\b")),
    ("preference", _pat(r"\b(j'aime|j'adore|je préfère|j'apprécie)\b")),
    ("emotion",    _pat(r"\bje me sens\b|\bje suis (heureux|heureuse|triste|anxieux|stressé|épuisé|motivé)\b")),
    ("concern",    _pat(r"\b(je m'inquiète|je suis inquiet|j'ai peur)\b")),
    ("insight",    _pat(r"\bje suis (introverti|extraverti|analytique|créatif)\b")),
]

_PATTERNS_PT = [
    ("goal",       _pat(r"\b(meu objetivo|meu sonho|eu quero|eu planejo|espero)\b")),
    ("preference", _pat(r"\b(eu gosto|eu amo|prefiro|curto|adoro)\b")),
    ("emotion",    _pat(r"\bme sinto\b|\bestou (feliz|triste|ansioso|estressado|esgotado|motivado)\b")),
    ("concern",    _pat(r"\b(estou preocupado|tenho medo|me preocupo)\b")),
    ("insight",    _pat(r"\bsou (introvertido|extrovertido|analítico|criativo)\b")),
]

_PATTERNS_IT = [
    ("goal",       _pat(r"\b(il mio obiettivo|il mio sogno|voglio|ho intenzione|spero di)\b")),
    ("preference", _pat(r"\b(mi piace|amo|preferisco|adoro|mi diverto)\b")),
    ("emotion",    _pat(r"\bmi sento\b|\bsono (felice|triste|ansioso|stressato|esaurito|motivato)\b")),
    ("concern",    _pat(r"\b(sono preoccupato|ho paura|mi preoccupo)\b")),
    ("insight",    _pat(r"\bsono (introverso|estroverso|analitico|creativo)\b")),
]

_PATTERNS_PL = [
    ("goal",       _pat(r"\b(moim celem|moim marzeniem|chcę|planuję|zamierzam)\b")),
    ("preference", _pat(r"\b(lubię|kocham|wolę|uwielbiam|cieszę się)\b")),
    ("emotion",    _pat(r"\bczuję się\b|\bjestem (szczęśliwy|smutny|niespokojny|zestresowany|wypalony|zmotywowany)\b")),
    ("concern",    _pat(r"\b(martwię się|boję się|jestem zaniepokojony)\b")),
    ("insight",    _pat(r"\bjestem (introwertykiem|ekstrawertykiem|analityczny|kreatywny)\b")),
]

_PATTERNS_ID = [
    ("goal",       _pat(r"\b(tujuan saya|impian saya|saya ingin|saya berencana|saya bermimpi)\b")),
    ("preference", _pat(r"\b(saya suka|saya senang|saya lebih suka|saya menikmati|saya cinta)\b")),
    ("emotion",    _pat(r"\bsaya merasa\b|\bsaya (bahagia|sedih|cemas|stres|kelelahan|termotivasi)\b")),
    ("concern",    _pat(r"\b(saya khawatir|saya takut|saya cemas)\b")),
    ("insight",    _pat(r"\bsaya (introvert|ekstrovert|analitis|kreatif)\b")),
]

_PATTERNS_VI = [
    ("goal",       _pat(r"\b(mục tiêu của tôi|ước mơ của tôi|tôi muốn|tôi dự định|tôi mong)\b")),
    ("preference", _pat(r"\b(tôi thích|tôi yêu|tôi ưa|tôi thưởng thức)\b")),
    ("emotion",    _pat(r"\btôi cảm thấy\b|\btôi (hạnh phúc|buồn|lo lắng|căng thẳng|kiệt sức|có động lực)\b")),
    ("concern",    _pat(r"\b(tôi lo lắng|tôi sợ|tôi lo ngại)\b")),
    ("insight",    _pat(r"\btôi là người (hướng nội|hướng ngoại|phân tích|sáng tạo)\b")),
]

# ── Cyrillic ─────────────────────────────────────────────────────────────────
_PATTERNS_RU = [
    ("goal",       _pat(r"\b(моя цель|моя мечта|я хочу|я планирую|я собираюсь|я надеюсь)\b")),
    ("preference", _pat(r"\b(я люблю|мне нравится|я предпочитаю|я обожаю)\b")),
    ("emotion",    _pat(r"\bя чувствую\b|\bя (счастлив|грустен|тревожен|напряжён|выгорел|мотивирован)\b")),
    ("concern",    _pat(r"\b(я беспокоюсь|я волнуюсь|я боюсь|мне страшно)\b")),
    ("insight",    _pat(r"\bя (интроверт|экстраверт|аналитический|творческий)\b")),
]

# ── RTL + Indic scripts (no \b — word boundary unreliable for these scripts) ─
_PATTERNS_AR = [
    ("goal",       _pat(r"(هدفي|حلمي|أريد أن|أخطط ل|أتمنى أن)")),
    ("preference", _pat(r"(أحب|أعشق|أفضل|أستمتع)")),
    ("emotion",    _pat(r"(أشعر|أنا سعيد|أنا حزين|أنا قلق|أنا متوتر|أنا محفوز)")),
    ("concern",    _pat(r"(أشعر بالقلق|أخشى|أخاف من|أنا خائف)")),
    ("insight",    _pat(r"(أنا انطوائي|أنا انبساطي|أنا تحليلي|أنا مبدع)")),
]

_PATTERNS_HI = [
    ("goal",       _pat(r"(मेरा लक्ष्य|मेरा सपना|मैं चाहता हूं|मेरी योजना|मुझे उम्मीद है)")),
    ("preference", _pat(r"(मुझे पसंद है|मुझे अच्छा लगता है|मैं पसंद करता हूं|मुझे प्यार है)")),
    ("emotion",    _pat(r"(मैं खुश|मैं दुखी|मैं चिंतित|मैं तनावग्रस्त|मैं थका|मुझे लगता है)")),
    ("concern",    _pat(r"(मुझे चिंता है|मैं डरता हूं|मुझे डर है)")),
    ("insight",    _pat(r"(मैं अंतर्मुखी|मैं बहिर्मुखी|मैं विश्लेषणात्मक|मैं रचनात्मक)")),
]

_PATTERNS_BN = [
    ("goal",       _pat(r"(আমার লক্ষ্য|আমার স্বপ্ন|আমি চাই|আমার পরিকল্পনা|আমি আশা করি)")),
    ("preference", _pat(r"(আমি পছন্দ করি|আমি ভালোবাসি|আমি উপভোগ করি|আমার ভালো লাগে)")),
    ("emotion",    _pat(r"(আমি অনুভব করি|আমি খুশি|আমি দুঃখী|আমি উদ্বিগ্ন|আমি চাপে|আমি ক্লান্ত)")),
    ("concern",    _pat(r"(আমি চিন্তিত|আমি ভয় পাচ্ছি|আমার ভয় হচ্ছে)")),
    ("insight",    _pat(r"(আমি অন্তর্মুখী|আমি বহির্মুখী|আমি বিশ্লেষণাত্মক|আমি সৃজনশীল)")),
]

_PATTERNS_UR = [
    ("goal",       _pat(r"(میرا مقصد|میرا خواب|میں چاہتا ہوں|میری منصوبہ بندی|مجھے امید ہے)")),
    ("preference", _pat(r"(مجھے پسند ہے|مجھے اچھا لگتا ہے|میں پسند کرتا ہوں|مجھے محبت ہے)")),
    ("emotion",    _pat(r"(میں محسوس کرتا|میں خوش|میں اداس|میں پریشان|میں تناؤ میں|میں تھکا)")),
    ("concern",    _pat(r"(میں فکرمند ہوں|مجھے ڈر ہے|میں ڈرتا ہوں)")),
    ("insight",    _pat(r"(میں انٹروورٹ|میں ایکسٹروورٹ|میں تجزیاتی|میں تخلیقی)")),
]

# ── CJK scripts (no \b — characters are not space-delimited) ─────────────────
_PATTERNS_KO = [
    ("goal",       _pat(r"(목표는|꿈은|하고 싶어|계획이야|하려고 해|원해)")),
    ("preference", _pat(r"(좋아해|좋아|즐겨|선호해|사랑해)")),
    ("emotion",    _pat(r"(기분이|행복해|슬퍼|불안해|스트레스|지쳤어|의욕이 없어|기뻐|느껴)")),
    ("concern",    _pat(r"(걱정돼|두려워|불안해|무서워)")),
    ("insight",    _pat(r"(내향적이야|외향적이야|분석적이야|창의적이야)")),
]

_PATTERNS_JA = [
    ("goal",       _pat(r"(目標は|夢は|したい|計画して|希望して|なりたい)")),
    ("preference", _pat(r"(好きです|好き|楽しんで|好みます|大好き)")),
    ("emotion",    _pat(r"(感じます|気分は|嬉しい|悲しい|不安|ストレス|疲れた|やる気がない)")),
    ("concern",    _pat(r"(心配です|怖い|不安です|恐れて)")),
    ("insight",    _pat(r"(内向的|外向的|分析的|創造的)")),
]

_PATTERNS_ZH = [
    ("goal",       _pat(r"(我的目标|我的梦想|我想|我计划|我希望|我打算)")),
    ("preference", _pat(r"(我喜欢|我爱|我偏好|我享受|我热爱)")),
    ("emotion",    _pat(r"(我感到|我觉得|我很开心|我很难过|我很焦虑|我很有压力|我很疲惫|我很有动力)")),
    ("concern",    _pat(r"(我担心|我害怕|我忧虑|我恐惧)")),
    ("insight",    _pat(r"(我是内向|我是外向|我很分析|我很有创意)")),
]

_LANG_PATTERNS: dict[str, list] = {
    "tr": _PATTERNS_TR,
    "en": _PATTERNS_EN,
    "de": _PATTERNS_DE,
    "es": _PATTERNS_ES,
    "fr": _PATTERNS_FR,
    "pt": _PATTERNS_PT,
    "it": _PATTERNS_IT,
    "pl": _PATTERNS_PL,
    "id": _PATTERNS_ID,
    "vi": _PATTERNS_VI,
    "ru": _PATTERNS_RU,
    "ar": _PATTERNS_AR,
    "hi": _PATTERNS_HI,
    "bn": _PATTERNS_BN,
    "ur": _PATTERNS_UR,
    "ko": _PATTERNS_KO,
    "ja": _PATTERNS_JA,
    "zh": _PATTERNS_ZH,
}


def _get_patterns(lang: str) -> list:
    return _LANG_PATTERNS.get(lang, _PATTERNS_EN)


def _extract_sentences(text: str) -> list[str]:
    """Split text into sentences across all supported scripts."""
    # Latin/Arabic/Urdu  . ! ? ؟ ،
    # CJK/Japanese       。 ！ ？ 、 ；
    # Korean             。 ！ ？ + standard
    sentences = re.split(r'[.!?؟،。！？、；\n]+\s*', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 5]


def extract_memories_from_message(user_message: str, lang: str) -> list[dict]:
    """
    Rule-based extraction of 0-3 memory items from a single user message.
    Returns list of {category, content} dicts.
    """
    _lang = lang if lang in _LANG_PATTERNS else "en"
    patterns = _get_patterns(_lang)
    results = []
    seen_sentences: set[str] = set()

    sentences = _extract_sentences(user_message)
    for sentence in sentences:
        for category, pattern in patterns:
            if pattern.search(sentence):
                clean = sentence[:MAX_MEM_LEN].strip()
                if clean and clean not in seen_sentences:
                    seen_sentences.add(clean)
                    results.append({"category": category, "content": clean})
                break  # only one category per sentence

    return results[:3]  # max 3 per message


def extract_and_save(
    user_id: int,
    user_message: str,
    conversation_id: str,
    lang: str,
    db,
) -> None:
    """
    Extract memories from user_message and save to ai_user_memory.
    Silently fails — never raises.
    """
    if not user_id or not user_message:
        return
    try:
        new_mems = extract_memories_from_message(user_message, lang)
        if not new_mems:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        mem_docs = [
            {
                "id": str(uuid.uuid4()),
                "content": m["content"],
                "category": m["category"],
                "created_at": now_iso,
                "conversation_id": conversation_id,
            }
            for m in new_mems
        ]

        col = db["ai_user_memory"]
        doc = col.find_one({"user_id": user_id}, {"_id": 0, "memories": 1})

        existing: list = (doc or {}).get("memories", [])
        combined = existing + mem_docs

        # Evict oldest if over limit
        if len(combined) > MAX_MEMORIES:
            combined = combined[-MAX_MEMORIES:]

        col.update_one(
            {"user_id": user_id},
            {"$set": {"memories": combined, "updated_at": now_iso}},
            upsert=True,
        )
        log.debug(f"✓ Saved {len(mem_docs)} memories for user {user_id}")
    except Exception as e:
        log.debug(f"Memory save failed for user {user_id}: {e}")


def get_memory_prompt_section(user_id: int, lang: str, db, limit: int = 8) -> str:
    """
    Returns formatted memory section for system prompt injection.
    Empty string if no memories found.
    """
    if not user_id:
        return ""
    try:
        doc = db["ai_user_memory"].find_one(
            {"user_id": user_id},
            {"_id": 0, "memories": 1},
        )
        if not doc:
            return ""

        memories: list = (doc.get("memories") or [])
        if not memories:
            return ""

        # Most recent N memories
        recent = memories[-limit:]
        section_title = _SECTION_LABELS.get(lang, _SECTION_LABELS["en"])
        lines = [section_title]
        for m in recent:
            cat = m.get("category", "")
            content = m.get("content", "")
            if content:
                lines.append(f"• [{cat}] {content}")

        return "\n".join(lines) if len(lines) > 1 else ""
    except Exception as e:
        log.debug(f"Memory fetch failed for user {user_id}: {e}")
        return ""


def get_memories(user_id: int, db) -> list:
    """Return full memory list for a user (for API endpoint)."""
    if not user_id:
        return []
    try:
        doc = db["ai_user_memory"].find_one({"user_id": user_id}, {"_id": 0})
        return (doc or {}).get("memories", [])
    except Exception as e:
        log.debug(f"get_memories failed: {e}")
        return []


def delete_memory(user_id: int, memory_id: str, db) -> bool:
    """Remove a single memory by id. Returns True if something was deleted."""
    if not user_id or not memory_id:
        return False
    try:
        col = db["ai_user_memory"]
        doc = col.find_one({"user_id": user_id}, {"_id": 0, "memories": 1})
        if not doc:
            return False
        original = doc.get("memories", [])
        filtered = [m for m in original if m.get("id") != memory_id]
        if len(filtered) == len(original):
            return False
        col.update_one(
            {"user_id": user_id},
            {"$set": {"memories": filtered, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        return True
    except Exception as e:
        log.debug(f"delete_memory failed: {e}")
        return False


# ── AI-powered conversation summary ──────────────────────────────────────────

_SUMMARY_PROMPTS = {
    "tr": (
        "Aşağıda bir kullanıcı ile yapay zeka koç arasındaki konuşma var.\n"
        "Bu konuşmadan kullanıcı hakkında 3-5 önemli bilgiyi JSON listesi olarak çıkar.\n"
        "Her madde: {{\"category\": \"goal|preference|emotion|concern|insight\", \"content\": \"kısa cümle (max 140 karakter)\"}}\n"
        "Sadece JSON listesini döndür, başka bir şey ekleme.\n\n"
        "Konuşma:\n{conversation}"
    ),
    "en": (
        "Below is a conversation between a user and an AI coach.\n"
        "Extract 3-5 key facts about the user as a JSON list.\n"
        "Each item: {{\"category\": \"goal|preference|emotion|concern|insight\", \"content\": \"short sentence (max 140 chars)\"}}\n"
        "Return ONLY the JSON list, nothing else.\n\n"
        "Conversation:\n{conversation}"
    ),
}

def _format_msgs_for_summary(messages: list) -> str:
    lines = []
    for m in messages:
        role = "Kullanıcı" if m.get("role") == "user" else "Koç"
        content = (m.get("content") or "")[:300]
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def extract_and_save_summary(
    user_id: int,
    messages: list,
    conversation_id: str,
    lang: str,
    db,
) -> None:
    """
    Use Groq to extract structured insights from a completed conversation.
    Called once when the conversation has >= MIN_MSGS_SUMMARY user messages.
    Silently fails — never raises.
    """
    if not user_id or not messages:
        return

    user_msgs = [m for m in messages if m.get("role") == "user"]
    if len(user_msgs) < MIN_MSGS_SUMMARY:
        return

    client = _get_groq()
    if not client:
        return

    try:
        _lang = lang if lang in _SUMMARY_PROMPTS else "en"
        conv_text = _format_msgs_for_summary(messages[-20:])  # last 20 msgs
        prompt = _SUMMARY_PROMPTS[_lang].format(conversation=conv_text)

        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512,
        )
        raw = (resp.choices[0].message.content or "").strip()

        # Parse JSON — handle markdown code fences
        if raw.startswith("```"):
            raw = re.sub(r"```[a-z]*\n?", "", raw).replace("```", "").strip()
        items = json.loads(raw)
        if not isinstance(items, list):
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        new_mems = []
        for item in items[:5]:
            content = (item.get("content") or "")[:MAX_MEM_LEN].strip()
            cat     = item.get("category", "insight")
            if content:
                new_mems.append({
                    "id":              str(uuid.uuid4()),
                    "content":         content,
                    "category":        cat,
                    "source":          "ai_summary",
                    "created_at":      now_iso,
                    "conversation_id": conversation_id,
                })

        if not new_mems:
            return

        col = db["ai_user_memory"]
        doc = col.find_one({"user_id": user_id}, {"_id": 0, "memories": 1})
        existing: list = (doc or {}).get("memories", [])
        combined = existing + new_mems
        if len(combined) > MAX_MEMORIES:
            combined = combined[-MAX_MEMORIES:]

        col.update_one(
            {"user_id": user_id},
            {"$set": {"memories": combined, "updated_at": now_iso}},
            upsert=True,
        )
        log.info(f"✓ AI summary saved {len(new_mems)} memories for user {user_id}")
    except Exception as e:
        log.debug(f"AI summary extraction failed for user {user_id}: {e}")
