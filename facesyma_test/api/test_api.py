"""
facesyma_test/api/test_api.py
=============================
Facesyma Test Module — FastAPI service.

9 test types (Personality, Career, HR, Skills, Vocation, Relationship, EQ, Values, Stress)
Multi-language support (18 languages)
Likert 1-5 scale psychometric testing
AI interpretation via Ollama
Results storage in MongoDB

Endpoint routes:
  GET  /test/types              → Available test types
  POST /test/start              → Create session, get questions
  POST /test/submit             → Submit answers, get scored results
  GET  /test/results/{uid}      → User's test history
  GET  /test/pdf/{result_id}    → PDF download (GCS URL)
  GET  /test/languages          → Supported languages
  GET  /test/health             → Health check
"""

import os, json, uuid, logging, requests
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient, DESCENDING
import jwt

# Import PDF and GCS modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from pdf_generator import PDFReportGenerator
from gcs_storage import get_gcs_manager

# ── Configuration ──────────────────────────────────────────────────────────
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
MONGO_URI = os.environ.get("MONGO_URI", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable must be set.")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable must be set.")
MODEL = "orca-mini"
QUESTIONS_DIR = Path(__file__).parent.parent / "questions"

log = logging.getLogger(__name__)

# ── Load Question Banks ────────────────────────────────────────────────────
QUESTION_BANKS = {}
QUESTION_TYPES = ["personality", "career", "hr", "skills", "vocation", "relationship", "eq", "values", "stress"]
NONVERBAL_TYPES = {"emotion_recognition", "stroop"}
ALL_TEST_TYPES = set(QUESTION_TYPES) | NONVERBAL_TYPES

def load_questions():
    """Load all question bank JSON files"""
    for test_type in QUESTION_TYPES:
        file_path = QUESTIONS_DIR / f"{test_type}_questions.json"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                QUESTION_BANKS[test_type] = json.load(f)
            log.info(f"✓ Loaded {test_type} questions")
        except FileNotFoundError:
            log.error(f"✗ Question file not found: {file_path}")
            raise

load_questions()

# ── Database Helper ────────────────────────────────────────────────────────
_mongo_client = None

def get_db():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _mongo_client["facesyma-test-backup"]

# ── Ollama Integration ────────────────────────────────────────────────────
_LANG_NAMES = {
    "tr": "Turkish", "en": "English", "de": "German", "ru": "Russian",
    "ar": "Arabic",  "es": "Spanish", "ko": "Korean", "ja": "Japanese",
    "zh": "Chinese", "hi": "Hindi",   "fr": "French", "pt": "Portuguese",
    "bn": "Bengali", "id": "Indonesian", "ur": "Urdu", "it": "Italian",
    "vi": "Vietnamese", "pl": "Polish",
}

_FALLBACK_INTERPRETATIONS = {
    "tr": "Test sonuçlarınız analiz edildi. Güçlü alanlarınızı geliştirmeye devam edin.",
    "en": "Your test results have been analyzed. Continue developing your strengths.",
    "de": "Ihre Testergebnisse wurden analysiert. Entwickeln Sie Ihre Stärken weiter.",
    "ru": "Ваши результаты теста проанализированы. Продолжайте развивать свои сильные стороны.",
    "ar": "تم تحليل نتائج اختبارك. استمر في تطوير نقاط قوتك.",
    "es": "Los resultados de su prueba han sido analizados. Siga desarrollando sus fortalezas.",
    "ko": "테스트 결과가 분석되었습니다. 강점을 계속 개발하십시오.",
    "ja": "テスト結果が分析されました。強みを引き続き伸ばしてください。",
    "zh": "您的测试结果已分析完毕。继续发展您的优势。",
    "hi": "आपके परीक्षण परिणामों का विश्लेषण किया गया है। अपनी शक्तियों को विकसित करते रहें।",
    "fr": "Vos résultats de test ont été analysés. Continuez à développer vos points forts.",
    "pt": "Seus resultados de teste foram analisados. Continue desenvolvendo seus pontos fortes.",
    "bn": "আপনার পরীক্ষার ফলাফল বিশ্লেষণ করা হয়েছে। আপনার শক্তি বিকাশ চালিয়ে যান।",
    "id": "Hasil tes Anda telah dianalisis. Terus kembangkan kekuatan Anda.",
    "ur": "آپ کے ٹیسٹ کے نتائج کا تجزیہ کیا گیا ہے۔ اپنی طاقتوں کو ترقی دیتے رہیں۔",
    "it": "I risultati del tuo test sono stati analizzati. Continua a sviluppare i tuoi punti di forza.",
    "vi": "Kết quả kiểm tra của bạn đã được phân tích. Tiếp tục phát triển điểm mạnh của bạn.",
    "pl": "Wyniki Twojego testu zostały przeanalizowane. Kontynuuj rozwijanie swoich mocnych stron.",
}

