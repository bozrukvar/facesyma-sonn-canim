"""
Authentication & User Management Module
Handles user registration, login, sessions, and preferences

Sessions stored in Redis for:
  - Persistence across restarts
  - Sharing across multiple workers
  - Automatic expiration via TTL
  - Graceful degradation if Redis unavailable
"""
import os
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from facesyma_ai.core.redis_client import redis_get, redis_set, redis_delete

log = logging.getLogger(__name__)
SESSION_STORAGE_TTL = 86400  # 24 hours (matches Session duration_hours default)

class User:
    """User model with profile and preferences"""
    def __init__(self, user_id: str, email: str, name: str, lang: str = "tr"):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.lang = lang
        self.created_at = datetime.now().isoformat()
        self.last_login = None
        self.preferences = {
            "language": lang,
            "theme": "light",
            "notifications_enabled": True,
            "auto_save_conversations": True,
            "favorite_modules": [],
            "privacy_level": "private"  # private, friends, public
        }
        self.profile = {
            "bio": "",
            "avatar_url": None,
            "sifatlar": [],
            "personality_type": None,
            "golden_ratio_score": None
        }

class Session:
    """Session manager for user authentication with Redis persistence"""
    def __init__(self, user_id: str, duration_hours: int = 24):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        _now = datetime.now()
        self.created_at = _now.isoformat()
        self.expires_at = (_now + timedelta(hours=duration_hours)).isoformat()
        self.is_active = True

    def is_valid(self) -> bool:
        """Check if session is still valid"""
        return self.is_active and datetime.fromisoformat(self.expires_at) > datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dict for JSON serialization"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create session from dict"""
        session = cls.__new__(cls)
        session.session_id = data["session_id"]
        session.user_id = data["user_id"]
        session.created_at = data["created_at"]
        session.expires_at = data["expires_at"]
        session.is_active = data["is_active"]
        return session

class AuthManager:
    """Authentication and user management"""
    def __init__(self, users_db_path: str = "./users_db.json"):
        self.users_db_path = users_db_path
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.load_users()

    def load_users(self):
        """Load users from database"""
        if os.path.exists(self.users_db_path):
            try:
                with open(self.users_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, user_data in data.items():
                        user = User(**user_data)
                        self.users[user_id] = user
                log.info(f"Loaded {len(self.users)} users from database")
            except Exception as e:
                log.error(f"Error loading users: {e}")

    def save_users(self):
        """Save users to database"""
        try:
            data = {}
            for user_id, user in self.users.items():
                data[user_id] = {
                    "user_id": user.user_id,
                    "email": user.email,
                    "name": user.name,
                    "lang": user.lang,
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                    "preferences": user.preferences,
                    "profile": user.profile
                }
            with open(self.users_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.info("Users saved to database")
        except Exception as e:
            log.error(f"Error saving users: {e}")

    def register(self, email: str, name: str, lang: str = "tr") -> Optional[User]:
        """Register new user"""
        if any(u.email == email for u in self.users.values()):
            log.warning(f"User with email {email} already exists")
            return None

        user_id = str(uuid.uuid4())
        user = User(user_id, email, name, lang)
        self.users[user_id] = user
        self.save_users()
        log.info(f"User registered: {email}")
        return user

    def login(self, email: str) -> Optional[Session]:
        """Login user and create session stored in Redis"""
        user = next((u for u in self.users.values() if u.email == email), None)
        if not user:
            log.warning(f"Login failed: user {email} not found")
            return None

        user.last_login = datetime.now().isoformat()
        self.save_users()

        session = Session(user.user_id)
        _sid = session.session_id
        self.sessions[_sid] = session

        # Store session in Redis with TTL matching session expiry
        session_data = json.dumps(session.to_dict())
        redis_set(f"session:v1:{_sid}", session_data.encode(), ttl=SESSION_STORAGE_TTL)

        log.info(f"User logged in: {email} (session: {_sid})")
        return session

    def validate_session(self, session_id: str) -> Optional[User]:
        """Validate session and return user (checks Redis first for persistence)"""
        # Check Redis first
        redis_session_data = redis_get(f"session:v1:{session_id}")
        if redis_session_data:
            try:
                session_dict = json.loads(redis_session_data.decode())
                session = Session.from_dict(session_dict)
                if session.is_valid():
                    return self.users.get(session.user_id)
            except Exception as e:
                log.warning(f"Failed to deserialize Redis session {session_id}: {e}")

        # Fall back to in-memory cache
        session = self.sessions.get(session_id)
        if not session or not session.is_valid():
            return None

        return self.users.get(session.user_id)

    def logout(self, session_id: str) -> bool:
        """Logout user (removes from Redis and in-memory cache)"""
        session = self.sessions.get(session_id)
        if session:
            session.is_active = False
            # Delete from Redis
            redis_delete(f"session:v1:{session_id}")
            log.info(f"User logged out: {session.user_id}")
            return True
        return False

    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        user = self.users.get(user_id)
        if not user:
            return False

        user.preferences.update(preferences)
        self.save_users()
        log.info(f"Preferences updated for user: {user_id}")
        return True

    def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile (sifatlar, personality type, etc.)"""
        user = self.users.get(user_id)
        if not user:
            return False

        user.profile.update(profile_data)
        self.save_users()
        log.info(f"Profile updated for user: {user_id}")
        return True

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)

    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired = [sid for sid, session in self.sessions.items() if not session.is_valid()]
        for sid in expired:
            del self.sessions[sid]
        log.info(f"Cleaned up {len(expired)} expired sessions")
