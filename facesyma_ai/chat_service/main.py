"""
facesyma_ai/chat_service/main.py
=================================
Facesyma AI Asistan — FastAPI servisi.

Claude Sonnet 4.6 kullanarak:
  - Kullanıcının yüz analizi sonuçlarını yorumlar
  - 13 modül (kariyer, müzik, liderlik, vb.) hakkında soru cevaplar
  - Serbest sohbet eder, her cevap Facesyma verisine dayanır
  - Konuşma geçmişini MongoDB'de saklar

Endpoint'ler:
  POST /chat/start      → Analiz sonucuyla sohbet başlat
  POST /chat/message    → Mesaj gönder, cevap al
  GET  /chat/history    → Geçmiş konuşmaları listele
  GET  /chat/{id}       → Tek konuşmayı getir
  DELETE /chat/{id}     → Konuşmayı sil
"""

import os, json, time, uuid, logging, sys, hashlib
from datetime import datetime
from typing   import Optional

import requests
from fastapi              import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic             import BaseModel
from pymongo              import MongoClient, DESCENDING
import jwt

from facesyma_ai.core.redis_client import redis_get, redis_set

from .system_prompt import build_system_prompt
from .modules import get_registry, init_registry, ALL_MODULES, execute_module
from .intent import detect_intent
from .sifat_fetcher import build_sifat_context, format_context_for_ollama
from .routes.diet import router as diet_router

# Import RAG system if available
try:
    from ..rag.retriever import get_relevant_context
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    log.warning("⚠️  RAG system not available. Install chromadb: pip install chromadb")

# ── Django Chat Context Builder Integration ────────────────────────────────────
# Django'daki chat_context_builder'ı import et
try:
    # Path: /path/to/django/analysis_api
    DJANGO_PATH = os.environ.get("DJANGO_PATH", "/app/facesyma_backend")
    if DJANGO_PATH not in sys.path:
        sys.path.insert(0, DJANGO_PATH)

    from analysis_api.chat_context_builder import (
        build_ollama_context,
        cache_analysis_result,
        get_analysis_result
    )
    from analysis_api.ollama_system_prompt import get_system_prompt as get_ollama_prompt

    CONTEXT_BUILDER_AVAILABLE = True
    log = logging.getLogger(__name__)
    log.info("✓ Django Chat Context Builder loaded successfully")
except ImportError as e:
    log = logging.getLogger(__name__)
    log.warning(f"⚠️  Chat Context Builder not available: {e}")
    CONTEXT_BUILDER_AVAILABLE = False

# ── Yapılandırma ───────────────────────────────────────────────────────────────
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
MONGO_URI  = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/"
    "myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE"
)
JWT_SECRET  = os.environ.get("JWT_SECRET", "facesyma-jwt-secret-change-in-production")
MODEL       = "orca-mini"  # Ollama model adı
MAX_TOKENS  = 1024
MAX_HISTORY = 20   # konuşma başına max mesaj sayısı
LLM_RESPONSE_CACHE_TTL = 21600  # 6 hours

log = logging.getLogger(__name__)

# ── Ollama API Helper ──────────────────────────────────────────────────────────
def call_ollama(system_prompt: str, messages: list, cacheable: bool = False) -> str:
    """
    Ollama API'sine çağrı yap, cevap al.

    Args:
        system_prompt: System prompt for context
        messages: List of message dicts with role and content
        cacheable: If True, cache response in Redis for 6 hours.
                  Use for deterministic module calls (career, music, etc.).
                  Disable for free chat (temperature=0.7 makes caching pointless).

    Returns:
        LLM response text
    """
    # Generate cache key from system prompt + recent messages
    cache_key = None
    if cacheable:
        key_input = system_prompt[:500] + str(messages[-3:] if len(messages) >= 3 else messages)
        key_hash = hashlib.sha256(key_input.encode()).hexdigest()[:32]
        cache_key = f"llm:v1:{key_hash}"

        # Check Redis cache
        cached = redis_get(cache_key)
        if cached:
            try:
                return cached.decode()
            except Exception as e:
                log.warning(f"Failed to deserialize cached LLM response: {e}")
                # Fall through to call Ollama

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *messages
                ],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 512,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_ctx": 4096,
                }
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()["message"]["content"]

        # Cache result if cacheable
        if cacheable and cache_key:
            redis_set(cache_key, result.encode(), ttl=LLM_RESPONSE_CACHE_TTL)

        return result
    except Exception as e:
        log.error(f"Ollama error: {e}")
        raise HTTPException(500, f"AI servisi hatası: {str(e)}")

