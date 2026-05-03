"""Discovery game service — MongoDB-backed game sessions."""
import random
import string
from datetime import datetime
from gamification.models.discovery_game import DISCOVERY_GAME_TYPES


class DiscoveryGameError(Exception):
    pass


class SessionNotFoundError(DiscoveryGameError):
    pass


class GameTypeNotFoundError(DiscoveryGameError):
    pass


_SAMPLE_QUESTIONS = {
    "trait_discovery": [
        {
            "question_id": "td_001",
            "text_en": "Which trait best describes a prominent jaw?",
            "text_tr": "Belirgin bir çene hangi sıfatı en iyi tanımlar?",
            "choices_en": ["Dominant", "Gentle", "Creative", "Introverted"],
            "choices_tr": ["Baskın", "Nazik", "Yaratıcı", "İçe dönük"],
            "correct_index": 0,
            "time_limit_seconds": 15,
        },
        {
            "question_id": "td_002",
            "text_en": "Wide eyes are often associated with which trait?",
            "text_tr": "Geniş gözler hangi sıfatla ilişkilendirilir?",
            "choices_en": ["Analytical", "Empathetic", "Dominant", "Reserved"],
            "choices_tr": ["Analitik", "Empatik", "Baskın", "Çekingen"],
            "correct_index": 1,
            "time_limit_seconds": 15,
        },
    ],
    "sifat_learning": [
        {
            "question_id": "sl_001",
            "text_en": "What does 'Analitik' mean?",
            "text_tr": "'Analitik' ne anlama gelir?",
            "choices_en": ["Emotional", "Analytical", "Creative", "Social"],
            "choices_tr": ["Duygusal", "Analitik", "Yaratıcı", "Sosyal"],
            "correct_index": 1,
            "time_limit_seconds": 20,
        },
    ],
    "face_quiz": [
        {
            "question_id": "fq_001",
            "text_en": "Which face feature indicates analytical personality?",
            "text_tr": "Hangi yüz özelliği analitik kişiliği işaret eder?",
            "choices_en": ["Full lips", "High forehead", "Wide nose", "Round chin"],
            "choices_tr": ["Dolgun dudaklar", "Yüksek alın", "Geniş burun", "Yuvarlak çene"],
            "correct_index": 1,
            "time_limit_seconds": 20,
        },
    ],
}


def _gen_id():
    return "sess_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


class DiscoveryGameService:

    @staticmethod
    def _db():
        from admin_api.utils.mongo import _get_db
        return _get_db()

    @staticmethod
    def start_session(user_id: int, game_type_id: str) -> dict:
        if game_type_id not in DISCOVERY_GAME_TYPES:
            raise GameTypeNotFoundError(f"Unknown game type: {game_type_id}")
        gtype = DISCOVERY_GAME_TYPES[game_type_id]
        questions = _SAMPLE_QUESTIONS.get(game_type_id, [])
        session_id = _gen_id()
        now = datetime.utcnow()
        db = DiscoveryGameService._db()
        db["discovery_game_sessions"].insert_one({
            "session_id": session_id,
            "user_id": user_id,
            "game_type_id": game_type_id,
            "state": "active",
            "questions": questions,
            "current_question_idx": 0,
            "answers": [],
            "score": 0,
            "coins_wagered": gtype.coin_reward_play,
            "started_at": now.isoformat(),
            "updated_at": now.isoformat(),
        })
        first_q = questions[0] if questions else None
        return {
            "session_id": session_id,
            "game_type_id": game_type_id,
            "state": "active",
            "coins_wagered": gtype.coin_reward_play,
            "total_questions": len(questions),
            "current_question": first_q,
        }

    @staticmethod
    def start_game(
        user_id: int,
        game_type: str,
        difficulty: str = "normal",
        language: str = "en",
    ):
        """View-facing alias for start_session. Returns (session_id, first_question)."""
        result = DiscoveryGameService.start_session(user_id, game_type)
        return result["session_id"], result.get("current_question")

    @staticmethod
    def answer_question(session_id: str, user_id: int, answer_index: int) -> dict:
        db = DiscoveryGameService._db()
        col = db["discovery_game_sessions"]
        session = col.find_one({"session_id": session_id, "user_id": user_id})
        if not session:
            raise SessionNotFoundError(session_id)
        questions = session.get("questions", [])
        idx = session.get("current_question_idx", 0)
        if idx >= len(questions):
            return {"session_id": session_id, "completed": True, "score": session.get("score", 0)}
        current_q = questions[idx]
        correct = current_q.get("correct_index") == answer_index
        score = session.get("score", 0) + (10 if correct else 0)
        new_idx = idx + 1
        completed = new_idx >= len(questions)
        next_q = questions[new_idx] if not completed else None
        col.update_one(
            {"session_id": session_id},
            {"$set": {
                "current_question_idx": new_idx,
                "score": score,
                "state": "completed" if completed else "active",
                "updated_at": datetime.utcnow().isoformat(),
            }, "$push": {"answers": {"q_id": current_q["question_id"], "answer": answer_index, "correct": correct}}},
        )
        return {
            "session_id": session_id,
            "correct": correct,
            "score_gained": 10 if correct else 0,
            "total_score": score,
            "completed": completed,
            "next_question": next_q,
        }

    @staticmethod
    def submit_answer(
        session_id: str,
        user_id: int,
        question_id: str,
        answer,
    ):
        """View-facing method. Returns (is_correct, result) where result is
        next_question dict on continue or completion dict on game over."""
        answer_index = int(answer) if isinstance(answer, (int, float, str)) else 0
        result = DiscoveryGameService.answer_question(session_id, user_id, answer_index)
        is_correct = result.get("correct", False)
        if result.get("completed"):
            db = DiscoveryGameService._db()
            session = db["discovery_game_sessions"].find_one(
                {"session_id": session_id}, {"questions": 1, "answers": 1, "score": 1, "game_type_id": 1}
            )
            total_q = len(session.get("questions", [])) if session else 1
            correct_count = sum(1 for a in (session.get("answers", []) if session else []) if a.get("correct"))
            accuracy = round(correct_count / total_q * 100, 1) if total_q else 0.0
            gtype = DISCOVERY_GAME_TYPES.get(session.get("game_type_id", "") if session else "", None)
            coins = gtype.coin_reward_win if gtype else 0
            return is_correct, {
                "accuracy_percent": accuracy,
                "coins_earned": coins,
                "xp_earned": 10,
                "traits_discovered": [],
                "insights": "Great job! Your facial trait awareness is growing.",
            }
        return is_correct, result.get("next_question") or {}

    @staticmethod
    def abandon_game(session_id: str, user_id: int) -> bool:
        """View-facing alias for abandon_session."""
        return DiscoveryGameService.abandon_session(session_id, user_id)

    @staticmethod
    def get_session(session_id: str, user_id: int) -> dict:
        db = DiscoveryGameService._db()
        session = db["discovery_game_sessions"].find_one(
            {"session_id": session_id, "user_id": user_id}, {"_id": 0}
        )
        if not session:
            raise SessionNotFoundError(session_id)
        return session

    @staticmethod
    def abandon_session(session_id: str, user_id: int) -> bool:
        db = DiscoveryGameService._db()
        result = db["discovery_game_sessions"].update_one(
            {"session_id": session_id, "user_id": user_id},
            {"$set": {"state": "abandoned", "updated_at": datetime.utcnow().isoformat()}},
        )
        if result.matched_count == 0:
            raise SessionNotFoundError(session_id)
        return True