def get_ai_interpretation(test_type: str, scores: Dict, lang: str) -> str:
    """Get AI interpretation of test results in the user's language."""
    lang_name = _LANG_NAMES.get(lang, "English")
    fallback = _FALLBACK_INTERPRETATIONS.get(lang, _FALLBACK_INTERPRETATIONS["en"])
    try:
        score_text = "\n".join([f"  {domain}: {int(score)}/100" for domain, score in scores.items()])
        prompt = (
            f"You are a psychologist. Analyze the following {test_type} test results and "
            f"provide a brief, helpful interpretation in 2-3 sentences. "
            f"IMPORTANT: Respond ONLY in {lang_name}. Do not use any other language.\n\n"
            f"Test scores:\n{score_text}\n\n"
            f"Write your interpretation in {lang_name}:"
        )
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False, "temperature": 0.7},
            timeout=120,
        )
        response.raise_for_status()
        result = response.json().get("response", "").strip()
        return result if result else fallback
    except Exception as e:
        log.error(f"Ollama error: {e}")
        return fallback

# ── FastAPI App ───────────────────────────────────────────────────────────
app = FastAPI(title="Facesyma Test Module", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Models ────────────────────────────────────────────────
class StartTestRequest(BaseModel):
    test_type: str  # personality, career, hr, skills, vocation, relationship
    lang: str = "tr"

class StartTestResponse(BaseModel):
    session_id: str
    test_type: str
    lang: str
    questions: List[Dict]
    requires_health_consent: Optional[bool] = None
    is_clinical: Optional[bool] = None
    disclaimer: Optional[str] = None

class AnswerItem(BaseModel):
    q_id: str
    score: int  # 1-5 Likert; 0 placeholder for nonverbal (backend recomputes from selected_option)
    selected_option: Optional[str] = None   # nonverbal: user's chosen key
    response_time_ms: Optional[int] = None  # stroop: reaction time in ms

class SubmitTestRequest(BaseModel):
    session_id: str
    test_type: str
    lang: str
    answers: List[AnswerItem]

class SubmitTestResponse(BaseModel):
    result_id: str
    test_type: str
    domain_scores: Dict[str, float]
    ai_interpretation: str
    pdf_url: Optional[str] = None
    stress_details: Optional[Dict] = None
    nonverbal_details: Optional[Dict] = None

class TestTypeInfo(BaseModel):
    test_type: str
    name: str
    description: str
    domains: List[str]
    questions_count: int
    requires_health_consent: Optional[bool] = None
    is_clinical: Optional[bool] = None

# ── JWT Helper ────────────────────────────────────────────────────────────
def get_user_id(authorization: Optional[str]) -> Optional[int]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ", 1)[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except Exception:
        return None

# ── Scoring System ────────────────────────────────────────────────────────
def calculate_domain_scores(test_type: str, answers: List[AnswerItem]) -> Dict[str, float]:
    """Calculate domain scores from answers"""
    qbank = QUESTION_BANKS[test_type]
    questions = {q["q_id"]: q for q in qbank["questions"]}

    # Initialize domain scores
    domains = {}
    domain_counts = {}
    for q in qbank["questions"]:
        _qget = q.get
        domain = _qget("domain") or _qget("subscale")
        if domain not in domains:
            domains[domain] = 0
            domain_counts[domain] = 0

    # Calculate scores
    for answer in answers:
        _aqid = answer.q_id
        if _aqid not in questions:
            continue

        q = questions[_aqid]
        _qget = q.get
        domain = _qget("domain") or _qget("subscale")

        # Handle reverse-scored items
        score = answer.score
        if _qget("reverse_scored"):
            score = 6 - score

        domains[domain] += score
        domain_counts[domain] += 1

    # Convert to 0-100 scale
    domain_scores = {}
    for domain in domains:
        _dcd = domain_counts[domain]
        if _dcd > 0:
            avg = domains[domain] / _dcd  # 1-5 scale
            percentage = ((avg - 1) / 4) * 100  # Convert to 0-100
            domain_scores[domain] = max(0, min(100, percentage))

    return domain_scores

# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/test/types", response_model=List[TestTypeInfo])
async def get_test_types():
    """List all available test types"""
    types_info = {
        "personality": {
            "name": "Big Five Personality Test",
            "description": "Assess your personality traits across 5 dimensions",
            "domains": ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"],
        },
        "career": {
            "name": "Career Aptitude Test",
            "description": "Discover your career inclinations and strengths",
            "domains": ["analytical", "creative", "social", "entrepreneurial", "managerial", "technical"],
        },
        "hr": {
            "name": "HR / Work Style Test",
            "description": "Understand your workplace preferences and interpersonal style",
            "domains": ["leadership", "team_fit", "communication", "stress_tolerance", "motivation"],
        },
        "skills": {
            "name": "Skills Assessment Test",
            "description": "Evaluate your core competencies and abilities",
            "domains": ["problem_solving", "empathy", "organization", "learning_speed", "decision_making"],
        },
        "vocation": {
            "name": "Holland RIASEC Vocational Test",
            "description": "Find your ideal career path based on vocational interests",
            "domains": ["realistic", "investigative", "artistic", "social", "enterprising", "conventional"],
        },
        "relationship": {
            "name": "Relationship & Emotional Intelligence Test",
            "description": "Assess attachment styles, love languages, and emotional awareness",
            "domains": ["attachment_style", "love_language", "relationship_values", "emotional_intelligence"],
        },
        "eq": {
            "name": "Emotional Intelligence (EQ) Test",
            "description": "Assess your emotional intelligence across 5 core dimensions",
            "domains": ["self_awareness", "self_regulation", "motivation", "empathy", "social_skills"],
        },
        "values": {
            "name": "Schwartz Values Assessment",
            "description": "Discover your core personal values based on Schwartz Values Theory",
            "domains": ["universalism", "self_direction", "achievement", "security", "hedonism"],
        },
        "stress": {
            "name": "Stress & Wellbeing Assessment (PHQ-9 + GAD-7)",
            "description": "Assess depression and anxiety symptoms using validated clinical scales",
            "domains": ["depression", "anxiety"],
            "requires_health_consent": True,
            "is_clinical": True,
        },
        "emotion_recognition": {
            "name": "Emotional Face Recognition",
            "description": "Identify emotions from facial expressions — 21 questions",
            "domains": ["overall", "happy", "sad", "angry", "fearful", "disgusted", "surprised", "neutral", "contempt"],
            "questions_count": len(_EMOTION_STIMULI),
        },
        "stroop": {
            "name": "Stroop Attention Test",
            "description": "Cognitive flexibility and selective attention — 20 trials",
            "domains": ["accuracy", "cognitive_flexibility"],
            "questions_count": len(_STROOP_SEQUENCE),
        },
    }

    result = []
    for test_type, info in types_info.items():
        result.append(TestTypeInfo(
            test_type=test_type,
            name=info["name"],
            description=info["description"],
            domains=info["domains"],
            questions_count=info.get("questions_count") or (len(QUESTION_BANKS[test_type]["questions"]) if test_type in QUESTION_BANKS else 20),
            requires_health_consent=info.get("requires_health_consent"),
            is_clinical=info.get("is_clinical"),
        ))
    return result

@app.post("/test/start", response_model=StartTestResponse)
async def start_test(
    body: StartTestRequest,
    authorization: Optional[str] = Header(default=None)
):
    """Create a new test session and return 20 questions"""
    _ttype = body.test_type
    if _ttype not in ALL_TEST_TYPES:
        raise HTTPException(400, f"Unknown test type: {_ttype}")

    user_id = get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Authentication required.")
    session_id = str(uuid.uuid4())
    _lang = body.lang

    # Nonverbal: generate questions inline
    if _ttype == "emotion_recognition":
        response_questions = _generate_emotion_questions(_lang)
        db = get_db()
        db["test_sessions"].insert_one({
            "_id": session_id, "user_id": user_id, "test_type": _ttype,
            "lang": _lang, "status": "in_progress", "created_at": datetime.now().isoformat(),
        })
        return StartTestResponse(session_id=session_id, test_type=_ttype, lang=_lang, questions=response_questions)

    if _ttype == "stroop":
        response_questions = _generate_stroop_questions(_lang)
        db = get_db()
        db["test_sessions"].insert_one({
            "_id": session_id, "user_id": user_id, "test_type": _ttype,
            "lang": _lang, "status": "in_progress", "created_at": datetime.now().isoformat(),
        })
        return StartTestResponse(session_id=session_id, test_type=_ttype, lang=_lang, questions=response_questions)

    # Likert-based question loading
    qbank = QUESTION_BANKS[_ttype]
    questions = qbank["questions"]
    scale_labels = qbank["scale_labels"].get(_lang, qbank["scale_labels"]["en"])

    response_questions = []
    for q in questions:
        _qt = q["translations"]
        response_questions.append({
            "q_id": q["q_id"],
            "order": q["order"],
            "text": _qt.get(_lang, _qt["en"]),
            "scale": {"min": 1, "max": 5, "labels": scale_labels}
        })

    db = get_db()
    db["test_sessions"].insert_one({
        "_id": session_id, "user_id": user_id, "test_type": _ttype,
        "lang": _lang, "status": "in_progress", "created_at": datetime.now().isoformat(),
    })

    response_kwargs: Dict = {
        "session_id": session_id, "test_type": _ttype, "lang": _lang, "questions": response_questions,
    }
    if _ttype == "stress":
        response_kwargs["requires_health_consent"] = True
        response_kwargs["is_clinical"] = True
        response_kwargs["disclaimer"] = (
            "This assessment uses validated PHQ-9 and GAD-7 clinical scales. "
            "Results are for informational purposes only and do not constitute a medical diagnosis. "
            "If you are experiencing distress, please contact a healthcare professional."
        )
    return StartTestResponse(**response_kwargs)

def _stress_severity(domain_scores: Dict[str, float], answers: List[AnswerItem]) -> Dict:
    """Interpret PHQ-9/GAD-7 severity bands and check crisis flag."""
    dep = domain_scores.get("depression", 0)
    anx = domain_scores.get("anxiety", 0)

    if dep < 20:
        dep_sev = "minimal"
    elif dep < 40:
        dep_sev = "mild"
    elif dep < 60:
        dep_sev = "moderate"
    elif dep < 80:
        dep_sev = "moderately_severe"
    else:
        dep_sev = "severe"

    if anx < 20:
        anx_sev = "minimal"
    elif anx < 40:
        anx_sev = "mild"
    elif anx < 60:
        anx_sev = "moderate"
    else:
        anx_sev = "severe"

    crisis = any(a.q_id == "S009" and a.score >= 4 for a in answers)

    result: Dict = {
        "depression_severity": dep_sev,
        "anxiety_severity": anx_sev,
        "crisis_flag": crisis,
    }
    if crisis:
        result["crisis_resource"] = (
            "If you are having thoughts of self-harm, please reach out immediately. "
            "Turkey Crisis Line: 182 | International resources: https://www.iasp.info/resources/Crisis_Centres/"
        )
    return result


# ── Nonverbal Test Data ────────────────────────────────────────────────────

# 21 emotion stimuli: (q_id, emoji, correct_emotion_key, [4 option keys])
_EMOTION_STIMULI = [
    ("ER001", "😊", "happy",     ["happy", "sad", "neutral", "surprised"]),
    ("ER002", "😄", "happy",     ["happy", "surprised", "neutral", "contempt"]),
    ("ER003", "😁", "happy",     ["happy", "angry", "surprised", "neutral"]),
    ("ER004", "😢", "sad",       ["sad", "neutral", "fearful", "disgusted"]),
    ("ER005", "😔", "sad",       ["sad", "neutral", "contempt", "fearful"]),
    ("ER006", "🙁", "sad",       ["sad", "angry", "neutral", "disgusted"]),
    ("ER007", "😠", "angry",     ["angry", "disgusted", "sad", "contempt"]),
    ("ER008", "😡", "angry",     ["angry", "disgusted", "fearful", "neutral"]),
    ("ER009", "😤", "angry",     ["angry", "contempt", "disgusted", "neutral"]),
    ("ER010", "😨", "fearful",   ["fearful", "surprised", "sad", "neutral"]),
    ("ER011", "😱", "fearful",   ["fearful", "surprised", "angry", "neutral"]),
    ("ER012", "😰", "fearful",   ["fearful", "sad", "surprised", "neutral"]),
    ("ER013", "🤢", "disgusted", ["disgusted", "angry", "sad", "neutral"]),
    ("ER014", "😒", "disgusted", ["disgusted", "neutral", "contempt", "sad"]),
    ("ER015", "😣", "disgusted", ["disgusted", "sad", "fearful", "neutral"]),
    ("ER016", "😮", "surprised", ["surprised", "fearful", "happy", "neutral"]),
    ("ER017", "😲", "surprised", ["surprised", "fearful", "angry", "neutral"]),
    ("ER018", "🤯", "surprised", ["surprised", "fearful", "happy", "angry"]),
    ("ER019", "😐", "neutral",   ["neutral", "sad", "happy", "contempt"]),
    ("ER020", "😑", "neutral",   ["neutral", "contempt", "disgusted", "sad"]),
    ("ER021", "😏", "contempt",  ["contempt", "neutral", "happy", "angry"]),
]
_EMOTION_CORRECT_MAP = {s[0]: s[2] for s in _EMOTION_STIMULI}

_EMOTION_LABELS: Dict[str, Dict[str, str]] = {
    "tr": {"happy": "Mutlu", "sad": "Üzgün", "angry": "Kızgın", "fearful": "Korkmuş",
           "disgusted": "İğrenmiş", "surprised": "Şaşırmış", "neutral": "Nötr", "contempt": "Küçümseme"},
    "en": {"happy": "Happy", "sad": "Sad", "angry": "Angry", "fearful": "Fearful",
           "disgusted": "Disgusted", "surprised": "Surprised", "neutral": "Neutral", "contempt": "Contempt"},
    "de": {"happy": "Glücklich", "sad": "Traurig", "angry": "Wütend", "fearful": "Ängstlich",
           "disgusted": "Angewidert", "surprised": "Überrascht", "neutral": "Neutral", "contempt": "Verachtung"},
    "ru": {"happy": "Счастливый", "sad": "Грустный", "angry": "Злой", "fearful": "Испуганный",
           "disgusted": "Отвращение", "surprised": "Удивлённый", "neutral": "Нейтральный", "contempt": "Презрение"},
    "ar": {"happy": "سعيد", "sad": "حزين", "angry": "غاضب", "fearful": "خائف",
           "disgusted": "مشمئز", "surprised": "مندهش", "neutral": "محايد", "contempt": "ازدراء"},
    "es": {"happy": "Feliz", "sad": "Triste", "angry": "Enojado", "fearful": "Asustado",
           "disgusted": "Disgustado", "surprised": "Sorprendido", "neutral": "Neutral", "contempt": "Desprecio"},
    "ko": {"happy": "행복", "sad": "슬픔", "angry": "화남", "fearful": "두려움",
           "disgusted": "혐오", "surprised": "놀람", "neutral": "중립", "contempt": "경멸"},
    "ja": {"happy": "幸せ", "sad": "悲しい", "angry": "怒り", "fearful": "恐怖",
           "disgusted": "嫌悪", "surprised": "驚き", "neutral": "中立", "contempt": "軽蔑"},
    "zh": {"happy": "快乐", "sad": "悲伤", "angry": "愤怒", "fearful": "恐惧",
           "disgusted": "厌恶", "surprised": "惊讶", "neutral": "中性", "contempt": "轻蔑"},
    "hi": {"happy": "खुश", "sad": "उदास", "angry": "गुस्सा", "fearful": "डरा हुआ",
           "disgusted": "घृणा", "surprised": "चौंका", "neutral": "तटस्थ", "contempt": "तिरस्कार"},
    "fr": {"happy": "Heureux", "sad": "Triste", "angry": "En colère", "fearful": "Effrayé",
           "disgusted": "Dégoûté", "surprised": "Surpris", "neutral": "Neutre", "contempt": "Mépris"},
    "pt": {"happy": "Feliz", "sad": "Triste", "angry": "Com raiva", "fearful": "Com medo",
           "disgusted": "Nojento", "surprised": "Surpreso", "neutral": "Neutro", "contempt": "Desprezo"},
    "bn": {"happy": "সুখী", "sad": "দুঃখিত", "angry": "রাগান্বিত", "fearful": "ভীত",
           "disgusted": "বিরক্ত", "surprised": "অবাক", "neutral": "নিরপেক্ষ", "contempt": "ঘৃণা"},
    "id": {"happy": "Senang", "sad": "Sedih", "angry": "Marah", "fearful": "Takut",
           "disgusted": "Jijik", "surprised": "Terkejut", "neutral": "Netral", "contempt": "Penghinaan"},
    "ur": {"happy": "خوش", "sad": "اداس", "angry": "غصہ", "fearful": "خوفزدہ",
           "disgusted": "متنفر", "surprised": "حیران", "neutral": "غیر جانبدار", "contempt": "حقارت"},
    "it": {"happy": "Felice", "sad": "Triste", "angry": "Arrabbiato", "fearful": "Spaventato",
           "disgusted": "Disgustato", "surprised": "Sorpreso", "neutral": "Neutro", "contempt": "Disprezzo"},
    "vi": {"happy": "Vui", "sad": "Buồn", "angry": "Tức giận", "fearful": "Sợ hãi",
           "disgusted": "Ghê tởm", "surprised": "Ngạc nhiên", "neutral": "Trung lập", "contempt": "Khinh thường"},
    "pl": {"happy": "Szczęśliwy", "sad": "Smutny", "angry": "Zły", "fearful": "Przestraszony",
           "disgusted": "Zniesmaczony", "surprised": "Zaskoczony", "neutral": "Neutralny", "contempt": "Pogarda"},
}

# 20 Stroop trials: (q_id, word_color, ink_color, is_congruent)
_STROOP_SEQUENCE = [
    ("ST001", "red",    "red",    True),
    ("ST002", "blue",   "green",  False),
    ("ST003", "green",  "green",  True),
    ("ST004", "yellow", "red",    False),
    ("ST005", "blue",   "blue",   True),
    ("ST006", "red",    "yellow", False),
    ("ST007", "yellow", "yellow", True),
    ("ST008", "green",  "blue",   False),
    ("ST009", "red",    "green",  False),
    ("ST010", "blue",   "red",    False),
    ("ST011", "yellow", "blue",   False),
    ("ST012", "green",  "yellow", False),
    ("ST013", "red",    "red",    True),
    ("ST014", "blue",   "yellow", False),
    ("ST015", "green",  "green",  True),
    ("ST016", "yellow", "yellow", True),
    ("ST017", "red",    "blue",   False),
    ("ST018", "blue",   "blue",   True),
    ("ST019", "green",  "red",    False),
    ("ST020", "yellow", "green",  False),
]
_STROOP_CORRECT = {q[0]: q[2] for q in _STROOP_SEQUENCE}
_STROOP_CONGRUENT = {q[0]: q[3] for q in _STROOP_SEQUENCE}

_COLOR_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "tr": {"red": "KIRMIZI", "blue": "MAVİ",     "green": "YEŞİL",    "yellow": "SARI"},
    "en": {"red": "RED",     "blue": "BLUE",      "green": "GREEN",    "yellow": "YELLOW"},
    "de": {"red": "ROT",     "blue": "BLAU",      "green": "GRÜN",     "yellow": "GELB"},
    "ru": {"red": "КРАСНЫЙ", "blue": "СИНИЙ",     "green": "ЗЕЛЁНЫЙ",  "yellow": "ЖЁЛТЫЙ"},
    "ar": {"red": "أحمر",    "blue": "أزرق",      "green": "أخضر",     "yellow": "أصفر"},
    "es": {"red": "ROJO",    "blue": "AZUL",      "green": "VERDE",    "yellow": "AMARILLO"},
    "ko": {"red": "빨강",     "blue": "파랑",       "green": "초록",      "yellow": "노랑"},
    "ja": {"red": "赤",      "blue": "青",        "green": "緑",       "yellow": "黄"},
    "zh": {"red": "红色",     "blue": "蓝色",       "green": "绿色",      "yellow": "黄色"},
    "hi": {"red": "लाल",     "blue": "नीला",      "green": "हरा",      "yellow": "पीला"},
    "fr": {"red": "ROUGE",   "blue": "BLEU",      "green": "VERT",     "yellow": "JAUNE"},
    "pt": {"red": "VERMELHO","blue": "AZUL",      "green": "VERDE",    "yellow": "AMARELO"},
    "bn": {"red": "লাল",     "blue": "নীল",       "green": "সবুজ",     "yellow": "হলুদ"},
    "id": {"red": "MERAH",   "blue": "BIRU",      "green": "HIJAU",    "yellow": "KUNING"},
    "ur": {"red": "سرخ",     "blue": "نیلا",      "green": "سبز",      "yellow": "پیلا"},
    "it": {"red": "ROSSO",   "blue": "BLU",       "green": "VERDE",    "yellow": "GIALLO"},
    "vi": {"red": "ĐỎ",      "blue": "XANH DƯƠNG","green": "XANH LÁ", "yellow": "VÀNG"},
    "pl": {"red": "CZERWONY","blue": "NIEBIESKI",  "green": "ZIELONY",  "yellow": "ŻÓŁTY"},
}
_CSS_COLORS = {"red": "#e53935", "blue": "#1e88e5", "green": "#43a047", "yellow": "#f9a825"}


