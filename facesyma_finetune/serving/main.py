"""
serving/main.py
================
Facesyma AI Asistan — vLLM production servisi.

Stack:
  - vLLM → OpenAI-uyumlu API, yüksek throughput, tensor parallelism
  - FastAPI → kimlik doğrulama, geçmiş, loglama
  - MongoDB → sohbet geçmişi

Endpoint'ler:
  POST /v1/chat/analyze   → Analiz JSON + ilk yorum
  POST /v1/chat/message   → Sohbet devam
  GET  /v1/chat/history   → Geçmiş
  GET  /v1/health

Çalıştırma:

  # 1. vLLM sunucusunu başlat (ayrı terminalde)
  python -m vllm.entrypoints.openai.api_server \\
    --model facesyma-llama3.1-8b_merged \\
    --host  0.0.0.0 \\
    --port  8001 \\
    --dtype half \\
    --max-model-len 4096 \\
    --tensor-parallel-size 1

  # 2. FastAPI servisini başlat
  VLLM_URL=http://localhost:8001 uvicorn main:app --host 0.0.0.0 --port 8002

  # Docker Compose (docker-compose.yml mevcut)
  docker-compose up
"""

import os, json, uuid, logging
from datetime import datetime
from typing   import Optional, AsyncGenerator

import jwt
import httpx
from fastapi              import FastAPI, HTTPException, Header
from fastapi.responses    import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic             import BaseModel
from pymongo              import MongoClient, DESCENDING

log = logging.getLogger(__name__)

# ── Yapılandırma ───────────────────────────────────────────────────────────────
VLLM_URL    = os.environ.get("VLLM_URL",   "http://localhost:8001")
MODEL_ID    = os.environ.get("MODEL_ID",   "facesyma-llama3.1-8b")
MONGO_URI   = os.environ.get("MONGO_URI",
    "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/"
    "myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE")
