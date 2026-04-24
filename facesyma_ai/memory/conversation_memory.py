"""
Dialogue Memory Module
Manages conversation history, context, and semantic memory for coherent conversations
"""
import json
import os
from datetime import datetime, timedelta
from operator import attrgetter
from typing import Dict, List, Any, Optional
import logging

log = logging.getLogger(__name__)

class Message:
    """Single conversation message"""
    def __init__(self, role: str, content: str, category: str = None, module: str = None):
        self.timestamp = datetime.now().isoformat()
        self.role = role  # "user" or "assistant"
        self.content = content
        self.category = category
        self.module = module
        self.metadata = {}

class Conversation:
    """Single conversation session"""
    def __init__(self, conversation_id: str, user_id: str, language: str = "tr"):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.language = language
        self.created_at = self.updated_at = datetime.now().isoformat()
        self.messages: List[Message] = []
        self.theme = "general"  # general, career, relationships, etc.
        self.summary = ""
        self.key_topics = []

class ConversationMemory:
    """Manages conversation history and semantic memory"""
    def __init__(self, memory_db_path: str = "./conversations_db.json", max_history: int = 50):
        self.memory_db_path = memory_db_path
        self.max_history = max_history
        self.conversations: Dict[str, Conversation] = {}
        self.semantic_index: Dict[str, List[str]] = {}  # topic -> conversation_ids
        self.user_summaries: Dict[str, str] = {}  # user_id -> memory summary
        self.load_conversations()

    def load_conversations(self):
        """Load conversation history"""
        if os.path.exists(self.memory_db_path):
            try:
                with open(self.memory_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    _dget = data.get
                    for conv_id, conv_data in _dget("conversations", {}).items():
                        _cdget = conv_data.get
                        conv = Conversation(conv_id, conv_data["user_id"],
                                          _cdget("language", "tr"))
                        for msg_data in _cdget("messages", []):
                            _mdget = msg_data.get
                            msg = Message(msg_data["role"], msg_data["content"],
                                        _mdget("category"), _mdget("module"))
                            conv.messages.append(msg)
                        conv.theme     = _cdget("theme", "general")
                        conv.summary   = _cdget("summary", "")
                        conv.key_topics= _cdget("key_topics", [])
                        self.conversations[conv_id] = conv

                    self.user_summaries = _dget("user_summaries", {})
                    self.semantic_index = _dget("semantic_index", {})

                log.info(f"Loaded {len(self.conversations)} conversations")
            except Exception as e:
                log.error(f"Error loading conversations: {e}")

    def save_conversations(self):
        """Save conversation history"""
        try:
            data = {
                "conversations": {},
                "user_summaries": self.user_summaries,
                "semantic_index": self.semantic_index
            }

            for conv_id, conv in self.conversations.items():
                data["conversations"][conv_id] = {
                    "conversation_id": conv.conversation_id,
                    "user_id": conv.user_id,
                    "language": conv.language,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "messages": [
                        {
                            "timestamp": msg.timestamp,
                            "role": msg.role,
                            "content": msg.content,
                            "category": msg.category,
                            "module": msg.module
                        }
                        for msg in conv.messages
                    ],
                    "theme": conv.theme,
                    "summary": conv.summary,
                    "key_topics": conv.key_topics
                }

            with open(self.memory_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.info("Conversations saved")
        except Exception as e:
            log.error(f"Error saving conversations: {e}")

    def create_conversation(self, user_id: str, conversation_id: str,
                          language: str = "tr", theme: str = "general") -> Conversation:
        """Create new conversation"""
        conv = Conversation(conversation_id, user_id, language)
        conv.theme = theme
        self.conversations[conversation_id] = conv
        self.save_conversations()
        log.info(f"Conversation created: {conversation_id}")
        return conv

    def add_message(self, conversation_id: str, role: str, content: str,
                   category: str = None, module: str = None) -> bool:
        """Add message to conversation"""
        conv = self.conversations.get(conversation_id)
        if not conv:
            return False

        msg = Message(role, content, category, module)
        _msgs = conv.messages
        _msgs.append(msg)
        conv.updated_at = datetime.now().isoformat()

        # Limit history
        if len(_msgs) > self.max_history:
            conv.messages = _msgs[-self.max_history:]

        # Update semantic index
        if category:
            _si = self.semantic_index
            cat_list = _si.setdefault(category, [])
            if conversation_id not in cat_list:
                cat_list.append(conversation_id)

        self.save_conversations()
        return True

    def get_conversation_history(self, conversation_id: str,
                                limit: int = None) -> List[Dict[str, Any]]:
        """Get conversation history"""
        conv = self.conversations.get(conversation_id)
        if not conv:
            return []

        messages = conv.messages
        if limit:
            messages = messages[-limit:]

        return [
            {
                "timestamp": msg.timestamp,
                "role": msg.role,
                "content": msg.content,
                "category": msg.category,
                "module": msg.module
            }
            for msg in messages
        ]

    def get_context_window(self, conversation_id: str,
                          window_size: int = 10) -> List[Dict[str, str]]:
        """Get recent messages for LLM context"""
        messages = self.get_conversation_history(conversation_id, limit=window_size)
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def update_conversation_summary(self, conversation_id: str, summary: str,
                                   key_topics: List[str] = None) -> bool:
        """Update conversation summary (for long-term memory)"""
        conv = self.conversations.get(conversation_id)
        if not conv:
            return False

        conv.summary = summary
        if key_topics:
            conv.key_topics = key_topics

        self.save_conversations()
        return True

    def get_user_memory_summary(self, user_id: str) -> Optional[str]:
        """Get consolidated memory of user from past conversations"""
        return self.user_summaries.get(user_id)

    def update_user_memory_summary(self, user_id: str, summary: str):
        """Update user's consolidated memory summary"""
        self.user_summaries[user_id] = summary
        self.save_conversations()
        log.info(f"User memory summary updated: {user_id}")

    def get_conversations_by_theme(self, user_id: str, theme: str) -> List[Conversation]:
        """Get all conversations for a user by theme"""
        return [
            conv for conv in self.conversations.values()
            if conv.user_id == user_id and conv.theme == theme
        ]

    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user"""
        convs = [conv for conv in self.conversations.values() if conv.user_id == user_id]
        return [
            {
                "conversation_id": conv.conversation_id,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "theme": conv.theme,
                "message_count": len(conv.messages),
                "summary": conv.summary,
                "key_topics": conv.key_topics
            }
            for conv in sorted(convs, key=attrgetter('updated_at'), reverse=True)
        ]

    def find_related_conversations(self, topic: str, user_id: str) -> List[Conversation]:
        """Find conversations related to a topic"""
        related = []
        for conv in self.conversations.values():
            if conv.user_id != user_id:
                continue
            if topic in conv.key_topics or topic in conv.theme:
                related.append(conv)
        return related

    def cleanup_old_conversations(self, days: int = 90) -> int:
        """Delete conversations older than N days"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        to_delete = [
            cid for cid, conv in self.conversations.items()
            if conv.created_at < cutoff
        ]
        for cid in to_delete:
            del self.conversations[cid]
        self.save_conversations()
        _n = len(to_delete)
        log.info(f"Cleaned up {_n} old conversations")
        return _n