def _generate_emotion_questions(lang: str) -> List[Dict]:
    labels = _EMOTION_LABELS.get(lang, _EMOTION_LABELS["en"])
    result = []
    for i, (q_id, emoji, _correct, options) in enumerate(_EMOTION_STIMULI):
        result.append({
            "q_id": q_id,
            "order": i + 1,
            "display_type": "emotion_recognition",
            "emoji": emoji,
            "options": [{"key": opt, "label": labels.get(opt, opt)} for opt in options],
            "text": "",
        })
    return result


def _generate_stroop_questions(lang: str) -> List[Dict]:
    cw = _COLOR_TRANSLATIONS.get(lang, _COLOR_TRANSLATIONS["en"])
    result = []
    for i, (q_id, word_color, ink_color, _cong) in enumerate(_STROOP_SEQUENCE):
        result.append({
            "q_id": q_id,
            "order": i + 1,
            "display_type": "stroop",
            "word": cw[word_color],
            "ink_color": ink_color,
            "ink_hex": _CSS_COLORS[ink_color],
            "color_options": [
                {"key": c, "label": cw[c], "hex": _CSS_COLORS[c]}
                for c in ["red", "blue", "green", "yellow"]
            ],
            "text": "",
        })
    return result


def _emotion_score(answers: List[AnswerItem]) -> Dict[str, float]:
    from collections import defaultdict
    correct_by: defaultdict = defaultdict(int)
    total_by: defaultdict = defaultdict(int)
    for a in answers:
        emotion = _EMOTION_CORRECT_MAP.get(a.q_id)
        if not emotion:
            continue
        total_by[emotion] += 1
        if (a.selected_option or "") == emotion:
            correct_by[emotion] += 1
    total_c = sum(correct_by.values())
    total_t = sum(total_by.values())
    scores: Dict[str, float] = {"overall": round((total_c / total_t * 100) if total_t else 0, 1)}
    for em in total_by:
        t = total_by[em]
        scores[em] = round((correct_by[em] / t * 100) if t else 0, 1)
    return scores