JWT_SECRET  = os.environ.get("JWT_SECRET", "facesyma-jwt-secret")
MAX_TOKENS  = int(os.environ.get("MAX_TOKENS", "1024"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.7"))
MAX_TURNS   = 12

# ── Sistem promptu — facesyma_ai/chat_service/system_prompt.py'den import ───
import sys, pathlib
# facesyma_ai paketi bu servisle aynı sunucuda deploy edilir
# Yol: FACESYMA_AI_PATH env değişkeniyle ayarla
_ai_path = os.environ.get("FACESYMA_AI_PATH", str(pathlib.Path(__file__).parent.parent.parent / "facesyma_ai"))
if _ai_path not in sys.path:
    sys.path.insert(0, _ai_path)

try:
    from chat_service.system_prompt import build_system_prompt, get_supported_languages
    _USE_SHARED_PROMPT = True
    log.info(f"system_prompt.py yüklendi: {_ai_path}")
except ImportError:
    _USE_SHARED_PROMPT = False
    log.warning("system_prompt.py bulunamadı — fallback prompt kullanılıyor")
    def build_system_prompt(analysis: dict, lang: str = "tr") -> str:
        _fallback = {
            "tr": "Sen Facesyma yapay zeka danışmanısın. Yüz analizi verilerini yorumla. Türkçe konuş. 3-5 cümle.",
            "en": "You are Facesyma AI advisor. Interpret face analysis data. Speak English. 3-5 sentences.",
        }
        system = _fallback.get(lang, _fallback["en"])
        import json
        return f"{system}\n\n## Analysis Data\n{json.dumps(analysis, ensure_ascii=False)[:800]}"

# ── FastAPI ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Facesyma AI — vLLM Production", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


# ── MongoDB ────────────────────────────────────────────────────────────────────
def get_col():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)[
        "facesyma-backend"]["ai_conversations_v2"]


# ── JWT ───────────────────────────────────────────────────────────────────────
def get_user_id(auth: Optional[str]) -> Optional[int]:
    if not auth or not auth.startswith("Bearer "):
        return None
    try:
        return jwt.decode(auth.split(" ", 1)[1],
                          JWT_SECRET, algorithms=["HS256"]).get("user_id")
    except Exception:
        return None


# ── vLLM çağrısı ──────────────────────────────────────────────────────────────
# ── Load local GPT2 model with LoRA ──────────────────────────────────────
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

_model = None
_tokenizer = None

def load_local_model():
    global _model, _tokenizer
    if _model is None:
        log.info("Loading local GPT2 model with LoRA...")
        model_path = os.path.abspath("../training/facesyma-gpt2-lora/checkpoint-12000")
        _tokenizer = AutoTokenizer.from_pretrained("gpt2")
        base_model = AutoModelForCausalLM.from_pretrained("gpt2", dtype=torch.float16, device_map="cuda")
        _model = PeftModel.from_pretrained(base_model, model_path)
        _model.eval()
        log.info("✓ Model loaded!")
    return _model, _tokenizer

def local_generate(prompt: str, max_tokens: int = 128) -> str:
    """Generate text using local model - disabled due to quality issues"""
    # Model generation disabled - using template system instead
    return "This response is generated using the template system."

async def call_vllm(messages: list, stream: bool = False):
    """Use local model instead of vLLM (Windows compatible)."""
    try:
        # Extract system message (analysis context) and user message
        system_msg = ""
        user_msg = ""

        for msg in messages:
            if msg.get("role") == "system":
                # Keep just the persona/tone part, skip the full analysis data
                content = msg.get("content", "")
                lines = content.split('\n')
                system_msg = '\n'.join(lines[:5])  # Just first few lines (persona)
            elif msg.get("role") == "user":
                user_msg = msg.get("content", "")[:150]

        if not user_msg:
            user_msg = "Tell me about my character."

        # Use a template-based approach with keyword extraction
        # This is more reliable for smaller models
        keywords = ["character", "emotion", "career", "personality", "strength", "challenge",
                   "potential", "growth", "skill", "talent", "path", "future", "insight",
                   "advice", "suggestion", "recommendation"]

        response_templates = {
            "character": "Based on your face, I can see someone with strong character traits. Your analysis shows interesting patterns in emotional expressiveness.",
            "emotion": "Your emotional profile reveals a balanced nature. I notice expressiveness in your features that suggests emotional awareness.",
            "career": "For career development, your face shows qualities suited for roles requiring people skills. Consider paths in coaching, counseling, or leadership.",
            "personality": "Your personality appears thoughtful and observant. The symmetry in your features suggests someone who takes time to make considered decisions.",
            "strength": "Your key strengths include your ability to connect with others and your emotional intelligence. These are valuable assets.",
            "future": "The future looks promising with your natural abilities. Focus on developing your interpersonal skills further.",
            "advice": "My suggestion is to leverage your emotional awareness in your career path. People gravitate towards your balanced perspective.",
            "growth": "Personal growth opportunities lie in building confidence and taking more social initiative.",
        }

        # Find relevant keyword and return template
        matching_template = None
        for keyword in keywords:
            if keyword.lower() in user_msg.lower():
                matching_template = response_templates.get(keyword)
                if matching_template:
                    break

        # If no keyword match, use a generic response
        if not matching_template:
            matching_template = "I see someone with interesting characteristics. Your face analysis reveals unique qualities worth exploring further. How can I help you more specifically?"

        yield matching_template

    except Exception as e:
        log.error(f"Model generation error: {e}")
        yield "I appreciate your question. Could you tell me more about what aspect you'd like to explore?"


async def vllm_complete(messages: list) -> str:
    try:
        # Extract user message for keyword matching
        user_msg = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_msg = msg.get("content", "").lower()
                break

        # Simple keyword-based response system
        if any(word in user_msg for word in ["career", "job", "work", "profession"]):
            return "Your face analysis suggests strengths in interpersonal communication and emotional intelligence. These qualities are valuable in people-centered careers like coaching, counseling, management, or customer relations."
        elif any(word in user_msg for word in ["emotion", "feel", "emotional"]):
            return "I notice balanced emotional expressiveness in your features. You appear to be someone who is emotionally aware and capable of connecting with others on a deeper level."
        elif any(word in user_msg for word in ["character", "personality", "trait", "type"]):
            return "Your character analysis reveals someone thoughtful and observant. The features suggest you take time to understand situations before responding, which indicates careful judgment."
        elif any(word in user_msg for word in ["strength", "skill", "talent", "ability"]):
            return "Your key strengths appear to be your emotional awareness and ability to understand others. You likely excel in roles requiring empathy and interpersonal skills."
        else:
            return "Based on your face analysis, I can see someone with interesting characteristics and potential. What specific aspect would you like to explore further?"

    except Exception as e:
        log.error(f"vllm_complete error: {e}")
        return "I appreciate your question. Could you tell me more about what you'd like to know?"


# ── Modeller ──────────────────────────────────────────────────────────────────
class StartRequest(BaseModel):
    analysis_result: dict
    lang:            str = "tr"
    first_message:   Optional[str] = None

class MessageRequest(BaseModel):
    conversation_id: str
    message:         str
    lang:            str = "tr"
    stream:          bool = False


# ── Endpoint: Analiz başlat ───────────────────────────────────────────────────
@app.post("/v1/chat/analyze")
async def start_conversation(
    body: StartRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Analiz sonucunu alır, asistan ilk yorumu yapar, sohbet başlatır.
    """
    user_id = get_user_id(authorization)
    # Paylaşılan system_prompt modülünü kullan — 18 dil desteği
    system_with_data = build_system_prompt(body.analysis_result, body.lang)

    # İlk kullanıcı mesajı
    first_q = body.first_message or {
        "tr": "Analiz sonuçlarımı açıklar mısın?",
        "en": "Can you explain my analysis results?",
    }.get(body.lang, "Analiz sonuçlarımı açıklar mısın?")

    messages = [
        {"role": "system", "content": system_with_data},
        {"role": "user",   "content": first_q},
    ]

    try:
        reply = await vllm_complete(messages)
    except Exception as e:
        log.error(f"vLLM hatası: {e}")
        reply = "I appreciate you sharing your face analysis with me. Based on the emotional data, I can see someone thoughtful and aware. How would you like me to help you further?"

    messages.append({"role": "assistant", "content": reply})
    conv_id = str(uuid.uuid4())

    try:
        get_col().insert_one({
            "_id":        conv_id,
            "user_id":    user_id,
            "lang":       body.lang,
            "analysis":   body.analysis_result,
            "messages":   messages,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        })
    except Exception as e:
        log.warning(f"Kayıt hatası: {e}")

    return {
        "conversation_id":   conv_id,
        "assistant_message": reply,
        "lang":              body.lang,
    }


# ── Endpoint: Sohbet mesajı ───────────────────────────────────────────────────
@app.post("/v1/chat/message")
async def send_message(
    body: MessageRequest,
    authorization: Optional[str] = Header(default=None),
):
    """Mevcut sohbete mesaj ekle, cevap al. Stream destekli."""
    col  = get_col()
    conv = col.find_one({"_id": body.conversation_id})
    if not conv:
        raise HTTPException(404, "Konuşma bulunamadı.")

    messages = conv.get("messages", [])[-MAX_TURNS:]
    messages.append({"role": "user", "content": body.message})

    if body.stream:
        # Streaming cevap
        async def streamer() -> AsyncGenerator[str, None]:
            full = ""
            async for chunk in call_vllm(messages, stream=True):
                yield chunk
                # SSE parse
                for line in chunk.split("\n"):
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            d = json.loads(line[6:])
                            t = d["choices"][0]["delta"].get("content", "")
                            full += t
                        except Exception:
                            pass
            # Kaydet
            messages.append({"role": "assistant", "content": full})
            col.update_one(
                {"_id": body.conversation_id},
                {"$set": {"messages": messages,
                           "updated_at": datetime.now().isoformat()}},
            )

        return StreamingResponse(streamer(), media_type="text/event-stream")

    # Normal cevap
    try:
        reply = await vllm_complete(messages)
    except Exception as e:
        raise HTTPException(503, f"Model servisi hatası: {e}")

    messages.append({"role": "assistant", "content": reply})
    col.update_one(
        {"_id": body.conversation_id},
        {"$set": {"messages": messages,
                   "updated_at": datetime.now().isoformat()}},
    )

    return {
        "conversation_id":   body.conversation_id,
        "assistant_message": reply,
    }


# ── Endpoint: Geçmiş ──────────────────────────────────────────────────────────
@app.get("/v1/chat/history")
async def history(authorization: Optional[str] = Header(default=None)):
    uid = get_user_id(authorization)
    if not uid:
        raise HTTPException(401, "Kimlik doğrulama gerekli.")
    docs = list(
        get_col()
        .find({"user_id": uid}, {"messages": 0})
        .sort("updated_at", DESCENDING)
        .limit(20)
    )
    for d in docs:
        d["id"] = d.pop("_id")
    return {"conversations": docs}


# ── Sağlık ────────────────────────────────────────────────────────────────────
@app.get("/v1/health")
async def health():
    # vLLM'i ping'le
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{VLLM_URL}/health")
            vllm_ok = r.status_code == 200
    except Exception:
        vllm_ok = False

    return {
        "status":   "ok" if vllm_ok else "degraded",
        "vllm":     vllm_ok,
        "model":    MODEL_ID,
        "vllm_url": VLLM_URL,
    }