# ── MongoDB Connection Pooling ────────────────────────────────────────────────
_mongo_client: MongoClient | None = None

def get_mongo_client() -> MongoClient:
    """Get shared MongoDB client with connection pooling"""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(
            MONGO_URI,
            maxPoolSize=50,
            minPoolSize=5,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            retryWrites=True,
        )
        log.info("✓ MongoDB client initialized (pool: 5-50 connections)")
    return _mongo_client

def get_db():
    """Get facesyma-backend database with pooled connection"""
    return get_mongo_client()["facesyma-backend"]

# ── FastAPI ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Facesyma AI Asistan", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Module Registry Initialization ─────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Initialize module registry at startup."""
    registry = init_registry(ALL_MODULES)
    log.info(f"✓ Module Registry initialized with {len(registry.get_all())} modules")

# ── Modeller ──────────────────────────────────────────────────────────────────
class StartChatRequest(BaseModel):
    analysis_result: dict          # Yüz analizi sonucu (JSON)
    lang:            str = "tr"
    first_message:   Optional[str] = None  # İlk mesaj (opsiyonel)

class MessageRequest(BaseModel):
    conversation_id: str
    message:         str
    lang:            str = "tr"

class StartChatResponse(BaseModel):
    conversation_id: str
    assistant_message: str
    lang: str

class MessageResponse(BaseModel):
    conversation_id: str
    assistant_message: str
    usage: dict