def _stroop_score(answers: List[AnswerItem]):
    total = len(answers)
    if total == 0:
        return {"accuracy": 0.0, "cognitive_flexibility": 0.0}, {}
    correct = sum(
        1 for a in answers
        if (a.selected_option or "") == _STROOP_CORRECT.get(a.q_id, "")
    )
    accuracy = round(correct / total * 100, 1)
    times = [a.response_time_ms for a in answers if a.response_time_ms and a.response_time_ms > 0]
    avg_rt = int(sum(times) / len(times)) if times else 0
    cong = [a for a in answers if _STROOP_CONGRUENT.get(a.q_id, False)]
    incong = [a for a in answers if not _STROOP_CONGRUENT.get(a.q_id, True)]
    cong_acc = round(
        sum(1 for a in cong if (a.selected_option or "") == _STROOP_CORRECT.get(a.q_id, "")) / len(cong) * 100, 1
    ) if cong else 0.0
    incong_acc = round(
        sum(1 for a in incong if (a.selected_option or "") == _STROOP_CORRECT.get(a.q_id, "")) / len(incong) * 100, 1
    ) if incong else 0.0
    interference = round(cong_acc - incong_acc, 1)
    rt_penalty = max(0.0, min(20.0, max(0, avg_rt - 800) / 1000 * 10))
    cog_flex = round(max(0.0, accuracy - rt_penalty), 1)
    domain_scores = {"accuracy": accuracy, "cognitive_flexibility": cog_flex}
    details = {
        "congruent_accuracy": cong_acc,
        "incongruent_accuracy": incong_acc,
        "interference_effect": interference,
        "avg_reaction_ms": avg_rt,
    }
    return domain_scores, details


