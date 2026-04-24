"""
facesyma_test/api/test_api.py
=============================
Facesyma Test Module — FastAPI service.

6 test types (Personality, Career, HR, Skills, Vocation, Relationship)
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
QUESTION_TYPES = ["personality", "career", "hr", "skills", "vocation", "relationship"]

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
def get_ai_interpretation(test_type: str, scores: Dict, lang: str) -> str:
    """Get AI interpretation of test results"""
    try:
        score_text = "\n".join([f"{domain}: {int(score)}/100" for domain, score in scores.items()])

        prompt = f"""
تحليل نتائج الاختبار {test_type}
===================================
النطاقات والدرجات:
{score_text}

يرجى تقديم تفسير مختصر (2-3 جمل) لهذه النتائج بلغة طبيعية.
"""

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        log.error(f"Ollama error: {e}")
        return f"Results interpretation could not be generated."

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
    questions: List[Dict]  # 20 questions with translations

class AnswerItem(BaseModel):
    q_id: str
    score: int  # 1-5

class SubmitTestRequest(BaseModel):
    session_id: str
    test_type: str
    lang: str
    answers: List[AnswerItem]

class SubmitTestResponse(BaseModel):
    result_id: str
    test_type: str
    domain_scores: Dict[str, float]  # domain -> 0-100
    ai_interpretation: str
    pdf_url: Optional[str] = None

class TestTypeInfo(BaseModel):
    test_type: str
    name: str
    description: str
    domains: List[str]
    questions_count: int

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
    }

    result = []
    for test_type, info in types_info.items():
        result.append(TestTypeInfo(
            test_type=test_type,
            name=info["name"],
            description=info["description"],
            domains=info["domains"],
            questions_count=20
        ))
    return result

@app.post("/test/start", response_model=StartTestResponse)
async def start_test(
    body: StartTestRequest,
    authorization: Optional[str] = Header(default=None)
):
    """Create a new test session and return 20 questions"""
    _ttype = body.test_type
    if _ttype not in QUESTION_BANKS:
        raise HTTPException(400, f"Unknown test type: {_ttype}")

    user_id = get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Authentication required.")
    session_id = str(uuid.uuid4())

    _lang = body.lang
    qbank = QUESTION_BANKS[_ttype]
    questions = qbank["questions"]
    scale_labels = qbank["scale_labels"].get(_lang, qbank["scale_labels"]["en"])

    # Build response questions with translations
    response_questions = []
    for q in questions:
        _qt = q["translations"]
        response_questions.append({
            "q_id": q["q_id"],
            "order": q["order"],
            "text": _qt.get(_lang, _qt["en"]),
            "scale": {
                "min": 1,
                "max": 5,
                "labels": scale_labels
            }
        })

    # Save session to DB
    db = get_db()
    db["test_sessions"].insert_one({
        "_id": session_id,
        "user_id": user_id,
        "test_type": _ttype,
        "lang": _lang,
        "status": "in_progress",
        "created_at": datetime.now().isoformat(),
    })

    return StartTestResponse(
        session_id=session_id,
        test_type=_ttype,
        lang=_lang,
        questions=response_questions
    )

@app.post("/test/submit", response_model=SubmitTestResponse)
async def submit_test(
    body: SubmitTestRequest,
    authorization: Optional[str] = Header(default=None)
):
    """Submit test answers and get scored results"""
    _ttype = body.test_type
    user_id = get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Authentication required.")

    # Calculate domain scores
    domain_scores = calculate_domain_scores(_ttype, body.answers)

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
    db["test_results"].insert_one({
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
    })

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
        pdf_url=pdf_url
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
    return {"status": "ok", "model": MODEL, "tests": QUESTION_TYPES}

# ── Startup ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