# ── JWT yardımcısı ────────────────────────────────────────────────────────────
def get_user_id(authorization: Optional[str]) -> Optional[int]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token   = authorization.split(" ", 1)[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except Exception:
        return None

# ── Konuşma kayıt yardımcıları ────────────────────────────────────────────────
def save_conversation(conv_id: str, user_id: Optional[int],
                      messages: list, analysis: dict, lang: str):
    db = get_db()
    db["ai_conversations"].update_one(
        {"_id": conv_id},
        {"$set": {
            "_id":        conv_id,
            "user_id":    user_id,
            "messages":   messages[-MAX_HISTORY:],
            "analysis":   analysis,
            "lang":       lang,
            "updated_at": datetime.now().isoformat(),
        }},
        upsert=True
    )

def load_conversation(conv_id: str) -> Optional[dict]:
    db = get_db()
    return db["ai_conversations"].find_one({"_id": conv_id})

# ── Endpoint: Sohbet Başlat ───────────────────────────────────────────────────
@app.post("/chat/start", response_model=StartChatResponse)
async def start_chat(
    body:          StartChatRequest,
    authorization: Optional[str] = Header(default=None)
):
    """
    Yüz analizi sonucuyla yeni bir sohbet başlatır.
    Asistan analiz sonucunu otomatik olarak yorumlar.
    """
    user_id     = get_user_id(authorization)
    conv_id     = str(uuid.uuid4())

    # ── Adım 1: Analysis Sonucunu Cache'le ───────────────────────────────
    analysis_for_save = body.analysis_result
    if CONTEXT_BUILDER_AVAILABLE and user_id:
        try:
            cache_analysis_result(user_id, body.lang, body.analysis_result)
            log.info(f"✓ Analysis cached for user {user_id}")
        except Exception as e:
            log.warning(f"⚠️  Failed to cache analysis: {e}")

    # ── Adım 2: Context Oluştur (Ollama'ya gönderilecek) ──────────────────
    system_msg = None
    if CONTEXT_BUILDER_AVAILABLE and user_id:
        try:
            ollama_context = build_ollama_context(user_id, body.lang)
            system_msg = get_ollama_prompt(body.lang, ollama_context)
            analysis_for_save = ollama_context.get("user", body.analysis_result)
            log.info(f"✓ Ollama context built with enriched data")
        except Exception as e:
            log.warning(f"⚠️  Failed to build context: {e}, falling back to basic system prompt")
            system_msg = None

    # ── Fallback: Temel system prompt ────────────────────────────────────
    if not system_msg:
        system_msg = build_system_prompt(body.analysis_result, body.lang)

    # İlk kullanıcı mesajı — belirtilmezse default
    if body.first_message:
        user_text = body.first_message
    else:
        greetings = {
            "tr": "Merhaba! Analiz sonuçlarımı açıklar mısın?",
            "en": "Hello! Can you explain my analysis results?",
            "de": "Hallo! Kannst du mir meine Analyseergebnisse erklären?",
            "ru": "Привет! Можешь объяснить мои результаты анализа?",
            "ar": "مرحبا! هل يمكنك شرح نتائج تحليلي؟",
            "es": "¡Hola! ¿Puedes explicarme mis resultados de análisis?",
            "ko": "안녕하세요! 분석 결과를 설명해 주실 수 있나요?",
            "ja": "こんにちは！分析結果を説明していただけますか？",
        }
        user_text = greetings.get(body.lang, greetings["tr"])

    messages = [{"role": "user", "content": user_text}]

    # Ollama'ya gönder
    assistant_text = call_ollama(system_msg, messages)
    messages.append({"role": "assistant", "content": assistant_text})

    # Kaydet (enriched context varsa o, yoksa original analysis)
    save_conversation(conv_id, user_id, messages, analysis_for_save, body.lang)

    return StartChatResponse(
        conversation_id   = conv_id,
        assistant_message = assistant_text,
        lang              = body.lang,
    )

# ── Endpoint: Mesaj Gönder (with Orchestration) ─────────────────────────────
@app.post("/chat/message", response_model=MessageResponse)
async def send_message(
    body:          MessageRequest,
    authorization: Optional[str] = Header(default=None)
):
    """
    Mevcut sohbete mesaj gönderir, asistandan cevap alır.

    NEW: Intent detection ve module orchestration destekler.
    Kullanıcı bir modül ile ilgili bir şey söylerse (ör. "doğum tarihim..."),
    ilgili modülü çalıştırır ve sonucu sohbete ekler.
    """
    conv = load_conversation(body.conversation_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı.")

    user_lang = body.lang or conv.get("lang", "tr")
    messages = conv.get("messages", [])

    # ── Adım 1: Intent Detection ─────────────────────────────────────────────
    intent_result = detect_intent(body.message, user_lang)
    log.info(f"Intent detected: {intent_result.get('intent')} (confidence: {intent_result.get('confidence')})")

    # ── Adım 2: Module Execution (if module intent) ──────────────────────────
    module_context = ""
    if intent_result.get("intent") != "chat":
        module_name = intent_result.get("intent")
        registry = get_registry()
        module = registry.get(module_name)

        if module:
            # Execute the module
            exec_result = execute_module(
                module_name,
                intent_result.get("params", {}),
                user_lang,
                token=authorization
            )

            if exec_result.get("status") == "success":
                # Format module result for AI context
                result_data = exec_result.get("result", {})

                # Special handling: Store face_analysis in conversation analysis
                if module_name == "face_analysis":
                    conv["analysis"]["face_analysis"] = result_data
                    log.info(f"✓ Face analysis stored in conversation")

                module_context = f"\n\n[Modül Sonucu: {module_name}]\n{json.dumps(result_data, ensure_ascii=False, indent=2)}"
                log.info(f"✓ Module executed successfully: {module_name}")
            elif exec_result.get("status") == "pending":
                # Test module - return questions to user
                return MessageResponse(
                    conversation_id=body.conversation_id,
                    assistant_message=json.dumps({
                        "type": "test_pending",
                        "test_type": exec_result.get("test_type"),
                        "session_id": exec_result.get("session_id"),
                        "questions": exec_result.get("questions", []),
                    }, ensure_ascii=False),
                    usage={"input_tokens": 0, "output_tokens": 0},
                )

    # ── Adım 3: System Prompt ───────────────────────────────────────────────
    # Try to use enriched context builder if available
    system_msg = None
    user_id_for_context = get_user_id(authorization)

    if CONTEXT_BUILDER_AVAILABLE and user_id_for_context:
        try:
            ollama_context = build_ollama_context(user_id_for_context, user_lang)
            system_msg = get_ollama_prompt(user_lang, ollama_context)
            log.info(f"✓ Ollama context used for message endpoint")
        except Exception as e:
            log.warning(f"⚠️  Failed to build context for message: {e}, using basic prompt")
            system_msg = None

    # Fallback: Temel system prompt
    if not system_msg:
        system_msg = build_system_prompt(conv["analysis"], user_lang)

    # Eğer modül context varsa (tavsiye, motivasyon, vb.), sıfat cümlelerini ekle
    if module_context and intent_result.get("intent") != "chat":
        module_name = intent_result.get("intent")
        detected_sifatlar = conv["analysis"].get("face_analysis", {}).get("key_attributes", {})

        if detected_sifatlar:
            # Sıfat context oluştur
            sifat_context = build_sifat_context(
                list(detected_sifatlar.keys()),
                module_name,
                sifat_details={
                    sifat: {"score": score}
                    for sifat, score in detected_sifatlar.items()
                },
                lang=user_lang
            )

            # Ollama için format
            formatted_sifat = format_context_for_ollama(sifat_context, user_lang)
            system_msg += formatted_sifat
            log.info(f"✓ Sıfat context eklendi: {len(detected_sifatlar)} sıfat")

    # ── Adım 4: Build Message History ────────────────────────────────────────
    messages.append({"role": "user", "content": body.message})
    trimmed = messages[-MAX_HISTORY:]

    # Add module context to system message if available
    if module_context:
        system_msg += module_context

    # ── Adım 5: Inject RAG Context ───────────────────────────────────────────
    if RAG_AVAILABLE:
        try:
            # Get top sifatlar from analysis
            analysis = conv.get("analysis", {})
            top_sifatlar = []

            # Try to get from face_analysis
            if "face_analysis" in analysis:
                key_attrs = analysis["face_analysis"].get("key_attributes", {})
                top_sifatlar = list(key_attrs.keys())[:10]

            # Get RAG context based on user message and sifatlar
            if top_sifatlar or body.message:
                rag_context = get_relevant_context(
                    body.message,
                    top_sifatlar,
                    user_lang
                )
                if rag_context:
                    system_msg += f"\n\n## Bilgi Tabanı\n{rag_context}"
                    log.info(f"✓ RAG context injected ({len(rag_context)} chars)")
        except Exception as e:
            log.warning(f"⚠️  RAG context injection failed: {e}")

    # ── Adım 6: Call Ollama ──────────────────────────────────────────────────
    assistant_text = call_ollama(system_msg, trimmed)
    messages.append({"role": "assistant", "content": assistant_text})

    # ── Adım 7: Save Conversation ────────────────────────────────────────────
    save_conversation(
        body.conversation_id,
        get_user_id(authorization),
        messages,
        conv["analysis"],
        user_lang,
    )

    return MessageResponse(
        conversation_id   = body.conversation_id,
        assistant_message = assistant_text,
        usage             = {
            "input_tokens":  0,
            "output_tokens": 0,
        },
    )

# ── Endpoint: Konuşma Geçmişi ─────────────────────────────────────────────────
@app.get("/chat/history")
async def get_history(authorization: Optional[str] = Header(default=None)):
    user_id = get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Kimlik doğrulama gerekli.")

    db   = get_db()
    docs = list(
        db["ai_conversations"]
        .find({"user_id": user_id}, {"messages": 0})
        .sort("updated_at", DESCENDING)
        .limit(20)
    )
    for d in docs:
        d["id"] = d.pop("_id")
    return {"conversations": docs}

# ── Endpoint: Tek Konuşma ─────────────────────────────────────────────────────
@app.get("/chat/{conversation_id}")
async def get_conversation(conversation_id: str):
    conv = load_conversation(conversation_id)
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı.")
    conv["id"] = conv.pop("_id")
    return conv

# ── Endpoint: Konuşmayı Sil ───────────────────────────────────────────────────
@app.delete("/chat/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    authorization:   Optional[str] = Header(default=None)
):
    user_id = get_user_id(authorization)
    db      = get_db()
    result  = db["ai_conversations"].delete_one(
        {"_id": conversation_id, "user_id": user_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(404, "Konuşma bulunamadı veya izniniz yok.")
    return {"deleted": True}

# ── Endpoint: Mevcut Modüller ────────────────────────────────────────────────
@app.get("/modules")
async def list_modules(lang: str = "tr"):
    """Mevcut tüm modüllerin listesini döner."""
    registry = get_registry()
    modules = []

    for module in registry.get_all():
        modules.append({
            "name": module["name"],
            "display": module.get("display", {}).get(lang, module["name"]),
            "description": module.get("description", {}).get(lang, ""),
            "requires_input": module.get("requires_input"),
        })

    return {"modules": modules, "total": len(modules)}

# ── Sağlık kontrolü ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    registry = get_registry()
    return {
        "status": "ok",
        "model": MODEL,
        "modules_registered": len(registry.get_all()),
    }

# ── Desteklenen diller ────────────────────────────────────────────────────────
@app.get("/languages")
async def get_languages():
    """Desteklenen dillerin listesini döner — mobil/web dil seçici için."""
    from .system_prompt import get_supported_languages
    return {"languages": get_supported_languages()}

# ── Beslenme Koçluğu Router ────────────────────────────────────────────────────
app.include_router(diet_router)
log.info("✓ Diet coaching router included")