@app.post("/test/submit", response_model=SubmitTestResponse)
async def submit_test(
    body: SubmitTestRequest,
    authorization: Optional[str] = Header(default=None)
):
    """Submit test answers and get scored results"""
    _ttype = body.test_type
    _lang = body.lang
    user_id = get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Authentication required.")

    # Calculate domain scores
    nonverbal_details = None
    if _ttype == "emotion_recognition":
        domain_scores = _emotion_score(body.answers)
    elif _ttype == "stroop":
        domain_scores, nonverbal_details = _stroop_score(body.answers)
    else:
        domain_scores = calculate_domain_scores(_ttype, body.answers)

    # Stress-specific severity interpretation
    stress_details = _stress_severity(domain_scores, body.answers) if _ttype == "stress" else None

    # Get AI interpretation
    ai_interpretation = get_ai_interpretation(
        _ttype,
        domain_scores,
        _lang
    )

    # Create result ID
    result_id = str(uuid.uuid4())

    # Generate PDF and upload to GCS
    pdf_url = None
    try:
        generator = PDFReportGenerator(test_type=_ttype, lang=_lang)
        pdf_buffer = generator.generate_pdf(
            result_id=result_id,
            domain_scores=domain_scores,
            ai_interpretation=ai_interpretation,
            user_id=user_id
        )

        # Upload to GCS
        gcs_manager = get_gcs_manager()
        pdf_url = gcs_manager.upload_pdf(
            result_id=result_id,
            pdf_buffer=pdf_buffer
        )
        log.info(f"PDF generated and uploaded for result {result_id}")
    except Exception as e:
        log.error(f"PDF generation/upload failed: {e}")
        # Continue without PDF if generation fails

    # Save result
    db = get_db()
    result_doc = {
        "_id": result_id,
        "user_id": user_id,
        "session_id": body.session_id,
        "test_type": _ttype,
        "lang": _lang,
        "answers": [{"q_id": a.q_id, "score": a.score} for a in body.answers],
        "domain_scores": domain_scores,
        "ai_interpretation": ai_interpretation,
        "pdf_url": pdf_url,
        "created_at": datetime.now().isoformat(),
    }
    if stress_details:
        result_doc["stress_details"] = stress_details
    if nonverbal_details:
        result_doc["nonverbal_details"] = nonverbal_details
    db["test_results"].insert_one(result_doc)

    # Mark session as completed
    db["test_sessions"].update_one(
        {"_id": body.session_id},
        {"$set": {"status": "completed", "result_id": result_id}}
    )

    return SubmitTestResponse(
        result_id=result_id,
        test_type=_ttype,
        domain_scores=domain_scores,
        ai_interpretation=ai_interpretation,
        pdf_url=pdf_url,
        stress_details=stress_details,
        nonverbal_details=nonverbal_details,
    )

@app.get("/test/results/{uid}")
async def get_user_results(
    uid: int,
    authorization: Optional[str] = Header(default=None)
):
    """Get user's test history"""
    user_id = get_user_id(authorization)
    if not user_id or user_id != uid:
        raise HTTPException(401, "Unauthorized")

    db = get_db()
    results = list(
        db["test_results"]
        .find({"user_id": user_id}, {"answers": 0})
        .sort("created_at", DESCENDING)
        .limit(50)
    )

    for r in results:
        r["id"] = r.pop("_id")

    return {"results": results}

@app.get("/test/pdf/{result_id}")
async def get_pdf(result_id: str, authorization: Optional[str] = Header(default=None)):
    """Get PDF download URL (GCS signed URL)"""
    user_id = get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Unauthorized")

    db = get_db()
    result = db["test_results"].find_one({"_id": result_id})
    if not result:
        raise HTTPException(404, "Result not found")

    _rget = result.get
    if _rget("user_id") != user_id:
        raise HTTPException(403, "Access denied")

    pdf_url = _rget("pdf_url")
    status = "ready" if pdf_url else "unavailable"

    return {
        "result_id": result_id,
        "pdf_url": pdf_url,
        "status": status,
        "test_type": _rget("test_type"),
        "created_at": _rget("created_at")
    }

@app.get("/test/languages")
async def get_languages():
    """Get supported languages"""
    return {
        "languages": [
            {"code": "tr", "name": "Turkish"},
            {"code": "en", "name": "English"},
            {"code": "de", "name": "German"},
            {"code": "ru", "name": "Russian"},
            {"code": "ar", "name": "Arabic"},
            {"code": "es", "name": "Spanish"},
            {"code": "ko", "name": "Korean"},
            {"code": "ja", "name": "Japanese"},
            {"code": "zh", "name": "Chinese"},
            {"code": "hi", "name": "Hindi"},
            {"code": "fr", "name": "French"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "bn", "name": "Bengali"},
            {"code": "id", "name": "Indonesian"},
            {"code": "ur", "name": "Urdu"},
            {"code": "it", "name": "Italian"},
            {"code": "vi", "name": "Vietnamese"},
            {"code": "pl", "name": "Polish"},
        ]
    }

@app.get("/test/health")
async def health():
    return {"status": "ok", "model": MODEL, "tests": QUESTION_TYPES, "nonverbal": list(NONVERBAL_TYPES)}

# ── Startup ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
